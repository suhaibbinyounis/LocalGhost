# LocalGhost

Cross-platform local authorization service with consent-driven security. LocalGhost runs as a background service exposing local HTTP/WebSocket endpoints, with native system tray integration and user consent prompts.

## Features

- 🔐 **Consent-Driven Security** - Native OS dialogs for authorization approval
- 🖥️ **Cross-Platform** - Windows (Task Scheduler), macOS (launchd), Linux (systemd)
- 🔌 **Plugin System** - Extensible endpoint registration (public/protected)
- 🌐 **HTTP + WebSocket** - FastAPI-powered local server
- 🔑 **Token-Based Auth** - Scoped, encrypted authorization tokens
- 📊 **System Tray** - Status monitoring and permission management
- ⚙️ **pyproject.toml Config** - All defaults configurable

## Installation

```bash
pip install git+https://github.com/suhaibbinyounis/LocalGhost.git
```

**Auto-start**: The service automatically registers for startup on first use. No manual `install` command needed.

To disable auto-start:
```bash
localghost uninstall
# Or set environment variable before install:
LOCALGHOST_NO_AUTOSTART=1 pip install git+...
```

For development:

```bash
git clone https://github.com/suhaibbinyounis/LocalGhost.git
cd LocalGhost
pip install -e ".[dev]"
```

## Quick Start

### Run the Server

```bash
# Run with system tray
localghost run

# Run without system tray
localghost run --no-tray

# Custom host/port
localghost run --host 127.0.0.1 --port 9000
```

### Install as System Service

```bash
# Install (auto-starts on boot)
localghost install

# Service management
localghost start
localghost stop
localghost status

# Remove
localghost uninstall
```

### Permission Management

```bash
# List all granted permissions
localghost permissions

# Revoke all permissions for a client
localghost revoke <client_id>
```

## API Endpoints

| Endpoint | Type | Description |
|----------|------|-------------|
| `/health` | Public | Health check |
| `/capabilities` | Public | List registered plugins |
| `/permissions` | Protected | List all grants (admin) |
| `/ws` | WebSocket | Real-time communication |

## Plugin Example

```python
from localghost.plugins.base import Endpoint, EndpointType, Plugin

class MyPlugin(Plugin):
    @property
    def name(self) -> str:
        return "myplugin"

    @property
    def version(self) -> str:
        return "1.0.0"

    def get_endpoints(self) -> list[Endpoint]:
        return [
            Endpoint(
                path="/hello",
                handler=self.hello,
                endpoint_type=EndpointType.PUBLIC,
            ),
            Endpoint(
                path="/secret",
                handler=self.secret,
                endpoint_type=EndpointType.PROTECTED,
            ),
        ]

    async def hello(self) -> dict:
        return {"message": "Hello!"}

    async def secret(self) -> dict:
        return {"secret": "42"}
```

## Client Example

```python
import httpx

with httpx.Client(base_url="http://127.0.0.1:8473") as client:
    # Public - no auth
    response = client.get("/health")
    print(response.json())

    # Protected - triggers consent prompt
    response = client.get(
        "/permissions",
        headers={"X-Process-Name": "my-app"}
    )
```

## Configuration

All defaults are in `pyproject.toml` under `[tool.localghost]`:

```toml
[tool.localghost]
app_name = "LocalGhost"
default_host = "127.0.0.1"
default_port = 8473
token_expiry_hours = 24
consent_timeout_seconds = 60
```

Override via environment variables:

```bash
LOCALGHOST_HOST=0.0.0.0 LOCALGHOST_PORT=9000 localghost run
```

## Security

- **Local-only** - Binds to `127.0.0.1` by default
- **Encrypted tokens** - Fernet symmetric encryption
- **Audit logging** - All grants/revokes logged to SQLite
- **Consent prompts** - Native OS dialogs (macOS AppleScript, Windows PowerShell, Linux zenity/kdialog)

## Development

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest tests/ -v

# Type checking
mypy src/localghost

# Linting
ruff check src/
```

## License

MIT
