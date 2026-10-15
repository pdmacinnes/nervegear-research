import hashlib
import json
import os
import subprocess
import sys
import unittest

import h5py
import numpy as np
import test_pipeline

from nervegear_benchmark import diagnostics


class StatisticTests(unittest.TestCase):
    def test_error_decomposition_and_group_weighting(self):
        first = diagnostics.error_stats(np.array([[2.0], [4.0]]), np.zeros((2, 1)))
        self.assertEqual(first["mae_rad"], 3)
        self.assertEqual(first["mse_rad2"], 10)
        self.assertEqual(first["residual_mean_rad"], [3])
        self.assertEqual(first["residual_variance_rad2"], [1])
        self.assertEqual(first["per_joint_mse_rad2"], [10])
        second = diagnostics.error_stats(np.full((6, 1), 1.0), np.zeros((6, 1)))
        aggregate = diagnostics.aggregate_stats([first, second])
        self.assertEqual(aggregate["macro_mae_rad"], 2)
        self.assertEqual(aggregate["sample_weighted_mae_rad"], 1.5)
        self.assertEqual(aggregate["macro_mse_rad2"], 5.5)
        self.assertAlmostEqual(aggregate["macro_rmse_rad"], np.sqrt(5.5))

    def test_own_recording_median_is_a_descriptive_lower_bound(self):
        y = np.array([[0.0, 1], [1, 2], [20, 3]])
        stats = diagnostics.pose_stats(y)
        self.assertAlmostEqual(stats["own_median_mae_rad"], 22 / 6)
        self.assertLessEqual(stats["own_median_mae_rad"], np.abs(y - 5).mean())
        np.testing.assert_allclose(stats["iqr_rad"], [10, 1])

    def test_feature_shift_uses_training_scale_and_handles_constants(self):
        train = np.array([[0.0, 8], [2, 8]])
        reference = diagnostics.feature_reference(train)
        self.assertEqual(reference["constant_channels"], [False, True])
        shifted = diagnostics.feature_shift(np.array([[5.0, 9], [5, 9]]), reference)
        self.assertEqual(shifted["standardized_mean"], [4, 1])
        self.assertEqual(shifted["fraction_abs_z_gt_3"], [1, 0])
        self.assertEqual(shifted["fraction_outside_train_p01_p99"], [1, 1])
        self.assertEqual(reference["mean"], [1, 8])

    def test_range_groups_count_angle_elements_and_keep_empty_groups_null(self):
        train = np.array([[0.0, 0], [2, 2]])
        y = np.ones((2, 2))
        prediction = np.array([[1.0, 3], [-1, 1]])
        stats = diagnostics.range_stats(prediction, y, train)
        full = stats["training_min_max"]
        self.assertEqual(full["prediction_fraction_outside_per_joint"], [0.5, 0.5])
        self.assertEqual(full["outside_prediction_angle_elements"], 2)
        self.assertEqual(full["outside_prediction_mae_rad"], 2)
        self.assertEqual(full["inside_prediction_mae_rad"], 0)
        empty = diagnostics.range_stats(y, y, train)["training_min_max"]
        self.assertEqual(empty["outside_prediction_angle_elements"], 0)
        self.assertIsNone(empty["outside_prediction_mae_rad"])

    def test_singular_features_are_explicit_and_regularized_solver_agrees(self):
        x = np.ones((6, 3))
        y = np.arange(6.0)[:, None]
        stats = diagnostics.solver_stats(x, y, 10)
        self.assertEqual(stats["rank"], 0)
        self.assertTrue(stats["singular"])
        self.assertIsNone(stats["feature_condition_number"])
        self.assertAlmostEqual(stats["regularized_condition_number"], 1)
        self.assertLess(stats["independent_prediction_max_abs_difference_rad"], 1e-9)


class DiagnosticCommandTests(unittest.TestCase):
    def setUp(self):
        test_pipeline.CommandTests.setUp(self)
        for entry in self.protocol["files"]:
            if entry["split"] == "test":
                (self.root / entry["filename"]).unlink()

    def run_cli(self, output="diagnostics"):
        return subprocess.run(
            [
                sys.executable,
                "-m",
                "nervegear_benchmark",
                "diagnose",
                "--manifest",
                str(self.manifest),
                "--data-dir",
                str(self.root),
                "--output",
                str(self.root / output),
            ],
            env=os.environ.copy(),
            capture_output=True,
            text=True,
            timeout=60,
        )

    def test_command_needs_only_twelve_files_and_ignores_corrupt_test_files(self):
        result = self.run_cli("missing-test")
        self.assertEqual(result.returncode, 0, result.stderr)
        a = json.loads((self.root / "missing-test/summary.json").read_text())
        self.assertEqual(len(a["loaded_files"]), 12)
        self.assertEqual({e["split"] for e in a["loaded_files"]}, {"train", "validation"})
        self.assertEqual(len(a["configurations"]), 9)
        self.assertEqual(a["coverage"]["validation"]["scored_outputs"], 30)
        self.assertTrue((self.root / "missing-test/fit-gap.svg").is_file())
        for entry in self.protocol["files"]:
            if entry["split"] == "test":
                (self.root / entry["filename"]).write_bytes(b"not an HDF5 recording")
        result = self.run_cli("corrupt-test")
        self.assertEqual(result.returncode, 0, result.stderr)
        b = json.loads((self.root / "corrupt-test/summary.json").read_text())
        self.assertEqual(a["configurations"], b["configurations"])
        self.assertEqual(a["feature_distributions"], b["feature_distributions"])
        again = self.run_cli("missing-test")
        self.assertNotEqual(again.returncode, 0)
        self.assertIn("exists", again.stderr)

    def test_required_file_failure_leaves_no_completion_marker(self):
        (self.root / self.protocol["files"][0]["filename"]).unlink()
        result = self.run_cli("missing-train")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn(self.protocol["files"][0]["filename"], result.stderr)
        self.assertFalse((self.root / "missing-train/completion.json").exists())

    def test_bad_required_hash_is_rejected(self):
        (self.root / self.protocol["files"][0]["filename"]).write_bytes(b"bad training file")
        result = self.run_cli("bad-hash")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("checksum", result.stderr)

    def test_validation_changes_cannot_change_training_statistics_or_fit(self):
        first = self.run_cli("original-validation")
        self.assertEqual(first.returncode, 0, first.stderr)
        for entry in self.protocol["files"]:
            if entry["split"] == "validation":
                path = self.root / entry["filename"]
                with h5py.File(path, "r+") as stream:
                    data = stream["emg2pose/timeseries"][:]
                    data["emg"] *= 100
                    data["joint_angles"] *= 2
                    stream["emg2pose/timeseries"][:] = data
                entry["sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
        self.manifest.write_text(json.dumps(self.protocol))
        second = self.run_cli("changed-validation")
        self.assertEqual(second.returncode, 0, second.stderr)
        a = json.loads((self.root / "original-validation/summary.json").read_text())
        b = json.loads((self.root / "changed-validation/summary.json").read_text())
        for history in ["100", "200", "400"]:
            self.assertEqual(
                a["feature_distributions"][history]["training_reference"],
                b["feature_distributions"][history]["training_reference"],
            )
        for original, changed in zip(a["configurations"], b["configurations"], strict=True):
            self.assertEqual(original["scores"]["train"], changed["scores"]["train"])
        self.assertEqual(a["baselines"]["Median"]["train"], b["baselines"]["Median"]["train"])
        self.assertNotEqual(
            a["feature_distributions"]["400"]["records"],
            b["feature_distributions"]["400"]["records"],
        )

    def test_empty_recording_fails_with_filename_and_counts(self):
        from nervegear_benchmark.pipeline import table

        record = {
            "emg": np.ones((800, 16)),
            "time": np.arange(800) / 2000,
            "target": np.zeros((800, 20)),
            "entry": self.protocol["files"][0],
        }
        item = table(record, 400)
        with self.assertRaisesRegex(ValueError, "recording-1_left.*scored_outputs.*0"):
            diagnostics.require_scored(item)


if __name__ == "__main__":
    unittest.main()
