"""Tests for the G0DM0D3 MCP bridge.

Run with pytest:
    pytest tests/test_tools.py

pytest-asyncio collects these because they are named `test_*` and are
async coroutines.
"""

from __future__ import annotations

from typing import Any

from godmod3_mcp.tools import coding_chat
from godmod3_mcp.utils import (
    aggregate_stream,
    format_chat_response,
    merge_local_models,
    normalize_messages,
)


class _FakeClient:
    """Minimal async client stub for testing coding_chat payload routing."""

    def __init__(self) -> None:
        self.last_method: str | None = None
        self.last_payload: dict[str, Any] | None = None

    async def ultraplinian_completions(self, payload: dict[str, Any]) -> dict[str, Any]:
        self.last_method = "ultraplinian_completions"
        self.last_payload = payload
        return {"response": "ok"}

    async def consortium_completions(self, payload: dict[str, Any]) -> dict[str, Any]:
        self.last_method = "consortium_completions"
        self.last_payload = payload
        return {"synthesis": "ok"}

    async def chat_completions(self, payload: dict[str, Any]) -> dict[str, Any]:
        self.last_method = "chat_completions"
        self.last_payload = payload
        return {"choices": [{"message": {"content": "ok"}}]}


class _FakeContext:
    def __init__(self, client: _FakeClient) -> None:
        self.request_context = type("R", (), {"lifespan_context": {"client": client}})()


def _assert_coding_defaults(payload: dict[str, Any]) -> None:
    assert payload["godmode"] is True
    assert payload["autotune"] is True
    assert payload["strategy"] == "adaptive"
    assert payload["parseltongue"] is True
    assert payload["parseltongue_technique"] == "leetspeak"
    assert payload["parseltongue_intensity"] == "high"
    assert payload["stm_modules"] == ["hedge_reducer", "direct_mode"]
    assert payload["contribute_to_dataset"] is False


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


async def test_coding_chat_defaults_to_ultraplinian() -> None:
    client = _FakeClient()
    ctx = _FakeContext(client)
    await coding_chat("Write a Python function", stream=False, ctx=ctx)
    assert client.last_method == "ultraplinian_completions"
    payload = client.last_payload
    assert payload is not None
    assert payload["messages"] == [{"role": "user", "content": "Write a Python function"}]
    assert payload["tier"] == "standard"
    assert payload["liquid_min_delta"] == 8
    _assert_coding_defaults(payload)


async def test_coding_chat_consortium_engine() -> None:
    client = _FakeClient()
    ctx = _FakeContext(client)
    await coding_chat(
        "Refactor this class",
        engine="consortium",
        tier="smart",
        model="custom/model",
        stream=False,
        ctx=ctx,
    )
    assert client.last_method == "consortium_completions"
    payload = client.last_payload
    assert payload is not None
    assert payload["tier"] == "smart"
    assert payload["orchestrator_model"] == "custom/model"
    _assert_coding_defaults(payload)


async def test_coding_chat_single_engine() -> None:
    client = _FakeClient()
    ctx = _FakeContext(client)
    await coding_chat(
        [{"role": "user", "content": "Hello"}],
        engine="single",
        model="qwen/qwen3-8b",
        stream=False,
        ctx=ctx,
    )
    assert client.last_method == "chat_completions"
    payload = client.last_payload
    assert payload is not None
    assert payload["model"] == "qwen/qwen3-8b"
    _assert_coding_defaults(payload)


async def test_coding_chat_overrides_obfuscation_intensity() -> None:
    client = _FakeClient()
    ctx = _FakeContext(client)
    await coding_chat("Hello", parseltongue_intensity="low", stream=False, ctx=ctx)
    assert client.last_payload["parseltongue_intensity"] == "low"


async def test_coding_chat_streaming_ultraplinian() -> None:
    class _StreamingFakeClient(_FakeClient):
        async def _stream(self):
            yield {"choices": [{"delta": {"content": "code"}}]}
            yield {"winner": {"model": "a/b", "score": 95}}
            yield {"_event": "done"}

        async def ultraplinian_completions(self, payload: dict[str, Any]):
            self.last_payload = payload
            self.last_method = "ultraplinian_completions"
            return self._stream()

    client = _StreamingFakeClient()
    ctx = _FakeContext(client)
    result = await coding_chat("Hello", stream=True, ctx=ctx)
    assert "code" in result
    assert "Winner" in result
