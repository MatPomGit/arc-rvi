# Neutral data interface (draft)

Proposed export package:
- `manifest.json`: schema version, evidence level, session ID, capture setup,
  relative paths, SHA-256 hashes, validity status, and calibration reference.
- `images/`: independently approved image assets.
- `quality.json`: measured focus/exposure/coverage metrics and thresholds.
- `poses.json`: timestamped coordinate frame and robot/camera pose estimates.

Require schema validation and version negotiation before integration. Do not
include personal names, customers, registration plates or proprietary metadata.
The current `build_image_manifest` function only records paths, sizes and
SHA-256; it does not implement the entire proposed export contract.
