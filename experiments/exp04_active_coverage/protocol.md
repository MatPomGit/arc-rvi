# Study 04: Uncertainty-Aware Active Visual Coverage of Partially Unknown Objects

**Status:** planned; no results or data collected by this repository.

## Research question
Does epistemic uncertainty improve next-view choice for incomplete 3-D surfaces?

## Pre-registered hypotheses
- H0: Uncertainty-conditioned next-view selection does not reduce observations for matched coverage.
- H1: Adaptive information-gain planning achieves target coverage with fewer costly views.

## Baselines
Static coverage path; nearest unseen surface; classic next-best-view.

## Primary endpoint
Number and motion cost of accepted views to reach a pre-registered surface coverage threshold.

## Design and independent unit
Compare partially observed geometries and occlusions, with blind held-out shapes; measure calibration of uncertainty.

## Research controls
- Freeze task definitions, baseline code and primary outcome before confirmation studies.
- Stratify held-out objects and sessions; no train/test leakage across repeated images.
- Replicate seeds and independently sampled scenarios; report negative trials too.
- Choose sample size from pilot variance or an explicit power/precision calculation.
- Version raw data, metadata, analysis code, calibration and commit hashes.
- Document uncertainty, effect sizes, confidence intervals, multiple-comparison policy and limitations.

## Publication and data
Corresponding manuscript: `papers/paper04/manuscript.tex`.
Ground-truth surface coverage in simulation must be separated from estimated online coverage.
