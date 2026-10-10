# Estándares de Organización AIG

## Carpetas

| Patrón | Uso | Ejemplo |
|---|---|---|
| `kebab-case` | Directorios | `content-creation/`, `auto-scaling/` |
| `snake_case` | Ficheros Python | `content_tools.py`, `auto_scaling.py` |
| `PascalCase` | Clases | `ContentTools`, `AutoScaling` |

## Nombres de plataforma móvil

Regla de nombres (decisión 2026-10-04, **sin renames masivos**: 607 ficheros
afectados y coste > beneficio). Cada palabra designa un nivel distinto;
no son sinónimos y no se unifican:

| Nombre | Nivel | Qué abarca | Ejemplos |
|---|---|---|---|
| `android` | plataforma (SO/dispositivo) | lo que vale para cualquier Android | `skills/connectors/android/`, `scripts/android/`, marker pytest `android` (="test que necesita ADB") |
| `android-app` | la app compilable | solo el proyecto de app | `daniela-os/android-app/` (Kotlin), `frontend/apps/android-app/` (PWA) |
| `pixel` | hardware concreto | el modelo/dispositivo de este proyecto | `PIXEL_TOKEN`, `pixel_bridge_hub` |
| `termux` | runtime en el móvil | todo lo que exige la app Termux | `termux_api_gateway.py`, boot scripts |
| `mobile-app` | árbol cliente | PWA + servicios edge | `mobile-app/`; tests → `tests/mobile/` |

- `PIXEL_TOKEN` y los nombres `termux_*` **no se renombran**: el secreto vive
  en el `.env` de PC y del móvil, y `termux_*` declara una dependencia real.
- Lo que sí se arregla es duplicación, no nombres: una sola copia canónica
  (`skills/connectors/android/`), el resto se encola en el dedup (oss-queue).


## Estructura de Carpetas

```
aig/
  agents/           # Agentes del sistema
  api/              # APIs (shims canónicos hacia dominios, ej. api/homeassistant_api.py)
  apps/             # Aplicaciones embebidas (nexus, etc.)
  config/           # Configuración
  connectors/       # Conectores externos (de bajo nivel; sin duplicar backends)
  core/             # Núcleo del sistema
  data/             # Datos runtime (ignorado por git salvo tokens)
  docs/             # Documentación + ADR-XXX
  engine/           # Motores canónicos (los twins *_engine/ en raíz = pendiente ADR)
  frontend/         # Apps cliente (PWA mobile-app)
  gev/              # GEV (God's Eye View) + servidor real (gev/daniela-os/server.py)
  iot_hub/          # Dominio IoT: /api/iot/* (ADR-020)
  mcps/             # MCPs
  mobile-app/       # puntero de 36 B -> frontend/apps/android-app/mobile-app/
  daniela-os/phone/ # Runtime telefono (ADR-019; agents/, core/, services/)
  prototypes/       # Prototipos sueltos sin referencias (JS huérfanos + pipelines de vídeo)
  scripts/          # Scripts de automatización
  shared/           # Paquete compartido (shim de aig-shared)
  skills/           # Skills
  static/           # Estáticos servidos
  sync/             # Sincronización
  tenants/          # Datos multi-tenant
  tests/            # Tests organizados por categoría
  tools/            # Tools
  unified-dashboard/ # Dashboard Flask + Svelte (server.py + src/; SPA build = pendiente)
  web/              # HUD de control Daniela OS (HTML5/JS puro, serve_control.py :8082)
```

## Escritorio Daniela OS (Windows, 2026-10-04)

Suite cyberpunk desplegable con `scripts/desktop/deploy_desktop.ps1`
(winget + copia de configs con backup `.bak-YYYYMMDD`):

| Componente | Config en repo | Destino en el equipo |
|---|---|---|
| GlazeWM (tiling) | `scripts/desktop/configs/glazewm/config.yaml` | `%USERPROFILE%\.glzr\glazewm\config.yaml` |
| YASB (barra HUD) | `configs/yasb/{config.yaml,styles.css}` | `%APPDATA%\yasb\` |
| Rainmeter HUD | `configs/rainmeter/DanielaOS/HUD/Skin.ini` | `%APPDATA%\Rainmeter\Skins\DanielaOS\` |
| WezTerm | `configs/wezterm/wezterm.lua` | `%USERPROFILE%\.config\wezterm\` |
| Starship | `configs/starship/starship.toml` | `%USERPROFILE%\.config\starship.toml` |

- Ciclo: `start_desktop.ps1` (arranca WM/barra/HUD, `-Dashboard` añade
  `serve_control.py`) → `stop_desktop.ps1` (para todo, `-Dashboard` incluye
  el servidor) → `deploy_desktop.ps1 -Uninstall` (solo paquetes).
- **Puerto 8082 = dashboard de control** (`web/` + `scripts/serve_control.py`),
  no Hermes (Hermes esta en 9300; 9900 es el Cross-Engine Orchestrator). El HUD consume `GET /api/status` (JSON)
  y `GET /api/hud.txt` (pipe-separated para WebParser de Rainmeter).
- Estado operativo en `state.db` (SQLite WAL, `scripts/state_db.py`).

## Ficheros Sueltos

| Ubicación | Ficheros |
|---|---|
| Raíz | `README.md`, `.gitignore`, `pyproject.toml`, `docker-compose.yml` |
| `scripts/` | Scripts de automatización |
| `tests/` | Tests organizados por categoría |

## Tests de Organización

Los tests de organización verifican:
1. Todas las carpetas siguen `kebab-case`
2. Todos los ficheros Python siguen `snake_case`
3. No hay ficheros sueltos en lugares incorrectos
4. La estructura coincide con el estándar
