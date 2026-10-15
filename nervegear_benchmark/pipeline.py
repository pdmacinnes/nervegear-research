import hashlib
import json
import os
import platform
import time
from pathlib import Path

import h5py
import numpy as np

from . import __version__, core
from .report import write_report

CONDITIONS = ["clean", "drop_channel_0", "gain_0.5", "gain_1.5", "noise_0.1"]


def validate_protocol(protocol):
    expected = {
        "schema_version": 1,
        "reference_pose_input": False,
        "joint_indices": list(range(20)),
        "input_channels": list(range(16)),
        "nominal_sample_rate_hz": 2000,
        "prediction_horizon_ms": 0,
        "history_ms": [50, 100, 200],
        "history_samples": [100, 200, 400],
        "output_stride_samples": 40,
        "first_output_sample_index": 399,
        "timestamp_step_nominal_bounds": [0.5, 1.5],
        "software_delay_ms": [0, 20, 40, 100],
        "timing_repeats": 5,
        "ridge_alpha_candidates": [0.1, 1.0, 10.0],
        "target_units": "radians",
    }
    for key, value in expected.items():
        if protocol.get(key) != value:
            raise ValueError(f"Unsupported protocol setting: {key}")
    if protocol.get("resource_limits") != {
        "gpu_required": False,
        "paid_services_required": False,
        "maximum_threads": 2,
        "single_reproduction_run_minutes": 15,
        "runtime_limit_status": (
            "Provisional; measure the baseline first, and revise explicitly if needed."
        ),
    }:
        raise ValueError("Unsupported resource limits")
    robustness = protocol.get("robustness_proposal", {})
    if (
        robustness.get("seed") != 0
        or robustness.get("channel_dropout") != [0]
        or robustness.get("global_gain") != [0.5, 1.5]
        or robustness.get("additive_gaussian_noise_std_fraction_of_train_channel_rms") != [0.1]
    ):
        raise ValueError("Unsupported robustness settings")
    files = protocol["files"]
    names = [f["filename"] for f in files]
    if len(set(names)) != len(names):
        raise ValueError("Protocol contains duplicate filenames across recordings or splits")
    if len(files) != 15 or sorted(f["recording"] for f in files) != list(range(1, 16)):
        raise ValueError("Pilot requires recordings 1-15 exactly once")
    prefixes = set()
    for entry in files:
        name = entry["filename"]
        if Path(name).name != name or "\\" in name or not name.endswith("_left.hdf5"):
            raise ValueError(f"Unsafe or unsupported filename: {name}")
        prefixes.add(name.split("-recording-")[0])
        recording = entry["recording"]
        split = "train" if recording <= 9 else "validation" if recording <= 12 else "test"
        if entry["split"] != split or entry["source_split"] != "val":
            raise ValueError("Unexpected split membership or source split")
        if not name.endswith(f"-recording-{recording}_left.hdf5"):
            raise ValueError("Recording number does not match filename")
        digest = entry["sha256"]
        if len(digest) != 64 or any(c not in "0123456789abcdef" for c in digest):
            raise ValueError("Invalid SHA-256 digest")
    if len(prefixes) != 1:
        raise ValueError("The pilot requires one source session")
    return protocol


def select_candidate(candidates):
    return min(candidates, key=lambda item: item[1])[0]


def sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def load_record(root, entry):
    path = (root / entry["filename"]).resolve()
    if not path.is_relative_to(root.resolve()):
        raise ValueError("Recording path escapes data directory")
    if sha256(path) != entry["sha256"]:
        raise ValueError(f"Recording checksum mismatch: {entry['filename']}")
    with h5py.File(path, "r") as stream:
        data = stream["emg2pose/timeseries"][:]
    if set(data.dtype.names or ()) != {
        "time",
        "joint_angles",
        "emg",
    }:
        raise ValueError("Unexpected HDF5 field schema")
    if data["emg"].shape != (len(data), 16) or data["joint_angles"].shape != (len(data), 20):
        raise ValueError("Unexpected EMG or joint-angle shape")
    return {
        "entry": entry,
        "time": data["time"].copy(),
        "emg": data["emg"].copy(),
        "target": data["joint_angles"].copy(),
    }


def table(record, history, emg=None):
    ends, x, valid = core.features(
        record["emg"] if emg is None else emg, record["time"], history, 40, 399, 400
    )
    y = record["target"][ends].astype(np.float64)
    reference = core.reference_valid(y)
    return {
        "ends": ends,
        "x": x,
        "y": y,
        "input_valid": valid,
        "reference_valid": reference,
        "eligible": valid & reference,
        "entry": record["entry"],
    }


def coverage(tables):
    totals = {
        "candidate_outputs": 0,
        "invalid_input_outputs": 0,
        "invalid_reference_outputs": 0,
        "scored_outputs": 0,
    }
    records = []
    for item in tables:
        counts = {
            "candidate_outputs": len(item["ends"]),
            "invalid_input_outputs": int((~item["input_valid"]).sum()),
            "invalid_reference_outputs": int(
                (item["input_valid"] & ~item["reference_valid"]).sum()
            ),
            "scored_outputs": int(item["eligible"].sum()),
        }
        for key in totals:
            totals[key] += counts[key]
        records.append({"filename": item["entry"]["filename"], **counts})
    totals["records"] = records
    totals["scored_fraction"] = totals["scored_outputs"] / max(1, totals["candidate_outputs"])
    return totals


def score(tables, predictor):
    records = []
    for item in tables:
        mask = item["eligible"]
        result = core.errors(predictor(item["x"][mask]), item["y"][mask])
        records.append(
            {"filename": item["entry"]["filename"], "stage": item["entry"]["stage"], **result}
        )
    return {"records": records, "aggregate": core.aggregate(records)}


def join_training(tables):
    return (
        np.concatenate([t["x"][t["eligible"]] for t in tables]),
        np.concatenate([t["y"][t["eligible"]] for t in tables]),
    )


def delayed_scores(tables, model):
    grouped = {delay: [] for delay in [0, 20, 40, 100]}
    for item in tables:
        n = len(item["ends"])
        current = np.arange(5, n)
        paired = item["eligible"][current].copy()
        for lag in [0, 1, 2, 5]:
            paired &= item["input_valid"][current - lag]
        current = current[paired]
        for delay in grouped:
            lag = delay // 20
            result = core.errors(model.predict(item["x"][current - lag]), item["y"][current])
            grouped[delay].append({"filename": item["entry"]["filename"], **result})
    return {
        str(delay): {"records": values, "aggregate": core.aggregate(values)}
        for delay, values in grouped.items()
    }


def percentiles_ns(values):
    return {f"p{p}_ms": float(np.percentile(values, p) / 1e6) for p in [50, 95, 99]}


def measure_timing(records, model, history):
    passes = []
    checksum = 0.0
    for repeat in range(5):
        feature_ns, predict_ns, total_ns = [], [], []
        for record in records:
            item = table(record, history)
            ends = item["ends"][item["eligible"]]
            # Warm each recording before timing complete, unbatched trailing windows.
            warm = np.log1p(np.sqrt(np.mean(record["emg"][:history].astype(float) ** 2, axis=0)))[
                None
            ]
            for _ in range(20):
                model.predict(warm)
            for end in ends:
                start = time.perf_counter_ns()
                window = record["emg"][end - history + 1 : end + 1].astype(np.float64)
                x = np.log1p(np.sqrt(np.mean(window * window, axis=0)))[None]
                middle = time.perf_counter_ns()
                prediction = model.predict(x)
                finish = time.perf_counter_ns()
                checksum += float(prediction.sum())
                feature_ns.append(middle - start)
                predict_ns.append(finish - middle)
                total_ns.append(finish - start)
        passes.append(
            {
                "repeat": repeat,
                "outputs": len(total_ns),
                "feature": percentiles_ns(feature_ns),
                "prediction": percentiles_ns(predict_ns),
                "combined": percentiles_ns(total_ns),
            }
        )
    return {
        "passes": passes,
        "prediction_sum_checksum": checksum,
        "definition": "Unbatched trailing-window feature extraction plus prediction; "
        "excludes HDF5 I/O, corruption, eligibility, replay scheduling, "
        "output serialization, and simulated waiting. Five warm repeated passes.",
        "lookahead_ms": 0,
        "update_period_ms": 20,
        "warmup_samples": 400,
        "replay_scheduling": "No wall-clock stream scheduler; offline iteration only.",
    }


def peak_memory_mib():
    if os.name == "nt":
        import ctypes
        from ctypes import wintypes

        class Counters(ctypes.Structure):
            _fields_ = [("cb", wintypes.DWORD), ("faults", wintypes.DWORD)] + [
                (name, ctypes.c_size_t)
                for name in [
                    "peak",
                    "working",
                    "paged_peak",
                    "paged",
                    "nonpaged_peak",
                    "nonpaged",
                    "pagefile",
                    "pagefile_peak",
                ]
            ]

        counters = Counters()
        counters.cb = ctypes.sizeof(counters)
        kernel = ctypes.WinDLL("kernel32", use_last_error=True)
        kernel.GetCurrentProcess.restype = wintypes.HANDLE
        psapi = ctypes.WinDLL("psapi", use_last_error=True)
        psapi.GetProcessMemoryInfo.argtypes = [wintypes.HANDLE, ctypes.c_void_p, wintypes.DWORD]
        if psapi.GetProcessMemoryInfo(
            kernel.GetCurrentProcess(), ctypes.byref(counters), counters.cb
        ):
            return counters.peak / 1024**2
        return None
    import resource

    value = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return value / (1024**2 if platform.system() == "Darwin" else 1024)


def run(manifest_path, data_dir, output):
    started = time.perf_counter()
    cpu_started = time.process_time()
    protocol = validate_protocol(json.loads(manifest_path.read_text(encoding="utf-8")))
    if output.exists():
        raise ValueError("Output directory already exists; choose a new run directory")
    if sum((data_dir / f["filename"]).stat().st_size for f in protocol["files"]) > 5 * 1024**3:
        raise ValueError("Declared recordings exceed disk cap")
    records = [load_record(data_dir, entry) for entry in protocol["files"]]
    grouped = {
        split: [r for r in records if r["entry"]["split"] == split]
        for split in ["train", "validation", "test"]
    }
    cached = {
        h: {split: [table(r, h) for r in values] for split, values in grouped.items()}
        for h in protocol["history_samples"]
    }
    candidates = []
    models = {}
    validation = []
    for history in protocol["history_samples"]:
        x, y = join_training(cached[history]["train"])
        for alpha in protocol["ridge_alpha_candidates"]:
            model = core.fit_ridge(x, y, alpha)
            result = score(cached[history]["validation"], model.predict)
            key = {"history": history, "alpha": alpha}
            candidates.append((key, result["aggregate"]["macro_mae_rad"]))
            models[(history, alpha)] = model
            validation.append({**key, **result})
    selected = select_candidate(candidates)
    history = selected["history"]
    model = models[(history, selected["alpha"])]
    _, train_y = join_training(cached[history]["train"])
    baselines = {}
    for name, pose in [("mean", train_y.mean(axis=0)), ("median", np.median(train_y, axis=0))]:
        baselines[name] = score(
            cached[history]["test"], lambda x, pose=pose: np.broadcast_to(pose, (len(x), 20))
        )
    count = sum(len(r["emg"]) for r in grouped["train"])
    squares = sum(
        np.where(np.isfinite(r["emg"]), r["emg"], 0).astype(float).__pow__(2).sum(0)
        for r in grouped["train"]
    )
    finite_counts = sum(np.isfinite(r["emg"]).sum(0) for r in grouped["train"])
    train_rms = np.sqrt(squares / np.maximum(finite_counts, 1))
    test = {}
    for condition in CONDITIONS:
        perturbed = [
            table(r, history, core.corrupt(r["emg"], condition, train_rms, 0))
            for r in grouped["test"]
        ]
        for clean, changed in zip(cached[history]["test"], perturbed, strict=True):
            if not np.array_equal(clean["eligible"], changed["eligible"]):
                raise ValueError("Corruption changed paired eligible timestamps")
        test[condition] = score(perturbed, model.predict)
    comparisons = []
    for h in protocol["history_samples"]:
        best = select_candidate([(key, value) for key, value in candidates if key["history"] == h])
        result = score(cached[h]["test"], models[(h, best["alpha"])].predict)
        comparisons.append({**best, **result})
    summary = {
        "schema_version": 1,
        "protocol_id": protocol["protocol_id"],
        "protocol_sha256": hashlib.sha256(
            json.dumps(protocol, sort_keys=True, separators=(",", ":"), allow_nan=False).encode(
                "utf-8"
            )
        ).hexdigest(),
        "protocol_hash_definition": (
            "SHA-256 of parsed JSON, sorted keys, compact separators, UTF-8"
        ),
        "source_commit": protocol["source_commit"],
        "scope": protocol["scope"],
        "reference_pose_input": False,
        "software": {
            "benchmark": __version__,
            "python": platform.python_version(),
            "numpy": np.__version__,
            "h5py": h5py.__version__,
            "platform": platform.system(),
            "machine": platform.machine(),
            "logical_cpu_count": os.cpu_count(),
        },
        "thread_environment": {
            key: os.environ.get(key)
            for key in ["OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "OMP_NUM_THREADS"]
        },
        "selection": selected,
        "validation_candidates": validation,
        "fitted_model_sha256": hashlib.sha256(
            b"".join(
                np.asarray(a, dtype="<f8").tobytes()
                for a in [model.mean, model.scale, model.target_mean, model.coefficients]
            )
        ).hexdigest(),
        "coverage": {split: coverage(values) for split, values in cached[history].items()},
        "baselines": baselines,
        "test": test,
        "history_comparisons": comparisons,
        "delayed_outputs": delayed_scores(cached[history]["test"], model),
        "timing": measure_timing(grouped["test"], model, history),
        "training_raw_samples_for_noise_scale": count,
        "training_duration_seconds": sum(
            float(r["time"][-1] - r["time"][0]) for r in grouped["train"]
        ),
        "unsupported_claims": protocol["unsupported_claims"],
        "resources": {
            "peak_process_memory_mib": peak_memory_mib(),
            "cpu_seconds": time.process_time() - cpu_started,
            "analysis_wall_seconds": time.perf_counter() - started,
            "limit_seconds": 900,
        },
    }
    if summary["resources"]["analysis_wall_seconds"] >= 900:
        raise ValueError("Run exceeded 15-minute wall-clock budget")
    output.mkdir(parents=True, exist_ok=False)
    (output / "protocol.json").write_text(json.dumps(protocol, indent=2) + "\n", encoding="utf-8")
    (output / "summary.json").write_text(
        json.dumps(summary, indent=2, allow_nan=False) + "\n", encoding="utf-8"
    )
    write_report(summary, output)
    elapsed = time.perf_counter() - started
    (output / "completion.json").write_text(
        json.dumps(
            {"complete": True, "wall_seconds_including_outputs": elapsed, "error_count": 0},
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    print(f"Completed: {output}; selected {history / 2:g} ms, alpha={selected['alpha']}")
    return summary
