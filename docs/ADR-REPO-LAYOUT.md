# ADR-001 — Layout del repo: paquete `aig/` por dominio + shims en raíz

**Estado:** aceptado (piloto `agents/` ejecutado 2026-09-11)
**Contexto:** 242 `.py` en raíz, imports frágiles, clones en `phone_deploy/`.

## Decisión

Estructura objetivo (Fase 2):

```
aig/
  core/       core.py, adapters.py, auth/billing/analytics
  agents/     agent_*.py, agents.py, swarm_intelligence.py        ← PILOTO HECHO
  content/    content factory, brand kit, viral, calendar
  pixel/      pixel bridge, battery, termux, sensors
  sil/        sil_engine.py, autofix
daniela_os.py api_gateway.py admin_panel.py                      ← apps (raíz)
phone_deploy/                                                     ← GENERADO
```

Reglas:

1. **Un dominio por vez, con shims.** Cada fichero movido deja un shim en
   raíz (`from aig.<dominio>.<mod> import *`) durante 1–2 sprints
   para no romper Termux/Pixel/scripts externos.
2. **`__init__.py` ligeros.** Sin re-exports eager: coste de arranque
   en Termux/Pixel y riesgo de ciclos.
3. **Rutas de datos a raíz de repo.** Constantes tipo `OUTPUT_DIR` se
   resuelven con `_REPO_ROOT` (3 × `dirname` desde `aig/<dom>/`),
   nunca con `dirname(__file__)` a secas.
4. **Loader multi-ruta.** `aig_adapters.load_module()` busca en
   raíz + `agents/` (extensible a más dominios).
5. **`phone_deploy/` se genera.** Fuente de verdad = raíz (luego el
   paquete). `python scripts/sync_phone_deploy.py --check` debe dar OK.
6. **No mover sin smoke.** Por dominio: `core status` + `health` +
   test de chat + `ruff` + `sync --check`, todo verde antes del commit.

## Piloto `agents/` (2026-09-11)

Movidos 8 ficheros, 8 shims, 3 fixes de rutas (`calendar_events.json`,
`data/documents`, `static/brand`), loader multi-ruta, 1 import muerto
eliminado (`list_queue`). Health 9/10 (igual que baseline: solo falla
`content_factory`, preexistente — `content_factory_ai.py` no existe).
`swarm_intelligence.py` no expone `SwarmCoordinator` (solo
`SwarmIntelligence`): el adapter ya devolvía stub y sigue igual —
pendiente Fase 3 (swarm real).

## Piloto `core/` (2026-09-11)

Movidos `aig_core.py` + `adapters.py` → `aig/core/`,
2 shims en raíz. Particularidades de este dominio (el que todo importa):

- **Cero imports top-level** del core en toda la raíz: `api_gateway.py` y
  `daniela_os.py` cargan por ruta de fichero (`importlib`) y lazy
  `from aig_core import ...` en funciones → shims 100% transparentes,
  cero cambios en consumidores.
- **`CONFIG_PATH` fijado a repo root** (`_REPO_ROOT =
  parents[2]`): sin el fix el core creaba un config virgen en
  `aig/core/` ignorando el `aig_config.json` real.
- **`MODULE_SEARCH_PATHS` re-anclado a repo root** (antes colgaba de
  `MODULES_DIR`, que ahora es `aig/core/`).
- **Shims con delegación `__main__ → main()`** donde el módulo real
  define `main()` (core, adapters, agent_epic_ideas): el smoke
  `python aig_core.py status` sigue funcionando idéntico.
  Los shims de agentes con solo bloques `demo()` quedan como shims
  de importación puros (las demos nunca fueron contrato).
- **`phone_deploy/` sigue recibiendo el módulo REAL en plano**:
  `scripts/sync_phone_deploy.py` acepta entradas como
  `aig/core/aig_core.py` (src) con dst = basename, así
  Termux no nota el empaquetado. Verificado: la copia del teléfono
  contiene `class AIGestionCore`, no el shim.

## Piloto `content/` + `sil/` (2026-09-11)

4 ficheros → `aig/content/`, 2 → `aig/sil/`, shims + fixes
`BASE_DIR`/`PROJECT_ROOT` a repo root. Hallazgo: `content_factory_ai.py`
tiene un **SyntaxError preexistente** (f-string con backslash, línea 575,
en HEAD) — el adapter ya lo toleraba (devuelve error) y el shim conserva
el comportamiento exacto. Fix pendiente (Fase 3, no packaging).
`sil_engine.py status` vía shim lee el estado real (health 72/100):
sin dirs parásitos en el paquete.

## Dominio `pixel/` (2026-09-11, cierra Fase 2)

36 ficheros → `aig/pixel/` (todos los `register_*_routes` de
`daniela_os.py` + battery + termux gateway), 36 shims, `daniela_os.py`
**sin tocar** (precedente core: consumidores intactos).

- **Grafo acíclico verificado** por AST antes de mover: 12 aristas
  hoja→hub, cero pares mutuos → shims top-level terminan siempre.
- **35 `PROJECT_ROOT`/`DATA_DIR` re-anclados** a repo root (todos eran
  `data/...`, `templates/...`, globs de repo, `cd` de daemon): verificado
  por uso, no por inspección visual.
- **Lint triado, no ciego**: `--fix` solo para W293/I001/F401 de
  stdlib/typing; a mano y con verificación: 4 nombres `safe_exec`
  recortados (ocurrencia única = import), E741 `l→les/line`,
  2 dead stores `freq` en `ir_bridge` (scope-verificados),
  `zeroconf` conservado con `noqa` (sonda opcional intencional).
- **Smoke duro**: `daniela_os` registra **242/242 reglas** antes,
  después del move, después del lint y después del resync.
- **Sync**: 31 entradas de `PHONE_MODULES` remapeadas a
  `aig/pixel/<mod>` (dst = basename, Termux en plano);
  `battery_aware_scheduler` y `model_router` nunca estuvieron en la
  lista del teléfono — no se añaden (fuera de alcance).
- `safe_exec.py`, `auto_sanitizer.py`, `message_broker.py`,
  `autofix_watchdog.sh` quedan en raíz (infra transversal / no-Python):
  documentado, no olvidado.

# ADR-002 — Fase 3: swarm real + scoreboard honesto (2026-09-11)

## Swarm real (`agents/swarm_intelligence.py`)

- Capas: **router E-32 → simulado honesto**. Cada tarea intenta LLM
  vía `model_router.responder()`; sin clave usable o con fallo, degrada
  a simulación con `mode + motivo` en el reporte (nunca finge).
- **Placeholder guard**: `REPLACE_WITH_*`/etc no cuentan como clave
  (Fase 0 las redactó; llamar con ellas quemaría timeouts).
- **Ollama TCP probe (3 s)**: `OLLAMA_HOST` configurado ≠ reachable.
  Sin esto, un Ollama muerto colgaba cada tarea hasta TIMEOUT_LOCAL
  (150 s) — observado en smoke (70 s/tarea) antes del fix.
- **Exec log** `data/swarm/exec_log.jsonl` (nunca rompe la misión):
  es la fuente del scoreboard. Tokens = chars/4 **estimados**
  (el router no expone usage; etiquetado).
- **`SwarmCoordinator.dispatch(task, agents)`** (fachada sync):
  infiere tipo (code/research/analysis/content), crea misión,
  ejecuta, devuelve reporte con `mode` global. El adapter del core
  (`do_default` → `do_dispatch`, + `do_status`/`do_results`) deja
  de devolver stub: `core.ask("coordinar swarm para X")` ejecuta
  de verdad (4 s simulado sin claves; minutos en live con claves).
- Probado: rama `live` con mock (4/4 live), rama `simulated` sin
  claves (4/4), una ejecución live real contra Ollama local
  (`daniela-local:latest`, 68 s) quedó registrada en el log.

## Scoreboard (`agents/agent_scoreboard.py`, idea #8)

Tres señales reales: `core.health()+status()` por módulo (ok/degraded/
down), exec_log (live_ratio, tokens_est, success_rate), "sin datos"
cuando no hay datos. CLI (`python agent_scoreboard.py [--json]`) +
rutas `/api/scoreboard`, `/api/scoreboard/summary` (test_client 200) +
bloque guarded en `daniela_os.py` (242 → 244 reglas). Shim en raíz
con delegación CLI. No va a `phone_deploy` (el guard lo degrada
limpio en Termux).

# ADR-003 — Fase 3 extendida: code-gen, vault, squad, SIL semanal (2026-09-11)

## `aig/core/llm_client.py` (nuevo, compartido)

Una sola puerta al router E-32: `llm_available()` (placeholder guard +
Ollama TCP probe) + `llm_call()` (nunca lanza). Swarm y code-gen lo
usan; el swarm se refactoreó a él sin cambio de comportamiento
(smoke: mismo dispatch simulado en 4 s).

## Code-gen real (`code_generation_agent.py`, raíz: Quick Win sin dominio)

- `generate(description, language="python")`: el 2º parámetro además
  **arregla un TypeError latente** (el adapter llamaba con 2 args).
- LLM (código + tests propios) o template honesto (`mode`).
- Sandbox `safe_exec`: tmpdir + `sys.path` auto-inyectado + pytest con
  ruta absoluta (un smoke cazó ruta relativa) + timeout 120 s.
- Resultado extiende dataclass (`mode`, `tests_passed`, `test_output`,
  defaults compatibles). Adapter `do_default→do_generate`: el chat
  ejecuta de verdad (cuidado con queries ambiguas: "emails" gana
  a "codigo" por orden del KEYWORD_MAP en empates — preexistente).
- Verificado: template 1 failed/2 passed (stub demostrado), LLM mock
  `complete` con 0 errores.

## Memory Vault v2 (`agents/memory_vault.py`, idea #4)

SQLite stdlib (sin FTS5 en este build → scoring TF en Python),
`memory_links` auto-creados por solape ≥2 tokens (cap 5), recall con
**expansión a 1 salto incluso sin solape directo** (el primer diseño
solo expandía matches directos: inútil). CLI record/recall/stats +
shim. DB en `.gitignore`.

## Squad bridge (`agents/agent_squad.py`)

5 personajes → agentes reales, acciones de **solo lectura**,
constructores verificados sin efectos laterales. `briefing_diario()`
escribe `static/brand/squad_briefing.json` (entrada del calendar,
fuera de git) y registra en el vault (`squad/<personaje>`).
Smoke: 5/5 OK (Vigía: CPU 24% real). CLI + shim.

## SIL semanal (`scripts/sil_weekly.py` + `docs/SIL-WEEKLY-JOB.md`)

Modo local seguro por defecto (review/lessons-export/dashboard +
scoreboard; rc honestos + reporte JSON en `data/sil/`); `--full`
añade dispatch/verify (Jules, documentado como riesgo). Smoke real:
3×rc 0. Cron + schtasks + Termux documentados.

# ADR-004 — Daniela Continuum, cerebro nocturno (idea #1, 2026-09-11)

`agents/agent_continuum.py` + shim + `docs/CONTINUUM.md`.
Repaso: briefing fresco + vault recall + SIL (state/trend/dispatch) +
scoreboard → 3 acciones por reglas con `porque` → digest JSON+MD
(ignorados por git) + record `continuum/resumen`.

Bugs cazados en smoke: digest JSON escrito ANTES de vault/ficheros
(reordenado: vault → escribir → reescribir completo); títulos de
recurrentes ausentes en abiertos (fallback al dispatch_log).
`--auto` encola 5 tareas en `dispatch_log` (queued, local sin claves
Jules). stdout `--json` mezcla logs de core (preexistente en todos
los CLI; el JSON canónico es el fichero). Digests verificados:
SR-05 recurrente, deterioro 72→25, live_ratio real del swarm.

# ADR-005 — Pixel Edge Node, worker del swarm (idea #2, 2026-09-11)

Servidor `aig/pixel/edge_node.py` + worker `edge_worker.py`
(raíz, en `phone_deploy`) + `docs/EDGE-NODE.md`.

- Cola por log de eventos con lease TTL (300/900 s) y reintentos (3→dead);
  `data/edge/` ignorado. Redis solo aviso best-effort (`no_configurado`
  sin REDIS_URL).
- Política batería vía scheduler: full→todo, normal→sin pesadas,
  save→solo prioridad 0 (el código permitía todo `low` en save:
  corregido a urgentes para igualar el doc). Cargando = full.
  Sin dato de batería: conservador (normal).
- Protocolo verificado contra servidor live: claim → `no_soportado`
  honesto (PC sin GPS) → done; lease respeta reclamos ajenos
  ("cola vacia"); 244 → 248 reglas.
- Worker Termux-aware con capability matrix documentada (estado y
  geofence reales en Pixel; voz parcial honesta; OCR si hay tesseract).
  Solo stdlib + requests + safe_exec.
- Shim `edge_node.py` en raíz; `edge_worker.py` ya vive en raíz.

# ADR-006 — Zero-Inbox Court (idea #5, 2026-09-11)

`tribunal` en `agents/agent_court.py` + shim + CLI + 4 rutas
(248 → 252) + `docs/ZERO-INBOX-COURT.md`.

- Zonas por confianza calibrada v1 (spam .93/news .90 auto; resto
  gris con borrador). Spam ambiguo → gris (fallar hacia el humano
  es diseño). Borradores en `data/court/` (nunca se envían: sin
  OAuth no hay envío; documentado).
- `email_zero_inbox.py` suma `classify_email`/`generate_reply` a
  nivel de módulo: el adapter del core los esperaba y devolvía stub.
  `EmailAdapter.do_default` clasifica texto pegado (sender "chat").
- Feedback loop (`feedback.jsonl` + `tasa_aprobacion` en stats):
  cierra el gap auditado "sin feedback"; calibración manual futura.
- Vault: decisiones en `court/decisiones`.

# ADR-007 — Invoice Truth Graph (idea #4, 2026-09-11)

Grafo en `agents/agent_invoice_graph.py` + shim + CLI +
4 rutas (252 → 256) + `docs/INVOICE-TRUTH-GRAPH.md`.

- Ledger `data/invoice/ledger.jsonl`; grafo derivado (proveedores,
  duplicados exactos/probables, 6 señales documentadas).
- `puedo_pagar()`: smoke AcerosX — nuevo+alto→revisar, probable→
  revisar, exacto→**bloquear** (auditor y grafo de acuerdo).
- Auditor: alias `audit()` (el adapter explotaba con AttributeError)
  + E722 preexistente estrechado; `invoice_*.json` del auditor a
  `.gitignore`. Adapter `do_default` audita dicts.
- Veredictos revisar/bloquear → vault (`invoice/alertas`).
- No lee facturas reales ni ejecuta pagos: propuestas registradas.

# ADR-008 — Meeting → Expediente (idea #6, 2026-09-11)

Puente en `agents/agent_expediente.py` + shim + CLI +
2 rutas (256 → 258) + `docs/MEETING-EXPEDIENTE.md`.

- Usa API española real (el adapter llamaba constructor + métodos
  ingleses inexistentes → reescrito + `do_default` + `do_expediente`).
- Acta en `data/documents/` + evento por action item en calendario
  + vault + ledger. Fechas ES por reglas (próxima ocurrencia
  estrictamente futura; +7 etiquetado sin fecha).
- Bugs: acta fantasma ADS por `:` en título (saneado en
  `agent_documentos` + `import re`); regex sin variante `manana`.
- `calendar_events.json` (trackeado con datos) y
  `meeting_history.json` fuera de git (runtime, precedente Fase 0).

# ADR-009 — Content OS (idea #7, 2026-09-11)

Pipeline en `aig/content/content_os.py` + shim + CLI + 2 rutas
(258 → 260) + `docs/CONTENT-OS.md`.

- Factory→brand (CTA+hashtags)→viral (hook+límites reales)→calendar
  (`ContentSlot`+`BEST_TIMES`, su esquema)→preview HTML real→
  `multi_post` (`en_cola`/`sin_canal`, nunca "publicado" fingido).
- Resucitado `content_factory_ai` (SyntaxError desde HEAD; helper
  `_slug_archivo`) → adapter real sin tocarlo.
- Cola social persistida (`data/social/cola.json`; era amnésica).
- Consola Windows: `_imprimir()` ante emojis en stdout (ledger es
  la interfaz canónica).
- Video-factory excluida a propósito (otro medio).

# ADR-010 — Safe Evolution Gate (idea #9, 2026-09-11)

`aig/sil/safe_gate.py` + shim + `githooks/pre-push` +
`docs/SAFE-EVOLUTION-GATE.md`. Sin rutas HTTP a propósito
(operar git por red al repo prod = footgun).

- Gate = trabajos cerrados de `ci_runner` (quick ~5 s, full con
  arranque/mypy/pytest). `fusionar_si_verde` aborta sin fusionar
  ante cualquier fallo.
- `test_and_apply_fix` ya NO commitea en la rama actual: rama
  `autofix/*` + commit + gate + vuelta; merge solo con
  `merge_if_green` y gate verde.
- El propio smoke demostró el problema: con el código viejo (stash
  mediante), el autofix commiteó basura directo a universo-v1
  (commit revertido con reset; ramas temporales borradas).
- Limpieza para el verde: RCE por chat en `server.py:88`
  neutralizado, `Popen("sync")` fuera, `swarm_planner` y
  `nightly_maintenance` a `safe_exec` sin shell.
- Hook validado por comando (sin `sh` en este Windows para
  ejecutarlo literal; instalacion por `core.hooksPath`).

# ADR-011 — White-Label in a Box (idea #12, 2026-09-11)

`docker-compose.enterprise.yml` + `scripts/deploy/tenant_bootstrap.py` +
`docs/WHITE-LABEL.md`. Un tenant por stack, sin tocar su código.

- Bootstrap: brand CSS/HTML + white-label config + admin auth
  (enterprise/admin, password aleatoria una vez) + suscripción
  enterprise + PIN + DBs inicializadas + `.env` (todo en `tenants/`,
  ignorado). Truco necesario: los módulos abren SQLite por nombre
  relativo → todo lo que escribe DBs corre con cwd=tenant.
- Override compose validado con `docker compose config` (Docker
  29.7.2): 2 bugs cazados — `:?` no vale en nombres de volúmenes
  top-level; la lista redis se fusionaba mal → redis compartido
  a propósito (caché volátil).
- Precedencia compose real: el PIN efectivo sale del SHELL
  (environment: gana a env_file); el `.env` del tenant es registro.
- Límites: un tenant por stack (`-p`); `static/` compartido salvo
  `static/tenants/<slug>/`; multi-tenant en un stack = futuro.

# ADR-012 — Second Screen Command (idea #11, 2026-09-11)

HUD en `/pixel-dashboard`: sección Pendientes (court + invoice +
edge) con taps que ejecutan (`decidir` / `visto` / `reencolar`).
2 rutas (260 → 262), template con botones, `docs/SECOND-SCREEN.md`.

- `_leer_ledger(solo_facturas=False)` para el HUD (el filtro
  `ev==factura` lo cegaba; `red()` intacto).
- Bonus: `/api/pixel/dashboard/data` daba 500 desde siempre
  (`app.jsonify`); corregido a `flask.jsonify`.
- Invoice `visto` = acuse, no reescribe el grafo.

# ADR-013 — Mesh Offline-First (idea #3, 2026-09-11)

Outbox en `aig/pixel/mesh_outbox.py` + shim + CLI + 3 rutas
(262 → 265) + `docs/MESH-OFFLINE.md`. Va también a `phone_deploy`
(37 módulos: el teléfono es quien más lo necesita).

- Aplicar en local al encolar + cola cifrada (vault, fail-closed,
  troceado 6K) + drain a peers/documentos + ledger de eventos.
- Red: forzar > termux-wifi > peer TCP; sin peers = offline.
- Smoke: offline-first leído, log sin plaintext, PIN mal rechazado,
  vaults cruzados fallan por op (honesto), drain HTTP 2/2 con bytes
  exactos, fold (dead/lease) unit-testeado.
- El vault real tiene PIN de operador (2 secretos preexistentes):
  no se toca; smoke con vault simulado + documento de límites.

# ADR-014 — Open CADStudio (idea epica, 2026-09-11)

`agents/agent_cad_studio.py` + shim + CLI + adapter
(`cad_studio`, intent `cad`) + 2 rutas (265 → 267) + `docs/CAD-STUDIO.md`.

- Biblioteca offline (RPi5+VESa, caja, soporte) con bounds; LLM
  (Groq primero) para piezas libres; `llm_call` suma `proveedor=`.
- Validacion sin kernel + volumen por primitivas CON sustitucion
  de params (sin ella daba 0.22 cm3 para una carcasa de 164).
- BOM con supuestos etiquetados; exports con toolchain ausente =
  `no disponible` + receta (verificado: sin openscad/freecad).
- Cola persistente? No: ledger + vault + `--publicar` explicito.

## Consecuencias

- `import agent_correo` y `from aig.agents import agent_correo`
  devuelven los **mismos objetos** (verificado en smoke).
- `agents/` (minúsculas, solo `templates/*.md`, sin `__init__.py`) no
  colisiona con el shim `agents.py`.
- Próximos dominios candidatos: `core/`, `content/`, `sil/`. (En 2026-09-29
  `pixel/` **descartó** ser dominio propio: es el código del teléfono y vive
  agrupado por destino en `mobile-app/services/`, `mobile-app/bridges/` y
  `mobile-app/core/`; ver ADR-016.)

---

# ADR-015 — El layout REAL tras el merge del PR #109: **gana la raíz** (2026-09-17)

**Estado:** aceptado. **No se cambia nada**; se documenta lo que hay.
**Contexto:** ADR-001 fijó como objetivo `aig/<dominio>/` + shims en raíz.
El merge del PR #109 **resucitó las copias de la raíz**, así que hoy `import X`
resuelve a la raíz, no al paquete. Medido, no supuesto.

## Lo que pasa de verdad

```
$ ls *.py | wc -l
231                     # antes del merge eran 4

$ python -c "import tunnel_guard; print(tunnel_guard.__file__)"
C:\Users\Alejandro\aig\tunnel_guard.py     # la RAÍZ, no aig/pixel/
```

`tunnel_guard.py` existe **cinco veces**:

| Fichero | Líneas | |
|---|---|---|
| `tunnel_guard.py` (raíz) | **1133** | ← **esta es la que se importa** |
| `aig/pixel/tunnel_guard.py` | **1155** | 🔴 código **DISTINTO** |
| `core/tunnel_guard.py` | 1133 | |
| `scripts/archive/tunnel_guard.py` | 1133 | código muerto |
| `scripts/tunnel_guard.py` | 5 | shim |

🔴 **El shim miente.** Su docstring dice *"la fuente de verdad vive en
`aig/pixel/tunnel_guard.py`"* y hace `from aig.pixel.tunnel_guard
import *`. Pero `import tunnel_guard` —lo que hace el código real— devuelve el de
la **raíz**, que es **otro fichero**. Quien se fíe del docstring editará un módulo
que no se ejecuta.

## Cuánto hay duplicado (medido 2026-09-17)

| Medida | Valor |
|---|---|
| Copias con contenido **idéntico** (sha1) | **505**, en 310 grupos |
| Nombres de fichero repetidos | **389** (1.305 ficheros) |

Copias redundantes por directorio: **raíz 183**, `scripts/` 170, `core/` 40,
`phone_deploy/` 39, `aig/` 13.

**Casi todas son ESTRUCTURALES, no accidentes:**

- `scripts/X.py` = **shims de 5 líneas** con docstring (decisión de ADR-001).
- `Dockerfile` **x26** y `server.py` **x27** = los 19 microservicios.
- `__init__.py` **x104** = paquetes normales.
- `phone_deploy/` es **generado** (`scripts/sync_phone_deploy.py`).
- Las de la raíz son, precisamente, las que **ganan** al importar.

## Decisión

**NO se consolida nada.** Motivos, por orden de peso:

1. **Las copias de la raíz son las que se ejecutan.** Borrarlas no "limpia":
   rompe el sistema entero.
2. **Los shims son intencionales** (ADR-001) y sostienen Termux/Pixel/scripts
   externos que hacen `import X`.
3. **Ya pasó una vez.** El merge del PR #109 resucitó las copias de la raíz y dejó
   231 `.py` donde había 4. Una limpieza a lo bruto repite el problema al revés.
4. **El radio de explosión es alto y no hay prisa**: los 505 ficheros no cuestan
   nada en runtime, solo confunden. Es deuda **documentada**, no invisible.

## La regla que hay que seguir (esta es la importante)

**Antes de editar un módulo, comprobar cuál se carga de verdad:**

```
python -c "import X; print(X.__file__)"
```

Editar `aig/pixel/X.py` **no tiene efecto** si la raíz tiene su copia.
Ya ha costado tiempo real más de una vez.

## Cuándo se podría abordar

Cuando haga falta de verdad, y **con red**: la suite está en **939 tests verdes** y
el CI ya ejecuta **los 34 ficheros de `tests/`** (commit `2b05af3ba`). Con el smoke
de `daniela_os.py` registrando **397 rutas** como referencia, un refactor por
dominio —como el de ADR-001— es viable. Hasta entonces: documentado y quieto.


---

# ADR-016 — Cliente único: `mobile-app/` agrupado por destino (2026-09-29)

**Estado:** aceptado. Rama `unificacion-20260929` (fusión con `origin/main`).

**Contexto.** El cliente vivía en tres árboles a la vez: `mobile-app/`,
`android_app/` (con `android_app/mobile-app/`, `android_app/pixel/` y
`android_app/phone_deploy/`) y copias sueltas en la raíz. Al fusionar, el
teléfono traía la migración a medias: muchos destinos canónicos eran
**stubs** (`class StereoVision: pass`, `class BTBridge: pass`) mientras la
implementación real seguía en las copias planas de 653/729 líneas.

**Decisión.**

1. `mobile-app/` es el único árbol de cliente, agrupado por destino según los
   `__init__.py` que trajo el teléfono (canónico > versión plana):
   `services/{sensors,security,mesh,ui,iot}/`, `bridges/{comms,pixel}/`,
   `core/{autonomy,context,ci}/`, `api/`.
2. Los destinos stub se rellenaron con la implementación real + alias de
   compatibilidad (`BTBridge = PuenteBluetooth`, `StereoVision = VisionEstereo`);
   el stub `services/sensors/geofence.py` se borró y su `__init__` apunta a
   `.geofence_engine`.
3. Regla de fusión de contenido: **nuestra versión completa + solo las
   inserciones del teléfono**. Nunca se aplican sus borrados (su copia estaba
   podada) ni sus bloques `replace` a ciegas. Verificado tras la reparación:
   **0** de nuestros cambios sobre la base ausentes y **69** líneas del teléfono
   aún pendientes (strings de log y renombres).
4. `mobile-app/` no es paquete Python (lleva guion): su `__init__.py` es solo
   documentación. Los subpaquetes se importan en plano con `mobile-app/` el
   primero de `sys.path` —lo hacen `main.py`, `run.py` y los shims de `scripts/`.
5. Imports reescritos en 188 ficheros: `android_app.X` → `X`, `from pixel.X` /
   `from phone_deploy.X` / imports desnudos → ruta canónica
   (`from bridges.comms.safe_exec import ...`).
6. Docker: se eliminó el `COPY ./mobile-app/pixel/ ./pixel/` de la imagen de
   Daniela y las líneas `!mobile-app/pixel` de `.dockerignore`;
   `core/llm_client.py` carga `mobile-app/core/autonomy/model_router.py` por
   ruta y degrada a "router no disponible" si la imagen no lo trae.
7. Se reescribieron los 42 shims de `scripts/` que importaban
   `aig.pixel.*` (paquete que **nunca** estuvo trackeado: siempre rotos)
   para que apunten al módulo canónico con bootstrap de `sys.path`.

**Consecuencias.**

- 205 `.py` en `mobile-app/`: todos compilan y **57/57** módulos canónicos importan.
- `mobile-app/pixel/` y `mobile-app/phone_deploy/` ya no existen: 154 ficheros
  trackeados borrados y 14 migrados a su grupo canónico.
- La colisión `core/` (raíz) vs `mobile-app/core/` queda acotada a los
  procesos que ponen `mobile-app/` primero en `sys.path`; `ia-services/hermes`
  y el resto de la raíz siguen viendo `core/` de raíz.

---

# ADR-017 — Daniela omnipresente: propiedad de Daniela OS (2026-09-29)

**Estado:** aceptado (regla explícita de producto).

**Regla.** *«Daniela omnipresente es una propiedad de Daniela OS.»*
Omnipresente no es un servicio aparte que compita con Daniela: es que
**Daniela esté siempre activa en el móvil y en el PC**, y que **si todo
falla, el estado se guarde en la nube**.

**Consecuencias técnicas.**

1. **Registro único**: `daniela.registrar()` (`daniela.py`, `FASES`) es la
   única puerta de entrada de rutas y ciclos de vida. God's Eye es una
   pantalla más de Daniela —en móvil y en PC—, no un proceso paralelo con su
   propio registro.
2. **Un solo dueño del puerto 9200**: `daniela-omnipresente/server.py` no
   puede ser un daemon independiente que compita por `9200`
   (`SERVICE_PORTS["daniela_omnipresente"] = 9200`). Se absorbe en `daniela.py`
   y su daemon duplicado (`daniela-omnipresente/daemon.py`, 177 L) se retira
   en favor de `gev/daniela-os/daemon.py` (181 L).
3. **Siempre activa en los dos extremos**: móvil (Termux, arranque en boot) y
   PC (docker compose / daemon de `gev/daniela-os/`).
4. **La nube es el respaldo, no una opción más**: `agents/memory_vault.py`
   hoy fija `DB_PATH = _REPO_ROOT / "memory_rag.db"` sin alternativa; el
   fallback a nube es parte de la regla, no una mejora opcional.

---

# ADR-018 — Sidecars: procesos ajenos, nunca dependencias nuestras (2026-09-30)

**Estado:** aceptado (criterio de arquitectura derivado de ADR-016/ADR-017).

**Regla.** *Todo runtime de terceros que adoptemos entra como **sidecar**
(proceso lateral o servidor MCP), nunca como dependencia pip del monorepo.*

**Decisión.** Sidecar, no dependencia: se ejecutan fuera del árbol de
dependencias (proceso aparte, contenedor aparte o servidor MCP). El repo
solo habla con ellos por HTTP/WS/MCP. Si un sidecar necesita tocar Daniela,
lo hace por Hermes (`:9900`) o `daniela.registrar()`. Fase 0 obligatoria
antes de nada (licencia, `requires-python`, telemetría, dependencias
nativas). Los sidecars no entran en el health gate de 13 servicios.

**Consecuencias.** Cero inflación de `pyproject.toml`; un lado cae sin
arrastrar al otro; los forks/patches de terceros no viven en nuestro
historial. Hay que mantener el puente (wrapper HTTP/MCP) y su contract
test. El sidecar puede morirse sin que el gate lo nota → el health gate
propio debe seguir siendo el criterio de verdad.

**Candidatos:** Vite (`gev`) en producción; `google/artemis` en
Fase 0/1; OpenClaw encolado.

> Fichero completo: `docs/ADR-018-SIDECARS.md`
