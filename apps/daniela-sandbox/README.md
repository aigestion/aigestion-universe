# daniela-sandbox

Isolated code/shell execution for Daniela OS. Backs the
`run_shell` tool in the tools-gateway.

## Why

- **Pluggable isolation** — process (fast, weak) or Docker
  (ephemeral, read-only, no-network, strong).
- **Resource limits** — timeout, output cap, memory cap.
- **Network isolation** — `--network none` by default.
- **Audit** — every execution is logged in a hash-chained,
  tamper-evident ledger (`/audit/verify`).
- **Secret redaction** — API keys/tokens are redacted before
  they hit the audit log.

## Quick start

```bash
cp .env.example .env
uv sync --extra dev
uvicorn services.sandbox:create_app --factory --port 8090
```

## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | executor availability + isolation level |
| POST | `/exec` | run a shell command with limits |
| POST | `/python` | run a Python snippet |
| GET | `/audit` | recent executions |
| GET | `/audit/verify` | verify the hash chain is intact |

## Executors

### process (default)
Fast, low-overhead subprocess. Applies `RLIMIT_CPU` /
`RLIMIT_AS` on Unix. **Not a security boundary** — only use
for trusted commands.

### docker (strong)
Runs each command in an ephemeral container:
`--network none`, `--memory`, `--read-only`, `--tmpfs`,
`--user nobody`, `--pids-limit`. Requires the Docker daemon.

## Example

```bash
curl -X POST http://localhost:8090/exec \
  -H "Content-Type: application/json" \
  -d '{
    "command": "echo hello && python -c "print(2+2)"",
    "backend": "process",
    "timeout_s": 10
  }'
```

## Security model

1. Default backend is `process`; opt into `docker` for
   untrusted code.
2. Network is **off by default** (`network_allowed: false`).
3. Output is capped (`max_output_bytes`) to prevent memory
   exhaustion via a runaway process.
4. Every execution is audit-logged and hash-chained.
5. Secrets in the command string are redacted before logging.

## Production hardening

- Run the sandbox itself in a container/VM with minimal
  privileges.
- Prefer the Docker executor, or a dedicated sandbox VM
  (gVisor / Firecracker) for stronger isolation.
- Mount the audit log to a write-once store.
- Inject executor config from a secret manager, not `.env`.
