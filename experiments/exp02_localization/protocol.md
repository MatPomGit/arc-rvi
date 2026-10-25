# Study 02: Robust Instance-Level Object Localization in Multi-Object Environments for Humanoid Robots

**Status:** planned; no results or data collected by this repository.

## Research question
Can spatial and visual observations jointly identify a requested object among visually similar instances?

## Pre-registered hypotheses
- H0: Fused spatial-visual identification does not improve target assignment over strongest unimodal baseline.
- H1: Joint identification reduces false assignments under occlusion and distractors.

## Baselines
Visual instance matching; geometry-only association; identification markers when permitted.

## Primary endpoint
Target identification precision/recall and false assignment rate per independently sampled scene.

## Design and independent unit
Vary object similarity, occlusion, crowding and sensor noise; test a held-out object population and limited physical trials.

## Research controls
- Freeze task definitions, baseline code and primary outcome before confirmation studies.
- Stratify held-out objects and sessions; no train/test leakage across repeated images.
- Replicate seeds and independently sampled scenarios; report negative trials too.
- Choose sample size from pilot variance or an explicit power/precision calculation.
- Version raw data, metadata, analysis code, calibration and commit hashes.
- Document uncertainty, effect sizes, confidence intervals, multiple-comparison policy and limitations.

## Publication and data
Corresponding manuscript: `papers/paper02/manuscript.tex`.
Keep identifying markers synthetic; do not report localization success before physical calibration.
