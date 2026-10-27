# Appendix C: Research Hypotheses and Experimental Recommendations

## C.1 Falsifiable Research Hypotheses

### C.1.1 RVI-01: Reproducible Benchmarking

#### Hypothesis 1.1: Environmental Variation Effects
**Statement**: Autonomous visual inspection performance degrades systematically under controlled environmental variations (lighting, object placement, occlusion), with degradation magnitude varying across robot platforms and planning methods.

**Independent variables**:
- Lighting intensity: 100 lux, 500 lux, 1000 lux, 2000 lux
- Object placement: Position (±10 cm), orientation (±15°)
- Occlusion level: 0%, 25%, 50%, 75% of target surface occluded

**Dependent variables**:
- Coverage completeness: Percentage of target surface observed above resolution threshold (%)
- Acquisition quality score: Composite metric combining blur, exposure, occlusion, framing (0–1 scale)
- Execution time: Total time from start to completion (seconds)

**Controls**:
- Fixed robot platform (e.g., Franka Panda manipulator)
- Fixed planning method (e.g., coverage-first viewpoint planning)
- Randomized trial order to control for learning effects
- Fixed target objects (e.g., YCB objects)

**Validation**:
- Repeated trials: n≥30 per condition (4 lighting × 3 placement × 4 occlusion = 48 conditions × 30 trials = 1,440 trials)
- Statistical analysis: Three-way repeated measures ANOVA with post-hoc Tukey HSD comparisons
- Effect size: Partial eta-squared (η²p) for each main effect and interaction
- Power analysis: Ensure 80% power to detect medium effect sizes (η²p ≥ 0.06)

**Expected outcome**: Significant main effects of lighting (F(3,87) > 3.0, p < 0.05), placement (F(2,58) > 3.0, p < 0.05), and occlusion (F(3,87) > 3.0, p < 0.05) on coverage completeness and quality score; significant interactions between factors

**Falsification criteria**: If no significant main effects or interactions are observed (p > 0.05), the hypothesis is rejected

---

#### Hypothesis 1.2: Platform Performance Trade-offs
**Statement**: Humanoid robots exhibit different performance trade-offs compared to manipulators and wheeled robots for visual inspection tasks, with humanoids offering superior workspace coverage but longer execution times and lower repeatability.

**Independent variables**:
- Robot platform: Humanoid (Unitree G1), manipulator (Franka Panda), wheeled mobile robot (Clearpath Husky with UR5)

**Dependent variables**:
- Workspace coverage: Percentage of workspace volume accessible for inspection (%)
- Execution time: Total time from start to completion (seconds)
- Pose repeatability: Standard deviation of camera pose across repeated trials (mm for position, degrees for orientation)

**Controls**:
- Fixed task: Inspect standardized object (e.g., YCB object) from multiple viewpoints
- Fixed environment: Controlled laboratory setup with standardized lighting and object placement
- Fixed planning method: Same viewpoint planning algorithm adapted to each platform

**Validation**:
- Repeated trials: n≥30 per platform (3 platforms × 30 trials = 90 trials)
- Statistical analysis: One-way repeated measures ANOVA with post-hoc Tukey HSD comparisons
- Effect size: Partial eta-squared (η²p) for platform effect
- Power analysis: Ensure 80% power to detect medium effect sizes (η²p ≥ 0.06)

**Expected outcome**: Significant main effect of platform on workspace coverage (F(2,58) > 3.0, p < 0.05), execution time (F(2,58) > 3.0, p < 0.05), and pose repeatability (F(2,58) > 3.0, p < 0.05); humanoid > manipulator > wheeled robot for workspace coverage; humanoid > wheeled robot > manipulator for execution time; manipulator > wheeled robot > humanoid for pose repeatability

**Falsification criteria**: If no significant platform effect is observed (p > 0.05) or if the expected ordering is not confirmed, the hypothesis is rejected

---

### C.1.2 RVI-03: Viewpoint and Motion Planning

#### Hypothesis 3.1: Humanoid-Specific Planning Effectiveness
**Statement**: Humanoid-specific viewpoint planning incorporating whole-body kinematics and bipedal stability constraints achieves higher coverage completeness and kinematic feasibility compared to manipulator-centric planning adapted to humanoid platforms.

**Independent variables**:
- Planning method: Humanoid-specific planning (incorporating whole-body kinematics and stability constraints), adapted manipulator planning (treating humanoid as fixed-base manipulator)

**Dependent variables**:
- Coverage completeness: Percentage of target surface observed above resolution threshold (%)
- Kinematic feasibility: Percentage of planned viewpoints executable without violating joint limits or stability constraints (%)
- Execution success rate: Percentage of trials completed without failures (%)

**Controls**:
- Fixed robot platform: Unitree G1 humanoid robot
- Fixed environment: Controlled laboratory setup with standardized lighting and object placement
- Fixed target objects: YCB objects with varying geometry and size

**Validation**:
- Repeated trials: n≥30 per method (2 methods × 30 trials = 60 trials)
- Statistical analysis: Paired t-tests for each dependent variable
- Effect size: Cohen's d for each comparison
- Power analysis: Ensure 80% power to detect medium effect sizes (d ≥ 0.5)

**Expected outcome**: Humanoid-specific planning > adapted manipulator planning for coverage completeness (t(29) > 2.0, p < 0.05, d > 0.5), kinematic feasibility (t(29) > 2.0, p < 0.05, d > 0.5), and execution success rate (t(29) > 2.0, p < 0.05, d > 0.5)

**Falsification criteria**: If no significant differences are observed (p > 0.05) or if adapted manipulator planning outperforms humanoid-specific planning, the hypothesis is rejected

---

#### Hypothesis 3.2: Joint Optimization Benefits
**Statement**: Joint optimization of viewpoint selection and motion planning outperforms sequential planning (viewpoint selection followed by motion planning) in terms of coverage completeness, execution time, and motion smoothness.

**Independent variables**:
- Planning approach: Joint optimization (simultaneous viewpoint and motion planning), sequential planning (viewpoint selection followed by motion planning)

**Dependent variables**:
- Coverage completeness: Percentage of target surface observed above resolution threshold (%)
- Execution time: Total time from start to completion (seconds)
- Motion smoothness: Root mean square jerk (m/s³) and acceleration (m/s²)

**Controls**:
- Fixed robot platform: Franka Panda manipulator or Unitree G1 humanoid robot
- Fixed environment: Controlled laboratory setup with standardized lighting and object placement
- Fixed target objects: YCB objects with varying geometry and size

**Validation**:
- Repeated trials: n≥30 per approach (2 approaches × 30 trials = 60 trials)
- Statistical analysis: Paired t-tests for each dependent variable
- Effect size: Cohen's d for each comparison
- Power analysis: Ensure 80% power to detect medium effect sizes (d ≥ 0.5)

**Expected outcome**: Joint optimization > sequential planning for coverage completeness (t(29) > 2.0, p < 0.05, d > 0.5) and motion smoothness (t(29) > 2.0, p < 0.05, d > 0.5); joint optimization < sequential planning for execution time (t(29) > 2.0, p < 0.05, d > 0.5)

**Falsification criteria**: If no significant differences are observed (p > 0.05) or if sequential planning outperforms joint optimization on coverage or smoothness, the hypothesis is rejected

---

### C.1.3 RVI-06: Acquisition Quality Control

#### Hypothesis 6.1: Quality-Aware NBV Effectiveness
**Statement**: Quality-aware next-best-view planning that integrates image quality assessment into viewpoint selection achieves higher acquisition quality and fewer re-observations compared to coverage-first planning with post-hoc quality filtering.

**Independent variables**:
- Planning method: Quality-aware NBV (integrates quality assessment into viewpoint selection), coverage-first with filtering (selects viewpoints for coverage, filters poor-quality images, triggers re-observation)

**Dependent variables**:
- Acquisition quality score: Composite metric combining blur, exposure, occlusion, framing (0–1 scale)
- Number of re-observations: Total number of viewpoints requiring re-observation due to poor quality
- Execution time: Total time from start to completion (seconds)

**Controls**:
- Fixed robot platform: Franka Panda manipulator or Unitree G1 humanoid robot
- Fixed environment: Controlled laboratory setup with varying lighting conditions
- Fixed target objects: YCB objects with varying geometry and reflectance

**Validation**:
- Repeated trials: n≥30 per method (2 methods × 30 trials = 60 trials)
- Statistical analysis: Paired t-tests for each dependent variable
- Effect size: Cohen's d for each comparison
- Power analysis: Ensure 80% power to detect medium effect sizes (d ≥ 0.5)

**Expected outcome**: Quality-aware NBV > coverage-first with filtering for acquisition quality score (t(29) > 2.0, p < 0.05, d > 0.5); quality-aware NBV < coverage-first with filtering for number of re-observations (t(29) > 2.0, p < 0.05, d > 0.5); quality-aware NBV ≈ coverage-first with filtering for execution time (t(29) < 2.0, p > 0.05)

**Falsification criteria**: If no significant differences are observed for quality score or re-observations (p > 0.05), or if coverage-first with filtering outperforms quality-aware NBV, the hypothesis is rejected

---

#### Hypothesis 6.2: Proactive vs. Reactive Quality Control
**Statement**: Proactive quality-aware viewpoint planning reduces the frequency of poor-quality acquisitions (blur, over/underexposure, occlusion) compared to reactive quality control that triggers re-observation after detecting poor quality.

**Independent variables**:
- Quality control strategy: Proactive planning (selects viewpoints to maximize expected quality), reactive re-observation (detects poor quality and triggers re-observation)

**Dependent variables**:
- Frequency of poor-quality acquisitions: Percentage of viewpoints with quality score < 0.5 (%)
- Number of re-observations: Total number of viewpoints requiring re-observation
- Execution time: Total time from start to completion (seconds)

**Controls**:
- Fixed robot platform: Franka Panda manipulator or Unitree G1 humanoid robot
- Fixed environment: Controlled laboratory setup with varying lighting conditions
- Fixed target objects: YCB objects with varying geometry and reflectance

**Validation**:
- Repeated trials: n≥30 per strategy (2 strategies × 30 trials = 60 trials)
- Statistical analysis: Paired t-tests for each dependent variable
- Effect size: Cohen's d for each comparison
- Power analysis: Ensure 80% power to detect medium effect sizes (d ≥ 0.5)

**Expected outcome**: Proactive planning < reactive re-observation for frequency of poor-quality acquisitions (t(29) > 2.0, p < 0.05, d > 0.5) and number of re-observations (t(29) > 2.0, p < 0.05, d > 0.5); proactive planning ≈ reactive re-observation for execution time (t(29) < 2.0, p > 0.05)

**Falsification criteria**: If no significant differences are observed for poor-quality frequency or re-observations (p > 0.05), or if reactive re-observation outperforms proactive planning, the hypothesis is rejected

---

### C.1.4 RVI-07: Simulation-to-Reality Transfer

#### Hypothesis 7.1: Visibility Model Fidelity
**Statement**: Simulated visibility models exhibit systematic bias compared to physical measurements, with bias magnitude varying across occlusion types (self-occlusion, external occlusion, sensor limitations) and calibration methods.

**Independent variables**:
- Occlusion type: Self-occlusion (object geometry), external occlusion (obstacles), sensor limitations (field-of-view, resolution)
- Calibration method: No calibration (default simulator parameters), geometric calibration (camera intrinsics/extrinsics), full calibration (geometric + sensor noise + illumination)

**Dependent variables**:
- Visibility prediction error: Absolute difference between simulated and measured visibility (percentage of surface visible)
- Coverage prediction error: Absolute difference between simulated and measured coverage (percentage of surface observed above resolution threshold)
- Occlusion detection error: False positive and false negative rates for occlusion detection

**Controls**:
- Fixed robot platform: Franka Panda manipulator with Intel RealSense D435i camera
- Fixed environment: Controlled laboratory setup with standardized lighting and object placement
- Fixed target objects: YCB objects with known geometry
- Independent ground truth: Laser tracker or photogrammetry system

**Validation**:
- Repeated trials: n≥30 per condition (3 occlusion types × 3 calibration methods = 9 conditions × 30 trials = 270 trials)
- Statistical analysis: Two-way repeated measures ANOVA with post-hoc Tukey HSD comparisons
- Effect size: Partial eta-squared (η²p) for each main effect and interaction
- Power analysis: Ensure 80% power to detect medium effect sizes (η²p ≥ 0.06)

**Expected outcome**: Significant main effects of occlusion type (F(2,58) > 3.0, p < 0.05) and calibration method (F(2,58) > 3.0, p < 0.05) on visibility and coverage prediction errors; full calibration < geometric calibration < no calibration for prediction errors

**Falsification criteria**: If no significant main effects or interactions are observed (p > 0.05), or if calibration does not reduce prediction errors, the hypothesis is rejected

---

## C.2 Experimental Recommendations

### C.2.1 Datasets and Benchmark Environments

#### Recommended Datasets

**1. YCB Object and Model Set**
- **Description**: Standardized set of 77 objects with known geometry, texture, and physical properties
- **Relevance**: Enables coverage evaluation with ground truth geometry
- **Usage**: Target objects for inspection tasks; coverage completeness validation
- **Availability**: http://www.ycbbenchmarks.com/

**2. ShapeNet**
- **Description**: Large-scale 3D object dataset with 51,300 models across 55 categories
- **Relevance**: Enables large-scale simulation experiments with diverse object geometries
- **Usage**: Simulation-based evaluation; generalization testing
- **Availability**: https://shapenet.org/

**3. Replica**
- **Description**: Photo-realistic 3D scene models for indoor environments
- **Relevance**: Enables realistic simulation of navigation and inspection tasks
- **Usage**: Simulation-based evaluation; sim-to-real transfer validation
- **Availability**: https://github.com/facebookresearch/Replica-Dataset

**4. LIBERO**
- **Description**: Manipulation benchmark with diverse tasks and environments
- **Relevance**: Enables standardized evaluation of manipulation and inspection tasks
- **Usage**: Benchmarking; comparison against existing methods
- **Availability**: https://libero-project.github.io/

**5. Custom ARC-RVI Benchmark Dataset**
- **Description**: Curated dataset for autonomous visual inspection evaluation
- **Contents**: 
  - Standardized inspection tasks (object documentation, surface coverage, defect localization)
  - Controlled environmental variations (lighting, object placement, occlusion)
  - Multi-platform validation data (manipulator, mobile robot, humanoid)
  - Ground truth measurements (laser tracker, photogrammetry)
- **Relevance**: Addresses gap in inspection-specific benchmarking
- **Usage**: Primary evaluation dataset for ARC-RVI research
- **Availability**: To be released publicly upon completion

---

#### Recommended Benchmark Environments

**1. Controlled Laboratory Setup**
- **Description**: Adjustable lighting, object placement, and occlusion for systematic evaluation
- **Components**:
  - Programmable LED lighting array (100–2000 lux, adjustable color temperature)
  - Precision positioning stage for object placement (±0.1 mm accuracy)
  - Modular occlusion panels (0%, 25%, 50%, 75% occlusion levels)
  - Independent measurement system (laser tracker or photogrammetry)
- **Relevance**: Enables controlled experimental validation with ground truth
- **Usage**: Primary physical validation environment

**2. Simulated Environments**
- **Isaac Sim**: NVIDIA's physics-based simulation platform with photo-realistic rendering
  - **Relevance**: Enables large-scale evaluation and domain randomization
  - **Usage**: Sim-to-real transfer experiments; large-scale benchmarking
  - **Availability**: https://developer.nvidia.com/isaac-sim

- **Gazebo**: Open-source robot simulation platform with ROS integration
  - **Relevance**: Widely used in robotics research; supports diverse robot platforms
  - **Usage**: Simulation-based evaluation; comparison against existing methods
  - **Availability**: http://gazebosim.org/

- **MuJoCo**: Physics engine for robotics and biomechanics simulation
  - **Relevance**: Fast, accurate physics simulation; supports contact-rich tasks
  - **Usage**: Simulation-based evaluation; reinforcement learning experiments
  - **Availability**: https://mujoco.org/

**3. Real-World Scenarios**
- **Office environment**: Desks, shelves, cabinets for object inspection
- **Warehouse environment**: Pallets, boxes, industrial equipment for large-scale inspection
- **Manufacturing environment**: Assembly lines, workstations, quality control stations

---

### C.2.2 Baseline Algorithms

#### Viewpoint Planning Baselines

**1. Coverage-First Methods**
- **Set Covering Problem (SCP)**: Formulates viewpoint selection as SCP; minimizes number of viewpoints for complete coverage [1], [2], [3]
- **Traveling Salesman Problem (TSP)**: Formulates viewpoint sequencing as TSP; minimizes travel distance [1], [2], [10]
- **Generalized TSP (GTSP)**: Formulates scan path selection as GTSP; incorporates kinematic constraints [2]

**2. Information-Theoretic NBV**
- **Entropy Reduction**: Selects viewpoints maximizing expected entropy reduction in occupancy map [2], [3], [5]
- **Mutual Information**: Selects viewpoints maximizing mutual information between observations and scene geometry [2], [3]
- **Coverage Gain**: Selects viewpoints maximizing expected coverage gain [1], [5]

**3. Learning-Based NBV**
- **3D CNN-Based Scoring**: Uses 3D convolutional neural networks to predict viewpoint utility from occupancy maps [22]
- **Reinforcement Learning**: Trains policies via RL to select viewpoints maximizing cumulative reward [14]
- **Transformer-Based Generation**: Uses Transformer architectures to generate viewpoint sequences [9]

---

#### Quality Control Baselines

**1. Adaptive Exposure Control**
- **Gradient-Based**: Maximizes image gradient information [3], [16]
- **Entropy-Based**: Maximizes image entropy [6], [8]
- **Bayesian Optimization**: Uses Bayesian optimization to learn optimal exposure parameters [15], [23]
- **Reinforcement Learning**: Trains policies via RL to adjust exposure in dynamic lighting [9]

**2. Noise-Aware Quality Assessment**
- **Gradient + Entropy + Noise**: Combines gradient, entropy, and noise metrics [8]
- **No-Reference Quality Estimation**: Uses learned models to predict quality without reference images [14]

**3. Motion Blur Detection**
- **Edge Detection**: Uses improved edge detection with Gaussian noise reduction [7]
- **Laplacian Variance**: Uses Laplacian variance to detect blur [27]
- **IMU-Based Detection**: Uses IMU signals to detect motion blur [30]

---

#### Sim-to-Real Transfer Baselines

**1. Domain Randomization**
- **Visual Randomization**: Varies textures, lighting, colors, camera parameters [1], [2], [9], [14]
- **Physics Randomization**: Varies object masses, friction coefficients, contact parameters [1], [4]
- **Sensor Randomization**: Varies sensor noise, resolution, field-of-view [8], [14]

**2. Domain Adaptation**
- **Feature Alignment**: Aligns feature distributions between simulation and reality [10], [11], [22]
- **Adversarial Training**: Uses adversarial loss to encourage domain-invariant features [11], [22]
- **Dual VAE**: Uses dual variational autoencoders with shared decoder [11]

**3. Real-to-Sim Calibration**
- **System Identification**: Estimates physical parameters from video observations [6], [17], [23]
- **VLM-Guided Calibration**: Uses vision-language models to diagnose sim-real mismatches [17], [23]
- **3D Gaussian Splatting**: Uses 3D Gaussian splatting to model real scenes [25]

---

### C.2.3 Statistical Methods and Validation Procedures

#### Recommended Statistical Methods

**1. Repeated Measures ANOVA**
- **Purpose**: Compare methods across multiple conditions with repeated trials
- **Assumptions**: Normality, sphericity (Mauchly's test), homogeneity of variance
- **Post-hoc tests**: Tukey HSD or Bonferroni correction for pairwise comparisons
- **Effect size**: Partial eta-squared (η²p) to quantify practical significance
- **Software**: R (ez package), Python (statsmodels), SPSS

**2. Paired t-tests**
- **Purpose**: Compare two methods on the same subjects/trials
- **Assumptions**: Normality of differences, independence of observations
- **Effect size**: Cohen's d to quantify practical significance
- **Software**: R (t.test), Python (scipy.stats), SPSS

**3. Power Analysis**
- **Purpose**: Determine required sample sizes for detecting meaningful differences
- **Parameters**: Desired power (typically 0.80), significance level (typically 0.05), expected effect size
- **Software**: G*Power, R (pwr package), Python (statsmodels)

**4. Confidence Intervals**
- **Purpose**: Report uncertainty in effect estimates
- **Recommendation**: Report 95% CIs for all effect estimates
- **Interpretation**: If CI excludes zero, effect is statistically significant at α = 0.05

---

#### Validation Procedures

**1. Cross-Validation**
- **Purpose**: Assess generalization of learning-based methods
- **Methods**: K-fold cross-validation (k=5 or k=10), leave-one-out cross-validation
- **Application**: Learning-based NBV, quality assessment, sim-to-real transfer

**2. Held-Out Test Sets**
- **Purpose**: Independent evaluation data not used during training or tuning
- **Recommendation**: 70% training, 15% validation, 15% test split
- **Application**: All learning-based methods

**3. Ablation Studies**
- **Purpose**: Assess individual contributions of components
- **Method**: Systematically remove components and measure performance degradation
- **Application**: All multi-component methods (e.g., quality-aware NBV, integrated planning)

**4. Sensitivity Analysis**
- **Purpose**: Assess robustness to parameter variations
- **Method**: Vary parameters (e.g., ±10%, ±20%) and measure performance changes
- **Application**: All methods with tunable parameters

**5. Independent Replication**
- **Purpose**: Verify reproducibility of results
- **Method**: Independent researchers replicate experiments using published code and data
- **Recommendation**: Provide open-source code, datasets, and detailed documentation

---

### C.2.4 Experimental Design Recommendations

#### General Principles

**1. Randomization**
- Randomize trial order to control for learning effects and temporal confounds
- Use blocked randomization to ensure balanced conditions

**2. Blinding**
- Blind experimenters to condition assignments when possible
- Use automated data collection and analysis to minimize experimenter bias

**3. Replication**
- Conduct sufficient repeated trials (n≥30 per condition) for statistical power
- Replicate key experiments across multiple sessions and environments

**4. Ground Truth**
- Use independent measurement systems (laser trackers, photogrammetry) for ground truth
- Validate ground truth accuracy and precision

**5. Documentation**
- Document all experimental procedures, parameters, and deviations
- Provide detailed supplementary materials for reproducibility

---

#### Platform-Specific Recommendations

**1. Humanoid Platform (Unitree G1)**
- **Safety**: Implement emergency stop procedures; use safety barriers
- **Calibration**: Calibrate camera intrinsics/extrinsics; validate kinematic model
- **Stability**: Monitor center of mass; implement fall detection and recovery
- **Repeatability**: Conduct repeated trials to assess pose repeatability

**2. Manipulator Platform (Franka Panda)**
- **Safety**: Implement collision detection; use safety-rated controllers
- **Calibration**: Calibrate camera intrinsics/extrinsics; validate kinematic model
- **Repeatability**: Conduct repeated trials to assess pose repeatability

**3. Mobile Robot Platform (Clearpath Husky + UR5)**
- **Safety**: Implement obstacle detection; use safety-rated controllers
- **Calibration**: Calibrate camera intrinsics/extrinsics; validate kinematic model
- **Localization**: Use independent localization system (motion capture, laser tracker)

---

### C.2.5 Recommended Evaluation Metrics

#### Coverage Metrics

**1. Coverage Completeness**
- **Definition**: Percentage of target surface observed above resolution threshold
- **Calculation**: (Observed surface area) / (Total surface area) × 100%
- **Threshold**: Minimum resolution (e.g., 1 mm/pixel for defect detection)

**2. Coverage Efficiency**
- **Definition**: Coverage completeness per unit time or per viewpoint
- **Calculation**: (Coverage completeness) / (Execution time or number of viewpoints)

**3. Coverage Redundancy**
- **Definition**: Average number of times each surface point is observed
- **Calculation**: (Total observations) / (Unique surface points observed)

---

#### Quality Metrics

**1. Acquisition Quality Score**
- **Definition**: Composite metric combining blur, exposure, occlusion, framing
- **Components**:
  - Blur score: Laplacian variance or gradient magnitude
  - Exposure score: Histogram distribution or entropy
  - Occlusion score: Percentage of target visible
  - Framing score: Target size and centering in image
- **Calculation**: Weighted average of component scores (0–1 scale)

**2. Re-Observation Frequency**
- **Definition**: Percentage of viewpoints requiring re-observation due to poor quality
- **Calculation**: (Number of re-observations) / (Total viewpoints) × 100%

---

#### Repeatability Metrics

**1. Pose Repeatability**
- **Definition**: Standard deviation of camera pose across repeated trials
- **Calculation**: σ(position) in mm, σ(orientation) in degrees
- **Measurement**: Laser tracker or motion capture system

**2. Image Attribute Consistency**
- **Definition**: Standard deviation of image attributes across repeated trials
- **Attributes**: Resolution, blur, exposure, framing
- **Calculation**: σ(attribute) for each attribute

---

#### Efficiency Metrics

**1. Execution Time**
- **Definition**: Total time from start to completion
- **Components**: Planning time, motion time, acquisition time, quality assessment time

**2. Motion Distance**
- **Definition**: Total distance traveled by robot end-effector or base
- **Calculation**: Sum of Euclidean distances between consecutive poses

**3. Number of Viewpoints**
- **Definition**: Total number of viewpoints required for complete coverage
- **Calculation**: Count of unique camera poses

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