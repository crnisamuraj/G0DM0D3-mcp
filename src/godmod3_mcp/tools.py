"""MCP tool definitions for G0DM0D3."""

from __future__ import annotations

from mcp.server.fastmcp import Context

from .client import Godmod3Client
from .utils import aggregate_stream, format_chat_response, merge_local_models, normalize_messages


# ---------------------------------------------------------------------------
# Discovery / status
# ---------------------------------------------------------------------------

async def health_check(ctx: Context) -> str:
    """Check connectivity to the G0DM0D3 API."""
    client: Godmod3Client = ctx.request_context.lifespan_context["client"]
    data = await client.health()
    return f"G0DM0D3 API status: {data.get('status')} at {client.config.base_url}"


async def server_info(ctx: Context) -> str:
    """Return G0DM0D3 API info, endpoints, and tier defaults."""
    client: Godmod3Client = ctx.request_context.lifespan_context["client"]
    data = await client.info()
    return format_chat_response(data)


async def list_models(ctx: Context) -> str:
    """List available models including virtual ULTRAPLINIAN/CONSORTIUM models."""
    client: Godmod3Client = ctx.request_context.lifespan_context["client"]
    data = await client.list_models()
    models = [m["id"] for m in data.get("data", [])]
    return "\n".join(models) or "No models found."


async def get_tier(ctx: Context) -> str:
    """Show your current G0DM0D3 API tier, limits, and features."""
    client: Godmod3Client = ctx.request_context.lifespan_context["client"]
    data = await client.get_tier()
    features = data.get("features", {})
    lines = [
        f"Tier: {data.get('label', data.get('tier'))}",
        f"Limits: {data.get('limits')}",
        f"ULTRAPLINIAN tiers: {features.get('ultraplinian_tiers')}",
        f"Research access: {features.get('research_access')}",
        f"Dataset export formats: {features.get('dataset_export_formats')}",
    ]
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Chat engines
# ---------------------------------------------------------------------------

async def single_chat(
    messages: list[dict[str, str]],
    model: str = "nousresearch/hermes-4-70b",
    openrouter_api_key: str | None = None,
    stream: bool = False,
    max_tokens: int = 4096,
    temperature: float | None = None,
    top_p: float | None = None,
    top_k: int | None = None,
    frequency_penalty: float | None = None,
    presence_penalty: float | None = None,
    repetition_penalty: float | None = None,
    godmode: bool = True,
    custom_system_prompt: str | None = None,
    autotune: bool = True,
    strategy: str = "adaptive",
    parseltongue: bool = True,
    parseltongue_technique: str = "leetspeak",
    parseltongue_intensity: str = "medium",
    stm_modules: list[str] | None = None,
    contribute_to_dataset: bool = False,
    local_model_url: str | None = None,
    local_models: list[str] | None = None,
    provider_preference: str = "openrouter",
    ctx: Context | None = None,
) -> str:
    """Single-model chat with the full G0DM0D3 pipeline (GODMODE, AutoTune, Parseltongue, STM)."""
    assert ctx is not None
    client: Godmod3Client = ctx.request_context.lifespan_context["client"]

    payload = _build_chat_payload(
        messages=messages,
        model=model,
        openrouter_api_key=openrouter_api_key,
        stream=stream,
        max_tokens=max_tokens,
        temperature=temperature,
        top_p=top_p,
        top_k=top_k,
        frequency_penalty=frequency_penalty,
        presence_penalty=presence_penalty,
        repetition_penalty=repetition_penalty,
        godmode=godmode,
        custom_system_prompt=custom_system_prompt,
        autotune=autotune,
        strategy=strategy,
        parseltongue=parseltongue,
        parseltongue_technique=parseltongue_technique,
        parseltongue_intensity=parseltongue_intensity,
        stm_modules=stm_modules,
        contribute_to_dataset=contribute_to_dataset,
        local_model_url=local_model_url,
        local_models=local_models,
        provider_preference=provider_preference,
    )
    return await _send_chat(client, "chat_completions", payload, stream, "single")


async def ultraplinian_chat(
    messages: list[dict[str, str]],
    tier: str = "standard",
    openrouter_api_key: str | None = None,
    venice_api_key: str | None = None,
    stream: bool = True,
    liquid_min_delta: int = 8,
    max_tokens: int = 4096,
    temperature: float | None = None,
    godmode: bool = True,
    autotune: bool = True,
    strategy: str = "adaptive",
    parseltongue: bool = True,
    parseltongue_technique: str = "leetspeak",
    parseltongue_intensity: str = "medium",
    stm_modules: list[str] | None = None,
    contribute_to_dataset: bool = False,
    local_model_url: str | None = None,
    local_models: list[str] | None = None,
    provider_preference: str = "openrouter",
    ctx: Context | None = None,
) -> str:
    """Race many models in parallel and return the best response (ULTRAPLINIAN)."""
    assert ctx is not None
    client: Godmod3Client = ctx.request_context.lifespan_context["client"]

    payload = _build_chat_payload(
        messages=messages,
        openrouter_api_key=openrouter_api_key,
        stream=stream,
        max_tokens=max_tokens,
        temperature=temperature,
        godmode=godmode,
        autotune=autotune,
        strategy=strategy,
        parseltongue=parseltongue,
        parseltongue_technique=parseltongue_technique,
        parseltongue_intensity=parseltongue_intensity,
        stm_modules=stm_modules,
        contribute_to_dataset=contribute_to_dataset,
        local_model_url=local_model_url,
        local_models=local_models,
        provider_preference=provider_preference,
    )
    payload["tier"] = tier
    payload["liquid_min_delta"] = liquid_min_delta
    if venice_api_key:
        payload["venice_api_key"] = venice_api_key

    return await _send_chat(client, "ultraplinian_completions", payload, stream, "ultraplinian")


async def consortium_chat(
    messages: list[dict[str, str]],
    tier: str = "standard",
    orchestrator_model: str = "anthropic/claude-sonnet-4.6",
    openrouter_api_key: str | None = None,
    stream: bool = True,
    max_tokens: int = 8192,
    godmode: bool = True,
    autotune: bool = True,
    strategy: str = "adaptive",
    parseltongue: bool = True,
    parseltongue_technique: str = "leetspeak",
    parseltongue_intensity: str = "medium",
    stm_modules: list[str] | None = None,
    contribute_to_dataset: bool = False,
    local_model_url: str | None = None,
    local_models: list[str] | None = None,
    provider_preference: str = "openrouter",
    ctx: Context | None = None,
) -> str:
    """Collect responses from all tier models and synthesize ground truth (CONSORTIUM)."""
    assert ctx is not None
    client: Godmod3Client = ctx.request_context.lifespan_context["client"]

    payload = _build_chat_payload(
        messages=messages,
        openrouter_api_key=openrouter_api_key,
        stream=stream,
        max_tokens=max_tokens,
        godmode=godmode,
        autotune=autotune,
        strategy=strategy,
        parseltongue=parseltongue,
        parseltongue_technique=parseltongue_technique,
        parseltongue_intensity=parseltongue_intensity,
        stm_modules=stm_modules,
        contribute_to_dataset=contribute_to_dataset,
        local_model_url=local_model_url,
        local_models=local_models,
        provider_preference=provider_preference,
    )
    payload["tier"] = tier
    payload["orchestrator_model"] = orchestrator_model

    return await _send_chat(client, "consortium_completions", payload, stream, "consortium")


# ---------------------------------------------------------------------------
# Utilities
# ---------------------------------------------------------------------------

async def coding_chat(
    prompt: str | list[dict[str, str]],
    engine: str = "ultraplinian",
    tier: str = "standard",
    parseltongue_intensity: str = "high",
    model: str | None = None,
    stream: bool = True,
    max_tokens: int = 4096,
    contribute_to_dataset: bool = False,
    ctx: Context | None = None,
) -> str:
    """Optimized coding assistant with heavy obfuscation and direct-mode STM.

    Defaults are tuned for tasks where a single frontier model might refuse or
    hedge: multi-model racing or consensus, GODMODE, AutoTune, leetspeak
    parseltongue, and hedge-reducing STM modules.
    """
    assert ctx is not None
    client: Godmod3Client = ctx.request_context.lifespan_context["client"]

    messages = normalize_messages(prompt)
    payload = _build_chat_payload(
        messages=messages,
        stream=stream,
        max_tokens=max_tokens,
        godmode=True,
        autotune=True,
        strategy="adaptive",
        parseltongue=True,
        parseltongue_technique="leetspeak",
        parseltongue_intensity=parseltongue_intensity,
        stm_modules=["hedge_reducer", "direct_mode"],
        contribute_to_dataset=contribute_to_dataset,
    )

    engine = engine.lower()
    if engine == "ultraplinian":
        payload["tier"] = tier
        payload["liquid_min_delta"] = 8
        return await _send_chat(client, "ultraplinian_completions", payload, stream, "ultraplinian")
    if engine == "consortium":
        payload["tier"] = tier
        payload["orchestrator_model"] = model or "anthropic/claude-sonnet-4.6"
        return await _send_chat(client, "consortium_completions", payload, stream, "consortium")

    payload["model"] = model or "nousresearch/hermes-4-70b"
    return await _send_chat(client, "chat_completions", payload, stream, "single")


async def autotune_analyze(
    message: str,
    conversation_history: list[dict[str, str]] | None = None,
    strategy: str = "adaptive",
    ctx: Context | None = None,
) -> str:
    """Analyze a message and get optimal LLM sampling parameters from AutoTune."""
    assert ctx is not None
    client: Godmod3Client = ctx.request_context.lifespan_context["client"]
    payload: dict[str, object] = {"message": message, "strategy": strategy}
    if conversation_history:
        payload["conversation_history"] = normalize_messages(conversation_history)
    data = await client.autotune_analyze(payload)
    detected = data.get("detected_context")
    params = data.get("params", {})
    lines = [f"Detected context: {detected}", f"Confidence: {data.get('confidence')}", ""]
    lines += [f"- {k}: {v}" for k, v in params.items()]
    return "\n".join(lines)


async def parseltongue_encode(
    text: str,
    technique: str = "leetspeak",
    intensity: str = "medium",
    custom_triggers: list[str] | None = None,
    ctx: Context | None = None,
) -> str:
    """Obfuscate trigger words in text."""
    assert ctx is not None
    client: Godmod3Client = ctx.request_context.lifespan_context["client"]
    payload: dict[str, object] = {"text": text, "technique": technique, "intensity": intensity}
    if custom_triggers:
        payload["custom_triggers"] = custom_triggers
    data = await client.parseltongue_encode(payload)
    return data.get("transformed_text", data.get("text", str(data)))


async def parseltongue_detect(
    text: str,
    custom_triggers: list[str] | None = None,
    ctx: Context | None = None,
) -> str:
    """Detect trigger words without transforming them."""
    assert ctx is not None
    client: Godmod3Client = ctx.request_context.lifespan_context["client"]
    payload: dict[str, object] = {"text": text}
    if custom_triggers:
        payload["custom_triggers"] = custom_triggers
    data = await client.parseltongue_detect(payload)
    triggers = data.get("triggers", data.get("triggers_found", []))
    if not triggers:
        return "No trigger words detected."
    return "Triggers detected: " + ", ".join(triggers)


async def transform_text(
    text: str,
    modules: list[str] | None = None,
    ctx: Context | None = None,
) -> str:
    """Apply semantic transformation modules (STM) to text."""
    assert ctx is not None
    client: Godmod3Client = ctx.request_context.lifespan_context["client"]
    payload: dict[str, object] = {"text": text}
    if modules:
        payload["modules"] = modules
    data = await client.transform_text(payload)
    return data.get("transformed_text", data.get("text", str(data)))


async def submit_feedback(
    message_id: str,
    rating: int,
    context_type: str = "analytical",
    params: dict[str, float] | None = None,
    response_text: str | None = None,
    ctx: Context | None = None,
) -> str:
    """Submit quality feedback for the AutoTune EMA learning loop."""
    assert ctx is not None
    client: Godmod3Client = ctx.request_context.lifespan_context["client"]
    payload: dict[str, object] = {
        "message_id": message_id,
        "context_type": context_type,
        "rating": rating,
    }
    if params:
        payload["params"] = params
    if response_text:
        payload["response_text"] = response_text
    data = await client.submit_feedback(payload)
    return f"Feedback submitted: {data}"


# ---------------------------------------------------------------------------
# Dataset / research
# ---------------------------------------------------------------------------

async def dataset_stats(ctx: Context) -> str:
    """Show in-memory dataset statistics."""
    client: Godmod3Client = ctx.request_context.lifespan_context["client"]
    data = await client.dataset_stats()
    return format_chat_response(data)


async def export_dataset(format: str = "json", ctx: Context | None = None) -> str:
    """Export the dataset as JSON or JSONL."""
    assert ctx is not None
    client: Godmod3Client = ctx.request_context.lifespan_context["client"]
    return await client.export_dataset(format=format)


async def research_info(ctx: Context) -> str:
    """Return research dataset schema and repository info."""
    client: Godmod3Client = ctx.request_context.lifespan_context["client"]
    data = await client.research_info()
    return format_chat_response(data)


async def research_stats(ctx: Context) -> str:
    """Return aggregate stats across published HuggingFace batches."""
    client: Godmod3Client = ctx.request_context.lifespan_context["client"]
    data = await client.research_stats()
    return format_chat_response(data)


async def research_query(
    category: str = "dataset",
    mode: str | None = None,
    model: str | None = None,
    since: int | None = None,
    until: int | None = None,
    limit: int = 50,
    offset: int = 0,
    ctx: Context | None = None,
) -> str:
    """Query the published research corpus with filters."""
    assert ctx is not None
    client: Godmod3Client = ctx.request_context.lifespan_context["client"]
    params: dict[str, object] = {"category": category, "limit": limit, "offset": offset}
    if mode:
        params["mode"] = mode
    if model:
        params["model"] = model
    if since is not None:
        params["since"] = since
    if until is not None:
        params["until"] = until
    data = await client.research_query(params)
    return format_chat_response(data)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _build_chat_payload(
    messages: list[dict[str, str]],
    *,
    model: str | None = None,
    openrouter_api_key: str | None = None,
    stream: bool = False,
    max_tokens: int = 4096,
    temperature: float | None = None,
    top_p: float | None = None,
    top_k: int | None = None,
    frequency_penalty: float | None = None,
    presence_penalty: float | None = None,
    repetition_penalty: float | None = None,
    godmode: bool = True,
    custom_system_prompt: str | None = None,
    autotune: bool = True,
    strategy: str = "adaptive",
    parseltongue: bool = True,
    parseltongue_technique: str = "leetspeak",
    parseltongue_intensity: str = "medium",
    stm_modules: list[str] | None = None,
    contribute_to_dataset: bool = False,
    local_model_url: str | None = None,
    local_models: list[str] | None = None,
    provider_preference: str = "openrouter",
) -> dict[str, object]:
    """Build a G0DM0D3 chat request payload from tool arguments."""
    payload: dict[str, object] = {
        "messages": normalize_messages(messages),
        "stream": stream,
        "max_tokens": max_tokens,
        "godmode": godmode,
        "autotune": autotune,
        "strategy": strategy,
        "parseltongue": parseltongue,
        "parseltongue_technique": parseltongue_technique,
        "parseltongue_intensity": parseltongue_intensity,
        "stm_modules": stm_modules if stm_modules is not None else ["hedge_reducer", "direct_mode"],
        "contribute_to_dataset": contribute_to_dataset,
        "provider_preference": provider_preference,
    }

    if model:
        payload["model"] = model
    if openrouter_api_key:
        payload["openrouter_api_key"] = openrouter_api_key
    if custom_system_prompt:
        payload["custom_system_prompt"] = custom_system_prompt
    if temperature is not None:
        payload["temperature"] = temperature
    if top_p is not None:
        payload["top_p"] = top_p
    if top_k is not None:
        payload["top_k"] = top_k
    if frequency_penalty is not None:
        payload["frequency_penalty"] = frequency_penalty
    if presence_penalty is not None:
        payload["presence_penalty"] = presence_penalty
    if repetition_penalty is not None:
        payload["repetition_penalty"] = repetition_penalty

    if local_model_url or local_models:
        payload["local_model_url"] = local_model_url
        payload["local_models"] = local_models
        payload = merge_local_models(payload)

    return payload


async def _send_chat(
    client: Godmod3Client,
    client_method_name: str,
    payload: dict[str, object],
    stream: bool,
    mode: str,
) -> str:
    """Send a chat request and return formatted text for the agent."""
    client_method = getattr(client, client_method_name)
    result = await client_method(payload)

    if stream:
        aggregated = await aggregate_stream(result, mode=mode)
        content = aggregated["content"]
        metadata = aggregated.get("metadata", {})
        meta_text = _render_metadata(metadata, mode)
        return f"{content}\n\n{meta_text}" if meta_text else content

    return format_chat_response(result)


def _render_metadata(metadata: dict[str, object], mode: str) -> str:
    """Render brief metadata summary for agent consumption."""
    lines: list[str] = []
    if mode == "ultraplinian":
        winner = metadata.get("winner") if isinstance(metadata.get("winner"), dict) else None
        race = metadata.get("race") if isinstance(metadata.get("race"), dict) else None
        if winner:
            lines.append(f"**Winner:** {winner.get('model')} (score {winner.get('score')})")
        if race:
            lines.append(
                f"**Race:** {race.get('models_succeeded')}/{race.get('models_queried')} "
                f"models in {race.get('total_duration_ms')}ms"
            )
    elif mode == "consortium":
        orch = metadata.get("orchestrator") if isinstance(metadata.get("orchestrator"), dict) else None
        if orch:
            lines.append(f"**Orchestrator:** {orch.get('model')} ({orch.get('duration_ms')}ms)")
        coll = metadata.get("collection") if isinstance(metadata.get("collection"), dict) else None
        if coll:
            lines.append(
                f"**Collection:** {coll.get('models_succeeded')}/{coll.get('models_queried')} "
                f"models in {coll.get('total_duration_ms')}ms"
            )
    params = metadata.get("params_used") if isinstance(metadata.get("params_used"), dict) else None
    if params:
        lines.append(f"**Params:** {', '.join(f'{k}={v}' for k, v in params.items())}")
    return "\n".join(lines)
