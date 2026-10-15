# Research roadmap

Evidence baseline: October 14, 2026. Time windows are research planning horizons, not predictions of full-dive availability.

## Start with one closed sensorimotor loop

The first question is whether low-force EMG and a small tactile channel support useful stationary virtual-hand control across days. See [spec 001](specs/001-stationary-virtual-hand.md). Its status is proposed, awaiting approval. No prototype has been implemented.

| Step | Work | Evidence required to finish |
| --- | --- | --- |
| 1. Audit the evidence | Read the key papers, verify metrics against results and methods, record important limitations | A traceable evidence record for each claim used to choose the experiment |
| 2. Approve the experiment | Fix the task, primary outcome, comparisons, data policy, budget, and first implementation scope | Maintainer approval recorded in spec 001 |
| 3. Establish a software baseline | Build a one-degree-of-freedom virtual grasp task using a conventional controller and synthetic signals | Repeatable task behavior, known ground truth, visible error conditions, and passing behavior tests |
| 4. Select recording hardware | Check available equipment and bench-test acquisition, raw signal access, synchronization, and electrical isolation | A reviewed parts list within the approved budget and measured acquisition performance |
| 5. Close the loop | Add EMG control, idle detection, mechanical feedback, and physical movement measurement | Measured end-to-end delay, false activations, movement, and task success |
| 6. Run a feasibility pilot | Compare visual-only, informative feedback, and control feedback across separate days | A complete report, including null or negative results and artifact checks |
| 7. Choose the research direction | Identify whether drift, feedback encoding, latency, or user learning limits performance | One follow-on hypothesis supported by the pilot |

The software baseline is a rehearsal of the task. Results from synthetic input do not establish that EMG control or tactile feedback works in a person. Select hardware after the task and measurement requirements are settled.

## Near term: 0-5 years

Approximately 2026-2031.

Work on reliable low-force motor readout, idle detection, sparse tactile feedback, and calibration after sensor replacement. Clinical research can extend bidirectional interfaces for a hand or limb and improve independent home use.

Demonstrate closed-loop performance across days and users, measure physical movement, control feedback artifacts, and compare with simpler interfaces. Add another control dimension only after the first is reliable.

This horizon has strong foundations in existing human demonstrations. It does not imply that arbitrary whole-body control or sensory replacement is available.

## Medium term: 5-15 years

Approximately 2031-2041.

Possible research targets include richer chronic sensory prostheses, simultaneous control of more body parts, distributed brain and peripheral interfaces, and better movement and load perception.

Before treating these as steps toward strict full-dive, demonstrate that added hardware creates independent perceptual dimensions. Show functional benefit without depending on constant visual compensation. Measure chronic usability, calibration burden, adverse events, and removal or recovery behavior.

Progress depends on uncertain advances in selectivity, materials, encoding, and sensory integration. The dates do not guarantee those advances.

## Long term: 15+ years

Beyond approximately 2041.

Strict full-dive would require coordinated sensory experience across the body while managing physical movement and contradictory natural sensation. It would also require acceptable chronic risk for the intended user population.

There is no defensible completion date. Some architectures may prove impractical. Better rendering alone cannot establish safe motor separation, natural proprioception, or vestibular replacement.

## Advance by demonstrated capability

1. Control one virtual action reliably.
2. Provide feedback that improves that action.
3. Establish useful embodiment of one virtual limb.
4. Support simultaneous actions and sensory inputs.
5. Produce convincing virtual movement while the physical body stays largely stationary.
6. Establish safe repeated operation across the intended functions.

Do not treat more electrodes, a larger model, an implantation announcement, or a regulatory designation as completion of a functional milestone.

## Keep the independent work bounded

The proposed first experiment has an estimated planning budget of USD 300-1,000 excluding a computer and optional headset. This is not a current vendor quote or authorization to buy hardware. Its first useful outcome is a reproducible measurement, not a full-dive claim.

Choose a project license before inviting substantial external contributions. Keep raw personal recordings private until a separate consent and release decision permits publication.
