"""Deterministic planar geometry/kinematics model; no physics engine or robot I/O."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from math import atan2, fsum, hypot, isfinite, pi, ulp
from pathlib import Path

from ..evidence import digest, software_provenance
from ..geometry import angular_distance, segment_distance
from ..interfaces import AdapterUnavailable, CameraPose, SimulatedObservation
from ..scenarios import name, number, read_json

DISTANCE_TOLERANCE_M = 1e-10
ANGLE_TOLERANCE_RAD = 1e-12


@dataclass(frozen=True)
class CameraModel:
    horizontal_fov_rad: float
    min_range_m: float
    max_range_m: float
    max_incidence_rad: float


@dataclass(frozen=True)
class MotionModel:
    linear_speed_m_s: float
    angular_speed_rad_s: float
    robot_radius_m: float
    capture_duration_s: float
    max_time_s: float


@dataclass(frozen=True)
class Circle:
    x: float
    y: float
    radius_m: float


@dataclass(frozen=True)
class SurfacePatch:
    identifier: str
    x: float
    y: float
    normal_rad: float
    area_m2: float


@dataclass(frozen=True)
class PlanarScene:
    identifier: str
    start: CameraPose
    camera: CameraModel
    motion: MotionModel
    obstacles: tuple[Circle, ...]
    patches: tuple[SurfacePatch, ...]
    route: tuple[CameraPose, ...]


def validate_pose(pose: CameraPose) -> None:
    for value in (pose.x, pose.y, pose.yaw_rad):
        number(value, "pose coordinate or angle")
    if abs(pose.yaw_rad) > pi:
        raise ValueError("yaw_rad must be in [-pi, pi]")


class PlanarSimulator:
    def __init__(self, scene: PlanarScene):
        self.scene = scene
        name(scene.identifier, "scene_id")
        validate_pose(scene.start)
        for pose in scene.route:
            validate_pose(pose)
        camera, motion = scene.camera, scene.motion
        for value in asdict(camera).values():
            number(value, "camera parameter", nonnegative=True)
        if not 0 < camera.horizontal_fov_rad <= 2 * pi:
            raise ValueError("horizontal_fov_rad must be in (0, 2*pi]")
        if not camera.min_range_m < camera.max_range_m:
            raise ValueError("camera range must have min < max")
        if not 0 <= camera.max_incidence_rad <= pi / 2:
            raise ValueError("max_incidence_rad must be in [0, pi/2]")
        for field, value in asdict(motion).items():
            number(value, field, nonnegative=True)
        if motion.linear_speed_m_s <= 0 or motion.angular_speed_rad_s <= 0:
            raise ValueError("motion speeds must be positive")
        if not scene.patches:
            raise ValueError("scene needs at least one surface patch")
        identifiers = set()
        for patch in scene.patches:
            name(patch.identifier, "patch id")
            if patch.identifier in identifiers:
                raise ValueError("duplicate surface patch id")
            identifiers.add(patch.identifier)
            for value in (patch.x, patch.y, patch.normal_rad):
                number(value, "surface patch coordinate or angle")
            if abs(patch.normal_rad) > pi:
                raise ValueError("normal_rad must be in [-pi, pi]")
            if number(patch.area_m2, "area_m2", nonnegative=True) <= 0:
                raise ValueError("patch area must be positive")
        try:
            total_area = fsum(patch.area_m2 for patch in scene.patches)
        except OverflowError as exc:
            raise ValueError("total surface area must be finite") from exc
        if not isfinite(total_area):
            raise ValueError("total surface area must be finite")
        for obstacle in scene.obstacles:
            number(obstacle.x, "obstacle x")
            number(obstacle.y, "obstacle y")
            if number(obstacle.radius_m, "obstacle radius", nonnegative=True) <= 0:
                raise ValueError("obstacle radius must be positive")
        origin = (scene.start.x, scene.start.y)
        if self.blocked(origin, origin, motion.robot_radius_m):
            raise ValueError("start pose intersects an obstacle")
        self.reset()

    def reset(self) -> None:
        self.pose = self.scene.start
        self.elapsed_time_s = 0.0
        self.travel_distance_m = 0.0
        self.failure_reason = None

    def blocked(self, start, end, radius_m=0.0) -> bool:
        return any(segment_distance((item.x, item.y), start, end)
                   <= item.radius_m + radius_m + DISTANCE_TOLERANCE_M
                   for item in self.scene.obstacles)

    def visible_patches(self, pose: CameraPose) -> tuple[str, ...]:
        validate_pose(pose)
        camera = self.scene.camera
        visible = []
        for patch in self.scene.patches:
            dx, dy = patch.x - pose.x, patch.y - pose.y
            distance = hypot(dx, dy)
            if not isfinite(distance):
                raise ValueError("geometry exceeds finite camera range")
            if distance == 0 or not camera.min_range_m <= distance <= camera.max_range_m:
                continue
            bearing = atan2(dy, dx)
            if angular_distance(bearing, pose.yaw_rad) > camera.horizontal_fov_rad / 2 + ANGLE_TOLERANCE_RAD:
                continue
            if angular_distance(atan2(-dy, -dx), patch.normal_rad) > camera.max_incidence_rad + ANGLE_TOLERANCE_RAD:
                continue
            if not self.blocked((pose.x, pose.y), (patch.x, patch.y)):
                visible.append(patch.identifier)
        return tuple(sorted(visible))

    def acquire(self, pose: CameraPose) -> SimulatedObservation:
        if self.failure_reason is not None:
            raise ValueError("reset simulator after a rejected action")
        validate_pose(pose)
        distance = hypot(pose.x - self.pose.x, pose.y - self.pose.y)
        motion = self.scene.motion
        duration = (distance / motion.linear_speed_m_s
                    + angular_distance(pose.yaw_rad, self.pose.yaw_rad) / motion.angular_speed_rad_s
                    + motion.capture_duration_s)
        if not all(isfinite(value) for value in (distance, duration, self.elapsed_time_s + duration,
                                                 self.travel_distance_m + distance)):
            raise ValueError("motion produces a non-finite distance or duration")
        total_time = self.elapsed_time_s + duration
        rounding_slack = 8 * max(ulp(total_time), ulp(motion.max_time_s))
        if total_time > motion.max_time_s and total_time - motion.max_time_s > rounding_slack:
            self.failure_reason = "time_budget_exceeded"
        elif self.blocked((self.pose.x, self.pose.y), (pose.x, pose.y), motion.robot_radius_m):
            self.failure_reason = "path_collision"
        if self.failure_reason:
            return SimulatedObservation(self.pose, (), self.elapsed_time_s,
                                        self.travel_distance_m, self.failure_reason)
        visible = self.visible_patches(pose)
        self.pose = pose
        self.elapsed_time_s += duration
        self.travel_distance_m += distance
        return SimulatedObservation(pose, visible, self.elapsed_time_s, self.travel_distance_m, None)


def exact_fields(value, fields: set[str], label: str) -> dict:
    if not isinstance(value, dict) or value.keys() != fields:
        raise ValueError(f"{label} fields must be: {', '.join(sorted(fields))}")
    return value


def load_scene(path: Path) -> tuple[PlanarScene, bytes]:
    payload, raw = read_json(path)
    exact_fields(payload, {"schema_version", "scene_id", "evidence_type", "start", "camera",
                           "motion", "obstacles", "patches", "route"}, "scene")
    if payload["schema_version"] != "1.0.0" or payload["evidence_type"] != "simulation":
        raise ValueError("only version 1.0.0 simulation scenes are supported")

    def pose(entry):
        return CameraPose(**exact_fields(entry, {"x", "y", "yaw_rad"}, "pose"))

    for field in ("obstacles", "patches", "route"):
        if not isinstance(payload[field], list):
            raise ValueError(f"{field} must be a list")
    camera = CameraModel(**exact_fields(payload["camera"], set(CameraModel.__annotations__), "camera"))
    motion = MotionModel(**exact_fields(payload["motion"], set(MotionModel.__annotations__), "motion"))
    obstacles = tuple(Circle(**exact_fields(entry, set(Circle.__annotations__), "obstacle"))
                      for entry in payload["obstacles"])
    patches = tuple(SurfacePatch(**exact_fields(entry, set(SurfacePatch.__annotations__), "patch"))
                    for entry in payload["patches"])
    scene = PlanarScene(payload["scene_id"], pose(payload["start"]), camera, motion,
                        obstacles, patches, tuple(pose(entry) for entry in payload["route"]))
    return scene, raw


def run_simulation(path: Path) -> dict:
    scene, raw = load_scene(path)
    simulator = PlanarSimulator(scene)
    covered = set()
    observations = []
    for index, pose in enumerate(scene.route, start=1):
        observation = simulator.acquire(pose)
        observations.append({"step": index, "requested_pose": asdict(pose),
                             **asdict(observation)})
        covered.update(observation.visible_patch_ids)
        if observation.failure_reason:
            break
    total = fsum(patch.area_m2 for patch in scene.patches)
    covered_area = fsum(patch.area_m2 for patch in scene.patches if patch.identifier in covered)
    reason = simulator.failure_reason
    return {"schema_version": "1.0.0", "scene_id": scene.identifier,
            "evidence_type": "simulation", "model": "planar_geometry_kinematics_v1",
            "source": software_provenance(), "scene_sha256": digest(raw), "randomness": "none",
            "observations": observations, "covered_patch_ids": sorted(covered),
            "missing_patch_ids": sorted(patch.identifier for patch in scene.patches
                                        if patch.identifier not in covered),
            "sampled_surface_coverage": covered_area / total,
            "elapsed_time_s": simulator.elapsed_time_s,
            "travel_distance_m": simulator.travel_distance_m,
            "route_complete": reason is None,
            "coverage_complete": len(covered) == len(scene.patches),
            "status": "completed" if reason is None else "algorithm_failure",
            "failure_reason": reason}


def connect_simulator() -> None:
    """The separate external physics-engine connector remains unavailable."""
    raise AdapterUnavailable("physics simulator integration not configured")
