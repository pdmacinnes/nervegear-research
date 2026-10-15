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

Start with a simple baseline and measurements that can disprove the hypothesis. Evaluate live performance, idle false activations, timing, and generalization across recording sessions.

## Protect research participants and private data

Publish synthetic data, public datasets used under their terms, or appropriately consented and de-identified results. Do not commit raw personal biosignals, participant identities, consent documents, credentials, or private correspondence.

Human research requirements depend on the institution, jurisdiction, recruitment, and study design. Establish the applicable review and consent process before recruiting participants. The first proposed project uses recording and benign mechanical feedback. It does not propose implants, nerve stimulation, pain generation, or movement suppression.

## Review changes

Use a branch and pull request. Keep automatic merging disabled. Check local links, citations, units, evidence labels, and privacy before publishing. When executable features exist, add behavior tests before implementing them and maintain `FEATURE_MAP.md`.

The repository has no project-wide reuse license yet. Public visibility does not grant a new license to project material. Resolve the license before accepting substantial third-party contributions. Linked publications, datasets, and software keep their own terms.
