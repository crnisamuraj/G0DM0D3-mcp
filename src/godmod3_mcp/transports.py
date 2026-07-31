"""Transport bootstrapping for stdio and HTTP/SSE MCP.

Uses the official `mcp` SDK's FastMCP server with a lifespan-managed G0DM0D3
client.
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import Any, AsyncIterator

from mcp.server.fastmcp import FastMCP
from mcp.server.transport_security import TransportSecuritySettings

from .client import Godmod3Client
from .config import Config

logger = logging.getLogger(__name__)


def build_mcp_server(name: str = "godmod3") -> FastMCP:
    """Build a FastMCP instance with lifespan-managed G0DM0D3 client."""
    return _build_fastmcp_server(name)


def _build_fastmcp_server(name: str) -> FastMCP:
    config = Config.from_env()

    transport_security: TransportSecuritySettings | None = None
    if config.mcp_disable_dns_rebinding_protection:
        transport_security = TransportSecuritySettings(
            enable_dns_rebinding_protection=False,
        )
    elif config.mcp_allowed_hosts:
        transport_security = TransportSecuritySettings(
            enable_dns_rebinding_protection=True,
            allowed_hosts=["localhost:*", "127.0.0.1:*"] + config.mcp_allowed_hosts,
        )

    @asynccontextmanager
    async def app_lifespan(server: FastMCP) -> AsyncIterator[dict[str, Any]]:
        client = Godmod3Client(config)
        try:
            logger.info("G0DM0D3 MCP bridge connecting to %s", config.base_url)
            yield {"client": client}
        finally:
            await client.close()

    mcp_kwargs: dict[str, Any] = {"lifespan": app_lifespan}
    if transport_security is not None:
        mcp_kwargs["transport_security"] = transport_security

    return FastMCP(name, **mcp_kwargs)
