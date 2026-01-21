# 👻 LocalGhost

**Cross-platform local authorization service** that runs silently in the background and lets programs expose secure local endpoints.

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

---

## 📋 Table of Contents

- [What is LocalGhost?](#-what-is-localghost)
- [Installation](#-installation)
- [Quick Start](#-quick-start)
- [Uninstallation](#-uninstallation)
- [How It Works](#-how-it-works)
- [Authentication](#-authentication)
- [API Reference](#-api-reference)
- [Examples](#-examples)
- [Troubleshooting](#-troubleshooting)
- [Recovery & Repair](#-recovery--repair)
- [Configuration](#-configuration)
- [Contributing](#contributing)

---

## 🤔 What is LocalGhost?

LocalGhost is a **background service** that:
- Runs on your computer (localhost only - never exposed to the internet)
- Lets programs communicate with each other securely
- Shows a popup when a new program wants access (you click "Allow" or "Deny")
- Remembers your choices so you don't get asked again
- Works on **Windows**, **macOS**, and **Linux**

**Think of it like:** A security guard for your local programs. When a new program wants to talk to LocalGhost, it asks you first.

---

## 📦 Installation

### The Easy Way (Recommended)

**Works on all platforms** (Windows, macOS, Linux):

```bash
pip install git+https://github.com/suhaibbinyounis/LocalGhost.git
```

That's it! LocalGhost will **automatically start** when you first use it.

---

### If Installation Fails

#### Error: "Could not build wheels"

Try adding `--no-build-isolation`:

```bash
pip install --no-build-isolation git+https://github.com/suhaibbinyounis/LocalGhost.git
```

#### Error: "externally-managed-environment" (Linux/macOS)

On newer Linux/macOS, you might see this error. Use one of these solutions:

**Option 1: Use `--break-system-packages`** (quick fix)
```bash
pip install --break-system-packages git+https://github.com/suhaibbinyounis/LocalGhost.git
```

**Option 2: Use pipx** (recommended for CLI tools)
```bash
pipx install git+https://github.com/suhaibbinyounis/LocalGhost.git
```

**Option 3: Use a virtual environment** (cleanest)
```bash
python3 -m venv ~/.localghost-venv
source ~/.localghost-venv/bin/activate  # On Windows: .localghost-venv\Scripts\activate
pip install git+https://github.com/suhaibbinyounis/LocalGhost.git
```

#### Error: "python not found"

Make sure Python 3.10+ is installed:
- **Windows**: Download from [python.org](https://www.python.org/downloads/)
- **macOS**: `brew install python` or download from python.org
- **Linux**: `sudo apt install python3 python3-pip` (Ubuntu/Debian)

---

### Platform-Specific Notes

#### 🪟 Windows
```bash
pip install git+https://github.com/suhaibbinyounis/LocalGhost.git
```
- Runs as a **Scheduled Task** (no admin required)
- System tray icon appears in the taskbar

#### 🍎 macOS
```bash
pip install git+https://github.com/suhaibbinyounis/LocalGhost.git
```
- Runs as a **LaunchAgent** (no admin required)
- Menu bar icon appears at the top

#### 🐧 Linux
```bash
pip install --break-system-packages git+https://github.com/suhaibbinyounis/LocalGhost.git
# OR
pipx install git+https://github.com/suhaibbinyounis/LocalGhost.git
```
- Runs as a **systemd user service**
- Works on Ubuntu, Fedora, Arch, etc.

---

### Disable Auto-Start

If you don't want LocalGhost to auto-start on boot:

```bash
# Set this BEFORE installing
LOCALGHOST_NO_AUTOSTART=1 pip install git+https://github.com/suhaibbinyounis/LocalGhost.git

# Or disable after installing
localghost uninstall
```

---

## 🚀 Quick Start

### 1. Start the server

```bash
localghost run
```

You'll see a 👻 ghost icon in your system tray/menu bar.

### 2. Open the demo page

Open your browser and go to:
```
http://127.0.0.1:51473/demo
```

This page lets you test all features and shows your team how to use the API.

### 3. Test an endpoint

```bash
# Using curl
curl http://127.0.0.1:51473/health

# Or in your browser
http://127.0.0.1:51473/health
```

---

## 🗑️ Uninstallation

### Remove Auto-Start Only

Keep LocalGhost installed but stop it from running at startup:

```bash
localghost uninstall
```

### Complete Removal

**Step 1: Remove auto-start**
```bash
localghost uninstall
```

**Step 2: Uninstall the package**
```bash
pip uninstall localghost
```

**Step 3: Remove data files (optional)**

| Platform | Data Location |
|----------|--------------|
| Windows | `%APPDATA%\LocalGhost\` |
| macOS | `~/Library/Application Support/LocalGhost/` |
| Linux | `~/.local/share/LocalGhost/` |

```bash
# macOS/Linux
rm -rf ~/.local/share/LocalGhost
rm -rf ~/Library/Application\ Support/LocalGhost

# Windows (PowerShell)
Remove-Item -Recurse "$env:APPDATA\LocalGhost"
```

---

## 🔧 How It Works

### Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      Your Computer                          │
│                                                             │
│  ┌──────────────┐     HTTP/WS      ┌──────────────────┐    │
│  │   Browser    │ ───────────────► │                  │    │
│  └──────────────┘                  │                  │    │
│                                    │   LocalGhost     │    │
│  ┌──────────────┐     HTTP/WS      │   (Port 51473)    │    │
│  │  Your App    │ ───────────────► │                  │    │
│  └──────────────┘                  │  127.0.0.1 only  │    │
│                                    │                  │    │
│  ┌──────────────┐     HTTP/WS      │                  │    │
│  │   Script     │ ───────────────► │                  │    │
│  └──────────────┘                  └──────────────────┘    │
│                                            │               │
│                                            ▼               │
│                                    ┌──────────────────┐    │
│                                    │   System Tray    │    │
│                                    │   (shows status) │    │
│                                    └──────────────────┘    │
└─────────────────────────────────────────────────────────────┘
```

### Key Concepts

| Concept | Description |
|---------|-------------|
| **Localhost Only** | Never accessible from other computers |
| **Public Endpoints** | Anyone can access (e.g., `/health`) |
| **Protected Endpoints** | Requires your approval first |
| **Tokens** | After you approve, the app gets a token for future access |
| **Plugins** | Extensions that add new endpoints |

### Workflow

1. **First Request**: App calls a protected endpoint
2. **Popup Appears**: "Allow [App Name] to access [Endpoint]?"
3. **You Choose**: Allow Once, Allow Always, or Deny
4. **Token Issued**: If allowed, app gets a token
5. **Future Requests**: Token is used automatically (no popup)

---

## 🔐 Authentication

### How Auth Works

LocalGhost uses **consent-based authentication**:

1. No passwords or API keys needed
2. When a new app tries to access a protected endpoint, you see a popup
3. You decide: Allow or Deny
4. Your choice is remembered

### Permission Types

| Type | Description |
|------|-------------|
| **Allow Once** | Just this one request |
| **Allow for Session** | Until LocalGhost restarts |
| **Allow Always** | Permanently (until you revoke) |
| **Deny** | Block the request |

### Viewing Permissions

```bash
localghost permissions
```

### Revoking Permissions

```bash
# Revoke for a specific app
localghost revoke <client_id>
```

You can also revoke via the system tray menu.

### Headers for Identification

When your app makes requests, include these headers so you know what's asking for access:

```
X-Process-Name: my-app-name
X-Process-PID: 12345  (optional)
```

---

## 📡 API Reference

### Base URL

```
http://127.0.0.1:51473
```

### Built-in Endpoints

| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| `/health` | GET | Public | Check if server is running |
| `/capabilities` | GET | Public | List all available endpoints |
| `/permissions` | GET | Protected | View granted permissions |
| `/demo` | GET | Public | Interactive demo page |
| `/ws` | WebSocket | Public | Real-time communication |

### Demo Plugin Endpoints

| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| `/demo/ping` | GET | Public | Simple ping |
| `/demo/echo` | POST | Public | Echo back your data |
| `/demo/time` | GET | Public | Current server time |
| `/demo/system-info` | GET | Protected | System information |
| `/demo/execute` | POST | Protected | Run safe commands |

---

## 💡 Examples

### JavaScript (Browser)

```javascript
// Simple request (public endpoint)
const response = await fetch('http://127.0.0.1:51473/health');
const data = await response.json();
console.log(data);  // {status: "healthy", version: "0.1.0", ...}

// With identification (recommended)
const response = await fetch('http://127.0.0.1:51473/demo/system-info', {
    headers: {
        'X-Process-Name': 'my-web-app'
    }
});
// First time: popup appears asking for permission
// After approval: works automatically
```

### Python

```python
import httpx

# Simple request
response = httpx.get("http://127.0.0.1:51473/health")
print(response.json())

# With identification
response = httpx.get(
    "http://127.0.0.1:51473/demo/system-info",
    headers={"X-Process-Name": "my-python-script"}
)
print(response.json())
```

### cURL

```bash
# Health check
curl http://127.0.0.1:51473/health

# With identification
curl -H "X-Process-Name: my-script" http://127.0.0.1:51473/demo/system-info
```

### WebSocket

```javascript
const ws = new WebSocket('ws://127.0.0.1:51473/ws');

ws.onopen = () => {
    ws.send(JSON.stringify({ type: 'hello', data: 'world' }));
};

ws.onmessage = (event) => {
    console.log('Received:', JSON.parse(event.data));
};
```

---

## 🔧 Troubleshooting

### "Connection refused" or "Cannot connect"

**The server isn't running.** Start it:
```bash
localghost run
```

### "Address already in use"

**Another process is using port 51473.** Find and stop it:
```bash
# macOS/Linux
lsof -i :51473
kill <PID>

# Windows (PowerShell)
Get-NetTCPConnection -LocalPort 51473
Stop-Process -Id <PID>
```

Or use a different port:
```bash
localghost run --port 9000
```

### System tray icon not showing

Some Linux systems need extra packages:
```bash
# Ubuntu/Debian
sudo apt install python3-gi gir1.2-appindicator3-0.1

# Fedora
sudo dnf install python3-gobject libappindicator-gtk3
```

### "Permission denied" errors

Make sure you're not running as root/admin (you shouldn't need to).

### Popup not appearing

Check if LocalGhost is running:
```bash
localghost status
```

---

## 🔄 Recovery & Repair

### LocalGhost won't start

**Step 1: Check status**
```bash
localghost status
```

**Step 2: Try running manually**
```bash
localghost run --no-tray
```

**Step 3: Check logs**

| Platform | Log Location |
|----------|-------------|
| Windows | `%APPDATA%\LocalGhost\Logs\` |
| macOS | `~/Library/Logs/LocalGhost/` |
| Linux | `~/.local/state/LocalGhost/` |

### Reinstall from Scratch

```bash
# 1. Uninstall completely
localghost uninstall
pip uninstall localghost -y

# 2. Remove data (optional - removes all permissions)
rm -rf ~/.local/share/LocalGhost      # Linux
rm -rf ~/Library/Application\ Support/LocalGhost  # macOS

# 3. Install fresh
pip install git+https://github.com/suhaibbinyounis/LocalGhost.git
```

### Update to Latest Version

```bash
pip install --upgrade git+https://github.com/suhaibbinyounis/LocalGhost.git
```

### Reset Permissions

Delete the database to reset all permissions:

```bash
# Linux
rm ~/.local/share/LocalGhost/localghost.db

# macOS
rm ~/Library/Application\ Support/LocalGhost/localghost.db

# Windows (PowerShell)
Remove-Item "$env:APPDATA\LocalGhost\localghost.db"
```

### Reset Secret Key

This will invalidate all existing tokens:

```bash
# Linux
rm ~/.local/share/LocalGhost/.secret

# macOS
rm ~/Library/Application\ Support/LocalGhost/.secret

# Windows (PowerShell)
Remove-Item "$env:APPDATA\LocalGhost\.secret"
```

---

## ⚙️ Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `LOCALGHOST_HOST` | `127.0.0.1` | Bind address (don't change!) |
| `LOCALGHOST_PORT` | `51473` | Port number |
| `LOCALGHOST_NO_AUTOSTART` | (not set) | Set to `1` to disable auto-start |

### CLI Options

```bash
# Show help
localghost --help

# Run with options
localghost run --host 127.0.0.1 --port 9000 --no-tray

# Verbose mode
localghost -v run
```

### Default Configuration

All defaults are in `pyproject.toml` under `[tool.localghost]`:

```toml
[tool.localghost]
app_name = "LocalGhost"
default_host = "127.0.0.1"
default_port = 51473
token_expiry_hours = 24
consent_timeout_seconds = 60
```

---

## 🤝 Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for development setup.

```bash
# Clone
git clone https://github.com/suhaibbinyounis/LocalGhost.git
cd LocalGhost

# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest tests/ -v
```

---

## 📄 License

MIT License - see [LICENSE](LICENSE) file.

---

## 🆘 Need Help?

1. Check [Troubleshooting](#-troubleshooting) above
2. Open the demo page: `http://127.0.0.1:51473/demo`
3. [Open an issue](https://github.com/suhaibbinyounis/LocalGhost/issues) on GitHub
