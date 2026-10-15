import json
import os
import platform
import time

import h5py
import numpy as np

from . import __version__, core
from .calibration import arrays_digest, fingerprint, validate_time
from .diagnostics import aggregate_stats, error_stats
from .pipeline import coverage, load_record, peak_memory_mib, validate_protocol
from .report import bar_chart

ALPHAS = {"ridge_current": 10.0, "ridge_wide": 10.0, "ridge_history": 50.0}
DIMENSIONS = {"ridge_current": 16, "ridge_wide": 16, "ridge_history": 80}
METHODS = [*ALPHAS, "train_median", "prefix_median"]
PRIMARY = "ridge_history_minus_ridge_current"
SECONDARY = ["ridge_history_minus_ridge_wide", "ridge_history_minus_prefix_median"]


def make_table(record):
    ends, wide, valid = core.features(record["emg"], record["time"], 1200, 40, 1199, 1200)
    _, recent, _ = core.features(record["emg"], record["time"], 400, 40, 399, 400)
    rows = (ends - 399) // 40
    x = {
        "ridge_current": recent[rows],
        "ridge_wide": wide,
        "ridge_history": np.concatenate(
            [recent[rows - offset] for offset in [0, 5, 10, 15, 20]], axis=1
        ),
    }
    for values in x.values():
        values[~valid] = np.nan
    y = record["target"][ends].astype(np.float64)
    reference = core.reference_valid(y)
    return {
        "entry": record["entry"],
        "ends": ends,
        "x": x,
        "y": y,
        "input_valid": valid,
        "reference_valid": reference,
        "eligible": valid & reference,
    }


def partition(item, source_time):
    elapsed = source_time - source_time[0]
    ends = item["ends"]
    prefix = elapsed[ends] < 10.0
    score = (elapsed[ends] >= 10.6) & (elapsed[ends - 1199] >= 10.0)
    regions = {"prefix": prefix, "embargo": ~prefix & ~score, "score": score}
    masks = {}
    counts = {}
    for name, region in regions.items():
        masks[name] = region & item["eligible"]
        counts[name] = {
            "candidate_outputs": int(region.sum()),
            "invalid_input_outputs": int((region & ~item["input_valid"]).sum()),
            "invalid_reference_outputs": int(
                (region & item["input_valid"] & ~item["reference_valid"]).sum()
            ),
            "eligible_outputs": int(masks[name].sum()),
        }
    return masks, counts


def fit_fold(tables, held_out):
    training = [t for t in tables if t["entry"]["recording"] != held_out]
    if not training or not any(t["eligible"].any() for t in training):
        raise ValueError(f"Fold {held_out}: no eligible fitting outputs")
    target = np.concatenate([t["y"][t["eligible"]] for t in training])
    models = {}
    for name, alpha in ALPHAS.items():
        x = np.concatenate([t["x"][name][t["eligible"]] for t in training])
        model = core.fit_ridge(x, target, alpha)
        if not all(
            np.isfinite(v).all()
            for v in [model.mean, model.scale, model.target_mean, model.coefficients]
        ):
            raise ValueError(f"Fold {held_out}: nonfinite fitted parameters for {name}")
        models[name] = model
    median = np.median(target, axis=0)
    if not np.isfinite(median).all():
        raise ValueError(f"Fold {held_out}: nonfinite training median")
    return {
        "models": models,
        "train_median": median,
        "training_outputs": len(target),
        "training_recordings": [t["entry"]["recording"] for t in training],
    }


def predict_methods(fit, prefix_median, item, mask):
    result = {name: model.predict(item["x"][name][mask]) for name, model in fit["models"].items()}
    for name, value in [("train_median", fit["train_median"]), ("prefix_median", prefix_median)]:
        result[name] = np.broadcast_to(value, result["ridge_current"].shape)
    return result


def score_predictions(predictions, target):
    result = {}
    for name in METHODS:
        metrics = error_stats(predictions[name], target)
        metrics["per_joint_rmse_rad"] = np.sqrt(metrics["per_joint_mse_rad2"]).tolist()
        del metrics["residual_mean_rad"], metrics["residual_variance_rad2"]
        if not all(np.isfinite(v).all() for v in metrics.values()):
            raise ValueError(f"Nonfinite history metrics: {name}")
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
    paired = {}
    for key in [PRIMARY, *SECONDARY]:
        baseline = key.removeprefix("ridge_history_minus_")
        differences = [
            f["scores"]["ridge_history"]["mae_rad"] - f["scores"][baseline]["mae_rad"]
            for f in supported
        ]
        paired[key] = (
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
        "paired_differences": paired,
    }


def evaluate_fold(tables, record, item):
    recording = record["entry"]["recording"]
    fit = fit_fold(tables, recording)
    masks, counts = partition(item, record["time"])
    result = {
        "recording": recording,
        "filename": record["entry"]["filename"],
        "stage": record["entry"]["stage"],
        "training_recordings": fit["training_recordings"],
        "training_outputs": fit["training_outputs"],
        "model_settings": {
            name: {"dimension": model.coefficients.shape[0], "effective_alpha": ALPHAS[name]}
            for name, model in fit["models"].items()
        },
        "fit_sha256": {
            name: arrays_digest([model.mean, model.scale, model.target_mean, model.coefficients])
            for name, model in fit["models"].items()
        },
        "training_median_sha256": arrays_digest([fit["train_median"]]),
        "common_scored_mask_sha256": arrays_digest([masks["score"]]),
        "partitions": counts,
    }
    reasons = []
    if counts["prefix"]["eligible_outputs"] < 25:
        reasons.append("Fewer than 25 eligible prefix labels")
    if counts["score"]["eligible_outputs"] < 100:
        reasons.append("Fewer than 100 common scored outputs")
    if reasons:
        return {**result, "status": "unsupported", "reasons": reasons, "scores": None}
    prefix = np.median(item["y"][masks["prefix"]], axis=0)
    predictions = predict_methods(fit, prefix, item, masks["score"])
    return {
        **result,
        "status": "supported",
        "prefix_control_sha256": arrays_digest([prefix]),
        "prediction_sha256": {name: arrays_digest([value]) for name, value in predictions.items()},
        "scores": score_predictions(predictions, item["y"][masks["score"]]),
    }


def validate_study(study):
    expected = {
        "schema_version": 1,
        "study_id": "causal-history-decoder-v1",
        "source_protocol_id": "emg2pose-starter-left-pilot-v1",
        "fold_recordings": list(range(1, 10)),
        "common_history_samples": 1200,
        "first_output_sample_index": 1199,
        "output_stride_samples": 40,
        "tap_history_samples": 400,
        "tap_offsets_samples": [0, 200, 400, 600, 800],
        "base_ridge_alpha": 10.0,
        "history_standardized_feature_divisor_squared": 5.0,
        "effective_ridge_alphas": ALPHAS,
        "representation_dimensions": DIMENSIONS,
        "prefix_seconds": 10.0,
        "embargo_seconds": 0.6,
        "minimum_prefix_outputs": 25,
        "minimum_scored_outputs": 100,
        "tie_tolerance_rad": 1e-12,
        "methods": METHODS,
        "primary_comparison": PRIMARY,
        "secondary_comparisons": SECONDARY,
        "maximum_threads": 2,
        "maximum_run_seconds": 900,
    }
    for key, value in expected.items():
        if study.get(key) != value:
            raise ValueError(f"Unsupported history setting: {key}")
    if set(study) != set(expected) | {"scope", "label_access"}:
        raise ValueError("Unexpected history protocol fields")
    return study


def write_report(summary, output):
    aggregate = summary["aggregate"]
    rows = [
        (name, values["macro_mae_rad"] * 180 / np.pi)
        for name, values in aggregate["methods"].items()
        if values is not None
    ]
    bar_chart(
        output / "method-errors.svg",
        "Fixed causal EMG history comparison",
        rows or [("Unsupported folds", len(summary["folds"]))],
        subtitle="MAE in degrees; common fitting and scoring timestamps"
        if rows
        else "Counts only; all errors unavailable",
    )
    bar_chart(
        output / "score-coverage.svg",
        "Common scored outputs by recording",
        [
            (f"Recording {f['recording']}", f["partitions"]["score"]["eligible_outputs"])
            for f in summary["folds"]
        ],
        subtitle="Same targets for all five methods; minimum 100",
    )
    primary = aggregate["paired_differences"][PRIMARY]
    result = (
        f"History minus current-window macro MAE: "
        f"{primary['macro_mae_difference_rad'] * 180 / np.pi:+.6f} degrees. "
        "Negative means lower history error."
        if primary
        else "No supported folds; primary comparison unavailable."
    )
    lines = [
        "# Causal history study",
        "",
        f"Supported folds: {aggregate['supported_folds']}/9. {result}",
        "",
        "| Method | Macro MAE, degrees |",
        "| --- | ---: |",
    ]
    lines += [f"| {name} | {value:.3f} |" for name, value in rows]
    if not rows:
        lines += ["| All methods | Unavailable: no supported folds |"]
    lines += [
        "",
        "![Method comparison](method-errors.svg)",
        "",
        "![Common scoring coverage](score-coverage.svg)",
        "",
        "The three ridge models share training rows and scored targets. Current and wide "
        "RMS use alpha 10. History concatenates five 200 ms features spanning 600 ms and "
        "uses effective alpha 50, equivalent to dividing standardized features by sqrt(5) "
        "before alpha-10 fitting. No model or duration is selected from outcomes.",
        "",
        "The fixed 10-second prefix supplies the prefix-median constant only. Scoring "
        "follows a 600 ms embargo with complete histories beginning after the prefix. "
        "All feature inputs are causal. The history model has more parameters, so "
        "differences do not isolate temporal order from capacity.",
        "",
        "This exploratory study uses already inspected data from one person/session. "
        "Original validation and test files are excluded. Common histories change "
        "eligibility relative to earlier studies. No population inference, optimal "
        "duration, physiological latency, live control, or full-dive result is established.",
        "",
        "summary.json records every fold, coverage, fitted dimensions and effective "
        "alphas, paired metrics, integrity digests, and resources. Raw signals, per-sample "
        "labels/predictions, and coefficients are excluded. Dataset attribution and "
        "noncommercial terms are in docs/datasets/emg2pose.md.",
        "",
    ]
    (output / "report.md").write_text("\n".join(lines), encoding="utf-8")


def run(manifest_path, data_dir, output, study_path):
    started = time.perf_counter()
    cpu_started = time.process_time()
    source = validate_protocol(json.loads(manifest_path.read_text(encoding="utf-8")))
    study = validate_study(json.loads(study_path.read_text(encoding="utf-8")))
    if source["protocol_id"] != study["source_protocol_id"]:
        raise ValueError("Source protocol does not match history study")
    if output.exists():
        raise ValueError("Output directory already exists; choose a new history directory")
    entries = [e for e in source["files"] if e["split"] == "train"]
    if len(entries) != 9:
        raise ValueError("History requires exactly nine original training recordings")
    if sum((data_dir / e["filename"]).stat().st_size for e in entries) > 5 * 1024**3:
        raise ValueError("History recordings exceed the disk cap")
    records = [load_record(data_dir, e) for e in entries]
    for record in records:
        validate_time(record["time"], record["entry"]["filename"])
    tables = [make_table(record) for record in records]
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
        "integrity_definition": "SHA-256 identifies each model fit, training and prefix constants, "
        "common scoring masks, and each method's predictions without publishing per-sample data.",
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
        raise ValueError("History exceeded the 15-minute wall-clock limit")
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
    print(f"Completed history study: {output}; {aggregate['supported_folds']}/9 supported folds")
    return summary
