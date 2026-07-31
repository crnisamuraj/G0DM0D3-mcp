"""Tests for environment-based configuration parsing."""

from __future__ import annotations

import os

import pytest

from godmod3_mcp.config import Config


@pytest.fixture(autouse=True)
def _clear_godmod3_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Clear GODMOD3-prefixed environment variables before each test."""
    for key in list(os.environ):
        if key.startswith("GODMOD3_"):
            monkeypatch.delenv(key, raising=False)


def test_default_config() -> None:
    config = Config.from_env()
    assert config.base_url == "http://localhost:7860"
    assert config.api_key is None
    assert config.transport == "stdio"
    assert config.http_port == 3001
    assert config.timeout == 120.0
    assert config.log_level == "INFO"
    assert config.mcp_allowed_hosts == []
    assert config.mcp_disable_dns_rebinding_protection is False


def test_allowed_hosts_parsed_from_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GODMOD3_MCP_ALLOWED_HOSTS", "godmod3-mcp-http:*, odysseus:*,10.89.2.5:3001")
    config = Config.from_env()
    assert config.mcp_allowed_hosts == ["godmod3-mcp-http:*", "odysseus:*", "10.89.2.5:3001"]


def test_disable_dns_rebinding_protection_env_values(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    for value in ("true", "True", "1", "yes", "on"):
        monkeypatch.setenv("GODMOD3_MCP_DISABLE_DNS_REBINDING_PROTECTION", value)
        config = Config.from_env()
        assert config.mcp_disable_dns_rebinding_protection is True, value

    for value in ("false", "0", "no", "off", ""):
        monkeypatch.setenv("GODMOD3_MCP_DISABLE_DNS_REBINDING_PROTECTION", value)
        config = Config.from_env()
        assert config.mcp_disable_dns_rebinding_protection is False, value


def test_invalid_transport_defaults_to_stdio(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GODMOD3_MCP_TRANSPORT", "invalid")
    config = Config.from_env()
    assert config.transport == "stdio"


def test_invalid_http_port_defaults_to_3001(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GODMOD3_MCP_HTTP_PORT", "not-a-number")
    config = Config.from_env()
    assert config.http_port == 3001


def test_invalid_timeout_defaults_to_120(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GODMOD3_TIMEOUT", "not-a-number")
    config = Config.from_env()
    assert config.timeout == 120.0
