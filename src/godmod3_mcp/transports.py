"""Transport bootstrapping for stdio and HTTP/SSE MCP.

Uses the official `mcp` SDK's FastMCP server with a lifespan-managed G0DM0D3
client.
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import Any, AsyncIterator

from mcp.server.fastmcp import FastMCP

from .client import Godmod3Client
from .config import Config

logger = logging.getLogger(__name__)


def build_mcp_server(name: str = "godmod3") -> FastMCP:
    """Build a FastMCP instance with lifespan-managed G0DM0D3 client."""
    return _build_fastmcp_server(name)


def _build_fastmcp_server(name: str) -> FastMCP:
    @asynccontextmanager
    async def app_lifespan(server: FastMCP) -> AsyncIterator[dict[str, Any]]:
        config = Config.from_env()
        client = Godmod3Client(config)
        try:
            logger.info("G0DM0D3 MCP bridge connecting to %s", config.base_url)
            yield {"client": client}
        finally:
            await client.close()

    return FastMCP(name, lifespan=app_lifespan)
