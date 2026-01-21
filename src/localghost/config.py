"""Configuration management for LocalGhost.

Loads defaults from pyproject.toml [tool.localghost] section.
"""

from __future__ import annotations

import sys
from functools import lru_cache
from pathlib import Path
from typing import Any

import platformdirs
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib


def _load_tool_config() -> dict[str, Any]:
    """Load [tool.localghost] from pyproject.toml."""
    # Try to find pyproject.toml by traversing up from package location
    pkg_dir = Path(__file__).parent
    for parent in [pkg_dir, *pkg_dir.parents]:
        pyproject = parent / "pyproject.toml"
        if pyproject.exists():
            with open(pyproject, "rb") as f:
                data = tomllib.load(f)
            return data.get("tool", {}).get("localghost", {})
    return {}


_TOOL_CONFIG = _load_tool_config()


def _get_default(key: str, fallback: Any) -> Any:
    """Get default from tool config or use fallback."""
    return _TOOL_CONFIG.get(key, fallback)


class Settings(BaseSettings):
    """LocalGhost configuration settings."""

    model_config = SettingsConfigDict(
        env_prefix="LOCALGHOST_",
        env_file=".env",
        extra="ignore",
    )

    # App metadata
    app_name: str = Field(default_factory=lambda: _get_default("app_name", "LocalGhost"))

    # Server settings
    host: str = Field(default_factory=lambda: _get_default("default_host", "127.0.0.1"))
    port: int = Field(default_factory=lambda: _get_default("default_port", 8473))

    # Token settings
    token_expiry_hours: int = Field(
        default_factory=lambda: _get_default("token_expiry_hours", 24)
    )

    # Storage
    db_name: str = Field(default_factory=lambda: _get_default("db_name", "localghost.db"))
    config_filename: str = Field(
        default_factory=lambda: _get_default("config_filename", "config.yaml")
    )
    log_filename: str = Field(
        default_factory=lambda: _get_default("log_filename", "localghost.log")
    )

    # Service settings
    service_name: str = Field(
        default_factory=lambda: _get_default("service_name", "localghost")
    )
    service_display_name: str = Field(
        default_factory=lambda: _get_default("service_display_name", "LocalGhost Service")
    )
    service_description: str = Field(
        default_factory=lambda: _get_default(
            "service_description", "Local authorization service for cross-platform IPC"
        )
    )

    # Consent settings
    consent_timeout_seconds: int = Field(
        default_factory=lambda: _get_default("consent_timeout_seconds", 60)
    )
    default_grant_duration_hours: int = Field(
        default_factory=lambda: _get_default("default_grant_duration_hours", 8)
    )

    @property
    def data_dir(self) -> Path:
        """Get platform-specific data directory."""
        return Path(platformdirs.user_data_dir(self.app_name))

    @property
    def config_dir(self) -> Path:
        """Get platform-specific config directory."""
        return Path(platformdirs.user_config_dir(self.app_name))

    @property
    def log_dir(self) -> Path:
        """Get platform-specific log directory."""
        return Path(platformdirs.user_log_dir(self.app_name))

    @property
    def db_path(self) -> Path:
        """Full path to the database file."""
        return self.data_dir / self.db_name

    @property
    def config_path(self) -> Path:
        """Full path to the config file."""
        return self.config_dir / self.config_filename

    @property
    def log_path(self) -> Path:
        """Full path to the log file."""
        return self.log_dir / self.log_filename

    def ensure_dirs(self) -> None:
        """Create all required directories."""
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.log_dir.mkdir(parents=True, exist_ok=True)


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
