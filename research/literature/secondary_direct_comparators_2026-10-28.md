# ARC-RVI secondary-source targeted relevance appraisal (2026-10-28)

**Scope:** independent, selective appraisal of *secondary-only* DOI candidates
discovered in the 147 supporting CSVs of the contributor's existing archive.
The accompanying [whole-archive inventory](secondary_export_coverage_2026-10-28.md)
is the provenance and denominator reference. This document is **not** a
complete relevance screening of 2,858 identifiers or a systematic review.

**Review grades:** `M` = externally corroborated bibliographic metadata,
`A` = inspected abstract or publisher description,
`F` = inspected primary article text to the extent stated.
No `A`-grade source is represented as `F`. A source may be *direct
conceptual prior art* without proving equivalent hardware, terrain or endpoints.

| Candidate, DOI | Original CSV, row | Scope and evidence examined | Provisional ARC-RVI disposition |
| --- | --- | --- | --- |
| Monica, Aleotti & Piccinini, *Humanoid Robot Next Best View Planning Under Occlusions Using Body Movement Primitives*, [10.1109/IROS40897.2019.8968239](https://doi.org/10.1109/IROS40897.2019.8968239) | `scispace_viewpoint_motion_planning_2.csv#99` | **M**: IROS 2019 [official conference digest](https://www.iros2019.org/sites/g/files/asqsls1961/files/2019-11/IROS%202019%20Conference%20Digest_1.pdf) independently lists the paper; [bibliographic DOI cross-check](https://www.researchgate.net/publication/338942152_Humanoid_Robot_Next_Best_View_Planning_Under_Occlusions_Using_Body_Movement_Primitives). Full methods **not appraised**. | **P03: high-priority direct conceptual comparator.** Existence of humanoid NBV under occlusion defeats an unqualified claim that combining humanoid motion and viewpoint choice is unprecedented. Test distinct *inspection acceptance*, whole-body feasibility and terrain factors only after full-text review. |
| Chai, Gao & Lu, *Humanoid Whole-Body Control for Glass Curtain Wall Inspection Scenarios*, [10.1109/AIHCIR67580.2025.11404946](https://doi.org/10.1109/AIHCIR67580.2025.11404946) | `scispace_viewpoint_motion_planning_2.csv#69` | **M+A**: [independent proceedings/bibliographic abstract](https://eurekamag.com/research/105/697/105697122.php). Monocular-video motion retargeting/control is described; full text not examined. | **P03/P08: high relevance to humanoid inspection.** Hanging-basket/glass facade context differs from bipedal rough terrain. Check relationship to 2026 journal article below before counting independent evidence. |
| Chai et al., *VertInspect: Learning-based humanoid whole-body control for glass curtain wall inspection*, [10.1016/j.aei.2026.104590](https://doi.org/10.1016/j.aei.2026.104590) | **External follow-up, not in the secondary-only DOI queue** | **M+A, with publisher article sections inspected**: [publisher description and experiment overview](https://www.sciencedirect.com/science/article/pii/S147403462600282X) reports real-world humanoid deployment in hanging-basket glass-wall inspection and evaluation of motion tracking. Figures/results have **not** been independently reproduced. | **P03/P08: essential direct prior art.** Do not claim first humanoid inspection or first whole-body inspection control. Study/version relation to 2025 conference item is **unresolved**, with shared authors/subject, and must be checked before double counting. Does not establish safe bipedal rough-terrain inspection. |
| Preziosa et al., *FRA-NBV: A Fast and Reflectivity-Aware Next-Best-View Strategy*, [10.1109/LRA.2026.3728374](https://doi.org/10.1109/LRA.2026.3728374) | `scispace_active_visual_coverage_nbv_2.csv#81`; two secondary mentions | **M+A**: [IEEE publisher](https://ieeexplore.ieee.org/abstract/document/11669009) identifies reflectivity-associated missing depth and sensor-angle-adjustment reacquisition. [Author preprint](https://arxiv.org/abs/2608.01950) available; no independent experiment replication here. | **P04/P06: strong competitor** to a broad quality-aware NBV or imaging-recovery novelty claim. Require matched budget and independent inspection-valid acceptance metric; reflectivity-specific baseline where relevant. |
| Liu et al., *RASP: Robot Active Scene Perception With Joint Viewpoint Planning and Depth Completion in Cluttered Environments*, [10.1109/TASE.2025.3604455](https://doi.org/10.1109/TASE.2025.3604455) | `scispace_active_vision_reobservation.csv#41`; three secondary mentions | **M+A**: [IEEE publisher](https://ieeexplore.ieee.org/abstract/document/11145809) reports jointly learned sequence planning and depth completion under occlusion/unreliable depth; downstream grasping, not an independent inspection-grade endpoint. | **P04/P06: direct method comparator**, contextual for P02. Distinguish active sensing performance from independently certified visual inspection completeness. |
| Le et al., *CAIS: Culvert Autonomous Inspection Robotic System*, [10.1109/IROS58592.2024.10802162](https://doi.org/10.1109/IROS58592.2024.10802162) | `scispace_autonomous_robotic_inspection.csv#31`; two mentions | **M+F (limited)**: [public author manuscript on NSF repository](https://par.nsf.gov/servlets/purl/10595830) establishes a confined-space autonomous culvert inspection system integrating RGB-D sensing, lighting and non-destructive evaluation; [independent proceedings metadata](https://dblp.org/rec/conf/iros/LeWNZNNNL24). No independent reanalysis of outcomes. | **P08: strong end-to-end system comparator**, especially constrained access/lighting, but not a bipedal Unitree G1 EDU experiment. Full endpoints and intervention/failure rates require extraction. |
| Shahid, Janabi-Sharifi & Keenan, *A hybrid vision-based surface coverage measurement method for robotic inspection*, [10.1016/j.rcim.2018.11.009](https://doi.org/10.1016/j.rcim.2018.11.009) | `scispace_autonomous_robotic_inspection.csv#51` | **M+A**: [publisher abstract/method overview](https://www.sciencedirect.com/science/article/abs/pii/S0736584517302417) addresses visual coverage measurement for shot peening, not autonomous robot geometry exploration. | **P04: contextual measurement prior art, not a direct NBV policy benchmark**. Avoid conflating imaged treatment coverage with explored/unseen surface area. |

## Decisions on publication scope

1. **P03:** broad novelty claims for humanoid next-best-view or whole-body
   inspection motion cannot be defended. Make the hypothesis and comparator
   specific to constrained **G1 EDU bipedal terrain access**, independently
   evaluated inspection acceptance, and physically validated feasibility.
2. **P04/P06:** quality-aware viewpoint planning and recovery already have
   strong recent prior art (FRA-NBV, RASP). Distinct contribution must be tested
   through equal-budget comparisons, failure denominators, evaluator-held-out
   references and the predeclared inspection-valid end criterion.
3. **P08:** prior autonomous confined-access inspection (CAIS) and humanoid
   inspection (VertInspect) narrow the plausible novelty to **platform-specific
   and terrain-conditioned end-to-end reliability**, not a "first robot".
4. **Version control:** the 2025 conference item and 2026 VertInspect journal
   paper have overlapping authors and subject; classify as
   `possibly_related_work_versions`, not as two independent confirmations
   pending full-text relationship assessment.
5. **P07 and physical evidence:** none of these sources establishes
   ARC-RVI's simulator realism, actual G1 EDU hardware configuration,
   rough-terrain safety, experiment outcomes or a field-ready system.
   No go/no-go gate is relaxed.

## Required follow-up and review boundary

- Reconcile manuscript source claims with these verified **bibliographic**
  candidates; extract relevant *full methods, outcomes, data partition and
  limitations* before quantitative comparison.
- Explicitly add Monica et al. to P03; FRA-NBV/RASP to P04/P06; CAIS and
  VertInspect to P08 candidate comparator lists, with a full-text-pending flag.
- Screen the remaining secondary DOI leads using the source-indexed
  `secondary_only_doi_queue.csv` generated by the offline audit script;
  never silently auto-include, infer DOI accuracy from format or turn titles
  into fabricated methods/results.
- Preserve all current `PROJECT_STATE.yaml` scientific gates until evidence
  from executed, independently reproduced experiments exists.

**Editor status:** selective source-supported novelty-risk appraisal.
No new ARC-RVI simulation or physical experiments performed and no
systematic-search inclusion count established.
