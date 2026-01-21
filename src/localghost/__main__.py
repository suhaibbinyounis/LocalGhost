"""CLI entry point for LocalGhost."""

from __future__ import annotations

import logging
import sys

import click

from . import __version__
from .config import get_settings


def setup_logging(verbose: bool = False) -> None:
    """Configure logging."""
    level = logging.DEBUG if verbose else logging.INFO
    settings = get_settings()
    settings.ensure_dirs()

    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(settings.log_path),
        ],
    )


@click.group()
@click.version_option(version=__version__, prog_name="localghost")
@click.option("-v", "--verbose", is_flag=True, help="Enable verbose output")
@click.pass_context
def cli(ctx: click.Context, verbose: bool) -> None:
    """LocalGhost - Cross-platform local authorization service."""
    ctx.ensure_object(dict)
    ctx.obj["verbose"] = verbose
    setup_logging(verbose)


@cli.command()
@click.option("--host", default=None, help="Host to bind to")
@click.option("--port", default=None, type=int, help="Port to bind to")
@click.option("--tray/--no-tray", default=True, help="Enable system tray icon")
@click.pass_context
def run(ctx: click.Context, host: str | None, port: int | None, tray: bool) -> None:
    """Run the LocalGhost server."""
    from .server import run_server

    settings = get_settings()
    run_server(
        host=host or settings.host,
        port=port or settings.port,
        enable_tray=tray,
    )


@cli.command()
@click.pass_context
def install(ctx: click.Context) -> None:
    """Install LocalGhost as a system service."""
    from .service import install_service

    install_service()
    click.echo("LocalGhost service installed successfully.")


@cli.command()
@click.pass_context
def uninstall(ctx: click.Context) -> None:
    """Uninstall LocalGhost system service."""
    from .service import uninstall_service

    uninstall_service()
    click.echo("LocalGhost service uninstalled.")


@cli.command()
@click.pass_context
def start(ctx: click.Context) -> None:
    """Start the LocalGhost service."""
    from .service import start_service

    start_service()
    click.echo("LocalGhost service started.")


@cli.command()
@click.pass_context
def stop(ctx: click.Context) -> None:
    """Stop the LocalGhost service."""
    from .service import stop_service

    stop_service()
    click.echo("LocalGhost service stopped.")


@cli.command()
@click.pass_context
def status(ctx: click.Context) -> None:
    """Show LocalGhost service status."""
    from .service import get_service_status

    status_info = get_service_status()
    click.echo(f"Status: {status_info['status']}")
    if status_info.get("pid"):
        click.echo(f"PID: {status_info['pid']}")


@cli.command()
@click.pass_context
def permissions(ctx: click.Context) -> None:
    """List all granted permissions."""
    import asyncio

    from .auth.permissions import PermissionStore

    async def list_permissions() -> None:
        settings = get_settings()
        store = PermissionStore(settings.db_path)
        await store.initialize()
        grants = await store.list_all_grants()
        if not grants:
            click.echo("No permissions granted.")
            return
        for grant in grants:
            click.echo(
                f"  {grant['client_id']} -> {grant['endpoint']} "
                f"[{grant['grant_type']}] expires: {grant['expires_at'] or 'never'}"
            )

    asyncio.run(list_permissions())


@cli.command()
@click.argument("client_id")
@click.pass_context
def revoke(ctx: click.Context, client_id: str) -> None:
    """Revoke all permissions for a client."""
    import asyncio

    from .auth.permissions import PermissionStore

    async def do_revoke() -> None:
        settings = get_settings()
        store = PermissionStore(settings.db_path)
        await store.initialize()
        await store.revoke_all_for_client(client_id)

    asyncio.run(do_revoke())
    click.echo(f"Revoked all permissions for {client_id}")


if __name__ == "__main__":
    cli()
