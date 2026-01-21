"""Tests for permission storage."""

from pathlib import Path
from datetime import datetime, timedelta

import pytest

from localghost.auth.permissions import GrantType, PermissionStore


@pytest.fixture
async def store(tmp_path: Path):
    """Create a temporary permission store."""
    db_path = tmp_path / "test.db"
    store = PermissionStore(db_path)
    await store.initialize()
    yield store
    await store.close()


class TestPermissionStore:
    """Tests for PermissionStore."""

    @pytest.mark.asyncio
    async def test_grant_and_check_permission(self, store: PermissionStore) -> None:
        """Test granting and checking permissions."""
        await store.grant_permission(
            client_id="test-client",
            endpoint="/test/endpoint",
            permissions=["read"],
            grant_type=GrantType.PERMANENT,
            token="test-token-123",
            client_name="Test App",
        )

        result = await store.check_permission("test-client", "/test/endpoint")
        assert result is not None
        assert result["client_id"] == "test-client"
        assert result["token"] == "test-token-123"

    @pytest.mark.asyncio
    async def test_no_permission_returns_none(self, store: PermissionStore) -> None:
        """Test that missing permission returns None."""
        result = await store.check_permission("nonexistent", "/unknown")
        assert result is None

    @pytest.mark.asyncio
    async def test_revoke_permission(self, store: PermissionStore) -> None:
        """Test revoking permissions."""
        await store.grant_permission(
            client_id="test-client",
            endpoint="/test",
            permissions=["read"],
            grant_type=GrantType.PERMANENT,
            token="token",
        )

        # Verify granted
        assert await store.check_permission("test-client", "/test") is not None

        # Revoke
        await store.revoke_permission("test-client", "/test")

        # Verify revoked
        assert await store.check_permission("test-client", "/test") is None

    @pytest.mark.asyncio
    async def test_revoke_all_for_client(self, store: PermissionStore) -> None:
        """Test revoking all permissions for a client."""
        for i in range(3):
            await store.grant_permission(
                client_id="test-client",
                endpoint=f"/test/{i}",
                permissions=["read"],
                grant_type=GrantType.PERMANENT,
                token=f"token-{i}",
            )

        await store.revoke_all_for_client("test-client")

        for i in range(3):
            assert await store.check_permission("test-client", f"/test/{i}") is None

    @pytest.mark.asyncio
    async def test_list_all_grants(self, store: PermissionStore) -> None:
        """Test listing all grants."""
        for i in range(3):
            await store.grant_permission(
                client_id=f"client-{i}",
                endpoint="/test",
                permissions=["read"],
                grant_type=GrantType.PERMANENT,
                token=f"token-{i}",
            )

        grants = await store.list_all_grants()
        assert len(grants) == 3

    @pytest.mark.asyncio
    async def test_get_token(self, store: PermissionStore) -> None:
        """Test getting stored token."""
        await store.grant_permission(
            client_id="test-client",
            endpoint="/test",
            permissions=["read"],
            grant_type=GrantType.PERMANENT,
            token="secret-token",
        )

        token = await store.get_token("test-client", "/test")
        assert token == "secret-token"

    @pytest.mark.asyncio
    async def test_upsert_permission(self, store: PermissionStore) -> None:
        """Test that granting same client/endpoint updates the record."""
        await store.grant_permission(
            client_id="test-client",
            endpoint="/test",
            permissions=["read"],
            grant_type=GrantType.TEMPORARY,
            token="token-1",
        )

        await store.grant_permission(
            client_id="test-client",
            endpoint="/test",
            permissions=["read", "write"],
            grant_type=GrantType.PERMANENT,
            token="token-2",
        )

        result = await store.check_permission("test-client", "/test")
        assert result is not None
        assert result["token"] == "token-2"
        assert result["grant_type"] == "permanent"
