"""Helpers for streaming aggregation and response formatting."""

from __future__ import annotations

import json
import logging
from typing import Any, AsyncIterator

logger = logging.getLogger(__name__)


def format_chat_response(data: dict[str, Any]) -> str:
    """Format a non-streaming chat completion response for the agent."""
    parts: list[str] = []

    if "choices" in data:
        content = data["choices"][0].get("message", {}).get("content", "")
        if content:
            parts.append(content)
        if "model" in data:
            parts.append(f"\n\n_Model: {data['model']}_")
    elif "response" in data:
        parts.append(str(data["response"]))
        if data.get("winner"):
            winner = data["winner"]
            parts.append(
                f"\n\n**Winner:** {winner.get('model')} "
                f"(score {winner.get('score')}, {winner.get('duration_ms')}ms)"
            )
        if data.get("race"):
            race = data["race"]
            parts.append(
                f"\n**Race:** {race.get('models_succeeded')}/{race.get('models_queried')} models "
                f"in {race.get('total_duration_ms')}ms"
            )
    elif "synthesis" in data:
        parts.append(str(data["synthesis"]))
        orch = data.get("orchestrator", {})
        parts.append(f"\n\n**Orchestrator:** {orch.get('model')} ({orch.get('duration_ms')}ms)")
    else:
        parts.append(json.dumps(data, indent=2))

    return "\n".join(parts)


async def aggregate_stream(stream: AsyncIterator[dict[str, Any]], mode: str = "ultraplinian") -> dict[str, Any]:
    """Aggregate G0DM0D3 SSE events into a single final result.

    For ULTRAPLINIAN we accumulate the latest leader content + final metadata.
    For CONSORTIUM we wait for the consortium:complete event.
    For plain chat we accumulate delta content.
    """
    output_parts: list[str] = []
    final_metadata: dict[str, Any] | None = None

    async for event in stream:
        event_type = event.pop("_event", None)

        if event_type == "done":
            continue

        if mode == "consortium":
            if event.get("event") == "consortium:complete" or "synthesis" in event:
                final_metadata = event
                break
            content = _extract_delta(event)
            if content:
                output_parts.append(content)
            continue

        # ULTRAPLINIAN / chat default
        content = _extract_delta(event)
        if content:
            output_parts.append(content)
        if not event.get("choices") and not event.get("_raw"):
            # Likely a metadata-only event; keep the richest one
            final_metadata = _merge_metadata(final_metadata, event)

    text = "".join(output_parts).strip()
    return {
        "content": text,
        "metadata": final_metadata or {},
    }


def _extract_delta(event: dict[str, Any]) -> str:
    """Extract text delta from an OpenAI-compatible chunk."""
    try:
        return event["choices"][0]["delta"].get("content", "") or ""
    except (KeyError, IndexError, TypeError):
        return ""


def _merge_metadata(current: dict[str, Any] | None, new: dict[str, Any]) -> dict[str, Any]:
    """Keep the metadata object with the most useful fields."""
    if current is None:
        return dict(new)
    # Prefer events that contain race / pipeline / winner info
    score_current = len(current)
    score_new = len(new)
    if any(k in new for k in ("winner", "race", "pipeline", "params_used")):
        score_new += 10
    return dict(new) if score_new >= score_current else current


def normalize_messages(messages: Any) -> list[dict[str, str]]:
    """Ensure messages are OpenAI-format dicts with string content."""
    result: list[dict[str, str]] = []
    if isinstance(messages, str):
        return [{"role": "user", "content": messages}]
    if not isinstance(messages, list):
        return []
    for msg in messages:
        if isinstance(msg, dict) and "role" in msg and "content" in msg:
            result.append({"role": str(msg["role"]), "content": str(msg["content"])})
        elif isinstance(msg, str):
            result.append({"role": "user", "content": msg})
    return result


def merge_local_models(payload: dict[str, Any]) -> dict[str, Any]:
    """Add local model entries to payload when local endpoint is configured."""
    local_url = payload.pop("local_model_url", None)
    local_models = payload.pop("local_models", None)
    if not local_url or not local_models:
        return payload

    if not isinstance(local_models, list):
        local_models = [local_models] if isinstance(local_models, str) else []

    extra_entries = payload.get("extra_entries", [])
    for model_id in local_models:
        extra_entries.append(
            {
                "model": model_id,
                "provider": "local",
                "base_url": local_url,
            }
        )
    payload["extra_entries"] = extra_entries
    return payload
