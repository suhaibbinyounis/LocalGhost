"""Cross-platform daemon/service management."""

from __future__ import annotations

import logging
import platform
import sys
from typing import Any

logger = logging.getLogger(__name__)


def _get_platform_module() -> Any:
    """Get platform-specific service module."""
    system = platform.system()
    if system == "Windows":
        from . import windows
        return windows
    elif system == "Darwin":
        from . import macos
        return macos
    else:
        from . import linux
        return linux


def install_service() -> None:
    """Install LocalGhost as a system service."""
    module = _get_platform_module()
    module.install()
    logger.info("Service installed successfully")


def uninstall_service() -> None:
    """Uninstall LocalGhost system service."""
    module = _get_platform_module()
    module.uninstall()
    logger.info("Service uninstalled")


def start_service() -> None:
    """Start the LocalGhost service."""
    module = _get_platform_module()
    module.start()
    logger.info("Service started")


def stop_service() -> None:
    """Stop the LocalGhost service."""
    module = _get_platform_module()
    module.stop()
    logger.info("Service stopped")


def get_service_status() -> dict[str, Any]:
    """Get service status."""
    module = _get_platform_module()
    return module.get_status()


def run_as_service() -> None:
    """Run in service mode (blocking)."""
    from ..server import run_server
    from ..config import get_settings

    settings = get_settings()
    run_server(
        host=settings.host,
        port=settings.port,
        enable_tray=False,  # No tray in service mode
    )
