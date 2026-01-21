"""macOS launchd service integration."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path
from typing import Any

from ..config import get_settings


def _get_plist_path() -> Path:
    """Get path to launchd plist file."""
    return Path.home() / "Library" / "LaunchAgents" / "com.localghost.service.plist"


def _get_python_path() -> str:
    """Get path to Python executable."""
    return sys.executable


def _generate_plist() -> str:
    """Generate launchd plist content."""
    settings = get_settings()
    python_path = _get_python_path()

    return f'''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.localghost.service</string>
    <key>ProgramArguments</key>
    <array>
        <string>{python_path}</string>
        <string>-m</string>
        <string>localghost</string>
        <string>run</string>
        <string>--no-tray</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>{settings.log_dir}/stdout.log</string>
    <key>StandardErrorPath</key>
    <string>{settings.log_dir}/stderr.log</string>
    <key>EnvironmentVariables</key>
    <dict>
        <key>LOCALGHOST_HOST</key>
        <string>{settings.host}</string>
        <key>LOCALGHOST_PORT</key>
        <string>{settings.port}</string>
    </dict>
</dict>
</plist>'''


def install() -> None:
    """Install launchd service."""
    settings = get_settings()
    settings.ensure_dirs()

    plist_path = _get_plist_path()
    plist_path.parent.mkdir(parents=True, exist_ok=True)

    # Write plist file
    plist_content = _generate_plist()
    plist_path.write_text(plist_content)

    # Load the service
    subprocess.run(["launchctl", "load", str(plist_path)], check=True)


def uninstall() -> None:
    """Uninstall launchd service."""
    plist_path = _get_plist_path()

    if plist_path.exists():
        # Unload the service first
        subprocess.run(
            ["launchctl", "unload", str(plist_path)],
            check=False,  # May fail if not loaded
        )
        plist_path.unlink()


def start() -> None:
    """Start the launchd service."""
    subprocess.run(["launchctl", "start", "com.localghost.service"], check=True)


def stop() -> None:
    """Stop the launchd service."""
    subprocess.run(["launchctl", "stop", "com.localghost.service"], check=True)


def get_status() -> dict[str, Any]:
    """Get service status."""
    try:
        result = subprocess.run(
            ["launchctl", "list", "com.localghost.service"],
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            # Parse output for PID
            lines = result.stdout.strip().split("\n")
            if len(lines) >= 2:
                parts = lines[1].split()
                pid = parts[0] if parts[0] != "-" else None
                return {"status": "running", "pid": pid}
        return {"status": "stopped"}
    except Exception:
        return {"status": "unknown"}
