# Ideas épicas para optimización del código — 2026-09-25

Continuación de `docs/AUDITORIA-2026-09-25.md`. Aquí no hay teoría: cada idea
nace de un número medido en este repo, y cada una dice **qué duele, qué se hace,
cómo se sabe que funcionó y cuál es el riesgo**.

Distinción que gobierna todo el documento:

- **Optimizar** = misma funcionalidad, menos coste (tiempo, bytes, errores).
- **Refactorizar** = misma funcionalidad, mejor estructura.
- **Reescribir** = no es ninguna de las dos. Un stub de 40 líneas **no necesita
  optimización**: necesita borrarse o implementarse. Confundirlas es cómo este
  repo llegó a tener 135 basenames repetidos.

---

## 0. El principio que hace épico el resto

**El sistema no debe poder mentir.**

Este repo ya tiene un caso de éxito con esa forma: `plugins/registry.py::repin()`
existe porque el `sha256` *tiene que* romperse cuando el fichero cambia. Los
hashes del `ALLOWLIST` cuadran hoy (medido), y eso no es suerte: es diseño.

El resto del sistema no funciona así. La CI puede estar roja y nadie se entera
(§2.1). El baseline dice 0 y la realidad dice 33. Caddy arranca `healthy` con una
ruta muerta. Los tests pasan en verde mientras §2.3 duerme.

**Idea épica transversal:** extender el patrón de `repin()` a todo.
*Cada puerta del repo debe fallar en voz alta y temprano, o no es una puerta.*

---

## BLOQUE A — Las puertas (P0, mismos-agujeros-que-sangran)

### ÉPICA A1 · La CI de verdad
**Duele:** `ci.yml` corre con `working-directory: config`. `pytest tests/` busca
`config/tests` (no existe), `ruff check .` lintea JSON, y `pip install -e .` usa
un `build-backend` inexistente. **La CI nunca ha ejecutado un test.**

**Idea:** no "arreglar el YAML", sino hacer que **el fallo sea imposible de
ignorar**. Un paso previo (`smoke`) que verifique las precondiciones y aborte:

```yaml
- name: Precondiciones (aborta ruidosamente)
  working-directory: .
  run: |
    python -c "import tomllib,pathlib; \
      d=tomllib.loads(pathlib.Path('pyproject.toml').read_text()); \
      b=d['build-system']['build-backend']; \
      import importlib,sys; \
      importlib.import_module(b.split(':')[0]) or sys.exit(f'backend roto: {b}')"
    python -c "import pathlib,sys; \
      sys.exit(0 if pathlib.Path('tests').is_dir() else 'tests/ no existe')"
```

**Sabes que funcionó** cuando un commit que rompe deliberadamente `shared/` pone
la CI en rojo. **Riesgo:** ninguno; hoy está en 0.

**Extra épico:** el número de tests recogidos debe ser **assertado** (1204), no
solo ejecutado. Un `pytest --collect-only` que devuelva 300 por un `norecursedirs`
mal puesto es una CI verde con el 75% del repo sin probar. Ese es el fallo
silencioso clásico de este proyecto.

### ÉPICA A2 · El ratchet que se defiende solo
**Duele:** `.quality-baseline/ruff-count.txt` dice `0`; la realidad da `33`.
Y `grep -rn ruff-count` solo encuentra el `.md` — **nada lee el número**.

**Idea:** convertir el ratchet de documentación en automatización con memoria.
El salto épico no es "un script que cuente", es que el **presupuesto de deuda**
sea un objeto de primera clase:

```
.quality-baseline/
  ruff-count.txt       # techo actual: 0
  ruff-por-regla.json  # {"BLE001": 0, "S110": 0, ...}  <- nuevo
  historial.tsv        # fecha, commit, total, por-regla
```

La regla: **el total no puede subir, y ninguna regla individual puede subir
aunque el total baje.** Hoy podrías arreglar 40 `F401` y meter 20 `BLE001`
nuevos, y el total seguiría "mejorando". Con presupuesto por regla, no.

**Sabes que funcionó** cuando: introduces un `except Exception: pass` en
cualquier sitio y el gate te lo dice **con el nombre de la regla y el fichero**.
**Riesgo:** que el gate sea tan ruidoso que se desactive. Mitigación: que solo
hable cuando hay regresión, y que imprima el comando exacto para arreglarlo.

**Conexión:** esta es la idea que hace posibles A3, A4 y todo el bloque C.

### ÉPICA A3 · Una sola autoridad de lint (el fin del sombra)
**Duele:** `shared/pyproject.toml` tiene `[tool.ruff]` **sin `lint.ignore`**.
Ruff lo usa para todo `shared/`, así que los `ignore` de la raíz no llegan:

```
ruff check .                                -> 33 errores
ruff check shared/ --config pyproject.toml  -> All checks passed!
```

**Idea:** **una sola fuente de verdad de configuración de ruff**, y un test que
lo verifique. No basta con borrar el `[tool.ruff]` de `shared/`: hay que impedir
que vuelva. Test parametrizado sobre **todos** los `pyproject.toml`/`ruff.toml`
del repo:

> Ningún sub-proyecto declara `[tool.ruff]` con `select`/`ignore` propios.
> Si quiere desviarse, **debe** re-exportar la raíz con `extend`.

Y la verificación, **por mutación** (como manda `MEMORY.md`): reintroducir el
`[tool.ruff]` en `shared/pyproject.toml` y comprobar que el test se pone rojo.

**Sabes que funcionó** cuando `ruff check .` da 0 **sin ningún flag**.
Ese es el criterio de aceptación, y hoy **ningún flag** es la parte importante.

### ÉPICA A4 · Una sola versión de cada herramienta
**Duele:** el hook fija `ruff-pre-commit v0.4.10`; el venv tiene `0.16.7`.
`ruff format --check .` → **164 ficheros sin formatear** pese al pase masivo.
El hook **puede deshacer** lo que hace el venv. Esta es, probablemente, la razón
de que el changeset de 1470 ficheros no termine de cerrarse.

**Idea:** un **manifiesto de versiones de herramientas** que sea la única fuente,
y del que se *deriven* el hook y el venv:

```
.quality-baseline/toolchain.json    # {"ruff": "0.16.7", "pytest": "..."}
```

Un script genera el `rev:` del pre-commit y compara con el venv.
Si divergen, **falla**. Con el mismo número, el formateo converge y deja de
haber trabajo infinito.

**Generalización épica:** esto aplica a todo el repo. `MEMORY.md` ya documenta
que hay 3 `pyproject.toml`, 8 carpetas `shared` y 3 `event_bus.py`. La idea
grande es: **un repo, un número.** Cualquier cosa que se declare en dos sitios
divergirá; la única pregunta es cuándo.

---

## BLOQUE B — Recuperar el terreno perdido (duplicación y derivas)

### ÉPICA B1 · El mapa de duplicación que se mantiene solo
**Duele (medido):** `scripts/`, `core/`, `content/` guardan **copias literales**
del mismo módulo:

| Módulo | Copias | Líneas cada una |
|---|---|---|
| `tunnel_guard.py` | 5 | 1256 / 1234 / 1230 / … |
| `google_free_tier_automations.py` | 2 | **1496** |
| `flow_studio_aig.py` | 2 | **1382** |
| `sil_engine.py` | 3 | 1338 / 1337 / 1337 |
| `viral_content_factory.py` | 3 | 1268 |
| `termux_v2_roadmap.py` | 2 | 1288 |

**135 basenames** viven en >2 sitios. Y ya existe `scripts/utils/auditar_duplicacion.py`
para medirlo… que nadie ejecuta automáticamente.

**Idea épica:** no borrar copias a mano (te vas a equivocar), sino **fijar el
techo y bajarlo**. Igual que el ratchet de lint, pero de duplicación:

```
.quality-baseline/duplicacion.tsv   # fecha, commit, nº de gemelos, bytes duplicados
```

El gate: el número no puede subir. Cada vez que migras un módulo, bajas el techo
y lo anotas. En 10 sesiones tienes 30 módulos menos y un gráfico que lo demuestra.

**Lo que lo hace épico:** el criterio de resolución es **"un import, no una
copia"**. No hay que decidir *cuál* copia es la buena por cada caso: la buena es
`core/`, y todo lo demás son `sys.path` heredados. Eso es una regla, no 135
decisiones.

**Riesgo alto:** tocar `sys.path` puede romper el despliegue (este repo ya
gastó tres fallos encadenados por eso). Migración **de uno en uno**, con el test
`test_integridad_despliegue.py` corriendo antes y después.

### ÉPICA B2 · Un solo techo: matar el dual reverse-proxy
**Duele (medido):** hay **dos** reverse proxies declarados:

- `nginx` en `config/docker-compose.yml:263` — publica `80:80` y espera
  `service_healthy` de 6 servicios. Su contenedor está **`Created`**, nunca
  arrancó.
- `caddy` en `config/docker-compose.yml:293` — publica **también `80:80`** y
  `443`. Es el que está `healthy` y sirviendo.

Dos servicios pidiendo el mismo puerto. Hoy no chocan solo porque nginx nunca
levanta. El día que alguien haga `docker compose up nginx`, el arranque falla
o, peor, el `80` cambia de dueño sin aviso.

Encima, `config/Caddyfile` declara `handle_path /secure/*` **dos veces**
(línea 26 → 9880, línea 53 → 9999). Los `handle_path` son mutuamente
excluyentes: **el de 9999 es inalcanzable, sin error y sin log.**

**Idea épica:** **el proxy es Caddy, y nginx se retira del compose.**
No "arreglar los dos": retirar uno. Y llevar la promesa un paso más allá:

1. Un test que lea `config/docker-compose.yml` y **pruebe que ningún puerto del
   host está publicado dos veces**. Hoy fallaría, señalando nginx/caddy.
2. Un test que lea `config/Caddyfile` y **pruebe que no hay `handle_path`
   repetidos en el mismo site block**. Hoy fallaría, señalando `/secure/*`.
3. Resolver `/secure/*`: decidir el upstream (9880 = `secure-engine`,
   9999 = `sec-opt`) y borrar el otro.

Los tres son tests de 20 líneas que convierten "el sistema miente" en "el sistema
avisa". **Sabes que funcionó** cuando borras una línea del Caddyfile y el test te
dice exactamente qué ruta dejaste huérfana.

---

## BLOQUE C — Rendimiento donde duele de verdad

### ÉPICA C1 · SQLite en modo WAL: la optimización de 5 minutos
**Duele (medido):** ninguno de los 5 `.db` de trabajo tiene `-wal`/`-shm`:

```
aig.db / daniela_multiuser.db / memory_rag.db / scheduler_locks.db / trigger_watches.db
  -> 0 ficheros WAL
```

Sin WAL, SQLite usa rollback journal: **cada escritura bloquea a todos los
lectores**. En un sistema con 12 contenedores, un scheduler y un multi-tenant,
eso es contención pura.

**Idea:** activar WAL **en la capa de conexión**, no fichero a fichero (si no,
el próximo `.db` nace sin él):

```python
conn.execute("PRAGMA journal_mode=WAL")  # lectores y escritor a la vez
conn.execute("PRAGMA synchronous=NORMAL")  # seguro con WAL, mucho más rápido
conn.execute("PRAGMA busy_timeout=5000")  # adiós a "database is locked"
```

**Por qué es épica y no un one-liner:** ya existe `infra-opt/database/sqlite_wal.py`.
La idea no es escribirlo, es **hacerlo imposible de olvidar**: un helper único
(`aig_shared`) del que salgan todas las conexiones, más una guardia que falle si
aparece un `sqlite3.connect()` crudo en el código de servicios.

**Sabes que funcionó** cuando `daniela_multiuser.db-wal` existe en disco.
**Riesgo:** bajo, pero WAL no funciona en volúmenes de red (NFS/SMB). Si algún
`.db` vive en uno, ese se queda en journal y hay que documentarlo.

### ÉPICA C2 · Presupuesto de recursos por contenedor
**Duele:** hay 12 contenedores en un único host y **ninguno declara `mem_limit`
ni `cpus`** en el compose. Un pico de memoria en `gods-eye` o en un motor de
vídeo (los `prototypes/wan_cogvideo_*.py` son pesados) puede llevarse por delante
a Daniela o a Redis por OOM del kernel, y el diagnóstico será "algo se cayó".

**Idea épica:** **presupuesto explícito de memoria** por servicio, con techo
declarado y un test que lo verifique:

```yaml
deploy:
  resources:
    limits:   { memory: 512M }
    reservations: { memory: 128M }
```

Y un test que exija que **todo** servicio del compose declara límites.
**Sabes que funcionó** cuando `docker stats` no tiene ninguna fila sin `LIMIT`,
y cuando un pico falla *dentro* del contenedor (error claro) en vez de tumbar al
vecino.

### ÉPICA C3 · Del "arranca" al "arranca rápido"
**Duele:** hoy solo se mide que los contenedores estén `healthy`. No hay línea
base de **latencia de arranque** ni de tiempo de respuesta. Un servicio que
tarda 4 minutos en estar listo bloquea a nginx/caddy (esperan `service_healthy`).

**Idea:** `scripts/` ya tiene `load-testing/locust/locustfile.py` e
`infra-opt/database/connection_pool.py`. La idea épica es **tener un número y
vigilarlo**: presupuesto de arranque (p. ej. daniela < 30 s) y de p95 de
`/api/status`. El gate: no puede empeorar más de un 20% respecto al último
registro.

**Por qué importa aquí concretamente:** este repo introduce `/api/predictive`,
`/api/plugins`, `/api/healing`… cada blueprint nuevo añade tiempo de import.
Sin un presupuesto, el arranque crece de forma invisible hasta que un día nginx
no levanta.

---

## BLOQUE D — Que el conocimiento no se evapore

### ÉPICA D1 · `shared/` entra en el radar
**Duele (medido):** el `exclude` de ruff tiene 13 entradas —`.git`, `.venv`,
`archives`, `node_modules`, `vendor`, `ia-services/tencent_suite`, `decentraland`,
`android_app`, `gev/daniela-os/epic-pc/web`, `HunyuanDiT`…— pero **no hay
ninguna razón escrita para `shared/`**, que es donde viven los 33 errores.

Peor: `shared/pyproject.toml` **silencia** `shared/` sin que nadie lo decidiera.
Eso no es una decisión de arquitectura, es un accidente con consecuencias.

**Idea:** **el `exclude` de ruff es una decisión de arquitectura y debe estar
justificada**, entrada por entrada, en el propio fichero o en un test que la
exija. Nada se excluye del análisis sin una frase que diga por qué.

**Generalización:** el mismo problema aparece con las **8 carpetas `shared`**
(7 importables), los **3 `pyproject.toml`**, los **26 `server.py`** y los
**10 `config.py`**. `docs/ESTRUCTURA.md` existe; la idea es que sea **verificable**
—un test que confronte la estructura real con la documentada y falle cuando
aparezca un `server.py` número 27 sin registrar.

### ÉPICA D2 · La memoria que no se queda atrás
**Duele:** `.workbuddy-ai/memory/` se cortaba en `2026-09-22.md`. Todo el trabajo
del 23, 24 y 25 —el ratchet completo, el subsistema de integración de hermes,
la CI, Caddy— **no estaba registrado**. La siguiente sesión arranca ciega.

**Idea épica:** aquí hay algo genuinamente reutilizable. **Un script `repo-status`
que genere el parte de situación automáticamente** en lugar de fiarse de que
alguien se acuerde de escribirlo. Ya existe `scripts/utils/repo_status.py`
(registrado en `run.py` como *"estado real del repo sin fiarse de git"*).

El salto: que ese script emita **el bloque de memoria ya redactado** —conteo de
tests, rutas de daniela, estado de contenedores, cambios sin commitear,
divergencia del baseline— y que se pueda pegar tal cual. **Sabes que funcionó**
cuando la memoria de un día se escribe en 10 segundos y no contiene ni un número
inventado.

---

## BLOQUE E — La idea más épica: el presupuesto de deuda

Todo lo anterior son instancias de **una sola idea**, y merece decirse:

> **Este repo no necesita menos código. Necesita medir su deuda y no dejarla crecer.**

Evidencia de que funciona: **el ratchet ya lo hizo.** El historial de
`.quality-baseline/ruff-count.txt` va de **10 565 → 0**. Eso no es un backtest,
es un resultado conseguido en este repo por este equipo. La técnica está probada.

Lo que falta es **el segundo ratchet**, y luego el tercero:

| Deuda | Métrica | Techo hoy | Fuente |
|---|---|---|---|
| Lint | reglas ruff | **0** (mantener) | `ruff check .` sin flags |
| Duplicación | módulos gemelos | **135** basenames | `auditar_duplicacion.py` |
| Formato | ficheros sin formatear | **164** → 0 | `ruff format --check .` |
| Estructura | `shared`/`server.py` sin registrar | por definir | `ESTRUCTURA.md` |
| Arranque | segundos a `healthy` | por medir | `health_gate` |

Cada fila es una épica. Lo potente no es ninguna: es **el hábito**, y que el
progreso sea visible y acumulativo en lugar de depender de recordar.

---

## Orden de ejecución recomendado

Por **desbloqueo**, no por brillantez. Nada de esto tiene sentido mientras la CI
mienta, porque no habrá forma de saber si algo mejoró.

| # | Épica | Por qué en esta posición | Coste | Estado 2026-09-25 |
|---|---|---|---|---|
| 1 | **A1** CI de verdad | sin esto, todo lo demás es a ciegas | ~1 h | ✅ hecha |
| 2 | **A3** config única de ruff | criterio: 0 sin flags | ~1 h | ✅ hecha |
| 3 | **A4** una versión de ruff | desbloquea cerrar el changeset | ~30 min | ✅ hecha |
| 4 | **A2** ratchet automatizado | convierte A3/A4 en permanentes | ~2 h | ✅ hecho |
| 5 | **B2** un solo proxy | riesgo de arranque real, hoy latente | ~1 h | ⚠️ a medias |
| 6 | **C1** SQLite WAL | mejor ratio beneficio/riesgo del repo | ~1 h | pendiente |
| 7 | **B1** duplicación | el más caro; hacerlo por incrementos | semanas | pendiente |
| 8 | **C2, C3, D1, D2** | consolidación y vigilancia | continuo | pendiente |

**Lo que NO haría todavía:** tocar `sys.path` de forma masiva (B1 a lo bruto),
auto-corregir los ~56 ficheros AMBIVALENTES marcados en `auditar_raices.py`, ni
reescribir los stubs. Hasta que A1–A4 estén en pie, cualquier refactor grande es
indemostrable — y este repo ya pagó tres fallos encadenados por eso.

---

## Registro de lo ejecutado (2026-09-25)

### ✅ A1 · CI de verdad

`ci.yml` tenia `working-directory: config` en **todos** los pasos, copiado de
`cd.yml`. Resultado medido: `pytest tests/` buscaba `config/tests` (inexistente),
`ruff check .` linteaba JSON, y `pip install -e .` usaba el `build-backend`
inexistente de `config/pyproject.toml`. **La CI podia estar verde sin haber
comprobado nada.**

Hecho:

- `working-directory: .` en `ci.yml` (se mantiene `config` en `cd.yml`, donde
  sí es correcto porque el compose vive ahí). Los dos workflows ya no comparten
  `defaults`: tienen necesidades distintas.
- `scripts/core/ci_precondiciones.py`: valida los 3 `build-backend`, que
  `tests/` exista en el cwd, y que `testpaths` sea el de la raíz. Aborta con
  código 1 y dice qué falla.
- `scripts/core/ci_conteo_tests.py`: exige que se recojan **1220** tests. Una
  suite verde con la mitad sin colectar es el fallo silencioso clásico de este
  repo (`norecursedirs`, o un skip por una ruta movida).
- La lógica vive en scripts versionados, no en heredocs del YAML. Motivo
  medido: `tests/core/test_referencias_integridad.py` lee las rutas entre
  comillas del workflow y usa su `working-directory` como base, así que un
  heredoc con rutas dentro del YAML ponía ese test en rojo.

✅ **Resuelto el 2026-09-25.** El ⚠️ que estaba aquí ("Actions corre en
`self-hosted`, así que esto no se ha ejecutado en un runner real") se cerró
aplicando la **opción A** (`docs/PLAN-100-2026-09-25.md` §0): se dejó de fingir
que hay CI. `ci.yml` y `cd.yml` se archivaron en `docs/archive/` (no estaban
trackeados, así que nunca corrieron y no hay nada que perder) y la verificación
local tiene ahora punto de entrada único:
`scripts/core/verificar_todo.py`, vigilado por
`tests/core/test_punto_de_entrada.py` y verificado por mutación.

### ✅ A3 · Una sola autoridad de configuración de ruff

Se quitó el `[tool.ruff]` de `shared/pyproject.toml` (con una nota en el propio
fichero explicando por qué no debe volver).

**Criterio cumplido:**

```
ruff check .              -> All checks passed!     (antes: 33 errores)
--show-settings           -> Settings path: ...\pyproject.toml   (antes: shared/)
```

`tests/core/test_config_ruff_unica.py` (8 tests) lo vigila: ningún subproyecto
puede redeclarar `select`/`ignore`, no puede haber `ruff.toml` suelto, y no
puede aparecer un cuarto `pyproject.toml` sin registrar. Verificado **por
mutación en las 4 direcciones** (documentado en el propio test).

### ✅ A4 · Una versión de ruff

`.pre-commit-config.yaml` fijaba `ruff-pre-commit v0.4.10`; el venv tiene
`0.16.7`. Alineado a `v0.16.7` (confirmado que el tag existe en el repo de
astral-sh).

```
ruff format --check .     -> 1343 files already formatted   (antes: 168 pendientes)
```

⚠️ **Hallazgo inesperado y serio.** `ruff format` 0.16.7 **rompió la sintaxis**
de 3 ficheros:

```
agents/meeting_intelligence.py
core/meeting_intelligence.py
scripts/agents/meeting_intelligence.py
```

Reescribió un f-string con comillas dobles anidadas
(`f"- [{a["person"]}] ..."`), que es **Python 3.12+**, pese a que el
`pyproject.toml` declara `target-version = "py311"`. El fichero dejaba de
compilar: `invalid-syntax: Cannot reuse outer quote character`.

Es **reproducible**: formatear el fichero vuelve a romperlo cada pasada. Como
dejar el repo en un estado donde el formateador anula la sintaxis no es
aceptable, se extrajo la lógica a un helper `_lineas_pasos()`: mismo resultado
(verificado con datos reales), y estable frente al formateador. El repo queda
**convergente**: `ruff format` ya no tiene nada que cambiar.

### ✅ A2 · El ratchet, automatizado

`scripts/utils/ratchet_ruff.py`. Antes `grep -rn ruff-count` solo encontraba el
`.md`: **nada leía el número**.

- Mide con `ruff check .` **sin flags** (el comando reproducible) y lo compara
  con el techo de `.quality-baseline/ruff-count.txt`.
- Añade **presupuesto por regla** (`ruff-por-regla.json`): el total es agregado
  y se puede "mejorar" arreglando 40 `F401` y metiendo 20 `BLE001` nuevos.
- Verificado por mutación en las dos direcciones: una violación nueva da exit 1;
  y **una regla que crece mientras el total baja también da exit 1**.

### ⚠️ B2 · Un solo proxy — a medias, con una decisión pendiente

Arreglado lo que era inequívoco: `config/Caddyfile` declaraba
`handle_path /secure/*` **dos veces** (línea 26 → 9880, línea 53 → 9999). Los
`handle_path` de un site block son mutuamente excluyentes: el de **9999 estaba
enmascarado sin error ni log**.

Se conservó 9999, con evidencia:
- `9880` **no lo publica ningún servicio** del compose.
- `9999` es el servicio `security`.
- Probado en vivo: `curl localhost:9999` → **200**; `localhost:9880` → **000**.

**CERRADO el 2026-09-25 (opción A del informe): se retiró `nginx` del compose.**

`nginx` (antes línea 263) y `caddy` (línea 293) publicaban **ambos el puerto 80**.
No chocaban solo porque el contenedor `aig-nginx` estaba en estado `Created` y
nunca había arrancado: `StartedAt` = `0001-01-01T00:00:00Z`, sin IP, sin puerto
ocupado. Configuración muerta desde el primer despliegue.

Quién servía el puerto 80 lo confirma el propio servidor:
`curl -s --noproxy '*' http://127.0.0.1/health` → `Server: Caddy`.

Decisión: **retirar `nginx` del `config/docker-compose.yml`.** Los 11 servicios
restantes se resuelven sin él (`compose.sh config --services` → 0 coincidencias
de nginx). Los ficheros `nginx/nginx.conf` y `nginx/nginx.core.conf` **no** se
borran: los usan `docker-compose.prod.yml` y `docker-compose.core.yml`, que son
stacks alternativos.

Los dos tests que estaban en rojo a propósito pasan a verde **sin tocarlos**, que
es justo como se diseñaron:

```
PASSED test_ningun_puerto_del_host_lo_publican_dos_servicios
PASSED test_no_hay_dos_reverse_proxies_activos_en_el_compose
```

### Bonus: el healthcheck de Caddy no podía fallar

Retirar nginx dejó a Caddy como única puerta, así que su healthcheck pasó a
importar de verdad. Y estaba roto. Medido:

```
GET /health  Host: localhost    -> 308 Location: https://localhost/health
GET /health  Host: 127.0.0.1    -> 308 Location: https://127.0.0.1/health
```

El Caddyfile **no tenía site block para `localhost`**, así que Caddy aplicaba su
catch-all implícito y redirigía a HTTPS. Y `curl -f` **no falla con un 3xx**
(solo con 4xx/5xx y errores de red). El HTTPS automático tampoco podía
completarse: ACME no emite certificados para `localhost` ni para una IP.

Consecuencia: el contenedor llevaba **horas en `healthy` sin haber respondido
jamás un 200**. Un endpoint de salud con una sola función -decir "sigo vivo"- no
lo estaba haciendo.

Arreglo: site block `http://localhost { respond /health 200 }` (fuerza *sin*
TLS, que es lo que quiere un endpoint interno) y healthcheck con `wget -qO-`.
Verificado tras recrear el contenedor:

```
docker exec aig-caddy wget -S -qO- http://localhost/health
  HTTP/1.1 200 OK
  Server: Caddy
exit=0
```

⚠️ **Detalle que importa:** Caddy enruta por la cabecera `Host`. Tener site block
para `localhost` **no cubre** `127.0.0.1`. Un healthcheck contra la IP literal
reintroduce el 308. Hay una guardia para las dos formas.

