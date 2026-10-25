"""Navigation experiment boundary.

Path execution and safety-certified robot motion are not implemented.
Use a dedicated, validated adapter before physical deployment.
"""

from .interfaces import RobotAdapter

__all__ = ["RobotAdapter"]
