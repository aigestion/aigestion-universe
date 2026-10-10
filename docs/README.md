# aig

Plataforma de IA para gestorias fiscales, contables y PYMEs — y **Daniela OS**, que
controla un Pixel 8a desde el PC.

**Estado:** 383 endpoints activos · rama unica `main` = `universo-v1` · 28/28 epicas hechas

> ### 📚 Empieza por la documentacion
> **[Indice completo](docs/INDEX.md)** — el punto de entrada a los 33 documentos.
> _(Abriendo `docs/` como vault de Obsidian, funciona como `[[INDEX]]`.)_
>
> Los 3 que importan si vienes nuevo:
> 1. [INSTALACION](docs/INSTALACION.md) — ponerlo en marcha, con los fallos reales
> 2. [ARQUITECTURA](docs/ARQUITECTURA.md) — como esta montado de verdad
> 3. [AUDITORIA-CAMBIOS-2026-09-14](docs/AUDITORIA-CAMBIOS-2026-09-14.md) — estado y pendientes

## Descripcion

aig es una plataforma modular de inteligencia artificial que automatiza tareas
repetitivas de gestoria: clasificacion de emails, auditoria de facturas, generacion de
contenido, analisis de reuniones y mucho mas.

Ademas, **Daniela OS** extiende el sistema al movil: control del Pixel 8a por ADB,
sensores, NFC, infrarrojos, malla entre dispositivos y un largo etcetera. Son
**178 de los 383 endpoints**.

## Arquitectura

```
Daniela OS (Flask, 383 rutas) ──┬── aig/      core, agents, content, pixel, sil
                                ├── /api/pixel/*    178 rutas al Pixel 8a
                                ├── Autonomia       self_healing, blackbox, sil
                                └── api_gateway.py  API publica (JWT) — servicio aparte
```

Detalle completo, incluidos los blueprints y el mapa de rutas:
**[ARQUITECTURA.md](docs/ARQUITECTURA.md)**

## Estructura del repo

```
agents/   personajes + swarm
aig/core/     orquestador + adapters
aig/content/  factory, brand kit, viral, calendar
aig/pixel/    pixel bridge, termux, sensores, edge
aig/sil/      sil engine + autofix
daniela_os.py  api_gateway.py  admin_panel.py   ← apps (raiz)
docs/               ← toda la documentacion (ver docs/INDEX.md)
scripts/            ← herramientas: check_env.py, repo_status.py
tests/              ← 🔴 pendiente: no ejecuta ni un test
```

> ⚠️ **Aviso importante.** Tras el merge del PR #109, **la raiz tiene 226 `.py`** y
> `aig/pixel/` mantiene copias **distintas** de algunos modulos. El que se
> ejecuta es **el de la raiz**. Antes de editar un modulo, comprueba cual es el vivo:
>
> ```bash
> ./.venv/Scripts/python.exe -c "import tunnel_guard; print(tunnel_guard.__file__)"
> ```
>
> Mas detalle en [ARQUITECTURA.md](docs/ARQUITECTURA.md#5-el-problema-de-las-copias-duplicadas).

## Modulos Quick Win

| Modulo | Descripcion | Estado |
|--------|-------------|--------|
| Daniela Proactive Engine | Motor proactivo con analisis de calendario | ✅ |
| Email Zero Inbox | Clasificacion inteligente de emails | ✅ |
| Smart Invoice Auditor | OCR, duplicados, fraude | ✅ |
| Meeting Intelligence | Transcripcion y action items | ✅ |
| Sentiment Dashboard | Analisis de sentimiento en espanol | ✅ |
| Social Media Command Center | Centro de comando para redes | ✅ |
| Customer Support Automation | FAQ matching, tickets, escalamiento | ✅ |
| Code Generation Agent | NL → Codigo con tests | ✅ |
| Content Factory AI | Fabrica de contenido multi-plataforma | ✅ |
| Swarm Intelligence | Coordinador multi-agente | ✅ |

## Quick Start

```bash
# 1. Clonar y crear entorno
git clone https://github.com/aig/AIGESTION-MONOREPO.git
cd AIGESTION-MONOREPO
python -m venv .venv
.venv\Scripts\activate

# 2. Dependencias (sqlalchemy NO esta en requirements.txt — instalalo aparte)
pip install -r requirements.txt
pip install sqlalchemy==2.0.35

# 3. Comprobar el entorno (crítico: el .env se ha roto dos veces)
./.venv/Scripts/python.exe scripts/check_env.py

# 4. Arrancar (PYTHONPATH es obligatorio: sitecustomize mete scripts/ en sys.path)
PYTHONPATH="C:/Users/Alejandro/aig" ./.venv/Scripts/python.exe daniela_os.py
```

Abre **http://localhost:5000** (dashboard en `/dashboard`).

Guia completa con los problemas conocidos: **[INSTALACION.md](docs/INSTALACION.md)**

### Docker

```bash
docker-compose up -d
```

Servicios: Daniela OS `:5000` · API Gateway `:8080` · Admin `/admin` · Nginx `:80`

## Uso

### Chat con Daniela

```bash
curl -X POST http://localhost:5000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "genera contenido para blog sobre IA"}'
```

### API Gateway

```bash
curl -X POST http://localhost:8080/v1/admin/token \
  -d '{"api_key": "tu-api-key"}'

curl -X POST http://localhost:8080/v1/ask \
  -H "Authorization: Bearer <token>" \
  -d '{"query": "analiza sentimiento: estoy muy feliz"}'
```

### Pipeline

```bash
curl -X POST http://localhost:8080/v1/pipeline \
  -H "Authorization: Bearer <token>" \
  -d '{"steps": [
    {"module": "content_factory", "action": "generate", "params": {"topic": "IA", "platform": "twitter"}},
    {"module": "social_media", "action": "generate_post", "params": {"topic": "IA"}}
  ]}'
```

## Tiers

| Tier | Precio | Requests/dia | Modulos | API |
|------|--------|-------------|---------|-----|
| Free | €0 | 100 | 3 basicos | No |
| Pro | €29/mes | 1,000 | Todos | Si |
| Enterprise | €99/mes | Ilimitado | Todos + White-label | Si |

## Comandos Slash (Daniela OS)

| Comando | Descripcion |
|---------|-------------|
| `/core <query>` | Consulta directa al core |
| `/content <tema>` | Generar contenido |
| `/swarm <objetivo>` | Coordinar swarm |
| `/code <desc>` | Generar codigo |
| `/email <texto>` | Clasificar email |
| `/invoice <datos>` | Auditar factura |
| `/sentiment <texto>` | Analizar sentimiento |
| `/social <tema>` | Generar post social |
| `/support <query>` | Soporte automatico |
| `/meeting <transcripcion>` | Analizar reunion |
| `/proactive` | Ver alertas del calendario |
| `/help` | Mostrar ayuda |

## Variables de entorno

| Variable | Descripcion | Usada por |
|----------|-------------|-----------|
| `GEMINI_API_KEY` | API key de Google Gemini | **~75 modulos** |
| `DANIELA_PIN` | PIN de acceso al panel | 1 |
| `GROQ_API_KEY` | IA de respaldo | ~20 |
| `OPENROUTER_API_KEY` | IA de respaldo | ~10 |
| `PIXEL_IP` / `PIXEL_TOKEN` | Control del movil | ~30 |
| `GOOGLE_API_KEY` | API key de Google | varios |
| `SUPABASE_URL` / `_KEY` | Cloud y RAG | varios |
| `AIGESTION_JWT_SECRET` | Secret para JWT del gateway | 1 |

> 🔴 **Se lee el `.env` de la raiz, no `config/.env`.** (Desde el 14 sep 2026 se
> cargan los dos: el de la raiz tiene prioridad, `config/.env` rellena huecos.)
> Diagnosticar con `scripts/check_env.py`.
>
> 🔐 **Nunca escribas una clave real, ni "como ejemplo", en un documento o un
> commit.** El hook Secret Guard lo bloquea y `tunnel_guard` lo marca como fuga.

## Testing

```bash
# 🔴 PENDIENTE: la suite no ejecuta ni un test (6 errores de coleccion)
./.venv/Scripts/python.exe -m pytest tests/ -q

# Comprobaciones que SI funcionan hoy:
./.venv/Scripts/python.exe scripts/check_env.py      # entorno
./.venv/Scripts/python.exe scripts/repo_status.py    # estado del repo
# El core no tiene CLI: se carga por ruta (ver core/daniela_os_core.py)
python -c "import core.daniela_os_core as c; print(c.DanielaCore)"
```

Por que importa y como arreglarlo: [ARQUITECTURA.md](docs/ARQUITECTURA.md#7-los-tests-estado-y-por-qué-importa)

## Contribuir

Antes de tocar nada, lee la seccion **"Trampas conocidas"** de
[docs/INDEX.md](docs/INDEX.md). En resumen:

- `git status -sb` **miente** en este repo → usa `scripts/repo_status.py`
- El modulo que crees editar puede no ser el que se ejecuta → comprueba `__file__`
- Hay dos `.env` → usa `scripts/check_env.py`
- No `git add .` sin revisar → `bin/` son 132 MB

1. Fork el repositorio
2. Crea una rama (`git checkout -b feature/nueva-feature`)
3. Commit (`git commit -m 'feat: nueva feature'`)
4. Push (`git push origin feature/nueva-feature`)
5. Abre un Pull Request

Politica de ramas: [docs/branch_policy.md](docs/branch_policy.md)

## Licencia

MIT License - aig Team 2026

