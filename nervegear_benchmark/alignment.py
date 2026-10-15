import json
import os
import platform
import time

import h5py
import numpy as np

from . import __version__
from .calibration import arrays_digest, fingerprint, fit_fold, validate_time
from .diagnostics import aggregate_stats, error_stats
from .pipeline import coverage, load_record, peak_memory_mib, table, validate_protocol
from .report import bar_chart

SHIFTS = {
    "ridge": 0,
    "ridge_past_1s": -50,
    "ridge_future_1s": 50,
    "ridge_past_5s": -250,
    "ridge_future_5s": 250,
}
METHODS = [*SHIFTS, "train_median", "prefix_median"]
PRIMARY = "ridge_minus_symmetric_5s_error"
SECONDARY = [f"ridge_minus_{name}" for name in [*list(SHIFTS)[1:], "prefix_median"]]


def within_shift_tolerance(duration, nominal):
    return (duration >= nominal - 0.010) & (duration <= nominal + 0.010)


def pair_outputs(item, source_time):
    elapsed = source_time - source_time[0]
    ends = item["ends"]
    rows = np.arange(len(ends))
    sources = {name: rows + shift for name, shift in SHIFTS.items()}
    prefix = (elapsed[ends] < 10.0) & item["eligible"]
    mask = item["eligible"].copy()
    counts = {"all_grid_rows": len(rows), "target_valid": int(mask.sum())}
    for indices in sources.values():
        mask &= (indices >= 0) & (indices < len(rows))
    counts["indices_in_bounds"] = int(mask.sum())
    # Clipped indices permit vectorized checks; the in-bounds mask rejects every clipped row.
    safe = {name: np.clip(indices, 0, max(len(rows) - 1, 0)) for name, indices in sources.items()}
    for indices in safe.values():
        mask &= item["input_valid"][indices]
    counts["source_inputs_valid"] = int(mask.sum())
    for indices in safe.values():
        mask &= (elapsed[ends[indices]] >= 10.2) & (elapsed[ends[indices] - 399] >= 10.0)
    counts["after_prefix_and_embargo"] = int(mask.sum())
    for name, shift in SHIFTS.items():
        if shift:
            duration = elapsed[ends[safe[name]]] - elapsed[ends]
            mask &= within_shift_tolerance(duration, shift * 0.02)
    counts["shift_tolerances"] = int(mask.sum())
    selected = {name: indices[mask] for name, indices in sources.items()}
    durations = {}
    for name, shift in SHIFTS.items():
        if not shift:
            continue
        values = elapsed[ends[selected[name]]] - elapsed[ends[mask]]
        durations[name] = (
            {"minimum_seconds": float(values.min()), "maximum_seconds": float(values.max())}
            if len(values)
            else None
        )
    return {
        "prefix_mask": prefix,
        "mask": mask,
        "sources": selected,
        "coverage": counts,
        "realized_shifts": durations,
    }


def predict_methods(fit, prefix_median, item, sources):
    result = {name: fit["model"].predict(item["x"][indices]) for name, indices in sources.items()}
    for name, pose in [("train_median", fit["train_median"]), ("prefix_median", prefix_median)]:
        result[name] = np.broadcast_to(pose, result["ridge"].shape)
    return result


def score_predictions(predictions, target):
    result = {}
    for name in METHODS:
        metrics = error_stats(predictions[name], target)
        metrics["per_joint_rmse_rad"] = np.sqrt(metrics["per_joint_mse_rad2"]).tolist()
        del metrics["residual_mean_rad"], metrics["residual_variance_rad2"]
        if not all(np.isfinite(v).all() for v in metrics.values()):
            raise ValueError(f"Nonfinite alignment metrics: {name}")
        result[name] = metrics
    return result


def aggregate_folds(folds):
    supported = [f for f in folds if f["status"] == "supported"]
    methods = {}
    for name in METHODS:
        values = [f["scores"][name] for f in supported]
        if not values:
            methods[name] = None
            continue
        mse = np.mean([v["per_joint_mse_rad2"] for v in values], axis=0)
        methods[name] = {
            **aggregate_stats(values),
            "macro_per_joint_mse_rad2": mse.tolist(),
            "macro_per_joint_rmse_rad": np.sqrt(mse).tolist(),
        }
    comparisons = {}
    for key in [PRIMARY, *SECONDARY]:
        differences = []
        for fold in supported:
            scores = fold["scores"]
            baseline = (
                (scores["ridge_past_5s"]["mae_rad"] + scores["ridge_future_5s"]["mae_rad"]) / 2
                if key == PRIMARY
                else scores[key.removeprefix("ridge_minus_")]["mae_rad"]
            )
            differences.append(scores["ridge"]["mae_rad"] - baseline)
        comparisons[key] = (
            {
                "macro_mae_difference_rad": float(np.mean(differences)),
                "improved": sum(v < -1e-12 for v in differences),
                "tied": sum(abs(v) <= 1e-12 for v in differences),
                "worsened": sum(v > 1e-12 for v in differences),
                "folds": [
                    {"recording": f["recording"], "difference_rad": value}
                    for f, value in zip(supported, differences, strict=True)
                ],
            }
            if supported
            else None
        )
    return {
        "supported_folds": len(supported),
        "unsupported_folds": len(folds) - len(supported),
        "methods": methods,
        "paired_differences": comparisons,
    }


def validate_study(study):
    expected = {
        "schema_version": 1,
        "study_id": "temporal-alignment-audit-v1",
        "source_protocol_id": "emg2pose-starter-left-pilot-v1",
        "fold_recordings": list(range(1, 10)),
        "history_samples": 400,
        "first_output_sample_index": 399,
        "output_stride_samples": 40,
        "ridge_alpha": 10.0,
        "prefix_seconds": 10.0,
        "embargo_seconds": 0.2,
        "minimum_prefix_outputs": 25,
        "minimum_scored_outputs": 100,
        "shift_rows": SHIFTS,
        "nominal_output_interval_seconds": 0.02,
        "shift_tolerance_seconds": 0.010,
        "tie_tolerance_rad": 1e-12,
        "methods": METHODS,
        "primary_comparison": PRIMARY,
        "secondary_comparisons": SECONDARY,
        "maximum_threads": 2,
        "maximum_run_seconds": 900,
    }
    for key, value in expected.items():
        if study.get(key) != value:
            raise ValueError(f"Unsupported alignment setting: {key}")
    if set(study) != set(expected) | {"scope", "label_access"}:
        raise ValueError("Unexpected alignment protocol fields")
    return study


def evaluate_fold(tables, record, item):
    recording = record["entry"]["recording"]
    fit = fit_fold(tables, recording)
    pair = pair_outputs(item, record["time"])
    prefix_count = int(pair["prefix_mask"].sum())
    result = {
        "recording": recording,
        "stage": record["entry"]["stage"],
        "filename": record["entry"]["filename"],
        "prefix_outputs": prefix_count,
        "coverage": pair["coverage"],
        "realized_shifts": pair["realized_shifts"],
        "common_target_mask_sha256": arrays_digest([pair["mask"]]),
    }
    reasons = []
    if prefix_count < 25:
        reasons.append("Fewer than 25 eligible prefix labels")
    if pair["coverage"]["shift_tolerances"] < 100:
        reasons.append("Fewer than 100 common scored outputs")
    if reasons:
        return {**result, "status": "unsupported", "reasons": reasons, "scores": None}
    model = fit["model"]
    prefix_median = np.median(item["y"][pair["prefix_mask"]], axis=0)
    predictions = predict_methods(fit, prefix_median, item, pair["sources"])
    scores = score_predictions(predictions, item["y"][pair["mask"]])
    return {
        **result,
        "status": "supported",
        "training_recordings": fit["training_recordings"],
        "training_outputs": fit["training_outputs"],
        "initial_fit_sha256": arrays_digest(
            [model.mean, model.scale, model.target_mean, model.coefficients, fit["train_median"]]
        ),
        "prefix_control_sha256": arrays_digest([prefix_median]),
        "prediction_sha256": {
            name: arrays_digest([values]) for name, values in predictions.items()
        },
        "scores": scores,
    }


def write_report(summary, output):
    aggregate = summary["aggregate"]
    rows = [
        (name, values["macro_mae_rad"] * 180 / np.pi)
        for name, values in aggregate["methods"].items()
        if values is not None
    ]
    bar_chart(
        output / "method-errors.svg",
        "Temporal alignment audit",
        rows or [("Unsupported folds", len(summary["folds"]))],
        subtitle="MAE in degrees; common targets; future shifts use future inputs"
        if rows
        else "Counts only; all scores unavailable",
    )
    bar_chart(
        output / "common-coverage.svg",
        "Common scored outputs by recording",
        [
            (f"Recording {f['recording']}", f["coverage"]["shift_tolerances"])
            for f in summary["folds"]
        ],
        subtitle="Same targets for all seven methods; minimum 100 per supported fold",
    )
    primary = aggregate["paired_differences"][PRIMARY]
    verdict = (
        f"Aligned minus mean past/future 5-second errors: "
        f"{primary['macro_mae_difference_rad'] * 180 / np.pi:+.6f} degrees. "
        "Negative means lower aligned error."
        if primary
        else "No supported folds; primary comparison unavailable."
    )
    lines = [
        "# Temporal alignment audit",
        "",
        f"Supported folds: {aggregate['supported_folds']}/9. {verdict}",
        "",
        "| Method | Macro MAE, degrees |",
        "| --- | ---: |",
    ]
    lines += [f"| {name} | {value:.3f} |" for name, value in rows]
    if not rows:
        lines += ["| All methods | Unavailable: no supported folds |"]
    lines += [
        "",
        "![Method errors](method-errors.svg)",
        "",
        "![Common coverage](common-coverage.svg)",
        "",
        "Each fold fits fixed RMS ridge on the other eight original training recordings. "
        "All methods use identical target timestamps after the prefix and embargo. "
        "Future shifts use future EMG and are noncausal diagnostic controls. "
        "The primary comparison averages two MAEs, not two prediction vectors.",
        "",
        "These already inspected data cover one person/session. Shifts can retain pose "
        "information and change pose composition. This audit establishes neither neural "
        "latency nor a biological mechanism, live control, or full-dive capability. "
        "It supplies no population confidence interval or formal null distribution.",
        "",
        "summary.json reports every fold, coverage, actual shift durations, per-joint "
        "errors, paired comparisons, fingerprints, and resources. Original validation "
        "and test files are excluded. No raw samples, per-sample predictions, or fitted "
        "coefficients are published. Dataset attribution and noncommercial terms are "
        "in docs/datasets/emg2pose.md.",
        "",
    ]
    (output / "report.md").write_text("\n".join(lines), encoding="utf-8")


def run(manifest_path, data_dir, output, study_path):
    started = time.perf_counter()
    cpu_started = time.process_time()
    source = validate_protocol(json.loads(manifest_path.read_text(encoding="utf-8")))
    study = validate_study(json.loads(study_path.read_text(encoding="utf-8")))
    if source["protocol_id"] != study["source_protocol_id"]:
        raise ValueError("Source protocol does not match alignment study")
    if output.exists():
        raise ValueError("Output directory already exists; choose a new alignment directory")
    entries = [e for e in source["files"] if e["split"] == "train"]
    if len(entries) != 9:
        raise ValueError("Alignment requires exactly nine original training recordings")
    if sum((data_dir / e["filename"]).stat().st_size for e in entries) > 5 * 1024**3:
        raise ValueError("Alignment recordings exceed the disk cap")
    records = [load_record(data_dir, e) for e in entries]
    for record in records:
        validate_time(record["time"], record["entry"]["filename"])
    tables = [table(record, 400) for record in records]
    folds = [
        evaluate_fold(tables, record, item) for record, item in zip(records, tables, strict=True)
    ]
    aggregate = aggregate_folds(folds)
    summary = {
        "schema_version": 1,
        "status": "complete" if aggregate["supported_folds"] else "unsupported_study",
        "study": study,
        "study_sha256": fingerprint(study),
        "source_protocol_sha256": fingerprint(source),
        "loaded_files": entries,
        "source_coverage": coverage(tables),
        "folds": folds,
        "aggregate": aggregate,
        "integrity_definition": "SHA-256 digests identify fits, prefix constants, full common "
        "target masks, and per-method predictions without publishing per-sample data.",
        "software": {
            "benchmark": __version__,
            "python": platform.python_version(),
            "numpy": np.__version__,
            "h5py": h5py.__version__,
            "platform": platform.system(),
            "logical_cpu_count": os.cpu_count(),
        },
        "thread_environment": {
            key: os.environ.get(key)
            for key in ["OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "OMP_NUM_THREADS"]
        },
        "resources": {
            "analysis_wall_seconds": time.perf_counter() - started,
            "cpu_seconds": time.process_time() - cpu_started,
            "peak_process_memory_mib": peak_memory_mib(),
            "limit_seconds": 900,
        },
    }
    payload = json.dumps(summary, indent=2, allow_nan=False) + "\n"
    if time.perf_counter() - started >= 900:
        raise ValueError("Alignment exceeded the 15-minute wall-clock limit")
    output.mkdir(parents=True, exist_ok=False)
    (output / "summary.json").write_text(payload, encoding="utf-8")
    (output / "study.json").write_text(json.dumps(study, indent=2) + "\n", encoding="utf-8")
    write_report(summary, output)
    (output / "completion.json").write_text(
        json.dumps(
            {
                "complete": True,
                "error_count": 0,
                "wall_seconds_including_outputs": time.perf_counter() - started,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    print(f"Completed alignment audit: {output}; {aggregate['supported_folds']}/9 supported folds")
    return summary
