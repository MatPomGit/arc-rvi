"""Acquisition experiment boundary.

Image capture requires a device-specific, safety-reviewed adapter.
"""

from .interfaces import RobotAdapter

__all__ = ["RobotAdapter"]
