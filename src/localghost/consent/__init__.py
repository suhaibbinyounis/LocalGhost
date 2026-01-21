"""Consent system package."""

from .prompt import ConsentPrompt, ConsentResult
from .handler import ConsentHandler

__all__ = ["ConsentHandler", "ConsentPrompt", "ConsentResult"]
