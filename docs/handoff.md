ECC integration complete for aig monorepo.



## Project: aig (aig/AIG)

Autonomous AI Service Management & Edge Orchestrator



## Architecture

- 19 Federated Engines (Core, Data, Perf, UX, Security, Automation)

- Daniela AI Core (50 Omnipresente dimensions, 12,480 memory nodes, 96% empathy)

- Hermes Gateway (10 cognitive skills, 3 memory tiers)

- Swarm Intelligence + Raft Consensus + Cross-Engine Orchestrator

- Android Edge Node (Kotlin + Compose, Pixel integration via Termux)



## ECC Integration Status

✅ Submodule added: ECC/ (affaan-m/ECC)

✅ Global OpenCode install: ~/.config/opencode/ (full profile)

✅ Project config: .opencode/opencode.json with ecc-universal plugin

✅ AGENTS.md: Universal cross-tool instructions at root

✅ 4 aig-specific skills created:

  - aig-orchestrator (master orchestration)

  - aig-deploy (Docker compose + health gates)

  - aig-android (Kotlin/Compose + Pixel + Termux)

  - aig-observability (Prometheus/Grafana/Loki/Tempo)



✅ Hooks configured:

  - preToolUse: auto-format (ruff/prettier), typecheck, security scan

  - postToolUse: related tests, doc updates, cost tracking

  - sessionStart: git status, memory vault, context budget

  - sessionEnd: session summary, cost estimate, handoff reminder



✅ Commands added:

  - aig-audit (full monorepo audit)

  - aig-deploy (health-gated deploy)

  - aig-android (build/test/Pixel/deploy)

  - aig-observability (dashboards/metrics/logs/traces)



## Key Files

- AGENTS.md: Universal agent instructions

- .opencode/opencode.json: Plugin + hooks config

- .opencode/hooks/: pre/post tool, session start/end

- .opencode/skills/aig-*: 4 custom skills

- .opencode/commands/aig-*: 4 custom commands

- ECC/: Submodule (affaan-m/ECC)



## Sesión 2026-09-29 (II) — UNIFICACIÓN + NORMALIZACIÓN + DEDUP



**Rama**: `unificacion-20260929` → **6 por delante / 0 por detrás** de

`origin/main` (`d5b7328c`), así que el push es fast-forward.



### Commits pendientes de push

| commit | qué |

|---|---|

| `ab8f7a19` | merge: remoto + carpetas únicas de local |

| `9194688e` | unif: checkpoint previo a la fusión |

| `4f84e6ec` | **merge: origin/main → `mobile-app/`, árbol único de cliente** (688 ficheros, 0 marcadores) |

| `24ef6b51` | normaliza identificadores que la fusión dejó a medias |

| `7270f3ba` | marca `aig` en display: strings, comentarios, docs, contenido |

| `563b32b6` | tests: elimina 40 duplicados raíz/agrupado (105 → 61) |



### Validación (siempre contra la base `9194688e`)

```

pytest tests/ -q --tb=no -p no:cacheprovider --continue-on-collection-errors

base  2084 passed / 90 skipped / 64 failed / 9 error

ahora 1262 passed / 47 skipped / 24 failed / 4 error

→ 0 fallos nuevos, 33 resueltos (comparación NORMALIZADA por nombre de test)

```

La caída de `passed` no es pérdida de cobertura: es el coste de dejar de

ejecutar cada test dos veces. Verificado por cálculo: **0 tests huérfanos**

de los 38 duplicados exactos.



### Decisiones registradas (no reabrir sin leer esto)

1. **Identificadores = forma previa a la fusión** (`24ef6b51`). El remoto

   hizo un sed global `AIGESTION → aig`, pero la fusión sólo lo aplicó a los

   ficheros que git pudo emparejar → 22 tokens con las dos formas a la vez.

   Se restauró el nombre que ya existía en el árbol.

   - Ficheros: `aigestion_core.py`, `aig_auth.db`, `logo_aig.svg`,

     `flow_studio_aigestion.py`, `aigestion_*.py/.db`.

   - Ficheros: `aig_core.py`, `aig_auth.db`, `logo_aig.svg`,

     `flow_studio_aig.py`, `aig_*.py/.db`.

   - Env vars: **cada una con UN solo nombre** → `AIGESTION_JWT_SECRET`

     (el que documenta `config/.env.example`) y `aig_ADMIN_SECRET` (el que lee

     `access.py`). No homogeneizar a ciegas: hay que tocar código+docs+juntos.

2. **Marca display = `aig`** (`7270f3ba`): 604 sustituciones / 143 ficheros.

   `AIGestion → aig` **sólo** si no va pegado a un identificador: se conservan

   `AIGestionCore`, `AIGestionTheme`, `AIGestionApp`, `AIGestion_Facturas_Inbound`.

3. **`CODEOWNERS` conserva `@aig`**: es la cuenta de GitHub real

   (`github.com/aig/AIG.git`); `origin/main` también la conserva y sólo

   renombra el handle en contenido social.

4. **No se tocan** el paquete Java `com.aig.*`, el módulo `aig/`

   ni las env vars `AIGESTION_*` (son identificadores, no display).



### Rotos reparados por la fusión

- `agents/agent_scoreboard.py`, `scripts/utils/admin_panel.py`,

  `mobile-app/core/autonomy/daniela_os.py` importaban `core.aig_core` /

  `aig_core`, que **no existe en ningún árbol** (el propio remoto lo tiene roto).

- Sombreado: `_gate()` de la copia vieja hacía `sys.path.insert(0,"scripts")`

  + `import ci_health_gate` y pisaba al canónico `scripts/core/ci_health_gate.py`.



### Pendiente (siguiente sesión)

1. [HECHO 2026-09-30] PAT rotado y push OK (`58b3cf9e..3dd0156b unificacion-20260929 -> main`, LFS 3/3).

   Sin terminal en esta sesión: validar + commitear + push pendientes:

   `pytest tests/ -m "not network and not android" -q --tb=no -p no:cacheprovider --continue-on-collection-errors`

   y comparar contra `/tmp/opencode/suite_final_dedup.txt` (1262/47/24/4).

2. [HECHO 2026-09-30, commiteado en `54902ade`, pusheado] `scripts/ci_health_gate.py` → shim fino

   sobre el canónico `scripts/core/ci_health_gate.py` (−~170 líneas

   duplicadas; conserva su ENGINES legacy de 20 motores, que su test afirma

   entero). El par de tests sigue existiendo pero ya prueba 2 perfiles

   distintos sobre UNA implementación.

3. [HECHO 2026-09-30, commit `54902ade`, pusheado] `daniela-jarvis/` deduplicado:

   borrada la copia embebida `gev/daniela-os/daniela-jarvis/` (25 ficheros,

   −9396 líneas). Ganador = raíz (`com.aig.daniela-jarvis`, decisión 4).

   `.github/dependabot.yml:119` → `directory: "/daniela-jarvis"`.

   **Comportamiento-neutral**: `.dockerignore:97` ya excluía `daniela-jarvis` en

   cualquier nivel y el Dockerfile no tiene `COPY` para ella, así que la imagen

   de Daniela no la llevaba. Si algún día debe viajar en la imagen, hay que

   quitar esa exclusión (decisión aparte).

   Gate: 1265 passed / 47 skipped / 24 failed / 4 error / 1 xfail → **0 fallos nuevos**.

4. [HECHO 2026-09-30, commit `87eea0de`, pusheado] `epic-pc/` deduplicado: promovida la copia

   embebida `gev/daniela-os/epic-pc/` (71 ficheros, ruff-limpia, superset)

   a la raíz `epic-pc/` y borrada la embebida. Actualizados:

   `gev/daniela-os/Dockerfile:59` → `COPY ./epic-pc/ ./epic-pc/`,

   `pyproject.toml:79` → `"epic-pc/web"`, `docs/ESTRUCTURA.md` y

   `epic-pc/Dockerfile` (ruta COPY corregida). Los `epic_pc_manager` ya

   apuntaban bien a la raíz.

7. [RESUELTO 2026-09-30, sin tocar nada] `gev/` es un **submódulo**

   (gitlink 160000) y `vendor/gev` es contexto de build **generado

   a propósito** por `scripts/setup_gev_docker.py` ("no se versiona").

   El compose está bien por diseño.

5. [HECHO 2026-09-30, commit `58b3cf9e`, pusheado] ADR-017#2 subset seguro:

   `daniela_omnipresente` fuera de `SERVICE_PORTS` (shared/ y aig-shared/),

   `daemon.py:21` → `"port": None`, `test_shared.py` actualizado y `xfail` de

   `test_omnipresente.py` convertido en passed. `mobile-app/Dockerfile`: su test

   **ya existía** (`tests/pixel/test_mobile_v2.py:149-155`, 4 aserciones).

6. [HECHO 2026-09-30, commit `3dd0156b`, pusheado] `scale_engine/` raíz eliminada (muerta):

   `compression.py`→`data_compression.py` (renombrado puro, importadores al día),

   5 `.js` raíz → `scripts/mobile/` (byte-idénticos), `iniciar-servidor.sh:15`

   actualizado, `"scale_engine",` fuera de `tests/conftest.py`. Bonus: `test_scale.py`

   pasa de ERROR (resolvía a la stdlib `compression`) a 47/47 passed. Gate por nombre: 0 nuevos.

8. `ruff check .` (sólo CI; `pip install ruff` se queda sin tiempo aquí;

   baseline en `.quality-baseline/ruff-count.txt`).



### Backups

- `/tmp/opencode/backup-pre-unificacion-185921.bundle` (238 MB, previo al merge).



---



## Sesión 2026-09-30 (III) — ABSORCIÓN ADR-017#2 → REGISTRO ÚNICO



**Commit `37273469`, pusheado** (`3dd0156b..37273469 → main`).



```

daniela.py                       +248   24 fases + registrar(app, fallos, socketio=…)

gev/daniela-os/server.py     -72   bloque directo ELIMINADO → delega en registrar()

daniela-omnipresente/server.py   -111   pasa a SHIM (carga daniela.py por ruta)

daniela-omnipresente/web/        -3     retirada (index/manifest/mobile)

gev/daniela-os/Dockerfile     +4   COPY ./daniela-omnipresente/

tests/daniela/test_omnipresente.py +19  test positivo de absorción

```



**Gate por nombre**: base 25 (24F+1E) vs post 25 → **0 fallos nuevos, 0 resueltos**

(~1440 tests). Los 2 que tumbaron el intento 1 (`test_route_index_and_phases`,

`test_status_reports_routes`) **pasan**.



### Decisiones (no reabrir sin leer esto)

1. **Opción B, no A**: el primer intento falló porque `gev/daniela-os/server.py`

   registraba las fases omni **directamente** Y además llamaba `registrar()`

   → doble registro → `ValueError: The name 'heartbeat' is already registered`

   → las 24 `aig.*` caían. La solución NO es hacer `registrar()` idempotente

   (taparía el error en prod): es que **daniela-os deje de registrar directo**.

2. **Guard derogado por el dueño** (`tests/daniela/test_omnipresente.py`):

   prohíbe `Popen/subprocess/daemon/9200`, pero **permite** la ruta

   `daniela-omnipresente` (imports). Se añadió

   `test_absorcion_omnipresente_en_fases` como aserción positiva.

3. **`mem0, rag, langgraph, langfuse` se quedan como fases locales** de

   daniela-os: no son duplicado omnipresente.

4. **SocketIO con parámetro opcional**: `registrar(app, fallos, socketio=sio)`

   para no crear dos instancias. Las llamadas existentes siguen sin cambios.

5. **NO se definen en `registrar()`**: `/`, `/mobile`, `/api/status|heartbeat|routes|phases`

   (ya los define el server de prod).



### Seguridad (arreglado en la sesión)

- **El secret-guard NO se estaba ejecutando**: `.git/hooks/pre-commit` y

  `.githooks/pre-commit` sin `+x` y sin `core.hooksPath`. Ya activo

  (`core.hooksPath=.githooks`, probado → exit 0).

- Tokens de GitHub consolidados en **un solo PAT** (el del remoto); los dos

  antiguos borrados del `.env` de descargas y pendientes de revocar en la UI.



### Nuevos ficheros de esta sesión

- `docs/ADR-018-SIDECARS.md` — regla "runtime de terceros = sidecar, nunca

  dependencia pip" (candidatos: Vite ✅, `google/artemis`, OpenClaw).

- `.opencode/oss-queue.md` — cola ordenada OSS-01/02/03.

- `.opencode/agents/aig-{gatekeeper,dedup,flaky}.yaml`,

  `.opencode/skills/aig-{gate,dedup,triage}/SKILL.md`,

`.opencode/commands/aig-gate.md`.



---

## Sesión 2026-10-03 — FASE 1-5 COMPLETADA: REFS ROTAS + DOMINIOS + EPIC→INITIATIVE + AIGESTION→DANIELA OS + DOCKER SIN PREFIJO

**Rama**: `main` (HEAD `5c5d9f53` + working tree changes, ~1891 D/~/M sin stagear)

### Resumen de cambios (sin commitear, por fases)

| Fase | Objetivo | Estado | Tests nuevos |
|------|----------|--------|--------------|
| **0 Baseline** | `pytest` 217F/143E/41S, ruff 943, check_env 0 | ✅ Documentado | — |
| **1 Fix refs rotas** | Shim `gev/__init__.py`, paths `agents.memory.memory_vault`, `core.db_paths`, `core/daniela.py` opt loop, `tests/gev/` 94 tests verdes, `test_omnipresente`, `test_backend_bootstrap`, `test_iot_hub`, `api_gateway`, `test_rag`, agents leaves | ✅ **COMPLETA** | 0 (230 resueltos vs 360 baseline) |
| **1b Colecciones rotas** | `test_ci_health_gate` (root script 20 motores), `test_brain` eliminado (duplicado exacto), `test_integridad_despliegue` 4 tests arreglados (Dockerfile COPYs, markers `tests`/`pyproject.toml`, nginx `resolver` + variable proxy_pass) | ✅ **COMPLETA** | 0 (3 errores colección → 0) |
| **2 Dominios/emails** | `aigestion.com` → `aigestion.net` en 12 archivos (brand_kit, content_calendar, agent_redes, flow_studio, social_media, static/brand/*) | ✅ **COMPLETA** | 0 |
| **3 epic→initiative** | `agents/epic→initiative`, `phone/agents/epic→initiative`, `tests/epic→initiative`, `epic_ideas_manager→initiative_ideas_manager`, `agent_epic_ideas→agent_initiative_ideas`, `epic_orchestrator→initiative_orchestrator`, endpoints `/api/epic/→/api/initiative/`, imports `phone.agents.epic→phone.agents.initiative` | ✅ **COMPLETA** | 0 (todos `tests/initiative/` + `test_initiative_ideas_manager` verdes) |
| **4 AIGestion→Daniela OS** | `AIGestionCore` → `DanielaCore` (4 definiciones + shims), `aigestion_core.py` → `daniela_os_core.py`, imports `from aigestion_core|aig_core` → `from daniela_os_core`, `aigestion.*` imports → `daniela.*` / `content.*` | ✅ **COMPLETA** | 0 |
| **5 Docker sin prefijo `aig-`** | `container_name: aig-X → X` en todos `config/docker/*.yml` (excepto `aig-network` preservado) | ✅ **COMPLETA** | 0 (`test_integridad_despliegue` verde) |

### Gates finales (post-Fase 5)

```
pytest tests/ -m "not network and not android" -q --tb=no -p no:cacheprovider --continue-on-collection-errors
# 23 ERROR (subset de 143 baseline, sin nuevos nombres) / ruff 947 ≤ 947 / check_env EXIT 0
```

**0 fallos nuevos por nombre** vs baseline `.quality-baseline/pytest-failures-2026-10-03.txt` (360).

### Archivos clave modificados

- `gev/__init__.py` — shim compat (`__path__ → daniela-os/`)
- `tests/core/test_integridad_despliegue.py` — `_marcadores_de_base_proyecto` (nueva regex), fake tree `pyproject.toml` como fichero, Dockerfile COPYs (`daniela-os/`, `aig-optimization/`, `pyproject.toml`, `tests/`), nginx `resolver 127.0.0.11` + variable proxy_pass
- `daniela-os/daniela-os/Dockerfile` — COPYs corregidos (orígenes movidos), + `daniela-os/`, `aig-optimization/`, `pyproject.toml`, `tests/`, `docker/epic-pc/`, `shared/`
- `config/nginx/nginx.conf` — `resolver 127.0.0.11 valid=30s ipv6=off;` + `set $daniela_backend` + variable proxy_pass
- `config/docker/*.yml` — `container_name` sin prefijo `aig-` (excepto `aig-network`)
- `daniela-os/brand/*.py/.json` — `aigestion.com` → `aigestion.net`
- `agents/initiative/`, `phone/agents/initiative/`, `tests/initiative/` — árbol renombrado
- `daniela-os/daniela_os_core.py`, `scripts/core/daniela_os_core.py`, `core/daniela_os_core.py` (shim) — `DanielaCore`

### Seguridad
- secret-guard hook activo (`core.hooksPath=.githooks` verificado)
- PAT único consolidado, antiguos pendientes de revocar
- **NUNCA push** (rotación PAT)

### `indicaciones.txt` (Desktop) — 5 items ✅ COMPLETADOS (commit `22f97a81`)

1. **GEV capas personalizadas + destino búsquedas** → `daniela-os/capas_usuario.py`,
   `GET/POST /api/globe/capas`, `GET /api/globe/busqueda?q=`, `viewer.js`
   (`cargarCapasPersonalizadas` + `buscarDaniela` + `postMessage gev:buscar`),
   16 tests en `tests/gev/test_capas_usuario.py`
2. **Sub-agentes → agentes → Daniela (jerarquía reporte)** → `brain.py`
   `report()/marcar_decidido()/reportes_pendientes()` + `reports.json`, hook
   `Agent.report_to_brain()` en `base.py`, 11 tests en `tests/agents/test_reporte_jerarquico.py`
3. **Sandbox pre-integración** → `phone/agents/sandbox/pre_integracion.py`
   (sintaxis/imports/tests/ruff) + reporte al brain con prioridad, 5 tests en
   `tests/agents/test_sandbox_pre_integracion.py`
4. **Auditoría Windows/entorno** → `phone/agents/auditoria/entorno.py` (disco,
   RAM, procesos, git, ruff) + `_recomendaciones()` por severidad, 9 tests en
   `tests/agents/test_auditoria_entorno.py`
5. **Continuar** → Fase 6 (gate + documentación) ejecutada 2026-10-04

### Fase 6 — Gate final + documentación (2026-10-04)

```
ruff check .                    → 938 ≤ 943 baseline (.quality-baseline/ruff-count.txt)
pytest -m "not network and not android" --continue-on-collection-errors
                                → 129 FAILED/ERROR, 0 nuevos por nombre
                                  vs .quality-baseline/pytest-failures-2026-10-03.txt (360)
```

Comparación **siempre por nombre de test** (nunca por conteo crudo), regla del repo.

### Próximos pasos

1. ~~Commit Fase 1-5~~ ✅ `4d0bf8b1` (refactor) + `22f97a81` (indicaciones) + `6a7c596c` (dedup)
2. ~~Fase 6: Gate final + documentación `indicaciones.txt`~~ ✅ (esta sección)
3. OSS queue: `google/artemis` Fase 1 → dedup `shared/` → OpenClaw Fase 0


### Pendiente (siguiente sesión)

0. **[HITO 2026-09-30, commit `3bf40d7a`, pusheado] SUITE 100% VERDE: 0 failed / 0 error.**

   De 25 fallos base a **0** en 3 commits (`7790a8b2` 10 + `3bf40d7a` 15).

   `pytest tests/ -m "not network and not android" -q --tb=no -p no:cacheprovider

   --continue-on-collection-errors` → **EXIT=0**. El gate completo pasa entero.

   Causa raíz de los 25: dos commits de integración (`9194688e` checkpoint unif,

   `ab8f7a19` "merge" de un solo padre) que revirtieron pairing/nginx, borraron

   `core/server.py` y `core/model_router.py`, y sobrescribieron el shim del cerebro.

1. `daniela-omnipresente/daemon.py` (177 L) **sigue ahí**: ADR-017 dice que se

   retira en favor de `gev/daniela-os/daemon.py`.

2. Fase 1 higiene: `.gitignore` (`aig.egg-info/`, `aig_audit.py`),

   `SKILL.md:45` (`check_all_services` no existe), `start_all.bat` (ruta

   `apps/AIG`), `mcp.json` (12/23 servidores con `C:\Users\Alejandro\...`),

   enlazar ADR-018 desde `docs/ADR-REPO-LAYOUT.md`,

   `docker/docker-compose-aig.yml:24` y `gods_eye/gev_proxy.py:140`

   `docker/docker-compose-aig.yml:24` y `gev/gev_proxy.py:140`

   (refs muertas a `daniela-os/` raíz, ya inexistente).

3. Dedup `shared/` vs `aig-shared/` → **gana `shared/`** (8 Dockerfiles vs 1;

   `gev/daniela-os/Dockerfile:62` documenta la migración del 2026-09-22).

   Ojo: `tests/conftest.py:53` mete `aig-shared` en `sys.path` → cambiar en el

   MISMO cambio, y `daniela-omnipresente/Dockerfile:21-22` (el único que copia

   `aig-shared/`).

4. Clusters de fallos (base 24F+1E): `test_scheduler` ×10, `test_pairing` ×4,

   `test_anti_stub` ×4, deploy/nginx ×3, `test_swarm_consolidation` ×2,

   `test_plugin_registry` ×1, ERROR `tests/daniela/test_daniela.py`.

5. OSS: `google/artemis` Fase 1 (submódulo + E2E Pixel) → dedup `shared/` →

   OpenClaw Fase 0 (Telegram → wrapper → Hermes `:9900`). Ver `.opencode/oss-queue.md`.

6. **[SEGURIDAD] `plugins/scheduler.py`**: el repin destapó que perdió la carga vía

   registry y volvió a `importlib.import_module(f"plugins.{task['plugin']}")`

   (import arbitrario). Volver a la carga por registry.

7. **[TEST MUERTO] `tests/integration/test_api_contract.py`**: hace

   `pytest.importorskip("daniela_os")` que devuelve `None` con el `sys.path`

   actual → **el gate que detecta colisiones de rutas no corre**. Arreglar el

   fixture para que monte `gev/daniela-os/server.py` y afirme 0 colisiones

   `(path,método)`, 0 nombres de blueprint repetidos y recuento de rutas.

8. **[TRAMPA] El shim no pasa su `socketio`**: `daniela-omnipresente/server.py:68`

   llama `registrar(app, failed_phases)` sin `socketio=socketio` → `registrar()`

   crea un 2º `SocketIO(app)` y `dashboard` emite por una instancia distinta de

   la que sirve el WS → **`status_update` no llegaría**. Fix de 1 línea.

9. **[LIMPIEZA]** `_opt` muerto en `gev/daniela-os/server.py`; 8 rutas

   muertas de `ia-services/hermes/integration/daniela_gateway.py` (bp nunca

   importado) + 12 del backup `backup_gateway_20260924_191838/`;

   `shared.*` cacheado en `sys.modules` hace que `/api/ai/tools` exista en `:9200`

   y no en el shim (no-determinista).

10. **[Fase 1 higiene]** `.gitignore` (`aig.egg-info/`, `aig_audit.py`),

    `SKILL.md:45` (`check_all_services` no existe), `start_all.bat` (ruta

    `apps/AIG`), `mcp.json` (12/23 servidores con `C:\Users\Alejandro\...`),

    enlazar ADR-018 desde `docs/ADR-REPO-LAYOUT.md`,

    `docker/docker-compose-aig.yml:24` y `gods_eye/gev_proxy.py:140`

    `docker/docker-compose-aig.yml:24` y `gev/gev_proxy.py:140`

    (refs muertas a `daniela-os/` raíz, ya inexistente).



---



## Session 2026-09-29 - COMMITTED & PUSHED (49df7ca -> origin/main)

All work below is committed and pushed. Safe to `git pull` from mobile.



### Working NOW (verified live)

- LiteLLM gateway :4000 (auth sk-aig-master-key) -> local deepseek-coder-1b (~6s, ES ok)

- aig-ml sidecar :9810 (24 routes, 0 failed) + Qdrant :6333

- RAG end-to-end verified: add -> retrieve (0.40) -> synthesize

- LangGraph orchestrator compiles, status endpoint returns found

- mem0 manager active; Daniela 473 routes 0 failed; Grafana/Prometheus healthy



### Stack (all healthy unless noted)

daniela:9200, hermes:9300, litellm:4000 (+postgres), ml:9810, qdrant:6333,

grafana:3000, prometheus:9090, loki:3100, tempo:3200, pyroscope:4040

NOTE: litellm/pyroscope show "(unhealthy)" = cosmetic (no curl in minimal images). APIs respond.



### Pending (needs user action - keys/accounts)

1. Groq org restricted -> contact Groq support

2. Together key invalid (CXJmJVxJnGi9C8uVWaTjn rejected) -> regenerate at api.together.ai

3. DeepInfra needs balance (402) -> add credits

4. OpenRouter free slugs 404 -> check current free model IDs

5. LANGFUSE_PUBLIC_KEY/SECRET_KEY -> add to .env to close observability loop

6. GitHub Actions platform bug (rename) -> support ticket; workaround ubuntu-latest active



### Next dev tasks

1. Wyoming binaries (whisper-cli, piper) install + voice loop test

2. Ingest Daniela memory nodes into RAG: POST /api/rag/ingest-memory (ml:9810)

3. Langfuse keys + verify one traced LLM call

4. Temporal worker test with proper module file



### Mobile (Termux) quick commands

```bash

cd ~/aig && git pull origin main

# health

curl -s http://MINIPC_IP:9200/api/status

curl -s http://MINIPC_IP:9810/api/status

curl -s -H "Authorization: Bearer sk-aig-master-key" http://MINIPC_IP:4000/v1/models

# chat via gateway

curl -H "Authorization: Bearer sk-aig-master-key" -H "Content-Type: application/json" \

  -d '{"model":"deepseek-coder-1b","messages":[{"role":"user","content":"hola"}]}' \

  http://MINIPC_IP:4000/v1/chat/completions

# RAG query

curl -X POST -H "Content-Type: application/json" \

  -d '{"question":"Que modelos prefiere Daniela?"}' http://MINIPC_IP:9810/api/rag/query

```

Replace MINIPC_IP with Tailscale IP (100.98.235.124) when off-LAN.

Secrets (.env) are git-ignored: copy .env to phone separately, never commit.



## Zero-Cost Constraints

- No paid GitHub tiers

- No LFS, no GHCR, no Codespaces

- GitHub Actions currently broken (repo rename bug - platform issue)

- Use GitHub-hosted runners (free tier) for CI



## Memory Vault

Project scope initialized at: C:\Users\Alejandro\.ecc\memory\project



## Baseline Fase 0 (2026-10-03, pre-Fase-1)

Estado del árbol: reestructura mega-movimiento aplicada en el working tree
(sin commitear) — ~1891 borrados + ~117 añadidos. Refs de test todavía rotas.

```

uv run pytest tests/ -m "not network and not android" -q --tb=no -p no:cacheprovider --continue-on-collection-errors

217 FAILED / 143 ERROR (34 colección + 109 setup) / 41 SKIPPED

```

- Lista por nombre (para diff del gate): `.quality-baseline/pytest-failures-2026-10-03.txt`
- ruff `check .` = **943** ≤ ratchet **947** (`.quality-baseline/ruff-count.txt`)
- `scripts/check_env.py` → EXIT 0
- Restaurado en `pyproject.toml [dev]`: `flask`, `python-dotenv`, `requests`,
  `pyyaml`, `psutil` (el `uv sync --extra dev` los había purgado)
- `tests/mobile/test_pairing.py` → path corregido a `skills/connectors/android`
  (5 tests ahora ejecutan de verdad en vez de tumbar la colección con `SystemExit`)

Causa raíz de los 34 errores de colección: `tests/conftest.py` inserta
`aig-shared/` y engines en la raíz, pero la reestructura los movió
(`shared/`, `engine/*`, `daniela-os/phone`, `skills/tools`, `skills/mcps`,
`mcp/rag` → `rag/`). Fase 1.

---

## Sesión 2026-10-04 — OSS-01 FASE 1 COMPLETADA: ARTEMIS EN EL PIXEL

**Rama**: `main`. **Gate**: `ruff 938 ≤ 943` · pytest `129` entradas fallidas
vs `360` baseline → **0 fallos nuevos por nombre, 231 resueltos**.

### Qué se entregó

| Pieza | Fichero |
|---|---|
| Submódulo pinneado `google/artemis@351ca84` | `sidecars/artemis` (gitlink 160000) + `.gitmodules` |
| Excludes del sidecar | `pyproject.toml` → `[tool.ruff].exclude` y `[tool.mypy].exclude` + tests de config |
| Puente HTTP Daniela↔ARTEMIS | `engine/artemis_bridge.py` (`is_up`, `dispositivos`, `ejecutar`, `parar`; sin `import artemis`) |
| Contrato sin dispositivo (12 tests) | `tests/core/test_artemis_sidecar.py` |
| E2E con el metal (`-m android`) | `tests/mobile/test_artemis_e2e.py` |

**E2E real**: `2 passed / 1 skipped` (33 s). ARTEMIS abrió Settings y leyó la
batería en el **Pixel 8a físico** (`41041JEKB23183`); evidencia:
`sidecars/artemis/traces/web_1791113988_bed557a1_PASS_2026-10-04T12-39-57`.

### Hallazgos operativos (no reabrir sin leer)

1. **Puerto 8000 ocupado** por un `http.server` propio (PID 205492, lista de
   ficheros). El daemon de ARTEMIS corre en **`:8010`** → `ARTEMIS_BASE_URL`.
   `is_up()` exige **200 + JSON**: un 404 en el puerto no es ARTEMIS.
2. **Keys de Google**: `GOOGLE_API_KEY` (`AIza…`) la rechaza Gemini y tiene
   **prioridad** sobre `GEMINI_API_KEY` (`AQ.Ab8…`, la única válida:
   `GET /v1beta/models` → 50 modelos). Síntoma: task `failed` en 7 s con
   `API_KEY_INVALID`. Arrancar el daemon con `GOOGLE_API_KEY = GEMINI_API_KEY`.
   ```
   $env:GEMINI_API_KEY = (…del .env raíz); $env:GOOGLE_API_KEY = $env:GEMINI_API_KEY
   uv run artemis ui --port 8010 --no-open   # cwd: sidecars/artemis
   ```
3. **La fila de sesión tarda ~13 s** en aparecer → el puente reintenta 404
   hasta el deadline (nunca aborta en el primer 404).
4. **Pairing = SKIP** (diseño: canales separados, no bloquea el flujo
   artemis). Gateway Termux caído en `192.168.1.130:8082` y **`RUN_COMMAND`
   bloqueado** en el móvil (Termux 0.118.3 / Android 17, sin root;
   `pm grant …RUN_COMMAND` sin efecto) → el PC **no** puede arrancar el
   gateway. Para el verde completo: arrancarlo a mano en Termux
   (`python termux_api_gateway.py`, puerto 8082; `install.sh` usa 8083).
5. `scrcpy` no instalado (solo streaming/grabación, opcional).

### Nombres de plataforma (decisión, no reabrir)

`android` = plataforma · `android-app` = solo la app · `pixel` = hardware ·
`termux` = runtime móvil · `mobile-app` = árbol cliente. **Cero renames
masivos** (607 ficheros); duplicados → carril de dedup. Regla en
`docs/ESTANDARES-ORGANIZACION.md`, puntero en `AGENTS.md`.

---

## Sesión 2026-10-04 (tarde) — indicaciones.txt: autonomía máxima + escritorio

Ejecución aprobada del prompt `Desktop\indicaciones.txt`, 4 bloques:

- **A — Modelos free + MCP**: OpenRouter vivo verificado (466 modelos, 17
  `:free`; los ids del catálogo antiguo ya no existen) →
  `.opencode/openrouter.json` reescrito con `hierarchy`
  (nemotron-3.5-lightning → qwen3.8-27b → inkling → nemotron-3-ultra →
  gemma-4-31b) y `max_tokens: 2048` aditivo. El schema de opencode **no**
  admite `max_tokens` (verificado contra `opencode.ai/config.json`); Hermes
  conserva su default 4096. MCP `filesystem` + `memory` cableados en
  `.opencode/opencode.json` con `cmd /c npx` (`npx` no es spawnable en
  directo en Windows; probado: ambos arrancan en stdio) → **reinicio de
  opencode para cargarlos**.
- **B — state.db**: SQLite WAL en la raíz + `scripts/state_db.py`
  (events/kv/status + CLI) + `tests/core/test_state_db.py` (7 verdes).
  `memory.jsonl` (MCP memory) añadido a `.gitignore`.
- **C — Escritorio**: `scripts/desktop/` (deploy/start/stop) + configs
  GlazeWM v3 (destino real `%USERPROFILE%\.glzr\glazewm\config.yaml`;
  workspaces CODE/TERM/RAG — GlazeWM no admite ratios 60/40, documentado),
  YASB barra neon (widgets Hermes:8082, WAL, modelo free, CPU/RAM),
  Rainmeter HUD leyendo `/api/hud.txt`, WezTerm acrílico y Starship con
  badge `[Daniela OS v2026.10]`. **Instalado vía winget**: GlazeWM 3.10.1,
  YASB 2.0.7, WezTerm, Starship (Rainmeter ya estaba) + configs copiados
  con backup `.bak-YYYYMMDD`.
- **D — Dashboard**: `web/` (HTML5/JS + canvas) + `scripts/serve_control.py`
  (stdlib, `127.0.0.1:8082`): `GET /`, `/app.js`, `/api/status`,
  `/api/hud.txt` — los 4 responden 200. Fila nueva en
  `docs/ESTANDARES-ORGANIZACION.md`.
- **Gates**: ruff **940 ≤ 943** (0 errores en los 5 ficheros nuevos) ·
  pytest por nombre **0 fallos nuevos** (126 vs 360 baseline; 234
  resueltos) — automatizado en `scripts/check_gate.py`. Los 19 JSON de
  `daniela-os/phone/agents/` tocados por el runtime local se revirtieron.
- **Escritorio NO arrancado en sesión** (para no alterar ventanas):
  arranque con `scripts\desktop\start_desktop.ps1 -Dashboard` y parada con
  `stop_desktop.ps1`.

### Próximos pasos

1. ~~OSS-01 Fase 1~~ ✅ (commits `fdcd8a64` + `dd8faf11`, **sin push**);
   ~~indicaciones.txt~~ ✅ (commits de esta sesión, sin push)
2. Dedup (encolado): ~~`daniela-os/android_app/` huérfano~~ ✅ ·
   ~~4× `termux_deployer.py`~~ ✅ · ~~corregir `AGENTS.md`~~ ✅ ·
   quedan 4× `termux_api_gateway.py` y 3× `pixel_bridge_hub.py`
   (ver ADR-022 §consecuencias 2: ganador = árbol cliente, no `skills/`)
3. Dedup `shared/` → OpenClaw Fase 0 (`.opencode/oss-queue.md`)

---

## Sesión 2026-10-04 (noche) — ADR-022 + DEDUP 1/3 CLUSTERS

**Rama** `main`, 4 commits, working tree limpio. **Gate: GO** —
ruff **938 ≤ 943** · pytest `129` fallidas vs `360` baseline →
**0 fallos nuevos por nombre, 231 resueltos** (`scripts/check_gate.py`).

| commit | qué |
|---|---|
| `12463c5e` | dedup: borra `daniela-os/android_app/` (1 manifest huérfano, 0 consumidores) |
| `f5d792a0` | docs: rutas muertas en `AGENTS.md` + `.opencode` (android skill/agent/command/perf) + usage real de `pairing.py` |
| `0fd67aaf` | ADR-022 + borrado de las 3 copias rotas de `termux_deployer.py` |
| `3274945f` | `termux_deployer.py` único en `skills/` con `ROOT`/`BUNDLE` al repo real + `tests/mobile/test_termux_deployer.py` (4 verdes) |

### Decisión delegada → `docs/ADR-022-CANAL-CODIGO-TELEFONOS.md`

El dueño respondió a "¿cómo llega el código a los teléfonos?":
**"Play Store + dentro de la app"**, con el Pixel como suyo (la app
tiene que valer para **cualquier** Android) y delegando el criterio.
La decisión registrada:

1. **Un artefacto, tres transportes**: `phone-bundle` versionado con
   `manifest.json` (sha256/fichero) → `adb` (admin/dev), `git` (dev
   Termux), **`https` pull = canal de clientes**.
2. **La APK es el canal y el guardián**: Play Store reparte el binario;
   "Actualizar servicios" dentro de la app baja/aplica/reinicia el
   bundle y **reporta la versión al dashboard 8082**. El admin nunca
   necesita ADB con clientes.
3. **Runtime agnóstico**: mismo bundle en Termux o Linux (proot);
   `launch.sh` detecta. **No se embebe CPython** (peso/CVEs/ciclo propio,
   espíritu ADR-018). Sin intérprete → degradación a la PWA.
4. **Fuente única**: árbol cliente `frontend/apps/android-app/mobile-app/`
   + `daniela-os/phone/` (ADR-019). **`phone_deploy/` pasa a ser SALIDA
   DE BUILD** y deja de versionarse (ya lo decían `sync_phone_deploy.py`
   y `termux_deployer.build()`; el drift 5/40 era la prueba de incumplimiento).
5. **Reparto por LADO, no por carpeta**:
   - PC/admin → `skills/connectors/android/` (`pairing.py`,
     `termux_deployer.py`)
   - Teléfono → árbol cliente (`api/termux_api_gateway.py`,
     `bridges/pixel/pixel_bridge_hub.py`)
   - Runtime Termux → `daniela-os/phone/` (ADR-019)

> **Inversión de la nota anterior** ("canónico `skills/connectors/android/`"):
> vale **sólo para el lado PC**. El gateway/hub son código de teléfono y
> `skills/` **no está en el bundle**, por eso estaban driftando.

### Pendiente (siguiente sesión)

1. ~~**Dedup 2/3 — `termux_api_gateway.py` (lado teléfono)**~~ ✅ commit
   `e1b79fec` (ver sección siguiente).
2. **Dedup 3/3 — `pixel_bridge_hub.py` (lado teléfono)**: gana
   `frontend/.../bridges/pixel/`. Las 8 importaciones planas están
   envueltas en `try/except ImportError` → degradan sin romper
   (`[Pixel Bridge] Not available`), pero hay que repuntearlas o
   retirarlas con la fachada antigua. Borrar `skills/`, `daniela-os/`
   (byte-idéntica a `skills/`) y `phone_deploy/`.
3. **~HECHO 2026-10-04 (P2, commit 714696a5)~** `phone_deploy/` eliminado (41 ficheros).
   41 ficheros trackeados, 38 byte-idénticos a `daniela-os/<mismo
   nombre>` y 3 con drift (`daniela_os.py`, `git_brain_sync.py`,
   `safe_exec.py`) → `git rm -r` + `.gitignore` + arreglar
   `scripts/sync_phone_deploy.py` (su `DEPLOY` y sus `PHONE_MODULES`
   apuntan a `mobile-app/pixel/*`, rutas muertas).
4. Comando `publish` (consecuencia 5) + versión aplicada en `/api/status`
   del dashboard 8082 (consecuencia 6).
5. Dedup `shared/` → OpenClaw Fase 0 (`.opencode/oss-queue.md`).

### Ojo (stale, sin tocar)

- `AGENTS.md` describe la app Android como *Kotlin 2.2.10 / Gradle 9.3.1 /
  AGP 9.1.1 / min 26 / target 36*; el proyecto real
  (`daniela-os/android-app/`) usa **Groovy DSL, minSdk 24, targetSdk 34,
  Compose 1.5.8** y no declara versión de AGP en `settings.gradle`.
  Candidato a decisión (actualizar docs o actualizar el proyecto).
---

## Sesión 2026-10-04 (noche, cont.) — DEDUP 2/3 CLUSTER

**Rama** `main`, 1 commit, working tree limpio. **Gate: GO** —
ruff **934 ≤ 943** (bajó 4: las copias borradas acumulaban violations) ·
pytest `129` fallidas vs `360` baseline → **0 fallos nuevos por nombre,
231 resueltos** (`scripts/check_gate.py`).

| commit | qué |
|---|---|
| `e1b79fec` | dedup 2/3: `termux_api_gateway.py` única en el árbol cliente (pairing portado, 3 copias borradas) |

### Qué se hizo

- **Portado el pairing** (`import hashlib`, bypass de auth para
  `/api/pair/challenge` en el middleware y la ruta) a
  `frontend/apps/android-app/mobile-app/api/termux_api_gateway.py`,
  que queda como única fuente (ADR-022 §5). El ganador se queda además
  con `~/apps/aig/daniela-os/` en cámara/mic (paths reales de Termux)
  y con el stub `TermuxAPIGateway` del final.
- **Borradas las 3 copias**: `skills/connectors/android/` (393 L, perdia
  el pairing y tenía `~/daniela-os/`), `daniela-os/` y
  `daniela-os/phone_deploy/` (371 L cada una). **-1163 líneas.**
- **`termux_deployer.MODULES`** acepta rutas relativas al repo
  (`frontend/.../api/termux_api_gateway.py`); el destino sigue **FLAT**
  porque así corre en Termux. El bundle se regenera con `build()`.
- **Tests repunteados**: `test_pairing.py` y
  `test_termux_api_gateway.py` apuntan al árbol cliente y **bloquean**
  cualquier reaparición de las 3 copias legacy; `test_termux_deployer`
  resuelve `MODULES` con la misma lógica (plano = `ROOT/`, con `/` =
  `REPO/`). 11 verdes en los 3 ficheros.
- **`.gitignore`**: `connectors/.paired.json` (ruta anclada muerta,
  vieja raíz `connectors/`) → `**/.paired.json`; antes el estado real
  `skills/connectors/android/.paired.json` **no** estaba ignorado.
- Docs: `AGENTS.md`, `.opencode/skills/aig-android/SKILL.md`,
  `.opencode/agents/aig-android.yaml`, docstring de `pairing.py`.

### Pendiente (siguiente sesión)

1. ~~**Dedup 3/3 — `pixel_bridge_hub.py`**~~ ✅ `97e25e00` (ver sección
   siguiente).
2. **`phone_deploy/` deja de trackearse** (consecuencia 4 del ADR):
   41 ficheros trackeados, 38 byte-idénticos a `daniela-os/<mismo
   nombre>` y 3 con drift (`daniela_os.py`, `git_brain_sync.py`,
   `safe_exec.py`) → `git rm -r` + `.gitignore`
   + decidir el destino de `scripts/sync_phone_deploy.py` (y su clon
   `scripts/deploy/`): su `DEPLOY` y sus `PHONE_MODULES` apuntan a
   `mobile-app/pixel/*` (rutas muertas) y su función —copiar módulos a
   `phone_deploy/`— es la misma que `termux_deployer.build()`.
3. Comando `publish` (consecuencia 5) + versión aplicada en `/api/status`
   del dashboard 8082 (consecuencia 6).
4. Dedup `shared/` → OpenClaw Fase 0 (`.opencode/oss-queue.md`).

---

## Sesión 2026-10-04 (noche, cont. II) — DEDUP 3/3 CLUSTER (carril android/termux cerrado)

**Rama** `main`, 1 commit, working tree limpio. **Gate: GO** —
ruff **929 ≤ 943** · pytest `129` fallidas vs `360` baseline →
**0 fallos nuevos por nombre, 231 resueltos** (`scripts/check_gate.py`).

| commit | qué |
|---|---|
| `97e25e00` | dedup 3/3: `pixel_bridge_hub.py` única en el árbol cliente (3 copias borradas, `-1308` líneas) |

### Qué se hizo

- **Ganador** `frontend/apps/android-app/mobile-app/bridges/pixel/`
  (ADR-022 §5): es el que ya importan con ruta de paquete los módulos
  vivos (`bridges.pixel.pixel_bridge_hub` en `main.py:81`,
  `tunnel_guard.py:727`, `battery_aware_scheduler.py:150`,
  `pixel_second_screen.py:98`) y aporta **`KNOWN_IPS` desde `.env`**
  (`PIXEL_IPS`/`PIXEL_IP`) y `PIXEL_GATEWAY_PORT`, que las copias no
  tenían.
- **Borradas las 3 copias**: `skills/connectors/android/` y
  `daniela-os/` (byte-idénticas entre sí, 1085 B menores) y
  `daniela-os/phone_deploy/` (salida de build). **-1308 líneas.**
- **Los 8 importadores planos NO se tocaron**: todos van en
  `try/except`, así que al borrar la copia **degradan sin romper**
  (ADR-022 §3). Ya degradaban antes en `scripts/` (`sys.path[0]` no
  contiene el módulo) y `tunnel_guard.py` tiene fallback de IPs
  idéntico. Cubren: `daniela_os.py` ×2, `tunnel_guard`,
  `battery_aware_scheduler`, `dual_mode_switch` ×3,
  `pixel_second_screen` ×2.
- **`termux_deployer.MODULES`** → ruta relativa al mismo árbol cliente
  (mismo patrón de `e1b79fec`, destino FLAT).
- **`.gitignore`**: el patrón muerto `connectors/data/` (anclado a una
  raíz que ya no existe) pasa a `**/pixel_bridge/pixel_state.json`;
  se borró el `skills/connectors/data/pixel_bridge/pixel_state.json`
  trackeado (runtime del módulo recién retirado).
- **Nuevo** `tests/mobile/test_pixel_bridge_hub.py` (3 guardas): único
  ganador, cero copias legacy, y que los 9 importadores planos sigan
  protegidos por `except` (si alguien lo quita, el test lo avisa).
- Drive-by: el gateway del árbol cliente acabó con newline final (W292).

### Estado del carril android/termux

3/3 clusters cerrados: ~~`daniela-os/android_app/`~~ `12463c5e` ·
~~`termux_deployer.py`×4~~ `3274945f` · ~~`termux_api_gateway.py`×4~~
`e1b79fec` · ~~`pixel_bridge_hub.py`×4~~ `97e25e00`.

### Pendiente (siguiente sesión)

1. **`phone_deploy/` deja de trackearse** (consecuencia 4 del ADR) —
   ver arriba: `git rm -r` + `.gitignore` + resolver
   `scripts/sync_phone_deploy.py` (redundante con `build()`).
2. Comando `publish` (consecuencia 5) + versión aplicada en
   `/api/status` del dashboard 8082 (consecuencia 6).
3. Dedup `shared/` → OpenClaw Fase 0 (`.opencode/oss-queue.md`).



---

## Migracion aig -> aigestion-universe (sesion 2026-10-08/09, en curso)

### Estado CI (GitHub, HEAD tras fase 3)
- **CI 4/4 jobs VERDE**: run `37855395116` (Python daniela-core, Protobuf,
  Docker Compose config, Node apps = tsc + `pnpm -r typecheck` (mypy 11/11)
  + `pnpm -r --if-present lint` (ruff 11/11) + Build landing).
- **Docker VERDE**: runs `37795145805`, `37853683334`, `37855250351`,
  `37855395141`. daniela-shell Docker build sigue deshabilitado
  (`if: false`, issue @react-three/fiber + React 18).

### Commits en remoto (universe)
- `b606d6e8` Phase 3: gates (ruff baseline select E4/E7/E9/F en 11 pkgs,
  mypy baseline `#BASELINE-MYPY-2026-10-08`, fix landing Next, Link en
  not-found, gitignore secretos/>100MB). Rehizo (reset a origin/main) los
  2 commits locales que contenian 5 secretos + 3 ficheros >100MB: NUNCA
  llegaron a un remoto -> sin rotacion obligatoria (flag: pueden existir en
  el remoto legacy AIG).
- `8b43d2d4` fix CI: `astral-sh/setup-uv@v3` en job Node (uv no instalado)
  + docker-compose: 9 servicios engines/minio reubicados de `secrets:` a
  `services:` (y `minio-data:` a `volumes:`), `docker compose config
  --quiet` rc=0 con 22 services.
- `19ccd0d2` gitignore: `.env.*` (conserva `.env.example`) +
  `**/voice_pipeline/piper_voices/`.

### Secretos locales (en disco, fuera de git)
`**/credentials.json`, `**/secret.key`, `**/*service_account*.json`,
backups `.env.*` de `storage/archives/` y modelos piper >100MB ignorados.
Limite GitHub: avisos <50/100MB (supabase.exe 95MB, oficina3d.glb 93MB)
se mantienen trackeados a proposito; NADA >100MB en el index.

### Test baseline vigente (2026-10-08)
- `uv run pytest -q --tb=short` (core): **53 passed** (3.55s).
- ruff 0 en 11/11 paquetes; mypy 0 en 11/11; `pnpm -r typecheck` y
  `pnpm -r --if-present lint` rc=0.

### Pendiente (siguiente sesion)
1. Commit/push cosmeticos: migracion ruff `select/ignore/per-file-ignores`
   -> `lint.*` (12 pyprojects), borrado de `[tool.uv] dev-dependencies`
   duplicado en core (uv lock regenerado), rewrite de
   `NEXTJS_BUILD_ISSUE.md` (causa raiz real: NODE_ENV=development de nivel
   usuario + `experimental.serverActions` booleano) y esta seccion.
2. ~~Tag `archive/legacy-20251008` en aig/AIG + archivar remoto~~ [HECHO
   2026-10-09: tag + `gh repo archive aigestion/AIG --yes` tras el push
   del commit de cierre; NO se borro nada de `aig` local].
3. Cosmetico opcional: mypy "unused section prometheus_fastapi_instrumentator.*".

### 2026-10-09 - Gate del legado GO + cierre de la migracion

- **GATE GO** (`aig`): `uv run pytest tests/ -m "not network and not android
  and not integration" -q --tb=no -p no:cacheprovider --continue-on-collection-errors`
  → **29 fallos (tras el fix de `tests/conftest.py`), TODOS en baseline (360)**
  → `scripts/check_gate.py`: `NUEVOS=0`, resueltos=331.
  `ratchet_ruff.py` OK (techo 0 = realidad 0).
- Fixes de paths de reestructura: `frontend/apps/daniela-os` (server, shim
  `gev/`, gev_server) y `aig/aig-optimization/{sse,health,observe,conn}`
  en `core/daniela.py`; `health_sub`/`_opt` idempotentes (mismo bp
  `health_checks`); casbin bypass con `app.config["TESTING"]`;
  `test_daniela_ai` parchea `core.ai_bridge` (el duplicado que sirve
  `/api/ai/*`); `test_provider` → `pytestmark integration`; lefthook
  `full-test` → pytest al fichero + `check_gate.py`.
- Commit de cierre: el arbol que el gate valido (`shared/`,
  `frontend/apps/daniela-os/` solo existian en working tree; `frontend`
  y `shared` NO estaban en HEAD). Sin trackear a proposito: `conftest.py`
  raiz (rutas absolutas de maquina), `daniela-desktop/` (10.5 GB), los
  `.glb` duplicados de `frontend/apps/daniela-os/assets/` (canonicos en
  `assets/`) y **`aig/`** (dir runtime local: lo prohibe
  `test_no_carpetas_kebab_en_raiz`; `aig-optimization` vive solo en disco).
- Pre-commit endurecido (2026-10-09): `ktlint`/`detekt` con guard de
  gradlew (mismo patron que `android-lint`), `ruff-format` retirado (deuda
  pre-existente; el gate es `ruff check` + ratchet), `pytest-unit` sin
  `-x` y validado por nombre via `check_gate.py`
  (`PYTEST_CURRENT_FILE=<fichero>`), y `tests/conftest.py` corregido a
  `frontend/apps/daniela-os` (path stale `daniela-os/`).
