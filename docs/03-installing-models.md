# 03 — Installing & connecting models

PurpleMCP talks to **local** models (Ollama) and **cloud** models (Anthropic,
OpenAI, Gemini, OpenRouter) through the same interface. You bring the keys; only
configure the ones you want.

```bash
cp .env.example .env     # then edit
purplemcp providers      # shows which are ready
```

## Local: Ollama

No key needed — just have Ollama running.

```bash
ollama serve             # if not already running
ollama pull llama3.1     # a TOOL-CAPABLE model (important!)
purplemcp ask "19% of 4200?" -p ollama -m llama3.1 -s calculator
```

> [!IMPORTANT]
> **Not every local model supports tool calling.** Code/FIM models like
> `codestral` return `does not support tools (400)`. Use a tool-capable model:
> `llama3.1`, `llama3.2`, `qwen2.5`, `mistral-nemo`, `firefunction-v2`, etc.
> `.env` sets `OLLAMA_MODEL`; override per command with `-m`.

## Cloud (bring your own key)

Put the key in `.env`, then select the provider with `-p`:

| Provider | `.env` keys | Example |
| --- | --- | --- |
| Anthropic | `ANTHROPIC_API_KEY`, `ANTHROPIC_MODEL` | `-p anthropic` |
| OpenAI | `OPENAI_API_KEY`, `OPENAI_MODEL` | `-p openai` |
| Gemini | `GEMINI_API_KEY`, `GEMINI_MODEL` | `-p gemini` |
| OpenRouter | `OPENROUTER_API_KEY`, `OPENROUTER_MODEL` | `-p openrouter` |

```bash
purplemcp ask "summarize my notes" -p anthropic -s notes
purplemcp chat -p openai -s calculator -s notes        # multi-server chat
```

OpenRouter is handy for trying many models behind one key — set
`OPENROUTER_MODEL` to e.g. `anthropic/claude-3.5-sonnet` or `meta-llama/llama-3.1-70b-instruct`.

## Installing a server into another host (e.g. Claude Desktop)

```bash
purplemcp install claude-desktop -s calculator   # merges into the config (with backup)
purplemcp install print -s calculator            # just prints the JSON snippet
```

## Tips for tool use with smaller local models
- Smaller models call tools less reliably — be explicit ("use the `percent_of`
  tool").
- Keep the number of tools in one session small.
- Bump `--max-steps` if a multi-tool task gets cut off.

Next: [04 — attack catalog](04-attack-catalog.md).
