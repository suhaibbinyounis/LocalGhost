"""LocalGhost - Cross-platform local authorization service."""

from importlib.metadata import version, PackageNotFoundError

try:
    __version__ = version("localghost")
except PackageNotFoundError:
    __version__ = "0.0.0.dev"

__all__ = ["__version__"]


def _auto_register_service() -> None:
    """Auto-register service on first run after installation."""
    import os
    import sys
    
    # Skip if running tests or in non-interactive mode
    if "pytest" in sys.modules or not sys.stdout.isatty():
        return
    
    # Skip if explicitly disabled
    if os.environ.get("LOCALGHOST_NO_AUTOSTART"):
        return
    
    try:
        from .config import get_settings
        settings = get_settings()
        
        # Check if already registered (marker file exists)
        marker = settings.data_dir / ".registered"
        if marker.exists():
            return
        
        # Register the service
        settings.ensure_dirs()
        
        from .service import install_service, get_service_status
        
        status = get_service_status()
        if status.get("status") not in ("running", "active"):
            install_service()
            marker.touch()
            print(f"\n[{settings.app_name}] Auto-registered for startup. Use 'localghost uninstall' to disable.\n")
    except Exception:
        # Silently fail - don't break imports
        pass


# Auto-register on first import (after pip install)
_auto_register_service()
