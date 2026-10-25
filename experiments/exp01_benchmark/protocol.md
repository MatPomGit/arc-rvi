# Study 01: Reproducible Simulation Benchmark for Autonomous Robotic Visual Inspection

**Status:** planned; no results or data collected by this repository.

## Research question
Can a diverse, repeatable benchmark expose robustness differences hidden by a single nominal scene?

## Pre-registered hypotheses
- H0: Robustness ranking across baseline methods is unchanged by scenario diversity.
- H1: Scenario diversity reveals reproducible method-by-condition differences.

## Baselines
Single nominal scenario; randomized but undocumented scenario sampling.

## Primary endpoint
Within-method success degradation across pre-specified conditions, with confidence intervals.

## Design and independent unit
Factorial synthetic scenes covering object geometry, occlusion, illumination and clutter; multiple independent seeds and held-out scenario families.

## Research controls
- Freeze task definitions, baseline code and primary outcome before confirmation studies.
- Stratify held-out objects and sessions; no train/test leakage across repeated images.
- Replicate seeds and independently sampled scenarios; report negative trials too.
- Choose sample size from pilot variance or an explicit power/precision calculation.
- Version raw data, metadata, analysis code, calibration and commit hashes.
- Document uncertainty, effect sizes, confidence intervals, multiple-comparison policy and limitations.

## Publication and data
Corresponding manuscript: `papers/paper01/manuscript.tex`.
A benchmark is publishable only after diverse external algorithms and tasks have been validated; fixture-only results are insufficient.
