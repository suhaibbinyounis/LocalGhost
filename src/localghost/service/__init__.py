"""Service/daemon package."""

from .daemon import (
    get_service_status,
    install_service,
    start_service,
    stop_service,
    uninstall_service,
)

__all__ = [
    "get_service_status",
    "install_service",
    "start_service",
    "stop_service",
    "uninstall_service",
]
