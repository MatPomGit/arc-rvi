#!/usr/bin/env python3
"""Read-only G1 EDU SSH inventory; no robot commands, privileged operations or installs.

Run remotely via: ssh -T ROBOT 'python3 - --dds-interface eth0' < this_file > report.json
The report intentionally omits hostnames, serials, MACs, addresses and motor data.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
from hashlib import sha256
from importlib import metadata, util
import json
import os
from pathlib import Path
import platform
import re
import subprocess
import sys

SCHEMA = "1.0.0"
MAX_URDF_BYTES = 2_000_000
MAX_URDFS = 24
DDS_TIMEOUT_S = 9

# The entire DDS subscriber lives in a separately bounded process, so SDK
# threads cannot hold the SSH session open. No ChannelPublisher is imported.
DDS_READ_ONLY = r'''
import json
import os
import sys
from threading import Event

result = {"status": "no_lowstate_received", "mode_machine": None}
ready = Event()
try:
    from unitree_sdk2py.core.channel import ChannelFactoryInitialize, ChannelSubscriber
    from unitree_sdk2py.idl.unitree_hg.msg.dds_ import LowState_
    ChannelFactoryInitialize(0, sys.argv[1])
    def receive(msg):
        if not ready.is_set():
            value = getattr(msg, "mode_machine", None)
            if type(value) is int and 0 <= value <= 255:
                result.update(status="received", mode_machine=value)
            else:
                result["status"] = "invalid_mode_machine"
            ready.set()
    subscriber = ChannelSubscriber("rt/lowstate", LowState_)
    subscriber.Init(receive, 1)
    ready.wait(5)
except Exception as exc:
    result["status"] = "sdk_or_dds_error"
    result["error_type"] = type(exc).__name__
finally:
    # Exit only this isolated read-only diagnostic subprocess, even if DDS
    # implementation leaves non-daemon background threads active.
    print("RVI_DDS_JSON=" + json.dumps(result, sort_keys=True), flush=True)
    os._exit(0)
'''


def _read(path: Path, limit: int = 256) -> str | None:
    """Read one bounded sysfs/proc value; no recursive inspection."""
    try:
        if not path.is_file() or path.stat().st_size > 65536:
            return None
        return path.read_text(encoding="utf-8", errors="replace")[:limit].strip()
    except (OSError, ValueError, UnicodeError):
        return None


def _os_release() -> dict[str, str]:
    data = {}
    raw = _read(Path("/etc/os-release"), 8192) or ""
    for line in raw.splitlines():
        key, sep, value = line.partition("=")
        if sep and key in {"ID", "VERSION_ID", "PRETTY_NAME"}:
            data[key.lower()] = value.strip('"')[:160]
    return data


def _list_devices(root: Path, keys: tuple[str, ...], limit: int = 40) -> list[dict]:
    entries = []
    if not root.is_dir():
        return entries
    try:
        candidates = sorted(root.iterdir(), key=lambda p: p.name)[:limit]
    except OSError:
        return entries
    for entry in candidates:
        properties = {key: value for key in keys
                      if (value := _read(entry / key, 128)) is not None}
        if properties:
            entries.append({"sysfs_name": entry.name, **properties})
    return entries


def _net_interfaces() -> list[dict]:
    entries = []
    root = Path("/sys/class/net")
    if root.is_dir():
        for entry in sorted(root.iterdir(), key=lambda p: p.name)[:32]:
            if not re.fullmatch(r"[a-zA-Z0-9_.:-]{1,40}", entry.name):
                continue
            entries.append({"interface": entry.name,
                            "operstate": _read(entry / "operstate", 32),
                            "carrier": _read(entry / "carrier", 4)})
    return entries


def _versions() -> dict[str, dict]:
    distribution_names = {"unitree-sdk2py": "unitree-sdk2py", "cyclonedds": "cyclonedds",
                          "pyrealsense2": "pyrealsense2", "rclpy": "rclpy",
                          "opencv-python": "opencv-python"}
    result = {}
    for display, distribution in distribution_names.items():
        try:
            result[display] = {"installed": True,
                               "version": metadata.version(distribution)}
        except metadata.PackageNotFoundError:
            result[display] = {"installed": False, "version": None}
    # The module may be installed from source without wheel metadata.
    try:
        result["unitree-sdk2py"]["module_importable"] = (
            util.find_spec("unitree_sdk2py") is not None)
    except (ImportError, ValueError):
        result["unitree-sdk2py"]["module_importable"] = False
    return result


def _ros() -> dict:
    root = Path("/opt/ros")
    installs = []
    if root.is_dir():
        installs = sorted(x.name for x in root.iterdir()
                          if x.is_dir() and re.fullmatch(r"[A-Za-z0-9_-]+", x.name))[:12]
    # Never export arbitrary environment variables or their values.
    return {"distributions_on_disk": installs,
            "active_ros_distro": os.environ.get("ROS_DISTRO")
            if os.environ.get("ROS_DISTRO", "").lower() in {
                "foxy", "galactic", "humble", "iron", "jazzy", "rolling", "kilted"}
            else None,
            "ros_domain_id": int(os.environ["ROS_DOMAIN_ID"])
            if os.environ.get("ROS_DOMAIN_ID", "").isdigit()
            and 0 <= int(os.environ["ROS_DOMAIN_ID"]) <= 232 else None}


def _candidate_urdfs(extra: list[Path]) -> list[dict]:
    """Search only bounded, explicitly named description roots, never ~/ recursively."""
    home = Path.home()
    paths = [home / "unitree_ros/robots/g1_description",
             home / "unitree_rl_gym/resources/robots/g1_description",
             home / "g1_description/urdf",
             home / "unitree_ros2/robots/g1_description"]
    paths.extend(extra[:4])
    seen = set()
    found = []
    for root in paths:
        if not root.is_dir() or root.is_symlink():
            continue
        for path in sorted(root.glob("*.urdf"))[:MAX_URDFS]:
            if len(found) >= MAX_URDFS:
                return found
            if path.is_symlink() or not path.is_file() or path in seen:
                continue
            seen.add(path)
            try:
                size = path.stat().st_size
                if size > MAX_URDF_BYTES:
                    continue
                raw = path.read_bytes()
            except OSError:
                continue
            # This is merely a file listing/hash, not the ARC-RVI URDF validator.
            location = str(path)
            if path.is_relative_to(home):
                location = "~/" + str(path.relative_to(home))
            found.append({"path": location, "bytes": len(raw),
                          "sha256": sha256(raw).hexdigest()})
    return found


def _dds_mode(interface: str | None) -> dict:
    if interface is None:
        return {"status": "not_requested", "mode_machine": None}
    if interface not in {x["interface"] for x in _net_interfaces()}:
        return {"status": "interface_not_found", "mode_machine": None}
    try:
        proc = subprocess.run([sys.executable, "-c", DDS_READ_ONLY, interface],
                              capture_output=True, text=True, timeout=DDS_TIMEOUT_S,
                              check=False)
    except subprocess.TimeoutExpired:
        return {"status": "bounded_timeout", "mode_machine": None}
    if proc.returncode != 0:
        return {"status": "subscriber_process_failed", "mode_machine": None}
    try:
        messages = [line.removeprefix("RVI_DDS_JSON=")
                    for line in proc.stdout.splitlines()
                    if line.startswith("RVI_DDS_JSON=")]
        if len(messages) != 1:
            raise ValueError("no unique DDS result")
        data = json.loads(messages[0])
        if (not isinstance(data, dict) or data.get("status") not in
                {"received", "no_lowstate_received", "invalid_mode_machine",
                 "sdk_or_dds_error"}):
            raise ValueError("invalid DDS output")
        if data.get("status") == "received" and (
                type(data.get("mode_machine")) is not int
                or not 0 <= data["mode_machine"] <= 255):
            raise ValueError("bad mode")
        return {"interface": interface, "subscription": "rt/lowstate_only", **data}
    except (ValueError, TypeError):
        return {"status": "invalid_subscriber_response", "mode_machine": None}


def collect(*, interface: str | None = None,
            urdf_dirs: list[Path] | None = None) -> dict:
    """Collect unprivileged diagnostic facts; never start/stop any device service."""
    return {
        "schema_version": SCHEMA,
        "evidence_type": "system_inventory_read_only_not_physical_validation",
        "captured_utc": datetime.now(timezone.utc).isoformat(),
        "robot_identity": "user_identified_unitree_g1_edu_unverified",
        "os": {**_os_release(), "kernel": platform.release(),
               "architecture": platform.machine(),
               "python": platform.python_version()},
        "network": {"interfaces_without_addresses": _net_interfaces()},
        "devices": {
            "usb_without_serials": _list_devices(Path("/sys/bus/usb/devices"),
                                                 ("idVendor", "idProduct", "manufacturer", "product")),
            "video": _list_devices(Path("/sys/class/video4linux"), ("name",)),
            "iio": _list_devices(Path("/sys/bus/iio/devices"), ("name",)),
        },
        "software": {"python_packages": _versions(), "ros": _ros()},
        "local_urdf_candidates": _candidate_urdfs(urdf_dirs or []),
        "dds_lowstate": _dds_mode(interface),
        "not_verified": [
            "serial_and_exact_hardware_variant", "installed_sensor_calibration",
            "camera_lidar_imu_extrinsics", "physical_safety_authorization",
            "urdf_kinematic_equivalence", "hardware_joint_limits",
        ],
        "privacy": "no_hostnames_ips_macs_serials_passwords_or_raw_motor_state",
        "control": "no_publishers_no_commands_no_motion",
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dds-interface", metavar="IFACE",
                        help="optional bounded read-only rt/lowstate subscription")
    parser.add_argument("--urdf-dir", type=Path, action="append", default=[],
                        help="additional local description directory (max 4)")
    args = parser.parse_args(argv)
    if args.dds_interface is not None and not re.fullmatch(
            r"[a-zA-Z0-9_.:-]{1,40}", args.dds_interface):
        parser.error("invalid DDS interface name")
    try:
        report = collect(interface=args.dds_interface, urdf_dirs=args.urdf_dir)
    except (OSError, ValueError) as exc:
        print(f"Robot inspection failed: {type(exc).__name__}", file=sys.stderr)
        return 2
    print(json.dumps(report, indent=2, sort_keys=True, ensure_ascii=False,
                     allow_nan=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
