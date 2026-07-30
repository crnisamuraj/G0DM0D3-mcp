# godmod3-mcp

MCP bridge for [G0DM0D3](https://github.com/elder-plinius/G0DM0D3) with dedicated skills for **Odysseus** and **Hermes Agent**.

This package delegates 100% to a self-hosted G0DM0D3 API and exposes every flagship feature as an MCP tool:

- ULTRAPLINIAN multi-model racing
- CONSORTIUM hive-mind synthesis
- Single-chat with GODMODE / AutoTune / Parseltongue / STM
- AutoTune analysis, Parseltongue obfuscation, STM transforms
- Dataset + research endpoints
- Local OpenAI-compatible model support (Ollama, LM Studio, vLLM)

## Quick start

### Recommended deployment

Run the upstream G0DM0D3 API as a container, run a local stdio bridge for Hermes, and run a separate HTTP bridge container for Odysseus.

#### 1. Start the G0DM0D3 API container

```bash
cp .env.example .env
# edit .env with optional keys
docker compose -f docker-compose.api.yml up -d --build
```

The API is available at `http://localhost:7860` from the host and at `http://godmod3-api:7860` from containers on the shared `godmod3` network.

#### 2. Install the bridge locally for Hermes (stdio)

```bash
pip install -e .
```

This installs the bridge and the console script `godmod3-mcp`.

#### 3. Start the HTTP bridge container for Odysseus

```bash
docker compose -f docker-compose.bridge-http.yml up -d --build
```

Odysseus connects to `http://localhost:3001/sse`.

#### 4. Verify

```bash
python -m godmod3_mcp.server --test
```

### Alternative: run the API directly

If you prefer not to containerize the API:

```bash
git clone https://github.com/elder-plinius/G0DM0D3.git
cd G0DM0D3
npm install
npm run api
```

### Alternative: full stack at once

```bash
docker compose up -d --build
```

This is equivalent to starting both `docker-compose.api.yml` and `docker-compose.bridge-http.yml` together.

## Configuration

| Variable | Default | Description |
|---|---|---|
| `GODMOD3_BASE_URL` | `http://localhost:7860` | G0DM0D3 API endpoint |
| `GODMOD3_API_KEY` | *(none)* | Bearer token if API requires auth |
| `GODMOD3_MCP_TRANSPORT` | `stdio` | `stdio`, `http`, or `sse` |
| `GODMOD3_MCP_HTTP_PORT` | `3001` | HTTP/SSE listen port |

## MCP Tools

- `health_check`
- `server_info`
- `list_models`
- `get_tier`
- `single_chat`
- `ultraplinian_chat`
- `consortium_chat`
- `autotune_analyze`
- `parseltongue_encode`
- `parseltongue_detect`
- `transform_text`
- `submit_feedback`
- `dataset_stats`
- `export_dataset`
- `research_info`
- `research_stats`
- `research_query`

## Connect to Odysseus

Via the MCP admin UI or API:

```json
{
  "name": "godmod3",
  "transport": "stdio",
  "command": "python",
  "args": ["-m", "godmod3_mcp.server"],
  "env": {
    "GODMOD3_BASE_URL": "http://localhost:7860",
    "GODMOD3_API_KEY": "optional-key"
  }
}
```

Or via the HTTP bridge container:

```json
{
  "name": "godmod3",
  "transport": "http",
  "url": "http://localhost:3001/sse"
}
```

Install the skill:

```bash
cp -r skills/odysseus/godmod3 /path/to/odysseus/data/skills/
```

## Connect to Hermes Agent

Hermes launches the bridge as a local stdio subprocess. Make sure you installed the bridge with `pip install -e .` and that the API container is exposing port `7860`.

Add to your Hermes MCP config (file path depends on install; often `~/.hermes/mcp_servers.json` or via `hermes config`):

```json
{
  "godmod3": {
    "command": "godmod3-mcp",
    "env": {
      "GODMOD3_BASE_URL": "http://localhost:7860",
      "GODMOD3_API_KEY": "optional-key"
    }
  }
}
```

Install the skill:

```bash
cp -r skills/hermes/godmod3 ~/.hermes/skills/
```

Then invoke with `/godmod3`.

## Local model support

Pass `local_model_url` and `local_models` to any chat tool:

```json
{
  "messages": [{"role": "user", "content": "Hello"}],
  "local_model_url": "http://localhost:11434/v1",
  "local_models": ["qwen3:8b"],
  "provider_preference": "all"
}
```

## Tests

```bash
pytest tests/test_tools.py
```

## License

AGPL-3.0-or-later — same as G0DM0D3.
