"""Example client demonstrating LocalGhost API usage."""

from __future__ import annotations

import os
import httpx


def main() -> None:
    """Demonstrate LocalGhost client usage."""
    base_url = os.environ.get("LOCALGHOST_URL", "http://127.0.0.1:8473")

    with httpx.Client(base_url=base_url) as client:
        # Public endpoint - no auth required
        print("=== Health Check (Public) ===")
        response = client.get("/health")
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")

        print("\n=== Capabilities (Public) ===")
        response = client.get("/capabilities")
        print(f"Plugins: {response.json()}")

        # Protected endpoint - will trigger consent prompt
        print("\n=== Protected Endpoint ===")
        headers = {
            "X-Process-Name": "example_client",
            "X-Process-PID": str(os.getpid()),
        }
        response = client.get("/permissions", headers=headers)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")


if __name__ == "__main__":
    main()
