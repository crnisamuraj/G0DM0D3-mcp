# Agent Guide for godmod3-mcp

This file is written for AI coding agents. It assumes no prior knowledge of the project.

## Project overview

`godmod3-mcp` is a Python [Model Context Protocol (MCP)](https://modelcontextprotocol.io) bridge for the self-hosted [G0DM0D3](https://github.com/elder-plinius/G0DM0D3) API. It exposes every flagship G0DM0D3 feature as an MCP tool so that agent frameworks (primarily **Odysseus** and **Hermes Agent**) can call them.

The bridge is a thin, stateless adapter: it does not implement model routing, prompt engineering, or dataset logic itself. It forwards requests over HTTP to a G0DM0D3 API instance and formats the responses for MCP clients.

Key capabilities exposed through MCP tools:

- Multi-model racing via `ultraplinian_chat`
- Hive-mind synthesis via `consortium_chat`
- Single-model chat with GODMODE / AutoTune / Parseltongue / STM via `single_chat`
- AutoTune analysis, Parseltongue encode/detect, STM transforms
- Dataset and research endpoints
- Local OpenAI-compatible model support (Ollama, LM Studio, vLLM)

The package supports both `stdio` and `HTTP/SSE` MCP transports using the official `mcp` Python SDK.

- **Version:** 0.1.0
- **License:** AGPL-3.0-or-later
- **Python:** >=3.10
- **Build backend:** hatchling

## Repository layout

```
├── src/godmod3_mcp/          # Main Python package
│   ├── __init__.py           # Public exports: Config, Godmod3Client, Godmod3ClientError, main
│   ├── __main__.py           # `python -m godmod3_mcp.server` shim
│   ├── server.py             # CLI entry point, transport selection, tool registration
│   ├── client.py             # Async HTTP client for the G0DM0D3 REST API
│   ├── config.py             # Environment-based configuration dataclass
│   ├── tools.py              # MCP tool definitions and payload builders
│   ├── utils.py              # SSE aggregation, response formatting, message normalization
│   └── transports.py         # FastMCP server bootstrap with lifespan-managed client
├── skills/
│   ├── odysseus/godmod3/SKILL.md   # Odysseus-specific skill instructions
│   ├── hermes/godmod3/SKILL.md     # Hermes Agent-specific skill instructions
│   ├── generic-mcp/SKILL.md        # Generic instructions for any MCP client
│   ├── claude-code/CLAUDE.md       # Claude Code project instructions
│   ├── cursor/.cursorrules         # Cursor rules
│   └── codex/CODEX.md              # Codex system prompt
├── tests/
│   ├── test_tools.py         # pytest-compatible async unit tests
│   └── conftest.py           # Test helpers (make_config, run_async, run_sync)
├── pyproject.toml            # Package metadata, dependencies, build config, pytest options
├── requirements.txt          # Runtime deps (httpx + official `mcp` SDK)
├── requirements-http.txt     # Deprecated alias; `mcp` is now in requirements.txt
├── Dockerfile                     # Container image for the bridge
├── Dockerfile.api                 # Patched upstream G0DM0D3 API container
├── docker-compose.yml             # Full stack: includes API + HTTP bridge
├── docker-compose.api.yml         # G0DM0D3 API container only
├── docker-compose.bridge-http.yml # HTTP/SSE MCP bridge container only
├── .env.example                   # Documented environment variables
├── README.md                 # Human-facing setup guide
├── plan.md                   # Original implementation plan
├── plan.html                 # Interactive rendered version of plan.md
└── build-report.html         # Build verification report
```

## Technology stack

- **Language:** Python 3.10+
- **HTTP client:** `httpx` (async)
- **MCP server:** `mcp.server.fastmcp.FastMCP`
- **Packaging:** hatchling, editable installs via `pip install -e .`
- **Containerization:** Docker / Docker Compose
- **Testing:** `pytest` + `pytest-asyncio`

## Build, install, and run commands

### Install for local development

```bash
pip install -e .
```

### Run the server

```bash
# stdio transport (default)
python -m godmod3_mcp.server

# HTTP/SSE transport
python -m godmod3_mcp.server --transport http --port 3001

# Print configuration and registered tool list, then exit
python -m godmod3_mcp.server --test
```

There is also a console script entry point:

```bash
godmod3-mcp --transport stdio
```

### Run with Docker Compose

The stack is split into two compose files so you can manage the API and the HTTP bridge independently.

Start only the G0DM0D3 API container (for use with a local stdio bridge for Hermes):

```bash
cp .env.example .env
# edit .env as needed
docker compose -f docker-compose.api.yml up -d --build
```

Start the HTTP/SSE MCP bridge container (for Odysseus):

```bash
docker compose -f docker-compose.bridge-http.yml up -d --build
```

Or start both at once:

```bash
docker compose up -d --build
```

- `docker-compose.api.yml` builds the upstream G0DM0D3 API as `godmod3-api` (host port 7860).
- `docker-compose.bridge-http.yml` builds this bridge as `godmod3-mcp-http` (host port 3001).
- The two containers share a Docker network named `godmod3`, so the bridge reaches the API at `http://godmod3-api:7860`.
- A local stdio bridge on the host reaches the API at `http://localhost:7860`.

`docker-compose.api.yml` uses the local `Dockerfile.api` instead of building directly from the upstream repo. The upstream API currently uses an Express route pattern (`/batch/*`) that is incompatible with recent `path-to-regexp` versions, causing the container to crash on startup. `Dockerfile.api` clones the upstream source and applies a compatibility patch before building.

### Avoiding upstream rate limits

The upstream API defaults to the **Free tier** (5 total requests, 10/min, 50/day). To use unlimited **Enterprise** tier locally, set an API key and assign it to the enterprise tier in `.env`:

```bash
GODMODE_API_KEY=my-local-key-123
GODMODE_TIER_KEYS=enterprise:my-local-key-123
GODMOD3_API_KEY=my-local-key-123
```

Then restart the API container. The bridge sends `GODMOD3_API_KEY` as the bearer token, and the upstream API maps it to the Enterprise tier via `GODMODE_TIER_KEYS`.

## Configuration

Configuration is loaded exclusively from environment variables in `src/godmod3_mcp/config.py` (`Config.from_env()`). CLI flags override environment values for transport and port.

| Variable | Default | Description |
|---|---|---|
| `GODMOD3_BASE_URL` | `http://localhost:7860` | G0DM0D3 API endpoint |
| `GODMOD3_API_KEY` | *(none)* | Bearer token if the API requires auth |
| `GODMOD3_MCP_TRANSPORT` | `stdio` | `stdio`, `http`, or `sse` |
| `GODMOD3_MCP_HTTP_PORT` | `3001` | HTTP/SSE listen port |
| `GODMOD3_TIMEOUT` | `120` | Request timeout in seconds |
| `GODMOD3_LOG_LEVEL` | `INFO` | Python logging level |

`.env.example` documents the same variables plus optional upstream keys (`OPENROUTER_API_KEY`, `HF_TOKEN`, `HF_DATASET_REPO`) that are forwarded to the G0DM0D3 API container.

## Testing instructions

Tests live in `tests/test_tools.py` and are written as plain `async def test_*` coroutines. Run them with pytest:

```bash
pytest tests/test_tools.py
```

`pyproject.toml` configures `asyncio_mode = auto` so the async tests are collected correctly when `pytest-asyncio` is installed.

### Verifying the server starts correctly

```bash
python -m godmod3_mcp.server --test
```

This prints the selected transport, the configured base URL, whether an API key is set, and the list of registered tools.

## Multi-client skill files

In addition to the Hermes and Odysseus skills, the repo includes generic instructions for other MCP clients under `skills/`:

- `skills/generic-mcp/SKILL.md` — usable with any MCP client
- `skills/claude-code/CLAUDE.md` — Claude Code project instructions
- `skills/cursor/.cursorrules` — Cursor rules
- `skills/codex/CODEX.md` — Codex system prompt

When adding or changing tool behavior, update all relevant skill files so instructions stay consistent across clients.

## Code style guidelines

- Use `from __future__ import annotations` at the top of every module.
- Use type hints throughout; prefer `str | None` union syntax and `list[...]` generic syntax (Python 3.10+).
- Prefer `dict[str, Any]` for loose JSON-like structures.
- Use `logging.getLogger(__name__)` rather than print statements.
- Keep tool functions in `tools.py` focused on request building and response formatting; all HTTP logic belongs in `client.py`.
- Do not introduce new third-party dependencies unless the capability is genuinely missing and justified. The runtime depends on `httpx` and the official `mcp` SDK.
- Preserve the existing two-agent skill structure under `skills/odysseus/godmod3/` and `skills/hermes/godmod3/`.

## Security considerations

- **API keys are passed via environment variables.** Never commit real keys to the repository. `.gitignore` already excludes `.env`.
- **Bearer tokens are sent on every authenticated request.** The client attaches the `Authorization: Bearer <GODMOD3_API_KEY>` header for all endpoints except `health`, `info`, and `list_models`.
- **No built-in request signing or TLS verification bypass.** If the upstream API is remote, use an HTTPS `GODMOD3_BASE_URL`.
- **Dataset contribution is opt-in.** Chat tools accept `contribute_to_dataset=false` by default. Changing this to `true` publishes conversation content to the upstream dataset/research corpus.
- **Parseltongue is a prompt obfuscation utility.** It is disabled by default and should only be enabled for explicit red-team or research use cases.
- **The bridge is a thin proxy.** It does not validate prompt content, filter outputs, or enforce rate limits. Those responsibilities live in the upstream G0DM0D3 API or the agent framework.
- **Container runs as root by default.** Harden the `Dockerfile` if deploying in a shared environment.

## MCP tools

All tools are registered in `src/godmod3_mcp/server.py` and implemented in `src/godmod3_mcp/tools.py`.

| Tool | G0DM0D3 endpoint | Purpose |
|---|---|---|
| `health_check` | `GET /v1/health` | API connectivity check |
| `server_info` | `GET /v1/info` | API metadata |
| `list_models` | `GET /v1/models` | Available models |
| `get_tier` | `GET /v1/tier` | Rate-limit tier and features |
| `single_chat` | `POST /v1/chat/completions` | Single-model chat |
| `ultraplinian_chat` | `POST /v1/ultraplinian/completions` | Multi-model race |
| `consortium_chat` | `POST /v1/consortium/completions` | Consensus synthesis |
| `autotune_analyze` | `POST /v1/autotune/analyze` | Sampling-parameter analysis |
| `parseltongue_encode` | `POST /v1/parseltongue/encode` | Trigger-word obfuscation |
| `parseltongue_detect` | `POST /v1/parseltongue/detect` | Trigger-word detection |
| `transform_text` | `POST /v1/transform` | STM text transformation |
| `submit_feedback` | `POST /v1/feedback` | AutoTune feedback |
| `dataset_stats` | `GET /v1/dataset/stats` | Dataset statistics |
| `export_dataset` | `GET /v1/dataset/export` | Dataset export (JSON/JSONL) |
| `research_info` | `GET /v1/research/info` | Research schema/repo info |
| `research_stats` | `GET /v1/research/stats` | Aggregate research stats |
| `research_query` | `GET /v1/research/query` | Filtered research query |

Streaming responses are aggregated in `utils.py` and returned as a single text result with optional metadata.

## Common development tasks

### Add a new MCP tool

1. Define the async function in `src/godmod3_mcp/tools.py`.
2. Accept `ctx: Context | None = None` and assert it is not `None` inside the body to access `ctx.request_context.lifespan_context["client"]`.
3. Add the function to the `tools` list in `src/godmod3_mcp/server.py::_attach_tools`.
4. Add a unit test in `tests/test_tools.py` if the tool has logic that can be tested without a live API.
5. Run both `pytest tests/test_tools.py` and `python -m godmod3_mcp.server --test` before committing.

### Modify the G0DM0D3 client

1. Edit or add methods in `src/godmod3_mcp/client.py`.
2. Keep methods typed, use `_request`/`_raw_request`/`_stream_sse` helpers, and raise `Godmod3ClientError` on failures.
3. Update `src/godmod3_mcp/__init__.py` if new public symbols are exported.

### Update dependencies

- Runtime dependencies: edit both `pyproject.toml` `[project] dependencies` and `requirements.txt`.

## Deployment notes

- The `Dockerfile` installs the package with `pip install -e .`. The default entrypoint runs in `stdio` mode; override `CMD` for HTTP/SSE.
- `docker-compose.yml` sets `GODMOD3_BASE_URL=http://godmod3-api:7860` inside the bridge container and waits for the API healthcheck before starting the bridge.

## Verification checklist after changes

1. `pytest tests/test_tools.py` passes.
2. `python -m godmod3_mcp.server --test` lists all expected tools and correct config.
3. `python -m godmod3_mcp.server --transport http --port 3001` starts without error.
4. If modifying skills, both `skills/odysseus/godmod3/SKILL.md` and `skills/hermes/godmod3/SKILL.md` remain internally consistent.
