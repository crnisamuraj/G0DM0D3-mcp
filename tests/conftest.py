"""Test helpers and fixtures for pytest."""

from __future__ import annotations

import asyncio
from typing import Any

from godmod3_mcp.config import Config


def make_config(**overrides: Any) -> Config:
    defaults = {
        "base_url": "http://localhost:7860",
        "api_key": None,
        "transport": "stdio",
        "http_port": 3001,
        "timeout": 30.0,
        "log_level": "INFO",
        "mcp_allowed_hosts": [],
        "mcp_disable_dns_rebinding_protection": False,
    }
    defaults.update(overrides)
    return Config(**defaults)


async def run_async(coro: Any) -> Any:
    return await coro


def run_sync(coro: Any) -> Any:
    return asyncio.run(coro)
