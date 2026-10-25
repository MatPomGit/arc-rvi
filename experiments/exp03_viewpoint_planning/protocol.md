# Study 03: Whole-Body-Aware Viewpoint and Path Planning for Humanoid Visual Inspection

**Status:** planned; no results or data collected by this repository.

## Research question
Does coupled viewpoint and motion planning improve the feasible coverage-cost trade-off?

## Pre-registered hypotheses
- H0: Joint planning is not better than independent viewpoint selection followed by route planning.
- H1: Kinematic and stability constraints plus joint optimization improve the coverage-cost Pareto frontier.

## Baselines
Nearest-neighbor route; greedy set cover; decoupled viewpoint/TSP baseline.

## Primary endpoint
Surface coverage under motion-feasibility and collision-free constraints at a fixed time budget.

## Design and independent unit
Cross-factor object shape, accessible space, joint limits and locomotion envelope; ablate pose feasibility and path cost.

## Research controls
- Freeze task definitions, baseline code and primary outcome before confirmation studies.
- Stratify held-out objects and sessions; no train/test leakage across repeated images.
- Replicate seeds and independently sampled scenarios; report negative trials too.
- Choose sample size from pilot variance or an explicit power/precision calculation.
- Version raw data, metadata, analysis code, calibration and commit hashes.
- Document uncertainty, effect sizes, confidence intervals, multiple-comparison policy and limitations.

## Publication and data
Corresponding manuscript: `papers/paper03/manuscript.tex`.
Current 2-D greedy planner is a baseline, not a whole-body motion planner.
