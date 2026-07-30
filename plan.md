# G0DM0D3 MCP Wrapper + Skills Plan

## Goal
Expose the full G0DM0D3 feature set inside **Odysseus** and **Hermes Agent** via a Python MCP server that delegates 100% to a self-hosted G0DM0D3 API instance, plus dedicated skills for each agent.

## Architecture

```
Odysseus / Hermes Agent
        │
        │ MCP (stdio or HTTP/SSE)
        ▼
┌─────────────────────┐
│   godmod3-mcp       │   Python MCP bridge (this repo)
│   (MCP server)      │
└──────────┬──────────┘
           │ HTTP REST
           ▼
┌─────────────────────┐
│   godmod3-api       │   github.com/elder-plinius/G0DM0D3 api/
│   (Node/Express)    │
└─────────────────────┘
```

## Deployment modes

- **stdio** — easy local/CLI integration for both agents.
- **HTTP/SSE** — shared/remote service, better for Docker stacks and multi-host setups.
- A single package supports both. Transport chosen via env var / CLI arg. Both modes use the official `mcp` Python SDK.

## Default configuration

| Variable | Default | Purpose |
|---|---|---|
| `GODMOD3_BASE_URL` | `http://localhost:7860` | G0DM0D3 API endpoint |
| `GODMOD3_API_KEY` | *(none)* | Bearer token if your API requires auth |
| `GODMOD3_MCP_TRANSPORT` | `stdio` | `stdio`, `http`, or `sse` |
| `GODMOD3_MCP_HTTP_PORT` | `3001` | HTTP/SSE listen port |

## MCP tools

### Chat engines

| Tool | Endpoint | Notes |
|---|---|---|
| `ultraplinian_chat` | `POST /v1/ultraplinian/completions` | Multi-model race; aggregates SSE liquid response |
| `consortium_chat` | `POST /v1/consortium/completions` | Hive-mind synthesis; aggregates SSE events |
| `single_chat` | `POST /v1/chat/completions` | Single-model with GODMODE/AutoTune/Parseltongue/STM |

### Utilities

| Tool | Endpoint |
|---|---|
| `autotune_analyze` | `POST /v1/autotune/analyze` |
| `parseltongue_encode` | `POST /v1/parseltongue/encode` |
| `parseltongue_detect` | `POST /v1/parseltongue/detect` |
| `transform_text` | `POST /v1/transform` |
| `submit_feedback` | `POST /v1/feedback` |

### Discovery / status

| Tool | Endpoint |
|---|---|
| `server_info` | `GET /v1/info` |
| `list_models` | `GET /v1/models` |
| `get_tier` | `GET /v1/tier` |
| `health_check` | `GET /v1/health` |

### Dataset / research

| Tool | Endpoint | Tier |
|---|---|---|
| `dataset_stats` | `GET /v1/dataset/stats` | Pro+ |
| `export_dataset` | `GET /v1/dataset/export` | Pro+ |
| `research_info` | `GET /v1/research/info` | Pro+ |
| `research_stats` | `GET /v1/research/stats` | Pro+ |
| `research_query` | `GET /v1/research/query` | Enterprise |

## Local endpoint support

All chat tools accept:

- `local_model_url` — e.g. `http://localhost:11434/v1`
- `local_models` — list of local model IDs
- `provider_preference` — `openrouter`, `venice`, `local`, or `all`

## Streaming handling

G0DM0D3 streams SSE by default. The bridge parses events and returns a single text result plus metadata to Odysseus/Hermes.

## Files to create

| File | Purpose |
|---|---|
| `src/godmod3_mcp/server.py` | MCP server entry (stdio + HTTP/SSE) |
| `src/godmod3_mcp/client.py` | Typed G0DM0D3 REST client |
| `src/godmod3_mcp/config.py` | Env/config handling |
| `src/godmod3_mcp/tools.py` | Tool schema definitions |
| `src/godmod3_mcp/utils.py` | SSE aggregation, response formatting |
| `src/godmod3_mcp/transports.py` | stdio + HTTP/SSE bootstrap |
| `pyproject.toml` | Package config |
| `requirements.txt` | Dependencies |
| `Dockerfile` | Container for godmod3-mcp bridge |
| `docker-compose.yml` | godmod3-api + godmod3-mcp stack |
| `.env.example` | Env vars documentation |
| `tests/test_tools.py` | Integration test scaffold |
| `skills/odysseus/godmod3/SKILL.md` | Odysseus-specific skill |
| `skills/hermes/godmod3/SKILL.md` | Hermes-specific skill |
| `README.md` | Setup for both agents |
| `plan.html` | ADHD-friendly interactive version of this plan |

## Docker services

- `godmod3-api` — builds `elder-plinius/G0DM0D3` API, exposes port `7860`.
- `godmod3-mcp` — builds this bridge, exposes HTTP MCP on configurable port (default `3001`).

## Skills

### Odysseus

Install into `data/skills/godmod3/SKILL.md` (Odysseus skill directory).

Body tailored to Odysseus agent conventions:
- Slash commands
- MCP tool namespacing (`mcp__godmod3__...`)
- Plan mode / tool approval awareness

### Hermes

Install into `~/.hermes/skills/godmod3/SKILL.md` (Hermes skill directory).

Body tailored to Hermes conventions:
- `/<skill>` invocation
- Tool Gateway support
- Native function-calling style

Both skills cover:

- **When to use ULTRAPLINIAN** — fastest best single answer.
- **When to use CONSORTIUM** — high-confidence, consensus-grounded synthesis (~30–60s).
- **When to use single chat** — direct controlled completion.
- **Tier selection** — `fast` for speed/cost, `smart` for quality, `power`/`ultra` for frontier coverage.
- **Parseltongue** — red-team / bypass trigger-word obfuscation.
- **STM modules** — `hedge_reducer`, `direct_mode`, `casual_mode`.
- **Local-only mode** — requires Ollama/LM Studio/vLLM running.
- **Feedback loop** — submit ratings to improve AutoTune.

## Verification checklist

1. Start `godmod3-api`.
2. Run bridge in stdio mode: `python -m godmod3_mcp.server`.
3. Test HTTP/SSE mode: `python -m godmod3_mcp.server --transport http`.
4. Add to Odysseus MCP servers; verify tools appear.
5. Add to Hermes MCP config; verify skill invocation.
6. Run `pytest tests/test_tools.py`.

## Next step

Implement the package, skills, Docker stack, and tests.
