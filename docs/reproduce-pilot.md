# Reproduce the CPU EMG pilot

Run the frozen experiment on an ordinary computer. Allow about 1.3 GB for data and at least 2 GB of free memory. No specialized device, GPU, paid service, or new recording is required.

## Install the runner

Use Python 3.12. From the repository root, create and activate a virtual environment. On Windows PowerShell:

```powershell
python -m venv .venv
.venv/Scripts/Activate.ps1
python -m pip install ".[dev]"
```

On Linux or macOS, activate with `source .venv/bin/activate` after creating the environment. The runtime dependencies are NumPy 2.3.5 for numerical operations and h5py 3.14.0 for HDF5. Ruff checks style. Build checks distribution packaging.

## Acquire the bounded starter data

Read the [dataset card](datasets/emg2pose.md) and its source licenses first. This experiment is noncommercial research. Do not redistribute the recordings.

The following PowerShell commands download the official 647,198,208-byte starter archive and verify its audited hash before extraction. Do not substitute the full dataset archive.

```powershell
New-Item -ItemType Directory -Force data/emg2pose-audit | Out-Null
$archivePath = 'data/emg2pose-audit/emg2pose_dataset_mini.tar'
Invoke-WebRequest 'https://fb-ctrl-oss.s3.amazonaws.com/emg2pose/emg2pose_dataset_mini.tar' -OutFile $archivePath
$expectedHash = 'd7400e98508ccbb2139c2d78e552867b23501f637456546fd6680f3fe7fec50d'
if ((Get-Item $archivePath).Length -ne 647198208) { throw 'Unexpected archive size' }
if ((Get-FileHash $archivePath -Algorithm SHA256).Hash.ToLower() -ne $expectedHash) { throw 'Archive checksum mismatch' }
New-Item -ItemType Directory -Force data/emg2pose-audit/extracted | Out-Null
tar -xf $archivePath -C data/emg2pose-audit/extracted
```

Extract only after both checks pass. The [acquisition manifest](../research/emg2pose/acquisition.json) also supplies the optional full metadata CSV URL and hash. The runner needs the starter HDF5 files, not that CSV. On other operating systems, download the same URL, verify the same size and SHA-256 digest, and extract to the same relative directory.

## Run a fresh experiment

```powershell
python -m nervegear_benchmark run --data-dir data/emg2pose-audit/extracted/emg2pose_dataset_mini --output runs/my-pilot-01
```

The runner verifies each declared file before fitting. It sets numerical-library thread limits to two and stops at 15 minutes. Choose a new output directory for every run. Existing outputs are never overwritten. The command exits nonzero on a checksum, schema, protocol, scoring, or output error. Exit 124 means the time limit fired. Only a directory with `completion.json` marked complete is a completed run.

Read `runs/my-pilot-01/report.md` and its plots. `summary.json` contains all nine validation candidates, the selected model, constant-pose baselines, three history comparisons, synthetic sensitivity, delay diagnostics, per-recording and per-joint errors, coverage, five timing passes, and resource use. `protocol.json` preserves the run configuration. Raw recordings, per-sample poses, and predictions are not copied into these outputs.

The [frozen manifest](../research/emg2pose/pilot-v1.json) is deliberately narrow. Unsupported numeric configuration changes fail rather than silently falling back. The protocol fingerprint hashes parsed JSON with sorted keys and compact separators, encoded as UTF-8. Indentation and line endings do not change that fingerprint. Source recording hashes still identify exact file bytes. A different study needs a protocol amendment and code/tests that implement it. Keep test results out of parameter selection.

## Diagnose the training-to-validation failure

After reproducing v1, run the approved diagnostics in a new directory:

```powershell
python -m nervegear_benchmark diagnose --data-dir data/emg2pose-audit/extracted/emg2pose_dataset_mini --output runs/my-diagnostics-01
```

This command verifies and opens only the nine training and three validation recordings. The three test files can be absent. It refits the same nine configurations, leaves v1 unchanged, and selects no replacement model. Read `report.md`, `summary.json`, and the three SVG plots in the new output directory. `diagnostic-config.json` records thresholds, file membership, and the existing primary model. Empty conditional groups have null errors, not fabricated zero error. Singular feature matrices carry an explicit flag and null unregularized condition number.

The [diagnostic report](experiments/decoder-diagnostics-v1.md) explains the findings and limitations. A successful run has a completion marker. The same CPU, time, data-integrity, and no-overwrite rules apply. No additional data or dependencies are required.

## Reproduce the fixed-prefix calibration study

```powershell
python -m nervegear_benchmark calibrate --data-dir data/emg2pose-audit/extracted/emg2pose_dataset_mini --output runs/my-calibration-01
```

The default study is [calibration-v1.json](../research/emg2pose/calibration-v1.json). Use `--calibration-protocol <path>` to name an explicit copy; unsupported settings fail. That option is valid only for `calibrate`. Fingerprints use canonical parsed JSON, independently of indentation and line endings.

The command opens only original training recordings 1-9. Each fold fits on the other eight, uses a fixed 10-second labeled prefix for intercept calibration and equally informed constants, and scores after a 200 ms embargo. It cannot use original validation/test recordings. A short or label-deficient fold is explicitly unsupported; an entirely unsupported study has null aggregate metrics and still reports its reasons.

Read the generated `report.md`, `summary.json`, `study.json`, two SVG plots, and completion marker. The [published report](experiments/limited-label-calibration-v1.md) explains the negative result and label-access limitations. Integrity fingerprints allow repeatability checks without publishing fitted coefficients or per-sample predictions. Existing resource, data-integrity, and no-overwrite rules apply. No new download or dependency is required.

## Reproduce the temporal alignment audit

```powershell
python -m nervegear_benchmark align --data-dir data/emg2pose-audit/extracted/emg2pose_dataset_mini --output runs/my-alignment-01
```

The default protocol is [alignment-v1.json](../research/emg2pose/alignment-v1.json). Use `--alignment-protocol <path>` for an explicit copy. This option is valid only for `align`. Unsupported settings fail. The command verifies and opens only original custom training recordings 1-9. Original validation and test files can be absent.

Each fold fits the fixed decoder on the other eight recordings. Predictions at the aligned time and at fixed signed shifts of 1 and 5 seconds share one scoring mask. Shifts use the original output grid, never a compressed list of valid rows. Source references are unnecessary. All source histories must follow the 10-second prefix, with endpoints after its 200 ms embargo and realized shift durations within the fixed 10 ms tolerance. Future sources are noncausal diagnostic controls.

The training-median and prefix-median controls use the same retained targets. Prefix median uses at least 25 valid prefix labels from the public recording. A fold needs at least 100 common scored outputs. Unsupported folds retain counts and reasons, while all-unsupported studies have null metrics. Empty fitting data cause an error even when target folds would be unsupported.

Read `summary.json`, `study.json`, `report.md`, the two SVG plots, and the completion marker. The [published report](experiments/temporal-alignment-v1.md) explains the primary mean-of-errors comparison, actual shift durations, and limits. Existing CPU, integrity, timeout, and no-overwrite rules apply. No new data or dependencies are required. For an installed package launched outside the checkout, supply absolute paths with both `--manifest` and `--alignment-protocol`.

## Verify the software

```powershell
python -m unittest discover -s tests -v
python -m ruff check .
python -m ruff format --check nervegear_benchmark tests
python -m build
```

The tests generate small synthetic HDF5 recordings and exercise the real command. They do not download data. There is no graphical application or live stream in this project. A package build and synthetic end-to-end command checks are the relevant release gate.

Compare scientific results with [the published report](experiments/emg2pose-pilot-v1.md). Allow timing to vary with hardware and desktop load. Identical model hashes are expected for the recorded environment; other BLAS implementations can introduce floating-point differences. Do not use this pilot as an official dataset leaderboard score.
