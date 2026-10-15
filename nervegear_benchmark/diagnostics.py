import hashlib
import json
import os
import platform
import time

import h5py
import numpy as np

from . import __version__, core
from .pipeline import (
    coverage,
    join_training,
    load_record,
    peak_memory_mib,
    table,
    validate_protocol,
)
from .report import bar_chart


def error_stats(prediction, target):
    result = core.errors(prediction, target)
    residual = prediction - target
    mean = residual.mean(axis=0)
    variance = residual.var(axis=0)
    mse = np.mean(residual**2, axis=0)
    if not np.allclose(mse, mean**2 + variance, rtol=1e-10, atol=1e-12):
        raise ValueError("Residual MSE decomposition failed verification")
    return {
        **result,
        "mse_rad2": float(mse.mean()),
        "rmse_rad": float(np.sqrt(mse.mean())),
        "per_joint_mse_rad2": mse.tolist(),
        "residual_mean_rad": mean.tolist(),
        "residual_variance_rad2": variance.tolist(),
    }


def aggregate_stats(records):
    mse = float(np.mean([r["mse_rad2"] for r in records]))
    return {**core.aggregate(records), "macro_mse_rad2": mse, "macro_rmse_rad": float(np.sqrt(mse))}


def pose_stats(target):
    median = np.median(target, axis=0)
    return {
        "mean_rad": target.mean(axis=0).tolist(),
        "std_rad": target.std(axis=0).tolist(),
        "iqr_rad": (np.quantile(target, 0.75, axis=0) - np.quantile(target, 0.25, axis=0)).tolist(),
        "own_median_mae_rad": float(np.abs(target - median).mean()),
        "own_median_per_joint_mae_rad": np.abs(target - median).mean(axis=0).tolist(),
        "interpretation": "Descriptive within-recording lower bound for constant predictors; "
        "uses this recording labels and is not a fair deployed baseline.",
    }


def feature_reference(train):
    scale = train.std(axis=0)
    constant = scale == 0
    scale[constant] = 1
    return {
        "mean": train.mean(axis=0).tolist(),
        "scale": scale.tolist(),
        "constant_channels": constant.tolist(),
        "p01": np.quantile(train, 0.01, axis=0).tolist(),
        "p99": np.quantile(train, 0.99, axis=0).tolist(),
    }


def feature_shift(x, reference):
    z = (x - reference["mean"]) / reference["scale"]
    outside = (x < reference["p01"]) | (x > reference["p99"])
    return {
        "standardized_mean": z.mean(axis=0).tolist(),
        "standardized_std": z.std(axis=0).tolist(),
        "fraction_abs_z_gt_3": (np.abs(z) > 3).mean(axis=0).tolist(),
        "fraction_outside_train_p01_p99": outside.mean(axis=0).tolist(),
    }


def range_stats(prediction, target, train):
    thresholds = {
        "training_min_max": (train.min(axis=0), train.max(axis=0)),
        "training_p01_p99": (np.quantile(train, 0.01, axis=0), np.quantile(train, 0.99, axis=0)),
    }
    result = {}
    error = np.abs(prediction - target)
    for name, (lower, upper) in thresholds.items():
        outside = (prediction < lower) | (prediction > upper)
        target_outside = (target < lower) | (target > upper)
        result[name] = {
            "lower_rad": lower.tolist(),
            "upper_rad": upper.tolist(),
            "prediction_fraction_outside_per_joint": outside.mean(axis=0).tolist(),
            "target_fraction_outside_per_joint": target_outside.mean(axis=0).tolist(),
            "outside_prediction_angle_elements": int(outside.sum()),
            "inside_prediction_angle_elements": int((~outside).sum()),
            "outside_prediction_mae_rad": float(error[outside].mean()) if outside.any() else None,
            "inside_prediction_mae_rad": float(error[~outside].mean())
            if (~outside).any()
            else None,
        }
    return result


def solver_stats(x, y, alpha, evaluation=None):
    model = core.fit_ridge(x, y, alpha)
    z = (x - model.mean) / model.scale
    singular_values = np.linalg.svd(z, compute_uv=False)
    rank = int(np.linalg.matrix_rank(z))
    singular = rank < x.shape[1]
    augmented_x = np.vstack([z, np.sqrt(alpha) * np.eye(x.shape[1])])
    augmented_y = np.vstack([y - model.target_mean, np.zeros((x.shape[1], y.shape[1]))])
    coefficients = np.linalg.lstsq(augmented_x, augmented_y, rcond=None)[0]
    values = x if evaluation is None else np.vstack([x, evaluation])
    independent = ((values - model.mean) / model.scale) @ coefficients + model.target_mean
    original = model.predict(values)
    if not np.allclose(original, independent, rtol=1e-7, atol=1e-9):
        raise ValueError("Independent augmented least-squares predictions disagree")
    return {
        "singular_values": singular_values.tolist(),
        "rank": rank,
        "singular": singular,
        "feature_condition_number": None
        if singular
        else float(singular_values[0] / singular_values[-1]),
        "regularized_condition_number": float(np.linalg.cond(z.T @ z + alpha * np.eye(x.shape[1]))),
        "coefficient_l2_norm": float(np.linalg.norm(model.coefficients)),
        "independent_prediction_max_abs_difference_rad": float(
            np.max(np.abs(independent - original))
        ),
    }


def require_scored(item):
    if not item["eligible"].any():
        counts = coverage([item])
        raise ValueError(f"{item['entry']['filename']}: no scored outputs; {counts}")


def score_split(tables, predictor, primary=False):
    records = []
    for item in tables:
        mask = item["eligible"]
        result = error_stats(predictor(item["x"][mask]), item["y"][mask])
        if not primary:
            for key in ["per_joint_mse_rad2", "residual_mean_rad", "residual_variance_rad2"]:
                del result[key]
        records.append(
            {
                "filename": item["entry"]["filename"],
                "recording": item["entry"]["recording"],
                "stage": item["entry"]["stage"],
                **result,
            }
        )
    return {"records": records, "aggregate": aggregate_stats(records)}


def write_report(summary, output):
    degrees = 180 / np.pi
    primary = next(c for c in summary["configurations"] if c["primary"])
    rows = []
    for name, values in [*summary["baselines"].items(), ("Ridge 200 ms", primary["scores"])]:
        for split in ["train", "validation"]:
            rows.append((f"{name} {split}", values[split]["aggregate"]["macro_mae_rad"] * degrees))
    bar_chart(output / "fit-gap.svg", "Training and validation fit", rows)
    reference = summary["feature_distributions"]["400"]
    shifts = [
        (f"Recording {r['recording']}", max(abs(v) for v in r["standardized_mean"]))
        for r in reference["records"]
        if r["split"] == "validation"
    ]
    bar_chart(
        output / "feature-shift.svg",
        "Validation feature mean shift",
        shifts,
        subtitle="Largest absolute training-standardized channel mean; 200 ms history",
    )
    joint_rows = [
        (f"Joint {i}", value * degrees)
        for i, value in enumerate(
            primary["scores"]["validation"]["aggregate"]["macro_per_joint_mae_rad"]
        )
    ]
    bar_chart(
        output / "joint-errors.svg",
        "Primary model validation errors by joint",
        joint_rows,
        subtitle="Equal recording weight; angular MAE in degrees; audited joint order",
    )
    lines = [
        "# Training and validation diagnostics",
        "",
        "This exploratory study loads only the nine training and three validation recordings. "
        "The v1 test outcomes are already known; this is not a new blind evaluation.",
        "",
        "| Method and partition | Macro MAE, degrees |",
        "| --- | ---: |",
    ]
    lines += [f"| {name} | {value:.3f} |" for name, value in rows]
    lines += [
        "",
        "![Training and validation](fit-gap.svg)",
        "",
        "![Feature shift](feature-shift.svg)",
        "",
        "![Joint errors](joint-errors.svg)",
        "",
        "summary.json contains all nine fixed configurations, coverage, per-recording and "
        "per-joint scores, residual decompositions, target dispersion, feature distributions, "
        "prediction ranges, and independent solver checks.",
        "",
        "Squared-error fitting and MAE evaluation are different objectives. "
        "Within-recording median errors use that recording labels and are descriptive "
        "lower bounds for constants, not fair deployed baselines. Range and distribution "
        "thresholds are descriptive, not physiological limits or statistical significance tests.",
        "",
        "These observational diagnostics cannot identify a unique biological cause. "
        "They do not establish new-user generalization, live control, perception, or full dive.",
        "",
        "Data attribution: emg2pose, Meta and its authors. See the repository dataset "
        "card for source and noncommercial license terms. Raw samples and per-sample "
        "predictions are excluded.",
        "",
    ]
    (output / "report.md").write_text("\n".join(lines), encoding="utf-8")


def run(manifest_path, data_dir, output):
    started = time.perf_counter()
    cpu_started = time.process_time()
    protocol = validate_protocol(json.loads(manifest_path.read_text(encoding="utf-8")))
    if output.exists():
        raise ValueError("Output directory already exists; choose a new diagnostic directory")
    entries = [entry for entry in protocol["files"] if entry["split"] in ["train", "validation"]]
    if len(entries) != 12:
        raise ValueError("Diagnostics require nine training and three validation entries")
    if sum((data_dir / entry["filename"]).stat().st_size for entry in entries) > 5 * 1024**3:
        raise ValueError("Diagnostic recordings exceed the disk cap")
    records = [load_record(data_dir, entry) for entry in entries]
    cached = {
        h: {
            split: [table(r, h) for r in records if r["entry"]["split"] == split]
            for split in ["train", "validation"]
        }
        for h in protocol["history_samples"]
    }
    for grouped in cached.values():
        for items in grouped.values():
            for item in items:
                require_scored(item)
    _, train_y = join_training(cached[400]["train"])
    baselines = {}
    for name, pose in [("Mean", train_y.mean(axis=0)), ("Median", np.median(train_y, axis=0))]:
        baselines[name] = {
            split: score_split(items, lambda x, pose=pose: np.broadcast_to(pose, (len(x), 20)))
            for split, items in cached[400].items()
        }
    configurations = []
    feature_distributions = {}
    primary_model = None
    for history, grouped in cached.items():
        x, y = join_training(grouped["train"])
        val_x, _ = join_training(grouped["validation"])
        reference = feature_reference(x)
        feature_distributions[str(history)] = {"training_reference": reference, "records": []}
        for split, items in grouped.items():
            for item in items:
                feature_distributions[str(history)]["records"].append(
                    {
                        "recording": item["entry"]["recording"],
                        "split": split,
                        **feature_shift(item["x"][item["eligible"]], reference),
                    }
                )
        for alpha in protocol["ridge_alpha_candidates"]:
            primary = history == 400 and alpha == 10
            model = core.fit_ridge(x, y, alpha)
            if primary:
                primary_model = model
            configurations.append(
                {
                    "history": history,
                    "alpha": alpha,
                    "primary": primary,
                    "scores": {
                        split: score_split(items, model.predict, primary)
                        for split, items in grouped.items()
                    },
                    "solver": solver_stats(x, y, alpha, val_x),
                }
            )
    poses = []
    ranges = []
    for split, items in cached[400].items():
        for item in items:
            mask = item["eligible"]
            poses.append(
                {
                    "recording": item["entry"]["recording"],
                    "split": split,
                    "stage": item["entry"]["stage"],
                    **pose_stats(item["y"][mask]),
                }
            )
            ranges.append(
                {
                    "recording": item["entry"]["recording"],
                    "split": split,
                    **range_stats(primary_model.predict(item["x"][mask]), item["y"][mask], train_y),
                }
            )
    config = {
        "schema_version": 1,
        "diagnostic_id": "rms-ridge-train-validation-v1",
        "base_protocol_sha256": hashlib.sha256(
            json.dumps(protocol, sort_keys=True, separators=(",", ":"), allow_nan=False).encode(
                "utf-8"
            )
        ).hexdigest(),
        "histories": [100, 200, 400],
        "alphas": [0.1, 1, 10],
        "primary": {"history": 400, "alpha": 10},
        "replacement_model_selected": False,
        "feature_abs_z_threshold": 3,
        "quantiles": [0.01, 0.99],
        "solver_prediction_rtol": 1e-7,
        "solver_prediction_atol": 1e-9,
        "files": entries,
        "test_recordings_excluded": [13, 14, 15],
    }
    summary = {
        "schema_version": 1,
        "config": config,
        "diagnostic_config_sha256": hashlib.sha256(
            json.dumps(config, sort_keys=True, separators=(",", ":"), allow_nan=False).encode(
                "utf-8"
            )
        ).hexdigest(),
        "loaded_files": entries,
        "coverage": {split: coverage(items) for split, items in cached[400].items()},
        "baselines": baselines,
        "configurations": configurations,
        "feature_distributions": feature_distributions,
        "target_dispersion": poses,
        "prediction_ranges": ranges,
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
            "peak_process_memory_mib": peak_memory_mib(),
            "cpu_seconds": time.process_time() - cpu_started,
            "analysis_wall_seconds": time.perf_counter() - started,
            "limit_seconds": 900,
        },
    }
    payload = json.dumps(summary, indent=2, allow_nan=False) + "\n"
    if time.perf_counter() - started >= 900:
        raise ValueError("Diagnostics exceeded the 15-minute wall-clock limit")
    output.mkdir(parents=True, exist_ok=False)
    (output / "summary.json").write_text(payload, encoding="utf-8")
    (output / "diagnostic-config.json").write_text(
        json.dumps(config, indent=2) + "\n", encoding="utf-8"
    )
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
    print(f"Completed diagnostics: {output}; loaded 12 training/validation files")
    return summary
