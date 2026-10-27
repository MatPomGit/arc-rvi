# Critical prior-art appraisal: P02–P08

**Editorial evidence note (2026-10-27).** This table records 12 additional
bibliographic and abstract-level checks against named external pages, rather
than performing a full-text systematic review. The original research drafts
remain byte-for-byte unchanged. DOI keys, metadata and publisher/preprint
status are maintained in the
[reviewed manifest](https://github.com/MatPomGit/arc-rvi/blob/main/research/literature/verified_doi_metadata.json).
The [literature audit](literature.md) explains the incomplete 1,908/240/79
screening provenance and the 64 original bracket-number collisions.

## Evidence classification and direct comparator risks

The level here describes the evidence **reported by the cited work** in its
abstract or publicly accessible summary. It is not a validation performed by
ARC-RVI or a replica of the source paper.

| Study | Primary bibliographic record | Reported method and level | Implications / remaining check |
| --- | --- | --- | --- |
| P02 | [Fusion++, McCormac et al., 2018](https://doi.org/10.1109/3DV.2018.00015) | Online object-level RGB-D SLAM with semantic instance segmentation, TSDF maps and 6-DoF pose graph; RGB-D sequences and benchmark comparisons | Compare identity association separately from full SLAM; inspection pose repeatability is not its stated primary endpoint |
| P02 | [RoboEye, Zhang et al., 2025, arXiv](https://arxiv.org/abs/2509.14966) | Two-stage, 2D/geometry-aware re-ranking for visually similar objects in warehouse packing; **preprint** | Appearance/spatial fusion is established related work. ARC-RVI must show disjoint object/session generalization and abstention under inspection conditions |
| P03 | [Staderini et al., IROS 2024](https://doi.org/10.1109/IROS58592.2024.10802791) | Combines 3D object geometry, robot kinematics and inspection visibility for feasible viewpoints; abstract reports simulations and experiments | Do not call kinematics-aware inspection viewpoint optimization novel per se; inspect platform and matched motion-budget details |
| P03 | [Gemerek et al., T-RO 2022](https://doi.org/10.1109/TRO.2022.3180628) | Directional-sensor planning under occlusion constraints; bibliographic index confirms title and DOI | Distinguish P03's planned bipedal whole-body feasibility from generic line-of-sight constrained sensor routing |
| P03 | [Ghaleb et al., *Machines* 2026](https://doi.org/10.3390/machines14090980) | Visibility-risk navigation with CBF filtering and replanning; locked numerical/Gazebo evaluations | **Simulation evidence only** in the source; do not cite it as physical humanoid inspection validation |
| P03 / P04 | [Bettles et al., 2026, arXiv](https://arxiv.org/abs/2603.16471) | Coverage-first NBV, online geometry and stochastic collision constraints; reports **physical mobile-manipulator experiments** with a confined mock-up pipe network | An especially direct comparator. Novelty cannot be “physical NBV inspection in clutter”; residual question is humanoid-specific or different endpoint, with independent evidence |
| P06 | [Deng et al., *RCIM* 2024](https://doi.org/10.1016/j.rcim.2023.102619) | Learning-based predictive exposure control for vision-guided disassembly; publisher abstract | Image quality control predates P06; compare fixed budget and independently accepted inspection surface coverage, not merely exposure quality |
| P06 | [Zhang et al., *Sensors* 2022](https://doi.org/10.3390/s22249641) | Automatic exposure adjustment for two-camera **stereo-DIC metrology** | Not a robot inspection control-loop experiment; do not pool as evidence of physical robotic inspection |
| P06 | [Shin et al., IROS 2019](https://doi.org/10.1109/IROS40897.2019.8968590) | Noise-/gradient-/entropy-aware exposure and gain control in robot vision | Baseline for acquisition quality; only full-method review can establish comparable perturbations and datasets |
| P08 | [Kim et al., *Drones* 2022](https://doi.org/10.3390/drones6110355) | **Field comparison of human and UAS bridge inspection** | Precludes “first human-versus-robot inspection comparison”; not an autonomous humanoid documentation noninferiority test |
| P08 | [Gehring et al., *FSR* 2021](https://doi.org/10.1007/978-981-15-9460-1_18) | **Offshore physical field tests of quadruped ANYmal** for inspection | Precludes “first field-robot industrial inspection”; not a humanoid/manual controlled comparison |
| P08 | [Seppänen et al., *JIRS* 2022](https://doi.org/10.1007/s10846-022-01711-3) | Semi-autonomous mobile-robot teleoperation and communication delay with prototype tests | Time-delay/teleoperation comparator, **not** assessor-blinded image coverage or acquisition quality evidence |

A source's article summary may report experiments without fully explaining
its controls, sample size, calibration or statistical independence.
**Verification of bibliographic metadata is not verification of experimental claims.**
Bettles et al. is a preprint as catalogued, even though its manuscript reports
physical manipulator experiments; Ghaleb et al. is a journal article describing
numerical/Gazebo runs, not a physical robot deployment. Do not conflate
publication status with evidence level.

## Revised research differentiation

- **P02:** paired identity association in clutter with target-absent
  requests and abstention calibration. Baselines must include nontrivial
  visual matching/fusion beyond 8×8 synthetic texture. Its real-image and
  independent-identity reference remain missing.
- **P03:** joint view/motion planning on verified Unitree G1 EDU
  articulated/stability constraints under matched mission time. Do not
  claim novelty for generic kinematic viewpoint planning or 2D visibility.
  No physical G1 verification yet exists in ARC-RVI.
- **P04:** online unknown-surface coverage with hidden evaluator geometry
  and motion budget. Physical NBV inspection exists in the literature.
  Do not reuse P03's known-mesh primary result as new confirmation.
- **P06:** independent image-quality scoring plus bounded recovery and
  accepted inspection coverage at a common time budget, with the
  additional baseline of exposure optimization. A good exposure score
  alone is not a validated inspection outcome.
- **P08:** assessor-blinded paired manual versus fully autonomous
  *documentation*, with prespecified noninferiority margin, independent
  physical reference and failure accounting. Compare against UAS,
  quadruped and semi-autonomous field precedents, not only manipulators.

## Outstanding review protocol (not yet executed)

For every source that would support a final novelty statement, extract
the actual robot platform, sensor, acquisition scope, reference-truth
calibration, physical/simulation status, sample unit, method contrast and
uncertainty from the full manuscript and supplementary materials.
Resolve publisher/preprint version relationships and study-level
duplicate experiments. Record dated search queries and screening decisions,
then freeze the comparator list before a confirmation dataset is opened.

**Go/no-go:** P02–P08 remain **NO-GO for empirical submission claims**.
This document refines comparisons but cannot establish eight independent
publishable contributions or observed effect sizes.
