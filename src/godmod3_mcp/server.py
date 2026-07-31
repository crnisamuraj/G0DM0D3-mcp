"""MCP server entry point for G0DM0D3.

Supports both stdio and HTTP/SSE transports via the official `mcp` SDK's
FastMCP server.

Run with:
    python -m godmod3_mcp.server                 # stdio (default)
    python -m godmod3_mcp.server --transport http # HTTP/SSE
"""

from __future__ import annotations

import argparse
import asyncio
import logging
import sys

from .config import Config
from .tools import (
    autotune_analyze,
    consortium_chat,
    dataset_stats,
    export_dataset,
    get_tier,
    health_check,
    list_models,
    parseltongue_detect,
    parseltongue_encode,
    research_info,
    research_query,
    research_stats,
    server_info,
    single_chat,
    submit_feedback,
    transform_text,
    ultraplinian_chat,
)
from .transports import build_mcp_server

logger = logging.getLogger(__name__)


def _attach_tools(mcp_server) -> None:
    """Register all G0DM0D3 tools on the MCP server instance."""
    tools = [
        health_check,
        server_info,
        list_models,
        get_tier,
        single_chat,
        ultraplinian_chat,
        consortium_chat,
        autotune_analyze,
        parseltongue_encode,
        parseltongue_detect,
        transform_text,
        submit_feedback,
        dataset_stats,
        export_dataset,
        research_info,
        research_stats,
        research_query,
    ]
    for tool in tools:
        mcp_server.add_tool(tool)


def _list_tool_names(mcp_server) -> list[str]:
    """Introspect registered tool names from the FastMCP tool manager."""
    tool_manager = getattr(mcp_server, "_tool_manager", None)
    if tool_manager is None:
        return []
    tools = getattr(tool_manager, "_tools", {})
    return sorted(tools.keys())


async def _run_stdio() -> None:
    mcp = build_mcp_server("godmod3")
    _attach_tools(mcp)
    await mcp.run_stdio_async()


async def _run_http(port: int) -> None:
    mcp = build_mcp_server("godmod3")
    _attach_tools(mcp)
    mcp.settings.port = port
    mcp.settings.host = "0.0.0.0"
    logger.info("Starting G0DM0D3 MCP HTTP/SSE server on %s:%s", mcp.settings.host, port)
    await mcp.run_sse_async()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="G0DM0D3 MCP bridge")
    parser.add_argument(
        "--transport",
        choices=["stdio", "http", "sse"],
        default=None,
        help="MCP transport (default: env GODMOD3_MCP_TRANSPORT or stdio)",
    )
    parser.add_argument("--port", type=int, default=None, help="HTTP/SSE port")
    parser.add_argument("--test", action="store_true", help="Print tool list and config then exit")
    args = parser.parse_args(argv)

    config = Config.from_env()
    transport = (args.transport or config.transport).lower()
    port = args.port or config.http_port

    logging.basicConfig(
        level=getattr(logging, config.log_level, logging.INFO),
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    if args.test:
        mcp = build_mcp_server("godmod3")
        _attach_tools(mcp)
        print(f"Transport: {transport}")
        print(f"Base URL: {config.base_url}")
        print(f"API key set: {bool(config.api_key)}")
        print("Tools:")
        for name in _list_tool_names(mcp):
            print(f"  - {name}")
        return 0

    try:
        if transport in ("http", "sse"):
            asyncio.run(_run_http(port))
        else:
            asyncio.run(_run_stdio())
    except KeyboardInterrupt:
        logger.info("Shutdown requested")
    return 0


if __name__ == "__main__":
    sys.exit(main())
