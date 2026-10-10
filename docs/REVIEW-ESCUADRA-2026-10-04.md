# REVIEW-ESCUADRA 2026-10-04 — Backlog consolidado

**Método:** 4 subagentes de revisión en paralelo (solo lectura):
1. Auditor de seguridad (nginx/Caddy, auth, crypto, secrets, inyección)
2. Cazador de duplicados y dead code (hashes SHA-256, referencias)
3. Auditor de contratos (compose ↔ Caddy/nginx ↔ código, puertos)
4. Auditor de deriva docs↔código (AGENTS.md, docs/, READMEs)

Estado de salida de la campaña P1–P6 + quality: **pytest 0 fallos, ruff 0, GATE GO**.

## Resuelto en wave 2 (commit c022a3fe + docs)

- **S1** litellm: 5 claves LLM -> `${OPENROUTER_API_KEY}`/`${GROQ_API_KEY}`/`${TOGETHER_API_KEY}`/`${DEEPINFRA_API_KEY}`, master_key sin default, puerto a `127.0.0.1`, DB password env-izada. **Pendiente del dueño: rotar las 5 claves (estan en el historial de git).**
- **S2** JWT fail-closed en 5 ficheros (`shared/aig_shared/config`, `api/api_gateway`, `daniela-os/api_gateway`, `daniela-os/auth_system`, `scripts/auth_system`); conftest fija secreto de test.
- **S3** `network.conf`: secretos por entorno con `${VAR:?}` (ya no hay secretos en git).
- **D1-D5** despliegue: `context: ../..` en prod/slim/core (28 builds), dockerfiles reales (hermes->ide/hermes, infra->engine/infra-opt, perf->backend/perf-opt, prometheus->skills/plugins/prometheus), COPYs internos corregidos (mobile-app pointer, aig-shared->shared, gev eliminado), nginx upstream `daniela:9200` + 443/ssl montado.
- **D6, D9, D10, D11, D13** aplicados (agents/api COPY, cross_engine shared, infra/perf COPY, puertos, env_file agent).
- **D7** `security` y **gods-eye**: en `profiles` (sin codigo / repo externo) + depends_on saneados. `docker compose config` valida OK en prod/slim.
- **G1-G16** docs: AGENTS.md, README.md, INDEX.md, ESTANDARES, CODE-REVIEW, MODULES/DEPLOYMENT/PHASES, daniela-os/README, handoff, ESTRUCTURA.
- **Frase de marca**: "La empresa de IA que te vende tiempo" en landing + brand kit.

## Resuelto en wave 4 (commit 98bc0abc)

- **S4** secure_engine login: exige `SECURE_ENGINE_ADMIN_TOKEN` (const-time) + lockout registra fallos reales.
- **S5** TOTP: sin semilla por defecto (antes la del RFC, publica); aleatoria por instancia.
- **S6** middleware JWT: exencion loopback ELIMINADA; `X-Service-Token` con `hmac.compare_digest`.
- **S7** api_gateway: tenant desde JWT `sub` (antes cabecera `X-Client-ID` controlable); `get_db` aplica `search_path` en su conexion; dead code eliminado.
- **S8** webhook: exige HMAC-SHA256 (`WEBHOOK_SECRET`); ya no pasa el body crudo a `core.ask`.
- **S11** datos: postgres/redis/minio/n8n bind a `127.0.0.1` + credenciales por env + `requirepass` redis.
- **S12** cifrado: XOR+PBKDF2 -> AES-256-GCM (cryptography) con nonce aleatorio; fail-closed sin clave.
- **S14** casbin: wildcard `["admin","*","*","*","allow"]` ELIMINADO; enforcer conectado al middleware JWT (fail-open para sujetos sin politicas).
- **S15** Caddy: headers de seguridad globales + `basic_auth` en `/secure/*` y `/devtools/*`.

## Resumen ejecutivo

- **2 P0 de seguridad**: claves LLM reales en `config/observability/litellm_config.yaml` y `JWT_SECRET` por defecto en 5 ficheros de auth (ningún compose lo inyecta).
- **5 P0 de despliegue**: el stack principal `docker/docker-compose-aig.yml` no compila 9/11 servicios; `prod` y `slim` usan `context: ..` que resuelve a `config/` (17/23 y 8/10 rotos); nginx prod apunta a `daniela-os:5000` (no existe; es `daniela:9200`); nginx prod no expone 443 ni monta SSL (no arranca); `daniela-os/Dockerfile` hace `COPY ./mobile-app/...` y `mobile-app` es un fichero de 36 bytes, no una carpeta.
- **Duplicación crónica**: 532 nombres de fichero `.py` viven en 2+ ubicaciones (1.563 ficheros); 197 grupos idénticos por hash. La raíz de `scripts/` es casi zombie (99/116 sin referencias).
- **Docs desfasadas**: AGENTS.md, README.md, docs/INDEX.md y ESTANDARES-ORGANIZACION.md describen layout, puertos y servicios que ya no existen tras P1–P6.

---

## P0 — Seguridad

| # | Hallazgo | Fix |
|---|---|---|
| S1 | `config/observability/litellm_config.yaml:22,31,39,47,55,62,69,77,85` — 5 claves LLM reales en claro trackeadas (OpenRouter `sk-or-v1-…`, Groq `gsk_…`, Together, DeepInfra, Qwen) + `master_key: ${LITELLM_MASTER_KEY:-sk-aig-master-key}` (L124) + proxy en `host: 0.0.0.0` (L128) publicado 0.0.0.0:4000 | **Rotar las 5 claves YA (manual, fuera del repo)**. Cargar claves vía env (`${OPENROUTER_API_KEY}`), `master_key` fuerte por env, bind del proxy a red interna |
| S2 | `shared/aig_shared/config/__init__.py:54` — `os.getenv("JWT_SECRET", "change-me-in-production")`; duplicado en `api/api_gateway.py:175`, `daniela-os/api_gateway.py:37`, `daniela-os/auth_system.py:32`, `scripts/auth_system.py:49`. Ningún compose inyecta `JWT_SECRET` y `.dockerignore` excluye `.env` → en contenedor el JWT se firma con secreto público | Fail-closed: lanzar `RuntimeError` si el secreto es el default; inyectar `JWT_SECRET` (alto entropo, por despliegue) en todos los compose; revocar tokens emitidos con defaults |
| S3 (P1→P0) | `config/nginx/network.conf:32-33` — `JWT_SECRET="aigestion_jwt_secret_2026"` y `API_KEY="aigestion_api_key_2026"` en claro trackeadas (detectado por Secret Guard en commit P6); la sincronización PC↔móvil va por `http://` (L66) y rsync/scp en claro (83-86) | Generar por despliegue, mover a `.env` gitignored, cifrar el canal (TLS/Tailscale) |

## P0 — Despliegue / Contratos

| # | Hallazgo | Fix |
|---|---|---|
| D1 | `docker/docker-compose-aig.yml` (stack principal, 11 servicios): 9/9 builds rotos — contextos `./hermes-epic/`, `./infra-opt/`, `./sec-opt/`, `./perf-opt/`, `./nginx/Dockerfile`, `./prometheus/Dockerfile`, `../vendor/gev` inexistentes en raíz; `daniela-os/Dockerfile:80` `COPY ./mobile-app/core/autonomy/model_router.py` (fichero de 36 bytes); `agents/api/Dockerfile` `COPY ./gev/daniela-os/shared/*` (`gev/` solo trae `__init__.py`) | Reescribir contextos a rutas reales (`ide/hermes`, `engine/infra-opt`, `backend/perf-opt`), corregir los 2 COPYs, crear `sec-opt/` o retirar el servicio |
| D2 | `config/docker/docker-compose.prod.yml` + `.slim.yml` (movidos a `config/docker/` el 2026-10-04): `context: ..` resuelve a `config/` y no a la raíz → 17/23 (prod) y 8/10 (slim) servicios no compilan; solo se corrigió `env_file: ../../.env` | `context: ../..` en todos los servicios con build (o mover los compose a `config/` de vuelta) |
| D3 | `config/nginx/nginx.conf:28` — `set $daniela_backend daniela-os:5000;`: no existe servicio `daniela-os` (es `daniela`) y el puerto es 9200 → todo `/api/*` devuelve 502 | `set $daniela_backend daniela:9200;` |
| D4 | `config/nginx/nginx.conf:45-55` — el nginx prod hace `return 301 https://…` pero expone solo `80:80` (443 inalcanzable) y no monta `/etc/nginx/ssl/{cert,key}.pem` → `nginx:alpine` muere: `cannot load certificate` | Exponer 443 + montar ssl, o quitar el redirect y depender del Caddyfile |
| D5 | `daniela-os/Dockerfile:80` — `COPY ./mobile-app/…`: `mobile-app` en raíz es un **fichero regular de 36 bytes** con el texto `frontend/apps/android-app/mobile-app` (no es symlink; AGENTS.md:36 dice que sí lo es) → la imagen del servicio core falla en todos los stacks | Junction/symlink real en raíz, o `COPY frontend/apps/android-app/mobile-app/…` en el Dockerfile |

## P1 — Seguridad (código)

| # | Hallazgo | Fix |
|---|---|---|
| S4 | `engine/secure_engine/server.py:102` — endpoint `login` expuesto (:9880, Caddy `/secure/*`) crea sesión **sin verificar credencial**: `record_attempt(user_id, True)` siempre en verde. El lockout es teatro | Validar contraseña/TOTP antes de crear sesión; registrar fallos reales |
| S5 | `engine/secure_engine/auth_engine.py:195` — semilla TOTP por defecto = la del RFC (`JBSWY3DPEHPK3PXP`); `server.py:47` la instancia sin semilla; `mfa_generate` devuelve código + backup codes en claro (113-117) | `secrets.token_urlsafe(20)` por usuario, semilla persistida, nunca exponer códigos por API |
| S6 | `shared/aig_shared/auth/middleware.py:41-69` — doble bypass: exención de auth para `remote_addr` en loopback + `X-Service-Token` estático global exime de JWT a todo `/api/*` (comparación no constante) | Eliminar exención loopback (rutas /health dedicadas); tokens por servicio con scope + `hmac.compare_digest` |
| S7 | `api/api_gateway.py:241,256,265,786-789` — tenant desde cabecera `X-Client-ID` + `CREATE SCHEMA`/`SET search_path` por f-string SQL; el aislamiento multi-tenant es código muerto (`get_db()` no aplica el `search_path` del hook, `set_schema_for_request` nunca se usa) | Derivar tenant del `sub` del JWT; aplicar `SET search_path` sobre la conexión de la petición |
| S8 | `api/api_gateway.py:1003-1026` — `/webhook/<source>` público sin verificar firma (L1009 solo lee la cabecera) y el default hace `core.ask(f"webhook from {source}: …")` → prompt-injection sin auth | Exigir HMAC por fuente (o `@require_auth`); no pasar el body crudo al core |
| S9 | `engine/auto_engine/workflow_engine.py:436-438` — `eval(condition, {"__builtins__": {}}, context)` sobre condiciones persistentes = RCE (escape vía `().__class__.__mro__…`); el `except` devuelve `True` (fail-open) | Whitelist de AST para expresiones; fail-closed |
| S10 | `config/nginx/nginx.conf:60` — `Access-Control-Allow-Origin: *` + `Allow-Headers: Authorization` en el proxy `/api/*`; sin HSTS/nosniff/X-Frame | Eco de origin contra allowlist; añadir headers de seguridad |
| S11 | `config/docker/docker-compose.yml:41-183` — postgres 5432 (password `postgres`), redis 6379 sin contraseña, minio 9000/9001 `minioadmin`, grafana 3000 `admin`, n8n 5678 `admin/admin`, mqtt/esphome/HA en 0.0.0.0 | Bind a `127.0.0.1:` o `100.x.x.x:` (Tailscale); contraseñas por env; `requirepass` redis |
| S12 | `engine/data_engine/storage.py:558-571` — "cifrado at rest" = XOR contra PBKDF2 con `salt = md5(time)[:16]` (predecible) y sin autenticación | AES-256-GCM (cryptography) + salt aleatorio 16 bytes + clave por entorno |
| S13 | `api/api_gateway.py:969,976` — claves API truncadas a 64 bits (`sha256(urandom)[:16]`) y `/v1/admin/token` sin rate-limit | `secrets.token_urlsafe(32)` + `@rate_limited` |
| S14 | `core/auth/casbin_auth.py:128` + `daniela-os/server.py:138-143` — el enforcer casbin se instancia pero NINGÚN hook lo usa; policy por defecto `["admin","*","*","*","allow"]` | Conectar el enforcer al middleware con la identidad del JWT |
| S15 | `config/nginx/Caddyfile` — 17 rutas proxy sin headers de seguridad ni auth; `/secure/*` y `/devtools/*` (sandbox) expuestas sin barrera | Bloque global `header`; exigir JWT en `/secure/*` y `/devtools/*` |

## P1 — Despliegue (resto)

| # | Hallazgo | Fix |
|---|---|---|
| D6 | `agents/api/Dockerfile` — `COPY ./gev/daniela-os/shared/*`: `gev/` solo trae `__init__.py`; el módulo real ya va dentro de `agents/api/agent_shared/` | Borrar los COPYs (o copiar desde `agents/api/agent_shared/`) |
| D7 | Servicio `security` (aig:198, prod:257, slim:128): **no existe `sec-opt/`** en el repo ni `/api/secure/status` en ningún server.py; solo lo citan tests/dashboards | Implementar el código o retirar el servicio del compose y de `scripts/core/ci_health_gate.py:28` |
| D8 | hermes: 3 caminos rotos — prod/slim piden `ia-services/hermes/Dockerfile` (inexistente), main pide `hermes-epic/Dockerfile` (root) sin `server.py`, y el código real (`ide/hermes/server.py`, puerto 9300) tiene un Dockerfile que copia `./IA-SERVICES/hermes/` y `./aig-shared/` (inexistentes) | Dockerfile canónico en `ide/hermes/` (`COPY ide/hermes/` + `COPY shared/`) y actualizar los 3 compose |
| D9 | `engine/cross_engine/Dockerfile:9` — `COPY aig-shared/ ./shared/` con contexto `config/` → el dir real es `shared/` en raíz | `COPY shared/ ./shared/` + contexto `../..` |
| D10 | `engine/infra-opt/Dockerfile:5` y `backend/perf-opt/Dockerfile:5` — `COPY ./infra-opt/ .` / `./perf-opt/ .` asumen raíz; el código vive en `engine/` y `backend/` | `COPY ./engine/infra-opt/ .` / `COPY ./backend/perf-opt/ .` |
| D11 | Puertos duplicados: minio `9001` vs mqtt `9001` (compose.yml:147,183); tempo `4317/4318` vs otel-collector (observability.yml:25,87) | Remapear host port (mqtt→9002, otel→4327/4328) |
| D12 | `config/docker/docker-compose.observability.yml:20-85` — `./tempo.yaml`, `./loki.yaml`, `./promtail.yaml`, `./otel-collector.yaml` y `./grafana/{provisioning,dashboards}` no existen en `config/docker/` (los yamls están en `config/observability/`) → 4/5 contenedores crash-loop | Rutas `../observability/*.yaml` + crear `config/grafana/provisioning` o desmontar |
| D13 | `config/docker/docker-compose.slim.yml:99-126` + `docker/docker-compose-aig.yml:174-196` — `agent`/`agent_mobile` sin `GEMINI_API_KEY` ni `env_file`; `agents/api/server.py:53` la exige → bootloop | Añadir `env_file: ../../.env` (como hace prod:232) |
| D14 | Menores: compose legacy con contextos `config/docker/docker/*` inexistentes + volúmenes huérfanos; `docker-compose.core.yml` mapea 5000:5000 y healthcheck `/api/health` inexistente (el Dockerfile binda 9200); healthcheck nginx a `/health` recibe 301 (falso-healthy); `ecosystem_engine/server.py` no lee `SERVICE_PORT`; imágenes `ghcr.io/esphome` y `ghcr.io/home-assistant` violan el mandato "no GHCR" | Corregir cada uno; ver commit de wave-2 |

## P1 — Duplicados (los que sí se borran/confligen; wave-3)

Regla del cazador: **0 imports cruzados medidos entre copias** — el canónico se decide por rutas de despliegue (Dockerfile/compose). Top:

| Fichero (nº de copias) | Veredicto |
|---|---|
| `flow_studio_aig.py` (2, idénticos) | BORRAR `scripts/flow_studio_aig.py` (canónico `scripts/core/`) |
| `daniela_self_improvement.py` (3) | BORRAR `scripts/`; confligir `daniela-os/` (fork leve) |
| `google_tools_epic_ideas.py` (3, idénticos) | BORRAR `scripts/` y `daniela-os/` (canónico `scripts/utils/`) |
| `billing_system.py` (3) | BORRAR `scripts/` y `daniela-os/` (canónico `scripts/core/`; docs citan `core.billing_system` = ruta rota) |
| `pixel_audit_ideas.py` (3, idénticos) | BORRAR `scripts/` y `daniela-os/` |
| `gemini35_free_tier.py` (3) | BORRAR `scripts/` y `daniela-os/` (canónico `scripts/utils/`) |
| `analytics.py` (3) | BORRAR `scripts/` y `daniela-os/` (canónico `scripts/core/`) |
| `autoprog_engine.py` (3) | BORRAR `scripts/` y `daniela-os/` (el `scripts/core/` trae el fix de rutas Windows) |
| `termux_v2_roadmap.py` (3) | BORRAR `scripts/pixel/` y `daniela-os/` (raíz = superconjunto) |
| `google_free_tier_automations.py` (3) | CONFLIGIR: propagar la versión 1157L a `scripts/utils/` |
| `sil_engine.py` (3) | BORRAR `daniela-os/` y `scripts/core/` (canónico `sil/`; Dockerfile copia `./sil/`) |
| `swarm_intelligence.py` (2) | BORRAR `daniela-os/` (placeholder; canónico `agents/`) |
| `message_broker.py` (2) | BORRAR `daniela-os/` (canónico `core/`, usa `paths.py`) |
| `viral_content_factory.py` (3) | BORRAR `daniela-os/` y `scripts/utils/media/` (canónico `content/`) |
| `content_factory_ai.py` (2) | BORRAR `daniela-os/` (canónico `content/`) |
| `aigestion_brand_kit.py` (3) | CONFLIGIR (3 versiones; la que viaja al contenedor es `content/`) |
| `admin_panel.py` (3) | CONFLIGIR (root = fork antiguo; `handoff.md` apunta a `scripts/utils/`) |
| `aig_adapters.py` (2) | CONFLIGIR + revisar bug: en `core/`, `_REPO_ROOT = Path(__file__).parent.parent` apunta FUERA del repo |
| `tenant_bootstrap.py` (2) | BORRAR `scripts/tenant_bootstrap.py` (canónico `scripts/deploy/`, lo usa `docker-compose.enterprise.yml`) |
| `supabase_env.py` (2) | BORRAR `scripts/utils/supabase_env.py` (docs citan `scripts/supabase_env.py` como vivo) |
| `check_env.py` (2) | CONFLIGIR (la raíz trae `--restore` del backup .env) |
| `dual_mode_switch.py` (3, idénticos) | **NO borrar**: `tests/mobile/test_pixel_bridge_hub.py` verifica las 3 copias (ADR-022 §3) |

**Shims rotos (importan `aig.*` que ya no existe tras P4):** `scripts/aig_content_calendar.py`, `scripts/connections_manager.py`, `scripts/media_pipeline.py`, `scripts/content_os.py`, `scripts/aig_core.py`, `scripts/sil_engine.py`, `scripts/safe_gate.py` (+`scripts/core/`), `scripts/safe_exec.py`, `scripts/agents/*.py` ×8 (agent_court, agent_squad, agent_scoreboard, agent_continuum, agent_cad_studio, agent_invoice_graph, agent_expediente, memory_vault). **Fix:** apunten al canónico real (`core/`, `content/`, `sil/`, `agents/`) o bórranse.

**Otros muertos:**
- `scripts/reorganize_monorepo.py`, `scripts/migrate_home_to_repo.py` — one-shots de la reestructura.
- `daniela-os/backup_patches/` (40 ficheros) — parches "sovereign", cada uno con gemelo idéntico en `scripts/archive/`, 0 refs.
- `scripts/archive/` — 226 ficheros (crecimiento descontrolado de la papelera).
- `agents/agent-opt/` (15 `.py` idénticos a `agents/api/`) — espejo muerto sin Dockerfile ni compose.
- `_incoming/phone/danielaos/` (45 ficheros) — staging; el canónico es `frontend/apps/android-app/mobile-app/` + `daniela-os/phone/` (ADR-022).

## P0/P1 — Deriva docs (wave-2)

| # | Doc | Deriva |
|---|---|---|
| G1 | `AGENTS.md:12` | Compose: dice `config/docker-compose.yml (23)`; real: `config/docker/docker-compose.yml` (14), `.prod.yml` (23), `.slim.yml` (10), `.observability.yml` (5) |
| G2 | `AGENTS.md:28-31` | Caddy: dice `api.localhost → /gods-eye/* → daniela:9200`; real: `daniela.localhost→9200`, `hermes.localhost→9300`, sin handler `/gods-eye`. Hermes=**9300** (no 9900; 9900 es el orchestrator cross_engine) |
| G3 | `AGENTS.md:20-21` | "13/13 Healthy" con `daniela` dos veces; el health gate canónico (`scripts/core/ci_health_gate.py`) vigila **18** servicios; `caddy` no es un servicio de compose (corre nativo) |
| G4 | `AGENTS.md:8,14` | Android: dice Kotlin 2.2.10/Gradle 9.3.1/AGP 9.1.1/SDK 26-36; real en `daniela-os/android-app/`: Kotlin 1.9.22, Gradle 8.6, AGP 8.3.0, minSdk 24, targetSdk 34 |
| G5 | `AGENTS.md:24-25` | Rutas muertas: `epic-pc/`, `daniela-omnipresente/`, `gods_eye/`, `IA-SERVICES/hermes/`, `hermes-epic/` → hoy: `daniela-os/daniela-jarvis/`, `gev/`, `ide/hermes/`, `docker/epic-pc/`, `docker/hermes-epic/` |
| G6 | `AGENTS.md:36` | "en raíz `mobile-app` hay un symlink" → es un fichero regular de 36 bytes (ver D5) |
| G7 | `AGENTS.md:77-81` | `.codex/`, `.cursor/`, `.github/copilot-instructions.md` no existen |
| G8 | `README.md:110-140` | Comandos `pytest tests/test_paths_integrity.py` y `tests/test_boot_scripts.py` (rutas muertas: son `tests/security/` y `tests/integration/`); enlace `[LICENSE]` muerto (no hay LICENSE trackeado) |
| G9 | `README.md:9-34` | Estructura: 9 rutas de raíz inexistentes (`phone/`, `grafana/`, `hermes-epic/`, `epic-pc/`, `load-testing/`, `sec-opt/`, `perf-opt/`, `plugins/`, `connectors/`); `mobile-app/` descrita como carpeta cuando es pointer-file |
| G10 | `docs/INDEX.md:56,114-152,186-209` | Mapa del repo con `aig/`, `epic-pc/`, `daniela-ompidresente/`, `phone_deploy/`, `hermes-epic/`, `daniela-jarvis/` en raíz (todos movidos/eliminados en P1–P4); "tests/ NO EJECUTA NI UN TEST (6 errores)" → hoy 0 fallos |
| G11 | `docs/ESTANDARES-ORGANIZACION.md:33-88` | Listado de carpetas canónicas con 5 rutas muertas; "Hermes sigue en 9900" → 9300 |
| G12 | `docs/CODE-REVIEW.md:85-87` | "10k+ legacy lint findings" → ruff = 0 desde el 2026-10-04 (ratchet = 0, guardia anti-regresión) |
| G13 | `docs/MODULES.md:614,618` + `docs/DEPLOYMENT.md:101` + `PHASES.md:210` | `pytest tests/test_ci_health_gate.py` → renombrado a `tests/core/test_ci_health_gate_core.py` |
| G14 | `daniela-os/README.md:38,45,138` | Clone `github.com/aigestion/AIGESTION-MONOREPO` (real: `aigestion/AIG`); `aigestion_core.py` no existe; pide Python 3.13+ (el pyproject exige >=3.11) |
| G15 | `docs/handoff.md:860-878,989-996` | Pendiente "phone_deploy deja de trackearse" → ya hecho en P2; gates ruff 929/934 desfasados |
| G16 | `docs/ESTRUCTURA.md:73,175,263` + `docs/ADR-REPO-LAYOUT.md` | Listan `optimization/` y `cross_engine/` en raíz (P4); ADR-001 sin nota de supersedeo |

## Plan de olas (propuesta)

- **Wave 2 (ahora):** P0 seguridad en código (S1 env-ización, S2 fail-closed, S3) + P0 docs (G1–G11, G13) — commits gated por gate pytest/ruff.
- **Wave 3:** P0 despliegue (D1–D5, D6, D9, D10, D11, D13) — reescribir los 3 compose + Dockerfiles + nginx; verificar builds con `docker compose build` si hay Docker.
- **Wave 4:** P1 seguridad código (S4–S9: secure_engine, middleware, webhooks, eval) — cambia comportamiento; con tests.
- **Wave 5:** P1 duplicados — lotes de BORRAR por hash + shims rotos + paperera.
- **Wave 6:** P1 despliegue resto (D7, D8, D12, D14) + P2 (docs menores, ports, etc.).

## Pendiente del dueño (manual, fuera del repo)

1. **Rotar las 5 claves LLM** de `config/observability/litellm_config.yaml` (S1): OpenRouter, Groq, Together, DeepInfra, Qwen — ya están en un repo versionado.
2. **Rotar `JWT_SECRET`/`API_KEY`** de `config/nginx/network.conf` (S3) y los defaults de la pila de auth (S2).
3. Decisión D7: el servicio `security` (:9999) no tiene código — implementarlo o retirarlo del health-gate.
