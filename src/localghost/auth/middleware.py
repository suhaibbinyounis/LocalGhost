"""Authentication middleware for FastAPI."""

from __future__ import annotations

from typing import TYPE_CHECKING, Callable

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

if TYPE_CHECKING:
    from .permissions import PermissionStore
    from .tokens import TokenManager


class AuthMiddleware(BaseHTTPMiddleware):
    """Middleware for authentication and authorization."""

    def __init__(
        self,
        app: Callable,
        token_manager: TokenManager,
        permission_store: PermissionStore,
        public_paths: set[str] | None = None,
        consent_handler: Callable | None = None,
    ) -> None:
        """Initialize middleware."""
        super().__init__(app)
        self.token_manager = token_manager
        self.permission_store = permission_store
        self.public_paths = public_paths or {"/health", "/capabilities", "/docs", "/openapi.json"}
        self.consent_handler = consent_handler

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request through auth middleware."""
        path = request.url.path

        # Allow public paths without auth
        if path in self.public_paths or path.startswith("/public/"):
            return await call_next(request)

        # Get client identification
        client_id = self._identify_client(request)

        # Check for authorization header
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header[7:]
            payload = self.token_manager.validate_token(token)
            if payload and payload.client_id == client_id:
                # Valid token - proceed
                request.state.client_id = client_id
                request.state.permissions = payload.permissions
                return await call_next(request)

        # Check stored permission
        stored = await self.permission_store.check_permission(client_id, path)
        if stored:
            request.state.client_id = client_id
            request.state.permissions = stored.get("permissions", [])
            return await call_next(request)

        # No valid auth - trigger consent flow if handler available
        if self.consent_handler:
            approved = await self.consent_handler(client_id, path, request)
            if approved:
                request.state.client_id = client_id
                request.state.permissions = approved.get("permissions", [])
                return await call_next(request)

        # Denied
        return JSONResponse(
            status_code=401,
            content={
                "error": "unauthorized",
                "message": "Access requires authorization. Use system tray to approve.",
                "client_id": client_id,
                "endpoint": path,
            },
        )

    def _identify_client(self, request: Request) -> str:
        """Identify the client from request."""
        # Try X-Client-ID header first
        client_id = request.headers.get("X-Client-ID")
        if client_id:
            return client_id

        # Try to identify by process info (if provided)
        process_name = request.headers.get("X-Process-Name", "unknown")
        process_pid = request.headers.get("X-Process-PID")

        pid = int(process_pid) if process_pid else None
        return self.token_manager.generate_client_id(process_name, pid)
