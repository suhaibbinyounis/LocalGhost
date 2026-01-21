"""Tests for token management."""

import time

import pytest

from localghost.auth.tokens import TokenManager, TokenPayload


class TestTokenManager:
    """Tests for TokenManager."""

    def test_generate_and_validate_token(self) -> None:
        """Test basic token generation and validation."""
        manager = TokenManager()

        token = manager.generate_token(
            client_id="test-client",
            endpoint="/test/endpoint",
            permissions=["read", "write"],
            expires_in_hours=1,
        )

        assert token is not None
        assert isinstance(token, str)

        payload = manager.validate_token(token)
        assert payload is not None
        assert payload.client_id == "test-client"
        assert payload.endpoint == "/test/endpoint"
        assert payload.permissions == ["read", "write"]

    def test_token_expiration(self) -> None:
        """Test that expired tokens are rejected."""
        manager = TokenManager()

        # Create token that expires immediately
        token = manager.generate_token(
            client_id="test-client",
            endpoint="/test",
            permissions=[],
            expires_in_hours=0,  # Expires immediately
        )

        # Should be invalid (expired)
        time.sleep(0.1)
        payload = manager.validate_token(token)
        assert payload is None

    def test_invalid_token_rejected(self) -> None:
        """Test that invalid tokens are rejected."""
        manager = TokenManager()

        # Random invalid token
        payload = manager.validate_token("invalid-token-data")
        assert payload is None

        # Token from different secret
        other_manager = TokenManager()
        token = other_manager.generate_token(
            client_id="test",
            endpoint="/test",
            permissions=[],
        )
        payload = manager.validate_token(token)
        assert payload is None

    def test_generate_client_id(self) -> None:
        """Test client ID generation."""
        manager = TokenManager()

        # Same input should produce same ID
        id1 = manager.generate_client_id("test-app")
        id2 = manager.generate_client_id("test-app")
        assert id1 == id2

        # Different input should produce different ID
        id3 = manager.generate_client_id("other-app")
        assert id1 != id3

        # With PID
        id4 = manager.generate_client_id("test-app", pid=12345)
        assert id4 != id1

    def test_permanent_token_no_expiration(self) -> None:
        """Test that permanent tokens don't expire."""
        manager = TokenManager()

        token = manager.generate_token(
            client_id="test-client",
            endpoint="/test",
            permissions=["access"],
            expires_in_hours=None,  # No expiration
        )

        payload = manager.validate_token(token)
        assert payload is not None
        assert payload.expires_at is None

    def test_secret_key_persistence(self) -> None:
        """Test that secret key can be persisted and reused."""
        manager1 = TokenManager()
        secret = manager1.secret_key

        token = manager1.generate_token(
            client_id="test",
            endpoint="/test",
            permissions=[],
        )

        # Create new manager with same secret
        manager2 = TokenManager(secret)
        payload = manager2.validate_token(token)
        assert payload is not None
        assert payload.client_id == "test"
