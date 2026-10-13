"""
Capability registry.
Add new capabilities here — import the class and call register().
The connection handler and operator API both use this registry.
"""

from capabilities.base import Capability
from capabilities.shell_exec import ShellExec

_registry: dict[str, type[Capability]] = {}


def register(cls: type[Capability]):
    """Register a capability class by its name."""
    _registry[cls.name] = cls
    return cls


def get(name: str) -> type[Capability] | None:
    return _registry.get(name)


def list_capabilities() -> list[dict]:
    return [{"name": c.name, "description": c.description} for c in _registry.values()]


# Built-in capabilities
register(ShellExec)
