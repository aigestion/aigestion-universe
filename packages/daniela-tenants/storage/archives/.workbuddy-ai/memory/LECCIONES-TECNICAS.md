# MEMORY.md — aig / DanielaOS (`C:\Users\Alejandro\aig`)

Daniela controla un Pixel 8a desde el PC, solo capas gratis ($0/mes).
Usuario principiante en git, escribe en español con faltas.
Venv `./.venv/Scripts/python.exe` (dotenv, flask, requests, httpx).
Ejecutar: `PYTHONPATH="C:/Users/Alejandro/aig" ./.venv/Scripts/python.exe …`
**Índice maestro de docs: `docs/INDEX.md`** (empezar aquí).

**Estado (2026-09-17): 397 rutas · 939 tests verdes · árbol limpio · CI y CD en verde.**

## 0. 🔴🔴 REGLAS DE MÉTODO (lo que más caro ha costado)
1. **MEDIR antes de actuar.** El plan escrito ha estado mal **5 veces** (B-1 elección,
   B-1 nº rutas, B-3, limpieza del `.env`, causa del CD rojo). Leer y **ejecutar** el
   código *antes* de diseñar; nunca fiarse del documento de plan.
2. **Mirar el VALOR, no el NOMBRE** (`METAMASK_PRIVATE_KEY` valía `YOUR_VALUE_HERE`).
   Y el **contenido**, no el nombre del fichero (falso positivo en
   `consolidate_env_backups.py`).
3. **Un test que pasa argumentos explícitos NO prueba el camino de producción.** El bug
   del CD vivía en el *parsing* de CLI y los 939 tests llamaban `main(argv=[...])`.
4. **Verde en un sitio ≠ verde en otro.** Antes de tocar un workflow, reproducir el
   runner en un `git worktree` limpio (ver §5).
5. **Cuando un hook no funciona, imprimir CUÁNDO se llama** en vez de suponer.
6. **Un script que reescribe un fichero crítico DEBE probarse en su rama de FALLO**
   (saboteando el invariante). El camino feliz no basta.

## 1. 🔴 Estructura: entre copias duplicadas MANDA LA RAÍZ
- `import X` resuelve a la copia de la **raíz**, NO a `aig/pixel/` ni `scripts/`.
  Ej.: `tunnel_guard` → `aig\tunnel_guard.py` (1.133 líneas); la de `aig/pixel/`
  (1.155, **distinta**) no se usa. **Verificar:** `python -c "import X; print(X.__file__)"`.
- ~231 `.py` en la raíz (antes 4). `scripts/` = shims de 5 líneas; `scripts/archive/` =
  código muerto. El docstring de los shims **miente** sobre la fuente de verdad.
- `sitecustomize.py` mete `scripts/` en `sys.path` → **sin PYTHONPATH todo falla**.
- Datos: `Path(__file__).resolve().parents[2] / "data" / "<modulo>"`.
- **505 copias de contenido IDÉNTICO** (310 grupos) y 389 nombres repetidos (1.305
  ficheros) — casi todas **ESTRUCTURALES** (`Dockerfile` x26 / `server.py` x27 = los 19
  microservicios, `__init__.py` x104). **NO borrar sin refactor deliberado.** Decisión
  documentada en **ADR-015** (`docs/ADR-REPO-LAYOUT.md`, que es el registro ADR-001…015).

## 2. Ramas — ✅ RESUELTO
- `main` = `universo-v1` = HEAD. Promocionado por **fast-forward, sin `--force`**.
- 10 etiquetas `archivo-2026-09-14-*` creadas antes de borrar ramas → recuperable.
- Quedan 4 ramas con commits propios fuera de main (NO borrar sin mirar): `ui-stable`,
  `uistable-flat` (puerto 5055 + `/api/offload`), `feature/darwin-api`, `autofix/…`.
- 🔴🔴 **`git fetch` NO PERSISTE NADA aquí.** `git status -sb` / `git branch -vv`
  **MIENTEN** (dicen `[origin/universo-v1: gone]`, falso). Usar **`git ls-remote origin`**.
- Hay `stash@{0}` y `stash@{1}`. **No `stash clear`.**
- Worktree huérfano `C:\Users\Alejandro\worktrees\aig\total-sycamore\aig`.

## 3. 🔴 Secretos — ⏳ SOLO FALTA ROTAR (el usuario dijo "no rotes las claves")
- ✅ **`.env` de la raíz RESTAURADO el 2026-09-14** (676 B/12 → 33.496 B/561).
  Causa raíz cerrada: `daniela_os.py` carga `.env` **y** `config/.env` y avisa de las
  claves críticas que falten. Diagnóstico: **`scripts/check_env.py`** (`--restore`).
- 🔴 **FALTA ROTAR (usuario), ANTES de cualquier `git filter-repo`:**
  1. **`GEMINI_API_KEY`** — es token OAuth (`AQ.Ab8…`), no key de Gemini (`AIza…`).
     Google da `401`. **Bloquea ~75 módulos.**
  2. **`AIzaSyAGTxKesg…`** — 🔴 **PUBLICADA en 18 commits**. Urgente.
  3. **`SUPABASE_SERVICE_KEY`** (`sb_secret_T8jp…`) — 0 commits.
  4. **`client_secret` Google** (`GOCSPX-9136…` en `credentials.json`) — 0 commits.
  Orden completo: **`docs/INVENTARIO-CLAVES.md` §6**.
- ✅ Redactadas las 4 copias en claro de `AIzaSyAGTxKesg…` (`<REDACTADO-2026-09-14>`).
- ⚠️ Hay **volcados del `.env` DENTRO del repo** (`data/tunnel_guard/backups/`,
  `config/env/.env.master`). Ignorados; se arregla **rotando**, no borrando.
  **NO tocar** `.env`, `config/env/.env.master`, `data/tunnel_guard/backups/`.
- `credentials.json` y `secret.key` **ya no trackeados** pero **siguen en el HISTORIAL**
  → rotar igualmente. Nunca pegar un secreto real "de ejemplo": el hook Secret Guard lo
  bloquea (`scripts/supabase_env.py` L8 lo tiene en el docstring → **falso positivo**).
- 🔴 **`PIXEL_TOKEN` y `PIXEL_GATEWAY_TOKEN` NO se pueden unificar** aunque valgan igual:
  Termux lee `PIXEL_GATEWAY_TOKEN`, ~10 módulos `PIXEL_TOKEN`, `ar_stage.py` hace
  fallback. Es un **alias en uso**.

## 4. 🧨 Trampas de git y del `.env`
- `git check-ignore <f>` dice "no ignorado" si el fichero **ya está trackeado**. Usar
  `git check-ignore --no-index -v <f>`. Índice: `git ls-files -i -c --exclude-standard`
  (**debe salir VACÍO**). Sacar del índice sin borrar: `git rm --cached <f>`.
- **CRLF vs LF ≠ cambio real**: un `.py` con CRLF en disco y LF en HEAD sale `M`/`D`
  pero `git diff` sale VACÍO. **No commitear ni preocuparse.**
- `git commit -F /tmp/msg.txt` falla (git no ve `/tmp`). **Escribir en `.git/CM.txt`.**
  Commits con `-F fichero`, **nunca `-m` con backticks** (bash los ejecuta).
- 🔴 **`git log -S` MIENTE si le tapas la boca.** Muere con
  `fatal: unable to read files to diff` si el historial tiene un `.pdf` (intenta
  tratarlo como texto). Con `2>/dev/null` el comando devuelve **0 líneas** y parece
  "no está". **Acotar el pathspec** (`-- . ':!*.pdf'`), **mirar el returncode** y
  **no ocultar stderr**. Ver §13: caí en esta trampa el 2026-09-18 y reporté un
  falso negativo grave.
- 🔴 **`sed -i` en bash con backticks revienta.** Usar la herramienta de edición.
- 🔴🟢 **En un `.env` GANA LA ÚLTIMA aparición de una clave.** El `.env` raíz tenía **5
  claves dobles** y en las 5 la plantilla iba PRIMERO y el valor real DESPUÉS
  (`GROQ_MODEL`, `GEMINI_MODEL`, `OLLAMA_HOST`, `SUPABASE_ANON_KEY`, `SUPABASE_URL`).
  **Funcionaba solo por el orden de las líneas.** Ordenar alfabéticamente las devuelve a
  `YOUR_VALUE_HERE` **en silencio**. ✅ Resuelto con **`scripts/limpiar_env.py`** (+10
  tests) que **comenta, nunca borra** y verifica equivalencia antes/después.
  Doc: `docs/ENV-LIMPIEZA-2026-09-14.md`.
- ⚠️ **`dotenv_values()` devuelve `OrderedDict` y su `__eq__` SÍ mira el orden** (un
  `dict` no). Comparar `dict(a) == dict(b)`. **Un test que exige de más rechaza cambios
  buenos.**
- **`config/.env` (557 claves) aporta CERO**: el `.env` raíz es superconjunto estricto.
  ✅ **NO trackeado** (`config/.gitignore:2`). Los 5 huecos de plantilla **rellenados
  2026-09-17** (opción B de `docs/ENV-LIMPIEZA-2026-09-14.md` §6).

## 5. 🧪 La suite de tests — las trampas que la tumbaron (2026-09-17)
- 🔴 **Un import que falla en la COLECCIÓN aborta la sesión ENTERA de pytest** (no
  "falla un fichero": **no corre nada**). Pasó con `import yaml` en
  `ecosystem_engine/protocol.py` (import **duro**, declarado solo en el `requirements.txt`
  del engine). **Un import duro de una dependencia opcional es una bomba.** `flasgger`,
  `prometheus-client`, `pyjwt`, `psutil` están protegidos con `try/except` → no rompen,
  pero **apagan funcionalidad sin avisar**. (Los 4 ya están instalados →
  `api_gateway.py` importa.)
- 🔴 **9 ficheros llamados `server.py`** (raíz + 8 engines) → colisión en `sys.modules`.
  `test_daniela.py` necesita el de la **raíz** (único con `init_db`); `test_daniela2.py` y
  `test_daniela_ai.py` el de `daniela-omnipresente/`. **El primero que se importa gana**
  → **48 tests pasaban SOLOS y fallaban JUNTOS.** Arreglo: purgar `server` y `analytics`
  (**los 2 únicos nombres ambiguos de 271**). El hook correcto es
  **`pytest_collectstart`, NO `pytest_pycollect_makemodule`**.
- ⚠️ **`tests/conftest.py` fue REEMPLAZADO una vez**: se perdieron los markers
  (`network`/`android`/`slow`), la raíz en `sys.path` y los fixtures **`client`** y
  **`gateway_client`** (los usan 6 ficheros). Si se reescribe, comprobar que siguen.
- ⚠️ **Un test puede ser FLAKY sin que nadie lo sepa**: `test_manual_collect` afirmaba
  `gc.collect() > 0` (propiedad del ENTORNO, no del código). Si un test mide
  tiempo/memoria/GC, hacerlo determinista (medido: 100 ciclos con `gc.disable()` →
  99-100 estable) o afirmar el contrato. Arreglado en `744825e35`.
- ✅ **"CI verde" = "suite verde" desde `2b05af3ba`.** Antes el CI llevaba una **lista
  fija de 25 ficheros** a mano: `tests/` tiene **34 / 942** y el CI ejecutaba **25 / 852**
  → **90 tests (9,6 %) nunca corrían** (incluidos `test_daniela.py` y `test_daniela_ai.py`,
  los del `conftest.py`). Ahora: `pytest tests/ -m "not network and not android"`.
  Evidencia en el runner: `938 passed, 1 skipped, 3 deselected`.
  ⚠️ **Corrección de mi propia hipótesis**: el CI **SÍ** instalaba `requirements.txt`; la
  causa era que alguien había recortado la lista, no una dependencia que faltara.
- ✅ **3 scripts con nombre de test → `.obsoleto`** (`f8838c5c9`): `test_core.py` (raíz) y
  `core/test_core.py` (duplicados exactos, mismo md5) y `core/test_rag.py`. Los 3 llamaban
  a su función **a nivel de módulo** → importarlos **abortaba la colección entera**. Los de
  Gemini además usan `gemini-3.7-flash` (**no existe**) y cargan `~/.env`. El de RAG **sí
  vale**: es `scripts/check_rag.py` arreglado; en su cabecera está cómo revivirlo como
  `scripts/checks/check_rag_live.py`.
- ✅ **UNA sola config de pytest desde 2026-09-17**: `pytest.ini` **borrado**, todo
  fusionado en `pyproject.toml [tool.pytest.ini_options]`. ⚠️ Antes **ganaba la peor**:
  `pytest.ini` tiene prioridad sobre `pyproject.toml` → `--strict-markers`, `-v` y
  `markers` estaban **muertos**; y su `norecursedirs = auto_generated` **sustituía** la
  lista por defecto (se perdían los excludes de `.venv`, `node_modules`, dirs con punto).
  🔴 **`norecursedirs` REEMPLAZA, no extiende** — hay que repetir los 9 por defecto.
  Verificado tras unificar: `--strict-markers` **ahora sí funciona** (un marker inventado
  falla en colección) y la suite da **939 tests, 0 fallos, 0 errores, 0 skipped**.
- ✅ **Método reutilizable para predecir el CI**: `git worktree add` a un directorio nuevo
  reproduce el runner **sin `.env` ni `data/`** (ambos en `.gitignore`). Ahí se midió que
  los 9 ficheros excluidos pasaban (939 tests, 0 fallos) **antes** de tocar el workflow.
  ⚠️ En Git Bash, pasar `/c/...` a un binario nativo crea `C:\c\...` (la conversión de ruta
  falla con `--junitxml` y con `git worktree add`). Usar `C:/...`.
- Ejecutar: `pytest tests/ -m "not network and not android"` → **939 verdes**.

## 6. 🔴 `ci_health_gate.py` — el bug que tenía el CD rojo (2026-09-17)
- Síntoma: `Connection refused` en ux_engine/scale_engine/chaos_engine/regions. Causa
  real: `main()` tenía **dos condiciones solapadas**; por CLI (`argv is None`) la segunda
  también se cumplía y **machacaba lo parseado con los DEFAULTS** → `--only` se descartaba
  (21 engines en vez de 3) y `--fail-under 100` volvía a 95. Arreglado en `9b3054686`
  (una sola rama) + 2 tests de regresión que ejercitan el **camino CLI real**
  (`main()` sin args + `sys.argv` monkeypatcheado).
- **Los 939 tests no lo veían** porque llamaban a `main(argv=[...])` con argv
  **explícito** → la condición `argv is None` nunca se cumplía. **Verde en local, rojo en
  CD.** ✅ **Los 5 workflows en verde desde `9b3054686`.**

## 7. Higiene del repo — ✅ BLOQUE 🅰️ COMPLETO (2026-09-14)
- ✅ `.gitignore` ampliado (`bin/` 132 MB, `supabase/`, los 7 scripts del RAG,
  `external_assets/DanielaCloud/`, `*.db`, `.env*` salvo `.example`, `output_assets/`).
  Corregido `main` → `/main` (ignoraba `android_app/src/main/`).
  ✅ Regla `$*` (red de seguridad; `$settingsFile` de 14 B **borrado**, su creador no está
  en el repo). ✅ Regla `hermes-epic/` **eliminada**: era **falsa** (es un servicio real —
  `docker-compose.yml:55`, `cd-21.yml:48`, `start_servers.py:6`) y solo escondía los
  ficheros NUEVOS de la carpeta. Invariante `git ls-files -i -c --exclude-standard`:
  64 → **0**.
- ✅ **23 ficheros sacados del índice** (`git rm --cached`, **nada borrado**):
  `credentials.json`, `secret.key`, 4 `.db`, 2 `.mp4`, 2 `.wav`… Copia en
  `.backup-indice-2026-09-14/`.
- ✅ `scripts/cloud_immortal_sync.ps1` reescrito: copiaba `.env` y `.db` **dentro del
  repo** → filtraba credenciales. Ahora en `%USERPROFILE%\DanielaBackups\`.
- ✅ **378 ficheros commiteados (`36a1578f7`, +65.842 líneas)**; árbol limpio.
  `core/__init__.py` + `core/epic_ideas_manager.py` trackeados → **un clon limpio YA puede
  ejecutar la suite**. ✅ `scripts/start_all.bat` estaba CORRUPTO; arreglado.
- ⏳ Pendiente: `.git` = **1,9 GB**; 148 commits "Auto-backup Daniela OS"; 3 gitlinks
  `tencent_suite/Hunyuan*` sin `.gitmodules`; `assets/oficina3d.glb` (90 MB) trackeado.
- Informe: `docs/AUDITORIA-CAMBIOS-2026-09-14.md`.

## 8. Cómo añadir un módulo (aprendido rompiendo cosas)
1. Código en `aig/pixel/X.py` (o `aig/agents/`) + shim `scripts/X.py`; datos
   en `data/X/`.
2. Blueprint de nombre único y `endpoint=` explícito, o dos módulos con `_status`
   revientan el arranque ("overwriting an existing endpoint"). ⚠️ Flask prefija el
   endpoint con **PUNTO** (`blueprint.endpoint`), no guion bajo.
3. `get_instance()` + `register_X_routes(app)`; en `daniela_os.py` usar **`try/except
   Exception`** (¡`except ImportError` NO captura un SyntaxError!). Muchos bloques vecinos
   usan `except ImportError` — **no copiarlo**.
4. **Nunca `os.system` / `shell=True`** → `subprocess.run(list_args)`. Verificar con AST.
5. **Nunca PIPE + timeout**: bloquea para siempre si el nieto sobrevive. Usar
   `tempfile.TemporaryFile` + matar el árbol.
6. `es_android()` antes de `cmd`/`dumpsys` (cmd.exe existe en Windows → falso positivo).
7. Llamadas a servicios LOCALES con `proxies={"http": None, "https": None}`: con
   `HTTP_PROXY` puesto, `localhost` rebota y devuelve 502.
8. **Antes de diseñar, leer lo que ya existe** (casi dupliqué el sistema de memoria:
   `aig/agents/memory_vault.py` **ya funcionaba**).
9. **Añadir un módulo NO sube el contador de rutas solo**: registrar en `daniela_os.py` y
   **re-verificar el total**.
10. **`os.getenv("K", defecto)` devuelve el PLACEHOLDER si la clave existe con valor
    `YOUR_VALUE_HERE`.** Validar siempre que el valor no sea la plantilla.
11. 🔴 **`wave.open(..., "wb")` como context manager SUSTITUYE la excepción original** (su
    `__exit__` falla y tapa el error real con `wave.Error`). **Cerrar a mano** (envolver el
    `with` en try/except **NO** sirve: `__exit__` corre antes). Si falla, **borrar el
    fichero a medias**.
12. **Una función de LECTURA no debe crear esquema** (ni escribir en la BD).
13. **`os.getenv("K", defecto)`**: validar contra plantillas (ver 10).

## 9. Módulos entregados (docs y estado)
- **E-28 memoria semántica** `aig/agents/memory_semantic.py` (+shim): `sqlite-vec`
  sobre `rag_docs`, vectores en tabla virtual `rag_vecs`. `search_hybrid()` = vector +
  grafo del vault. 4 rutas `/api/memory/semantic/*`.
  🔴 **`sqlite-vec` devuelve distancia L2, NO coseno** (restar 1 daba 0.000 en todo):
  vectores unitarios → **`cos = 1 - L2²/2`** (`_l2_a_coseno()`).
  🔴 **Ninguna API de embeddings funciona hoy** (DashScope 403, OpenRouter 401, Groq 403,
  Gemini rota, Ollama apagado). Defecto `hashing` (no captura sinónimos). Cuando arreglen
  las claves: `MEMORY_EMBED_PROVIDER=ollama` + `ollama pull nomic-embed-text` +
  **`reindex`** (cambiar de proveedor invalida los vectores). `OLLAMA_URL=YOUR_VALUE_HERE`
  → urllib revienta; añadido `_url_util()`.
- **B-1 islas de `plugins/`**: `docs/B1-PILOTO-ISLAS-DIAGNOSTICO.md`,
  `docs/B1-PASO2-INTEGRITY-GUARD.md`. 🔴 `invoice_extractor` (el piloto del plan) **NO es
  viable** (apunta a `~/daniela-os`, exige `token.json` con navegador). Medido sobre 32
  plugins: **18 (56 %) hardcodean `~/daniela-os`**; **6 NO SE PUEDEN IMPORTAR**
  (`genai.Client()` a nivel de módulo) y usan `model="gemini-3.7-flash"` (no existe).
  - ✅ `aig/agents/plugin_health.py` → `/api/plugins/health[/<nombre>]`
    (`?importar=false` = auditoría estática). 23 tests. `17 ADAPTAR · 11 CANDIDATO ·
    6 ROTO · 2 INCOMPLETO`.
  - ✅ `aig/agents/integrity_guard.py` → `/api/integrity/{status,sign,check,manifest}`.
    40 tests. **Detección de MUTACIÓN** (vs `epic-pc/file-integrity/`, que es *auditor*;
    complementarios). 🔴 4 defectos del plugin original, con test de regresión: `os.walk`
    sin filtrar (`.venv`+`.git` 1,9 GB), **no detectaba BORRADOS**, rutas `~/daniela-os`,
    **el manifiesto se auditaba a sí mismo**. 🔴 Excluir prefijos **con barra**
    (`static/media/`; `"mediacion.js".startswith("media")` es True). 🔴 Una ruta como
    `POST /sign` **no debe tocar producción en ningún test** (dejaría hashes falsos);
    `?dry_run=true`. **`409` vs `500`:** "hay cambios" es legítimo; `400` = no hay sello.
  - ⏳ **DECISIÓN DEL USUARIO** (afecta a 17 ficheros): cómo resolver `~/daniela-os`.
    **Recomiendo A:** `DANIELA_BASE_DIR` con defecto `~/daniela-os`. Ya aplicada en
    `integrity_guard`. ⏳ **Pendiente: sellar el árbol** (`POST /api/integrity/sign`).
  - **NO tocar `cleaner.py`**: borra recursivamente y su ruta base no existe.
- **B-3 voz offline Piper**: `docs/B3-VOZ-OFFLINE-PIPER.md`.
  `aig/agents/piper_engine.py` → `/api/voice/piper/{status,voices,prepare,say}`.
  39 tests. 🔴 **El plan estaba mal en 3 cosas**: decía 9 rutas → **hay 4**; decía
  "edge-tts + faster-whisper" → **`faster-whisper` NO instalado** (la escucha no funciona
  en el PC); decía "solo falta el motor" → faltaba motor **Y** modelo (109 MB).
  ✅ `piper-tts==1.8.0`. Voz por defecto **`es_AR-daniela-high`** (176 voces, 9 ES).
  Medido: carga 2,59 s · síntesis ~0,5x tiempo real · **síntesis SIN RED OK**.
  ⚠️ `piper.download_voices.list_voices()` imprime por stdout y devuelve `None`; el
  catálogo se lee de `dv.VOICES_JSON` con `urlopen`; verificar el `.onnx` en disco.
  🔴 **`voice_pipeline.py` NO se tocó** (edge-tts sigue vivo); unificar = decisión usuario.

## 10. Red: Tailscale (pendiente) y Móvil (Pixel 8a, Android 17, sin root)
- **Tailscale: móvil SÍ** (`com.tailscale.ipn`, IP **100.65.50.219**); **PC NO**.
  Instalador en `data/instaladores/tailscale-setup-amd64.msi` → lo ejecuta el usuario
  (UAC) con la MISMA cuenta. `cloudflared` sigue vivo: **adb NO puede matarlo** (sin root)
  → `pkill cloudflared` en Termux. **No** `am force-stop com.termux`. El 8082 escucha en
  `0.0.0.0` → conviene ligarlo a la IP VPN. Guía: `docs/TAILSCALE-P0.md`.
- **El home de Termux es INACCESIBLE por adb**: solo `adb push` a `/sdcard`; para ejecutar
  dentro de Termux hay que pedírselo al usuario.
- El DanielaOS del :8082 es un **MOCK** (responde 200/405 sin ejecutar nada).
- Shell Android: aritmética de 32 bits con signo; `find /sdcard` da 0 (usar
  `/storage/emulated/0/`); `sort -h` no existe → `sort -rn`.
- Pendiente del usuario: `bash /sdcard/DanielaOS/deploy/install.sh`; vaciar
  `/sdcard/DanielaOS/.papelera` (4,1 GB, reversible).

## 11. Estado épicas: **28/28 HECHAS** — **397 rutas**
- `scripts/termux_v2_roadmap.py` (E-01..E-34). `EpicIdea` NO tiene `status`: se marca con
  `done=True` + `module="aig/pixel/X.py"`.
- **E-30** `tunnel_guard.py` (8 rutas): 30 → 0 literales de token; gateway con
  `hmac.compare_digest` fail-closed.
- **E-12** `urban_nodes.py` (8 rutas): Open-Meteo + Nominatim + Overpass + Wikipedia, sin
  clave. Nominatim exige User-Agent propio y 1 req/s; Overpass por POST.
- **E-13** `local_brain.py` (8 rutas): Ollama en PC VIVO (24-33 s en frío, 2,3-2,5 s en
  caliente). La parte llama.cpp EN EL MÓVIL **no está hecha**.
- **E-18** `ar_stage.py` (8 rutas): 🔴 **WebXR solo arranca en contexto seguro** (https o
  localhost): por IP no existe `navigator.xr`. Gratis: `adb reverse tcp:5000 tcp:5000`.
- Lo que queda es **operación**, no código.

## 12. Documentación — ✅ EXPANDIDA
- `docs/` es un **vault de Obsidian** (`.obsidian/`, enlaces `[[NOMBRE]]` → `NOMBRE.md`).
  ⚠️ **Anclas de GitHub**: colapsa el emoji dejando **UN** guion y **conserva el acento**.
- Nuevos: **`INDEX.md`** (maestro), `ARQUITECTURA.md`, `INSTALACION.md`,
  `IDEAS-EPICAS-SIGUIENTES-PASOS.md`, `INVENTARIO-CLAVES.md`, los B-1/B-3,
  `REVISION-2026-09-17.md`, `PLAN-COMMIT-2026-09-17.md`, `EJECUCION-2026-09-17.md`,
  `ADR-REPO-LAYOUT.md`.
- **`IDEAS-EPICAS-SIGUIENTES-PASOS.md`** = qué hacer ahora (bloques A/B/C + orden).
  🅰️ COMPLETO; 🅱️ B-1/B-2/B-3 HECHAS; 🅲 (producto: C-1 auditoría fiscal con prueba
  criptográfica, C-2 Pixel como nodo de campo, C-3 white-label) **requiere decisión de
  negocio del usuario**.
- **Roadmap abierto** (`docs/EJECUCION-2026-09-17.md` §7): 1️⃣ CI suite completa ✅ ·
  2️⃣ `.obsoleto` ✅ · 3️⃣ ADR layout ✅ · config pytest unificada ✅ ·
  4️⃣ `scripts/setup_daniela_os_master.ps1` arreglar o borrar (**decisión usuario**;
  tiene comillas mal en L10 y typo `PRoaming` en L14, y hace `Stop-Process -Force` sobre
  Windsurf/VS Code + borra cachés → **no arreglado a propósito**) · 5️⃣ qué es el CD de
  verdad (17 de 21 servicios no despliegan en ningún sitio) · 6️⃣ higiene de git ·
  7️⃣ operación (Tailscale, `faster-whisper`, sello de integridad, `DANIELA_BASE_DIR`).
  🔴 **NO rotar claves** (orden explícita del usuario).

## 13. 🔴 Auditoría 2026-09-18 — y el falso negativo del que hay que acordarse

Informe completo: **`docs/AUDITORIA-2026-09-18.md`**.

### 🔴🔴 El error: reporté "0 commits" y era mentira

Primer pase: `git log --all --oneline -S "$CLAVE" 2>/dev/null | wc -l` → **0**.
Conclusión que escribí: *"la clave NO está en git"*. **FALSO.** El `2>/dev/null`
tapaba esto:

```
E: unsupported filetype .../git-blob-XXXX/reporte_ejecutivo.pdf
fatal: unable to read files to diff
```

`git log -S` **muere** con un `.pdf` en el historial. Sin stderr, `wc -l` da **0
líneas** → parece "no está". **El número era un artefacto del fallo, no un dato.**

- **Control que lo desenmascaró**: `git grep -l -F "$P25" <commit>` SÍ encontraba la
  clave en los commits que citaba el documento. **Cuando dos métodos discrepan, uno
  está roto — averiguar cuál, no elegir el que gusta.**
- **Control del propio método**: `git log -S "assets/oficina3d.glb"` → 2 commits
  (una cadena larga que sí está). El mecanismo funcionaba; lo que fallaba era el
  pathspec.
- **Arreglo**: `-- . ':!*.pdf'` + `if r.returncode != 0 or "fatal" in stderr: avisar`
  en vez de devolver 0.

### Los números reales

| Medida | Antes (mal) | Ahora (bien) |
|---|---|---|
| Commits con `AIzaSyAGTxKesg…` | 0 | **30** (21 ficheros, **11 `.py`**) |
| `client_secret` de Google | "0 commits" | **19** (valor real de 35 chars) |
| Secretos reales en el historial | 1 | **6** |
| `.git` | "1,9 GB" | **1,87 GiB**, de los que **1,46 GB (76%) es historia muerta** |

Los **6 secretos** en el historial: `AIzaSyAGTxKesg…` (30), `client_secret` Google
(19), `TELEGRAM_BOT_TOKEN` (12), `DASHSCOPE_API_KEY` (11), `GROQ_API_KEY` (9),
`OPENROUTER_API_KEY` (9).

**Falsos positivos que hay que saber descartar:**
- `DANIELA_PIN` "59 commits" → el PIN tiene **4 chars**; un prefijo corto coincide
  con cualquier cosa. **Un prefijo debe ser largo (≥20 chars) o el conteo no vale.**
- `sb_secret_` "6 commits" → solo aparece con **14 y 18 chars** (citas + el docstring
  de `scripts/supabase_env.py`). Medir la **longitud** del token, no solo si aparece.
- `OLLAMA_HOST` / `SUPABASE_URL` → un host y una URL no son secretos.

### 🔴 El repo es PRIVADO — cambia la urgencia

`gh repo view --json visibility` → `"visibility":"PRIVATE"`. La documentación decía
"PUBLICADA en cualquier clon": **inexacto**. Rotar sigue siendo necesario, pero **no
es una emergencia pública**. Y `GEMINI_API_KEY` no es un problema de seguridad sino
de **funcionalidad** (su valor es un token OAuth → 401 → ~75 módulos muertos).

### Lo que NO hay que arreglar (aunque lo parezca)

- **`.git` de 1,87 GiB**: 1,46 GB son 5 directorios que **ya no existen en disco**
  (`decenterland/`, `backups/`, `mobile-aig/`, `06_ARCHIVE/`, `pixela8/`;
  32.052 blobs). 🔴 **No encogerlo por separado**: va dentro del **mismo**
  `git filter-repo` que purga los 6 secretos. Una sola reescritura, dos fines.
- **`deploy-prod` MIENTE**: `cd-21.yml:264-265` tiene el `docker compose` real
  **comentado** y en su lugar imprime "Production deployment completed". El "CD"
  arranca **4 de 18** servicios → es un **smoke test**, no un deploy.
- **3 gitlinks sin `.gitmodules`** (`tencent_suite/Hunyuan*`): un clon deja 3 carpetas
  vacías **en silencio**. 552 MB de clones anidados que solo usan `prototypes/`.
- **Los 2 `.glb` (173 MB): NADA los carga.** La única mención es un string de
  descripción (`frontend_epic_ideas.py:119`). Y borrarlos **no encoge `.git`**.
- `scripts/setup_daniela_os_master.ps1`: **borrar** (roto + destructivo).

### Método: auditar secretos en git (reutilizable)

1. **Nunca** `2>/dev/null` en la medición. Capturar `stderr` y **mirar el returncode**.
2. **Acotar el pathspec** para esquivar el `.pdf`: `-- . ':!*.pdf'`.
3. Usar un prefijo de **≥20 chars** del valor real (descarta falsos positivos).
4. **Medir la longitud** del token hallado: <25 chars = cita/plantilla, no secreto.
5. Comprobar **HEAD aparte del historial**: son dos preguntas distintas.
6. Cruzar con `git grep -F <prefijo> <commit>` como **control independiente**.
7. Comprobar la **visibilidad del repo** (`gh repo view`): cambia la gravedad.
8. Scripts usados: `.git/scan_key.py`, `.git/scan_historial.py`, `.git/scan_head.py`
   (viven en `.git/`, no se commitean).

## 14. 🔴 Reset de arquitectura 2026-09-18 — por que "no funciona nada"

Informe: **`docs/RESET-ARQUITECTURA-2026-09-18.md`**. Todo medido ejecutando.

### 🔴 La causa nº1: el cerebro es un STUB

`aig_core.py:142-148`:

```python
def ask(self, query: str, **context: Any) -> Dict[str, Any]:
    """Very naive implementation – echoes the query."""
    answer = f"Respuesta simulada a la consulta: '{query}'"
    return {"query": query, "answer": answer, "context": context}
```

Y `daniela_os.py:766` (`core_ask`) lo llama para **todo** lo que pasa por `/core`.
**El núcleo de decisión nunca pensó.** No es un bug: es un placeholder de 177 líneas
que se quedó en producción. El docstring del módulo lo dice sin disimular
("*deliberately lightweight*").

🔴 **Lección: un stub con nombre serio es peor que un error.** `aigCore.ask()`
devuelve un `dict` válido con `status` implícito OK, así que **ninguna capa de arriba
detecta que no hay IA**. Un `raise NotImplementedError` habría saltado el primer día.

### Las otras 5 causas (todas medidas)

| # | Causa | Evidencia |
|---|---|---|
| 1 | **45% de rutas dependen del móvil** | 178 de 397 son `/api/pixel/*`; LAN y Tailscale inalcanzables |
| 2 | **4 de 5 proveedores de IA caídos** | OpenRouter 200 · Gemini 401 · Groq 403 · DashScope 401 · Ollama apagado |
| 3 | **El RAG está vacío** | `rag_docs: 0 filas`, `memory_links: 0 filas`, `no such module: vec0` |
| 4 | **Producción va 5 días por detrás** | imagen del 13-sep → `/api/router|urban|guard|vault/status` = **404** |
| 5 | **14 interfaces sin jerarquía** | `:5000 :9200 :9300 :3002 :9500 :9600 :9997 :9998 :9999 :9400 :9700 :9800 :8090 :5020` |

### ⚠️ Dos trampas de medición que hay que recordar

1. **`com.docker.backend.exe` aparece como dueño del puerto 5000.** No es que Docker
   "robe" el puerto: es el **reenviador de puertos publicado** hacia el contenedor.
   Concluí "Docker ocupa :5000 y Daniela no corre" y **era falso**: `docker ps`
   demostró que `aig-daniela` está arriba y healthy. **Antes de acusar a un
   proceso, mirar `docker ps`.**
2. **`HTTP_PROXY` está activo en este PC.** Sin `--noproxy '*'`, `curl` a `localhost`
   devuelve **502** y *parece* caído. Con el bypass: 200. Ya está documentado en §7
   del método de módulos, pero **aplica a toda medición de salud**.

### Los agentes: el mapa real

- ✅ **Cableados**: `agent_marketplace` (`/api/agents`, 9 rutas), `agent_court` (4),
  `agent_invoice_graph` (4), `agent_scoreboard` (2), `agent_expediente` (2),
  `agent_cad_studio` (2), `memory_semantic` (4), `plugin_health` (10),
  `integrity_guard` (4), `piper_engine` (8).
- ❌ **Código muerto** (3 copias: raíz + `agents/` + `aig/agents/`, 0 rutas,
  y `daniela_os.py` **no los importa**): `agent_calendario`, `agent_correo`,
  `agent_documentos`, `agent_redes`, `agent_vigia`, `agent_epic_ideas`.
  `auto_swarm_dispatcher` tiene **0 usos en todo el repo**; `swarm_planner`,
  `swarm_intelligence`, `code_generation_agent`, `cyber_sentinel` tampoco están cableados.
- ⚠️ **`agents_catalog.json` NO describe lo que corre**: es un catálogo de
  **marketplace** con `installs`, `rating`, `credits_per_run`. 10 "agentes" de
  escaparate. No confundirlo con la realidad.

### El plan (una frase)

**No construir nada nuevo.** Un backend (`daniela_os.py` :5000, 397 rutas), una
puerta (nginx :80/:443, **ya existe**), una pantalla, una voz (Piper, **ya existe**).
Apagar los 10 contenedores de UI. Para el móvil: **Tailscale en el PC** (falta, pide
UAC; instalador en `data/instaladores/tailscale-setup-amd64.msi`).

### Orden de arreglo

**Formalizado como épicas E-33 a E-48 (FASE 12)** en
`scripts/termux_v2_roadmap.py`. Informe: `docs/EPICAS-ARREGLO-2026-09-18.md`.
**Camino crítico: E-36 → E-33 → E-45.**

1. **Rebuild del contenedor** (5 min) — sin esto nada nuevo está activo. → **E-36**
2. **Conectar el chat al enrutador real** (1 h). → **E-33**
   ⚠️ **Corrección 2026-09-18 (medida):** el proveedor que funciona es **Cohere**
   (`command-a-03-2025`), **no** OpenRouter. OpenRouter devuelve **200 en `/v1/models`**
   pero **401 "User not found"** en una completion real. **Una clave puede pasar la
   lista de modelos y fallar el uso** → probar siempre con una completion, no con
   `/v1/models`. `model_router.py` ya recorre la cadena; E-33 debe **reutilizarlo**.
3. **Arrancar Ollama** + `nomic-embed-text` (15 min). → **E-34**
4. **Reindexar el RAG** (30 min) — hoy 0 documentos. → **E-35**
5. Tailscale en el PC (usuario, UAC). → **E-39**
6. Apagar las 10 UIs duplicadas. → **E-38**
7. Reconectar el móvil. → **E-41**

⚠️ **El `status` por defecto de `termux_v2_roadmap.py` es `cli_audit`** y muestra
datos **caducados**. Usar `roadmap` / `ideas` / `export`. No fiarse del `status`.

---

## 15. FASE 12 — las 16 épicas E-33..E-48 (2026-09-18)

Informe: `docs/EPICAS-ARREGLO-2026-09-18.md`. Inyectadas en
`scripts/termux_v2_roadmap.py` con `phase=12`, `done=False` (**E-32 era el id máximo**;
no había test que referenciara el roadmap). Total: **16 épicas · 22 rutas · 186 h · $0/mes**.

| id | qué |
|---|---|
| **E-33** | Cerebro real: `aig_core.ask()` → `model_router` (matar el stub) |
| **E-34** | Ollama + embeddings (`nomic-embed-text` ya descargado; solo hay que arrancarlo) |
| **E-35** | RAG con contenido (hoy `rag_docs: 0`) |
| **E-36** | Rebuild del contenedor de producción (congelado el 13-sep) |
| **E-37** | Front único (una sola pantalla) |
| **E-38** | Apagar las 10 UIs duplicadas |
| **E-39** | Tailscale en el PC (**usuario**, UAC) |
| **E-40** | Modo degradado para `/api/pixel/*` (45% de las rutas) |
| **E-41** | Reconexión del Pixel |
| **E-42** | Scheduler: revivir los 6 agentes muertos |
| **E-43** | Un solo swarm |
| **E-44** | Un agente, una copia |
| **E-45** | `/api/health` honesto (semáforo por subsistema, 503 si lo crítico cae) |
| **E-46** | Test anti-stub (2 h, la más barata y la que más protege) |
| **E-47** | Un solo `.env` |
| **E-48** | Purga del historial con `git filter-repo` (**después** de rotar) |

**Camino crítico: E-36 → E-33 → E-45 → E-46.** El resto no se nota sin esos.

**Aprendizaje de método que costó caro aquí:** el plan escrito decía "el único
proveedor vivo es OpenRouter"; **medido, era Cohere**. Van **7 veces** que medir
antes ha desmentido al documento. Ver §0.1.

---

## 16. 🔴🔴 El incidente de `.git` (2026-09-18) — y las tres trampas que reveló

**Resuelto.** Informe completo: `docs/INCIDENTE-GIT-2026-09-18.md`.
`.git` pasó de **1,87 GiB a 15 MB**; se borraron los `.pack`, `refs/` y `logs/`.
**El árbol de trabajo quedó intacto y el historial se recuperó entero** desde el
remoto (`origin/universo-v1` estaba en `b83426649` = HEAD local). Nada commiteado
se perdió.

### Trampa 1 — `"not a git repository"` NO significa permisos

Git exige que existan `.git/HEAD`, `.git/objects` **y `.git/refs`**. Faltaba
`refs/` (un directorio **vacío**) y eso bastaba para que todo comando fallara con
*"not a git repository"*. **Ante un error de git, listar qué falta en disco antes
de teorizar.** Arreglo: `mkdir -p .git/refs/heads .git/refs/tags .git/refs/remotes/origin .git/logs`.

### Trampa 2 — un `.idx` sin su `.pack` rompe `fsck` y **revierte transacciones**

Tras recuperar los packs quedaron 4 `.idx` huérfanos + un `multi-pack-index`
caducado (apuntaban a packs borrados). Efecto: `git fsck` lleno de
`failed to load pack in position N` y —lo importante— **`git fetch` imprimía
`[new branch] … -> origin/x`, salía con exit 0, y NO persistía los refs** (la
transacción se revertía en silencio). **Borrar los `.idx` sin `.pack` y el
`multi-pack-index`, y volver a comprobar `fsck` antes de dar algo por bueno.**

### Trampa 3 — `gc --auto` convierte un SIGTERM en un repo inconsistente

`gc.auto=10000` estaba activo y el repo tenía **~1,4 GB de objetos inalcanzables**
(restos previos al `filter-repo` del 11-sep). Un `git stash push` disparó
`gc --auto` → `repack -a -d` + `prune`, que **borra exactamente eso**; al morir el
proceso a mitad quedaron los `.idx` sin `.pack`.
→ **Prevención aplicada: `git config gc.auto 0` en este repo.** La recolección de
basura pasa a ser **siempre explícita**. Lección general: **no interrumpir nunca un
`git` que pueda estar repackando**, y en repos con mucha basura inalcanzable,
tener `gc.auto=0`.

### Trampa 4 — tres módulos `aig_core`, y gana el que diga `sys.path`

| Fichero | Qué es | Quién lo carga |
|---|---|---|
| `aig\aig_core.py` | **el cerebro** | `get_core()` de `daniela_os`/`api_gateway`, **por ruta explícita** |
| `aig\scripts\aig_core.py` (471 B) | shim → `from aig.core.aig_core import *` | `import aig_core` **dentro de daniela_os** |
| `aig\aig\core\aig_core.py` | `IntentRouter`: dispatcher **por palabras clave**, NO un LLM | `agent_scoreboard` |

`daniela_os.py:30` hace `sys.path.insert(0, _REPO_ROOT/"scripts")` → dentro de ese
proceso el `import` normal va al **shim**. Pero `get_core()` carga la **raíz** por
ruta. **Regla: en los tests, cargar el core como lo hace producción (por ruta
explícita), nunca con `import`.** Me hizo perder tiempo un test que decía "no
existe `SinProveedorError`" cuando sí existía — en el otro módulo.

### Trampa 5 — `2>/dev/null` otra vez (van dos)

No volvió a pasar aquí, pero es la misma familia: **un error nunca significa "no
está"**. Ver §0.6 y §13.

### Datos que hay que recordar de este incidente

- **Pérdidas reales:** 1 `stash` local y la rama `uistable-flat` (ambas basura; un
  stash **nunca** se empuja → irrecuperable por diseño). Los **20 tags** y 5 ramas
  **sí** estaban en el remoto y se restauraron.
- **Anomalía abierta:** en este entorno `git fetch` **no persiste `refs/remotes/*`**
  (exit 0 pero sin efecto); `git update-ref` sobre esa ruta tampoco. **Escribir el
  fichero suelto a mano SÍ funciona** (probado). No afecta a `commit`/`push`; **sí**
  a `git pull` sin `fetch` previo.
- **Pendiente:** `git repack -a -d` para deduplicar (2 packs: 1,2 GB + 456 MB) y un
  `git bundle` de respaldo periódico — hoy el único respaldo real es GitHub.
- **Respaldo del incidente:** `C:\Users\Alejandro\aig-recuperacion-2026-09-18\`.

---

## 17. E-45 + E-46 (2026-09-18) — health honesto, tests anti-stub y tres trampas nuevas

### La lección más importante: **juzgar la suite con el filtro del CI**

El CI ejecuta `pytest tests/ -m "not network and not android"`. En local (sin `-m`)
vi **2 fallos** y **los di por malos**: `test_gemini_responde` y
`test_retencion_de_contexto_y_memoria`. Los dos están **marcados `network`**, así que
**el CI los deselecciona**. El CI estaba verde y sigue verde.
→ **Nunca juzgar la suite con un filtro distinto al del CI.** Comando bueno:
`pytest tests/ -m "not network and not android"` (da la línea de resumen; con `-q`
dos veces se la come).

### 🔴 Cuatro `model_router.py`, y el de producción no es el de la raíz

| Fichero | Tamaño | Proveedores |
|---|---|---|
| `aig/pixel/model_router.py` | 36.013 B | **9** (`deepseek`, `qwen`/DashScope incluidos) ← **PRODUCCIÓN** |
| `model_router.py` (raíz) | 35.145 B | 7 |
| `core/model_router.py` | 35.145 B | 7 |
| `scripts/model_router.py` | 272 B | shim → `aig/pixel/...` |

`daniela_os.py:30` mete `scripts/` en `sys.path[0]` → dentro de daniela_os
`import model_router` va al **shim** → **aig/pixel** (9). **Los tests cargan
la de la raíz (7).** → **los tests NO ejercitan el router de producción** (E-44).
Consecuencia práctica: al limpiar claves en un test hay que limpiar las de los **9**
(`DEEPSEEK_API_KEY`, `QWEN_API_KEY`, `DASHSCOPE_API_KEY` además de las 7 conocidas).

### 🔴 `estado()` publica una caché de sondas SIN mirar la antigüedad

`EnrutadorModelos.estado()` devuelve `disponibles_ahora` = proveedores con
`salud[pid]["ok"]`, y **`salud` se persiste en `data/model_router/estado.json`**.
Resultado medido: tras **borrar todas las claves**, el health seguía diciendo
"cohere disponible". → **Una caché persistida no es una comprobación.** Si se
informa de ella, hay que mirar `cuando` contra el `ttl_salud_s` **y** volver a
comprobar que el proveedor sigue teniendo clave.

### 🔴 Un módulo cargado por ruta hay que registrarlo en `sys.modules`

Cargar con `importlib.util.spec_from_file_location` + `module_from_spec` +
`exec_module` **sin** `sys.modules[spec.name] = mod` revienta con
`AttributeError: 'NoneType' object has no attribute '__dict__'` en cualquier
`@dataclass`: `dataclasses` resuelve `cls.__module__` buscándolo en `sys.modules`.
(Por eso `daniela_os.get_core()` sí lo registra.)

### Cómo se prueba un test anti-stub: **en su rama de fallo**

Regla del proyecto (nº 5). Reintroduje el stub a propósito en `aig_core.py`,
corrí los tests → **3 fallaron** con `"respuesta simulada a la consulta: ..."`,
revertí y comprobé con `git diff` **vacío**. Un test anti-stub que nunca se ha visto
fallar no protege de nada.

### Resultado

- `aig_core.py`: `ask()` real, `SinProveedorError`, VERSION 0.2.0.
- `daniela_os.py`: `/api/health` (cerebro crítico + rag + movil, 503 si lo crítico
  cae) y el `except` de Gemini que ya no miente con "Usando modo local".
- `tests/test_anti_stub.py`: 10 tests, sin marca `network`.
- **Suite con el filtro del CI: 949 passed, 3 deselected, 0 failed.**

---

## 18. E-36 (2026-09-18) — el despliegue honesto y los 4 bugs que aparecieron al medirlo

### 🔴 Lo que estaba mal NO era lo que decía el plan

El plan decía "el CD finge desplegar". Cierto, pero eran **tres** workflows, no uno,
y la causa real era otra: **no existe destino de despliegue**.

```console
$ gh api repos/aig/aig-MONOREPO/actions/runners
{"total_count":0,"runners":[]}
$ gh secret list        # ni DEPLOY_HOST ni SSH_KEY: solo 6 claves de API
```

Cero runners, cero secretos de despliegue, PC en red doméstica sin ingreso público
→ **un runner de GitHub no tiene camino de red hasta el PC**. La orden `docker compose`
estaba comentada porque *no puede funcionar*. El pecado no fue comentarla: fue
**seguir imprimiendo "Production deployment completed"** después.

Y `cd.yml` iba más allá: su job de health checks imprimía 11 `"✓ Placeholder check
passed"` + `"All services are healthy!"` **con los `curl` comentados**. No podía
fallar nunca. **Un health check que no puede fallar no es un health check.**

### 🔴 El gate que decide si el despliegue está bien TAMBIÉN mentía

`scripts/ci_health_gate.py` aceptaba solo `{"alive","online","active"}`. Vocabulario
**medido** de los 21 motores reales:

| Palabra | Motores |
|---|---|
| `alive` | 10 |
| `ok` | 3 |
| `running` | 5 |
| `active` | 1 |
| `operational` | 1 |
| *(sin campo `status`)* | 1 (`regions`) |

Antes: `21 motores · 14 sanos · 66.67% · exit 1` (7 falsos negativos con HTTP 200).
Después: `21 · 21 · 100% · exit 0`.

**Un gate con 7 falsos negativos de 21 es peor que no tener gate**: `--fail-under 95`
no se alcanza nunca y eso **enseña a ignorar el rojo**. Si vas a medir la salud de
algo, mide primero **qué palabras usa de verdad** (`for eng in ENGINES: print(payload)`),
no lo que crees que debería decir.

### 🔴 Tres bugs de "solo pasa en la máquina real"

1. **Ruta inventada.** `deploy.sh`/`deploy.ps1` probaban `/status` → **404 en los 21**;
   la buena es `/api/status` (**200**). Los 19 motores salían `OFFLINE` estando sanos.
   **Un 404 en una ruta que te has inventado parece un servicio caído.**
2. **El plugin `docker compose` NO existe en este PC.** Solo el binario suelto
   `docker-compose` v5.5.1 (`docker compose` → *"unknown command"*). `deploy.sh`
   **comprobaba** `docker-compose` pero luego **invocaba** `docker compose` → con
   `set -e` moría en el paso 4. **El runner de Ubuntu SÍ tiene el plugin: el CI jamás
   lo habría detectado.** Los fallos que solo ocurren donde de verdad se despliega no
   los ve el CI.
3. **El proxy convierte "caído" en 502.** Con `HTTP_PROXY` puesto, el puerto 8082
   (caído) da **502 con proxy** y **000 sin proxy**; el 8080 (vivo) da 200 en ambos.
   Un 502 parece un fallo del gateway; la causa real era "no hay nadie escuchando".
   Para URL local el proxy no aporta nada → `instalar_opener_sin_proxy()` +
   `curl --noproxy '*'`.

### 🔴🔴 TRAMPA DE HERRAMIENTA: dos ediciones al MISMO fichero en un solo mensaje se pisan

Dos veces en esta épica: lancé dos `Edit` sobre el mismo fichero en el mismo mensaje
y **una de las dos se perdió** (el fichero quedó con una firma vieja). Síntoma:
`TypeError: check() got an unexpected keyword argument 'noproxy'` o
`UnboundLocalError: noproxy`. **Regla: una edición por fichero y por mensaje.**
Verificar con `grep -n "^def "` después de editar una función.

### 🔴 Otras dos trampas de entorno

* **`subprocess.run(["bash", ...])` en Windows resuelve al stub de WSL**
  (`System32\bash.exe` → `wsl.exe`), que está **bloqueado por política** → "Acceso
  denegado" en UTF-16. Hay que pasar la **ruta absoluta** de Git Bash
  (`shutil.which("bash")` devuelve PortableGit; comprobar que no contenga `system32`).
* **`2>/tmp/x.json` no vale para leerlo luego desde Python de Windows**: `/tmp` es de
  Git Bash. Escribir en una ruta del repo (p. ej. `.git/`).

### 🔴 Un landmine que estaba ahí: `scripts/deploy.sh`

Hace `pkill -9 -f "python3"` (mata **todo** python del PC, incluido DanielaOS),
`git add .` + `git commit` a ciegas y **`git push origin main --force`**, y apunta a
`~/apps/aig-MONOREPO` (no existe en el PC). Es de Termux. Se le puso **guardia**:
sin `PREFIX` con `com.termux` no se ejecuta. Probado: `exit 1` con el motivo.
**Antes de añadir un script a `scripts/`, comprobar si ya había uno con el mismo
nombre que hace algo peligroso.**

### Qué queda

- `scripts/deploy_prod.sh` (**NUEVO**) es el despliegue de verdad: preflight →
  `build` → `up -d --remove-orphans` → espera → **health gate que puede fallar**.
  `--dry-run` probado (exit 0). Detecta el compose real. **No toca git.**
- **26 tests nuevos** (`tests/test_deploy_honesto.py`), **probados en su rama de
  fallo**: reintroduje `echo "Production deployment completed"` → falló con el
  mensaje exacto; revertido → verde. Inspeccionan los **cuerpos de los pasos**
  (`run`), no el texto crudo: un comentario que explica la historia es legítimo.
- **Suite con el filtro del CI: 975 passed, 3 deselected, 0 failed** (antes 949).
- ⚠️ **No se ha podido ver un run verde**: la cuota de Actions está agotada
  (`steps: []`, `runner_name: ''`). Ver §16.
