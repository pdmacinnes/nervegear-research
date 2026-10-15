# emg2pose dataset audit

Audit date: October 14, 2026. This audit supports [issue 2](https://github.com/pdmacinnes/nervegear-research/issues/2) and [spec 001](../../specs/001-stationary-virtual-hand.md).

## Decision

The public starter archive supports a bounded software-only pilot. It does not support new-person, new-session, cross-day, or actual electrode-replacement evaluation. The proposed first experiment is therefore absolute hand-pose regression within one person's recording session, using disjoint stage recordings.

The archive contains 30 HDF5 files covering both hands, one anonymized person, one session, and 15 stages. The default upstream mini configuration uses only six files, split across three recordings. The archive is larger than that example configuration's selection.

All 30 starter files belong to the full dataset's validation split. A custom experiment that trains on them is not an official benchmark result. Preserve that distinction in every results table. No model has been trained or scored during this audit.

## Pin sources and permitted use

The audited upstream commit is `5f6f62b1a0a08426adffe55900842e75a8adb38c` from [facebookresearch/emg2pose](https://github.com/facebookresearch/emg2pose/tree/5f6f62b1a0a08426adffe55900842e75a8adb38c).

The upstream project declares CC-BY-NC-SA-4.0. UmeTrack has a separate CC-BY-NC-4.0 license. This project uses the dataset for noncommercial research and publishes no raw recordings. Retain source attribution and respect the separate terms when distributing adapted material. Do not describe the dataset or copied upstream code as permissively licensed. The repository's own license decision remains separate. [Upstream license](https://github.com/facebookresearch/emg2pose/blob/5f6f62b1a0a08426adffe55900842e75a8adb38c/LICENSE), [UmeTrack license](https://github.com/facebookresearch/emg2pose/blob/5f6f62b1a0a08426adffe55900842e75a8adb38c/emg2pose/UmeTrack/LICENSE)

The strongest directly relevant prior work is the authors' [emg2pose paper](https://arxiv.org/abs/2412.02725). Its velocity-based method integrates predicted motion and distinguishes regression from tracking with an initial reference pose. A small direct-regression CPU pilot is a comparison tool, not an attempt to reproduce its large-scale generalization scores.

## Verify acquisition and resource bounds

The [acquisition manifest](../../research/emg2pose/acquisition.json) records public URLs, exact sizes, and SHA-256 checksums. They identify the bytes received, not an independent guarantee about their publisher.

| Artifact | Observed size |
| --- | ---: |
| Metadata CSV | 5,674,462 bytes |
| Starter TAR | 647,198,208 bytes |
| Regular files after extraction | 647,172,814 bytes |
| Download total for metadata and starter TAR | 652,872,670 bytes |
| Current project data including archive, extraction, and metadata | 1,300,045,484 bytes |

The downloads fit the 1 GiB archive cap. Data on disk fit the 5 GiB cap. No full archive, GPU, paid service, or specialized device is required. Audit inspection used Python 3.12.14, NumPy 2.3.5, and h5py 3.14.0. The HDF5 reader was installed in an ignored local directory, without changing global packages. The proposed baseline uses a provisional two-thread, 15-minute CPU run budget. That runtime has not yet been measured.

Archive inspection found 32 members: one directory, 30 HDF5 files, and a metadata CSV. Extraction accepted only regular files and directories under the intended data directory. No archive member escaped that directory.

The full metadata contains 25,253 unique filenames, 193 anonymized people, 751 session identifiers, and 29 stages. These are metadata counts, not a claim that the full dataset was downloaded. The [audit results](../../research/emg2pose/audit-results.json) contain the observed starter-file counts and data-quality summaries.

## Read the actual file schema

Each inspected file contains `emg2pose/timeseries`, a structured HDF5 dataset. Its fields are:

| Field | Observed type and shape | Meaning |
| --- | --- | --- |
| `time` | float64, T | Absolute timestamps in seconds |
| `emg` | float32, T by 16 | One hand's recorded EMG channels |
| `joint_angles` | float32, T by 20 | Reference hand joint angles |

Attributes identify the source session, anonymized person, side, stage, sampling rate, split, and generalization category. The nominal EMG rate is 2,000 Hz. Across the starter files, positive timestamp steps ranged from about 0.450 to 0.550 ms. There were no nonpositive steps or nonfinite EMG or angle values.

The loader's introductory comment describes a different older field layout. The actual field constants and downloaded files agree on `emg`, `joint_angles`, and `time`. Build against the inspected schema rather than that comment. [Pinned loader](https://github.com/facebookresearch/emg2pose/blob/5f6f62b1a0a08426adffe55900842e75a8adb38c/emg2pose/data.py)

The 20 targets are four angles per finger. The thumb uses CMC flexion and abduction, MCP flexion, and IP flexion. Other fingers use MCP abduction and flexion, PIP flexion, and DIP flexion. Their order is defined in the [pinned constants](https://github.com/facebookresearch/emg2pose/blob/5f6f62b1a0a08426adffe55900842e75a8adb38c/emg2pose/constants.py). The source metrics treat angles as radians. Report radians and convert explicitly to degrees when presenting results. [Pinned metrics](https://github.com/facebookresearch/emg2pose/blob/5f6f62b1a0a08426adffe55900842e75a8adb38c/emg2pose/metrics.py)

## Mask reference failures and limit causal claims

The upstream validity heuristic rejects a timestamp if all 20 reference angles are close to zero under NumPy's default `isclose` behavior. It is a reference-failure mask, not a physiological rest label. Apply finite-value checks separately. [Pinned mask definition](https://github.com/facebookresearch/emg2pose/blob/5f6f62b1a0a08426adffe55900842e75a8adb38c/emg2pose/utils.py)

Across both hands, 659,172 of 4,218,756 samples match the rejected-pose heuristic, about 15.6%. Both hands were recorded concurrently, so these counts are not independent observations. A score that retains these invalid targets could reward predicting the failure representation. Report scored coverage for each file and use the same eligible timestamps for paired comparisons.

The paper describes preprocessing of recorded EMG and motion-capture-derived labels, including filtering and temporal upsampling. Those labels are reference estimates rather than unprocessed instantaneous physical angles. This audit does not establish causal timing for the original acquisition and label pipeline. Claim causality only for the new decoder operating on the released arrays. Do not infer sensor-to-percept latency from offline execution time. [Author datasheet and methods](https://arxiv.org/html/2412.02725v1#A1)

## Define a bounded pilot

The [pilot manifest](../../research/emg2pose/pilot-v1.json) fixes the proposed membership before model fitting:

| Partition | Recording numbers | Hand | Files |
| --- | --- | --- | ---: |
| Train | 1-9 | Left | 9 |
| Validation | 10-12 | Left | 3 |
| Test | 13-15 | Left | 3 |

Right-hand files remain unused. No contralateral recording of a test interval enters training. All partitions belong to the same source person and session. The test recordings cover freestyle and unconstrained stages. They introduce task differences within this session, not population-level evidence of generalization. The split is a custom pilot. It does not preserve the full dataset's training protocol or the [upstream mini split](https://github.com/facebookresearch/emg2pose/blob/5f6f62b1a0a08426adffe55900842e75a8adb38c/config/data_split/mini_split.yaml).

Predict all 20 angles without initial reference-pose access. Compare train-set mean and median poses with a ridge decoder using trailing-window EMG features. Compare nominal histories of 50, 100, and 200 ms at a 50 Hz output cadence. Use common warm-up and eligible timestamps across comparisons. Choose ridge strength and history on validation data only. Never use test labels for calibration or time-shift selection.

The primary score is the mean of the per-recording angular MAEs, with equal recording weight. Also report per-joint errors, sample-weighted MAE, and coverage. A long freestyle recording must not silently dominate the primary result. Three test recordings do not support uncertainty estimates across people.

The manifest lists deterministic dropout, gain, and noise conditions for sensitivity analysis. These are synthetic corruptions, not actual electrode-replacement or biological-drift validation. Missing timestamps and invalid inputs need explicit software failure behavior.

The protocol is a proposal based on an inspected dataset. The data-quality audit has seen reference masks and ranges. It is not a preregistered experiment or a blind test-set acquisition. No model error or performance score was computed.

## Claims this pilot cannot establish

It cannot establish new-user or new-session performance, cross-day robustness, actual electrode replacement, physiological rest detection, low-force stationary control, live user control, tactile benefit, embodiment, subjective perception, or clinical safety. It cannot reproduce an official generalization score from a one-person custom split.

Its useful deliverable is a reproducible CPU comparison with clear causality, masking, timing, and evaluation boundaries. A negative result completes that experiment if the method and limitations are reported.
