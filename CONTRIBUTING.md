# Contributing to LocalGhost

Thank you for your interest in contributing! 🎉

## Quick Start

```bash
# Clone the repo
git clone https://github.com/suhaibbinyounis/LocalGhost.git
cd LocalGhost

# Install in development mode
pip install -e ".[dev]"

# Run tests
pytest tests/ -v

# Run linting
ruff check src/
mypy src/localghost
```

## Development Workflow

1. **Fork** the repository
2. **Create a branch** for your feature: `git checkout -b feature/my-feature`
3. **Make changes** and add tests
4. **Run tests**: `pytest tests/ -v`
5. **Commit**: `git commit -m "Add my feature"`
6. **Push**: `git push origin feature/my-feature`
7. **Open a Pull Request**

## Code Style

- Follow PEP 8 guidelines
- Use type hints for all functions
- Maximum line length: 100 characters
- Run `ruff check` and `mypy` before submitting

## Adding a Plugin

1. Create a new file in `src/localghost/plugins/`
2. Extend the `Plugin` base class
3. Define endpoints with `Endpoint` dataclass
4. Mark endpoints as `PUBLIC` or `PROTECTED`

Example:
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
        ]
    
    async def hello(self) -> dict:
        return {"message": "Hello!"}
```

## Reporting Issues

- Use GitHub Issues
- Include OS, Python version, and steps to reproduce
- Attach logs if available

## Questions?

Open a Discussion or Issue on GitHub.
