"""Example plugin demonstrating LocalGhost plugin interface."""

from __future__ import annotations

from localghost.plugins.base import Endpoint, EndpointType, Plugin


class HelloPlugin(Plugin):
    """Example plugin that provides greeting endpoints."""

    @property
    def name(self) -> str:
        return "hello"

    @property
    def version(self) -> str:
        return "1.0.0"

    @property
    def description(self) -> str:
        return "Example greeting plugin"

    def get_endpoints(self) -> list[Endpoint]:
        return [
            Endpoint(
                path="/greet",
                handler=self.greet,
                endpoint_type=EndpointType.PUBLIC,
                method="GET",
                description="Returns a friendly greeting",
            ),
            Endpoint(
                path="/secret",
                handler=self.secret,
                endpoint_type=EndpointType.PROTECTED,
                method="GET",
                description="Returns a secret message (requires authorization)",
                permissions=["read"],
            ),
        ]

    async def greet(self, name: str = "World") -> dict:
        """Public greeting endpoint."""
        return {"message": f"Hello, {name}!"}

    async def secret(self) -> dict:
        """Protected endpoint requiring authorization."""
        return {"secret": "The answer is 42"}


# Plugin entry point - LocalGhost will load this
plugin = HelloPlugin()
