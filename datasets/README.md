# Dataset governance

This directory holds policy and published dataset descriptors only.

A separately maintained historical source is
[`MatPomGit/alf-luca`](https://github.com/MatPomGit/alf-luca), a camera,
calibration and tracking program confirmed by the project owner to have run
on a Unitree G1 EDU. It includes [video recordings](https://github.com/MatPomGit/alf-luca/tree/main/video),
[extracted calibration frames](https://github.com/MatPomGit/alf-luca/tree/main/images_calib)
and a `camera_calib.npz` calibration artifact. These files remain in their
source repository; they are **not** bundled as ARC-RVI datasets. Before using
them in an experiment, audit recording origin, licensing/publication rights,
calibration quality, acquisition metadata, source revision and session-level
split independence. See the [G1 provenance notes](../docs/g1-reference/README.md).

Do not commit raw photos, telemetry, actual identifiers, subject data or
uncleared third-party datasets. Keep source data in access-controlled storage.
For each approved dataset, separately record license/permission, release
status, content hash, acquisition conditions, calibration, annotation protocol,
group identifiers for train/validation/test separation and retention policy.

Images from one physical object or session must not leak across independent
evaluation partitions. Publication requires rights clearance and privacy review.
