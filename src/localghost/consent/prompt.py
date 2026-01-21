"""Native consent prompts."""

from __future__ import annotations

import asyncio
import logging
import platform
import subprocess
import sys
from dataclasses import dataclass
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class ConsentResult(str, Enum):
    """Result of consent prompt."""

    DENIED = "denied"
    ALLOW_ONCE = "allow_once"
    ALLOW_SESSION = "allow_session"
    ALLOW_TIMED = "allow_timed"
    ALLOW_PERMANENT = "allow_permanent"


@dataclass
class ConsentPrompt:
    """Consent prompt data."""

    client_id: str
    client_name: str
    endpoint: str
    permissions: list[str]
    timeout_seconds: int = 60


async def show_consent_dialog(prompt: ConsentPrompt) -> ConsentResult:
    """Show native consent dialog.

    Uses platform-specific mechanisms:
    - macOS: osascript (AppleScript)
    - Windows: PowerShell/WPF or tkinter
    - Linux: zenity, kdialog, or tkinter fallback
    """
    system = platform.system()

    try:
        if system == "Darwin":
            return await _show_macos_dialog(prompt)
        elif system == "Windows":
            return await _show_windows_dialog(prompt)
        else:
            return await _show_linux_dialog(prompt)
    except Exception as e:
        logger.warning(f"Native dialog failed, using tkinter fallback: {e}")
        return await _show_tkinter_dialog(prompt)


async def _show_macos_dialog(prompt: ConsentPrompt) -> ConsentResult:
    """Show macOS native dialog using osascript."""
    script = f'''
    set theDialog to display dialog "The application '{prompt.client_name}' wants to access:\\n\\n{prompt.endpoint}\\n\\nPermissions: {', '.join(prompt.permissions)}" ¬
        buttons {{"Deny", "Allow Once", "Allow Always"}} ¬
        default button "Deny" ¬
        with title "LocalGhost Authorization" ¬
        giving up after {prompt.timeout_seconds}
    
    set theButton to button returned of theDialog
    if gave up of theDialog then
        return "timeout"
    end if
    return theButton
    '''

    proc = await asyncio.create_subprocess_exec(
        "osascript", "-e", script,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, _ = await proc.communicate()
    result = stdout.decode().strip()

    if result == "Allow Always":
        return ConsentResult.ALLOW_PERMANENT
    elif result == "Allow Once":
        return ConsentResult.ALLOW_ONCE
    else:
        return ConsentResult.DENIED


async def _show_windows_dialog(prompt: ConsentPrompt) -> ConsentResult:
    """Show Windows dialog using PowerShell."""
    ps_script = f'''
    Add-Type -AssemblyName System.Windows.Forms
    $result = [System.Windows.Forms.MessageBox]::Show(
        "The application '{prompt.client_name}' wants to access:`n`n{prompt.endpoint}`n`nPermissions: {', '.join(prompt.permissions)}`n`nAllow this access?",
        "LocalGhost Authorization",
        [System.Windows.Forms.MessageBoxButtons]::YesNoCancel,
        [System.Windows.Forms.MessageBoxIcon]::Question
    )
    Write-Output $result
    '''

    proc = await asyncio.create_subprocess_exec(
        "powershell", "-Command", ps_script,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, _ = await proc.communicate()
    result = stdout.decode().strip()

    if result == "Yes":
        return ConsentResult.ALLOW_PERMANENT
    elif result == "No":
        return ConsentResult.ALLOW_ONCE
    else:
        return ConsentResult.DENIED


async def _show_linux_dialog(prompt: ConsentPrompt) -> ConsentResult:
    """Show Linux dialog using zenity or kdialog."""
    message = (
        f"The application '{prompt.client_name}' wants to access:\n\n"
        f"{prompt.endpoint}\n\n"
        f"Permissions: {', '.join(prompt.permissions)}"
    )

    # Try zenity first
    try:
        proc = await asyncio.create_subprocess_exec(
            "zenity", "--question",
            "--title=LocalGhost Authorization",
            f"--text={message}",
            "--ok-label=Allow",
            "--cancel-label=Deny",
            f"--timeout={prompt.timeout_seconds}",
        )
        await proc.communicate()
        return ConsentResult.ALLOW_PERMANENT if proc.returncode == 0 else ConsentResult.DENIED
    except FileNotFoundError:
        pass

    # Try kdialog
    try:
        proc = await asyncio.create_subprocess_exec(
            "kdialog", "--yesno", message,
            "--title=LocalGhost Authorization",
        )
        await proc.communicate()
        return ConsentResult.ALLOW_PERMANENT if proc.returncode == 0 else ConsentResult.DENIED
    except FileNotFoundError:
        pass

    # Fall back to tkinter
    return await _show_tkinter_dialog(prompt)


async def _show_tkinter_dialog(prompt: ConsentPrompt) -> ConsentResult:
    """Show cross-platform dialog using tkinter."""

    def _show() -> str:
        import tkinter as tk
        from tkinter import messagebox

        root = tk.Tk()
        root.withdraw()
        root.attributes("-topmost", True)

        message = (
            f"The application '{prompt.client_name}' wants to access:\n\n"
            f"{prompt.endpoint}\n\n"
            f"Permissions: {', '.join(prompt.permissions)}\n\n"
            "Allow this access?"
        )

        result = messagebox.askyesnocancel(
            "LocalGhost Authorization",
            message,
        )

        root.destroy()

        if result is True:
            return "yes"
        elif result is False:
            return "once"
        else:
            return "no"

    # Run tkinter in thread pool to avoid blocking
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(None, _show)

    if result == "yes":
        return ConsentResult.ALLOW_PERMANENT
    elif result == "once":
        return ConsentResult.ALLOW_ONCE
    else:
        return ConsentResult.DENIED
