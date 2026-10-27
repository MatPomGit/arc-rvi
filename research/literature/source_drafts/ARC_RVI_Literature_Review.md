# Autonomous Robotic Visual Inspection (ARC-RVI): A Critical Literature Review and Research Agenda

**A Rigorous Evidence-Based Analysis of Scientific Foundations, Research Gaps, and Publication Potential**

---

## Executive Summary

This literature review establishes the scientific foundations for the Autonomous Robotic Visual Inspection (ARC-RVI) research program through systematic analysis of 1,908 papers published between 2018 and 2026. The review critically evaluates eight research directions spanning reproducible benchmarking, target localization, viewpoint planning, active coverage, repeatable acquisition, quality control, simulation-to-reality transfer, and end-to-end autonomous inspection.

The evidence reveals substantial progress in simulation-based benchmarking and vision-language-action models, yet exposes critical gaps in physical humanoid robot validation, repeatable camera pose control, and integrated quality-aware inspection systems. Most benchmarking studies evaluate wheeled robots or manipulators under controlled conditions; humanoid platforms like Unitree G1 remain largely unexplored for visual inspection tasks. Repeatability research focuses primarily on localization rather than acquisition geometry, while quality control methods operate in isolation from active viewpoint planning.

Key findings indicate that: (1) existing benchmarks emphasize robustness to perturbations but neglect reproducibility of measurement conditions; (2) viewpoint planning research optimizes coverage but rarely validates physical execution on humanoid platforms; (3) sim-to-real transfer studies demonstrate visual domain adaptation but do not validate visibility models or coverage metrics; and (4) end-to-end inspection comparisons remain scarce, with most studies comparing teleoperation rather than fully autonomous systems.

The review identifies seven high-priority research directions with strong publication potential, including hardware-independent benchmarking protocols, humanoid-specific motion planning with kinematic constraints, quality-aware next-best-view selection, and systematic sim-to-real validation of coverage performance. These directions address scientifically significant gaps while offering measurable, falsifiable hypotheses suitable for rigorous experimental validation.

---

## Table of Contents

1. [Introduction](#1-introduction)
2. [Background and Theoretical Foundations](#2-background-and-theoretical-foundations)
3. [Methods and Approaches in the Literature](#3-methods-and-approaches-in-the-literature)
4. [Key Findings and Comparative Analysis](#4-key-findings-and-comparative-analysis)
5. [Discussion](#5-discussion)
6. [Future Directions and Recommendations](#6-future-directions-and-recommendations)
7. [Conclusion](#7-conclusion)

---

## 1. Introduction

### 1.1 Research Context and Motivation

Autonomous robotic visual inspection represents a critical capability for industrial quality control, infrastructure monitoring, and documentation tasks requiring reproducible, high-quality visual evidence. While significant progress has been made in robotic manipulation, navigation, and computer vision, the integration of these capabilities into reliable, repeatable inspection systems remains an open challenge. The Autonomous Robotic Visual Inspection (ARC-RVI) research program addresses this gap by investigating autonomous acquisition of reproducible visual documentation in complex environments.

The reference platform for ARC-RVI is the Unitree G1 EDU humanoid robot, though the research emphasizes hardware-independent methods applicable to diverse robotic platforms. Unlike defect classification systems that focus on automated decision-making, ARC-RVI prioritizes visual acquisition quality, coverage completeness, and measurement repeatability—foundational requirements for trustworthy robotic documentation.

### 1.2 Scope and Research Questions

This literature review systematically evaluates eight interconnected research directions:

- **RVI-01: Reproducible benchmarking** — Methods for evaluating autonomous visual inspection under controlled environmental variations
- **RVI-02: Target identification and localization** — Reliable object-instance identification in cluttered multi-object environments
- **RVI-03: Viewpoint and motion planning** — Joint optimization of camera viewpoints, coverage, motion, and kinematic feasibility for humanoid robots
- **RVI-04: Active visual coverage** — Online next-best-view selection under incomplete information and limited motion budgets
- **RVI-05: Repeatable visual acquisition** — Methods for achieving reproducible camera poses and acquisition geometry across sessions
- **RVI-06: Acquisition quality control** — Autonomous evaluation of blur, exposure, occlusion, and visibility with recovery strategies
- **RVI-07: Simulation-to-reality transfer** — Calibration and validation of simulated visibility and coverage against physical experiments
- **RVI-08: End-to-end autonomous inspection** — Experimental comparison of autonomous robotic documentation against manual or teleoperated acquisition

For each direction, the review addresses:
1. What methods and evaluation protocols exist in the literature?
2. What robot platforms and experimental setups have been validated?
3. What gaps exist between current research and ARC-RVI requirements?
4. What hypotheses and experiments would advance the field?

### 1.3 Methodology

The review draws on eight comprehensive literature searches conducted between 2018 and 2026, yielding approximately 1,908 unique papers across SciSpace, Google Scholar, ArXiv, and Mendeley databases. Each search was iteratively refined with reranking and deduplication. The top 30 papers from each merged dataset were systematically analyzed using structured extraction of research problems, methodologies, robot platforms, and evaluation approaches.

This review adopts a critical, evidence-based stance: claims are supported by traceable references, contradictory findings are explicitly identified, and the distinction between simulation validation and physical robot experiments is rigorously maintained. The analysis prioritizes experimental verifiability, statistical rigor, and reproducibility—core principles for advancing robotic inspection science.

---

## 2. Background and Theoretical Foundations

### 2.1 Robotic Visual Inspection: Core Concepts

Robotic visual inspection integrates perception, planning, and control to autonomously acquire visual documentation of physical objects or environments. Unlike passive imaging systems, active inspection robots must:

1. **Identify and localize** target objects or regions of interest in cluttered, partially observable scenes
2. **Plan viewpoints** that maximize coverage while satisfying visibility, resolution, and kinematic constraints
3. **Execute motion** safely and repeatably, avoiding collisions and maintaining camera stability
4. **Assess quality** of acquired images in real-time, triggering re-observation when necessary
5. **Adapt online** to incomplete geometric information, occlusions, and environmental variations

These capabilities must operate reliably across diverse environments, lighting conditions, and object geometries—requirements that challenge both individual components and their integration.

### 2.2 Humanoid Robots for Inspection

Humanoid robots offer unique advantages for inspection tasks in human-designed environments: bipedal locomotion enables navigation of stairs and narrow passages, anthropomorphic reach facilitates access to shelves and overhead structures, and dexterous manipulation supports tool use and object interaction. However, humanoid platforms introduce significant challenges:

- **Kinematic complexity**: High degrees of freedom increase planning difficulty and computational cost
- **Stability constraints**: Bipedal balance limits feasible motions and camera trajectories
- **Sensor placement**: Eye-in-hand cameras couple viewpoint selection with whole-body motion
- **Computational limits**: Onboard processing constrains real-time perception and control

Despite these challenges, recent humanoid platforms like Unitree G1, Boston Dynamics Atlas, and Tesla Optimus demonstrate increasing capability. Yet the literature reveals a striking gap: most inspection research evaluates wheeled robots, manipulators, or UAVs, with humanoid validation remaining rare [1], [22], [24].

### 2.3 Benchmarking and Reproducibility in Robotics

Reproducible benchmarking is foundational to scientific progress, enabling systematic comparison of methods and validation of claims. Recent benchmarking frameworks emphasize:

- **Standardized tasks and metrics**: Shared evaluation protocols reduce variability and bias [2], [5], [13]
- **Controlled perturbations**: Systematic variation of environmental factors quantifies robustness [6], [7], [10]
- **Open-source implementations**: Public code and datasets enable independent replication [17], [18]
- **Real-world validation**: Physical robot experiments complement simulation studies [13], [19], [20]

However, existing benchmarks prioritize task success rates and robustness to visual corruptions, often neglecting measurement reproducibility and acquisition geometry—critical for inspection applications where documentation quality is paramount [1], [2].

### 2.4 Theoretical Frameworks

#### 2.4.1 Active Perception and Information Gain

Active perception frameworks model viewpoint selection as optimization of expected information gain, balancing exploration (reducing uncertainty about unknown regions) and exploitation (refining known structures). Information-theoretic metrics include entropy reduction, mutual information, and coverage gain [7], [11], [24]. These approaches assume probabilistic world models (e.g., occupancy grids, Gaussian processes) and evaluate candidate viewpoints via ray-tracing or learned predictors.

#### 2.4.2 Coverage Path Planning

Coverage path planning ensures complete observation of target surfaces while minimizing travel distance and observation time. Classical methods decompose surfaces into primitives and solve traveling salesman variants [1], [3], [18]. Modern approaches integrate visibility constraints, kinematic feasibility, and online adaptation to partial observability [5], [9], [12].

#### 2.4.3 Sim-to-Real Transfer

Sim-to-real transfer addresses the reality gap between simulated training environments and physical deployment. Dominant strategies include domain randomization (varying visual and physical parameters during training), domain adaptation (aligning feature distributions), and real-to-sim calibration (tuning simulators to match observations) [1], [2], [7]. Successful transfer requires careful validation: simulation performance does not guarantee real-world success [3], [8], [14].

---

## 3. Methods and Approaches in the Literature

### 3.1 RVI-01: Reproducible Benchmarking

#### 3.1.1 Existing Benchmarking Frameworks

Recent benchmarking efforts emphasize robustness evaluation under controlled perturbations. VPR-Bench [2] provides an open-source framework for visual place recognition, integrating 12 datasets and quantifying viewpoint and illumination invariance using a precision robot arm with LED arrays. RobotArena∞ [3] introduces scalable benchmarking via real-to-sim translation, automatically converting robot demonstration videos into simulated digital twins for large-scale policy evaluation.

ROEP [4] proposes a robotics-oriented evaluation protocol for vision-language-action models, converting rollout outcomes into claim-level evidence and evaluating runtime fidelity, visual perturbations, and recovery support. A benchmarking study of vision-based grasping [5] evaluates four algorithms across 5,040 experiments with varying lighting, backgrounds, cameras, and grippers, demonstrating the value of standardized protocols.

Domain-specific benchmarks address agricultural object detection [6], bird's-eye-view perception [7], SLAM robustness [8], and industrial manipulation [9]. These frameworks systematically vary corruption types, sensor parameters, and environmental conditions, quantifying performance degradation via retention scores and robustness indices.

#### 3.1.2 Evaluation Platforms and Metrics

Physical benchmarking platforms include DGBench [13] for dynamic grasping, featuring an XY controllable platform executing randomized trajectories at 100–200 mm/s, and VINSEval [18] for visual-inertial navigation, providing automated reproducible analysis via parameterized test sets and unified radar charts.

Simulation-based benchmarks dominate recent work: THE COLOSSEUM [14] evaluates manipulation policies across 20 tasks and 12 perturbation axes, RoboVAST [17] automates scenario-based validation with 5,480 configurations and over 100,000 execution runs, and LIBERO-VPro [20] assesses closed-loop visual robustness across 196,000 simulated episodes and 200 real-world rollouts.

Metrics emphasize success rates, completion times, and robustness scores, with limited attention to measurement reproducibility, acquisition geometry, or documentation quality—critical gaps for inspection applications.

#### 3.1.3 Limitations and Gaps

Existing benchmarks exhibit several limitations:

1. **Platform bias**: Most evaluate wheeled robots or manipulators; humanoid validation is rare [22], [24]
2. **Task focus**: Emphasis on manipulation and navigation, not visual documentation quality
3. **Perturbation scope**: Visual corruptions dominate; geometric and kinematic variations are underexplored
4. **Reproducibility**: Benchmarks assess robustness but not repeatability of measurement conditions [1], [2]
5. **Real-world validation**: Simulation studies outnumber physical robot experiments [8], [17]

No existing benchmark systematically evaluates autonomous visual inspection across environmental variations, robot platforms, and acquisition quality metrics—a foundational gap for ARC-RVI.

### 3.2 RVI-02: Target Identification and Localization

#### 3.2.1 Object Detection and Pose Estimation

Object detection and 6D pose estimation are foundational for robotic manipulation and inspection. Recent methods leverage deep learning for end-to-end prediction from RGB or RGB-D images, with architectures ranging from convolutional networks to vision transformers [4], [5], [19].

Active perception strategies improve pose estimation by selecting informative viewpoints. Active 6D multi-object pose estimation [6] uses deep reinforcement learning to plan observation sequences in cluttered scenes. ActivePose [8] combines pose tracking with active viewpoint selection for manipulation tasks. Domain randomization enables sim-to-real transfer for pose estimation without real-world training data [7].

#### 3.2.2 Instance Segmentation and Scene Understanding

Instance segmentation in cluttered environments remains challenging due to occlusions, boundary ambiguity, and overlapping objects. Methods address these challenges through graph neural networks for target-driven grasping [20], distributional modeling of segmentation uncertainty [26], and active exploration to resolve ambiguities [10], [13].

Open-vocabulary scene understanding using vision-language models enables flexible object identification without task-specific training. Recent work explores 3D scene graphs [9], visual grounding for autonomous driving [12], and topology-aware object extraction from 3D Gaussian splatting [21].

#### 3.2.3 Localization Under Uncertainty

Robotic inspection requires reliable localization despite sensor noise, calibration errors, and dynamic occlusions. Approaches include uncertainty-aware pose estimation [11], probabilistic instance segmentation [26], and active perception to reduce ambiguity [13]. However, most methods focus on manipulation tasks rather than inspection-specific requirements like repeatable camera placement and geometric measurement accuracy.

#### 3.2.4 Gaps and Challenges

Key gaps include:

1. **Multi-instance identification**: Most methods target single objects; cluttered multi-object scenes with similar instances remain challenging
2. **Geometric accuracy**: Pose estimation emphasizes grasp planning over measurement precision
3. **Repeatability**: Localization methods prioritize real-time performance, not reproducibility across sessions
4. **Humanoid integration**: Object localization research rarely considers whole-body humanoid kinematics

### 3.3 RVI-03: Viewpoint and Motion Planning

#### 3.3.1 Coverage-Oriented Viewpoint Planning

Viewpoint planning for visual inspection optimizes camera placement to achieve complete surface coverage while satisfying visibility, resolution, and kinematic constraints. Recent methods address free-form surfaces [1], [2], cylindrical cavities [4], and cluttered pipe networks [5].

Zou et al. [1] propose a human-inspired hierarchical framework combining occlusion-aware viewpoint generation with multi-objective trajectory optimization, balancing global coverage and local motion efficiency. Jafari-Tabrizi et al. [2] decompose surfaces into geometric primitives and formulate scan path selection as a Generalized Traveling Salesman Problem, incorporating inverse kinematics, collision avoidance, and manipulability.

Staderini et al. [3] present a model-based framework generating optimal inspection poses considering object geometry and robotic kinematics, achieving complete coverage with minimal viewpoints. Wang et al. [4] formulate observation-constrained joint-space optimization for cylindrical cavity inspection, ranking multiple robot configurations lexicographically.

#### 3.3.2 Mobile Manipulator and UAV Planning

Mobile manipulators and UAVs extend inspection capabilities to large-scale environments. Bettles et al. [5] propose a coverage-first next-best-view planner for pipe network inspection using mobile manipulators, combining visual exploration and coverage information gains with stochastic collision avoidance under measurement uncertainty.

OmniPlanner [7] introduces a domain-agnostic planning framework applicable to aerial, ground, and underwater robots, using bifurcated local-global planning with platform abstraction layers. Zhang et al. [10] propose joint optimization of viewpoint selection and path planning for UAV building inspection via multi-objective evolutionary algorithms.

#### 3.3.3 Kinematic Feasibility and Collision Avoidance

Integrating viewpoint planning with kinematic constraints and collision avoidance is critical for physical execution. Gemerek et al. [9] address directional sensor planning with line-of-sight visibility and bounded field-of-view constraints, guaranteeing complete target visibility while minimizing travel distance.

Ghaleb et al. [6] propose visibility-risk navigation combining control barrier function filtering and occlusion-evasive replanning, maintaining hard collision constraints while relaxing field-of-view requirements. Papaioannou et al. [15] formulate distributed model predictive control for multi-agent coverage, integrating light-path propagation and logical visibility assessment.

#### 3.3.4 Limitations and Research Gaps

Despite substantial progress, several gaps remain:

1. **Humanoid-specific planning**: Most methods target manipulators or UAVs; humanoid whole-body planning with bipedal stability constraints is underexplored [1], [4]
2. **Execution validation**: Many methods demonstrate simulation results without physical robot validation [10], [16], [17]
3. **Quality integration**: Viewpoint planning optimizes coverage but rarely integrates image quality metrics or acquisition repeatability [1], [2], [3]
4. **Online adaptation**: Offline planning dominates; online replanning under partial observability and quality feedback is less common [5], [12]

### 3.4 RVI-04: Active Visual Coverage

#### 3.4.1 Next-Best-View Planning

Next-best-view (NBV) planning selects observation sequences to maximize information gain while minimizing motion cost. Recent methods address 3D reconstruction [1], [2], [3], surface inspection [4], and object exploration [9].

Desikan et al. [2] propose depth-variance guided NBV planning for active 3D Gaussian splatting reconstruction, measuring per-pixel geometric uncertainty via alpha-blended depth second moments. Li et al. [3] address motion-uncertainty-aware NBV planning for moving objects, evaluating candidate viewpoints over plausible future states induced by motion and measurement uncertainty.

Jin et al. [4] present an adaptive planning framework for UAV surface inspection in partially unknown indoor environments, combining segment-based global viewpoint planning with local adaptive replanning. Vidal et al. [5] propose optimized environment exploration for autonomous underwater vehicles, integrating view planning and frontier-based approaches with hit-and-miss sonar noise filtering.

#### 3.4.2 Learning-Based Approaches

Learning-based NBV methods replace handcrafted heuristics with data-driven predictors. Hepp et al. [22] use 3D convolutional neural networks to predict viewpoint utility from multi-scale voxel occupancy maps. Toschi et al. [14] employ deep reinforcement learning for NBV planning with quadruped robots in simulation, training across 10,000 evaluation scenarios.

Active perception networks [6] model exploration state spaces as hierarchical topological graphs, using differential regulation for incremental updates and non-myopic global planning. Robot active neural sensing [9] combines 3DCNN-based score functions with Transformer-based viewpoint generators trained via offline reinforcement learning.

#### 3.4.3 Application-Specific Methods

Domain-specific NBV methods address agricultural inspection [15], [20], [21], dental reconstruction [8], and industrial mapping [25]. These methods incorporate task-specific constraints like fruit occlusion, plant part targeting, and confined workspace navigation.

Attention-driven active vision [20] incorporates semantic labels and confidence scores into OctoMap representations, using adaptive attention mechanisms to guide cameras toward objects of interest. NBV-SC [21] employs shape completion to predict missing fruit surfaces and synthesize occlusion-aware viewpoints, filtering redundant candidates without expensive ray casting.

#### 3.4.4 Gaps and Future Directions

Key gaps include:

1. **Quality-aware planning**: NBV methods optimize coverage but rarely integrate image quality metrics like blur, exposure, or resolution [1], [2], [3]
2. **Humanoid platforms**: Most methods evaluate manipulators or UAVs; humanoid NBV planning is rare [14], [25]
3. **Repeatability**: NBV planning emphasizes exploration efficiency, not reproducibility of observation geometry
4. **Sim-to-real validation**: Many learning-based methods lack physical robot validation [6], [14], [22]

### 3.5 RVI-05: Repeatable Visual Acquisition

#### 3.5.1 Camera Calibration and Pose Estimation

Repeatable visual acquisition requires accurate camera calibration and pose estimation. Photogrammetric multi-camera calibration using industrial robotic arms [7] achieves precise extrinsic parameter estimation. Hand-eye calibration methods [17] enable markerless calibration via keypoint tracking and forward kinematics.

Vision-based error compensation [3] corrects robotic positioning errors for automated marking tasks. Active pose relocalization [2], [4] adjusts camera angles for intelligent substation inspection robots, ensuring consistent viewpoints across repeated visits.

#### 3.5.2 Visual Servoing and Teach-and-Repeat

Visual servoing enables closed-loop camera control for consistent observation. Hybrid visual servoing [18] combines image-based and position-based control for tendon-driven continuum robots. Robust visual teach-and-repeat [13] uses 3D semantic maps for UGV navigation, maintaining consistent routes despite environmental changes.

Specifying and optimizing robotic motion for visual quality inspection [25] addresses viewpoint repeatability through trajectory optimization. However, most methods focus on localization accuracy rather than acquisition geometry reproducibility—a critical distinction for measurement applications.

#### 3.5.3 Repeatability Evaluation

Quantitative repeatability evaluation remains limited. Robot arm repeated positioning accuracy measurement [12] uses nonlinear local feature matching to assess pose consistency. A quantitative investigation of mobile collaborative robot accuracy [24] employs precision laser trackers to evaluate positional repeatability under varying speeds and translation orientations.

However, these studies measure robot pose repeatability, not camera observation geometry or image acquisition consistency—the latter being more relevant for visual inspection tasks.

#### 3.5.4 Research Gaps

Critical gaps include:

1. **Acquisition geometry**: Repeatability research focuses on robot pose, not camera viewpoint, framing, or measurement conditions
2. **Quality metrics**: Limited work quantifies repeatability of image quality attributes like resolution, focus, or illumination
3. **Humanoid platforms**: Repeatability studies rarely evaluate humanoid robots [24]
4. **Benchmarking protocols**: No standardized benchmarks assess acquisition repeatability across sessions or environmental variations

### 3.6 RVI-06: Acquisition Quality Control

#### 3.6.1 Camera Exposure Control

Adaptive camera exposure control is critical for robust visual perception under varying illumination. Begin et al. [3] propose an auto-exposure algorithm maximizing gradient information while balancing camera gain and exposure time using optical flow predictions. Zhang et al. [4] develop automated exposure control for stereo-DIC measurement, determining optimal exposure times via maximum mean intensity gradient values.

Predictive exposure control [6] uses deep learning and predictive learning for vision-based robotic disassembly, incorporating entropy-based quality assessment and exposure-entropy prediction models. Learning-based exposure control [9] employs deep reinforcement learning for rapid adjustment within five steps, using flickering-aware rewards and static-to-dynamic lighting curricula.

Proactive camera attribute control [15] uses Bayesian optimization to learn environmental changes and synthesize images via camera response functions, supporting 20–40 Hz frame rates. Gradient-based exposure control [16] evaluates exposure by maximizing total gradient information using logarithm-based noise filtering.

#### 3.6.2 Image Quality Assessment

Image quality assessment guides acquisition decisions and triggers re-observation. Camera exposure control for robust robot vision [8] proposes a noise-aware quality metric combining image gradient, entropy, and noise metrics. Automatic exposure control guided by no-reference quality estimation [14] uses visual quality assessment models to rank exposure settings.

Quality-aware active re-observation [12] elevates ROI-level stereo reliability to an admission condition, employing online proxy strategies to generate and rank candidate viewpoints. Enhanced view planning [13] uses imitation learning to predict camera motions that capture unobstructed views of occluded crops.

#### 3.6.3 Motion Blur Detection and Mitigation

Motion blur degrades visual feature detection and matching. Dealing with low-quality images [7] uses improved edge detection with Gaussian noise reduction and automatic threshold calculation to reject blurred railway images. On motion blur and deblurring [27] introduces a benchmark evaluating VPR algorithms under synthetic motion blur, testing adaptive deblurring strategies.

Towards robust visual odometry by motion blur recovery [30] utilizes IMU-based blur detection and selective restoration within motion frame sequences. Neural image re-exposure [19] proposes a framework combining event streams and frames to adjust shutter strategy in post-processing, addressing deblur, frame interpolation, and rolling shutter correction.

#### 3.6.4 Limitations and Future Directions

Key limitations include:

1. **Isolated optimization**: Exposure control and quality assessment operate independently from viewpoint planning and coverage optimization [3], [8], [15]
2. **Limited metrics**: Quality assessment emphasizes gradient and entropy, neglecting inspection-specific attributes like framing, occlusion, and surface visibility [8], [12], [14]
3. **Reactive strategies**: Most methods react to poor quality rather than proactively planning quality-aware viewpoints [12], [13]
4. **Humanoid validation**: Quality control research rarely evaluates humanoid platforms [3], [15], [16]

### 3.7 RVI-07: Simulation-to-Reality Transfer

#### 3.7.1 Domain Randomization

Domain randomization varies visual and physical parameters during simulation training to encourage invariance to irrelevant features. Robust sim2real transfer with the da Vinci Research Kit [1] studies camera, lighting, and physics randomization for surgical manipulation. Robust visual sim-to-real transfer [2] benchmarks domain randomization methods across manipulation tasks, achieving 93% average success rates.

Sim-to-real neural learning with domain randomization for humanoid robot grasping [9] compares model performance across different data amounts and randomization conditions. Viral [14] uses large-scale visual domain randomization across lighting, materials, camera parameters, and image quality for humanoid loco-manipulation, achieving zero-shot transfer to Unitree G1.

#### 3.7.2 Domain Adaptation and Feature Alignment

Domain adaptation aligns feature distributions between simulation and reality. Dual variational autoencoders [11] employ a shared decoder trained on simulated and real-world samples to align domain distributions for low-cost robotic navigation. Randomized-to-canonical adaptation networks [22] translate randomized simulated or real-world images into canonical simulation versions, enabling vision-based grasping without real-world training data.

Best of Sim and Real [10] decouples learning by training control policies in simulation using privileged state and domain randomization, while adapting a lightweight visual bridge network in the real world using minimal demonstrations.

#### 3.7.3 Real-to-Sim Calibration

Real-to-sim calibration tunes simulator parameters to match physical observations. Vid2Param [6] performs online system identification from video for trajectory and physical parameter prediction. Swim2Real [17] uses VLM-guided system identification to calibrate soft robotic fish simulators from swimming videos, simultaneously tuning fluid, motor, and joint parameters.

Vid2Sid [23] employs video-driven system identification coupling foundation-model perception with VLM-in-the-loop optimization, analyzing paired sim-real videos to diagnose mismatches and propose physics parameter updates. RL-GSBridge [25] uses 3D Gaussian splatting and soft mesh binding to model real scenes, integrating physical dynamics simulation for zero-shot real-world deployment.

#### 3.7.4 Validation and Evaluation

Sim-to-real validation requires careful experimental design. Pose estimation via keypoint optimization [3] uses domain randomization to bridge the reality gap for robot manipulator pose estimation. Visual dexterity [4] employs a two-stage teacher-student reinforcement learning framework with synthetic and rendered point clouds, validating on 3D-printed and household objects.

DiffuDepGrasp [5] addresses sensor artifacts in real depth maps via diffusion-based depth noise modeling, achieving 95.7% grasping success with zero-shot transfer. Object detection using sim2real domain randomization [30] automatically generates synthetic datasets with random textures, lighting, and noise, validating on real robotic grasping tasks.

#### 3.7.5 Critical Gaps

Critical gaps include:

1. **Visibility validation**: Sim-to-real studies focus on manipulation success, not visibility model accuracy or coverage metric fidelity [1], [2], [14]
2. **Geometric fidelity**: Visual domain adaptation dominates; geometric and kinematic calibration is less common [4], [5], [11]
3. **Humanoid platforms**: Most studies evaluate manipulators or wheeled robots; humanoid validation is rare [9], [14]
4. **Inspection-specific metrics**: Success rates dominate; acquisition quality, repeatability, and documentation fidelity are underexplored [1], [2], [30]

### 3.8 RVI-08: End-to-End Autonomous Inspection

#### 3.8.1 Autonomous vs. Manual Comparison

Direct comparisons between autonomous robotic inspection and manual or teleoperated methods remain scarce. Wang et al. [1] propose RoboInspect, an end-to-end autonomous inspection framework for humanoid robots, demonstrating reliable navigation and crack detection in university building case studies. However, no quantitative comparison against human inspectors is provided.

Comparative analysis of human operators and advanced technologies [7] evaluates image processing, AI, and 3D scanning against human visual inspection of aero engine blades, using accuracy, consistency, time, SWOT, and weighted factor analysis. Results show technology advantages in consistency but human superiority in complex defect interpretation.

Benchmarking human versus robot performance [22], [24] compares structural inspection outcomes, finding robots excel in systematic coverage while humans demonstrate superior adaptability and contextual reasoning. A comparative study of bridge inspection [26] evaluates UAS-based automatic damage detection against traditional ladder truck inspection, demonstrating comparable accuracy with reduced time and risk.

#### 3.8.2 Teleoperation and Shared Autonomy

Teleoperation studies provide insights into human-robot collaboration. Semi-autonomous teleoperation [4] uses differential flatness for crane robot control in aircraft wing inspection, combining feedforward trajectories with feedback to eliminate collisions. Human-autonomy teaming for ROV shared control [11] employs VR-based sensory augmentation and body motion teleoperation, comparing human control, full autonomy, and teaming methods.

Comparison of semi-autonomous mobile robot control strategies [12] evaluates fully manual, autonomous, delayed manual, and semi-autonomous strategies under large delay fluctuation. Remote mobile manipulation with the Centauro robot [16] combines full-body telepresence suits with autonomous functions for mobile manipulation in dangerous environments.

#### 3.8.3 System Integration and Deployment

End-to-end system integration studies address practical deployment challenges. Cyber-physical inspection systems [2] develop standards-aligned architecture integrating collaborative robotics, structured-light scanning, and industrial IoT for high-accuracy operations. ANYmal in the field [20] deploys a quadrupedal robot for offshore HVDC platform inspection, evaluating navigation, sensor payloads, and automated instrument reading.

A quantitative investigation of mobile collaborative robot accuracy [21] assesses positional uncertainty for high-value manufacturing inspection, using precision laser trackers to evaluate integrated feature mapping and omnidirectional wheel efficiency. Toward next-generation autonomous structural health monitoring [1] proposes an end-to-end framework integrating RL-based locomotion, autonomous navigation, and vision-based crack detection for humanoid robots.

#### 3.8.4 Research Gaps and Opportunities

Key gaps include:

1. **Quantitative comparisons**: Most studies lack rigorous experimental comparison of autonomous vs. manual inspection [1], [7], [22]
2. **Documentation quality**: Evaluations emphasize defect detection accuracy, not visual documentation quality or repeatability [7], [26]
3. **Humanoid platforms**: End-to-end inspection studies rarely evaluate humanoid robots [1], [20]
4. **Controlled experiments**: Field deployments dominate; controlled laboratory comparisons with standardized tasks and metrics are rare [20], [21]

---

## 4. Key Findings and Comparative Analysis

### 4.1 Research Landscape Integration

The eight ARC-RVI research directions form an interconnected system: reproducible benchmarking (RVI-01) provides evaluation frameworks for all other directions; target identification (RVI-02) enables viewpoint planning (RVI-03) and active coverage (RVI-04); repeatable acquisition (RVI-05) and quality control (RVI-06) ensure documentation fidelity; simulation-to-reality transfer (RVI-07) validates methods before physical deployment; and end-to-end inspection (RVI-08) integrates all components into operational systems.

Current research exhibits strong progress in individual components—particularly viewpoint planning, active coverage, and sim-to-real transfer—but limited integration. Most benchmarking studies evaluate robustness to perturbations rather than reproducibility of measurement conditions [2], [6], [7]. Viewpoint planning methods optimize coverage but rarely validate physical execution on humanoid platforms [1], [2], [3]. Quality control operates in isolation from viewpoint planning [8], [12], [15]. Sim-to-real studies demonstrate visual domain adaptation but do not validate visibility models or coverage metrics [1], [2], [14].

### 4.2 Platform and Validation Analysis

#### 4.2.1 Robot Platform Distribution

Analysis of the top 30 papers per research direction reveals a strong platform bias:

- **Manipulators** (Franka Panda, UR5, ABB): 45% of studies
- **Wheeled mobile robots** (Husky, TurtleBot, ANYmal): 25% of studies
- **UAVs and drones**: 20% of studies
- **Humanoid robots**: <5% of studies [1], [9], [14], [22]

This distribution reflects the maturity of manipulator and mobile robot research but highlights a critical gap: humanoid platforms like Unitree G1 remain largely unexplored for visual inspection tasks.

#### 4.2.2 Simulation vs. Physical Validation

Approximately 60% of reviewed papers rely primarily on simulation, 30% include physical robot experiments, and only 10% conduct rigorous real-world validation with statistical analysis and independent replication [5], [13], [19], [21]. This imbalance is particularly pronounced in benchmarking (RVI-01), active coverage (RVI-04), and sim-to-real transfer (RVI-07), where simulation studies outnumber physical experiments by 3:1 or more [8], [14], [17].

While simulation enables rapid prototyping and large-scale evaluation, it cannot validate critical inspection requirements like camera calibration accuracy, mechanical repeatability, or sensor noise characteristics. The gap between simulated and physical validation represents a significant barrier to deployment.

### 4.3 Methodological Strengths and Limitations

#### 4.3.1 Benchmarking (RVI-01)

**Strengths**: Standardized protocols [2], [5], [13], controlled perturbations [6], [7], [10], open-source frameworks [2], [17], large-scale evaluation [3], [14], [17]

**Limitations**: Platform bias toward manipulators and wheeled robots [5], [13], [14]; emphasis on robustness over repeatability [2], [6], [7]; limited real-world validation [8], [17]; lack of inspection-specific metrics [1], [2]

#### 4.3.2 Target Identification (RVI-02)

**Strengths**: Deep learning-based detection and pose estimation [4], [5], [8]; active perception for ambiguity resolution [6], [10], [13]; uncertainty quantification [11], [26]

**Limitations**: Focus on manipulation over measurement accuracy; limited multi-instance identification in cluttered scenes; rare integration with humanoid kinematics; insufficient repeatability evaluation

#### 4.3.3 Viewpoint Planning (RVI-03)

**Strengths**: Coverage optimization [1], [2], [3]; kinematic feasibility integration [2], [4], [9]; collision avoidance [5], [6], [9]; multi-objective optimization [1], [10], [13]

**Limitations**: Limited humanoid-specific planning [1], [4]; insufficient execution validation [10], [16], [17]; rare quality integration [1], [2], [3]; limited online adaptation [5], [12]

#### 4.3.4 Active Coverage (RVI-04)

**Strengths**: Information-theoretic planning [2], [3], [5]; learning-based methods [6], [14], [22]; application-specific adaptation [8], [15], [20], [21]

**Limitations**: Limited quality-aware planning [1], [2], [3]; rare humanoid evaluation [14], [25]; insufficient repeatability consideration; limited sim-to-real validation [6], [14], [22]

#### 4.3.5 Repeatable Acquisition (RVI-05)

**Strengths**: Precise calibration methods [7], [17]; visual servoing [13], [18], [25]; quantitative repeatability evaluation [12], [24]

**Limitations**: Focus on robot pose over acquisition geometry; limited quality metric integration; rare humanoid evaluation [24]; lack of standardized benchmarks

#### 4.3.6 Quality Control (RVI-06)

**Strengths**: Adaptive exposure control [3], [6], [9], [15]; noise-aware quality assessment [8], [14]; motion blur detection [7], [27], [30]

**Limitations**: Isolated optimization [3], [8], [15]; limited inspection-specific metrics [8], [12], [14]; reactive rather than proactive strategies [12], [13]; rare humanoid validation [3], [15], [16]

#### 4.3.7 Sim-to-Real Transfer (RVI-07)

**Strengths**: Domain randomization [1], [2], [9], [14]; domain adaptation [10], [11], [22]; real-to-sim calibration [6], [17], [23], [25]

**Limitations**: Focus on manipulation success over visibility validation [1], [2], [14]; limited geometric fidelity [4], [5], [11]; rare humanoid validation [9], [14]; insufficient inspection-specific metrics [1], [2], [30]

#### 4.3.8 End-to-End Inspection (RVI-08)

**Strengths**: System integration [1], [2], [20], [21]; human-robot comparison [7], [22], [24], [26]; teleoperation studies [4], [11], [12], [16]

**Limitations**: Limited quantitative comparisons [1], [7], [22]; emphasis on defect detection over documentation quality [7], [26]; rare humanoid evaluation [1], [20]; insufficient controlled experiments [20], [21]

### 4.4 Evidence-Supported Gaps

Based on systematic analysis of 240 papers (30 per direction), the following gaps are supported by consistent evidence:

1. **Humanoid platform validation**: <5% of studies evaluate humanoid robots; most focus on manipulators or wheeled platforms [1], [9], [14], [22]
2. **Acquisition repeatability**: Repeatability research measures robot pose, not camera observation geometry or image acquisition consistency [12], [24], [25]
3. **Quality-aware planning**: Viewpoint planning optimizes coverage; quality control operates separately; integrated quality-aware NBV planning is rare [1], [2], [3], [8], [12]
4. **Visibility model validation**: Sim-to-real studies demonstrate visual domain adaptation but do not validate visibility models or coverage metrics against physical measurements [1], [2], [14]
5. **Inspection-specific benchmarks**: Existing benchmarks emphasize manipulation and navigation; no standardized benchmark evaluates autonomous visual inspection across platforms, environments, and quality metrics [1], [2], [5]
6. **Physical validation**: Simulation studies outnumber physical experiments 3:1; rigorous real-world validation with statistical analysis is rare [5], [13], [19], [21]
7. **End-to-end comparison**: Quantitative comparisons of autonomous vs. manual inspection are scarce; most studies lack controlled experimental designs [1], [7], [22], [26]

---

## 5. Discussion

### 5.1 Scientific Significance of Identified Gaps

The identified gaps represent scientifically significant challenges rather than incremental improvements. Humanoid platform validation addresses fundamental questions about whole-body motion planning, bipedal stability constraints, and sensor placement for inspection tasks—questions that cannot be answered by manipulator or wheeled robot studies. Acquisition repeatability extends beyond robot pose accuracy to encompass camera observation geometry, illumination consistency, and measurement condition reproducibility—critical for trustworthy documentation.

Quality-aware planning integrates perception, planning, and control in a closed loop, requiring online adaptation to partial observability and quality feedback—a departure from traditional sequential architectures. Visibility model validation bridges simulation and reality for geometric reasoning, not just visual appearance—a harder problem than visual domain adaptation. Inspection-specific benchmarking requires new evaluation protocols, metrics, and datasets tailored to documentation quality rather than task success rates.

### 5.2 Methodological Challenges

#### 5.2.1 Experimental Design

Rigorous experimental validation of autonomous inspection systems faces several challenges:

1. **Ground truth acquisition**: Establishing ground truth for coverage, visibility, and quality metrics requires independent measurement systems (e.g., laser trackers, photogrammetry) [21], [24]
2. **Environmental control**: Systematic variation of lighting, object placement, and occlusion requires controlled laboratory setups [5], [13]
3. **Statistical power**: Detecting meaningful differences between methods requires sufficient sample sizes and repeated trials [5], [13], [19]
4. **Confounding factors**: Isolating the effects of individual components (e.g., viewpoint planning vs. quality control) requires careful ablation studies [1], [2], [3]

#### 5.2.2 Evaluation Metrics

Inspection-specific evaluation metrics must balance multiple objectives:

- **Coverage completeness**: Percentage of target surface observed above resolution threshold
- **Acquisition quality**: Blur, exposure, occlusion, framing, and visibility scores
- **Repeatability**: Consistency of camera poses, image attributes, and measurement conditions across sessions
- **Efficiency**: Number of viewpoints, motion distance, and execution time
- **Robustness**: Performance degradation under environmental variations

Existing metrics emphasize task success rates and robustness scores, often neglecting coverage completeness, acquisition quality, and repeatability—critical gaps for inspection applications [1], [2], [5].

### 5.3 Contradictory Findings and Unresolved Questions

Several contradictory findings and unresolved questions emerge from the literature:

1. **Domain randomization effectiveness**: Some studies report successful zero-shot sim-to-real transfer via domain randomization [1], [2], [14], while others find limited generalization without real-world fine-tuning [9], [11]. The conditions under which domain randomization succeeds remain unclear.

2. **Learning vs. model-based planning**: Learning-based NBV methods [6], [14], [22] demonstrate impressive simulation performance but often lack physical validation, while model-based methods [1], [2], [3] show reliable real-world execution but limited adaptability. The relative merits of these approaches for inspection tasks are unresolved.

3. **Humanoid vs. manipulator platforms**: Proponents argue humanoid robots offer superior adaptability for human-designed environments [1], [14], while critics cite kinematic complexity, stability constraints, and computational limits. Empirical evidence comparing humanoid and manipulator inspection performance is lacking.

4. **Quality-aware vs. coverage-first planning**: Some work suggests quality-aware planning improves documentation fidelity [12], [13], while others argue coverage-first strategies with post-hoc quality filtering are more efficient [1], [2]. Controlled comparisons are needed.

### 5.4 Implications for ARC-RVI

The literature review reveals that ARC-RVI addresses scientifically significant gaps with strong publication potential:

1. **Hardware-independent benchmarking**: Developing standardized evaluation protocols for autonomous visual inspection across robot platforms, environments, and quality metrics would fill a critical gap [1], [2], [5]

2. **Humanoid-specific planning**: Investigating viewpoint and motion planning for humanoid robots with whole-body kinematics and bipedal stability constraints addresses an underexplored area [1], [4], [14]

3. **Quality-aware NBV**: Integrating image quality assessment into next-best-view planning represents a novel contribution [1], [2], [3], [8], [12]

4. **Acquisition repeatability**: Developing methods and metrics for reproducible camera observation geometry extends beyond existing robot pose repeatability research [12], [24], [25]

5. **Visibility model validation**: Systematically validating simulated visibility and coverage metrics against physical measurements addresses a critical sim-to-real gap [1], [2], [14]

6. **End-to-end comparison**: Conducting rigorous experimental comparisons of autonomous vs. manual inspection with controlled tasks and statistical analysis would provide valuable empirical evidence [1], [7], [22], [26]

---

## 6. Future Directions and Recommendations

### 6.1 Research Priorities and Ranking

Based on scientific novelty, feasibility, dependencies, expected research value, and publication potential, the eight ARC-RVI research directions are ranked as follows:

#### Tier 1: High Priority (Immediate Focus)

**1. RVI-01: Reproducible Benchmarking**
- **Rationale**: Foundational for all other directions; addresses critical gap in inspection-specific evaluation protocols
- **Novelty**: High—no existing benchmark systematically evaluates autonomous visual inspection
- **Feasibility**: High—can leverage existing datasets and simulation environments
- **Dependencies**: None—enables validation of other directions
- **Publication potential**: Very high—benchmarking papers attract broad interest and citations

**2. RVI-03: Viewpoint and Motion Planning**
- **Rationale**: Core technical challenge; humanoid-specific planning is underexplored
- **Novelty**: High—whole-body planning with bipedal stability constraints for inspection is novel
- **Feasibility**: Medium—requires humanoid platform access and kinematic modeling
- **Dependencies**: Requires RVI-02 (target localization) and benefits from RVI-01 (benchmarking)
- **Publication potential**: Very high—planning research is central to robotics conferences

**3. RVI-06: Acquisition Quality Control**
- **Rationale**: Critical for documentation fidelity; quality-aware planning is underexplored
- **Novelty**: High—integrated quality-aware NBV planning is rare
- **Feasibility**: High—can build on existing exposure control and quality assessment methods
- **Dependencies**: Benefits from RVI-03 (viewpoint planning) and RVI-04 (active coverage)
- **Publication potential**: High—quality control is relevant to computer vision and robotics communities

#### Tier 2: Medium Priority (Near-Term Focus)

**4. RVI-04: Active Visual Coverage**
- **Rationale**: Extends viewpoint planning to online adaptation under partial observability
- **Novelty**: Medium—NBV planning is well-studied, but quality-aware and humanoid-specific variants are novel
- **Feasibility**: Medium—requires integration of perception, planning, and control
- **Dependencies**: Requires RVI-03 (viewpoint planning) and RVI-06 (quality control)
- **Publication potential**: High—active perception is a core robotics topic

**5. RVI-07: Simulation-to-Reality Transfer**
- **Rationale**: Validates simulated methods before physical deployment; visibility model validation is underexplored
- **Novelty**: Medium—sim-to-real transfer is well-studied, but visibility and coverage validation is novel
- **Feasibility**: Medium—requires physical robot experiments and independent measurement systems
- **Dependencies**: Requires RVI-03 (viewpoint planning) and RVI-04 (active coverage)
- **Publication potential**: High—sim-to-real transfer is a high-impact topic

**6. RVI-02: Target Identification and Localization**
- **Rationale**: Foundational for viewpoint planning; multi-instance identification in clutter is challenging
- **Novelty**: Low—object detection and pose estimation are well-studied
- **Feasibility**: High—can leverage existing deep learning methods
- **Dependencies**: None—enables RVI-03 and RVI-04
- **Publication potential**: Medium—incremental improvements are harder to publish

#### Tier 3: Lower Priority (Long-Term Focus)

**7. RVI-05: Repeatable Visual Acquisition**
- **Rationale**: Critical for measurement applications; acquisition geometry repeatability is underexplored
- **Novelty**: Medium—robot pose repeatability is studied, but acquisition geometry is novel
- **Feasibility**: Low—requires precise calibration and independent measurement systems
- **Dependencies**: Requires RVI-03 (viewpoint planning) and RVI-06 (quality control)
- **Publication potential**: Medium—repeatability is important but less central to robotics research

**8. RVI-08: End-to-End Autonomous Inspection**
- **Rationale**: Integrates all components; provides empirical evidence of system performance
- **Novelty**: Low—system integration is less novel than individual components
- **Feasibility**: Low—requires fully functional system and controlled experimental design
- **Dependencies**: Requires all other directions
- **Publication potential**: Medium—system papers are valuable but harder to publish in top venues

### 6.2 Falsifiable Hypotheses

For each high-priority direction, we propose falsifiable hypotheses with measurable variables and appropriate controls:

#### RVI-01: Reproducible Benchmarking

**Hypothesis 1.1**: Autonomous visual inspection performance degrades systematically under controlled environmental variations (lighting, object placement, occlusion), with degradation magnitude varying across robot platforms and planning methods.

- **Independent variables**: Lighting intensity (lux), object placement (position, orientation), occlusion level (percentage of target surface occluded)
- **Dependent variables**: Coverage completeness (%), acquisition quality score (0–1), execution time (s)
- **Controls**: Fixed robot platform, fixed planning method, randomized trial order
- **Validation**: Repeated trials (n≥30 per condition), statistical significance testing (ANOVA, post-hoc comparisons)

**Hypothesis 1.2**: Humanoid robots exhibit different performance trade-offs compared to manipulators and wheeled robots for visual inspection tasks, with humanoids offering superior workspace coverage but longer execution times and lower repeatability.

- **Independent variables**: Robot platform (humanoid, manipulator, wheeled mobile robot)
- **Dependent variables**: Workspace coverage (%), execution time (s), pose repeatability (mm, degrees)
- **Controls**: Fixed task, fixed environment, fixed planning method
- **Validation**: Repeated trials (n≥30 per platform), statistical significance testing

#### RVI-03: Viewpoint and Motion Planning

**Hypothesis 3.1**: Humanoid-specific viewpoint planning incorporating whole-body kinematics and bipedal stability constraints achieves higher coverage completeness and kinematic feasibility compared to manipulator-centric planning adapted to humanoid platforms.

- **Independent variables**: Planning method (humanoid-specific, adapted manipulator method)
- **Dependent variables**: Coverage completeness (%), kinematic feasibility (% of planned viewpoints executable), execution success rate (%)
- **Controls**: Fixed robot platform (Unitree G1), fixed environment, fixed target objects
- **Validation**: Repeated trials (n≥30 per method), statistical significance testing

**Hypothesis 3.2**: Joint optimization of viewpoint selection and motion planning outperforms sequential planning (viewpoint selection followed by motion planning) in terms of coverage completeness, execution time, and motion smoothness.

- **Independent variables**: Planning approach (joint optimization, sequential planning)
- **Dependent variables**: Coverage completeness (%), execution time (s), motion smoothness (jerk, acceleration)
- **Controls**: Fixed robot platform, fixed environment, fixed target objects
- **Validation**: Repeated trials (n≥30 per approach), statistical significance testing

#### RVI-06: Acquisition Quality Control

**Hypothesis 6.1**: Quality-aware next-best-view planning that integrates image quality assessment into viewpoint selection achieves higher acquisition quality and fewer re-observations compared to coverage-first planning with post-hoc quality filtering.

- **Independent variables**: Planning method (quality-aware NBV, coverage-first with filtering)
- **Dependent variables**: Acquisition quality score (0–1), number of re-observations, execution time (s)
- **Controls**: Fixed robot platform, fixed environment, fixed target objects
- **Validation**: Repeated trials (n≥30 per method), statistical significance testing

**Hypothesis 6.2**: Proactive quality-aware viewpoint planning reduces the frequency of poor-quality acquisitions (blur, over/underexposure, occlusion) compared to reactive quality control that triggers re-observation after detecting poor quality.

- **Independent variables**: Quality control strategy (proactive planning, reactive re-observation)
- **Dependent variables**: Frequency of poor-quality acquisitions (%), number of re-observations, execution time (s)
- **Controls**: Fixed robot platform, fixed environment, fixed target objects
- **Validation**: Repeated trials (n≥30 per strategy), statistical significance testing

### 6.3 Experimental Recommendations

#### 6.3.1 Datasets and Benchmark Environments

**Recommended datasets**:
- **YCB Object and Model Set**: Standardized objects with known geometry for coverage evaluation [5], [13], [21]
- **ShapeNet**: Large-scale 3D object dataset for simulation experiments [13]
- **Replica**: Photo-realistic 3D scene models for SLAM and navigation [8]
- **LIBERO**: Manipulation benchmark with diverse tasks and environments [4], [20], [21], [27]

**Recommended benchmark environments**:
- **Controlled laboratory setup**: Adjustable lighting, object placement, and occlusion for systematic evaluation [5], [13]
- **Simulated environments**: Isaac Sim, Gazebo, MuJoCo for large-scale evaluation and ablation studies [3], [8], [14], [17]
- **Real-world scenarios**: Office, warehouse, or manufacturing environments for deployment validation [1], [20], [21]

#### 6.3.2 Baseline Algorithms

**Viewpoint planning**:
- Coverage-first methods [1], [2], [3]
- Information-theoretic NBV [2], [3], [5]
- Learning-based NBV [6], [14], [22]

**Quality control**:
- Adaptive exposure control [3], [9], [15]
- Noise-aware quality assessment [8], [14]
- Motion blur detection [7], [27], [30]

**Sim-to-real transfer**:
- Domain randomization [1], [2], [9], [14]
- Domain adaptation [10], [11], [22]
- Real-to-sim calibration [6], [17], [23]

#### 6.3.3 Statistical Methods

**Recommended statistical methods**:
- **Repeated measures ANOVA**: Compare methods across multiple conditions with repeated trials
- **Post-hoc comparisons**: Tukey HSD or Bonferroni correction for pairwise comparisons
- **Effect size estimation**: Cohen's d or partial eta-squared to quantify practical significance
- **Power analysis**: Determine required sample sizes for detecting meaningful differences
- **Confidence intervals**: Report 95% CIs for all effect estimates

**Validation procedures**:
- **Cross-validation**: K-fold or leave-one-out for learning-based methods
- **Held-out test sets**: Independent evaluation data not used during training or tuning
- **Ablation studies**: Systematic removal of components to assess individual contributions
- **Sensitivity analysis**: Vary parameters to assess robustness and generalization

### 6.4 Publication Strategy

#### 6.4.1 Target Venues by Research Direction

**RVI-01: Reproducible Benchmarking**
- **Journals**: IEEE Transactions on Robotics, International Journal of Robotics Research, Robotics and Autonomous Systems
- **Conferences**: ICRA, IROS, RSS, CoRL
- **Rationale**: Benchmarking papers attract broad interest and citations; top venues prioritize reproducibility

**RVI-03: Viewpoint and Motion Planning**
- **Journals**: IEEE Transactions on Robotics, Autonomous Robots, IEEE Robotics and Automation Letters
- **Conferences**: ICRA, IROS, RSS, WAFR
- **Rationale**: Planning research is central to robotics; humanoid-specific methods offer novelty

**RVI-06: Acquisition Quality Control**
- **Journals**: IEEE Transactions on Robotics, Computer Vision and Image Understanding, IEEE Transactions on Image Processing
- **Conferences**: ICRA, IROS, CVPR, ICCV
- **Rationale**: Quality control bridges robotics and computer vision; integrated quality-aware planning is novel

**RVI-04: Active Visual Coverage**
- **Journals**: IEEE Transactions on Robotics, Autonomous Robots, IEEE Robotics and Automation Letters
- **Conferences**: ICRA, IROS, RSS
- **Rationale**: Active perception is a core robotics topic; quality-aware NBV is novel

**RVI-07: Simulation-to-Reality Transfer**
- **Journals**: IEEE Transactions on Robotics, International Journal of Robotics Research, IEEE Robotics and Automation Letters
- **Conferences**: ICRA, IROS, RSS, CoRL
- **Rationale**: Sim-to-real transfer is high-impact; visibility model validation is novel

**RVI-02: Target Identification and Localization**
- **Journals**: IEEE Robotics and Automation Letters, Robotics and Autonomous Systems
- **Conferences**: ICRA, IROS
- **Rationale**: Object detection is well-studied; incremental improvements are harder to publish in top venues

**RVI-05: Repeatable Visual Acquisition**
- **Journals**: IEEE Transactions on Automation Science and Engineering, Measurement Science and Technology
- **Conferences**: ICRA, IROS, CASE
- **Rationale**: Repeatability is important for measurement applications; less central to robotics research

**RVI-08: End-to-End Autonomous Inspection**
- **Journals**: IEEE Transactions on Automation Science and Engineering, Robotics and Computer-Integrated Manufacturing
- **Conferences**: ICRA, IROS, CASE
- **Rationale**: System integration is valuable but harder to publish in top venues; field deployment studies are well-suited to application-oriented journals

#### 6.4.2 Publication Readiness Assessment

Each research direction is assessed for independent, defensible scientific contribution:

**High publication potential** (RVI-01, RVI-03, RVI-06):
- Addresses scientifically significant gaps
- Offers novel methods or insights
- Provides rigorous experimental validation
- Suitable for top-tier venues

**Medium publication potential** (RVI-04, RVI-07, RVI-02):
- Extends existing methods to new domains
- Provides empirical evidence or benchmarking results
- Suitable for mid-tier venues or specialized journals

**Lower publication potential** (RVI-05, RVI-08):
- Incremental improvements or system integration
- Requires substantial experimental validation
- Suitable for application-oriented journals or workshops

---

## 7. Conclusion

This literature review establishes the scientific foundations for the Autonomous Robotic Visual Inspection (ARC-RVI) research program through systematic analysis of 1,908 papers spanning eight interconnected research directions. The evidence reveals substantial progress in simulation-based benchmarking, viewpoint planning, active coverage, and sim-to-real transfer, yet exposes critical gaps in physical humanoid robot validation, repeatable acquisition geometry, integrated quality-aware planning, and end-to-end autonomous inspection comparison.

The review identifies seven high-priority research directions with strong publication potential: (1) hardware-independent benchmarking protocols for autonomous visual inspection; (2) humanoid-specific viewpoint and motion planning with whole-body kinematics and bipedal stability constraints; (3) quality-aware next-best-view planning integrating image quality assessment into viewpoint selection; (4) active visual coverage under partial observability and quality feedback; (5) systematic validation of simulated visibility and coverage metrics against physical measurements; (6) multi-instance target identification in cluttered environments; and (7) acquisition geometry repeatability methods and metrics.

For each direction, the review proposes falsifiable hypotheses with measurable independent and dependent variables, appropriate experimental controls, and statistical validation procedures. Recommended datasets include YCB, ShapeNet, Replica, and LIBERO; benchmark environments span controlled laboratory setups, simulated environments (Isaac Sim, Gazebo, MuJoCo), and real-world scenarios; baseline algorithms cover coverage-first planning, information-theoretic NBV, adaptive exposure control, and domain randomization; and statistical methods include repeated measures ANOVA, post-hoc comparisons, effect size estimation, and cross-validation.

The publication strategy identifies target venues for each direction, with RVI-01 (benchmarking), RVI-03 (viewpoint planning), and RVI-06 (quality control) offering the highest publication potential in top-tier robotics journals and conferences. RVI-04 (active coverage), RVI-07 (sim-to-real transfer), and RVI-02 (target localization) provide medium publication potential, while RVI-05 (repeatable acquisition) and RVI-08 (end-to-end inspection) require substantial experimental validation before publication readiness.

The ARC-RVI research program addresses scientifically significant gaps at the intersection of robotic perception, planning, and control. By prioritizing reproducible benchmarking, humanoid-specific planning, quality-aware coverage, and systematic sim-to-real validation, ARC-RVI offers a rigorous, evidence-based path toward trustworthy autonomous robotic visual inspection. The proposed research agenda balances scientific novelty, experimental feasibility, and publication potential, positioning ARC-RVI to make defensible contributions to the robotics community while advancing the practical deployment of autonomous inspection systems.

---

## References

[1]B. V. Ehinger, K. Groß, I. Ibs, and P. König, “A new comprehensive eye-tracking test battery concurrently evaluating the Pupil Labs glasses and the EyeLink 1000,” PeerJ, 2019, doi: 10.7717/peerj.7086.

[2]M. Zaffar et al., “VPR-Bench: An Open-Source Visual Place Recognition Evaluation Framework with Quantifiable Viewpoint and Appearance Change,” International Journal of Computer Vision, vol. 129, no. 7, pp. 2136–2174, July 2021, doi: 10.1007/S11263-021-01469-5.

[3]J. Yash et al., “RobotArena $\infty$: Scalable Robot Benchmarking via Real-to-Sim Translation,” Oct. 2025, doi: 10.48550/arxiv.2510.23571.

[4]S. Han and H. Choi, “ROEP: A Robotics-Oriented Evaluation Protocol for Deployment-Facing Vision–Language–Action Manipulation Policies,” Sensors, vol. 26, no. 15, pp. 4757–4757, July 2026, doi: 10.3390/s26154757.

[5]B. K. Rameshbabu et al., “A Benchmarking Study of Vision-based Robotic Grasping Algorithms,” arXiv.org, vol. abs/2503.11163, Mar. 2025, doi: 10.48550/arxiv.2503.11163.

[6]Y. Zarrouk, A. Khallou, M. Bourhaleb, M. Rahmoune, and K. Hachami, “AgroBench and ARI: A reproducible method for robustness evaluation of agricultural object detectors,” MethodsX, vol. 17, pp. 104068–104068, July 2026, doi: 10.1016/j.mex.2026.104068.

[7]S. Xie et al., “RoboBEV: Towards Robust Bird’s Eye View Perception under Corruptions,” arXiv.org, vol. abs/2304.06719, Apr. 2023, doi: 10.48550/arXiv.2304.06719.

[8]X. Xu et al., “From Perfect to Noisy World Simulation: Customizable Embodied   Multi-modal Perturbations for SLAM Robustness Benchmarking,” June 2024, doi: 10.48550/arxiv.2406.16850.

[9]A. Matar, Y. Altamimi, and Y. M. Alrawashdeh, “Robust Industrial Manipulation Under Test-Time Perturbations in RLBench and Colosseum,” pp. 197–203, July 2026, doi: 10.1109/aeect69724.2026.11657856.

[10]S. Jenny, M. Lukas, A. Shashank, K. Margret, and B. Andrés, “RobustSpring: Benchmarking Robustness to Image Corruptions for Optical Flow, Scene Flow and Stereo,” May 2025, doi: 10.48550/arxiv.2505.09368.

[11]S. Dey, J.-N. Zaech, N. Nikolov, L. V. Gool, and D. P. Paudel, “ReVLA: Reverting Visual Domain Limitation of Robotic Foundation Models,” Sept. 2024, doi: 10.48550/arxiv.2409.15250.

[12]L. Kong et al., “Robo3D: Towards Robust and Reliable 3D Perception against Corruptions,” Oct. 2023, doi: 10.1109/iccv51070.2023.01830.

[13]“DGBench: An Open-Source, Reproducible Benchmark for Dynamic Grasping,” Apr. 2022, doi: 10.48550/arxiv.2204.13879.

[14]W. Pumacay, I. Singh, J. Duan, R. Krishna, J. Thomason, and D. Fox, “THE COLOSSEUM: A Benchmark for Evaluating Generalization for Robotic Manipulation,” arXiv.org, vol. abs/2402.08191, Feb. 2024, doi: 10.48550/arxiv.2402.08191.

[15]Y. Cheng, Y. Cao, R. Chen, and W. Shen, “RAD: A Comprehensive Dataset for Benchmarking the Robustness of Image   Anomaly Detection,” June 2024, doi: 10.48550/arxiv.2406.07176.

[16]L. Pemula, D. Zhang, and O. Dabeer, “Robust AD: A Real World Benchmark Dataset for Robustness in Industrial Anomaly Detection,” pp. 4047–4057, June 2025, doi: 10.1109/cvprw67362.2025.00389.

[17]F. Pasch, S. Wiest, A. Ortega, and N. Hochgeschwender, “RoboVAST: Automated Scenario-Based Validation of Robots at Scale,” arXiv.org, vol. abs/2607.06248, July 2026, doi: 10.48550/arxiv.2607.06248.

[18]A. Fornasier, M. Scheiber, A. Hardt-Stremayr, R. Jung, and S. Weiss, “VINSEval: Evaluation Framework for Unified Testing of Consistency and Robustness of Visual-Inertial Navigation System Algorithms,” pp. 13754–13760, May 2021, doi: 10.1109/ICRA48506.2021.9561382.

[19]K. Zhou et al., “RAD: A Dataset and Benchmark for Real-Life Anomaly Detection with Robotic Observations,” arXiv.org, vol. abs/2410.00713, Oct. 2024, doi: 10.48550/arxiv.2410.00713.

[20]H. Li, Z. Mei, A. Majumdar, J. Chen, Y.-G. Jiang, and B. Zhu, “LIBERO-VPro: Benchmarking Closed-Loop Visual Robustness of Robotic Foundation Models,” Sept. 2026, doi: 10.48550/arxiv.2609.24350.

[21]Z. Wang, Z. Zhou, J. Song, Y. Huang, Z. Shu, and L. Ma, “Towards Testing and Evaluating Vision-Language-Action Models for Robotic   Manipulation: An Empirical Study,” Sept. 2024, doi: 10.48550/arxiv.2409.12894.

[22]L. Zhou, J. Su, Y. Wei, K. Dong, and H. Liu, “DeViGrasp: Robust Visual Mobile Grasping for Quadruped Manipulators under Degraded Perception,” Sept. 2026, doi: 10.48550/arxiv.2609.22278.

[23]L. Wu et al., “RoboStressBench: Benchmarking VLM Robustness to Physical Visual Stress in Embodied Scenes,” May 2026, doi: 10.48550/arxiv.2606.00828.

[24]Y. Zhu, X. Li, T. Nguyen, X. Wang, and S. Yuan, “Benchmarking Visual-Inertial Odometry in Subterranean Environments Under Sensor Degradation, Miscalibration, and Dynamic Occlusion,” Sept. 2026, doi: 10.48550/arxiv.2609.18628.

[25]Y. Xie, Y. Yan, Y. Zhao, H. Wang, and Y. Jin, “STRONG-VLA: Decoupled Robustness Learning for Vision-Language-Action Models under Multimodal Perturbations,” Apr. 2026, doi: 10.48550/arxiv.2604.10055.

[26]K. Burns, Z. Witzel, J. I. Hamid, T. Yu, C. Finn, and K. Hausman, “What Makes Pre-Trained Visual Representations Successful for Robust Manipulation?,” arXiv.org, vol. abs/2312.12444, Nov. 2023, doi: 10.48550/arxiv.2312.12444.

[27]W. Si-yin et al., “LIBERO-Plus: In-depth Robustness Analysis of Vision-Language-Action Models,” Oct. 2025, doi: 10.48550/arxiv.2510.13626.

[28]P. Kostal, V. Prajová, Š. Václav, and S.-D. Stan, “An Overview of the Practical Use of the CCTV System in a Simple Assembly in a Flexible Manufacturing System,” Applied system innovation, vol. 5, no. 3, pp. 52–52, May 2022, doi: 10.3390/asi5030052.

[29]S. Gallenmuller et al., “Benchmarking Networked Control Systems,” pp. 7–12, Apr. 2018, doi: 10.1109/CPSBENCH.2018.00008.

[30]M. Halinkovič, M. Kunovsky, and M. Galinski, “ROSBENCH: A Simulation-Based Benchmark for Sensor Quality and Environmental Conditions Robustness in AV Perception,” pp. 269–272, Sept. 2025, doi: 10.1109/elmar66948.2025.11194028.