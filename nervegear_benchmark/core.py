from dataclasses import dataclass

import numpy as np


def features(emg, time, history, stride, first, common_history):
    emg = np.asarray(emg, dtype=np.float64)
    ends = np.arange(first, len(emg), stride)
    starts = ends - common_history + 1
    row_bad = ~np.isfinite(emg).all(axis=1) | ~np.isfinite(time)
    step = np.diff(time)
    step_bad = np.r_[False, ~np.isfinite(step) | (step < 0.00025) | (step > 0.00075)]
    rows = np.r_[0, np.cumsum(row_bad)]
    steps = np.r_[0, np.cumsum(step_bad)]
    valid = (rows[ends + 1] - rows[starts]) == 0
    valid &= (steps[ends + 1] - steps[starts + 1]) == 0
    clean = np.where(np.isfinite(emg), emg, 0)
    squares = np.vstack([np.zeros(emg.shape[1]), np.cumsum(clean * clean, axis=0)])
    power = (squares[ends + 1] - squares[ends - history + 1]) / history
    x = np.log1p(np.sqrt(np.maximum(power, 0)))
    x[~valid] = np.nan
    return ends, x, valid


def reference_valid(y):
    return np.isfinite(y).all(axis=1) & ~np.isclose(y, 0).all(axis=1)


@dataclass
class Ridge:
    mean: np.ndarray
    scale: np.ndarray
    target_mean: np.ndarray
    coefficients: np.ndarray

    def predict(self, x):
        return ((x - self.mean) / self.scale) @ self.coefficients + self.target_mean


def fit_ridge(x, y, alpha):
    mean = x.mean(axis=0)
    scale = x.std(axis=0)
    scale[scale == 0] = 1
    z = (x - mean) / scale
    target_mean = y.mean(axis=0)
    coefficients = np.linalg.solve(z.T @ z + alpha * np.eye(x.shape[1]), z.T @ (y - target_mean))
    return Ridge(mean, scale, target_mean, coefficients)


def errors(prediction, target):
    if prediction.shape != target.shape or len(target) == 0:
        raise ValueError("No scored outputs or mismatched prediction/target shapes")
    if not np.isfinite(prediction).all() or not np.isfinite(target).all():
        raise ValueError("Scored predictions and targets must be finite")
    per_joint = np.abs(prediction - target).mean(axis=0)
    return {
        "mae_rad": float(per_joint.mean()),
        "per_joint_mae_rad": per_joint.tolist(),
        "scored_outputs": len(target),
    }


def aggregate(records):
    count = sum(r["scored_outputs"] for r in records)
    return {
        "macro_mae_rad": float(np.mean([r["mae_rad"] for r in records])),
        "sample_weighted_mae_rad": float(
            sum(r["mae_rad"] * r["scored_outputs"] for r in records) / count
        ),
        "macro_per_joint_mae_rad": np.mean(
            [r["per_joint_mae_rad"] for r in records], axis=0
        ).tolist(),
        "scored_outputs": count,
    }


def corrupt(x, condition, train_rms, seed):
    x = np.array(x, dtype=np.float64, copy=True)
    if condition == "drop_channel_0":
        x[:, 0] = 0
    elif condition.startswith("gain_"):
        x *= float(condition.split("_")[1])
    elif condition == "noise_0.1":
        x += np.random.default_rng(seed).normal(size=x.shape) * train_rms * 0.1
    elif condition != "clean":
        raise ValueError(f"Unknown corruption: {condition}")
    return x
