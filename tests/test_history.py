import hashlib
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import h5py
import numpy as np

from nervegear_benchmark import history

STUDY = Path("research/emg2pose/history-v1.json")


def record(n=26000):
    return {
        "entry": {"recording": 1, "filename": "fixture", "stage": "synthetic"},
        "time": np.arange(n) / 2000,
        "emg": np.ones((n, 16)),
        "target": np.ones((n, 20)),
    }


def fitting_table(number, x, y):
    return {"entry": {"recording": number}, "x": x, "y": y, "eligible": np.ones(len(y), dtype=bool)}


class HistoryUnitTests(unittest.TestCase):
    def test_direct_windows_tap_order_grid_and_historic_label_independence(self):
        source = record(2000)
        source["emg"] = (np.arange(2000)[:, None] + np.arange(16)[None, :]) / 2000
        source["target"][799] = 0
        item = history.make_table(source)
        np.testing.assert_array_equal(item["ends"], np.arange(1199, 2000, 40))
        self.assertTrue(item["eligible"][0])

        def direct(a, b):
            return np.log1p(np.sqrt(np.mean(source["emg"][a : b + 1] ** 2, axis=0)))

        for row, end in enumerate(item["ends"]):
            np.testing.assert_allclose(
                item["x"]["ridge_current"][row], direct(end - 399, end), atol=1e-12
            )
            np.testing.assert_allclose(
                item["x"]["ridge_wide"][row], direct(end - 1199, end), atol=1e-12
            )
            stack = np.concatenate(
                [direct(end - offset - 399, end - offset) for offset in [0, 200, 400, 600, 800]]
            )
            np.testing.assert_allclose(item["x"]["ridge_history"][row], stack, atol=1e-12)
        for n in [0, 1, 1199]:
            empty = history.make_table(record(n))
            self.assertEqual(len(empty["ends"]), 0)
            self.assertEqual(empty["x"]["ridge_history"].shape, (0, 80))

    def test_full_span_invalid_input_and_timestamp_gap(self):
        source = record(2000)
        source["emg"][0, 0] = np.nan
        item = history.make_table(source)
        self.assertFalse(item["input_valid"][0])
        self.assertTrue(item["input_valid"][1])
        for values in item["x"].values():
            self.assertTrue(np.isnan(values[0]).all())
        source = record(2000)
        source["time"][500:] += 0.01
        item = history.make_table(source)
        self.assertFalse(item["input_valid"][0])
        self.assertTrue(item["input_valid"][-1])

    def test_prefix_embargo_support_minima_and_empty_fit(self):
        source = record(25200)
        item = history.make_table(source)
        masks, counts = history.partition(item, source["time"])
        self.assertEqual(counts["prefix"]["eligible_outputs"], 471)
        self.assertEqual(counts["score"]["eligible_outputs"], 100)
        ends = item["ends"][masks["score"]]
        self.assertEqual(ends[0], 21239)
        self.assertTrue(np.all(source["time"][ends - 1199] >= 10))
        tables = [{**item, "entry": {"recording": r}} for r in range(1, 10)]
        fold = history.evaluate_fold(tables, source, item)
        self.assertEqual(fold["status"], "supported")
        self.assertEqual({s["scored_outputs"] for s in fold["scores"].values()}, {100})
        prefix_rows = np.flatnonzero(masks["prefix"])
        limited = {**item, "eligible": item["eligible"].copy()}
        limited["eligible"][prefix_rows[25:]] = False
        self.assertEqual(history.evaluate_fold(tables, source, limited)["status"], "supported")
        limited["eligible"][prefix_rows[24]] = False
        self.assertEqual(history.evaluate_fold(tables, source, limited)["status"], "unsupported")
        short = record(25160)
        self.assertEqual(
            history.evaluate_fold(tables, short, history.make_table(short))["status"], "unsupported"
        )
        with self.assertRaisesRegex(ValueError, "fitting outputs"):
            history.evaluate_fold([tables[0]], record(1000), history.make_table(record(1000)))

    def test_duplicate_current_regularization_and_constant_predictions(self):
        rng = np.random.default_rng(42)
        x = rng.normal(size=(200, 16))
        x[:, 0] = 1
        y = rng.normal(size=(200, 20)) + 2
        features = {"ridge_current": x, "ridge_wide": x, "ridge_history": np.tile(x, (1, 5))}
        fit = history.fit_fold([fitting_table(1, features, y)], 2)
        a = fit["models"]["ridge_current"].predict(x)
        b = fit["models"]["ridge_history"].predict(features["ridge_history"])
        np.testing.assert_allclose(a, b, rtol=1e-11, atol=1e-12)
        self.assertEqual(fit["models"]["ridge_history"].coefficients.shape, (80, 20))
        self.assertEqual(fit["models"]["ridge_current"].scale[0], 1)
        constant = history.fit_fold([fitting_table(1, features, np.full_like(y, 2))], 2)
        predictions = history.predict_methods(
            constant, np.full(20, 2), {"x": features}, np.ones(200, bool)
        )
        scores = history.score_predictions(predictions, np.full_like(y, 2))
        self.assertEqual({s["mae_rad"] for s in scores.values()}, {0})

    def test_past_dependent_target_can_benefit_and_history_can_lose(self):
        rng = np.random.default_rng(91)
        stack = rng.normal(size=(1200, 80))
        target = 2 + 0.3 * stack[:, -16:]
        x = {"ridge_current": stack[:, :16], "ridge_wide": stack[:, :16], "ridge_history": stack}
        fit = history.fit_fold(
            [fitting_table(1, {k: v[:1000] for k, v in x.items()}, target[:1000])], 2
        )
        item = {"x": {k: v[1000:] for k, v in x.items()}}
        predictions = history.predict_methods(
            fit, np.median(target[:1000], axis=0), item, np.ones(200, bool)
        )
        scores = history.score_predictions(predictions, target[1000:])
        self.assertLess(scores["ridge_history"]["mae_rad"], scores["ridge_current"]["mae_rad"] / 4)
        losing = {name: np.ones((2, 1)) for name in history.METHODS}
        losing["ridge_history"] += 1
        scores = history.score_predictions(losing, np.ones((2, 1)))
        aggregate = history.aggregate_folds(
            [{"status": "supported", "recording": 1, "scores": scores}]
        )
        self.assertEqual(aggregate["paired_differences"][history.PRIMARY]["worsened"], 1)
        losing["ridge_history"][0, 0] = np.nan
        with self.assertRaisesRegex(ValueError, "finite"):
            history.score_predictions(losing, np.ones((2, 1)))

    def test_future_inputs_and_labels_cannot_change_earlier_predictions_or_fits(self):
        source = record()
        rng = np.random.default_rng(7)
        source["emg"] = rng.normal(size=(26000, 16))
        item = history.make_table(source)
        other = {**item, "entry": {"recording": 2}}
        fit = history.fit_fold([item, other], 1)
        masks, _ = history.partition(item, source["time"])
        early = masks["score"] & (source["time"][item["ends"]] < 12)
        self.assertGreater(early.sum(), 0)
        prefix = np.median(item["y"][masks["prefix"]], axis=0)
        before = history.predict_methods(fit, prefix, item, early)
        source["emg"][24000:] *= 10
        source["target"][24000:] += 2
        changed = history.make_table(source)
        new_fit = history.fit_fold([changed, other], 1)
        new_masks, _ = history.partition(changed, source["time"])
        new_prefix = np.median(changed["y"][new_masks["prefix"]], axis=0)
        after = history.predict_methods(new_fit, new_prefix, changed, early)
        for name in history.ALPHAS:
            np.testing.assert_array_equal(
                fit["models"][name].coefficients, new_fit["models"][name].coefficients
            )
        np.testing.assert_array_equal(item["eligible"][early], changed["eligible"][early])
        np.testing.assert_array_equal(prefix, new_prefix)
        for name in history.METHODS:
            np.testing.assert_array_equal(before[name], after[name])

    def test_paired_errors_tolerance_and_null_unsupported_aggregates(self):
        folds = []
        for number, difference in enumerate([-0.1, 1e-13, 0.2], 1):
            values = {name: np.full((2, 1), 2.0) for name in history.METHODS}
            values["ridge_history"] += difference
            folds.append(
                {
                    "recording": number,
                    "status": "supported",
                    "scores": history.score_predictions(values, np.ones((2, 1))),
                }
            )
        result = history.aggregate_folds(folds)
        primary = result["paired_differences"][history.PRIMARY]
        self.assertEqual([primary[k] for k in ["improved", "tied", "worsened"]], [1, 1, 1])
        self.assertAlmostEqual(primary["macro_mae_difference_rad"], (0.1 + 1e-13) / 3)
        self.assertAlmostEqual(
            result["methods"]["ridge_history"]["macro_rmse_rad"],
            np.sqrt((0.9**2 + (1 + 1e-13) ** 2 + 1.2**2) / 3),
        )
        empty = history.aggregate_folds([{"recording": 1, "status": "unsupported"}])
        self.assertIsNone(empty["methods"]["ridge_history"])
        self.assertIsNone(empty["paired_differences"][history.PRIMARY])
        study = json.loads(STUDY.read_text())
        history.validate_study(study)
        for field, value in [("embargo_seconds", 0.2), ("unexpected", 1)]:
            with self.assertRaisesRegex(ValueError, "history"):
                history.validate_study({**study, field: value})


class HistoryCommandTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.source = json.loads(Path("research/emg2pose/pilot-v1.json").read_text())
        rng = np.random.default_rng(21)
        for entry in self.source["files"]:
            if entry["split"] != "train":
                continue
            data = np.zeros(
                26000,
                dtype=[("time", "<f8"), ("emg", "<f4", (16,)), ("joint_angles", "<f4", (20,))],
            )
            data["time"] = np.arange(len(data)) / 2000
            data["emg"] = rng.normal(size=(len(data), 16))
            data["joint_angles"] = (
                0.3 + entry["recording"] * 0.01 + rng.normal(0, 0.02, (len(data), 20))
            )
            path = self.root / entry["filename"]
            with h5py.File(path, "w") as stream:
                stream.create_dataset("emg2pose/timeseries", data=data)
            entry["sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
        self.manifest = self.root / "source.json"
        self.manifest.write_text(json.dumps(self.source))

    def run_cli(self, output, extra=()):
        return subprocess.run(
            [
                sys.executable,
                "-m",
                "nervegear_benchmark",
                "history",
                "--manifest",
                str(self.manifest),
                "--history-protocol",
                str(STUDY.resolve()),
                "--data-dir",
                str(self.root),
                "--output",
                str(self.root / output),
                *extra,
            ],
            capture_output=True,
            text=True,
            env=os.environ.copy(),
            timeout=90,
        )

    def summary(self, name):
        return json.loads((self.root / name / "summary.json").read_text())

    def change_file(self, entry, transform):
        path = self.root / entry["filename"]
        with h5py.File(path, "r+") as stream:
            data = stream["emg2pose/timeseries"][:]
            transform(data)
            stream["emg2pose/timeseries"][:] = data
        entry["sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
        self.manifest.write_text(json.dumps(self.source))

    def test_nine_file_command_common_rows_and_other_file_isolation(self):
        result = self.run_cli("first")
        self.assertEqual(result.returncode, 0, result.stderr)
        first = self.summary("first")
        self.assertEqual(len(first["loaded_files"]), 9)
        self.assertEqual(first["aggregate"]["supported_folds"], 9)
        for fold in first["folds"]:
            self.assertEqual({s["scored_outputs"] for s in fold["scores"].values()}, {120})
            self.assertEqual(
                fold["model_settings"]["ridge_history"], {"dimension": 80, "effective_alpha": 50.0}
            )
            self.assertEqual(len(fold["fit_sha256"]), 3)
        for entry in self.source["files"]:
            if entry["split"] != "train":
                (self.root / entry["filename"]).write_bytes(b"unusable")
        result = self.run_cli("second")
        self.assertEqual(result.returncode, 0, result.stderr)
        second = self.summary("second")
        self.assertEqual(first["folds"], second["folds"])
        self.assertEqual(first["aggregate"], second["aggregate"])
        again = self.run_cli("first")
        self.assertNotEqual(again.returncode, 0)
        self.assertIn("exists", again.stderr)

    def test_later_labels_change_scores_but_not_models_controls_or_predictions(self):
        self.assertEqual(self.run_cli("before").returncode, 0)

        def change_later(data):
            data["joint_angles"][data["time"] >= 10] += 1

        self.change_file(self.source["files"][0], change_later)
        result = self.run_cli("after")
        self.assertEqual(result.returncode, 0, result.stderr)
        a, b = self.summary("before")["folds"][0], self.summary("after")["folds"][0]
        for key in [
            "fit_sha256",
            "prefix_control_sha256",
            "common_scored_mask_sha256",
            "prediction_sha256",
        ]:
            self.assertEqual(a[key], b[key], key)
        self.assertNotEqual(
            a["scores"]["ridge_history"]["mae_rad"], b["scores"]["ridge_history"]["mae_rad"]
        )

    def test_unsupported_prefixes_and_empty_fits_are_distinct(self):
        def invalidate_prefix(data):
            data["joint_angles"][data["time"] < 10] = 0

        for entry in self.source["files"]:
            if entry["split"] == "train":
                self.change_file(entry, invalidate_prefix)
        result = self.run_cli("unsupported")
        self.assertEqual(result.returncode, 0, result.stderr)
        summary = self.summary("unsupported")
        self.assertEqual(summary["status"], "unsupported_study")
        self.assertEqual(summary["aggregate"]["unsupported_folds"], 9)
        self.assertIsNone(summary["aggregate"]["methods"]["ridge_history"])
        self.assertTrue(
            all(f["partitions"]["score"]["eligible_outputs"] == 120 for f in summary["folds"])
        )

        def invalidate_all(data):
            data["joint_angles"] = 0

        for entry in self.source["files"]:
            if entry["split"] == "train":
                self.change_file(entry, invalidate_all)
        result = self.run_cli("empty-fit")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("fitting outputs", result.stderr)
        self.assertFalse((self.root / "empty-fit/completion.json").exists())

    def test_bad_time_corrupt_and_missing_files_cannot_complete(self):
        entry = self.source["files"][0]

        def repeat_time(data):
            data["time"][5] = data["time"][4]

        self.change_file(entry, repeat_time)
        bad = self.run_cli("bad-time")
        self.assertNotEqual(bad.returncode, 0)
        self.assertIn("timestamps", bad.stderr)
        path = self.root / entry["filename"]
        path.write_bytes(b"corrupt")
        bad = self.run_cli("corrupt")
        self.assertNotEqual(bad.returncode, 0)
        self.assertIn("checksum", bad.stderr)
        path.unlink()
        bad = self.run_cli("missing")
        self.assertNotEqual(bad.returncode, 0)
        self.assertIn(entry["filename"], bad.stderr)
        for name in ["bad-time", "corrupt", "missing"]:
            self.assertFalse((self.root / name / "completion.json").exists())

    def test_command_specific_options_are_rejected(self):
        result = self.run_cli("wrong", ["--alignment-protocol", str(STUDY)])
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("only valid for align", result.stderr)
        for command in ["run", "diagnose", "calibrate", "align"]:
            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "nervegear_benchmark",
                    command,
                    "--data-dir",
                    str(self.root),
                    "--output",
                    str(self.root / command),
                    "--history-protocol",
                    str(STUDY),
                ],
                capture_output=True,
                text=True,
                env=os.environ.copy(),
                timeout=30,
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("only valid for history", result.stderr)


if __name__ == "__main__":
    unittest.main()
