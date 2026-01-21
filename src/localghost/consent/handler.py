"""Consent flow handler."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from fastapi import Request

from ..auth.permissions import GrantType
from .prompt import ConsentPrompt, ConsentResult, show_consent_dialog

if TYPE_CHECKING:
    from ..auth.permissions import PermissionStore
    from ..auth.tokens import TokenManager
    from ..config import Settings


logger = logging.getLogger(__name__)


class ConsentHandler:
    """Handles consent flow for protected endpoints."""

    def __init__(
        self,
        settings: Settings,
        token_manager: TokenManager,
        permission_store: PermissionStore,
    ) -> None:
        """Initialize consent handler."""
        self.settings = settings
        self.token_manager = token_manager
        self.permission_store = permission_store
        self._pending_requests: dict[str, Any] = {}

    async def __call__(
        self,
        client_id: str,
        endpoint: str,
        request: Request,
    ) -> dict[str, Any] | None:
        """Handle consent request. Returns permissions dict if approved, None if denied."""
        # Get client info from request
        client_name = request.headers.get("X-Process-Name", "Unknown Application")
        permissions = ["access"]  # Default permission

        # Create consent prompt
        prompt = ConsentPrompt(
            client_id=client_id,
            client_name=client_name,
            endpoint=endpoint,
            permissions=permissions,
            timeout_seconds=self.settings.consent_timeout_seconds,
        )

        logger.info(f"Requesting consent for {client_name} -> {endpoint}")

        # Show dialog
        result = await show_consent_dialog(prompt)
        logger.info(f"Consent result: {result}")

        if result == ConsentResult.DENIED:
            return None

        # Map result to grant type
        grant_type_map = {
            ConsentResult.ALLOW_ONCE: GrantType.TEMPORARY,
            ConsentResult.ALLOW_SESSION: GrantType.SESSION,
            ConsentResult.ALLOW_TIMED: GrantType.TIMED,
            ConsentResult.ALLOW_PERMANENT: GrantType.PERMANENT,
        }
        grant_type = grant_type_map.get(result, GrantType.TEMPORARY)

        # Generate token
        duration = None
        if grant_type == GrantType.TIMED:
            duration = self.settings.default_grant_duration_hours
        elif grant_type == GrantType.PERMANENT:
            duration = None  # No expiration
        else:
            duration = self.settings.token_expiry_hours

        token = self.token_manager.generate_token(
            client_id=client_id,
            endpoint=endpoint,
            permissions=permissions,
            expires_in_hours=duration,
        )

        # Store permission
        await self.permission_store.grant_permission(
            client_id=client_id,
            endpoint=endpoint,
            permissions=permissions,
            grant_type=grant_type,
            token=token,
            client_name=client_name,
            duration_hours=duration,
        )

        return {"permissions": permissions, "token": token}

    async def request_consent_via_tray(
        self,
        client_id: str,
        client_name: str,
        endpoint: str,
        permissions: list[str],
    ) -> None:
        """Queue a consent request to be shown via tray notification."""
        request_id = f"{client_id}:{endpoint}"
        self._pending_requests[request_id] = {
            "client_id": client_id,
            "client_name": client_name,
            "endpoint": endpoint,
            "permissions": permissions,
        }

    def get_pending_requests(self) -> list[dict[str, Any]]:
        """Get list of pending consent requests."""
        return list(self._pending_requests.values())

    def clear_pending(self, client_id: str, endpoint: str) -> None:
        """Clear a pending request."""
        request_id = f"{client_id}:{endpoint}"
        self._pending_requests.pop(request_id, None)

    async def request_consent(self, client_id: str, endpoint: str) -> dict[str, Any] | None:
        """Request consent for a client to access an endpoint.
        
        This is a simplified version that doesn't require a Request object.
        """
        client_name = client_id.split("-")[0] if "-" in client_id else client_id
        permissions = ["access"]

        prompt = ConsentPrompt(
            client_id=client_id,
            client_name=client_name,
            endpoint=endpoint,
            permissions=permissions,
            timeout_seconds=self.settings.consent_timeout_seconds,
        )

        logger.info(f"Requesting consent for {client_name} -> {endpoint}")
        result = await show_consent_dialog(prompt)
        logger.info(f"Consent result: {result}")

        if result == ConsentResult.DENIED:
            return {"approved": False}

        # Map result to grant type
        grant_type_map = {
            ConsentResult.ALLOW_ONCE: GrantType.TEMPORARY,
            ConsentResult.ALLOW_SESSION: GrantType.SESSION,
            ConsentResult.ALLOW_TIMED: GrantType.TIMED,
            ConsentResult.ALLOW_PERMANENT: GrantType.PERMANENT,
        }
        grant_type = grant_type_map.get(result, GrantType.TEMPORARY)

        # Generate token
        duration = None
        if grant_type == GrantType.TIMED:
            duration = self.settings.default_grant_duration_hours
        elif grant_type == GrantType.PERMANENT:
            duration = None
        else:
            duration = self.settings.token_expiry_hours

        token = self.token_manager.generate_token(
            client_id=client_id,
            endpoint=endpoint,
            permissions=permissions,
            expires_in_hours=duration,
        )

        # Store permission
        await self.permission_store.grant_permission(
            client_id=client_id,
            endpoint=endpoint,
            permissions=permissions,
            grant_type=grant_type,
            token=token,
            client_name=client_name,
            duration_hours=duration,
        )

        return {"approved": True, "permissions": permissions, "token": token}
