# Auditoría y recuperación post-refactor — 2026-09-20

**Estado final: la suite completa está en verde (1028 passed, 0 fallos).**
Comando: `./.venv/Scripts/python.exe -m pytest tests/ -m "not network and not android"`

---

## 1. Contexto

En el árbol de trabajo del repo principal aparecían **566 ficheros trackeados borrados**,
59 modificados y un worktree roto en `C:\Users\Alejandro\worktrees\aig\total-sycamore`.

El usuario confirmó que **los borrados fueron intencionados**: un refactor de reubicación.

---

## 2. Veredicto del refactor: correcto, pero dejó dos clases de daño

### Lo que el refactor hizó bien (verificado)

| Comprobación | Resultado |
|---|---|
| Historia de git | Intacta — HEAD `cf42c19e`, reflog limpio, refs y objetos OK |
| Los 228 borrados de `scripts/` | Eran **225 shims** de ~460 B (`"""Compat shim..."""` + `from aig.x.y import *`). Borrarlos deja el código real. |
| `scripts/` reorganizado | 7 subcarpetas: `agents/` 34, `archive/` 215, `core/` 56, `daniela/` 81, `deploy/` 41, `pixel/` 37, `utils/` 105 |
| Contenido íntegro | `scripts/core/ci_health_gate.py` **idéntico byte a byte** a `HEAD:scripts/ci_health_gate.py`. De 32 basenames, 3 idénticos y 29 son la versión *real* (HEAD tenía el shim) |
| `frontend-optimization/` | No es un borrado del árbol: se eliminó en el commit `d3be7ba7` ("frontend unification") |
| Sintaxis | `compileall` de los modificados → exit 0 |

**Las "−97.982 líneas" del diff eran el efecto de borrar shims y duplicados, no contenido perdido.**

---

## 3. Causa raíz del daño: desplazamiento de exactamente 1 directorio

El refactor movió ficheros **un nivel más abajo**:

```
tests/x.py          →  tests/core/x.py
scripts/x.sh        →  scripts/deploy/x.sh
model_router.py     →  core/model_router.py
```

Todo cálculo de ruta basado en la posición del propio fichero quedó desviado:

| Patrón original | Correcto tras el refactor | Nº ficheros |
|---|---|---|
| `Path(__file__).resolve().parents[1]` | `parents[2]` | 7 |
| `os.path.join(os.path.dirname(__file__), "..")` | añadir otro `".."` | 11 |
| `dirname(dirname(abspath(__file__)))` | `dirname` × 3 | 2 |

**Consecuencia medida al inicio:** 14 ficheros de test **ni coleccionaban** (751 tests),
más 48 fallos.

---

## 4. Tres bugs REALES de producción (no eran solo tests)

### 4.1 El core no importaba
`core/aig_core.py` es un shim que re-ejecutaba `RAIZ/aig_core.py` — ruta que el
refactor eliminó. Reventaba con `FileNotFoundError` y con él todos los tests que cargan el
core por ruta. El sucesor real es `scripts/core/aig_core.py` (idéntico al antiguo,
solo cambian los finales de línea).

**Fix:** shim con lista de rutas candidatas y error explícito si no encuentra ninguna.

### 4.2 El despliegue a producción habría fallado
`scripts/deploy/deploy_prod.sh` calculaba `REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"`, que
ahora daba `scripts/` en vez de la raíz. Además:
- `COMPOSE_FILE="docker-compose.prod.yml"` → está en **`config/`**
- `HEALTH_GATE="scripts/ci_health_gate.py"` → está en **`scripts/core/`**

**Habbía fallado en la línea 118** (`no encuentro docker-compose.prod.yml`).
**Fix:** `../..` + resolución con respaldo de ambas rutas.

### 4.3 El scheduler no cargaba ningún agente
`daniela-os/shared/scheduler.py` detectaba `REPO_ROOT` buscando `server.py` en la
raíz (movido a `core/`), así que caía a `/app` **incluso en local**. Y `_agent_path()`
buscaba en la raíz y en `agents/`, cuando los agentes canónicos están en `agents/`.
Resultado: `_get_agent()` devolvía `None` para los 6 agentes → 18 tests en rojo.

**Fix:** marcadores múltiples para `REPO_ROOT` + `_AGENT_SUBDIRS = ("aig/agents", "agents", "scripts/agents")`.

---

## 5. Pérdida real de contenido (restaurada)

`scripts/deploy.sh` original (46 líneas) era el script de **Termux**, con una guardia
de seguridad contra `pkill -9 -f python3` y `git push --force` a `main`.

El refactor lo **sobrescribió** con un fichero homónimo distinto (el desplegador de los 21
engines). Búsqueda por contenido en todo el árbol: **no existía en ningún sitio**.

**Restaurado como `scripts/deploy/deploy_termux.sh`**, contenido verificado idéntico a
`HEAD:scripts/deploy.sh`.

> **Lección:** la reubicación por nombre de fichero colisionó dos ficheros distintos que
> compartían basename. Revisar colisiones de nombre al reubicar.

---

## 6. Cambios aplicados

### CI (5 workflows)
- Rutas actualizadas a `scripts/core/ci_health_gate.py` y `scripts/deploy/deploy_prod.sh`
  (`ci.yml`, `ci-21.yml`, `cd.yml`, `cd-21.yml`, `auto-deploy.yml`).
- `cd-21.yml`: eliminada la publicación de `frontend-optimization` (directorio inexistente);
  quitado `frontend_v1` del health-gate.
- `ci-21.yml`: los 6 shards pasan de **lista plana de ficheros** (todos eran rutas muertas) a
  **directorios**. Verificado programáticamente: cobertura total y disjunta de los 7 subdirs.
- Los 5 YAML validados con `yaml.safe_load`.

### Tests (19 ficheros)
Corrección off-by-one de rutas en `tests/{agents,core,daniela,integration,pixel,security}/`.

### `tests/conftest.py`
Añadido `core/` a `sys.path`: los shims internos hacen `from model_router import get_instance`
y `model_router.py` se movió a `core/`.

### Tests reescritos **conservando su intención**
| Fichero | Intención original | Cómo se conserva |
|---|---|---|
| `test_agent_consolidation.py` | "una copia por agente" | Ahora verifica copia canónica en `agents/` y **ninguna** en raíz ni `agents/` |
| `test_swarm_consolidation.py` | idem para el swarm | Rutas nuevas + `swarm_planner.py` en `scripts/agents/` |
| `test_deploy_honesto.py` | honestidad del despliegue | Rutas nuevas; el dry-run vuelve a pasar |
| `test_anti_stub.py` | el cerebro no puede ser un stub | Carga el core por ruta con candidatas |

---

## 7. Worktree roto

- `git worktree prune -v` ejecutado → el repo principal **ya no lo registra**
  (`git worktree list` solo muestra `C:/Users/Alejandro/aig`).
- **Backup completo previo:** `archives/worktree-backup-2026-09-20.tar.gz` (151 MB).
- Verificado que su contenido es la versión **dañada** (`safe_exec.py` 125 B frente a 206 B
  del bueno), sin commits propios ni trabajo único.
- **Pendiente:** la carpeta `C:\Users\Alejandro\worktrees\aig` (195 MB) sigue en disco.
  No se pudo borrar porque la política de seguridad bloquea `Add-Type` y
  `New-Object -ComObject Shell.Application` (las dos vías a la Papelera de reciclaje).

---

## 8. Estado final

```
$ ./.venv/Scripts/python.exe -m pytest tests/ -m "not network and not android"
1028 passed, 23 skipped, 3 deselected
```

| Métrica | Antes | Después |
|---|---|---|
| Errores de colección | 14 | **0** |
| Tests coleccionados | 751 | **1061** |
| Fallos | 48 | **0** |

---

## 9. Absorción del frontend: ya estaba terminada

El pendiente del 19-09 quedó resuelto dentro del propio refactor. Verificado el 2026-09-20:

| Comprobación | Resultado |
|---|---|
| Choque con el módulo `code` de la stdlib | **Resuelto** — los imports son relativos (`from .code.code_splitting import split_bp`) |
| `import frontend` | **OK** — 24 blueprints |
| `frontend.register_frontend(app)` | **OK** — **54 rutas** registradas (`/api/frontend/...`) |
| Aserciones `modules == 107` | **Resueltas** — ahora son `>= 107` (correctamente laxas), en `test_daniela2.py:23,266` y `test_daniela_ai.py:68` |
| Registro en el servidor | `daniela-os/server.py:92` → `("frontend", lambda: __import__("frontend").register_frontend(app))` |
| Estado reportado | `modules: 131`, `total_systems: 138` |
| Servicio `frontend` standalone | **Eliminado** de `config/docker-compose.yml` (0 referencias); los servicios restantes son daniela, hermes, infra, agent, security, perf, redis, nginx, prometheus, grafana |
| Tests de Daniela | **77 passed**, 7 skipped |

Los 9 ficheros estáticos del frontend (`app.js`, `index.html`, `sw.js`, `workspace.html`,
`ui_tests.js`, `metaverse_server.js`, `index_master_*.html`) también fueron reubicados de la
raíz a `frontend/`, con contenido **idéntico** al de HEAD.

---

## 10. Segunda pasada (2026-09-20, tarde) — hallazgos nuevos

### 10.1 🔴 P0 NUEVO: `.gitignore` borrado + 8 ficheros con credenciales expuestas

**El refactor borró `.gitignore`** (estaba trackeado, `HEAD:.gitignore`, 229 líneas).
Efecto inmediato medido: los ficheros sin trackear saltaron de ~53 a **130**, porque
git dejó de ignorar basura y —más grave— **secretos**:

| Fichero (untracked, con claves vivas) |
|---|
| `config/.env.bak-2026-09-14` |
| `config/.env.env.bak-opcionB-20260917_213329` |
| `config/env/.env.master` |
| `config/env/.env.master.bak-pre-redaccion-2026-09-14` |
| `data/tunnel_guard/backups/.env.20260910_175107.bak` |
| `data/tunnel_guard/backups/.env.20260910_175107.bak.bak-pre-redaccion-2026-09-14` |
| `external-assets/DanielaCloud/Obsidian_Backup/2026-09-10.md` |
| `external-assets/DanielaCloud/Obsidian_Backup/2026-09-10.md.bak-pre-redaccion` |

Con `.gitignore` ausente, un `git add .` los habría **metido en el historial de GitHub**.

**Acción tomada:** restaurado `git show HEAD:.gitignore > .gitignore`. Verificado con
`git check-ignore` que los 8 ficheros + `.env` quedan ignorados. Sin trackear: 130 → 53.

### 10.2 🔴 P1: referencias a `Dockerfile.base` rotas por la reubicación a `config/`

`Dockerfile.base`, `.flake8`, `.dockerignore`, `.pre-commit-config.yaml` se movieron a
`config/`, pero **11 referencias seguían apuntando a la raíz**, incluida la construcción
de la imagen base que usan CI y ambos scripts de deploy. Efecto: el build base se saltaba
en silencio (`|| echo warning`).

**Acción tomada:** corregidas las 11 referencias en `ci.yml`, `ci-21.yml`, `cd.yml`,
`cd-21.yml`, `scripts/deploy/deploy.sh`, `scripts/deploy/deploy.ps1`. YAML validado (5/5 OK).

### 10.3 ✅ `.devcontainer/devcontainer.json` restaurado

Se había perdido por completo (no existía en ningún sitio del árbol). Recuperado de `HEAD`.

### 10.4 Suite completa re-verificada

`1028 passed, 23 skipped, 3 deselected` — sin regresiones tras todos los arreglos de esta pasada.

---

## 11. Tercera pasada — consolidación del árbol (commit `955c18ba`)

El árbol llevaba **554 borrados + 60 modificados + 52 sin trackear** sin consolidar, lo que
hacía imposible distinguir cambio intencionado de daño. Se ha commiteado todo en un solo
commit de recuperación: **655 ficheros, +23.904 / −16.314 líneas**. Árbol de trabajo limpio.

### 13.1 🔴 P0 NUEVO: `archives/` (2.8 GB) NO estaba ignorado

Peor que el `.gitignore` ausente: `archives/` **nunca estuvo en la lista de ignorados** y
contiene:

- `archives/credentials.json` (credenciales de Google)
- `archives/.env.bak-consolidacion-20260917`
- `archives/.env.env.bak-envclean-20260915_003151`
- `archives/.env.supabase-2026-09-14.bak`

Un `git add .` los habría publicado. **Añadidas reglas** para `archives/`, `backups/`,
formatos comprimidos, `.env.*`, `credentials.json`, `*.db` y logs de runtime.

### 13.2 🔴 P0 NUEVO: el pre-commit hook estaba ROTO

`.githooks/pre-commit` (activo vía `core.hooksPath=.githooks`) invocaba
`python scripts/secret_guard.py` — ruta que el refactor movió a `scripts/utils/`.
Resultado: el hook **bloqueaba TODOS los commits** con `no such file or directory`.

Efecto perverso: el guardián anti-secretos llevaba roto desde el refactor. Se ha reparado
con detección de ambas rutas y `fail-closed` explícito. Verificado ejecutándolo: exit 0.

### 13.3 Verificación post-commit

| Comprobación | Resultado |
|---|---|
| `.env*` en el commit | **0 ficheros** |
| `archives/` en el commit | **0 ficheros** |
| `credentials*.json` en el commit | **0 ficheros** |
| Claves vivas en el árbol commiteado (`git grep`) | **0 coincidencias** |
| Suite completa | **1028 passed** |

---

## 12. Cuarta pasada — red de seguridad estructural (commit `50503fbf`)

### 12.1 El patrón de fondo

Los cuatro fallos de esta auditoría tienen **una sola causa raíz**: mover ficheros
sin actualizar quien los referencia. La suite de 1028 tests estaba en verde durante
todo el proceso porque **medía comportamiento, no estructura**.

Hueco identificado: ningún test verificaba que las rutas citadas en workflows,
hooks y scripts existiesen realmente.

### 12.2 Nuevo `tests/core/test_referencias_integridad.py` (39 casos)

| Categoría | Qué valida |
|---|---|
| Workflows | Cada ruta citada en `.github/workflows/*.yml` existe |
| Hooks | Cada `python X.py` de `.githooks/pre-commit` existe |
| Deploy | Rutas de `scripts/deploy/*.sh|ps1` (excluye ramas `else` de fallback) |
| Ficheros críticos | `.gitignore`, `conftest.py`, `ci_health_gate.py` presentes |
| Secretos | Reglas de `.gitignore` intactas; ningún `.env` trackeado |

No ejecuta nada, no levanta servidores, no necesita red. Su valor es fallar el día
que alguien mueva algo y olvide una referencia.

### 12.3 12 referencias rotas MÁS que el test destapó

| Ruta | Refs | Dónde vive | Impacto real |
|---|---|---|---|
| `docker-compose.yml` | **8** | `config/` | **Fallo duro** en cada job de CI y CD |
| `requirements.txt` | **3** | `config/` | **Fallo silencioso**: el guard `if [ -f ]` lo ocultaba y **no se instalaban dependencias** |
| `scripts/ci_health_gate.py` | 1 | `scripts/core/` | Rama `else` muerta de `deploy_prod.sh` |

Los dos primeros son más graves que los que ya había corregido antes: el de
`docker-compose.yml` rompía CI/CD en cada ejecución, y el de `requirements.txt`
era invisible porque el propio guard lo silenciaba.

**Acción:** 12 referencias corregidas. En `deploy_prod.sh` se añade además una
validación explícita que aborta con mensaje claro si la ruta resuelta no existe,
en lugar de fallar a mitad del deploy.

### 12.4 Verificación por sabotaje

Un test que solo pasa no demuestra nada. Se verificó revirtiendo cada arreglo:

| Sabotaje | Resultado |
|---|---|
| Quitar `archives/` de `.gitignore` | ❌ Falla correctamente |
| Revertir `Dockerfile.base` a la raíz | ❌ Falla correctamente |
| Hook apuntando a ruta inexistente | ❌ Falla correctamente |

### 12.5 Estado final

**1067 passed, 23 skipped, 0 fallos.** El shard `core-security` de CI ya cubre
`tests/core`, así que el nuevo test se ejecuta en cada push sin cambios de config.

---

## 13. Quinta pasada — automatización de seguridad y salud del sistema

### 12.1 Dependabot + CodeQL (commit `87052739`)

El repo no tenía **ningún** escaneo automático. Los P0 de credenciales se detectaron
a mano leyendo el historial de git, no por una herramienta.

**Dependabot** — 11 entradas, con agrupación de minor+patch. Sin agrupar, 16
manifiestos generan decenas de PRs semanales que nadie revisa. Los `MAJOR` van
sueltos porque merecen revisión individual. `tencent-suite/` y `decentraland/`
quedan fuera: son dependencias upstream que no mantenemos.

**CodeQL** — analiza python y javascript-typescript con `security-and-quality`.
Corre también **semanalmente**, porque las reglas se actualizan: código limpio hoy
puede aparecer como vulnerable la semana que viene.

Los 3 tests nuevos de Dependabot cazaron un error mío inmediatamente: había puesto
una entrada `pip: /` cuando en la raíz no hay `requirements.txt` ni `pyproject.toml`.
Dependabot habría ignorado esa entrada **en silencio**.

### 12.2 `/health` real + `/health/ready` (commit `60edb8d1`)

`GET /health` devolvía:

```json
{"gateway": "healthy", "core": "online", "timestamp": "..."}
```

Comprobaba **un booleano**. Un disco al 99%, memoria saturada o scheduler roto daban
la misma respuesta que un sistema sano. El refactor lo demostró: el scheduler dejó de
encontrar agentes y 18 tests fallaban, pero `/health` seguía diciendo `"healthy"`.

Ahora consulta 4 subsistemas y distingue liveness (`/health`, siempre 200) de
readiness (`/health/ready`, 503 si algo crítico cae) — convención Kubernetes, para
que el balanceador actúe sin provocar reinicios en cascada.

**Bug encontrado durante la implementación:** usé `parents[2]` desde
`core/health_checks.py`, que apunta a `C:\Users\Alejandro`. El chequeo reportaba
`.gitignore` como ausente **con el fichero delante**. Es el mismo error de
desplazamiento que causó el refactor. Sustituido por `_raiz_repo()`, que busca un
marcador (`.git`, `tests/conftest.py`) y es inmune a la profundidad.

### 12.3 🔴 HALLAZGO MAYOR: 64.631 líneas de código duplicado (commit `89c2ec83`)

Al editar `scripts/core/api_gateway.py` y comprobar que **el cambio no tenía efecto**,
descubrí la causa: el proyecto importa `core/api_gateway.py`. Las dos copias son
implementaciones completas de ~1000 líneas.

Ese caso no es aislado. Medido con hash SHA-256:

| Métrica | Valor |
|---|---|
| Grupos de ficheros `.py` idénticos | **240** |
| Grupos con ≥100 líneas por fichero | **111** |
| Líneas duplicadas en ficheros ≥100 líneas | **64.631** |
| Gemelos de `core/` fuera de `core/` | **177** |

**Por qué es peligroso y no solo feo:** la duplicación es una trampa activa.

1. Editas el fichero equivocado y el cambio no surte efecto *(comprobado hoy)*
2. Arreglas un bug en una copia y las otras siguen vulnerables
3. Un test pasa porque importa la copia buena, mientras producción usa la mala

El caso 3 es el peor: da sensación de estar cubierto sin estarlo.

**Acciones:**

- `scripts/utils/detector_duplicados.py` — encuentra grupos idénticos, ordena por
  líneas desperdiciadas (`líneas × (copias−1)`), filtra `__init__.py` (existen por
  definición del lenguaje) y no borra nada: reporta.
- Eliminado `scripts/core/api_gateway.py`, verificado que **nadie lo importa**. Su
  única diferencia era un comentario útil, que se preserva en `core/`.
- Tests con **presupuesto decreciente** en lugar de exigir cero: consolidar ~180
  gemelos de golpe rompe imports y el riesgo supera al de convivir con ellos. Lo
  inaceptable es que crezca.

### 12.4 Estado final de la quinta pasada

**1097 passed, 23 skipped, 0 fallos.** Sabotaje verificado en cada test nuevo.

---

## 14. Pendiente / recomendaciones

### Hecho ✅
1. ~~Commitear el refactor~~ → commit `955c18ba` (655 ficheros). Árbol limpio.
2. ~~Los 9 ficheros estáticos del frontend~~ → incluidos en ese commit.
3. ~~Referencias rotas en CI~~ → 24 corregidas (12 en la 4ª pasada, 12 más en la 5ª).
4. ~~Red de seguridad estructural~~ → `test_referencias_integridad.py` (56 casos).
5. ~~Escaneo automático~~ → Dependabot + CodeQL.
6. ~~`/health` que miente~~ → consulta 4 subsistemas + readiness probe.

### Bloqueante (solo puede hacerlo el usuario) 🔴
7. **Rotar las credenciales.** `GEMINI_API_KEY`, `DANIELA_PIN`, `OPENROUTER_API_KEY`
   y la `AQ.…` pegada en el chat. Siguen recuperables del historial. Ver sección 15.

### Siguiente
8. **Push a `origin`.** Hay 8 commits de recuperación solo en local. `origin/HEAD`
   apunta a `main`, no a `universo-v1`: quien clone el repo no ve nada de este trabajo.
9. **Verificar CI en GitHub Actions.** La cuota estaba agotada y los jobs en rojo tenían
   `steps=0` y `runner=null`: no llegaron a ejecutarse. Todo está verificado en local
   (1097 passed) pero **nada en CI todavía**.
10. **Borrar a mano** `C:\Users\Alejandro\worktrees\aig` (195 MB; backup en `archives/`).
11. **Consolidar duplicación de forma gradual.** 177 gemelos de `core/` fuera de `core/`.
    Un módulo por commit: verificar con `grep -rn "import <módulo>"` que nadie usa la
    copia, borrarla, ejecutar la suite, bajar el presupuesto del test.

### Reglas permanentes
12. Al reubicar ficheros, revisar: (a) colisiones de basename, (b) cálculos de ruta
    relativos al propio fichero, (c) referencias en CI y scripts, (d) config ocultos
    (`.gitignore`, `.dockerignore`, `.flake8`, `.devcontainer/`), (e) el pre-commit hook.
13. Antes de editar un fichero, comprobar que no tenga gemelo:
    `python scripts/utils/detector_duplicados.py`. Editar la copia equivocada produce
    tests verdes y cambios inertes.

### Observación del sistema (real, medida hoy)
14. **Memoria al 93% (1.07 GB libres).** Detectado por el nuevo chequeo de `/health`.
    No es un fallo del repo, pero conviene saberlo antes de levantar más servicios.

---

## 15. Credenciales comprometidas — plan de rotación y purga

**Confirmado:** `.env` estuvo trackeado y sigue recuperable en el historial
(`git show <commit>:.env`). Remoto: `https://github.com/aig/AIGESTION-MONOREPO.git`.

| Variable | Commits donde aparece |
|---|---|
| `GEMINI_API_KEY` | `7f3ecd2c`, `d67722ef`, `f598ea51` |
| `DANIELA_PIN` | `d67722ef`, `f598ea51` |
| `OPENROUTER_API_KEY` (`sk-or-v1-…`) | `a1c59314` |

**Orden correcto de actuación (importante):**

1. **Rotar primero** las tres claves en sus proveedores. Purgar el historial sin rotar no
   sirve de nada: quien ya clonó el repo conserva los valores.
2. Limpiar el `.env` local de los valores muertos. La clave `AQ.…` pegada en el chat debe
   considerarse **comprometida y revocada**.
3. **Purgar el historial** con `git filter-repo --path .env --invert-paths` (+ `--replace-text`
   para los valores), con backup previo del repo completo.
4. `git push --force` coordinado — rompe clones existentes; avisar a cualquiera que tenga fork.

Esta operación es destructiva sobre la historia. No ejecutar sin (1) hecho y sin backup.
