# ARC-RVI work-version decisions and first full-text appraisal

**Reviewed:** 2026-10-28. **Study scope:** P02/P03/P04/P06 and peripheral P01/P08. This document separates (A) source-linked publication identity, (B) findings reported by outside studies, and (C) measurements made by ARC-RVI. **No new ARC-RVI empirical evidence was collected.**

## A. Work-version decisions (four approved, two pending)

All six pairs are recorded with original DOI strings, source URLs and dated decision state in [`work_version_relations.json`](work_version_relations.json). The source CSVs and 1695 DOI-first/title-fallback candidate keys are immutable input records.

| Canonical DOI | Alternate DOI | Work | Identity decision |
| --- | --- | --- | --- |
| [10.1109/IROS47612.2022.9982063](https://graphics.cs.wisc.edu/Papers/2022/SHPRZGM22/) | [arXiv:2208.04391](https://arxiv.org/abs/2208.04391) | Senft et al., *A Method For Automated Drone Viewpoints ...*, IROS 2022 | **Approved same work**: University research bibliography explicitly cross-links IEEE and arXiv |
| [10.1109/IROS47612.2022.9981472](https://doi.org/10.1109/IROS47612.2022.9981472) | [arXiv:2207.10543](https://arxiv.org/abs/2207.10543) | Breyer et al., *Closed-Loop Next-Best-View Planning ...*, IROS 2022 | **Approved same work**: publisher title/abstract plus full arXiv authors/title, IROS submission |
| [10.1145/3570731](https://doi.org/10.1145/3570731) | [arXiv:2307.15363](https://arxiv.org/abs/2307.15363) | Robinson et al., *Robotic Vision for Human–Robot Interaction and Collaboration*, ACM THRI 2023 | **Approved same work**: arXiv lists the exact related ACM DOI |
| [10.3390/robotics12040108](https://www.mdpi.com/2218-6581/12/4/108) | [arXiv:2306.06969](https://arxiv.org/abs/2306.06969) | Magaña et al., *Viewpoint Generation Using Feature-Based Constrained Spaces ...*, *Robotics* 2023 | **Approved same work**: complete publisher/preprint author and title match |
| 10.1109/tfr.2026.3733788 | [arXiv:2603.04284](https://arxiv.org/abs/2603.04284) | Zacharia et al., *OmniPlanner*, 2026 | **Pending**: [secondary journal index](https://eurekamag.com/research/110/972/110972090.php) matches title and authors; arXiv states T-FR acceptance, but the actual publisher article linkage is uninspected |
| [10.1016/j.oceaneng.2019.106420](https://cordis.europa.eu/project/id/779776/results) | [Zenodo 4253168](https://zenodo.org/records/4253168) | Bonnin-Pascual and Ortiz, vessel-inspection survey | **Pending**: CORDIS confirms *Ocean Engineering* DOI and 2019 work; repository item contents, version and its 2020 deposit provenance were not accessible |

**Derived count if run on the pinned eight-export inventory:** 1695 original candidate keys minus four specifically approved version links = **1691 provisional work keys**. Do **not** call this a unique-publications, eligible-study, PRISMA or systematic-review count. The two unapproved pairs remain as four independent candidate keys; 1907 exported mentions are unaffected.

Reproduce using the original archive and Python standard library only:

```bash
python scripts/audit_literature_exports.py /path/to/agent-artifacts-zip_robo.zip --output-dir /tmp/rvi-raw-audit
python -m scripts.reconcile_literature_versions \
  --candidates /tmp/rvi-raw-audit/work_candidates.csv \
  --inventory-summary /tmp/rvi-raw-audit/summary.json \
  --output-dir /tmp/rvi-reviewed-works
```

The reconciliation rejects source-archive hash mismatches and repeated/missing DOI relations, refuses to merge pending links and does not overwrite existing outputs. The CSV preserves the original candidate/source-row association.

## B. First source-method appraisal: Breyer et al., IROS 2022

Primary accessible [author preprint, HTML, sections III–V](https://arxiv.org/html/2207.10543v1); journal/conference version identified above. **This is a reviewed external method and report, not replicated data.**

- **Question and algorithm:** target-driven grasp discovery under occlusion; TSDF reconstruction, VGN grasp prediction and information-gain next-best-view search. Viewpoints are sampled above an initial target box and checked for IK reachability. The policy replans continuously and stops after a stable grasp prediction or time/information-gain threshold (sections III-A–C).
- **Platform:** a seven-degree-of-freedom Franka Emika Panda with wrist-mounted RealSense D435; PyBullet used separately for simulation. This is **not** Unitree G1 EDU.
- **Independent comparisons reported:** `initial-view`, `top-view`, `top-trajectory` and `nbv-grasp` under a common arm controller (section IV-C). Reported task endpoint: **successful grasp**, not independently accepted *inspected area*.
- **Reported sample and illustrative result:** 400 simulation attempts per policy (section IV-D); the table reports 89% success and 5.9 s mean search time for `nbv-grasp`, versus 91% and 9.5 s for `top-trajectory`. Four trials per policy for each of four real-world scenarios are reported (section IV-E). These are the authors' point summaries; no reanalysis or independently assessed confidence interval was performed here.
- **Important bias/transfer limits:** the paper explicitly excludes occasional trials where MoveIt cannot plan the final grasp path (section IV-A). Its proposed online view/grasp candidate generation checks IK **but does not perform scene collision checking**, acknowledged in section V. Initial target bounding boxes are assumed given. Therefore use this article as prior art for closed-loop target-centric NBV and stopping conditions, **not** as proof of all-failures-included whole-body safe inspection or uncertainty-calibrated target identification.
- **ARC-RVI consequence:** P02 must independently measure wrong-instance assignment with missing-target abstention; P03/P04 must retain motion infeasibilities, collisions and missing acquisitions in their estimands. Do not reuse grasp success as inspection-valid coverage.

## C. First source-method appraisal: Magaña et al., Robotics 2023

[Publisher HTML, methods, application and limitations](https://www.mdpi.com/2218-6581/12/4/108), corroborated by the [institutional metadata entry](https://portal.fis.tum.de/en/publications/viewpoint-generation-using-feature-based-constrained-spaces-for-r/). **This is a primary-source methodological reading, not a replicated experiment.**

- **Method:** geometrically construct valid, continuous sensor-pose sets in SE(3) using feature-based constrained spaces, incorporating imaging frustum, relative sensor angle, feature geometry, occlusion, calibrated kinematic uncertainty and robot workspace (sections 2–4).
- **Reported evidence:** simulation example plus a real robot-vision system with two sensor types; **not a bipedal whole-body, time-budgeted inspection test**. The article specifically addresses the viewpoint-generation subproblem, not complete autonomous mission control.
- **Crucial explicitly stated limitations:** sensing quality is assumed sufficient, and image-quality corruption from lighting, reflections and noise is outside the model; exposure, gain and resolution are not optimized. The work's robot model ignores dynamics such as velocity, acceleration, jerk and torque constraints, and assumes repeatability error small compared with pose accuracy (sections 2.6–2.8). Some of these assumptions are unsuitable for a humanoid moving during visual acquisition.
- **ARC-RVI consequence:** P03 cannot claim geometric/kinematically constrained viewpoint generation as new. A narrower hypothesis is whether **whole-body feasibility plus independently accepted visual quality and safety/time constraints** improves inspection success. P05 must measure camera-to-target return error rather than adopt the paper's negligible-repeatability assumption. P06 can test online quality recovery as a separate contrast.

## D. Evidence status and next actions

The first two article-level method extractions above are directly relevant to P02–P04 and P05–P06, **not** an eight-paper systematic review. P01/P07/P08 comparators, uncertainty/replication for more papers, DOI validation for the remaining corpus, six unresolved DOI-less 79-row matrix entries, and the literature flow of 1908→240→79 are still outstanding. See issues [#70](https://github.com/MatPomGit/arc-rvi/issues/70) through [#74](https://github.com/MatPomGit/arc-rvi/issues/74). No ARC-RVI physical results or original studies' effect sizes are inferred.
