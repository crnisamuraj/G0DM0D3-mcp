"""Configuration for the G0DM0D3 MCP bridge."""

from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Config:
    """Runtime configuration loaded from environment variables."""

    base_url: str
    api_key: str | None
    transport: str
    http_port: int
    timeout: float
    log_level: str
    mcp_allowed_hosts: list[str]
    mcp_disable_dns_rebinding_protection: bool

    @classmethod
    def from_env(cls) -> "Config":
        """Load configuration from environment variables with sensible defaults."""
        transport = os.environ.get("GODMOD3_MCP_TRANSPORT", "stdio").lower().strip()
        if transport not in {"stdio", "http", "sse"}:
            transport = "stdio"

        http_port_raw = os.environ.get("GODMOD3_MCP_HTTP_PORT", "3001")
        try:
            http_port = int(http_port_raw)
        except ValueError:
            http_port = 3001

        timeout_raw = os.environ.get("GODMOD3_TIMEOUT", "120")
        try:
            timeout = float(timeout_raw)
        except ValueError:
            timeout = 120.0

        allowed_hosts_raw = os.environ.get("GODMOD3_MCP_ALLOWED_HOSTS", "")
        mcp_allowed_hosts = [
            host.strip()
            for host in allowed_hosts_raw.split(",")
            if host.strip()
        ]

        disable_dns_rebinding = (
            os.environ.get("GODMOD3_MCP_DISABLE_DNS_REBINDING_PROTECTION", "").lower().strip()
            in {"1", "true", "yes", "on"}
        )

        return cls(
            base_url=(os.environ.get("GODMOD3_BASE_URL") or "http://localhost:7860").rstrip("/"),
            api_key=os.environ.get("GODMOD3_API_KEY") or None,
            transport=transport,
            http_port=http_port,
            timeout=timeout,
            log_level=(os.environ.get("GODMOD3_LOG_LEVEL") or "INFO").upper(),
            mcp_allowed_hosts=mcp_allowed_hosts,
            mcp_disable_dns_rebinding_protection=disable_dns_rebinding,
        )

    @property
    def auth_header(self) -> dict[str, str]:
        """Return the Authorization header when an API key is configured."""
        if self.api_key:
            return {"Authorization": f"Bearer {self.api_key}"}
        return {}
