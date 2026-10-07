# daniela-tools-gateway

BYOK tool/MCP unification gateway for Daniela OS.

Routes LLM calls and tool invocations to **any** provider —
OpenAI, Anthropic, Google, or a local LLM — using **your
own API keys**. Applies **zero markup** on token costs:
what the provider charges is exactly what you see in `/usage`.

## Why

- **One interface, every backend.** Swap OpenAI ↔ Anthropic ↔ Gemini ↔ local without code changes.
- **Zero markup.** Cost ledger shows raw provider cost. No hidden fees.
- **MCP-compatible.** `/mcp` speaks JSON-RPC (`tools/list`, `tools/call`).
- **BYOK.** Keys live in your secret manager / HSM, never in the repo.

## Quick start

```bash
cp .env.example .env        # fill OPENAI_API_KEY etc.
uv sync --extra dev
uvicorn services.tools_gateway:create_app --factory --port 8083
```

## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | health + markup flag |
| POST | `/chat/completions` | unified completion (provider/model optional) |
| GET | `/providers` | list providers + configured status |
| POST | `/keys` | inject a provider key (in-memory; use secret manager in prod) |
| GET | `/tools` | list registered tools |
| POST | `/tools/register` | register a custom tool |
| POST | `/tools/call` | invoke a tool |
| GET | `/usage` | token/cost summary (zero markup) |
| GET | `/usage/records` | per-call usage ledger |
| POST | `/mcp` | MCP JSON-RPC endpoint (`tools/list`, `tools/call`) |

## Providers

Adapters live in `services/providers/` and implement a common
`Provider` protocol (`complete()` → `ProviderResponse`). Each
adapter carries its own per-1k-token pricing so cost is
computed accurately with zero markup.

- **OpenAI** — `gpt-4o`, `gpt-4o-mini`, `gpt-4-turbo`, `gpt-3.5-turbo`
- **Anthropic** — `claude-3-5-sonnet`, `claude-3-5-haiku`, `claude-3-opus`, …
- **Google** — `gemini-1.5-flash`, `gemini-1.5-pro`, `gemini-2.0-flash`
- **Local** — any OpenAI-compatible server (llama.cpp, vLLM, Ollama). Free.

## Routing

Explicit `provider` in the request wins. Otherwise the gateway
prefers **local** (free, on-prem) and falls back to the first
configured cloud provider.

## Cost transparency

Every completion is recorded in an append-only ledger with
prompt/completion tokens and the raw USD cost. `GET /usage`
aggregates by provider. `markup_applied` is always `false`
unless `ALLOW_MARKUP=true` (not recommended).

## Security

- Keys are held in memory only in this scaffold; in production
  inject them from a secret manager or HSM (FIPS 140-3 L3).
- Never commit `.env` or real keys.
