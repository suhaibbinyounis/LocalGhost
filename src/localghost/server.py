"""FastAPI server with HTTP and WebSocket transports."""

from __future__ import annotations

import asyncio
import logging
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, AsyncGenerator

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from . import __version__
from .auth.middleware import AuthMiddleware
from .auth.permissions import PermissionStore
from .auth.tokens import TokenManager
from .config import Settings, get_settings
from .consent.handler import ConsentHandler
from .plugins.registry import PluginRegistry

logger = logging.getLogger(__name__)

# Global state
_token_manager: TokenManager | None = None
_permission_store: PermissionStore | None = None
_plugin_registry: PluginRegistry | None = None
_consent_handler: ConsentHandler | None = None


def _load_or_create_secret(settings: Settings) -> bytes:
    """Load secret key from storage or create new one."""
    secret_path = settings.data_dir / ".secret"
    if secret_path.exists():
        return secret_path.read_bytes()
    else:
        secret = TokenManager.generate_secret()
        settings.ensure_dirs()
        secret_path.write_bytes(secret)
        secret_path.chmod(0o600)  # Restrict permissions
        return secret


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan handler."""
    global _token_manager, _permission_store, _plugin_registry, _consent_handler

    settings = get_settings()
    settings.ensure_dirs()

    # Initialize token manager with persistent secret
    secret = _load_or_create_secret(settings)
    _token_manager = TokenManager(secret)

    # Initialize permission store
    _permission_store = PermissionStore(settings.db_path)
    await _permission_store.initialize()

    # Initialize plugin registry
    _plugin_registry = PluginRegistry()

    # Load built-in demo plugin
    from .plugins.demo import demo_plugin
    await _plugin_registry.register(demo_plugin)

    # Initialize consent handler
    _consent_handler = ConsentHandler(settings, _token_manager, _permission_store)

    logger.info(f"LocalGhost v{__version__} starting on {settings.host}:{settings.port}")

    yield

    # Cleanup
    await _permission_store.close()
    logger.info("LocalGhost shutdown complete")


def create_app() -> FastAPI:
    """Create FastAPI application."""
    settings = get_settings()

    app = FastAPI(
        title=settings.app_name,
        version=__version__,
        description="Cross-platform local authorization service",
        lifespan=lifespan,
    )

    # CORS for local development
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Add routes
    @app.get("/health", tags=["public"])
    async def health() -> dict[str, Any]:
        """Health check endpoint."""
        return {
            "status": "healthy",
            "version": __version__,
            "service": settings.app_name,
        }

    @app.get("/capabilities", tags=["public"])
    async def capabilities() -> dict[str, Any]:
        """List all registered capabilities."""
        if _plugin_registry:
            return {
                "version": __version__,
                "plugins": _plugin_registry.get_capabilities(),
            }
        return {"version": __version__, "plugins": {}}

    @app.get("/permissions", tags=["protected"])
    async def list_permissions() -> dict[str, Any]:
        """List all granted permissions (admin endpoint)."""
        if _permission_store:
            grants = await _permission_store.list_all_grants()
            return {"permissions": grants}
        return {"permissions": []}

    # WebSocket endpoint for real-time communication
    @app.websocket("/ws")
    async def websocket_endpoint(websocket: WebSocket) -> None:
        """WebSocket endpoint for real-time communication."""
        await websocket.accept()

        # Get client identification
        client_id = websocket.headers.get("X-Client-ID", "unknown")

        try:
            while True:
                data = await websocket.receive_json()
                # Echo back with acknowledgment
                await websocket.send_json({
                    "type": "ack",
                    "client_id": client_id,
                    "received": data,
                })
        except WebSocketDisconnect:
            logger.debug(f"WebSocket client {client_id} disconnected")

    # Demo plugin routes (registered dynamically but defined here for clarity)
    @app.get("/demo/ping", tags=["demo"])
    async def demo_ping() -> dict[str, Any]:
        """Simple ping endpoint."""
        import datetime
        return {"pong": True, "timestamp": datetime.datetime.now().isoformat()}

    @app.post("/demo/echo", tags=["demo"])
    async def demo_echo(body: dict[str, Any] = {}) -> dict[str, Any]:
        """Echo back the request body."""
        return {"echoed": body}

    @app.get("/demo/time", tags=["demo"])
    async def demo_time() -> dict[str, Any]:
        """Get current server time."""
        import datetime
        now = datetime.datetime.now()
        return {
            "iso": now.isoformat(),
            "unix": now.timestamp(),
            "formatted": now.strftime("%Y-%m-%d %H:%M:%S"),
        }

    @app.get("/demo/system-info", tags=["demo"])
    async def demo_system_info() -> dict[str, Any]:
        """Get system information (protected endpoint)."""
        import platform
        import sys
        return {
            "platform": platform.system(),
            "platform_release": platform.release(),
            "architecture": platform.machine(),
            "python_version": sys.version,
            "hostname": platform.node(),
        }

    @app.post("/demo/execute", tags=["demo"])
    async def demo_execute(command: str = "echo hello") -> dict[str, Any]:
        """Execute a simple command (protected endpoint)."""
        import asyncio
        
        allowed_commands = ["echo", "date", "whoami", "pwd", "hostname"]
        cmd_name = command.split()[0] if command else ""
        
        if cmd_name not in allowed_commands:
            return {"error": f"Command '{cmd_name}' not allowed", "status": "denied"}
        
        proc = await asyncio.create_subprocess_shell(
            command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await proc.communicate()
        
        return {
            "command": command,
            "stdout": stdout.decode().strip(),
            "stderr": stderr.decode().strip(),
            "returncode": proc.returncode,
        }

    # Serve demo.html at /demo
    @app.get("/demo", tags=["demo"], include_in_schema=False)
    async def serve_demo():
        """Serve the demo HTML page."""
        from fastapi.responses import HTMLResponse
        from pathlib import Path
        import importlib.resources
        
        # Try package static folder first (works after pip install)
        try:
            # Python 3.9+ way
            static_dir = Path(__file__).parent / "static"
            demo_path = static_dir / "demo.html"
            if demo_path.exists():
                return HTMLResponse(content=demo_path.read_text(), status_code=200)
        except Exception:
            pass
        
        # Fallback to examples directory (for development)
        demo_paths = [
            Path(__file__).parent.parent.parent / "examples" / "demo.html",
            Path.cwd() / "examples" / "demo.html",
        ]
        
        for demo_path in demo_paths:
            if demo_path.exists():
                return HTMLResponse(content=demo_path.read_text(), status_code=200)
        
        return HTMLResponse(
            content="<h1>Demo page not found</h1><p>Please reinstall: pip install -e .</p>",
            status_code=404
        )

    return app


def get_app() -> FastAPI:
    """Get configured FastAPI app with middleware."""
    app = create_app()

    # Add auth middleware (after app creation for access to state)
    # This will be added during lifespan when components are initialized

    return app


def run_server(
    host: str = "127.0.0.1",
    port: int = 51473,
    enable_tray: bool = True,
) -> None:
    """Run the LocalGhost server."""
    import socket
    import threading

    import uvicorn

    def is_port_available(h: str, p: int) -> bool:
        """Check if a port is available."""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind((h, p))
                return True
        except OSError:
            return False

    def find_available_port(h: str, start_port: int) -> int:
        """Find an available port starting from start_port."""
        for p in range(start_port, start_port + 100):
            if is_port_available(h, p):
                return p
        raise RuntimeError("No available ports found")

    def check_if_running(h: str, p: int) -> bool:
        """Check if LocalGhost is already running on this port."""
        try:
            import httpx
            response = httpx.get(f"http://{h}:{p}/health", timeout=2)
            return response.status_code == 200 and "LocalGhost" in response.text
        except Exception:
            return False

    # Check if already running on default port
    if check_if_running(host, port):
        logger.info(f"LocalGhost is already running on {host}:{port}")
        print(f"\n✅ LocalGhost is already running at http://{host}:{port}")
        print(f"   Open http://{host}:{port}/demo in your browser")
        print(f"   Use 'localghost stop' to stop the service\n")
        return

    # Check if port is in use by something else
    if not is_port_available(host, port):
        logger.warning(f"Port {port} in use, finding alternative...")
        old_port = port
        port = find_available_port(host, port + 1)
        print(f"\n⚠️  Port {old_port} was in use, using port {port} instead\n")

    # Save running port to file for discovery
    settings = get_settings()
    port_file = settings.data_dir / ".port"
    try:
        settings.ensure_dirs()
        port_file.write_text(str(port))
    except Exception as e:
        logger.warning(f"Could not save port file: {e}")

    app = get_app()

    # Start system tray in background thread if enabled
    tray_thread = None
    if enable_tray:
        try:
            from .tray import run_tray

            def tray_runner() -> None:
                run_tray(host, port)

            tray_thread = threading.Thread(target=tray_runner, daemon=True)
            tray_thread.start()
        except ImportError as e:
            logger.warning(f"System tray not available: {e}")

    print(f"\n👻 LocalGhost running at http://{host}:{port}")
    print(f"   Demo page: http://{host}:{port}/demo")
    print(f"   Press Ctrl+C to stop\n")

    # Run uvicorn
    try:
        config = uvicorn.Config(
            app,
            host=host,
            port=port,
            log_level="info",
            access_log=True,
        )
        server = uvicorn.Server(config)
        server.run()
    finally:
        # Cleanup port file on exit
        try:
            if port_file.exists():
                port_file.unlink()
        except Exception:
            pass


def find_running_instance() -> tuple[str, int] | None:
    """Find a running LocalGhost instance on common ports."""
    import httpx
    
    # Check saved port file first
    try:
        from .config import get_settings
        settings = get_settings()
        port_file = settings.data_dir / ".port"
        if port_file.exists():
            saved_port = int(port_file.read_text().strip())
            try:
                response = httpx.get(f"http://127.0.0.1:{saved_port}/health", timeout=2)
                if response.status_code == 200:
                    return ("127.0.0.1", saved_port)
            except Exception:
                pass
    except Exception:
        pass
    
    # Check common ports
    common_ports = [51473, 8473, 51474, 51475]
    for p in common_ports:
        try:
            response = httpx.get(f"http://127.0.0.1:{p}/health", timeout=1)
            if response.status_code == 200 and "LocalGhost" in response.text:
                return ("127.0.0.1", p)
        except Exception:
            continue
    
    return None
