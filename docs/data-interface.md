# Neutral data interface (draft)

Proposed export package:
- `manifest.json`: schema version, evidence level, session ID, capture setup,
  relative paths, SHA-256 hashes, validity status, and calibration reference.
- `images/`: independently approved image assets.
- `quality.json`: measured focus/exposure/coverage metrics and thresholds.
- `poses.json`: timestamped coordinate frame and robot/camera pose estimates.

For the planned G1 EDU sensor ingestion boundary, preserve each stream's
original timestamp, `frame_id`, native units/resolution, calibration hash,
validity/missingness and dataset rights. Candidate sources in the user-supplied
manual include RGB, depth, 3D LiDAR, IMU and joint states; installed
devices and actual ROS 2 topics are **not verified**. Do not hard-code
illustrative `/camera/*` or `/lidar/*` topics as operational defaults.
TF2 camera-to-base and LiDAR-to-base extrinsics require independent
reference checks before geometric fusion.

Require schema validation and version negotiation before integration. Do not
include personal names, customers, registration plates or proprietary metadata.
The current `build_image_manifest` function only records paths, sizes and
SHA-256; it does not implement the entire proposed export contract.
