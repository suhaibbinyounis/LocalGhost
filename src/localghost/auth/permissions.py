"""Permission storage and management."""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from enum import Enum
from pathlib import Path
from typing import Any

import aiosqlite


class GrantType(str, Enum):
    """Types of permission grants."""

    TEMPORARY = "temporary"  # Single request
    SESSION = "session"  # Until service restart
    TIMED = "timed"  # For a specific duration
    PERMANENT = "permanent"  # Forever until revoked


class PermissionStore:
    """SQLite-based permission storage."""

    def __init__(self, db_path: Path) -> None:
        """Initialize with database path."""
        self.db_path = db_path
        self._db: aiosqlite.Connection | None = None

    async def initialize(self) -> None:
        """Initialize database and create tables."""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._db = await aiosqlite.connect(self.db_path)
        self._db.row_factory = aiosqlite.Row

        await self._db.execute("""
            CREATE TABLE IF NOT EXISTS permissions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                client_id TEXT NOT NULL,
                client_name TEXT,
                endpoint TEXT NOT NULL,
                permissions TEXT NOT NULL,
                grant_type TEXT NOT NULL,
                granted_at TEXT NOT NULL,
                expires_at TEXT,
                token TEXT,
                UNIQUE(client_id, endpoint)
            )
        """)

        await self._db.execute("""
            CREATE TABLE IF NOT EXISTS audit_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                client_id TEXT NOT NULL,
                endpoint TEXT NOT NULL,
                action TEXT NOT NULL,
                details TEXT
            )
        """)

        await self._db.commit()

    async def close(self) -> None:
        """Close database connection."""
        if self._db:
            await self._db.close()
            self._db = None

    async def grant_permission(
        self,
        client_id: str,
        endpoint: str,
        permissions: list[str],
        grant_type: GrantType,
        token: str,
        client_name: str | None = None,
        duration_hours: float | None = None,
    ) -> None:
        """Grant permission to a client."""
        if self._db is None:
            raise RuntimeError("Database not initialized")

        now = datetime.now(timezone.utc)
        expires_at = None
        if grant_type == GrantType.TIMED and duration_hours:
            expires_at = now + timedelta(hours=duration_hours)
        elif grant_type == GrantType.TEMPORARY:
            expires_at = now + timedelta(minutes=5)

        await self._db.execute(
            """
            INSERT OR REPLACE INTO permissions 
            (client_id, client_name, endpoint, permissions, grant_type, granted_at, expires_at, token)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                client_id,
                client_name,
                endpoint,
                json.dumps(permissions),
                grant_type.value,
                now.isoformat(),
                expires_at.isoformat() if expires_at else None,
                token,
            ),
        )
        await self._db.commit()

        await self._log_action(client_id, endpoint, "grant", {"grant_type": grant_type.value})

    async def check_permission(self, client_id: str, endpoint: str) -> dict[str, Any] | None:
        """Check if client has permission for endpoint."""
        if self._db is None:
            raise RuntimeError("Database not initialized")

        async with self._db.execute(
            """
            SELECT * FROM permissions 
            WHERE client_id = ? AND endpoint = ?
            """,
            (client_id, endpoint),
        ) as cursor:
            row = await cursor.fetchone()

        if row is None:
            return None

        # Check expiration
        if row["expires_at"]:
            expires = datetime.fromisoformat(row["expires_at"])
            if datetime.now(timezone.utc) > expires:
                await self.revoke_permission(client_id, endpoint)
                return None

        return dict(row)

    async def get_token(self, client_id: str, endpoint: str) -> str | None:
        """Get stored token for client/endpoint."""
        perm = await self.check_permission(client_id, endpoint)
        return perm["token"] if perm else None

    async def revoke_permission(self, client_id: str, endpoint: str) -> None:
        """Revoke permission for a client/endpoint pair."""
        if self._db is None:
            raise RuntimeError("Database not initialized")

        await self._db.execute(
            "DELETE FROM permissions WHERE client_id = ? AND endpoint = ?",
            (client_id, endpoint),
        )
        await self._db.commit()
        await self._log_action(client_id, endpoint, "revoke", {})

    async def revoke_all_for_client(self, client_id: str) -> None:
        """Revoke all permissions for a client."""
        if self._db is None:
            raise RuntimeError("Database not initialized")

        await self._db.execute("DELETE FROM permissions WHERE client_id = ?", (client_id,))
        await self._db.commit()
        await self._log_action(client_id, "*", "revoke_all", {})

    async def list_all_grants(self) -> list[dict[str, Any]]:
        """List all active permission grants."""
        if self._db is None:
            raise RuntimeError("Database not initialized")

        async with self._db.execute("SELECT * FROM permissions ORDER BY granted_at DESC") as cursor:
            rows = await cursor.fetchall()

        return [dict(row) for row in rows]

    async def _log_action(
        self, client_id: str, endpoint: str, action: str, details: dict[str, Any]
    ) -> None:
        """Log an audit action."""
        if self._db is None:
            return

        await self._db.execute(
            """
            INSERT INTO audit_log (timestamp, client_id, endpoint, action, details)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                datetime.now(timezone.utc).isoformat(),
                client_id,
                endpoint,
                action,
                json.dumps(details),
            ),
        )
        await self._db.commit()
