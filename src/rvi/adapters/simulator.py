"""Physics-simulator integration boundary; not implemented yet."""

from ..interfaces import AdapterUnavailable


def connect_simulator() -> None:
    raise AdapterUnavailable("physics simulator integration not configured")
