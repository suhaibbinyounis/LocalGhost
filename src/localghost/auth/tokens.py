"""Token generation and validation."""

from __future__ import annotations

import hashlib
import hmac
import json
import secrets
import time
from dataclasses import dataclass
from typing import Any

from cryptography.fernet import Fernet, InvalidToken


@dataclass
class TokenPayload:
    """Token payload data."""

    client_id: str
    endpoint: str
    permissions: list[str]
    issued_at: float
    expires_at: float | None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "client_id": self.client_id,
            "endpoint": self.endpoint,
            "permissions": self.permissions,
            "issued_at": self.issued_at,
            "expires_at": self.expires_at,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> TokenPayload:
        """Create from dictionary."""
        return cls(
            client_id=data["client_id"],
            endpoint=data["endpoint"],
            permissions=data["permissions"],
            issued_at=data["issued_at"],
            expires_at=data.get("expires_at"),
        )


class TokenManager:
    """Manages token generation and validation."""

    def __init__(self, secret_key: bytes | None = None) -> None:
        """Initialize with optional secret key."""
        if secret_key is None:
            secret_key = Fernet.generate_key()
        self._fernet = Fernet(secret_key)
        self._secret_key = secret_key

    @property
    def secret_key(self) -> bytes:
        """Get the secret key for persistence."""
        return self._secret_key

    def generate_token(
        self,
        client_id: str,
        endpoint: str,
        permissions: list[str],
        expires_in_hours: float | None = None,
    ) -> str:
        """Generate an encrypted token."""
        now = time.time()
        expires_at = None
        if expires_in_hours is not None:
            expires_at = now + (expires_in_hours * 3600)

        payload = TokenPayload(
            client_id=client_id,
            endpoint=endpoint,
            permissions=permissions,
            issued_at=now,
            expires_at=expires_at,
        )
        data = json.dumps(payload.to_dict()).encode()
        return self._fernet.encrypt(data).decode()

    def validate_token(self, token: str) -> TokenPayload | None:
        """Validate and decode a token. Returns None if invalid."""
        try:
            data = self._fernet.decrypt(token.encode())
            payload = TokenPayload.from_dict(json.loads(data))

            # Check expiration
            if payload.expires_at is not None and time.time() > payload.expires_at:
                return None

            return payload
        except (InvalidToken, json.JSONDecodeError, KeyError):
            return None

    def generate_client_id(self, program_name: str, pid: int | None = None) -> str:
        """Generate a deterministic client ID for a program."""
        data = program_name
        if pid is not None:
            data = f"{program_name}:{pid}"
        return hashlib.sha256(data.encode()).hexdigest()[:16]

    @staticmethod
    def generate_secret() -> bytes:
        """Generate a new secret key."""
        return Fernet.generate_key()
