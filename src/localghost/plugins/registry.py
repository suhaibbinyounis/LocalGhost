"""Plugin registry and management."""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter

from .base import Endpoint, EndpointType, Plugin

logger = logging.getLogger(__name__)


class PluginRegistry:
    """Manages plugin registration and endpoint routing."""

    def __init__(self) -> None:
        """Initialize registry."""
        self._plugins: dict[str, Plugin] = {}
        self._endpoints: dict[str, Endpoint] = {}
        self._public_router = APIRouter(prefix="/public", tags=["public"])
        self._protected_router = APIRouter(tags=["protected"])

    async def register(self, plugin: Plugin) -> None:
        """Register a plugin and its endpoints."""
        if plugin.name in self._plugins:
            logger.warning(f"Plugin {plugin.name} already registered, skipping")
            return

        await plugin.on_load()
        self._plugins[plugin.name] = plugin

        for endpoint in plugin.get_endpoints():
            full_path = f"/{plugin.name}{endpoint.path}"
            self._endpoints[full_path] = endpoint

            if endpoint.endpoint_type == EndpointType.PUBLIC:
                router = self._public_router
            else:
                router = self._protected_router

            router.add_api_route(
                full_path,
                endpoint.handler,
                methods=[endpoint.method],
                description=endpoint.description,
                tags=[plugin.name],
            )

        logger.info(
            f"Registered plugin '{plugin.name}' v{plugin.version} "
            f"with {len(plugin.get_endpoints())} endpoints"
        )

    async def unregister(self, plugin_name: str) -> None:
        """Unregister a plugin."""
        if plugin_name not in self._plugins:
            return

        plugin = self._plugins[plugin_name]
        await plugin.on_unload()

        # Remove endpoints
        for endpoint in plugin.get_endpoints():
            full_path = f"/{plugin_name}{endpoint.path}"
            self._endpoints.pop(full_path, None)

        del self._plugins[plugin_name]
        logger.info(f"Unregistered plugin '{plugin_name}'")

    def get_capabilities(self) -> dict[str, Any]:
        """Get all registered capabilities."""
        capabilities = {}
        for name, plugin in self._plugins.items():
            endpoints = []
            for endpoint in plugin.get_endpoints():
                endpoints.append({
                    "path": f"/{name}{endpoint.path}",
                    "method": endpoint.method,
                    "type": endpoint.endpoint_type.value,
                    "description": endpoint.description,
                })
            capabilities[name] = {
                "version": plugin.version,
                "description": plugin.description,
                "endpoints": endpoints,
            }
        return capabilities

    def get_endpoint(self, path: str) -> Endpoint | None:
        """Get endpoint by path."""
        return self._endpoints.get(path)

    def is_public(self, path: str) -> bool:
        """Check if a path is public."""
        endpoint = self.get_endpoint(path)
        if endpoint:
            return endpoint.endpoint_type == EndpointType.PUBLIC
        return path.startswith("/public/")

    @property
    def public_router(self) -> APIRouter:
        """Get public endpoint router."""
        return self._public_router

    @property
    def protected_router(self) -> APIRouter:
        """Get protected endpoint router."""
        return self._protected_router

    @property
    def plugins(self) -> dict[str, Plugin]:
        """Get all registered plugins."""
        return self._plugins.copy()
