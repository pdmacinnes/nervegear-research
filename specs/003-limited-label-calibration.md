# Spec: Fixed-prefix calibration on held-out training recordings

## Requirements & Goals

Status: Explicitly approved by the maintainer through the spec-review prompt on October 14, 2026. This is the final task for tonight. Finish the approved study, publish its results, and stop without starting another experiment.

Test whether a small, fixed labeled prefix reduces recording-specific bias in the original RMS ridge decoder, and whether any benefit exceeds equally informed constant-pose controls. Use only original training recordings 1-9. Original validation and test recordings are excluded from loading, fitting, calibration, and scoring. These public recordings and previous v1 outcomes have already been inspected; this is exploratory analysis, not a new blind test or preregistration.

Retain the 200 ms RMS features and ridge alpha 10. Change only the fitted model's output intercept during calibration. Select no new hyperparameters, label durations, features, or models from results. Negative results and unsupported folds are valid outcomes.

The maintainer has no specialized hardware now or in the future. Use the existing data and Python dependencies on an ordinary CPU computer. No new download, GPU, paid service, electrodes, headset, implants, lab, participants, or recordings are required. Retain two numerical-library threads and the 15-minute command limit. This offline study depends on dataset reference angles; it does not provide a hardware-free live calibration method or physiological closed loop.

## Inputs, Outputs & Behavior

Inputs are the unchanged v1 source manifest, a new fixed calibration protocol, and nine existing training HDF5 files. Add `python -m nervegear_benchmark calibrate --data-dir <directory> --output <new-directory>`. Preserve `run` and `diagnose`. Use `--calibration-protocol` for an explicitly validated study manifest, with the repository protocol as default. Reject this option for other commands instead of silently ignoring it.

Write a new directory with the study configuration and canonical fingerprint, verified nine-file inventory, per-fold aggregate metrics, coverage and exclusion counts, a completion marker, a Markdown report, and SVG plots. Publish only code, configuration, aggregate metrics, and plots. Keep source samples, per-sample labels, residuals, predictions, and model coefficients out of published artifacts. Preserve v1 and diagnostic protocols and results.

The normal flow is:

1. Validate source metadata and select original training entries before checking recording files. Verify and open only recordings 1-9, using existing checksum, path, and schema checks. Record their hashes. Never require original validation or test files.
2. Reuse original common eligibility, target validity, 400-sample history, first output index 399, and 40-sample output stride. Require each recording's timestamps to be finite and strictly increasing so elapsed-time partitioning is unambiguous. Large positive gaps remain subject to history eligibility checks.
3. Hold out each of the nine recordings in turn. Fit feature standardization, ridge, train-mean pose, and train-median pose using eligible outputs from the other eight recordings only. No part of the held-out recording enters this initial fit.
4. Define elapsed time from the held-out recording's first source timestamp. Calibration uses eligible output timestamps with elapsed time strictly less than 10.0 seconds. The allowance is a fixed elapsed prefix, not a movable interval or a fixed number of favorable labels. Report actual eligible calibration outputs and excluded counts for every fold. All calibrated methods receive exactly the same valid labels.
5. Score eligible outputs only at elapsed time at least 10.2 seconds, with the entire trailing input window starting at or after 10.0 seconds. This supplies at least a 200 ms embargo between the prefix boundary and scored endpoints and prevents feature histories from overlapping the calibration prefix. Prefix and embargo outputs are excluded from every method's scored timestamps.
6. Require at least 25 valid calibration outputs and one eligible scored output. Otherwise mark the fold unsupported with its counts and reason. Never extend the prefix, move the boundary, shrink the gap, or substitute another recording after inspecting results. Unsupported folds are excluded from all six methods' paired aggregates and remain visible in the report. If all folds are unsupported, emit null aggregate scores and an explicit unsupported-study result rather than fabricated zeros.
7. Evaluate six fixed methods on identical scored timestamps in each supported fold: uncalibrated ridge, calibrated ridge, train-mean pose, train-median pose, prefix-mean pose, and prefix-median pose. Training-only constants use the other eight recordings. Prefix constants use only the held-out prefix labels. They receive the same label allowance as calibrated ridge but use no EMG for prediction.
8. Calibrate ridge with `offset = mean(prefix_reference - original_prefix_prediction)` per joint. Add this fixed vector to later predictions. Leave coefficients, input standardization, and all other fit parameters unchanged. Do not use later reference labels, a target time shift, or later outcomes to compute the offset. Prefix-median pose is the primary matched-label constant control; prefix mean is secondary.
9. Report per-fold MAE, per-joint MAE, MSE, RMSE, and coverage. Aggregate MAE with equal weight per supported fold, and report sample-weighted MAE separately. Macro RMSE is the square root of mean fold MSE. Report paired differences for calibrated ridge minus uncalibrated ridge and calibrated ridge minus prefix-median pose; negative means lower error. Report improved, tied, and worsened fold counts using a fixed 1e-12 radian tie tolerance. Do not select a winning method or change the protocol from those outcomes.
10. Measure wall time, CPU time, and peak memory. Distinguish internal runner time from full-process wall time measured by the reproduction check. Refuse existing output directories. Write a success marker only after all required outputs are written. Interpret resource numbers as execution checks, not real-time or speedup evidence.
11. Write the measured result and its limits, including every unsupported fold. State whether offset calibration helps relative to the uncalibrated model and the primary equally informed constant. Do not infer new-user performance, future hardware feasibility, intent readout, perception, or a biological cause. Finish this task without launching another study tonight.

The nine folds overlap in their training recordings and belong to one person/session. Do not treat folds or overlapping windows as independent biological replicates. Report descriptive paired results without population confidence intervals or significance tests.

## Edge Cases & Error Handling

- Absent or unusable original validation/test files cannot affect results. Missing or corrupt required training files fail explicitly before a completed output is published.
- Unsupported numeric protocol settings fail rather than falling back. Canonical JSON fingerprints ignore whitespace and line endings. Recording hashes continue to identify exact bytes.
- Nonfinite or nonincreasing timestamps fail with the filename. Invalid EMG histories or reference targets follow existing masks and are counted, not filled with synthetic data.
- A fold with no eligible fitting outputs fails explicitly. A constant input feature retains the existing unit-scale behavior.
- A short recording or insufficient valid prefix produces an unsupported fold as defined above. Aggregate scores use the same supported-fold set for every method. Zero supported folds produce null metrics and an explicit unsupported status.
- A nonfinite offset, prediction, or required score fails explicitly. Null is reserved for unsupported aggregates, not a substitute for numerical errors.
- A run that fails or exceeds 15 minutes cannot publish a successful completion marker. Do not acquire more data or add paid compute as a fallback.

## Acceptance Criteria

- [x] The maintainer confirms this specification before implementation.
- [x] A versioned calibration manifest fixes the nine folds, prefix, gap, minimum counts, history, alpha, methods, metrics, and resource limits before model fitting.
- [x] Tests fail for missing behavior before implementation, then pass. Known-answer tests verify prefix/gap boundaries, nonoverlapping histories, fixed offsets, equally informed constants, paired metrics, tie handling, and unsupported folds.
- [x] End-to-end tests succeed with only nine training files present and produce unchanged scientific output when unusable validation/test files are added.
- [x] Isolation tests prove that held-out prefix or future changes cannot alter the initial fold fit, and that changing future reference labels cannot alter calibration or predictions. Every method uses the same scored timestamps.
- [x] All nine folds have explicit support status, actual calibration-label counts, and exclusion counts. Six-method per-fold and aggregate results follow the fixed definitions without post-hoc changes.
- [x] A CPU command completes within existing limits without hardware, downloads, GPUs, or paid services. Repeated real-data runs and an installed-package command reproduce scientific results.
- [x] Prior v1 and diagnostic protocols and result artifacts remain unchanged. Raw and per-sample data and model coefficients remain excluded from publication.
- [x] The report explains measured outcomes, known data exposure, matched-label comparisons, and unsupported claims. Negative or unsupported results satisfy the research goal.
- [x] Update the reproduction guide and feature map. Tests, lint, formatting, builds, link/result checks, inspected plots, and Linux/Windows CI pass before delivery through a branch and PR with automatic merging disabled.
- [x] Stop after delivering this study tonight. Do not start another experiment, create a recurring task, or spend the remaining usage window on unrequested follow-on work.
