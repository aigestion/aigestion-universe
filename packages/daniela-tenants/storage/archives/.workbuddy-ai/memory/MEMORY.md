# MEMORY.md — aig / DanielaOS (`C:\Users\Alejandro\aig`)

Daniela controla un Pixel 8a desde el PC, solo capas gratis ($0/mes). Usuario
**principiante en git**, escribe en español con faltas.
Ejecutar: `PYTHONPATH="C:/Users/Alejandro/aig" ./.venv/Scripts/python.exe …`
📖 **Detalle de cada lección: `LECCIONES-TECNICAS.md` (§0–§18). Índice de docs: `docs/INDEX.md`.**
Este fichero es **solo el índice**: antes de tocar algo delicado, leer el detalle.

**Estado (2026-09-18): 397 rutas · suite con el filtro del CI = 975 passed, 0 failed.**
Rama única: `main` = `universo-v1` = HEAD (`6bd41af5d`).
🔴 **Juzgar la suite SIEMPRE con el filtro del CI:** `pytest tests/ -m "not network and not android"`.
Sin el filtro salen 2 fallos que el CI **deselecciona** (clave Gemini muerta y un test
que envía `prompt` donde la ruta lee `message`) → **el CI está verde**.
🔴 **Este repo tiene `gc.auto=0`** (tras el incidente de `.git`): la recolección es
**explícita** a propósito. No la reactives.

## 🔴 Reglas de método — detalle: §0
1. **MEDIR antes de actuar.** El plan escrito ha estado mal **7 veces**: ejecutar el
   código *antes* de diseñar. Y **mirar el VALOR, no el NOMBRE**.
2. **Un test con argumentos explícitos NO prueba el camino de producción.**
3. **Verde en un sitio ≠ verde en otro.** Predecir el CI con `git worktree add`.
4. **Un script que reescribe un fichero crítico DEBE probarse en su rama de FALLO.**
5. 🔴🔴 **NUNCA `2>/dev/null` en una medición.** `git log -S` **muere** con
   `fatal: unable to read files to diff` si el historial tiene un `.pdf`: ocultar el
   stderr devuelve **0 líneas y parece "no está"** (reporté "0 commits" y estaba en 30).
   Acotar el pathspec (`-- . ':!*.pdf'`) **y mirar el returncode**.
6. **Una clave puede pasar `/v1/models` y fallar el uso real** (OpenRouter 200 → 401).
   **Probar con una completion.** Hoy solo funciona **Cohere** (`command-a-03-2025`).
7. 🔴 **`"not a git repository"` NO es permisos**: git exige que exista `.git/refs`.
   **Listar qué falta en disco antes de teorizar.** §16.
8. 🔴 **Un job de CI en rojo con `steps: []` y `runner_name: ''` NO ha fallado: no ha
   corrido** (2026-09-18: 3 workflows rojos por **cuota de Actions agotada**; los 21
   builds estaban verdes). Mirar pasos y runner antes de culpar al código.
9. 🔴🔴 **Dos ediciones al MISMO fichero en un solo mensaje SE PISAN**: perdí una firma
   de función 2 veces (síntoma: `TypeError`/`UnboundLocalError` en algo recién añadido).
   **Una edición por fichero y mensaje**; luego `grep -n "^def "`.

## 🔴 Lo que hay que saber antes de tocar nada
- 🔴 **HAY TRES `aig_core` Y GANA EL QUE DIGA `sys.path`.** El **cerebro** es
  `aig\aig_core.py` (raíz); lo cargan `get_core()` de `daniela_os` y `api_gateway`
  **por ruta explícita**. Un `import aig_core` normal resuelve al **shim**
  `scripts/aig_core.py` (porque `daniela_os.py:30` mete `scripts/` en
  `sys.path[0]`), que reexporta `aig/core/aig_core.py` — un **dispatcher por
  palabras clave, NO un LLM**. **En tests: cargar el core como producción (por ruta).**
  Un módulo cargado por ruta **hay que registrarlo en `sys.modules`** o `@dataclass`
  revienta (`AttributeError: 'NoneType' object has no attribute '__dict__'`).
- 🔴 **Igual con `model_router`: hay CUATRO; el de producción es
  `aig/pixel/model_router.py` (9 proveedores), NO el de la raíz (7).** Los tests
  cargan el de la raíz → **no ejercitan el router real** (candidata a E-44).
- **Estructura: manda la RAÍZ.** `import X` → `aig\X.py`, NO `aig/pixel/` ni
  `scripts/` (shims; su docstring **miente**). ~231 `.py` en la raíz.
  **Verificar:** `python -c "import X; print(X.__file__)"`. Ver ADR-015.
- **`git fetch`/`git push` NO persisten refs aquí** (exit 0, sin efecto): `git status -sb`
  **MIENTE**. Usar `git ls-remote origin`. Workaround: escribir los ficheros sueltos de
  `refs/remotes/origin/`. Hay 2 `stash`; **no `stash clear`**.
- **Secretos: son SEIS** (en el historial). Repo **PRIVADO** → rotar es necesario pero
  **no urgente-hoy**. 🔴 **NO rotar** (orden del usuario). Detalle: §3 y
  `docs/INVENTARIO-CLAVES.md` §6. No tocar `.env`, `config/env/.env.master`,
  `data/tunnel_guard/backups/`.
- 🔴 **En este PC NO existe el plugin `docker compose`** (`unknown command`): solo
  `docker-compose` v5.5.1. **Detectarlo, no asumirlo** (el runner de CI sí lo tiene → el
  CI nunca ve este fallo). Y la ruta de salud es **`/api/status`**: `/status` da **404 en
  los 21 motores**.
- **Un import que falla en la COLECCIÓN aborta pytest ENTERO** (import duro de
  dependencia opcional).
- **9 `server.py` colisionan en `sys.modules`**; `tests/conftest.py` purga `server` y
  `analytics` (si se reescribe: conservar markers, raíz en `sys.path`, fixtures
  `client`/`gateway_client`).
- **`norecursedirs` REEMPLAZA la lista por defecto**, no la amplía. Config única de pytest
  en `pyproject.toml` (`pytest.ini` borrado el 2026-09-17). **En un `.env` gana la
  ÚLTIMA aparición de una clave.**
- `git check-ignore` **miente** si el fichero ya está trackeado. Invariante:
  `git ls-files -i -c --exclude-standard` **debe salir VACÍO**.
  **CRLF vs LF ≠ cambio real** (`M`/`D` con `git diff` VACÍO → no commitear).
- Commits con `-F .git/CM.txt`; **nunca `-m` con backticks**. 🔴 `sed -i` con backticks
  revienta → usar la herramienta de edición.
- En Git Bash, `/c/...` a un binario nativo crea `C:\c\...`. **Usar `C:/...`.** Y
  `subprocess.run(["bash", …])` en Windows va al stub de WSL (bloqueado): pasar la **ruta
  absoluta**. `/tmp` es de Git Bash → temporales a una ruta del repo.
- **Nunca `os.system`/`shell=True`** → `subprocess.run(list_args)`. **Nunca PIPE +
  timeout** → `tempfile.TemporaryFile` + matar el árbol.
- ⚠️ **`HTTP_PROXY` activo**: convierte un puerto local **caído** en **502** (8082: 502 con
  proxy / 000 sin) y parece un fallo de gateway. Usar `--noproxy '*'`.
- **Antes de diseñar, leer lo que ya existe** (casi dupliqué `memory_vault.py`;
  `model_router.py` **ya tenía** la cadena de proveedores → E-33 debía reutilizarlo).
- `docs/` es un **vault de Obsidian**.

## Contexto del proyecto
- **19 microservicios** + `aig-shared/` + Docker Compose + 5 workflows.
- **505 copias IDÉNTICAS**, casi todas **estructurales** (los 19 servicios).
  **NO borrar sin refactor deliberado.**
- **28/28 épicas antiguas HECHAS**; corre **FASE 12 (E-33..E-48)** → §15.
  **Camino crítico CERRADO: E-36 ✅ → E-33 ✅ → E-45 ✅ → E-46 ✅.**
- ⏳ **Pendiente del usuario**: rotar los 6 secretos (**NO hacerlo**), Tailscale en el PC
  (UAC), reconectar el móvil, decidir `~/daniela-os` (`DANIELA_BASE_DIR`), y
  `scripts/setup_daniela_os_master.ps1` (destructivo, **no tocado a propósito**).

## Informes del 2026-09-18 — detalle completo: §13–§18
`docs/AUDITORIA-2026-09-18.md` · `docs/RESET-ARQUITECTURA-2026-09-18.md` ·
`docs/EPICAS-ARREGLO-2026-09-18.md` · `docs/E-36-DESPLIEGUE-HONESTO.md` ·
`docs/INCIDENTE-GIT-2026-09-18.md`.
Lo esencial: nada está roto, pero el sistema estaba **fragmentado y sin cerebro**
(cerebro STUB, 45% de rutas `/api/pixel/*`, 1 de 5 proveedores de IA, RAG vacío,
14 interfaces web, 6 agentes muertos) → de ahí las **16 épicas (E-33..E-48)**.
🔴 **`.git` perdió los `.pack` el 2026-09-18** (1,87 GiB → 15 MB); el árbol quedó intacto
y el historial se recuperó del remoto. Pérdidas: 1 `stash` local y `uistable-flat`.
**Pendiente: `git repack -a -d`** (quedan 2 packs).
