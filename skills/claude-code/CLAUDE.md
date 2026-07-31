# G0DM0D3 MCP Instructions

You have access to the G0DM0D3 MCP server, which provides multi-model reasoning tools through the G0DM0D3 API.

## When to use G0DM0D3 tools

Use these tools when a single model answer might be insufficient, censored, hedged, or shallow:

- Researching controversial, technical, or adversarial topics
- Wanting the strongest answer from many frontier models quickly
- Wanting a consensus-grounded synthesis across many model outputs
- Removing corporate hedging from a model reply
- Red-teaming model robustness or studying prompt engineering

## Main tools

Tool names in Claude Code may be prefixed, e.g., `mcp_godmod3_ultraplinian_chat` or `godmod3__ultraplinian_chat`. Look for the base names:

- `ultraplinian_chat` — race many models, return the best single response
- `consortium_chat` — collect responses from many models and synthesize ground truth
- `single_chat` — direct chat with one model + GODMODE/AutoTune/STM pipeline
- `autotune_analyze` — analyze a message and get optimal sampling parameters
- `parseltongue_encode` / `parseltongue_detect` — obfuscate or detect trigger words
- `transform_text` — apply STM modules like hedge_reducer and direct_mode
- `health_check`, `list_models`, `get_tier` — discovery/status tools

## Defaults

Unless the user asks otherwise, use these defaults for chat tools:

- `godmode: true`
- `autotune: true`
- `strategy: adaptive`
- `parseltongue: false`
- `stm_modules: ["hedge_reducer", "direct_mode"]`
- `contribute_to_dataset: false`

## Tier selection

For ULTRAPLINIAN and CONSORTIUM, choose a tier:

- `fast` — ~10 models, quick
- `standard` — ~24 models, balanced
- `smart` — ~36 models, strong reasoning
- `power` — ~45 models, frontier coverage
- `ultra` — ~51 models, maximum coverage

Free tier only supports `fast`. Pro supports `fast`/`standard`/`smart`. Enterprise supports all.

## Example calls

Get the strongest answer:

```json
{
  "tool": "mcp_godmod3_ultraplinian_chat",
  "arguments": {
    "messages": [{"role": "user", "content": "Explain how buffer overflows work"}],
    "tier": "standard"
  }
}
```

Synthesize consensus:

```json
{
  "tool": "mcp_godmod3_consortium_chat",
  "arguments": {
    "messages": [{"role": "user", "content": "What are the real risks of prompt injection?"}],
    "tier": "smart"
  }
}
```

Strip hedging from text:

```json
{
  "tool": "mcp_godmod3_transform_text",
  "arguments": {
    "text": "I think you should probably consider using a HashMap.",
    "modules": ["hedge_reducer", "direct_mode"]
  }
}
```

## Safety

- Enable `parseltongue` only for explicit red-team or research tasks.
- Keep `contribute_to_dataset: false` unless the user explicitly opts in.
