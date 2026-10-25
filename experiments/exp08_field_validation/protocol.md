# Study 08: Experimental Evaluation of Autonomous Humanoid Robots for Standardized Visual Documentation

**Status:** planned; no results or data collected by this repository.

## Research question
How does autonomous acquisition compare with standardized manual documentation under controlled field conditions?

## Pre-registered hypotheses
- H0: Autonomous inspection does not change completeness or between-operator variability at matched task requirements.
- H1: Autonomous acquisition reduces variability while maintaining required coverage; time and intervention trade-offs are measured.

## Baselines
Human operator using the same shot list; automated static-plan robot where feasible.

## Primary endpoint
Proportion of required image regions meeting predefined quality criteria per independent object/session.

## Design and independent unit
Balanced randomized order, blinded assessment, distinct operators and objects; preregistered mixed-effects analysis and failure reasons.

## Research controls
- Freeze task definitions, baseline code and primary outcome before confirmation studies.
- Stratify held-out objects and sessions; no train/test leakage across repeated images.
- Replicate seeds and independently sampled scenarios; report negative trials too.
- Choose sample size from pilot variance or an explicit power/precision calculation.
- Version raw data, metadata, analysis code, calibration and commit hashes.
- Document uncertainty, effect sizes, confidence intervals, multiple-comparison policy and limitations.

## Publication and data
Corresponding manuscript: `papers/paper08/manuscript.tex`.
A fully integrated physical system and ethics/safety/data approvals are needed before data collection.
