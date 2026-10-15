import copy
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

from nervegear_benchmark import pipeline

PROTOCOL = Path("research/emg2pose/pilot-v1.json")


class ManifestTests(unittest.TestCase):
    def test_duplicate_or_cross_split_files_are_rejected(self):
        p = json.loads(PROTOCOL.read_text())
        p["files"][12]["filename"] = p["files"][0]["filename"]
        with self.assertRaisesRegex(ValueError, "duplicate"):
            pipeline.validate_protocol(p)

    def test_unsupported_configuration_is_rejected(self):
        p = json.loads(PROTOCOL.read_text())
        p["reference_pose_input"] = True
        with self.assertRaisesRegex(ValueError, "reference"):
            pipeline.validate_protocol(p)
        p = json.loads(PROTOCOL.read_text())
        p["history_samples"][0] = 101
        with self.assertRaisesRegex(ValueError, "history"):
            pipeline.validate_protocol(p)

    def test_validation_selection_never_receives_test_data(self):
        candidates = [({"history": 100, "alpha": 1}, 0.8), ({"history": 200, "alpha": 1}, 0.2)]
        self.assertEqual(pipeline.select_candidate(candidates)["history"], 200)


class CommandTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.protocol = json.loads(PROTOCOL.read_text())
        rng = np.random.default_rng(4)
        for entry in self.protocol["files"]:
            n = 800
            data = np.zeros(
                n, dtype=[("time", "<f8"), ("emg", "<f4", (16,)), ("joint_angles", "<f4", (20,))]
            )
            data["time"] = np.arange(n) / 2000
            data["emg"] = rng.normal(size=(n, 16))
            data["joint_angles"] = 0.3 + rng.normal(0, 0.02, (n, 20))
            data["joint_angles"][439] = 0
            path = self.root / entry["filename"]
            with h5py.File(path, "w") as f:
                f.create_dataset("emg2pose/timeseries", data=data)
            entry["sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
        self.manifest = self.root / "protocol.json"
        self.manifest.write_text(json.dumps(self.protocol))

    def run_cli(self, output="out"):
        return subprocess.run(
            [
                sys.executable,
                "-m",
                "nervegear_benchmark",
                "run",
                "--manifest",
                str(self.manifest),
                "--data-dir",
                str(self.root),
                "--output",
                str(self.root / output),
            ],
            capture_output=True,
            text=True,
            env=os.environ.copy(),
            timeout=60,
        )

    def test_command_scores_real_fixture_files_and_never_overwrites(self):
        result = self.run_cli()
        self.assertEqual(result.returncode, 0, result.stderr)
        summary = json.loads((self.root / "out/summary.json").read_text())
        self.assertEqual(len(summary["test"]["clean"]["records"]), 3)
        self.assertEqual(summary["test"]["clean"]["aggregate"]["scored_outputs"], 30)
        self.assertEqual(summary["coverage"]["test"]["invalid_reference_outputs"], 3)
        self.assertEqual(len(summary["timing"]["passes"]), 5)
        self.assertTrue((self.root / "out/robustness.svg").is_file())
        again = self.run_cli()
        self.assertNotEqual(again.returncode, 0)
        self.assertIn("exists", again.stderr)

    def test_checksum_failure_leaves_no_results(self):
        path = self.root / self.protocol["files"][0]["filename"]
        with path.open("ab") as f:
            f.write(b"corruption")
        result = self.run_cli("bad")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("checksum", result.stderr)
        self.assertFalse((self.root / "bad/summary.json").exists())

    def test_protocol_fingerprint_ignores_json_formatting_and_line_endings(self):
        self.manifest.write_text(json.dumps(self.protocol, indent=2), newline="\n")
        first = self.run_cli("lf")
        self.assertEqual(first.returncode, 0, first.stderr)
        self.manifest.write_text(json.dumps(self.protocol, indent=4), newline="\r\n")
        second = self.run_cli("crlf")
        self.assertEqual(second.returncode, 0, second.stderr)
        a = json.loads((self.root / "lf/summary.json").read_text())
        b = json.loads((self.root / "crlf/summary.json").read_text())
        self.assertEqual(a["protocol_sha256"], b["protocol_sha256"])

    def test_held_out_label_changes_do_not_change_fitted_model_or_selection(self):
        result = self.run_cli("first")
        self.assertEqual(result.returncode, 0, result.stderr)
        for entry in self.protocol["files"]:
            if entry["split"] == "test":
                path = self.root / entry["filename"]
                with h5py.File(path, "r+") as f:
                    data = f["emg2pose/timeseries"][:]
                    data["joint_angles"] += 1
                    f["emg2pose/timeseries"][:] = data
                entry["sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
        self.manifest.write_text(json.dumps(self.protocol))
        result = self.run_cli("second")
        self.assertEqual(result.returncode, 0, result.stderr)
        a = json.loads((self.root / "first/summary.json").read_text())
        b = json.loads((self.root / "second/summary.json").read_text())
        self.assertEqual(a["selection"], b["selection"])
        self.assertEqual(a["fitted_model_sha256"], b["fitted_model_sha256"])
        self.assertNotEqual(
            a["test"]["clean"]["aggregate"]["macro_mae_rad"],
            b["test"]["clean"]["aggregate"]["macro_mae_rad"],
        )

    def test_path_traversal_is_rejected(self):
        p = copy.deepcopy(self.protocol)
        p["files"][0]["filename"] = "../outside.hdf5"
        with self.assertRaisesRegex(ValueError, "filename"):
            pipeline.validate_protocol(p)


if __name__ == "__main__":
    unittest.main()
