# Research repository rules

This is an independently maintained academic research repository.

## Scope and naming
- Use neutral technical vocabulary and identifiers. Do not insert commercial project names, organizational affiliations, customer names, partner names or other people's names into project-specific identifiers, documentation, tests, issues, branch names or commits.
- The repository owner's name may appear where academically appropriate, including manuscript authorship and legitimate copyright notices. Bibliographic citations must remain accurate and preserve source authorship.
- Do not import proprietary proposals, source code, datasets, confidential correspondence, screenshots or logos. Avoid actual registration numbers and identifiable people in synthetic fixtures.
- Keep historical third-party license notices intact. Do not rewrite legal attribution to satisfy naming style.

## Engineering
- Prefer small, testable modules, Python standard library and simple interfaces.
- Keep generic algorithms independent of robot models, sensor vendors, physics engines and external defect classifiers.
- Distinguish `fixture`, `simulation` and `physical` evidence explicitly. Never present fixture results as physical validation.
- A robot adapter is incomplete until separately implemented and verified on authorized equipment.
- Safety interlocks and a human-authorized test procedure are prerequisites for physical motion.
- Do not run untrusted code on persistent hosts; do not enable paid hosted automation.
- Develop in a feature branch and open a PR. Run local offline tests and review diffs before merge. Do not invent approvals or results.

## Code quality and simplicity (mandatory)
- Follow **KISS** and **YAGNI**: make the smallest correct change. Avoid overengineering, speculative features, unnecessary layers, factories, wrappers, configuration switches and dependencies.
- **Inspect before creating**: search existing modules, scripts, CLI commands and tests. Extend the canonical implementation instead of creating similar programs, parallel runners, duplicate generators or alternative entry points.
- Prefer reusable, cohesive functions with clear inputs/outputs. Separate domain logic from CLI, I/O and hardware adapters; introduce shared abstractions only for demonstrated reuse.
- Follow applicable Python PEPs, especially **PEP 8** (style, imports, naming and formatting), **PEP 257** (useful docstrings) and **PEP 484** (type hints at public interfaces). Keep functions readable and reasonably short.
- Prefer the standard library and existing dependencies. Do not add a package or build tool unless it solves a concrete requirement better than the current code.
- Refactor duplication in place. Replace obsolete implementations and remove redundant scripts/files after checking all callers; never delete research evidence or required historical sources.
- Add focused tests for changed behavior and important edge cases; reuse current test fixtures and infrastructure. Run `python scripts/validate.py` and report the actual result. Do not claim tests passed if not run.
- Keep PRs scoped. Review the diff for duplicated logic, unnecessary files, complexity and regressions; after merge, delete the feature branch.

## Documentation and communication
- Document **what is needed to use, reproduce or verify** a change, not everything that could be explained. Keep text short, factual, structured and free of repetition or filler.
- Update existing canonical documentation instead of generating new READMEs, guides, summaries, status files or diagrams for each small change. Create a new document only when it has a distinct, lasting purpose.
- Keep comments and docstrings concise; explain non-obvious decisions and research constraints rather than narrating self-evident code. Give brief agent/PR reports: result, evidence, remaining blockers. No overexplaining.
- Simplicity never overrides scientific provenance, security, validation, physical safety or reproducibility requirements.

## Project state
- Read `PROJECT_STATE.yaml` and `AUTOPILOT_PLAN.md` before continuing work.
- Update canonical state after verified changes; do not copy state into parallel status files.

## Experiments and publications
- Every experiment defines hypothesis, baselines, outcomes, independent sampling units, splits, provenance, failure criteria and analysis before data collection.
- Avoid data leakage: when multiple images belong to the same physical object, use group-separated splits.
- Track source commit, configuration, dataset version, seed, environment and software dependencies for each run.
- Each manuscript needs a distinct question, contribution and disjoint primary analysis; disclose overlapping data and related manuscripts.
- The folder layout is scaffolding, not evidence of completed research.

## Security and repository hygiene
- Never commit secrets, private recordings, raw run data or participant-identifying material.
- Keep large artifacts outside Git; commit small public synthetic fixtures only.
- The optional local name scanner uses a denial list stored **outside** this repository.
- Do not remove or modify the existing third-party license without independent legal review.
