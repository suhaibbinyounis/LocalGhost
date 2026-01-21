"""Base plugin interface."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Coroutine


class EndpointType(str, Enum):
    """Endpoint visibility type."""

    PUBLIC = "public"  # No auth required
    PROTECTED = "protected"  # Requires authorization


@dataclass
class Endpoint:
    """Endpoint definition."""

    path: str
    handler: Callable[..., Coroutine[Any, Any, Any]]
    endpoint_type: EndpointType = EndpointType.PROTECTED
    method: str = "GET"
    description: str = ""
    permissions: list[str] = field(default_factory=list)


class Plugin(ABC):
    """Base class for LocalGhost plugins."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Plugin name."""
        ...

    @property
    @abstractmethod
    def version(self) -> str:
        """Plugin version."""
        ...

    @property
    def description(self) -> str:
        """Plugin description."""
        return ""

    @abstractmethod
    def get_endpoints(self) -> list[Endpoint]:
        """Return list of endpoints this plugin exposes."""
        ...

    async def on_load(self) -> None:
        """Called when plugin is loaded."""
        pass

    async def on_unload(self) -> None:
        """Called when plugin is unloaded."""
        pass
