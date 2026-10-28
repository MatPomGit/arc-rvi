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
| P03 / P04 / P08 | [OmniPlanner, Zacharia et al., arXiv v2, 2026](https://arxiv.org/html/2603.04284v2) | Full-text inspection: shared exploration/visual-inspection planner with camera FoV and 3D surface coverage; simulation compares with FC-Planner, and the authors report real aerial and underwater exploration–inspection missions. The IEEE T-FR DOI version linkage is still pending primary publisher check. | Do not claim novel unified exploration/inspection or the first field inspection on other robot morphologies. No verified humanoid whole-body feasibility, image-valid acceptance or manual-documentation noninferiority comparator. |
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

## Additional full-text source appraisal: OmniPlanner (2026-10-28)

[Zacharia et al., arXiv:2603.04284v2](https://arxiv.org/html/2603.04284v2),
version dated 2026-09-16. **Source methods and results were inspected in
sections 3–7**, not independently reproduced in ARC-RVI. The arXiv page
states acceptance by IEEE Transactions on Field Robotics; the publisher DOI
`10.1109/tfr.2026.3733788` remains a **pending version relation**, because
a direct publisher record linking DOI and manuscript was not checked.

- **Planning mechanism (section 4.C.2):** samples candidate camera poses under
  camera FoV, range, surface visibility and graph-level motion validity;
  greedily selects incremental surface coverage and routes the selected
  viewpoints with shortest paths and a TSP heuristic. This is established
  geometry-based planning, not a proposed ARC-RVI innovation.
- **Simulation comparator (section 5.C.3, Table 6):** five trials of aerial
  exterior pipe inspection against FC-Planner. The authors report covered
  surface 97.82 ± 0.93% versus 97.36 ± 0.49%, respectively. These are
  **reported simulation summaries**, not an independent G1 EDU study,
  assessor-accepted image quality or a replicated effect estimate.
- **Physical evidence (section 6, Table 9):** the paper reports aerial
  exploration plus visual inspection in a ballast-water tank and an underwater
  exploration–inspection mission in a submarine bunker. The ground field
  platform is the quadruped ANYmal; **no bipedal whole-body G1 experiment**.
  Field mission path/duration statistics alone do not establish blinded
  inspection quality or coverage accuracy against external ground truth.
- **Stated limit (section 7.D):** the planning kernel is intended mainly for
  holonomic or near-holonomic systems. Complex whole-body behaviors and
  task-specific perception uncertainty need additional modelling; graph-level
  path feasibility is not a guarantee about continuous configuration space.

**Resulting study gates:** P03 needs independently modelled bipedal stability,
articulated reachability and sensor geometry; P04 needs hidden evaluator
surface truth and accepted image coverage under a matched budget; P08 needs
blinded documentation quality and complete failure accounting. These
research questions are **candidate differentiators**, not established
novelty or findings. See the
[version review](https://github.com/MatPomGit/arc-rvi/blob/main/research/literature/work_version_review_2026-10-28.md)
and [manual source screening](https://github.com/MatPomGit/arc-rvi/blob/main/research/literature/manual_screening_decisions.json).

## Additional comparator appraisal: inspected 2026 sources

The full source-to-study extraction is maintained in the
[P03/P04/P06 evidence matrix](https://github.com/MatPomGit/arc-rvi/blob/main/research/literature/evidence_to_experiments_2026-10-28.md).
The appraisal date is **2026-10-28**; sources and evidence levels must not be conflated:

- **Staderini, 2026 [TU Wien doctoral thesis](https://repositum.tuwien.at/handle/20.500.12708/226537),
  DOI `10.34726/hss.2026.138640` (institutional abstract inspected):**
  combines spatial-resolution-aware and photometric visibility, kinematic
  pose refinement and optimised inspection routing. Its abstract reports
  synthetic and real work on systems of 3/6/8 DoF. This is more
  directly competing with P03/P06 than geometric NBV alone.
  **Do not assume independence** from the overlapping
  [Staderini et al., IROS 2024](https://doi.org/10.1109/IROS58592.2024.10802791)
  paper; numerical effects, sample independence and complete thesis
  methods have not been extracted.
- **Bettles et al., 2026
  [arXiv preprint](https://arxiv.org/abs/2603.16471), abstract inspected:**
  report physical mobile-manipulator coverage in a confined pipe
  mock-up using online geometry estimation and chance-constrained
  collision avoidance. The available abstract does not establish an
  independently calibrated coverage denominator, numerical effect
  size or confidence interval. It does preclude a claim that
  physically executed inspection NBV with uncertainty-aware
  obstacle avoidance is unprecedented.
- **Zhao et al., 2026
  [*Applied Sciences* full HTML](https://www.mdpi.com/2076-3417/16/18/9389),
  DOI `10.3390/app16189389`:**
  4-DoF eye-in-hand Dobot stereo arm, six scenes and 60 samples.
  Source-reported ROI evaluability is **70.0% initially,
  76.7% with an online proxy, 93.3% for operator-selected offline views**.
  The author-reported paired online-minus-initial mean Q interval is
  **95% bootstrap [−0.008, 0.060]**, which includes zero.
  The source reports **30 of 60 online cases** improved or
  recovered, but **does not provide independent ground-truth depth**.
  Quality-gated, constrained re-observation is established prior art.
  The 60 samples nested within only six scenes require careful
  interpretation of inferential independence.

For **P03**, a reference baseline now needs to represent *coupled*
viewpoint quality, kinematic feasibility and route planning, not merely
naive coverage greedy. For **P04**, compare observation-driven unknown-surface
coverage with withheld evaluator geometry and time-capped failures.
For **P06**, compare against bounded, quality-gated feasible-view recovery
as well as same-view retries and exposure controls. A source's ROI
stereo-quality score is **not** independent inspection-valid area or
absolute 3D measurement accuracy. See the prospective
[P03/P04/P06 protocols](../experiments/README.md) for acceptance gates.

## Humanoid locomotion in difficult terrain: direct evidence boundaries (2026-10-28)

The reference hardware is **Unitree G1 EDU**, whereas published experiments
below identify a **Unitree G1**. Their observed success must **not**
be transferred to the unverified G1 EDU variant, its actuators, sensor
payload, firmware or inspection task. "Full text" means that the
publisher/author HTML method or result sections were inspected; it does
not mean that ARC-RVI reproduced those experiments.

| Prior art / inspected evidence | Reported platform, terrain and outcome | Consequence for ARC-RVI |
| --- | --- | --- |
| [Wang et al., *RoboInspect*, 2026, DOI 10.1016/j.cacaie.2026.100007](https://www.sciencedirect.com/science/article/pii/S1093968726018153); **publisher methods/results listing** | Physical humanoid with RL locomotion, LiDAR–IMU navigation and crack vision; two **controlled indoor** inspection case studies in open space, corridors and a landing. Not an experimentally demonstrated full rubble or stair-climbing inspection programme | Cannot claim first physical humanoid structural inspection. Required contrast is inspection validity *conditional on challenging terrain and independently verified contact safety*, not simple completion of a mapped indoor route |
| [Zhang, Wu & Bräunl, *Autonomous Robots* 2026, DOI 10.1007/s10514-026-10263-6](https://link.springer.com/article/10.1007/s10514-026-10263-6); **publisher full HTML, methods and real-robot experiments** | FAWBC adapts whole-body controller weights using estimated ground normal/contact-force feasibility; physical **G1** tested on concrete, grass, wood chips and a 15° ramp; reported simulator baseline failure on a slope | Terrain-aware whole-body contact feasibility is **already established**; do not claim generic contact-aware locomotion as new, and do not import slope or friction thresholds to G1 EDU |
| [Compton, Olkin & Ames, arXiv:2605.15517 (2026)](https://arxiv.org/abs/2605.15517); **author preprint abstract** | Physical **G1** long-horizon navigation reported for more than 70 m on rough outdoor surfaces and consecutive stairs; reference-guided policy plus MPC/CBF high-level navigation | Challenging-terrain *autonomous navigation* is established prior art. Exact independent sample structure, safety margin and camera inspection acceptance were **not** extracted from this abstract |
| [Liu et al., arXiv:2609.02542 (2026)](https://arxiv.org/abs/2609.02542); **preprint HTML methods and experiments** | Physical **G1**, one depth stream and proprioception, traverses gaps, stairs and stepping stones; authors report mean hardware success 93.3% across three terrain categories. Target metric is locomotion, not inspection quality | Anticipatory foothold control on disconnected surfaces is prior art. Hardware experiments on one G1 and locomotion-success definition do not validate inspection viewpoints or G1 EDU safety |
| [Zhang et al., arXiv:2604.17335 (2026)](https://arxiv.org/abs/2604.17335); **preprint HTML methods/introduction and hardware abstract** | Physical **G1** performs whole-body traversal of boxes, hurdles, stairs and mixed terrain, with diffusion-based motion generation and RL tracking | Coordinated whole-body terrain adaptation is prior art; actual inspection-camera quality, target coverage and constrained-mission failure accounting are distinct untested questions |

**Research gap, stated as a testable proposition rather than a fact of
novelty:** all five sources separately address humanoid navigation,
terrain-adaptive contacts, or indoor inspection. None of the **inspected
material** establishes a matched experiment jointly measuring
*terrain-conditioned bipedal feasibility*, *accepted inspection-image
coverage*, *common mission deadline*, *operator intervention* and
*independently assessed failure modes*. This is a **bounded gap
identified in these sources**, not a claim that no other publication
exists. Complete source-method review, search update and competition
audit are still required before novelty certification.

**Required ablations:** (1) planar or geometric-only view routing;
(2) contact/whole-body-aware routing without image acceptance;
(3) quality-aware inspection planning with the **same** validated
contact constraints; (4) fully coupled contact/visibility/inspection
policy. Compare on the same supported terrain families, mission
budgets, observations and independent evaluators; account for fall
risk, slip, abort, unobservable region and unreached waypoint. Do
not implement or enable physical motion by adding these planned
ablation labels to a protocol.

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
