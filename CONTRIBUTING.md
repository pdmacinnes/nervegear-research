# Contribute research

Contribute a specific claim, correction, experimental question, or reproducible result through an issue or pull request.

## Support claims with evidence

- Link to an original paper, official trial record, author-maintained dataset, or documented institutional result.
- State whether the result involves humans, animals, an isolated tissue preparation, a simulation, or a proposed system.
- State separately whether the source is peer reviewed, a preprint, a company announcement, or a program objective.
- Include the task, sample size, units, and important limits when reporting a number.
- Separate electrode count, recording rate, task throughput, and perceptual resolution.
- Do not infer human capabilities from animal results or a program's target specifications.
- Label engineering assessments and proposed milestones as judgments rather than demonstrated facts.

## Propose experiments before implementation

Create a numbered document in `specs/`. Include requirements, inputs and outputs, failure conditions, and pass-or-fail acceptance criteria. The maintainer must approve the spec before implementation.

Start with a simple baseline and measurements that can disprove the hypothesis. For the current offline scope, evaluate held-out error, causal processing, timing, failure behavior, and generalization. Do not label replay as a closed loop with a person.

## Keep required work software-only

Assume the maintainer has no access to specialized hardware, now or later. Every required milestone must finish on an ordinary computer with public data, analysis, or simulation. Do not introduce purchases, electrodes, headsets, implants, recruitment, new recordings, lab access, GPUs, or paid cloud services as dependencies.

Keep large datasets out of Git. Audit archive size, extraction size, license, and split coverage before downloads. A small fixture can verify software but cannot establish scientific generalization. If recordings lack session, date, movement, or rest labels, omit the associated claim rather than inventing labels.

Record this constraint in each new spec's requirements and acceptance criteria. Hardware validation can remain an external scientific limitation without becoming unfinished project work. A future change to this scope requires an explicit maintainer request.

## Protect research participants and private data

Publish synthetic data, public datasets used under their terms, or appropriately consented and de-identified results. Do not commit raw personal biosignals, participant identities, consent documents, credentials, or private correspondence.

The current project uses public recordings and synthetic fixtures. Respect each dataset's terms and publish original measurements without redistributing restricted data. It does not recruit participants or collect new biosignals. Any future human experiment would require a separate scope decision and applicable review and consent processes.

## Review changes

Use a branch and pull request. Keep automatic merging disabled. Check local links, citations, units, evidence labels, and privacy before publishing. When executable features exist, add behavior tests before implementing them and maintain `FEATURE_MAP.md`.

The repository has no project-wide reuse license yet. Public visibility does not grant a new license to project material. Resolve the license before accepting substantial third-party contributions. Linked publications, datasets, and software keep their own terms.
