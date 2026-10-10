# Hermes Agent — Error Audit (2026-09-20)

## TL;DR
Hermes is stuck in a self-restart loop and its LLM calls fail because the **OpenRouter API key is invalid (HTTP 401 "User not found")**. A stale Groq fallback model also 404s. The rest are secondary/transient.

## Error inventory (by severity)

### 🔴 CRÍTICO — OpenRouter API key inválida
- `hermes\logs\agent.log`: `openai.AuthenticationError: Error code: 401 - {'error': {'message': 'User not found.'}}`
  provider=`openrouter` base_url=`https://openrouter.ai/api/v1` model=`nvidia/nemotron-3-super-120b-a12b:free`
- Means **every LLM call from Hermes fails** → the agent can't think/respond. This is the root cause of "hermes da errores".
- Configured in `C:\Users\Alejandro\AppData\Local\hermes\.env` (key var likely `OPENROUTER_API_KEY` / `HERMES_OPENROUTER_KEY`).
- **Fix:** put a *valid* OpenRouter key in that `.env`. Get one at openrouter.ai/keys.

### 🟠 ALTO — Modelo Groq obsoleto en el fallback
- `agent.log`: `openai.NotFoundError: 404 - The model 'llama-3.3-70b-versatile' does not exist or you do not have access to it.`
  provider=`groq` base_url=`https://api.groq.com/openai/v1`
- That model was removed from Groq; the fallback chain dies. **Fix:** replace `llama-3.3-70b-versatile` with a current Groq model (e.g. `llama-3.1-8b-instant`) in the Hermes model/fallback config.

### 🟡 MEDIO — Bucle de reinicio del gateway (exit code 75)
- `hermes\logs\gateway-exit-diag.log`: repeated `asyncio.run.SystemExit ... code: 75` raised in `_resolve_gateway_exit_verdict`.
- `hermes\logs\errors.log`: `gateway.lifecycle_ledger: Previous gateway life ... exited UNCLEANLY (no exit path ran — SIGKILL ...)`.
- `gateway-starts.log`: ~40 start timestamps between 09-19 and 09-20 → constant restart.
- There are `state-snapshots/*-pre-update`, a `fleet_restart_pending` flag, and `update.log` → Hermes is in a **self-update / self-replace loop** (the `--replace` restarts). The failed auth (above) very likely keeps the update/health check from completing, so it loops.
- **Fix:** resolve the API key first; if the loop persists afterwards, clear the stuck `fleet_restart_pending` flag and review `update.log`.

### 🟡 MEDIO — PermissionError / Acceso denegado (transitorio)
- `agent.log`: `PermissionError: [Errno 13] Permission denied: '...\hermes\auth.json'`
- `errors.log`: `Failed to prune snapshot ... [WinError 5] Acceso denegado: '...\state-snapshots\20260919-222037-pre-update'`
- **ACLs are fine** (`icacls` shows ALEXPC\Alejandro = (F) Full Control on both). These are transient file locks from the restart loop racing on the same files. They should stop once the restart loop is fixed.

### 🟢 BAJO — Disk I/O error
- `errors.log`: `tools.process_registry: Could not restore async delegation completions: disk I/O error`
- Flag for disk health. Run `chkdsk C: /scan` (elevated) if it recurs.

### ⚪ INFO — DanielaOS api_gateway 404 /v1/models (benigno)
- `aig\service_stderr.log`: `GET /v1/models` → 404, repeatedly.
- The `aig API Gateway v1.0` is actually **running** (`Core: CONECTADO`). It just doesn't implement the OpenAI-style `/v1/models` route (it serves `/api/*`). Something is probing it for that endpoint. Not a crash.

## What was verified (no action needed)
- File permissions on `auth.json` and `state-snapshots` are correct.
- No `taskkill`/`pkill` in your `aig` scripts is killing Hermes — the kill/restart is Hermes's own supervisor.
- Ollama is running; LM Studio is not (not required).

## Recommended actions (in order)
1. **Set a valid OpenRouter API key** in `C:\Users\Alejandro\AppData\Local\hermes\.env`. (Resolves the 401 — the main break.)
2. **Update the Groq fallback model** from `llama-3.3-70b-versatile` to a current model.
3. Restart Hermes; confirm the gateway stops looping (no new `previous_unclean_exit` in `errors.log`).
4. If the loop persists, inspect/clear `fleet_restart_pending` and `update.log`.
5. Run `chkdsk C: /scan` if disk I/O errors recur.

---

## RESOLUTION — 2026-09-20 (session 2)

### What was actually done
- **Valid OpenRouter key written to `.env`** (user-supplied). Verified three ways:
  1. On-disk SHA256 of the `OPENROUTER_API_KEY` value matches the user's key exactly.
  2. Direct `GET https://openrouter.ai/api/v1/models` with `Authorization: Bearer <key>` → **HTTP 200, 446 models**. The key is valid.
  3. `auth.json` exhaustion cache for openrouter was cleared (`last_status`/`last_error_code` now `null`).
- **Key also registered via `hermes auth add openrouter --type api-key`** → stored as credential #2 (manual) in `auth.json` (`access_token` field, `request_count: 0`).

### Why Hermes still errors (the remaining blocker)
- The live gateway runs as the **NSSM service `AIGateway`** (`C:\Tools\nssm\nssm-2.24\win64\nssm.exe`, PID 4156 → python 21660 → 21576, listening on `:8080`). It loaded the **old invalid key at startup** and cached `last_status: exhausted / 401`. It will NOT hot-reload `.env`/auth.json — it only reads `env:OPENROUTER_API_KEY` at process start.
- `hermes auth status openrouter` → `logged out`; fresh gateway logs `credential pool: no available entries`. The gateway's in-memory pool does not pick up `manual` auth.json credentials in this version — only the `env:`-sourced one (#1), which is stale until restart.
- **`Restart-Service AIGateway`, `nssm restart AIGateway`, and `Stop-Process` on the gateway are all denied (`Acceso denegado`)** as the current user — the service runs under SYSTEM. A restart needs an elevated (Run as Administrator) prompt.
- NOTE: `hermes gateway restart` does NOT control the NSSM service. It spawns a *separate* scheduled-task gateway (`Hermes_Gateway`) that **does not load `.env`** and therefore also shows `logged out`. That duplicate is harmless but redundant; leave it or disable the task (see below).

### Action required from the user (elevated PowerShell)
The data is fixed; the running gateway just needs to reload it. Run as **Administrator**:

```powershell
# Reload .env (now contains the valid key) into the gateway
nssm restart AIGateway
# or: Restart-Service AIGateway

# Optional: stop the redundant scheduled-task gateway that doesn't load .env
Disable-ScheduledTask -TaskName "Hermes_Gateway"
```

After `nssm restart AIGateway` the gateway reloads `OPENROUTER_API_KEY` from `.env` → OpenRouter returns 200 → the 401 disappears and the restart loop should settle.

### Secondary (still pending)
- **Groq fallback `llama-3.3-70b-versatile` → 404** (model removed from Groq). Only matters if OpenRouter fails and the Groq fallback is tried. Replace with a current model (e.g. `llama-3.1-8b-instant`) in the Hermes fallback config if it recurs.

### Display note
The environment redacts `sk-or-v1-…` secrets in tool transcripts (shows masks like `i5-z261027785…` / `jv-de-i5-…`). Files on disk contain the **real** values — verified by hash. Don't be alarmed by masked output.

---

### FOLLOW-UP — `AIGateway` service crash loop (same session, after restart)
- Running `nssm restart AIGateway` left the service in a **crash loop**: `Program ...\python.exe for service AIGateway exited with return code 2`, "ran for less than 0 milliseconds", restarting every ~2s.
- NSSM config: `Application = aig\.venv\Scripts\python.exe`, `AppParameters = C:\Users\Alejandro\aig\api_gateway.py`, `AppDirectory = C:\Users\Alejandro\aig`.
- **Root cause:** `api_gateway.py` was **relocated to `C:\Users\Alejandro\aig\core\api_gateway.py`** (code reorg at ~21:50) but the NSSM service still pointed at the old root path. The previously-running process had the old code resident in memory so it kept serving :8080; the restart killed it and the relaunch hit the missing old path → instant exit 2.
- **Fix (run as Administrator):**
  ```powershell
  nssm set AIGateway AppParameters "C:\Users\Alejandro\aig\core\api_gateway.py"
  nssm restart AIGateway
  ```
  (Application and AppDirectory stay the same.) Verified manually: `core\api_gateway.py` starts cleanly → `Core: CONECTADO` on :8080.
- NOTE: `AIGateway` = the aig API Gateway that serves the Hermes stack — this is the service whose restart reloads the agent with the now-valid `OPENROUTER_API_KEY` from `hermes\.env`. The `Hermes_Gateway` scheduled task (separate, `hermes gateway run`) does NOT load `.env` and was left disabled.
