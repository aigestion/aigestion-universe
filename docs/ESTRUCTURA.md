# Estructura del repo — 2026-09-22

> Mapa de la organizacion actual, tras la reestructura del 2026-09-22
> (commit `623f10360`). Sustituye al layout que describia
> `docs/ADR-REPO-LAYOUT.md` (paquete `aig/` por dominio), que quedo
> obsoleto primero con el aplanado (`e2bb9a1bf`) y ahora con esta reestructura.

## 1. Principio

**Agrupar por dominio en la raiz, no por tipo de fichero.** Lo que antes estaba
suelto pasa a colgar de una carpeta que dice a que parte del sistema pertenece:

- el **nucleo** de la aplicacion -> `core/`
- el **visor y Daniela** -> `gev/`
- los **motores** -> `engine/`
- los **clientes** -> `mobile-app/`
- los **servicios de IA de terceros** -> `ia-services/`
- lo **retirado** -> `archives/`

La raiz tiene **80 carpetas y 39 ficheros sueltos**. Es mucho, y la seccion 7
explica que sobra.

---

## 2. La raiz, por bloques

### A. Nucleo de la aplicacion

| carpeta | que es | tamaño |
|---|---|---|
| `core/` | el nucleo: `server.py`, `api_gateway.py`, `model_router.py`, `core.py`, `health_checks.py`, billing, auth, `daniela/` | 277 ficheros, 54.5k lineas |
| `gev/` | visor 3D, OSINT, i18n, Command Center, billing + **`daniela-os/`** | 234 ficheros, 31.1k lineas |
| `engine/` | los **10 motores** (ver 3.1) | 88 ficheros, 28.1k lineas |
| `agents/` | los agentes (`agent_calendario`, `agent_redes`, `agent_vigia`...) + `api/` | 62 ficheros |
| `shared/` | el paquete **`aig_shared`** (el que se instala con pip) | 25 ficheros |
| `plugins/` | plugins de Daniela (36), `prometheus/` | 36 ficheros |
| `connectors/` | puentes a hardware y servicios: ADB, NFC, BLE, serial, Wi-Fi RTT, Google Workspace | 19 ficheros |
| `skills/` | skills empaquetables | 25 ficheros |
| `sil/` | SIL: `sil_engine.py`, `autofix_engine.py`, `safe_gate.py` | 3 ficheros |
| `ia-services/` | servicios de IA externos: `hermes/`, `tencent-suite/`, `google/` | 354 ficheros, 244 MB |

### B. Clientes

Todo el cliente vive bajo **un único directorio**: `mobile-app/`
(unificación de 2026-09-29; antes eran `mobile-app/`, `android_app/*` y en la
raíz otras dos copias de `pixel/` y `phone_deploy/`).

El código de cliente está agrupado por destino, siguiendo los `__init__.py`
que trajo el teléfono (canónico > versiones planas):

| carpeta | que es |
|---|---|
| `mobile-app/` | la PWA: `index.html`, `js/`, `css/`, `vendor/`, `assets/` + su `Dockerfile` |
| `mobile-app/services/{sensors,security,mesh,ui,iot}/` | servicios que corren en **el teléfono** — «Pixel» es el nombre del aparato, no un dominio |
| `mobile-app/bridges/{comms,pixel}/` | puentes: Termux, BT/IR/NFC/serie, ADB, FCM, hub del Pixel |
| `mobile-app/core/{autonomy,context,ci}/` | autonomía (malla, daemon, rutas, enrutador), contexto y CI edge |
| `mobile-app/api/` | `termux_api_gateway.py` (30 endpoints) |
| `mobile-app/main.py`, `run.py` | entrypoints (ponen `mobile-app/` el primero de `sys.path`) |
| `mobile-app/src/` | manifiesto Android huérfano (sin código asociado) |

Las copias planas que colgaban de `mobile-app/pixel/`, `mobile-app/phone_deploy/`
y `android_app/` están **fusionadas y borradas**: `mobile-app/pixel/` y
`mobile-app/phone_deploy/` ya no existen.

> El `Dockerfile` de la PWA copia esta carpeta a nginx: `mobile-app/.dockerignore`
> excluye el código Python (`services/`, `bridges/`, `core/`, `api/`, `src/`) para
> que no acabe publicado en el servidor estático.

### C. Servicios satelite

| carpeta | que es |
|---|---|
| `aig-optimization/` | cache, SSE, health, observabilidad, pool de conexiones (intocable, fuera del arbol principal) |
| `infra-opt/` | servicio de infraestructura |
| `perf-opt/` | servicio de rendimiento |
| `sec-opt/` | servicio de seguridad |
| `perf_tuning/` | `budgets.py`, `rightsize.py`, `slo.py` |
| `multi-region/` | escalado geografico: `dns_sim.py`, `Dockerfile.regions`, su propio compose |

> ⚠️ `optimization`, `infra-opt`, `perf-opt` y `sec-opt` son **cuatro copias del
> mismo esqueleto** (`Dockerfile` + `__init__.py` + `server.py` + `shared/` +
> `web/` + carpetas de dominio). Ver seccion 7.

### D. Datos y estado de ejecucion

| carpeta | que es |
|---|---|
| `data/` | bases de datos y catalogos (`aig_auth.db`, `agents_catalog.json`, `agent_activity/`) |
| `logs/` | logs locales (ignorado) |
| `output/`, `content_output/`, `media_exports/` | artefactos generados |
| `knowledge-db/` | `documents.json` |
| `drive-reports/`, `output-assets/`, `research/` | restos sueltos |
| `supabase/migrations/` | migraciones de BD |
| `tenants/` | vacio (multi-tenant declarado, no implementado) |

### E. Assets y contenido

| carpeta | que es |
|---|---|
| `assets/` | 3D, audio, broll, imagenes, video (186 MB) |
| `static/` | JS, CSS, brand, capturas |
| `templates/` | HTML de los dashboards |
| `external-assets/` | DanielaCloud, DanielaOS, DanielaOS_Docs, DanielaOS_Media |
| `vendor/` | `gev`, `web_app` (268k lineas de terceros) |
| `content/` | brand kit, calendario de contenido |
| `bin/` | binarios de Supabase (132 MB, **ignorado**) |

### F. Infra y despliegue

| carpeta | que es |
|---|---|
| `config/` | **7 ficheros de compose**, `nginx.conf`, `requirements.txt`, `Dockerfile.base` |
| `docker/` | compose de servicios auxiliares + `grafana/`, `homeassistant/`, `iot/`, `n8n/`, `nodered/`, `esphome/` |
| `nginx/` | `Dockerfile`, `nginx.conf`, `nginx.core.conf` |
| `deploy/` | `gods-eye/` |
| `ssl/` | `cert.pem` + `key.pem` locales (**ignorados**) |
| `security-hardening/` | `audit/`, `hardening/`, `penetration/`, `scanners/` |
| `load-testing/` | k6 + Locust + alertmanager + su compose |
| `.github/` | solo Dependabot: **cero Actions** (decision de costo). Los 4 workflows que traia `origin/main` estan en `docs/archive/workflows/` |
| `githooks/`, `.githooks/` | hooks de git |
| `.devcontainer/` | |

### G. Desarrollo y verificacion

| carpeta | que es |
|---|---|
| `tests/` | 1137 tests en `agents/`, `core/`, `daniela/`, `integration/`, `pixel/`, `security/` |
| `scripts/` | utilidades de despliegue y verificacion |
| `docs/` | 80+ documentos |
| `prototypes/` | 19.8 MB de prototipos (ffmpeg, brand studio) |
| `decentraland/` | escena de Decentraland |
| `app-scripts/` | `apps-script`, `apps-script-admin` (antes `apps_script*`) |

### H. Archivo y restos

| carpeta | que es |
|---|---|
| `archives/` | **2.7 GB** = 64% del arbol: `frontend/`, `unified-dashboard/`, `frontend_legacy_backup/`, `server.py` |
| `aig/` | shell de 1 fichero (un log). Resto del paquete `aig/` que se aplano |
| `tencent-suite/` | carpetas **vacias**; el contenido esta en `ia-services/tencent-suite/` |
| `biometric-profile/` | fotos de cara locales (destrackeadas, ignoradas) |

### I. Tooling local (no versionado)

`.venv/`, `__pycache__/`, `.pytest_cache/`, `.ruff_cache/`, `.workbuddy-ai/`,
`.plugin_registry/`, `.plugin_versions/`

### Ficheros sueltos en la raiz (13)

```
daniela.py              5.5 KB   <- integrador de aig (fase `aig`)
.gitignore, .dockerignore, .gitattributes
.env, .env.master.example        <- ignorados
daniela_multiuser.db, aig.db, scheduler_locks.db, trigger_watches.db, memory_rag.db
service_stderr.log, service_stdout.log
```

> `daniela.py` en la **raiz** es deliberado: la fase `aig` lo carga por
> ruta. Si lo mueves, hay que tocar `_cargar_integrador()` en
> `gev/daniela-os/server.py` (prueba 3 profundidades) y el
> `COPY ./daniela.py ./daniela.py` del Dockerfile.

---

## 3. Los bloques principales en detalle

### 3.1 `engine/` — los 10 motores

Creado en `e2bb9a1bf` (consolidacion). Cada uno con su `Dockerfile` y `COPY engine/<x>/ ./<x>/`:

```
engine/
  auto_engine/       (11)   agentes y scheduler
  chaos_engine/       (7)   inyeccion de caos
  engine/cross_engine/ (9) gateway (puertos 9900 y 8080)
  data_engine/        (9)
  devtools_engine/    (9)   debugger, code_analysis, sandbox
  ecosystem_engine/  (10)   marketplace, connectors, transformers, protocol
  intel_engine/       (9)   nlp, vision, recommendation, prediction, automation
  scale_engine/       (8)   caching, compression, concurrency, resilience, optimization
  secure_engine/      (8)
  ux_engine/          (8)   themes, i18n
```

### 3.2 `gev/` — visor y Daniela

```
gev/
  server.py           <- el servidor del visor
  osint.py, billing.py, command_center.py, i18n.py, gev_proxy.py
  static/, data/
  daniela-os/         <- Daniela OS (antes daniela-os/ en la raiz)
    server.py         <- 452 rutas, registra todas las fases
    Dockerfile
    ambient/ consciousness/ proactive/ emotional/ embodiment/
    dreams/ temporal/ social/ muse/ guardian/      <- fases 6-10
    daniela-jarvis/   <- el escritorio Electron (absorbido)
    epic-pc/          <- (absorbido)
    shared/           <- paquete real: ai_bridge, health, scheduler, pixel_guard...
    web/, data/
```

> **Dos cosas distintas, ambas en el PC:**
>
> | Nombre | Qué es |
> |--------|--------|
> | **Daniela OS** (`gev/daniela-os/`) | la **app para el PC de Daniela**: servidor, fases y escritorio |
> | **Epic PC** (`epic-pc/`) | **Daniela en el PC**: la experiencia de escritorio, no un módulo |
>
> Epic PC no aparece en el inventario de módulos (`docs/MODULES.md` §1) porque
> es una experiencia: sus 62/70 partes no se habilitan por separado.

> ✅ **Duplicado resuelto (2026-09-30):** la copia canónica es `epic-pc/` en
> la raíz, promovida desde `gev/daniela-os/epic-pc/` (Opción A: la embebida
> era ruff-limpia y superset). La copia embebida fue borrada. Los
> `epic_pc_manager` ya apuntaban bien a la raíz con su `EPIC_ROOT` de 3
> `parent`.

### 3.3 `ia-services/` — IA de terceros

```
ia-services/
  hermes/           <- antes hermes-epic/. Aplanado a /app, CMD server:app, puerto 9300
  tencent-suite/    <- Hunyuan3D-2, HunyuanDiT, HunyuanVideo (226/238/55 ficheros)
  google/
```

Aislar aqui las dependencias pesadas (modelos 3D y video) es correcto: el nucleo
no las necesita para arrancar.

### 3.4 `shared/` — cuidado, hay ocho

```
shared/                                  <- EL paquete `aig_shared` (pyproject.toml)
gev/daniela-os/shared/              <- paquete real (ai_bridge, health, scheduler)
core/daniela/omnipresente/shared/        <- copia
ia-services/hermes/shared/               <- copia
agents/api/shared/                       <- copia
infra-opt/shared/                        <- copia
perf-opt/shared/                         <- copia
sec-opt/shared/                          <- copia
```

Los seis ultimos son casi el mismo esqueleto (`__init__.py` + `config.py`). El
import depende del **orden de `sys.path`**, que a su vez depende de que test haya
corrido antes. Ver `tests/conftest.py`.

---

## 4. Mapa viejo -> nuevo

| antes | ahora |
|---|---|
| `daniela-os/` | `gev/daniela-os/` |
| `pixel/` y `android_app/pixel/` | `mobile-app/services/`, `mobile-app/bridges/`, `mobile-app/core/` |
| `mobile-app/pixel/` (copias planas) | igual, agrupado por destino |
| `phone_deploy/`, `android_app/phone_deploy/` y `mobile-app/phone_deploy/` | `mobile-app/services/`, `mobile-app/bridges/`, `mobile-app/core/` |
| `android_app/` (árbol entero) | `mobile-app/` |
| `android_app/mobile-app/` y `mobile-app/` (duplicado) | `mobile-app/` |
| `android_app/src/` | `mobile-app/src/` |
| `hermes-epic/` | `ia-services/hermes/` |
| `aig-shared/` | `shared/` |
| `optimization/` (raiz) | eliminado en P4; el motor vive en `aig-optimization/` |
| `tencent-suite/` | `ia-services/tencent-suite/` |
| `frontend/` | `archives/frontend/` |
| `unified-dashboard/` | `archives/unified-dashboard/` |
| `apps_script*`, `apps/` | `app-scripts/` |
| `grafana/`, `prometheus/` | `docker/grafana/`, `plugins/prometheus/` |
| `*_engine/` (10) | `engine/*_engine/` |
| `aig/*` | aplanado a la raiz |

---

## 5. Despliegue: servicios y contenedores

**7 ficheros de compose** en `config/`:

| fichero | servicios |
|---|---|
| `docker-compose.prod.yml` | 18 |
| `docker-compose.slim.yml` | 12 |
| `docker-compose.yml` | 12 |
| `docker-compose.core.yml` | 4 |
| `docker-compose.monitoring.yml` | 3 |
| `docker-compose.enterprise.yml` | 1 |
| `docker-compose.universes.yml` | **0** (muerto) |

**30 Dockerfiles** fuera de `archives/`.

**Servicios de primer nivel con `server.py` propio** (7): `core`, `gev`,
`infra-opt`, `multi-region`, `optimization`, `perf-opt`, `sec-opt`.

### Convencion de rutas en los Dockerfiles

El contexto de build es **la raiz del repo** (`context: ..` desde `config/`).
Regla: **el origen del COPY lleva la ruta nueva completa; el destino NO cambia**
si los imports dependen del nombre.

```dockerfile
# gev/daniela-os/Dockerfile
COPY ./gev/daniela-os/ .        # aplanado: /app/server.py
COPY ./mobile-app/pixel/ ./pixel/   # destino /app/pixel/ porque import dice `pixel.model_router`
COPY ./shared/ ./shared/
RUN pip install --no-cache-dir ./shared
```

Hay un test que valida cada COPY contra el disco **sin construir**:
`tests/core/test_integridad_despliegue.py`.

---

## 6. Donde va cada cosa nueva

| si anades... | va a |
|---|---|
| un motor nuevo | `engine/<nombre>_engine/` + su Dockerfile |
| un agente | `agents/agent_<nombre>.py` |
| una fase de Daniela | `gev/daniela-os/<fase>/` + registrarla en `register_all()` |
| un endpoint del visor | `gev/` |
| un puente a hardware | `connectors/` |
| un plugin | `plugins/` |
| un servicio de IA externo | `ia-services/<nombre>/` |
| una app de cliente | `mobile-app/<nombre>/` |
| codigo compartido de verdad | `shared/aig_shared/` |
| un test | `tests/<dominio>/test_<nombre>.py` |
| un documento | `docs/` |

**Nunca** anadas un modulo suelto en la raiz. La raiz ya tiene 80 carpetas.

---

## 7. Deuda de estructura

| # | problema | impacto |
|---|---|---|
| 1 | `archives/` = **2.7 GB**, 64% del arbol | clones y CI lentos |
| 2 | **8 carpetas `shared`** | el import depende de `sys.path` |
| 3 | **4 copias del mismo esqueleto** (`infra-opt`, `perf-opt`, `sec-opt`, `optimization`) | 4 servicios, 4 Dockerfiles, 4 `shared/` para lo mismo |
| 4 | **7 compose con ~50 definiciones** solapadas | divergen y se contradicen |
| 5 | `config/docker-compose.universes.yml` con 0 servicios | plantilla vacia (solo un ejemplo comentado) |
| 6 | `tencent-suite/` vacio pero con **3 gitlinks** en el indice | **RESUELTO** (`90699fbe6`) |
| 7 | pila E-36: `config/Dockerfile`, `config/Dockerfile.daniela`, `docker-compose.core.yml` | inconstruible: sus 6 `COPY` no existen |
| 8 | `aig/` (1 log), `research/` (1 log de 1 KB), `output-assets/` (vacio), `drive-reports/` (1 md) | ruido |
| 9 | `prototypes/` (19.8 MB) en el repo de produccion | no deberia viajar |
| 10 | `tenants/` vacio | multi-tenant declarado, no implementado |
| 11 | `docs/ADR-REPO-LAYOUT.md` describe un layout que ya no existe | doc enganosa |
| 12 | `scripts/utils/auditar_raices.py` con marcadores obsoletos | 44 falsos positivos |
| 13 | `startup_aig.ps1` (auto-arranque de Windows) buscaba su compose en la raiz | fallaba **en silencio**, sin levantar nada — **RESUELTO** |
| 14 | `docker/docker-compose-aig.yml` duplica el stack canonico (11 servicios, mismo orden) | copia derivada, sin referencias: divergira |

El detalle y el plan estan en `docs/AUDITORIA-2026-09-22.md`.

---

## 8. Verificacion

```bash
# La suite entera (0 fallos esperados)
.venv/Scripts/python.exe -m pytest tests/ -q

# Cada COPY de cada Dockerfile apunta a algo que existe
.venv/Scripts/python.exe -m pytest tests/core/test_integridad_despliegue.py -q

# Daniela registra todas las fases (failed_phases == [])
.venv/Scripts/python.exe -m pytest tests/daniela/test_daniela_fases.py -q

# Cada build: de cada compose existe en disco
.venv/Scripts/python.exe -m pytest tests/core/test_deploy_honesto.py -q
```
