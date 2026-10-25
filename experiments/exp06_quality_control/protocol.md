# Study 06: Closed-Loop Quality-Aware Image Acquisition for Autonomous Robotic Inspection

**Status:** planned; no results or data collected by this repository.

## Research question
Can quality-aware reacquisition improve accepted coverage without excessive mission delay?

## Pre-registered hypotheses
- H0: Quality-triggered resampling provides no benefit under matched motion/time budget.
- H1: Closed-loop focus/exposure/coverage checks improve valid documentation completion.

## Baselines
One-shot fixed views; fixed multiple exposures; quality-only retry without replanning.

## Primary endpoint
Valid image-region coverage at a fixed mission-time budget.

## Design and independent unit
Blind perturbations to focus, lighting and occlusion with tracked retry counts, failure rates and energy/time cost.

## Research controls
- Freeze task definitions, baseline code and primary outcome before confirmation studies.
- Stratify held-out objects and sessions; no train/test leakage across repeated images.
- Replicate seeds and independently sampled scenarios; report negative trials too.
- Choose sample size from pilot variance or an explicit power/precision calculation.
- Version raw data, metadata, analysis code, calibration and commit hashes.
- Document uncertainty, effect sizes, confidence intervals, multiple-comparison policy and limitations.

## Publication and data
Corresponding manuscript: `papers/paper06/manuscript.tex`.
Quality feature computation and actual reacquisition are future integrations; threshold helper alone is not the method.
