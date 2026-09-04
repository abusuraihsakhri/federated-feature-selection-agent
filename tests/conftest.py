"""
Shared pytest fixtures for federated-feature-selection-agent.

Sets a deterministic AUDIT_SECRET_KEY so HMAC-based tests are reproducible
without relying on the production key or a random ephemeral key.
"""
import os
import pytest


@pytest.fixture(autouse=True)
def _deterministic_audit_key(monkeypatch):
    """Ensure every test runs with a stable, known audit secret."""
    monkeypatch.setenv("AUDIT_SECRET_KEY", "test-audit-secret-key-deterministic-2026")
    yield
