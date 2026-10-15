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

from nervegear_benchmark import alignment, core
from nervegear_benchmark.pipeline import table

STUDY = Path("research/emg2pose/alignment-v1.json")


def record_and_table(n=50000):
    record = {
        "entry": {"recording": 1, "filename": "synthetic", "stage": "fixture"},
        "time": np.arange(n) / 2000,
        "emg": np.ones((n, 16)),
        "target": np.ones((n, 20)),
    }
    return record, table(record, 400)


class AlignmentUnitTests(unittest.TestCase):
    def test_original_grid_shifts_prefix_boundaries_and_no_wrap(self):
        record, item = record_and_table()
        pair = alignment.pair_outputs(item, record["time"])
        targets = np.flatnonzero(pair["mask"])
        np.testing.assert_array_equal(targets, np.arange(751, 991))
        self.assertEqual(pair["prefix_mask"].sum(), 491)
        self.assertEqual(pair["coverage"]["shift_tolerances"], 240)
        for name, shift in alignment.SHIFTS.items():
            np.testing.assert_array_equal(pair["sources"][name], targets + shift)
            ends = item["ends"][pair["sources"][name]]
            self.assertTrue(np.all(record["time"][ends] >= 10.2))
            self.assertTrue(np.all(record["time"][ends - 399] >= 10))
            if shift:
                duration = pair["realized_shifts"][name]
                self.assertAlmostEqual(duration["minimum_seconds"], shift * 0.02)
                self.assertAlmostEqual(duration["maximum_seconds"], shift * 0.02)

    def test_source_references_do_not_filter_or_compress_the_grid(self):
        record, item = record_and_table()
        item["reference_valid"][550] = False
        item["eligible"][550] = False
        pair = alignment.pair_outputs(item, record["time"])
        self.assertTrue(pair["mask"][800])
        target_position = list(np.flatnonzero(pair["mask"])).index(800)
        self.assertEqual(pair["sources"]["ridge_past_5s"][target_position], 550)
        item["reference_valid"][800] = False
        item["eligible"][800] = False
        pair = alignment.pair_outputs(item, record["time"])
        self.assertFalse(pair["mask"][800])
        item["reference_valid"][800] = True
        item["eligible"][800] = True
        item["input_valid"][550] = False
        pair = alignment.pair_outputs(item, record["time"])
        self.assertFalse(pair["mask"][800])
        self.assertLess(
            pair["coverage"]["source_inputs_valid"], pair["coverage"]["indices_in_bounds"]
        )

    def test_inclusive_tolerance_and_timestamp_gaps(self):
        for nominal in [-5.0, -1.0, 1.0, 5.0]:
            low, high = nominal - 0.010, nominal + 0.010
            values = np.array([low, high, np.nextafter(low, -np.inf), np.nextafter(high, np.inf)])
            np.testing.assert_array_equal(
                alignment.within_shift_tolerance(values, nominal), [True, True, False, False]
            )
        record, _ = record_and_table()
        record["time"][30000:] += 0.1
        item = table(record, 400)
        pair = alignment.pair_outputs(item, record["time"])
        counts = list(pair["coverage"].values())
        self.assertEqual(counts, sorted(counts, reverse=True))
        self.assertLess(counts[-1], counts[-2])

    def test_tracking_constant_and_better_shifted_predictions(self):
        record, item = record_and_table()
        item["x"] = (1 + np.arange(len(item["ends"])) / 1000)[:, None]
        item["y"] = item["x"].copy()
        model = core.Ridge(np.zeros(1), np.ones(1), np.zeros(1), np.ones((1, 1)))
        fit = {"model": model, "train_median": np.ones(1)}
        pair = alignment.pair_outputs(item, record["time"])
        predicted = alignment.predict_methods(fit, np.ones(1), item, pair["sources"])
        target = item["y"][pair["mask"]]
        scores = alignment.score_predictions(predicted, target)
        self.assertEqual(scores["ridge"]["mae_rad"], 0)
        self.assertTrue(
            all(scores[name]["mae_rad"] > 0 for name in alignment.SHIFTS if name != "ridge")
        )
        constant = {name: np.ones_like(target) for name in alignment.METHODS}
        constant_scores = alignment.score_predictions(constant, target)
        self.assertEqual(len({s["mae_rad"] for s in constant_scores.values()}), 1)
        delayed_target = predicted["ridge_future_1s"]
        delayed_scores = alignment.score_predictions(predicted, delayed_target)
        self.assertEqual(delayed_scores["ridge_future_1s"]["mae_rad"], 0)
        self.assertGreater(delayed_scores["ridge"]["mae_rad"], 0)
        predicted["ridge"][0, 0] = np.nan
        with self.assertRaisesRegex(ValueError, "finite"):
            alignment.score_predictions(predicted, target)

    def test_primary_comparison_averages_errors_and_keeps_unsupported_folds(self):
        target = np.ones((2, 1))
        folds = []
        for recording, value in enumerate([1.0, 2.0, 3.0], 1):
            predictions = {name: target + 2 for name in alignment.METHODS}
            predictions["ridge"] = target + value
            predictions["ridge_future_5s"] = target - 2
            folds.append(
                {
                    "recording": recording,
                    "status": "supported",
                    "scores": alignment.score_predictions(predictions, target),
                }
            )
        folds.append({"recording": 4, "status": "unsupported", "scores": None})
        result = alignment.aggregate_folds(folds)
        primary = result["paired_differences"]["ridge_minus_symmetric_5s_error"]
        self.assertEqual(primary["macro_mae_difference_rad"], 0)
        self.assertEqual([primary[k] for k in ["improved", "tied", "worsened"]], [1, 1, 1])
        self.assertEqual([r["difference_rad"] for r in primary["folds"]], [-1, 0, 1])
        self.assertEqual(result["unsupported_folds"], 1)
        self.assertEqual(result["methods"]["ridge"]["scored_outputs"], 6)
        self.assertAlmostEqual(result["methods"]["ridge"]["macro_rmse_rad"], np.sqrt(14 / 3))
        empty = alignment.aggregate_folds([folds[-1]])
        self.assertIsNone(empty["methods"]["ridge"])
        self.assertIsNone(empty["paired_differences"]["ridge_minus_symmetric_5s_error"])

    def test_support_threshold_and_held_out_fit_isolation(self):
        record, item = record_and_table(44400)
        tables = [{**item, "entry": {"recording": r}} for r in range(1, 10)]
        supported = alignment.evaluate_fold(tables, record, item)
        self.assertEqual(supported["status"], "supported")
        self.assertEqual(supported["coverage"]["shift_tolerances"], 100)
        prefix_rows = np.flatnonzero(record["time"][item["ends"]] < 10)
        limited = {**item, "eligible": item["eligible"].copy()}
        limited["eligible"][prefix_rows[25:]] = False
        self.assertEqual(alignment.evaluate_fold(tables, record, limited)["status"], "supported")
        limited["eligible"][prefix_rows[24]] = False
        self.assertEqual(alignment.evaluate_fold(tables, record, limited)["status"], "unsupported")
        changed = {**item, "x": item["x"] * 10, "y": item["y"] + 0.5}
        tables[0] = changed
        after = alignment.evaluate_fold(tables, record, changed)
        self.assertEqual(supported["initial_fit_sha256"], after["initial_fit_sha256"])
        self.assertNotEqual(supported["prefix_control_sha256"], after["prefix_control_sha256"])
        record, item = record_and_table(44360)
        unsupported = alignment.evaluate_fold(tables, record, item)
        self.assertEqual(unsupported["status"], "unsupported")
        self.assertEqual(unsupported["coverage"]["shift_tolerances"], 99)
        with self.assertRaisesRegex(ValueError, "fitting outputs"):
            alignment.evaluate_fold([tables[0]], *record_and_table())

    def test_short_grid_empty_durations_and_protocol_validation(self):
        record, item = record_and_table(1000)
        pair = alignment.pair_outputs(item, record["time"])
        self.assertEqual(pair["mask"].sum(), 0)
        self.assertTrue(all(v is None for v in pair["realized_shifts"].values()))
        study = json.loads(STUDY.read_text())
        alignment.validate_study(study)
        for key, value in [("minimum_scored_outputs", 1), ("surprise", 3)]:
            with self.assertRaisesRegex(ValueError, "alignment"):
                alignment.validate_study({**study, key: value})


class AlignmentCommandTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.source = json.loads(Path("research/emg2pose/pilot-v1.json").read_text())
        rng = np.random.default_rng(15)
        for entry in self.source["files"]:
            if entry["split"] != "train":
                continue
            n = 50000
            data = np.zeros(
                n, dtype=[("time", "<f8"), ("emg", "<f4", (16,)), ("joint_angles", "<f4", (20,))]
            )
            data["time"] = np.arange(n) / 2000
            data["emg"] = rng.normal(size=(n, 16))
            data["joint_angles"] = 0.3 + entry["recording"] * 0.01 + rng.normal(0, 0.02, (n, 20))
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
                "align",
                "--manifest",
                str(self.manifest),
                "--alignment-protocol",
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

    def read_summary(self, name):
        return json.loads((self.root / name / "summary.json").read_text())

    def change_file(self, entry, transform):
        path = self.root / entry["filename"]
        with h5py.File(path, "r+") as stream:
            data = stream["emg2pose/timeseries"][:]
            transform(data)
            stream["emg2pose/timeseries"][:] = data
        entry["sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
        self.manifest.write_text(json.dumps(self.source))

    def test_nine_file_command_isolation_common_targets_and_no_overwrite(self):
        first = self.run_cli("before")
        self.assertEqual(first.returncode, 0, first.stderr)
        a = self.read_summary("before")
        self.assertEqual(len(a["loaded_files"]), 9)
        self.assertEqual(a["aggregate"]["supported_folds"], 9)
        for fold in a["folds"]:
            self.assertEqual({s["scored_outputs"] for s in fold["scores"].values()}, {240})
            self.assertEqual(set(fold["prediction_sha256"]), set(alignment.METHODS))
        for entry in self.source["files"]:
            if entry["split"] != "train":
                (self.root / entry["filename"]).write_bytes(b"unusable")
        second = self.run_cli("after")
        self.assertEqual(second.returncode, 0, second.stderr)
        b = self.read_summary("after")
        self.assertEqual(a["folds"], b["folds"])
        self.assertEqual(a["aggregate"], b["aggregate"])
        again = self.run_cli("before")
        self.assertNotEqual(again.returncode, 0)
        self.assertIn("exists", again.stderr)

    def test_later_labels_change_scores_but_not_fit_control_mask_or_predictions(self):
        first = self.run_cli("before")
        self.assertEqual(first.returncode, 0, first.stderr)

        def change_future(data):
            data["joint_angles"][data["time"] >= 10] += 1

        self.change_file(self.source["files"][0], change_future)
        second = self.run_cli("after")
        self.assertEqual(second.returncode, 0, second.stderr)
        a = self.read_summary("before")["folds"][0]
        b = self.read_summary("after")["folds"][0]
        for key in [
            "initial_fit_sha256",
            "prefix_control_sha256",
            "common_target_mask_sha256",
            "prediction_sha256",
        ]:
            self.assertEqual(a[key], b[key], key)
        self.assertNotEqual(a["scores"]["ridge"]["mae_rad"], b["scores"]["ridge"]["mae_rad"])

    def test_all_unsupported_prefixes_keep_counts_and_null_metrics(self):
        def invalidate_prefix(data):
            data["joint_angles"][data["time"] < 10] = 0

        for entry in self.source["files"]:
            if entry["split"] == "train":
                self.change_file(entry, invalidate_prefix)
        result = self.run_cli("unsupported")
        self.assertEqual(result.returncode, 0, result.stderr)
        s = self.read_summary("unsupported")
        self.assertEqual(s["status"], "unsupported_study")
        self.assertEqual(s["aggregate"]["unsupported_folds"], 9)
        self.assertIsNone(s["aggregate"]["methods"]["ridge"])
        self.assertTrue(
            all(
                f["prefix_outputs"] == 0 and f["coverage"]["shift_tolerances"] == 240
                for f in s["folds"]
            )
        )
        self.assertTrue(
            json.loads((self.root / "unsupported/completion.json").read_text())["complete"]
        )

    def test_corrupt_missing_and_bad_time_files_cannot_complete(self):
        entry = self.source["files"][0]

        def repeat_time(data):
            data["time"][5] = data["time"][4]

        self.change_file(entry, repeat_time)
        bad_time = self.run_cli("bad-time")
        self.assertNotEqual(bad_time.returncode, 0)
        self.assertIn(entry["filename"], bad_time.stderr)
        self.assertIn("timestamps", bad_time.stderr)
        path = self.root / entry["filename"]
        path.write_bytes(b"corrupt")
        corrupt = self.run_cli("corrupt")
        self.assertNotEqual(corrupt.returncode, 0)
        self.assertIn("checksum", corrupt.stderr)
        path.unlink()
        missing = self.run_cli("missing")
        self.assertNotEqual(missing.returncode, 0)
        self.assertIn(entry["filename"], missing.stderr)
        for name in ["bad-time", "corrupt", "missing"]:
            self.assertFalse((self.root / name / "completion.json").exists())

    def test_empty_fitting_data_fail_even_when_target_folds_are_unsupported(self):
        def invalidate_all_references(data):
            data["joint_angles"] = 0

        for entry in self.source["files"]:
            if entry["split"] == "train":
                self.change_file(entry, invalidate_all_references)
        result = self.run_cli("empty-fit")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("fitting outputs", result.stderr)
        self.assertFalse((self.root / "empty-fit/completion.json").exists())

    def test_command_specific_options_are_rejected(self):
        wrong = self.run_cli("wrong", ["--calibration-protocol", str(STUDY)])
        self.assertNotEqual(wrong.returncode, 0)
        self.assertIn("only valid for calibrate", wrong.stderr)
        for command in ["run", "diagnose", "calibrate"]:
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
                    "--alignment-protocol",
                    str(STUDY),
                ],
                capture_output=True,
                text=True,
                env=os.environ.copy(),
                timeout=30,
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("only valid for align", result.stderr)


if __name__ == "__main__":
    unittest.main()
