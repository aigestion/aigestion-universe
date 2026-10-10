# 📚 Índice de documentación — aig / Daniela OS

**Puerta de entrada.** Si eres nuevo (o vuelves después de un tiempo), empieza aquí.
Última revisión: 4 oct 2026 · 38 documentos · 397 rutas activas

> **Cómo leer esto.** Los enlaces entre corchetes dobles (tipo `[` `[` `NOMBRE` `]` `]`)
> son enlaces wiki de Obsidian: funcionan solos si abres `docs/` como vault. Con
> Markdown normal (`docs/x.md`) también funcionan desde GitHub y desde el editor.

---

## 🚀 Si vienes nuevo: los 4 documentos que importan

| # | Documento | Para qué |
|---|---|---|
| 1 | **[[MERCADO-AIGESTION]]** | 🧭 **Qué somos, a quién vendemos y qué toca hacer.** Tesis (universo + BYOK + híbrido), mercado con fuentes, competencia, unit economics y roadmap F0-F7 con gates medibles. Sustituye a [[ROADMAP_MASTER]] y [[PHASES]] |
| 2 | **[[INSTALACION]]** | Poner el sistema en marcha desde cero |
| 3 | **[[ARQUITECTURA]]** | Entender cómo está montado (397 rutas, módulos, capas) |
| 4 | **[[GUIA_GITHUB]]** *(pendiente)* | Moverte con git sin romper cosas |
| 5 | **[[AUDITORIA-CAMBIOS-2026-09-14]]** | Estado real del proyecto y deuda técnica |
| 6 | **[[AUDITORIA-2026-09-18]]** | 🔴 **Qué es necesario de verdad y qué no.** Corrige los números de las claves (son 6, no 1) y el mito de los 1,9 GB de `.git` |
| 7 | **[[RESET-ARQUITECTURA-2026-09-18]]** | 🔴 **Mapa de agentes, flujo de una orden y plan "Daniela Omnipresente"**. Medido: el cerebro es un stub, el 45% de las rutas dependen del móvil, y de 5 proveedores de IA solo 1 responde |
| 8 | **[[EPICAS-ARREGLO-2026-09-18]]** | 🔴 **16 épicas (E-33 a E-48) para arreglar todo**, cada una atada a un problema medido. Camino crítico: E-36 → E-33 → E-45 |
| 9 | **[[IDEAS-EPICAS-SIGUIENTES-PASOS]]** | **Qué hacer ahora**, ordenado por lo que desbloquea |

---

## 🎯 Qué hacer ahora

| Documento | Qué cubre |
|---|---|
| **[[MERCADO-AIGESTION]]** | 🧭 **El documento maestro actual.** Tesis reinventada (universo admin + usuario final, login Gmail, BYOK, híbrido self-hosted), TAM/SAM/SOM con fuentes, competencia, unit economics, **10 agujeros verificados con `file:line`** y roadmap F0-F7 con gates medibles |
| **[[E-36-DESPLIEGUE-HONESTO]]** | 🔴 **Cómo se despliega de verdad y por qué el CD mentía.** Medido: 0 runners, 0 secretos de despliegue → GitHub **no puede** llegar al PC. Producción es el PC: `./scripts/deploy_prod.sh`. Incluye los 3 bugs extra (health gate con 7 falsos negativos, `/status` vs `/api/status`, el plugin `docker compose` que aquí no existe) |
| [[IDEAS-EPICAS-SIGUIENTES-PASOS]] | **Los siguientes pasos concretos**: cimientos, islas, producto nuevo |
| [[B1-PILOTO-ISLAS-DIAGNOSTICO]] | **Por qué las 32 islas de `plugins/` NO son código listo** (18 con `~/daniela-os`, 6 que ni importan) |
| [[B1-PASO2-INTEGRITY-GUARD]] | **La isla que sí se adaptó**: detección de mutación de ficheros, y los 4 defectos que tenía el plugin |
| [[B3-VOZ-OFFLINE-PIPER]] | **Voz que funciona sin internet**: Piper en vez de edge-tts, y el plan que estaba mal en 3 cosas |
| [[ENV-LIMPIEZA-2026-09-14]] | **5 claves del `.env` que funcionaban por accidente de orden**: si alguien lo ordena, vuelven a `YOUR_VALUE_HERE` en silencio |
| [[REVISION-2026-09-17]] | **Revisión de los 47 commits del 16-17 sep** (19 servicios, Docker, CI/CD): qué se rompió, qué queda roto y en qué orden arreglarlo |
| [[PLAN-COMMIT-2026-09-17]] | **Los 380 ficheros sin versionar, uno a uno**: qué entra (378), qué no (2) y los comandos exactos verificados |
| [[EJECUCION-2026-09-17]] | **El cierre**: `main` promocionado, 939 tests verdes y los 5 workflows en verde. Y las **5 cosas que el plan tenia mal** (la gorda: el `--only` del health gate, que era la causa real del CD rojo) |
| [[INVENTARIO-CLAVES]] | Qué claves del `.env` funcionan de verdad y cuáles son plantilla |
| [[PRIORIDADES-QUICK-WINS]] | Matriz impacto/esfuerzo de las 50 ideas (2026-09-05) |
| [[SAFE-EVOLUTION-GATE]] | Cómo cambiar el sistema sin romperlo |
| [[30-IDEAS-EPICAS-EXPANSION-AIGESTION-2026]] | Las 30 ideas épicas de producto |
| [[50-IDEAS-CASOS-USO-AIGESTION]] | 50 casos de uso para gestorías |

---

## 🏗️ Sistema y arquitectura

| Documento | Qué cubre |
|---|---|
| [[ARQUITECTURA]] | Mapa de capas, los 397 endpoints, blueprints, cómo añadir un módulo |
| [[INSTALACION]] | Requisitos, venv, `.env`, arranque local y en el móvil |
| [[ADR-REPO-LAYOUT]] | **ADR-001 a ADR-015.** Por qué hay `aig/` + shims; y **ADR-015: gana la raíz** (231 `.py`, 505 copias idénticas, y por qué NO se consolidan) |
| [[DEPENDENCY_REPORT]] | Dependencias y versiones del entorno |
| [[SKILLS-PACKAGING]] | Inventario de skills/plugins y plan de empaquetado |

## 📱 Pixel 8a / Termux (el móvil)

| Documento | Qué cubre |
|---|---|
| [[AUDITORIA_TELEFONO]] | Auditoría del Pixel 8a |
| [[AUDITORIA_TELEFONO_PROFUNDA]] | Auditoría profunda (números reales de consumo y límites) |
| [[ESPLENDOR_TELEFONO]] | 16 ideas épicas para exprimir el Pixel |
| [[EDGE-NODE]] | El teléfono como nodo trabajador del swarm |
| [[SECOND-SCREEN]] | HUD táctil con aprobar/rechazar |
| [[TAILSCALE-P0]] | 🔴 **Pendiente.** Pasar del túnel público a Tailscale (cierra un agujero abierto) |

## 🔐 Seguridad

| Documento | Qué cubre |
|---|---|
| [[AUDITORIA-CAMBIOS-2026-09-14]] | 🔴 **P0 vigentes**: rotar claves, secretos en el historial |
| [[AUDITORIA_V1]] | Auditoría completa del repo (v1) |
| [[WALLET-AUDIT-REPORT]] | Auditoría de wallets y tenencia de activos |
| [[SAFE-EVOLUTION-GATE]] | *Idea #9.* `main` solo avanza si los tests están verdes |
| [[SIL-WEEKLY-JOB]] | Rutina semanal de auto-mejora |

## 🧠 Ideas de producto (las 50+16)

Series de propuestas, con estado de implementación:

| Documento | Qué cubre |
|---|---|
| [[PRIORIDADES-QUICK-WINS]] | **Matriz de priorización de las 50 ideas** — empezar aquí |
| [[50-IDEAS-CASOS-USO-AIGESTION]] | Las 50 ideas y casos de uso |
| [[30-IDEAS-EPICAS-EXPANSION-AIGESTION-2026]] | 30 ideas de expansión para 2026 |
| [[CONTINUUM]] | #1 — Cerebro nocturno |
| [[EDGE-NODE]] | #2 — Pixel como worker |
| [[MESH-OFFLINE]] | #3 — Cola cifrada para mala red |
| [[INVOICE-TRUTH-GRAPH]] | #4 — Aviso proactivo antes de pagar |
| [[ZERO-INBOX-COURT]] | #5 — Confirmación humana solo en la zona gris |
| [[MEETING-EXPEDIENTE]] | #6 — De reunión a expediente |
| [[CONTENT-OS]] | #7 — Pipeline de contenido con preview real |
| [[SAFE-EVOLUTION-GATE]] | #9 — `main` solo en verde |
| [[SECOND-SCREEN]] | #11 — HUD con aprobar/rechazar |
| [[WHITE-LABEL]] | #12 — Enterprise sin tocar su código |
| [[CAD-STUDIO]] | Diseño paramétrico por texto (OpenSCAD / Blender) |

## 🌐 Infraestructura e integraciones

| Documento | Qué cubre |
|---|---|
| [[apis_gratis]] | Inventario de APIs gratuitas + épicas E-27..E-34 |
| [[GOOGLE-FREE-TIER-EXPANDIDO]] | Google Free Tier completo |
| [[METAVERSE-README]] | Metaverso aig v1.0.0 |
| [[branch_policy]] | Política de ramas (rescate selectivo, E-16) |
| [[GUIA_GITHUB]] | GitHub explicado desde cero |

---

## Mapa del repositorio (donde esta cada cosa, 2026-10-04)

```
C:\Users\Alejandro\aig\
├── README.md              presentacion corta (enlace al indice)
├── AGENTS.md              instrucciones del agente (layout, puertos, servicios)
├── docs/                  ESTA DOCUMENTACION (ADRs, auditorias, indices)
│
├── daniela-os/            app principal (Flask :9200) + phone/ + android-app/
├── engine/                19 motores federados (cross_engine :8080/:9900, ...)
├── agents/                agentes autonomos (api/ :9800, productivity/, ...)
├── core/                  modulos core (core, adapters, auth, safe_exec)
├── content/               fabrica de contenido (brand_kit, media_pipeline, ...)
├── scripts/               scripts operativos (core/, utils/, deploy/, daniela/, ...)
├── skills/                skills ECC + conectores
├── config/                docker/ (compose prod/slim/core), nginx/, observability/
├── docker/                Dockerfiles por servicio (ai-engine, api-gateway, ...)
├── frontend/              cliente Android (apps/android-app/mobile-app/)
├── gev/                   visor 3D (gods-eye-view)
├── ide/hermes/            servicio Hermes (:9300)
├── backend/perf-opt/      motor de rendimiento (:9998)
├── secops/                hardening y auditoria de seguridad
├── shared/                paquete aig_shared (auth, config, ai)
├── tests/                 pytest (0 fallos, markers network/android)
├── static/                frontend, landing, brand
└── web/                   dashboard de control (serve_control.py :8082)
```

**Aviso importante sobre la estructura.** La raiz tiene **226 ficheros `.py`** y
 La raíz tiene **226 ficheros `.py`** y
`aig/pixel/` tiene **copias distintas** de algunos. Comprueba siempre cuál se
carga de verdad **antes** de editar:

```bash
./.venv/Scripts/python.exe -c "import tunnel_guard; print(tunnel_guard.__file__)"
```

Detalle completo en [[ARQUITECTURA]] → *"El problema de las copias duplicadas"*.

---

## ⚙️ Comandos del día a día

```bash
# ── Comprobar que el entorno está bien (1 segundo) ──────────────────
./.venv/Scripts/python.exe scripts/check_env.py
./.venv/Scripts/python.exe scripts/check_env.py --restore   # si falta algo

# ── Estado real del repo (git status MIENTE en este repo) ────────────
./.venv/Scripts/python.exe scripts/repo_status.py

# ── Arrancar ─────────────────────────────────────────────────────────
PYTHONPATH="C:/Users/Alejandro/aig" ./.venv/Scripts/python.exe daniela_os.py

# ── Cuántas rutas tengo? ─────────────────────────────────────────────
PYTHONPATH="C:/Users/Alejandro/aig" ./.venv/Scripts/python.exe -c \
  "import daniela_os; print(len(list(daniela_os.app.url_map.iter_rules())))"
```

---

## Estado del proyecto (actualizado 2026-10-04)

### Sano
- **pytest: 0 fallos** (360 resueltos vs baseline 2026-10-03). Gate: GO.
- **ruff: 0** (ratchet `.quality-baseline/ruff-count.txt` = 0 desde el 2026-10-04).
- **P1-P6 ejecutados**: restructuracion, raices fantasma eliminadas, dominio
  `aigestion.net` unificado, stacks prod/slim validos (`docker compose config` OK).
- **Rama unica**: `main`.

### Pendiente y bloqueante
1. **Rotar claves LLM** de `config/observability/litellm_config.yaml` (OpenRouter,
   Groq, Together, DeepInfra): ya estan en el historial de git. El config ahora
   las lee del entorno (`${OPENROUTER_API_KEY}` etc.) — solo hay que rotarlas
   en los paneles y ponerlas en `.env`.
2. **Rotar `JWT_SECRET`/`API_KEY`** de la pila de auth (ahora fail-closed: sin
   secreto real no arranca) y los de `config/nginx/network.conf`.
3. **Servicio `security` (:9999) sin codigo**: `sec-opt/` no existe. Esta en
   `profiles` en prod/slim para no tumbar el stack. Decision del dueño:
   implementarlo o retirarlo del health-gate.
4. **`gods-eye` (GEV)**: proyecto externo, en `profiles`. Requiere
   `scripts/setup_gev_docker.py`.

### Deuda tecnica conocida
- Duplicados: 532 nombres `.py` en 2+ ubicaciones (ver `docs/REVIEW-ESCUADRA-2026-10-04.md`).
- `.git` = 1,9 GB, con 148 commits automaticos "Auto-backup Daniela OS".
- 3 subrepos de `tencent-suite/` sin `.gitmodules`.

Detalle y plan por bloques: [[AUDITORIA-CAMBIOS-2026-09-14]].

---

## 🧨 Trampas conocidas (leer antes de tocar nada)

| Trampa | Qué hacer |
|---|---|
| `git status -sb` y `git branch -vv` **mienten** | Usa `scripts/repo_status.py` o `git ls-remote` |
| `git check-ignore X` dice "no ignorado" si X **ya está trackeado** | Usa `git check-ignore --no-index` para probar la regla |
| Hay **dos `.env`** (raíz y `config/`) | `load_dotenv` solo leía la raíz → usa `scripts/check_env.py` |
| `aig/pixel/X.py` puede **no ser el que se ejecuta** | Comprueba `X.__file__` antes de editar |
| `git fetch` **no persiste refs** en este repo | No te fíes de refs `origin/...` |
| Copiar un secreto real "como ejemplo" en un doc | El hook Secret Guard lo bloquea (ya pasó) |

---

## 📖 Convenciones

- **Idioma:** español, sin tildes en identificadores y rutas de código; con tildes en prosa.
- **Nombres de fichero:** `MAYUSCULAS-CON-GUIONES.md` para documentos principales;
  `minusculas_con_guion.md` para notas internas y series de ideas.
- **Fechas:** `YYYY-MM-DD` en el nombre cuando el documento es una foto puntual
  (`AUDITORIA-CAMBIOS-2026-09-14.md`).
- **Estado en la cabecera:** cada documento dice si está vigente, obsoleto o es histórico.
- **Al añadir un documento:** añádenlo **también aquí**, en la sección que le toque.

---

*Este índice es el punto de entrada único. Si un documento no está enlazado aquí,
es que se ha olvidado: añádelo.*

