# Auditoría de la raíz — 2026-09-25

Auditoría **de solo lectura**: no se modificó ningún fichero del proyecto.
Todo lo que sigue está medido en esta máquina, con el comando que se indica,
para que se pueda reproducir. Donde algo no se pudo comprobar, se dice.

---

## 0. Resumen

El sistema **funciona**: 12 contenedores en `healthy`, Daniela sirve **451 rutas**
con `failed_phases: []`, y la suite de tests pasa **completa (1204 tests, 0 fallos)**.

El problema no es el código. Es que **las puertas que vigilan ese código están
rotas o son decorativas**, y hay **1470 ficheros sin commitear** que mezclan
formateo, autofixes y ediciones reales.

| Puerta | Estado real |
|---|---|
| CI (`.github/workflows/ci.yml`) | **ROTA** — no instala, no testea, el lint es vacuo |
| Ratchet de ruff | **NO CUADRA** — baseline 0, la realidad da 33 |
| Ratchet como automatización | **NO EXISTE** — nada lee el baseline |
| Pre-commit | **DESALINEADO** — ruff 0.4.10 en el hook, 0.16.7 en el venv |
| Tests | ✅ verdes, 1204 pasan |
| Despliegue | ⚠️ en marcha pero **no corresponde** al compose actual |
| `docs/CODE-REVIEW.md` §7 | ❌ contradice al repo |

---

## 1. Lo que está bien (verificado, no asumido)

- **Stack**: 12 contenedores `Up (healthy)` — daniela, hermes, infra, agent,
  security, perf, gods-eye, grafana, redis, caddy, prometheus, orchestrator.
- **Daniela**: `curl -s --noproxy '*' localhost:9200/api/status` →
  `routes: 451`, `failed_phases: []`, `status: alive`, `modules: 107`.
  Coincide exactamente con la expectativa registrada en `MEMORY.md`.
- **Tests**: `pytest tests/ -q` → **1204 tests, 0 fallos, 3 skip, 2 xfail**.
  Los dos `F` que aparecen en `test_out.txt` (salida del 14:53) eran
  `PermissionError: [WinError 5]` sobre el directorio temporal de pytest —
  fallo de entorno, no de código. Ya no reproducen.
- **Integridad de plugins**: los 14 `sha256` del `ALLOWLIST` de
  `plugins/registry.py` **cuadran** con los payloads en disco, pese a que el
  formateo los modificó. Verificado con el propio `registry.repin()`:
  `pins que NO cuadran: 0`.
- `node_modules/` está correctamente ignorado por `.gitignore:25`.

---

## 2. P0 — La CI no verifica nada

`.github/workflows/ci.yml` declara, para **todos** los pasos:

```yaml
defaults:
  run:
    shell: pwsh
    working-directory: config
```

`actions/checkout` deja el repo en la raíz del workspace, así que cada `run`
se ejecuta en `<repo>/config/`. Consecuencias, una por paso:

1. **`pip install -e ".[dev]"`** → resuelve `config/pyproject.toml`, que declara
   `build-backend = "setuptools.backends._legacy:_Backend"`. Ese módulo
   **no existe**:

   ```
   setuptools 79.0.1
   FALLA setuptools.backends._legacy -> ModuleNotFoundError No module named 'setuptools.backends'
   OK    setuptools.build_meta
   ```

   El paso de instalación falla. El backend correcto es `setuptools.build_meta`
   (el que usan la raíz y `shared/`).

2. **`python -m pytest tests/`** → `config/pyproject.toml` tiene
   `testpaths = ["tests"]`, que resuelve a `config/tests`. **No existe**
   (`ls: cannot access 'config/tests'`). Los tests nunca corren en CI.

3. **`python -m ruff check .`** → lintea el contenido de `config/`, que son
   JSON, Caddyfiles y Dockerfiles. La puerta de lint es **vacua**.

4. El mismo `working-directory: config` en **`cd.yml` sí es correcto**: el
   compose vive en `config/` y Compose resuelve `.env` respecto a su propio
   directorio. Por eso **no se puede quitar en bloque**: hay que separar los
   dos workflows, o hacer el `ci.yml` explícito con `working-directory: .`.

> Nota: el repo arrastra este patrón de tres `pyproject.toml`
> (raíz, `config/`, `shared/`) y solo uno de ellos tiene un `build-backend`
> válido. Es la misma familia de problema que el `parents[N]`: **dos sitios
> que dicen ser "el" proyecto**.

---

## 3. P0 — El ratchet de calidad no cuadra

`.quality-baseline/ruff-count.txt` termina en **`0`**.
La realidad, medida ahora:

```
$ ruff check .
Found 33 errors.          # todos BLE001/S110 en shared/aig_shared/
```

Reparto: `shared/aig_shared/ai/cache.py` (11), `ai/service.py` (7),
`events/__init__.py` (5), `ai/connector.py` (5), `ai/serving.py` (4),
`auth/__init__.py` (1).

### Causa raíz (medida)

`shared/pyproject.toml` **es un fichero de configuración de ruff** (tiene
`[tool.ruff]`) y **sombra** la configuración de la raíz para todo lo que cuelga
de `shared/`. No declara `lint.ignore`, así que los `ignore` de la raíz
(`BLE001`, `S110`, …) **no llegan**.

```
$ ruff check shared/aig_shared/ai/cache.py --show-settings | head -2
Resolved settings for: "...\shared\aig_shared\ai\cache.py"
Settings path: "C:\Users\Alejandro\aig\shared\pyproject.toml"     <-- el sombra

$ ruff check shared/ --config pyproject.toml
All checks passed!                                                <-- config raíz
```

La CI llega a 0 **solo** porque pasa los ignores por línea de comandos:
`ruff check . --ignore=BLE001 --ignore=S110 --ignore=UP017`.
Es decir: **el baseline no es reproducible con el comando que documenta
`docs/CODE-REVIEW.md` §7.** Cualquiera que ejecute `ruff check .` a mano ve
33 > 0 y cree que ha roto algo.

### Y el ratchet no lo lee nadie

```
$ grep -rn 'ruff-count' .            # excluyendo node_modules
docs/CODE-REVIEW.md                  # única aparición
```

No hay script, hook, ni workflow que lea `.quality-baseline/ruff-count.txt`.
El ratchet es **documentación**, no automatización. Nada impide subirlo.

---

## 4. P1 — El changeset sin commitear: 1470 ficheros

```
1470 files changed, 56228 insertions(+), 29079 deletions(-)
```

### Cuánto es forma y cuánto es fondo

Método: se extrajo `git archive HEAD` a un directorio temporal y se comparó el
**AST** de cada `.py` modificado contra su versión en HEAD. Un AST idéntico
significa que el fichero solo cambió de forma.

| Categoría | Ficheros |
|---|---|
| `.py` modificados | 1433 |
| **AST idéntico** (puro formateo) | **1269** |
| AST distinto | 163 |
| — solo docstrings | 6 |
| — solo imports (autofix) | 10 |
| — **resto** | **147** |

Los 147 con AST distinto contienen **autofixes seguros y ediciones reales
mezclados**. Dos ejemplos verificados:

- `core/location.py` → `{f for f in cls.__dataclass_fields__}` se convirtió en
  `set(cls.__dataclass_fields__)`. Autofix `C4`, equivalente.
- `plugins/registry.py` → **cambian valores `sha256` del `ALLOWLIST`**. Eso es
  una edición real de contenido de seguridad (correcta: los payloads cambiaron
  con el formateo, y el `repin()` confirma que cuadran).

Un comparador automático **no puede** distinguir "autofix equivalente" de
"edición real". Esos 147 ficheros necesitan ojos humanos, y hoy van en el mismo
saco que 1269 ficheros de reflujo de líneas.

`docs/CODE-REVIEW.md` §5 clasifica >1000 líneas como **XL → "Split, unless
mechanical"**. Aquí es mecánico en un 88% y no mecánico en el resto: hay que
partirlo, no justificarlo en bloque.

### P1 — Dos versiones de ruff

| Sitio | Versión |
|---|---|
| `.pre-commit-config.yaml` (`ruff-pre-commit`) | **v0.4.10** |
| `.venv` | **0.16.7** |

Dos formateadores distintos. Consecuencia medida:

```
$ ruff format --check .
164 files would be reformatted, 1172 files already formatted
```

Pese al pase masivo, quedan **164 ficheros sin formatear**. Y con el hook en
0.4.10, cualquier `git commit` puede **deshacer** el trabajo de 0.16.7. Esta es
la explicación más probable de por qué el changeset es tan grande y no termina
de cerrarse.

---

## 5. P1 — `docs/CODE-REVIEW.md` §7 contradice al repo

El documento afirma:

> 2026-09-23: GitHub Actions OFF by owner decision (zero billing).
> `.github/workflows/` is empty

Realidad en disco:

```
.github/workflows/ci.yml   2026-09-25 15:34
.github/workflows/cd.yml   2026-09-25 15:36
```

Ambos **sin trackear**. O se decidió re-activar Actions, o se dejaron
preparados y la doc no se enteró. El §7 también cita el baseline como
`10565` cuando el fichero dice `0`. La documentación de procesos está mintiendo
en los dos números que más importan.

---

## 6. P1 — Deriva de despliegue

| Evento | Momento |
|---|---|
| Imágenes construidas | 2026-09-25 **14:53–14:55** |
| Contenedores arrancados | 2026-09-25 **15:07–15:12** |
| `config/docker-compose.yml` modificado | 2026-09-25 **16:12** |

El compose cambió **una hora después** de levantar el stack. El stack en marcha
**no corresponde** al fichero en disco.

Lo tranquilizador: los ficheros fuente clave son *anteriores* a las imágenes
(`ia-services/hermes/server.py` 09-24 22:01, `core/api_gateway.py` 09-24 22:21),
así que el código desplegado sí los incluye. Lo que no se puede afirmar es que
la *configuración* en marcha sea la del compose actual.

---

## 7. P2 — Riesgos concretos

### 7.0 El framework de pre-commit nunca corre

`git config core.hooksPath` = `.githooks`, y el único hook presente es
`.githooks/pre-commit`, que **solo** llama a `scripts/utils/secret_guard.py`.
Dos consecuencias medidas el 2026-09-25:

```
$ python -m pre_commit --version
No module named pre_commit          # el framework no esta instalado
$ ls .git/hooks/pre-commit
No such file or directory
```

1. **`.pre-commit-config.yaml` es decorativo.** Declara `ruff --fix`,
   `ruff-format`, gitleaks, `trailing-whitespace`, `end-of-file-fixer`… y
   **ninguno se ejecuta**, porque el framework que los leería no está instalado
   ni enganchado. `docs/CODE-REVIEW.md` §7 los presenta como puertas
   **bloqueantes**. No lo son.

2. Lo que sí corre es el `secret_guard` (494 líneas, 12 patrones, stdlib puro), y
   funciona: es **fail-closed** (si no encuentra el script, bloquea todos los
   commits) y en staging no detecta secretos. Esa parte está bien.

Consecuencia práctica: hasta hoy, el único trabajo de lint/format que ocurría
antes de un commit dependía de que alguien lo lanzara a mano. Es la otra mitad
de por qué el changeset de 1470 ficheros podía acumularse sin que nada se
quejara. Para cerrarlo: `pip install pre-commit && pre-commit install`, o mover
ruff al `.githooks/pre-commit` (que ya funciona) en lugar de depender del
framework.

### 7.1 Una copia de seguridad viaja dentro del contenedor

`ia-services/hermes/integration/backup_gateway_20260924_191838/` contiene
`__init__.py` y **3 módulos duplicados**: `voice_engine.py`,
`shared_memory_sync.py`, `hermes_daniela_bridge.py`.

El `Dockerfile` de hermes hace `COPY ./ia-services/hermes/ .`, así que entra en
la imagen. Verificado en el contenedor vivo:

```
$ docker exec aig-hermes ls /app/integration/
backup_gateway_20260924_191838   daniela_gateway.py   voice_engine.py
shared_memory_sync.py            hermes_daniela_bridge.py   ...
```

Es un **subpaquete importable con módulos homónimos de los reales**. Exactamente
el patrón de "divergencia silenciosa" que describe `MEMORY.md`: dos copias del
mismo nombre importable, sin error, con la que gane según el orden de `sys.path`.

### 7.2 Ruta muerta en Caddy

`config/Caddyfile` — el que monta el contenedor `aig-caddy` (verificado:
`C:\Users\Alejandro\aig\config\Caddyfile -> /etc/caddy/Caddyfile`) — declara
`handle_path /secure/*` **dos veces**:

```
línea 26:  handle_path /secure/* { reverse_proxy localhost:9880 }   # secure_engine
línea 53:  handle_path /secure/* { reverse_proxy localhost:9999 }   # sec-opt
```

Los `handle_path` de un mismo site block son **mutuamente excluyentes**: gana el
primero. El de 9999 queda **inalcanzable, sin error y sin aviso**. Caddy arranca
`healthy` y no dice nada.

Además hay un `Caddyfile` en la **raíz, idéntico** a `config/Caddyfile`
(`diff -q` sin salida). Duplicado sin trackear; el contenedor usa el de `config/`.

### 7.3 Basura y ruido local

| Elemento | Tamaño / estado |
|---|---|
| `service_stderr.log` | **11 MB**, sin rotar, banner de Flask repetido cientos de veces (proceso reiniciándose en 8080) |
| `test_out.txt`, `test_final2.txt` | idénticos entre sí; salida de tests del 14:31 y 14:53 |
| `audit_daniela_hermes_20260924_190728/` | 586 KB de salida de auditoría |
| `.coverage`, `aig.egg-info/` | residuos |
| `node_modules/` | 73 MB en la raíz (sí ignorado por git) |

El banco TS de la raíz (`package.json`, `tsconfig.json`, `index.ts`, `stream.ts`,
`tools.ts`) usa `ai` + `@ai-sdk/google` y lee `.env`/`.env.local` para claves de
Gemini. Es un banco de pruebas, no forma parte del producto, y **no está
trackeado**. Su `npm test` es `exit 1`.

### 7.4 Endpoint fantasma

`/api/cross/status` → **404** hoy a las 16:14 y a las 16:46 (en
`service_stderr.log`). Alguien o algo lo espera.

### 7.5 Memoria del proyecto desactualizada

`.workbuddy-ai/memory/` se corta en `2026-09-22.md`. Todo el trabajo del 23, 24
y 25 — el ratchet completo, el subsistema de integración de hermes, la CI, Caddy
— **no está registrado**. La siguiente sesión arrancará sin ese contexto.

---

## 8. Siguientes pasos

### Bloque 0 — No commitear los 1470 ficheros tal cual

1. **Partir el changeset en cuatro commits**, usando el AST como criterio de corte:
   - **A** — `ruff format` puro: los 1269 con AST idéntico.
   - **B** — autofixes: los 163 con AST distinto pero sin edición manual
     (revisar los 147 uno a uno; `plugins/registry.py` va aquí).
   - **C** — subsistema nuevo: `ia-services/hermes/integration/*.py` sin trackear.
   - **D** — tooling: `.github/workflows/`, `Caddyfile`, banco TS.
   Sin esto, la revisión de §2–§4 es imposible y cualquier regresión queda
   enterrada entre 29 000 líneas borradas.

### Bloque 1 — Reparar las puertas (P0)

2. **`shared/pyproject.toml`**: quitar su `[tool.ruff]` para que herede de la
   raíz, o añadir el mismo `ignore`. Criterio de aceptación:
   `ruff check .` debe dar **0 sin ningún flag**.
3. **`config/pyproject.toml`**: `build-backend = "setuptools.build_meta"`.
4. **`ci.yml`**: quitar `working-directory: config` (dejar `pwsh`). Mantenerlo
   solo en `cd.yml`. Verificar que el paso de tests realmente recolecta **1204**.
5. **Unificar ruff**: subir `ruff-pre-commit` a `v0.16.7` (o bajar el venv) y
   después `ruff format .` **una vez**, en su propio commit. Los 164 pendientes
   deben bajar a 0.
6. **Hacer real el ratchet**: un script que lea `.quality-baseline/ruff-count.txt`
   y falle si el conteo sube. Hoy nada lo lee; el número se mantiene a mano.

### Bloque 2 — Limpieza y despliegue (P1/P2)

7. **Actualizar `docs/CODE-REVIEW.md` §7**: Actions ON/OFF y el número del
   baseline. Hoy contradice al repo en ambos.
8. **Sacar `backup_gateway_20260924_191838/`** de `ia-services/hermes/integration/`,
   añadir regla a `.dockerignore` y **reconstruir hermes**.
9. **Caddy**: eliminar el `handle_path /secure/*` duplicado (decidir cuál es el
   upstream correcto: 9880 o 9999) y borrar el `Caddyfile` de la raíz.
10. **Redesplegar**: el compose cambió después del arranque.
    `scripts/deploy/compose.sh up -d` y re-verificar `routes: 451` y
    `failed_phases: []`.
11. **Borrar residuos**: `test_out.txt`, `test_final2.txt`, `.coverage`,
    `audit_daniela_hermes_20260924_190728/`, `aig.egg-info/`.
    Decidir qué hacer con el banco TS (moverlo fuera o trackearlo con
    `node_modules` ya ignorado). Rotar `service_stderr.log`.
12. **Resolver `/api/cross/status`**: implementarlo o dejar de sondearlo.

### Bloque 3 — Cerrar el círculo

13. **Actualizar la memoria** del proyecto (23, 24, 25) y enlazar esta auditoría
    desde `docs/INDEX.md`.
14. **Añadir una guardia de regresión** para lo de §3: un test que ejecute
    `ruff check .` **sin flags** y exija 0. Es el único modo de que el sombra de
    `shared/pyproject.toml` no vuelva. Y verificarla **por mutación**: volver a
    meter el `[tool.ruff]` y comprobar que el test se pone rojo.

---

## Anexo — Cómo se separaron forma y fondo

El clasificador del §4 (comparar AST contra HEAD, ignorando docstrings e
imports). No modifica nada; solo lee.

```python
import ast, os, subprocess

REPO = r"C:\Users\Alejandro\aig"
HEAD = r"C:\...\aig_head"  # git archive HEAD | tar -x -C HEAD


class QuitaDocstrings(ast.NodeTransformer):
    def _limpia(self, body):
        if (
            body
            and isinstance(body[0], ast.Expr)
            and isinstance(body[0].value, ast.Constant)
            and isinstance(body[0].value.value, str)
        ):
            return body[1:]
        return body

    def generic_visit(self, node):
        for field in ("body", "orelse", "finalbody"):
            cuerpo = getattr(node, field, None)
            if isinstance(cuerpo, list) and cuerpo and isinstance(cuerpo[0], ast.stmt):
                setattr(node, field, self._limpia(cuerpo))
        return super().generic_visit(node)


def _norm(path, quita_doc, quita_imports):
    tree = ast.parse(open(path, "rb").read())
    if quita_doc:
        tree = QuitaDocstrings().visit(tree)
    if quita_imports:
        for node in ast.walk(tree):
            for field in ("body", "orelse", "finalbody"):
                cuerpo = getattr(node, field, None)
                if isinstance(cuerpo, list):
                    setattr(
                        node,
                        field,
                        [s for s in cuerpo if not isinstance(s, (ast.Import, ast.ImportFrom))],
                    )
    return ast.dump(tree, include_attributes=False)
```

Regla de decisión por fichero:

| Comparación | Veredicto |
|---|---|
| `_norm(a, F, F) == _norm(b, F, F)` | puro formateo → commit A |
| igual con docstrings quitados | solo docstrings |
| igual con imports quitados | solo imports (autofix) |
| distinto incluso así | **revisar a mano** → commit B |
