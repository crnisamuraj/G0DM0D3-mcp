"""Tests for the G0DM0D3 MCP bridge.

Run with pytest:
    pytest tests/test_tools.py

pytest-asyncio collects these because they are named `test_*` and are
async coroutines.
"""

from __future__ import annotations

from godmod3_mcp.utils import (
    aggregate_stream,
    format_chat_response,
    merge_local_models,
    normalize_messages,
)


async def test_normalize_messages_string() -> None:
    assert normalize_messages("hello") == [{"role": "user", "content": "hello"}]


async def test_normalize_messages_list() -> None:
    assert normalize_messages([{"role": "user", "content": "hi"}]) == [{"role": "user", "content": "hi"}]


async def test_merge_local_models() -> None:
    payload = {"local_model_url": "http://ollama:11434/v1", "local_models": ["qwen3:8b"]}
    merged = merge_local_models(payload)
    assert merged["extra_entries"][0]["model"] == "qwen3:8b"


async def test_format_chat_response_ultraplinian() -> None:
    data = {
        "response": "Buffer overflow works by...",
        "winner": {"model": "x/y", "score": 88, "duration_ms": 1200},
        "race": {"models_queried": 10, "models_succeeded": 9, "total_duration_ms": 5000},
    }
    text = format_chat_response(data)
    assert "Buffer overflow works by" in text
    assert "Winner" in text
    assert "Race" in text


async def test_aggregate_stream_chat() -> None:
    async def stream():
        yield {"choices": [{"delta": {"content": "Hello "}}]}
        yield {"choices": [{"delta": {"content": "world"}}]}
        yield {"_event": "done"}

    result = await aggregate_stream(stream(), mode="single")
    assert result["content"] == "Hello world"


async def test_aggregate_stream_ultraplinian_metadata() -> None:
    async def stream():
        yield {"choices": [{"delta": {"content": "Best"}}]}
        yield {"winner": {"model": "a/b", "score": 90}, "race": {"models_queried": 5, "models_succeeded": 5, "total_duration_ms": 1000}}
        yield {"_event": "done"}

    result = await aggregate_stream(stream(), mode="ultraplinian")
    assert result["content"] == "Best"
    assert result["metadata"]["winner"]["score"] == 90
