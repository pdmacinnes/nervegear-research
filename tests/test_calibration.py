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

from nervegear_benchmark import calibration, core
from nervegear_benchmark.pipeline import table

STUDY = Path("research/emg2pose/calibration-v1.json")


def small_table(recording, x, y):
    return {
        "entry": {"recording": recording},
        "x": np.array(x, dtype=float),
        "y": np.array(y, dtype=float),
        "eligible": np.ones(len(x), dtype=bool),
    }


class CalibrationUnitTests(unittest.TestCase):
    def test_prefix_embargo_and_histories_do_not_overlap(self):
        n = 22000
        record = {
            "emg": np.ones((n, 16)),
            "time": np.arange(n) / 2000,
            "target": np.ones((n, 20)),
            "entry": {"filename": "synthetic"},
        }
        item = table(record, 400)
        masks, counts = calibration.partition(item, record["time"])
        ends = item["ends"]
        self.assertTrue(np.all(record["time"][ends[masks["prefix"]]] < 10))
        self.assertTrue(np.all(record["time"][ends[masks["score"]]] >= 10.2))
        self.assertGreaterEqual(record["time"][ends[masks["score"]][0] - 399], 10)
        self.assertLess(ends[masks["prefix"]][-1], ends[masks["score"]][0] - 399)
        self.assertEqual(sum(c["candidate_outputs"] for c in counts.values()), len(ends))
        self.assertEqual(counts["score"]["eligible_outputs"], 40)

    def test_bad_timestamps_fail_instead_of_repartitioning(self):
        with self.assertRaisesRegex(ValueError, "timestamps"):
            calibration.validate_time(np.array([0, 0.001, 0.001]), "bad-file")

    def test_fold_fit_excludes_all_held_out_data(self):
        a = small_table(1, [[1], [2], [3]], [[1], [2], [3]])
        b = small_table(2, [[10], [20]], [[4], [5]])
        before = calibration.fit_fold([a, b], 2)
        b["x"] *= 1000
        b["y"] *= -1000
        after = calibration.fit_fold([a, b], 2)
        np.testing.assert_array_equal(before["model"].coefficients, after["model"].coefficients)
        np.testing.assert_array_equal(before["model"].mean, [2])
        np.testing.assert_array_equal(before["train_median"], after["train_median"])

    def test_fixed_offset_constants_and_future_label_isolation(self):
        model = core.Ridge(np.zeros(1), np.ones(1), np.zeros(1), np.ones((1, 1)))
        fit = {"model": model, "train_mean": np.array([0.0]), "train_median": np.array([0.0])}
        prefix_x = np.array([[1.0], [3]])
        prefix_y = np.array([[6.0], [8]])
        state = calibration.calibration_state(fit, prefix_x, prefix_y)
        np.testing.assert_array_equal(state["offset"], [5])
        prediction = calibration.predict_methods(fit, state, np.array([[4.0], [10]]))
        np.testing.assert_array_equal(prediction["calibrated_ridge"], [[9], [15]])
        np.testing.assert_array_equal(prediction["prefix_mean"], [[7], [7]])
        np.testing.assert_array_equal(prediction["prefix_median"], [[7], [7]])
        np.testing.assert_array_equal(model.coefficients, [[1]])
        future_labels = np.full((2, 1), 1000.0)
        core.errors(prediction["calibrated_ridge"], future_labels)
        np.testing.assert_array_equal(
            calibration.predict_methods(fit, state, np.array([[4.0], [10]]))["calibrated_ridge"],
            prediction["calibrated_ridge"],
        )

    def test_paired_differences_ties_and_unsupported_aggregates(self):
        folds = []
        for i, delta in enumerate([-0.1, 0, 0.2]):
            scores = {
                name: {
                    "mae_rad": 1.0,
                    "per_joint_mae_rad": [1.0],
                    "scored_outputs": 2,
                    "mse_rad2": 1.0,
                }
                for name in [
                    "ridge",
                    "calibrated_ridge",
                    "train_mean",
                    "train_median",
                    "prefix_mean",
                    "prefix_median",
                ]
            }
            scores["calibrated_ridge"]["mae_rad"] += delta
            folds.append({"recording": i + 1, "status": "supported", "scores": scores})
        result = calibration.aggregate_folds(folds)
        paired = result["paired_differences"]["calibrated_ridge_minus_ridge"]
        self.assertEqual([paired[k] for k in ["improved", "tied", "worsened"]], [1, 1, 1])
        self.assertAlmostEqual(paired["macro_mae_difference_rad"], 0.1 / 3)
        empty = calibration.aggregate_folds([{"recording": 1, "status": "unsupported"}])
        self.assertEqual(empty["supported_folds"], 0)
        self.assertIsNone(empty["methods"]["calibrated_ridge"])

    def test_protocol_changes_are_not_silently_accepted(self):
        p = json.loads(STUDY.read_text())
        p["prefix_seconds"] = 20
        with self.assertRaisesRegex(ValueError, "prefix_seconds"):
            calibration.validate_study(p)


class CalibrationCommandTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.source = json.loads(Path("research/emg2pose/pilot-v1.json").read_text())
        rng = np.random.default_rng(8)
        for entry in self.source["files"]:
            if entry["split"] != "train":
                continue
            n = 22000
            data = np.zeros(
                n, dtype=[("time", "<f8"), ("emg", "<f4", (16,)), ("joint_angles", "<f4", (20,))]
            )
            data["time"] = np.arange(n) / 2000
            data["emg"] = rng.normal(size=(n, 16))
            data["joint_angles"] = 0.3 + entry["recording"] * 0.01 + rng.normal(0, 0.02, (n, 20))
            data["joint_angles"][439] = 0
            path = self.root / entry["filename"]
            with h5py.File(path, "w") as stream:
                stream.create_dataset("emg2pose/timeseries", data=data)
            entry["sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
        self.manifest = self.root / "source.json"
        self.manifest.write_text(json.dumps(self.source))

    def run_cli(self, output):
        return subprocess.run(
            [
                sys.executable,
                "-m",
                "nervegear_benchmark",
                "calibrate",
                "--manifest",
                str(self.manifest),
                "--calibration-protocol",
                str(STUDY.resolve()),
                "--data-dir",
                str(self.root),
                "--output",
                str(self.root / output),
            ],
            capture_output=True,
            text=True,
            env=os.environ.copy(),
            timeout=90,
        )

    def change_file(self, entry, transform):
        path = self.root / entry["filename"]
        with h5py.File(path, "r+") as stream:
            data = stream["emg2pose/timeseries"][:]
            transform(data)
            stream["emg2pose/timeseries"][:] = data
        entry["sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
        self.manifest.write_text(json.dumps(self.source))

    def test_command_opens_only_nine_files_and_ignores_other_files(self):
        first = self.run_cli("first")
        self.assertEqual(first.returncode, 0, first.stderr)
        a = json.loads((self.root / "first/summary.json").read_text())
        self.assertEqual(len(a["loaded_files"]), 9)
        self.assertEqual(a["aggregate"]["supported_folds"], 9)
        for fold in a["folds"]:
            counts = {s["scored_outputs"] for s in fold["scores"].values()}
            self.assertEqual(counts, {40})
        for entry in self.source["files"]:
            if entry["split"] != "train":
                (self.root / entry["filename"]).write_bytes(b"not a recording")
        second = self.run_cli("second")
        self.assertEqual(second.returncode, 0, second.stderr)
        b = json.loads((self.root / "second/summary.json").read_text())
        self.assertEqual(a["folds"], b["folds"])
        self.assertEqual(a["aggregate"], b["aggregate"])
        again = self.run_cli("first")
        self.assertNotEqual(again.returncode, 0)
        self.assertIn("exists", again.stderr)

    def test_future_labels_change_scores_but_not_held_out_fit_or_predictions(self):
        first = self.run_cli("before")
        self.assertEqual(first.returncode, 0, first.stderr)
        entry = self.source["files"][0]

        def alter_future(data):
            data["joint_angles"][data["time"] >= 10.2] += 1

        self.change_file(entry, alter_future)
        second = self.run_cli("after")
        self.assertEqual(second.returncode, 0, second.stderr)
        a = json.loads((self.root / "before/summary.json").read_text())["folds"][0]
        b = json.loads((self.root / "after/summary.json").read_text())["folds"][0]
        self.assertEqual(a["initial_fit_sha256"], b["initial_fit_sha256"])
        self.assertEqual(a["calibration_state_sha256"], b["calibration_state_sha256"])
        self.assertEqual(a["prediction_sha256"], b["prediction_sha256"])
        self.assertNotEqual(
            a["scores"]["calibrated_ridge"]["mae_rad"], b["scores"]["calibrated_ridge"]["mae_rad"]
        )

    def test_unsupported_prefixes_remain_visible_without_fabricated_scores(self):
        def invalidate_prefix(data):
            data["joint_angles"][data["time"] < 10] = 0

        for entry in self.source["files"]:
            if entry["split"] == "train":
                self.change_file(entry, invalidate_prefix)
        result = self.run_cli("unsupported")
        self.assertEqual(result.returncode, 0, result.stderr)
        s = json.loads((self.root / "unsupported/summary.json").read_text())
        self.assertEqual(len(s["folds"]), 9)
        self.assertTrue(all(f["status"] == "unsupported" for f in s["folds"]))
        self.assertIsNone(s["aggregate"]["methods"]["calibrated_ridge"])
        self.assertTrue((self.root / "unsupported/completion.json").exists())

    def test_corrupt_required_file_cannot_publish_completed_results(self):
        (self.root / self.source["files"][0]["filename"]).write_bytes(b"corrupt")
        result = self.run_cli("bad")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("checksum", result.stderr)
        self.assertFalse((self.root / "bad/completion.json").exists())

    def test_other_commands_reject_calibration_option(self):
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "nervegear_benchmark",
                "diagnose",
                "--data-dir",
                str(self.root),
                "--output",
                str(self.root / "wrong-command"),
                "--calibration-protocol",
                str(STUDY),
            ],
            capture_output=True,
            text=True,
            env=os.environ.copy(),
            timeout=30,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("only valid for calibrate", result.stderr)


if __name__ == "__main__":
    unittest.main()
