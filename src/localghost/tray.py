"""System tray integration using pystray."""

from __future__ import annotations

import io
import logging
import os
import sys
import webbrowser
from typing import Any, Callable

logger = logging.getLogger(__name__)


def _create_icon_image() -> Any:
    """Create a simple icon image for the tray."""
    from PIL import Image, ImageDraw

    # Create a simple ghost-like icon
    size = 64
    image = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)

    # Draw a ghost shape (white with slight transparency)
    ghost_color = (255, 255, 255, 230)

    # Body (rounded top)
    draw.ellipse([8, 4, 56, 44], fill=ghost_color)
    draw.rectangle([8, 24, 56, 52], fill=ghost_color)

    # Wavy bottom
    for i in range(3):
        x = 8 + (i * 16)
        draw.ellipse([x, 44, x + 16, 60], fill=ghost_color)

    # Eyes
    eye_color = (50, 50, 50, 255)
    draw.ellipse([18, 18, 28, 30], fill=eye_color)
    draw.ellipse([36, 18, 46, 30], fill=eye_color)

    return image


def run_tray(host: str = "127.0.0.1", port: int = 8473) -> None:
    """Run the system tray icon."""
    try:
        import pystray
        from pystray import MenuItem as Item
    except ImportError:
        logger.error("pystray not installed. System tray disabled.")
        return

    from . import __version__
    from .config import get_settings

    settings = get_settings()

    def open_dashboard(icon: Any, item: Any) -> None:
        """Open web dashboard."""
        webbrowser.open(f"http://{host}:{port}/docs")

    def open_logs(icon: Any, item: Any) -> None:
        """Open log file."""
        log_path = settings.log_path
        if sys.platform == "darwin":
            os.system(f'open "{log_path}"')
        elif sys.platform == "win32":
            os.startfile(str(log_path))  # type: ignore
        else:
            os.system(f'xdg-open "{log_path}"')

    def show_status(icon: Any, item: Any) -> None:
        """Show status notification."""
        icon.notify(
            f"LocalGhost v{__version__}\nRunning on {host}:{port}",
            "LocalGhost Status",
        )

    def quit_app(icon: Any, item: Any) -> None:
        """Quit the application."""
        icon.stop()
        # Signal the main server to stop
        os._exit(0)

    # Create menu
    menu = pystray.Menu(
        Item(f"LocalGhost v{__version__}", lambda: None, enabled=False),
        Item("Status", show_status),
        pystray.Menu.SEPARATOR,
        Item("Open Dashboard", open_dashboard),
        Item("View Logs", open_logs),
        pystray.Menu.SEPARATOR,
        Item("Quit", quit_app),
    )

    # Create icon
    icon = pystray.Icon(
        name="localghost",
        icon=_create_icon_image(),
        title=f"{settings.app_name} - Running",
        menu=menu,
    )

    logger.info("System tray icon started")
    icon.run()
