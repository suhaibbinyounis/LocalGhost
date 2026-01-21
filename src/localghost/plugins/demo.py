"""Built-in demo plugin for LocalGhost."""

from __future__ import annotations

import datetime
import platform
import sys
from typing import Any

from ..plugins.base import Endpoint, EndpointType, Plugin


class DemoPlugin(Plugin):
    """Built-in demo plugin showing LocalGhost capabilities."""

    @property
    def name(self) -> str:
        return "demo"

    @property
    def version(self) -> str:
        return "1.0.0"

    @property
    def description(self) -> str:
        return "Built-in demo plugin for testing and documentation"

    def get_endpoints(self) -> list[Endpoint]:
        return [
            # Public endpoints (no auth required)
            Endpoint(
                path="/ping",
                handler=self.ping,
                endpoint_type=EndpointType.PUBLIC,
                method="GET",
                description="Simple ping endpoint",
            ),
            Endpoint(
                path="/echo",
                handler=self.echo,
                endpoint_type=EndpointType.PUBLIC,
                method="POST",
                description="Echo back the request body",
            ),
            Endpoint(
                path="/time",
                handler=self.get_time,
                endpoint_type=EndpointType.PUBLIC,
                method="GET",
                description="Get current server time",
            ),
            # Protected endpoints (requires authorization)
            Endpoint(
                path="/system-info",
                handler=self.system_info,
                endpoint_type=EndpointType.PROTECTED,
                method="GET",
                description="Get system information (protected)",
                permissions=["read:system"],
            ),
            Endpoint(
                path="/execute",
                handler=self.execute,
                endpoint_type=EndpointType.PROTECTED,
                method="POST",
                description="Execute a simple command (protected)",
                permissions=["execute"],
            ),
        ]

    async def ping(self) -> dict[str, Any]:
        """Simple ping endpoint."""
        return {"pong": True, "timestamp": datetime.datetime.now().isoformat()}

    async def echo(self, body: dict[str, Any] = {}) -> dict[str, Any]:
        """Echo back the request body."""
        return {"echoed": body}

    async def get_time(self) -> dict[str, Any]:
        """Get current server time."""
        now = datetime.datetime.now()
        return {
            "iso": now.isoformat(),
            "unix": now.timestamp(),
            "formatted": now.strftime("%Y-%m-%d %H:%M:%S"),
        }

    async def system_info(self) -> dict[str, Any]:
        """Get system information (protected endpoint)."""
        return {
            "platform": platform.system(),
            "platform_release": platform.release(),
            "platform_version": platform.version(),
            "architecture": platform.machine(),
            "python_version": sys.version,
            "hostname": platform.node(),
        }

    async def execute(self, command: str = "echo hello") -> dict[str, Any]:
        """Execute a simple command (protected endpoint)."""
        import asyncio
        
        # Only allow safe commands for demo
        allowed_commands = ["echo", "date", "whoami", "pwd", "hostname"]
        cmd_name = command.split()[0] if command else ""
        
        if cmd_name not in allowed_commands:
            return {
                "error": f"Command '{cmd_name}' not allowed. Allowed: {allowed_commands}",
                "status": "denied",
            }
        
        proc = await asyncio.create_subprocess_shell(
            command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await proc.communicate()
        
        return {
            "command": command,
            "stdout": stdout.decode().strip(),
            "stderr": stderr.decode().strip(),
            "returncode": proc.returncode,
        }


# Singleton instance
demo_plugin = DemoPlugin()
