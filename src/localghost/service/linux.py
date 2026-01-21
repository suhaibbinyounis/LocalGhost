"""Linux systemd service integration."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path
from typing import Any

from ..config import get_settings


def _get_service_path() -> Path:
    """Get path to systemd user service file."""
    return Path.home() / ".config" / "systemd" / "user" / "localghost.service"


def _get_python_path() -> str:
    """Get path to Python executable."""
    return sys.executable


def _generate_service_file() -> str:
    """Generate systemd service unit content."""
    settings = get_settings()
    python_path = _get_python_path()

    return f'''[Unit]
Description={settings.service_description}
After=network.target

[Service]
Type=simple
ExecStart={python_path} -m localghost run --no-tray
Restart=always
RestartSec=5
Environment=LOCALGHOST_HOST={settings.host}
Environment=LOCALGHOST_PORT={settings.port}

[Install]
WantedBy=default.target
'''


def install() -> None:
    """Install systemd user service."""
    settings = get_settings()
    settings.ensure_dirs()

    service_path = _get_service_path()
    service_path.parent.mkdir(parents=True, exist_ok=True)

    # Write service file
    service_content = _generate_service_file()
    service_path.write_text(service_content)

    # Reload systemd and enable service
    subprocess.run(["systemctl", "--user", "daemon-reload"], check=True)
    subprocess.run(["systemctl", "--user", "enable", "localghost.service"], check=True)


def uninstall() -> None:
    """Uninstall systemd user service."""
    service_path = _get_service_path()

    # Stop and disable first
    subprocess.run(
        ["systemctl", "--user", "stop", "localghost.service"],
        check=False,
    )
    subprocess.run(
        ["systemctl", "--user", "disable", "localghost.service"],
        check=False,
    )

    if service_path.exists():
        service_path.unlink()

    subprocess.run(["systemctl", "--user", "daemon-reload"], check=True)


def start() -> None:
    """Start the systemd service."""
    subprocess.run(["systemctl", "--user", "start", "localghost.service"], check=True)


def stop() -> None:
    """Stop the systemd service."""
    subprocess.run(["systemctl", "--user", "stop", "localghost.service"], check=True)


def get_status() -> dict[str, Any]:
    """Get service status."""
    try:
        result = subprocess.run(
            ["systemctl", "--user", "is-active", "localghost.service"],
            capture_output=True,
            text=True,
        )
        status = result.stdout.strip()

        pid = None
        if status == "active":
            # Get PID
            pid_result = subprocess.run(
                ["systemctl", "--user", "show", "--property=MainPID", "localghost.service"],
                capture_output=True,
                text=True,
            )
            if pid_result.returncode == 0:
                pid = pid_result.stdout.strip().split("=")[1]
                if pid == "0":
                    pid = None

        return {"status": status, "pid": pid}
    except Exception:
        return {"status": "unknown"}
