"""Post-install hook to auto-register LocalGhost service."""

from __future__ import annotations

import atexit
import sys


def _register_service() -> None:
    """Register LocalGhost as an auto-start service after pip install."""
    try:
        from localghost.service import install_service
        from localghost.config import get_settings
        
        settings = get_settings()
        settings.ensure_dirs()
        
        print(f"\n{'='*50}")
        print(f"  {settings.app_name} - Auto-registering service...")
        print(f"{'='*50}")
        
        install_service()
        
        print(f"✓ Service registered for auto-start")
        print(f"  Run 'localghost run' to start now, or reboot.")
        print(f"  Use 'localghost uninstall' to remove auto-start.")
        print(f"{'='*50}\n")
    except Exception as e:
        # Don't fail installation if service registration fails
        print(f"\n[LocalGhost] Note: Could not auto-register service: {e}")
        print("[LocalGhost] You can manually run: localghost install\n")


def register() -> None:
    """Called by setuptools after install."""
    # Use atexit to run after pip finishes (cleaner output)
    atexit.register(_register_service)


# Auto-run when this module is imported during install
if "pip" in sys.modules or "setuptools" in sys.modules:
    register()
