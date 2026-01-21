"""Plugin system package."""

from .base import Endpoint, EndpointType, Plugin
from .registry import PluginRegistry

__all__ = ["Endpoint", "EndpointType", "Plugin", "PluginRegistry"]
