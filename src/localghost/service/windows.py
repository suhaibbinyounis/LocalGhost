"""Windows service integration."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path
from typing import Any

from ..config import get_settings


def _get_python_path() -> str:
    """Get path to Python executable."""
    return sys.executable


def _get_pythonw_path() -> str:
    """Get path to pythonw (no console window)."""
    python_path = Path(sys.executable)
    pythonw = python_path.parent / "pythonw.exe"
    if pythonw.exists():
        return str(pythonw)
    return str(python_path)


def install() -> None:
    """Install Windows service using Task Scheduler (no admin required)."""
    settings = get_settings()
    settings.ensure_dirs()

    python_path = _get_pythonw_path()

    # Use Task Scheduler for user-level service (no admin required)
    # This runs at logon
    task_xml = f'''<?xml version="1.0" encoding="UTF-16"?>
<Task version="1.2" xmlns="http://schemas.microsoft.com/windows/2004/02/mit/task">
  <RegistrationInfo>
    <Description>{settings.service_description}</Description>
  </RegistrationInfo>
  <Triggers>
    <LogonTrigger>
      <Enabled>true</Enabled>
    </LogonTrigger>
  </Triggers>
  <Principals>
    <Principal>
      <LogonType>InteractiveToken</LogonType>
      <RunLevel>LeastPrivilege</RunLevel>
    </Principal>
  </Principals>
  <Settings>
    <MultipleInstancesPolicy>IgnoreNew</MultipleInstancesPolicy>
    <DisallowStartIfOnBatteries>false</DisallowStartIfOnBatteries>
    <StopIfGoingOnBatteries>false</StopIfGoingOnBatteries>
    <AllowHardTerminate>true</AllowHardTerminate>
    <StartWhenAvailable>true</StartWhenAvailable>
    <RunOnlyIfNetworkAvailable>false</RunOnlyIfNetworkAvailable>
    <AllowStartOnDemand>true</AllowStartOnDemand>
    <Enabled>true</Enabled>
    <Hidden>false</Hidden>
    <RunOnlyIfIdle>false</RunOnlyIfIdle>
    <WakeToRun>false</WakeToRun>
    <ExecutionTimeLimit>PT0S</ExecutionTimeLimit>
    <Priority>7</Priority>
    <RestartOnFailure>
      <Interval>PT1M</Interval>
      <Count>3</Count>
    </RestartOnFailure>
  </Settings>
  <Actions>
    <Exec>
      <Command>{python_path}</Command>
      <Arguments>-m localghost run --no-tray</Arguments>
    </Exec>
  </Actions>
</Task>'''

    # Write task XML to temp file
    task_file = settings.data_dir / "localghost_task.xml"
    task_file.write_text(task_xml, encoding="utf-16")

    # Create scheduled task
    subprocess.run(
        ["schtasks", "/create", "/tn", settings.service_name, "/xml", str(task_file), "/f"],
        check=True,
    )

    task_file.unlink()


def uninstall() -> None:
    """Uninstall Windows service."""
    settings = get_settings()

    # Stop first
    try:
        stop()
    except Exception:
        pass

    # Delete scheduled task
    subprocess.run(
        ["schtasks", "/delete", "/tn", settings.service_name, "/f"],
        check=False,
    )


def start() -> None:
    """Start the Windows service."""
    settings = get_settings()
    subprocess.run(
        ["schtasks", "/run", "/tn", settings.service_name],
        check=True,
    )


def stop() -> None:
    """Stop the Windows service."""
    settings = get_settings()
    subprocess.run(
        ["schtasks", "/end", "/tn", settings.service_name],
        check=True,
    )


def get_status() -> dict[str, Any]:
    """Get service status."""
    settings = get_settings()
    try:
        result = subprocess.run(
            ["schtasks", "/query", "/tn", settings.service_name, "/fo", "list"],
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            output = result.stdout
            if "Running" in output:
                return {"status": "running"}
            elif "Ready" in output:
                return {"status": "stopped"}
            else:
                return {"status": "stopped"}
        return {"status": "not installed"}
    except Exception:
        return {"status": "unknown"}
