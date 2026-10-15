import hashlib
import json
import os
import platform
import time

import h5py
import numpy as np

from . import __version__, core
from .diagnostics import aggregate_stats, error_stats
from .pipeline import (
    coverage,
    join_training,
    load_record,
    peak_memory_mib,
    table,
    validate_protocol,
)
from .report import bar_chart

METHODS = [
    "ridge",
    "calibrated_ridge",
    "train_mean",
    "train_median",
    "prefix_mean",
    "prefix_median",
]


def fingerprint(value):
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")
    ).hexdigest()


def arrays_digest(values):
    return hashlib.sha256(
        b"".join(np.asarray(v, dtype="<f8").tobytes() for v in values)
    ).hexdigest()


def partition(item, source_time):
    elapsed = source_time - source_time[0]
    ends = item["ends"]
    prefix = elapsed[ends] < 10.0
    score = (elapsed[ends] >= 10.2) & (elapsed[ends - 399] >= 10.0)
    regions = {"prefix": prefix, "embargo": ~prefix & ~score, "score": score}
    counts = {}
    masks = {}
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


def validate_time(source_time, filename):
    if (
        len(source_time) == 0
        or not np.isfinite(source_time).all()
        or not (np.diff(source_time) > 0).all()
    ):
        raise ValueError(f"{filename}: timestamps must be finite and strictly increasing")


def fit_fold(tables, held_recording):
    training = [t for t in tables if t["entry"]["recording"] != held_recording]
    if not training or not any(t["eligible"].any() for t in training):
        raise ValueError(f"Fold {held_recording}: no eligible fitting outputs")
    x, y = join_training(training)
    return {
        "model": core.fit_ridge(x, y, 10.0),
        "train_mean": y.mean(axis=0),
        "train_median": np.median(y, axis=0),
        "training_outputs": len(y),
        "training_recordings": [t["entry"]["recording"] for t in training],
    }


def calibration_state(fit, prefix_x, prefix_y):
    prediction = fit["model"].predict(prefix_x)
    core.errors(prediction, prefix_y)
    state = {
        "offset": np.mean(prefix_y - prediction, axis=0),
        "prefix_mean": prefix_y.mean(axis=0),
        "prefix_median": np.median(prefix_y, axis=0),
    }
    if not all(np.isfinite(v).all() for v in state.values()):
        raise ValueError("Nonfinite calibration state")
    return state


def predict_methods(fit, state, score_x):
    prediction = fit["model"].predict(score_x)
    result = {"ridge": prediction, "calibrated_ridge": prediction + state["offset"]}
    for name in ["train_mean", "train_median", "prefix_mean", "prefix_median"]:
        pose = fit[name] if name.startswith("train_") else state[name]
        result[name] = np.broadcast_to(pose, prediction.shape)
    return result


def aggregate_folds(folds):
    supported = [f for f in folds if f["status"] == "supported"]
    result = {
        "supported_folds": len(supported),
        "unsupported_folds": len(folds) - len(supported),
        "methods": {
            name: aggregate_stats([f["scores"][name] for f in supported]) if supported else None
            for name in METHODS
        },
        "paired_differences": {},
    }
    for baseline in ["ridge", "prefix_median"]:
        key = f"calibrated_ridge_minus_{baseline}"
        if not supported:
            result["paired_differences"][key] = None
            continue
        differences = [
            f["scores"]["calibrated_ridge"]["mae_rad"] - f["scores"][baseline]["mae_rad"]
            for f in supported
        ]
        result["paired_differences"][key] = {
            "macro_mae_difference_rad": float(np.mean(differences)),
            "improved": sum(v < -1e-12 for v in differences),
            "tied": sum(abs(v) <= 1e-12 for v in differences),
            "worsened": sum(v > 1e-12 for v in differences),
            "folds": [
                {"recording": f["recording"], "difference_rad": value}
                for f, value in zip(supported, differences, strict=True)
            ],
        }
    return result


def validate_study(study):
    expected = {
        "schema_version": 1,
        "study_id": "fixed-prefix-calibration-v1",
        "source_protocol_id": "emg2pose-starter-left-pilot-v1",
        "fold_recordings": list(range(1, 10)),
        "history_samples": 400,
        "first_output_sample_index": 399,
        "output_stride_samples": 40,
        "ridge_alpha": 10.0,
        "prefix_seconds": 10.0,
        "embargo_seconds": 0.2,
        "minimum_calibration_outputs": 25,
        "minimum_scored_outputs": 1,
        "tie_tolerance_rad": 1e-12,
        "methods": METHODS,
        "primary_comparisons": [
            "calibrated_ridge_minus_ridge",
            "calibrated_ridge_minus_prefix_median",
        ],
        "maximum_threads": 2,
        "maximum_run_seconds": 900,
    }
    for key, value in expected.items():
        if study.get(key) != value:
            raise ValueError(f"Unsupported calibration setting: {key}")
    if set(study) != set(expected) | {"scope", "label_access"}:
        raise ValueError("Unexpected calibration protocol fields")
    return study


def evaluate_fold(tables, record, item):
    recording = record["entry"]["recording"]
    masks, counts = partition(item, record["time"])
    result = {
        "recording": recording,
        "stage": record["entry"]["stage"],
        "filename": record["entry"]["filename"],
        "partitions": counts,
    }
    reasons = []
    if counts["prefix"]["eligible_outputs"] < 25:
        reasons.append("Fewer than 25 eligible prefix labels")
    if counts["score"]["eligible_outputs"] < 1:
        reasons.append("No eligible scored outputs after the fixed embargo")
    if reasons:
        return {**result, "status": "unsupported", "reasons": reasons, "scores": None}
    fit = fit_fold(tables, recording)
    model = fit["model"]
    initial_digest = arrays_digest(
        [
            model.mean,
            model.scale,
            model.target_mean,
            model.coefficients,
            fit["train_mean"],
            fit["train_median"],
        ]
    )
    state = calibration_state(fit, item["x"][masks["prefix"]], item["y"][masks["prefix"]])
    predictions = predict_methods(fit, state, item["x"][masks["score"]])
    scores = {}
    for name in METHODS:
        metrics = error_stats(predictions[name], item["y"][masks["score"]])
        for key in ["per_joint_mse_rad2", "residual_mean_rad", "residual_variance_rad2"]:
            del metrics[key]
        scores[name] = metrics
    return {
        **result,
        "status": "supported",
        "training_recordings": fit["training_recordings"],
        "training_outputs": fit["training_outputs"],
        "initial_fit_sha256": initial_digest,
        "calibration_state_sha256": arrays_digest(list(state.values())),
        "prediction_sha256": arrays_digest([predictions[name] for name in METHODS]),
        "scores": scores,
    }


def write_report(summary, output):
    degrees = 180 / np.pi
    aggregate = summary["aggregate"]
    supported = aggregate["supported_folds"]
    rows = [
        (name, values["macro_mae_rad"] * degrees)
        for name, values in aggregate["methods"].items()
        if values is not None
    ]
    if rows:
        bar_chart(
            output / "method-errors.svg",
            "Fixed-prefix calibration comparison",
            rows,
            subtitle="Equal supported-fold weight; MAE in degrees; one person/session",
        )
    else:
        bar_chart(
            output / "method-errors.svg",
            "No supported calibration folds",
            [("Unsupported folds", len(summary["folds"]))],
            subtitle="Counts only; all scores unavailable",
        )
    labels = [
        (f"Recording {f['recording']}", f["partitions"]["prefix"]["eligible_outputs"])
        for f in summary["folds"]
    ]
    bar_chart(
        output / "prefix-labels.svg",
        "Valid labels in the fixed 10-second prefix",
        labels,
        subtitle="Eligible labeled output timestamps, shared by calibrated methods; minimum 25",
    )
    lines = [
        "# Fixed-prefix calibration study",
        "",
        f"Supported folds: {supported}/9. Original validation and test recordings are excluded.",
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
        "![Prefix labels](prefix-labels.svg)",
        "",
        "The model uses 400-sample history and ridge alpha 10. Each fold fits only the other "
        "eight original training recordings. A fixed 10-second prefix calibrates the output "
        "intercept. Scoring starts after the 200 ms embargo, with no prefix-overlapping history.",
        "",
        "Prefix mean and prefix median receive the same labels as calibrated ridge. "
        "These references are supplied by the public dataset; this is not a hardware-free "
        "live calibration method. No later reference labels enter calibration.",
        "",
        "This exploratory study uses already inspected data from one person/session. "
        "Folds overlap in their training data. No biological independence, new-user evidence, "
        "live control, perception, or full-dive result is established.",
        "",
        "summary.json records all folds, unsupported reasons, coverage, per-joint errors, "
        "paired comparisons, integrity fingerprints, and resources. Data attribution and "
        "noncommercial terms are in docs/datasets/emg2pose.md. No raw samples, per-sample "
        "predictions, or model coefficients are published.",
        "",
    ]
    (output / "report.md").write_text("\n".join(lines), encoding="utf-8")


def run(manifest_path, data_dir, output, study_path):
    started = time.perf_counter()
    cpu_started = time.process_time()
    source = validate_protocol(json.loads(manifest_path.read_text(encoding="utf-8")))
    study = validate_study(json.loads(study_path.read_text(encoding="utf-8")))
    if source["protocol_id"] != study["source_protocol_id"]:
        raise ValueError("Source protocol does not match calibration study")
    if output.exists():
        raise ValueError("Output directory already exists; choose a new calibration directory")
    entries = [e for e in source["files"] if e["split"] == "train"]
    if len(entries) != 9:
        raise ValueError("Calibration requires exactly nine original training recordings")
    if sum((data_dir / e["filename"]).stat().st_size for e in entries) > 5 * 1024**3:
        raise ValueError("Calibration recordings exceed the disk cap")
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
        "integrity_definition": "SHA-256 parameter and prediction digests prove repeatability "
        "without publishing coefficients or per-sample predictions.",
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
        raise ValueError("Calibration exceeded the 15-minute wall-clock limit")
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
    print(f"Completed calibration: {output}; {aggregate['supported_folds']}/9 supported folds")
    return summary
