# Auditoria de la reestructura — 2026-09-22

Commit: `623f10360` (623 ficheros, +724 / −5423; git reconocio **520 renombrados**)
Estado: **1114 tests, 0 fallos, 0 errores, 26 saltados**. Arbol de trabajo limpio.

> **Actualización 2026-09-22 (commit `6a3e454af`):** 5 fixes post-audit aplicados:
> - `gev/daniela-os/server.py`: status() fix (107 módulos, 114 sistemas, sin "Frontend")
> - `gev/daniela-os/server.py`: CORS/SocketIO origins → solo 9200, 9300
> - `core/daniela/omnipresente/server.py`: legacy borrado (imports inexistentes)
> - `nginx/nginx.conf`: rutas `/engine/epic_pc/`, `/engine/frontend/` eliminadas
> - `tests/conftest.py`: `shared` en `_AMBIGUOS` → **0 errores colección**
> **Tests ahora: 1145 passed, 44 skipped**
>
> **Actualización 2026-09-22 (commit `TODO` - this session):** 9 next steps completados:
> 1. ✅ `archives/` 2.7GB — ya en `.gitignore`, no en git history
> 2. ✅ `.obsoleto` borrado, `tests/api/test_docker_marketplace.py` commiteado
> 3. ✅ `AUDITORIA-2026-09-22.md` actualizado con counts reales
> 4. ✅ `docker-compose.yml` vs `slim.yml` — diferencias intencionales documentadas
> 5. ✅ `docker-compose.prod.yml` — añadidos `infra`, `agent`, `gods-eye`, `prometheus`, `grafana` + nginx depends_on + volumes
> 6. ✅ `nginx/nginx.conf` — comentarios obsoletos eliminados
> 7. ✅ `docs/ARQUITECTURA.md` — sección 8-bis "Dos carpetas shared/" añadida
> 8. ✅ `pyproject.toml` + `.github/workflows/ci.yml` — ruff, mypy, black, pytest config + CI pipeline
> 9. ✅ `.env` — 766 líneas, solo 2 matches placeholder (comentarios). Rotación pendiente en proveedores (Gemini AIza, Supabase service_role, etc.) — ver `INVENTARIO-CLAVES.md`

---

## 1. Resumen ejecutivo

La reestructura esta **bien pensada** y va en la direccion correcta: agrupa por
dominio lo que estaba suelto. Pero dejo **9 clases de rotura silenciosa**, y dos
de ellas apagaban funcionalidad de produccion sin que ningun test lo notara:

| Rotura | Impacto medido |
|---|---|
| `_cargar_integrador()` busca `daniela.py` a la profundidad equivocada | **78 rutas muertas** (i18n, Command Center, Stripe, visor God's Eye + OSINT) |
| `shared/scheduler.py` acepta un `server.py` cualquiera como raiz | **5 agentes devolvian `None`**, 10 tests rojos |

Las otras siete son de arranque: 2 errores de coleccion de pytest, 23 lineas de
workflow con tabulador, 10 targets de compose, 22 COPY de Dockerfile, 3
directorios de Dependabot y 4 rutas de test.

Ninguna se veia en un `docker build` verde. Las dos graves solo se manifiestan
**en ejecucion** y **en el host** (no en el contenedor), que es justo donde menos
se prueba.

Una segunda pasada (seccion 4.4) encontro la vuelta de tuerca de esa misma idea:
**56 ficheros cuyo indice de raiz es correcto en el contenedor y erroneo en el
host**. La herramienta que debia detectarlo era la que estaba rota, y su modo
`--aplicar` habria "arreglado" el host rompiendo produccion.

Y la seccion 4.5 documenta lo que hoy es mas urgente: **el despliegue no esta
actualizado**. Produccion sigue ejecutando el codigo del 21 de septiembre.

---

## 2. Que cambio

| antes | ahora | contenido |
|---|---|---|
| `daniela-os/` | `gev/daniela-os/` | absorbe `daniela-jarvis`, `epic-pc`, `muse` |
| `pixel/` | `mobile-app/pixel/` | |
| `phone_deploy/` | `mobile-app/phone_deploy/` | |
| `mobile-app/` | `mobile-app/` | |
| `hermes-epic/` | `ia-services/hermes/` | |
| `aig-shared/` | `shared/` | el paquete `aig_shared`, intacto |
| `aig-optimization/` | `optimization/` | |
| `tencent-suite/` | `ia-services/tencent-suite/` | |
| `frontend/`, `unified-dashboard/` | `archives/` | islas retiradas |

### Medidas del repo

```
63 carpetas + 13 ficheros sueltos en la raiz
4.2 GB de arbol de trabajo (sin .git)

archives          2.7 GB   64%   <- el lastre
.venv             471 MB
IA-SERVICES       244 MB
media_exports     219 MB
assets            186 MB
data              152 MB
bin               131 MB
--- el codigo de verdad ---
core              2.6 MB
engine            1.1 MB
gev          7.5 MB
shared            120 KB

740.078 lineas por extension (3.321 ficheros)
  vendor          268.683  <- de terceros
  scripts          83.499
  IA-SERVICES      79.168
  mobile-app      69.072
  core             54.460
  gev         31.094
  engine           28.116
  tests            12.366
```

---

## 3. Las 9 roturas, una a una

### 3.1 `_cargar_integrador()`: 78 rutas muertas (la grave)

`gev/daniela-os/server.py` carga el integrador `daniela.py` **por ruta**,
probando dos profundidades:

```python
for candidata in (Path(__file__).parent / "daniela.py",          # contenedor
                  Path(__file__).parent.parent / "daniela.py"):   # host, ANTES
```

`daniela.py` vive **en la raiz del repo** (`<repo>/daniela.py`, 5.6 KB, tracked).
Con `server.py` en `<repo>/daniela-os/`, `parent.parent` daba en el clavo. Al
moverse a `<repo>/gev/daniela-os/`, el fichero queda en el **abuelo**, y
ninguno de los dos candidatos existe en el host.

Resultado: la fase `aig` moria con `ImportError: no se encontro daniela.py`
y se perdian, medido:

```
[i18n]            idioma por defecto: es (soportados: es, en)
[Command Center]  5 herramientas registradas en /api/cc/*
[Billing]         rutas registradas en /api/billing/*  (webhook Stripe con firma)
[God's Eye]       visor registrado en /gods-eye  (API /api/globe/*, OSINT /api/globe/osint/*)
[God's Eye Pro]   visor completo en /gods-eye/pro/
```

```
antes: 374 rutas, failed_phases = [{'phase': 'aig', ...}]
ahora: 452 rutas, failed_phases = []
```

**78 rutas = 17% de la superficie de API**, incluida toda la facturacion y el
visor OSINT. Arreglado anadiendo el tercer candidato, con un comentario que
avisa de que el numero de `.parent` depende de la profundidad de `server.py`.

### 3.2 `shared/scheduler.py`: marcador de raiz con DECOY

```python
if os.path.exists(os.path.join(_c, "server.py")) or os.path.exists(
    os.path.join(_c, "core", "server.py")):
```

A 3 niveles de `gev/daniela-os/shared/scheduler.py` esta `<repo>/gev/`,
que **tiene su propio `server.py`** (el del visor). El bucle lo aceptaba como
raiz, `AGENT_PATHS` apuntaba a `<repo>/gev/agent_*.py` (inexistente) y los
5 agentes (`calendario`, `correo`, `epic_ideas`, `redes`, `vigia`) devolvian
`None` → 10 tests rojos.

Arreglado exigiendo **dos** marcadores: `core/server.py` **y** `agents/`.
Comprobado que `<repo>/gev/` no tiene ninguno de los dos.

### 3.3 `server.py::_base_proyecto()` (reparado antes)

El marcador era `aig-optimization/`, que ya no existe. La raiz resolvia a
`gev/` y **5 fases morian en silencio** (`sse`, `health`, `obs`, `conn`,
`frontend`).

### 3.4 `tests/conftest.py`: el guardia de orden nunca se disparaba

Para resolver la colision de `optimization` (servicio en la raiz vs
`engine/scale_engine/optimization.py`) se puso un guardia que garantiza que la
raiz quede detras de los motores. Comparaba con `==`:

```python
if _RAIZ not in sys.path:      # <-- nunca era False
```

Pero los tests insertan la raiz **sin normalizar**:

```
RAIZ      : 'C:\Users\Alejandro\aig'
insertado : 'C:\Users\Alejandro\aig\tests\core\..\..'
iguales?    False      <-- pero Python los resuelve a lo mismo
```

Con `normpath`/`normcase` si coinciden. Arreglado; 3 tests (`test_devtools`,
`test_intel`, `test_ecosystem`) ademas insertaban la raiz para llegar a
`engine/`, asi que ahora insertan `engine/` directamente.

### 3.5 Rutas de test obsoletas

`../../scale-engine` (ya no existe; ahora `engine/scale_engine`) en
`test_scale.py`, y `../../daniela-os` en `test_embeddings.py`, `test_health.py`,
`test_daniela_fases.py`, `test_daniela_ai.py`, `test_pixel_guard.py`.

### 3.6 `ia-services/hermes/Dockerfile`

`COPY ./hermes-epic/ .` — la carpeta se movio. Detectado por el test de
integridad `test_dockerfile_copy_origenes_existen`, que valida cada COPY contra
el disco **sin construir**.

### 3.7 23 tabuladores en 6 workflows

`    \timeout-minutes: 15` — la reestructura se comio la `t` y dejo un TAB, que
YAML no admite como inicio de token. 8 tests de `test_deploy_honesto` fallaban
con `ScannerError`.

### 3.8 `.github/dependabot.yml`

Apuntaba a `/aig-shared`, `/unified-dashboard` y `/daniela-jarvis`. Los tres
inexistentes.

### 3.9 Compose y Dockerfiles

10 targets de build rotos y 22 COPY. Repuntados. El servicio `frontend` se
**retiro** de `slim` y `prod` en vez de dejarlo: una fase que siempre falla hace
que `/api/status` reporte un fallo permanente y **enmascara los fallos reales**.

---

## 4. Riesgos abiertos

### 4.1 La divergencia con el remoto — RESUELTA

```
antes:  remoto main = remoto universo-v1 = 653758a90
        local = 90699fbe6 (4 commits), merge-base 955c18ba8
        -> 19 commits del remoto que local no tenia, y viceversa

ahora:  main (local y remoto) = fed4001e7, y es la UNICA rama
```

**Como se resolvio, y por que no hizo falta `force-push`:**

Se midio primero si el contenido del remoto estaba ya en local, comparando
**hashes de contenido normalizado** (no rutas):

| zona | coinciden |
|---|---|
| fuera de `aig/` | 1807 / 1988 = **90.9%** |
| bajo `aig/` | 96 / 171 = **56.1%** |

El 44% restante **no es contenido perdido: son las reescrituras de rutas del
aplanado**. Verificado linea a linea en `gev/server.py`: 10 lineas de 476
difieren, y las 10 son `aig.gev` -> `gev` y
`aig.core.X` -> `core.X`.

Un merge normal daba **33 conflictos**, casi todos espurios (el remoto tiene el
arbol bajo `aig/`, local lo tiene aplanado). Peor: un merge con `-X ours`
habria **resucitado `aig/` como copia duplicada** al aplicar los ficheros
del remoto en rutas no conflictivas.

La solucion fue `git merge -s ours remoto-main`:

* registra los 19 commits del remoto como **ancestros** (no se pierde nada),
* **no toca el arbol** (nada de `aig/` resucitado),
* y convierte el push a `main` en **fast-forward** -> sin `force-push`.

Resultado: `653758a90..1f8658e0c  main -> main`, sin `+`, sin force.

**Consolidacion en una sola rama.** El repo tenia 6 ramas locales y 25 remotas.
Antes de borrar nada se comprobo que tenian commits unicos:

| rama | commits unicos | destino |
|---|---|---|
| `main` (vieja) | 0 | borrada |
| `edicion-apk` | 0 | borrada |
| `fase-11-seguridad-contexto` | 0 | borrada |
| `ui-stable` | **331** | etiquetada y borrada |
| `feature/darwin-api` | **4** | etiquetada y borrada |
| `universo-v1` | = HEAD | renombrada a `main` |

Las dos con trabajo unico se conservaron como etiquetas publicadas
(`archivo-ui-stable-98040ac47`, `archivo-feature-darwin-api-b7ba0dcce`), asi que
los 335 commits siguen accesibles desde el remoto.

**Dependabot.** Al quedar una sola rama, Dependabot recreo 14 ramas en segundos
y abrio 15 PRs (#129-#143) a las 08:55. Mientras haya un PR de versiones
abierto, su rama existe: **no se puede tener una sola rama y PRs automaticos de
versiones a la vez.** Se puso `open-pull-requests-limit: 0` en las 10 entradas
(commit `fed4001e7`) y se cerraron los 15 PRs. Las alertas de CVE y los security
updates **siguen activos**: se configuran en Settings > Code security, no en el
fichero.

### 4.1.b Un bug de git en este repo: los refs remotos no se escriben

Ni `git fetch` ni `git update-ref` consiguen persistir un ref bajo
`refs/remotes/`. Sintomas medidos:

```
$ git update-ref refs/remotes/origin/main <sha>
$ echo $?          -> 0            (dice que si)
$ git show-ref refs/remotes/origin/main
                   -> (nada)       (no existe)
$ ls .git/refs/remotes/origin/
                   -> No such file or directory
```

Descartado: `fetch.prune` (se probo a `false`), el refspec (es correcto:
`+refs/heads/*:refs/remotes/origin/*`), `core.hooksPath` (`.githooks` solo tiene
`pre-commit`), backend reftable (no hay `.git/reftable`), y permisos del sistema
de ficheros (se creo y borro un fichero de prueba en esa carpeta sin problema).

**Workaround que funciona:** escribir el ref como fichero plano.

```bash
mkdir -p .git/refs/remotes/origin
echo "<sha>" > .git/refs/remotes/origin/main
```

Con eso `git show-ref`, `git branch -r` y `git rev-parse origin/main` ya lo ven
bien. Es coherente con la corrupcion del almacen de objetos ya documentada en
`410c013af`; **no se ha encontrado la causa raiz.**

### 4.2 Ocho carpetas llamadas `shared` — medido: hoy NO hay sombra

```
./shared                                <- NO es un paquete: es el directorio fuente
                                           de `aig_shared` (no tiene __init__.py)
./gev/daniela-os/shared            <- paquete real (ai_bridge, health, scheduler...)
./core/daniela/omnipresente/shared      <- __init__.py + config.py + event_bus...
./ia-services/hermes/shared             <- __init__.py + config.py + event_bus.py
./infra-opt/shared                      <- __init__.py + config.py
./perf-opt/shared                       <- __init__.py + config.py
./sec-opt/shared                        <- __init__.py + config.py
./agents/api/shared                     <- __init__.py + config.py
```

Aqui decia antes "el import depende del orden de `sys.path`", que describe un riesgo
pero no lo mide. Medido el 2026-09-22 **dentro de los 6 servicios vivos**
(importando `server` para montar el `sys.path` real):

| Servicio | `shared` que gana | `WEB_PORT` | dirs distintos con `shared/` en el path |
|---|---|---|---|
| daniela | `/app/shared` | 9200 | **1** |
| hermes | `/app/shared` | 9300 | **1** |
| infra | `/app/shared` | 9700 | **1** |
| agent | `/app/shared` | 9800 | **1** |
| security | `/app/shared` | 9999 | **1** |
| perf | `/app/shared` | 9998 | **1** |

Cada servicio ve **exactamente una** `shared`, y es la suya: hoy no hay sombra.

⚠️ Trampa al medirlo, que casi hace reportar un falso positivo: `sys.path` lleva
**dos** entradas que apuntan a `/app` —la insertada explicitamente y la cadena vacia
del cwd—, asi que un `isdir(p + "/shared")` ingenuo cuenta 2 y parece una colision.
Hay que deduplicar por ruta real antes de concluir nada.

#### Lo que si queda: el material de un fallo silencioso

Los cuatro esqueletos son identicos salvo un numero, y sus `shared/config.py`
declaran `WEB_PORT` con valores **distintos** (9700, 9998, 9999, 9800). Ademas hay
**tres `event_bus.py` diferentes** bajo tres paquetes `shared` importables con el
mismo nombre, y `core/daniela/omnipresente/shared` duplica 5 ficheros de
`gev/daniela-os/shared` con contenido distinto.

Si alguien anade al `sys.path` uno de esos directorios —basta un
`sys.path.insert(0, BASE + "/core/daniela/omnipresente")`— el servicio arranca,
responde, y **se ata al puerto de otro**. No falla nada: `WEB_PORT` es un entero
valido, asi que no hay excepcion que seguir.

Lo que si se puede comprobar sin arrancar nada: **el `shared` de un servicio tiene
que declarar el mismo puerto que su Dockerfile**. Lo guarda
`test_el_shared_del_servicio_declara_su_mismo_puerto`, verificado por mutacion
(cambiar `perf-opt` al 9999 de `sec-opt` lo pone rojo).

### 4.3 Configuracion muerta y referencias rotas — medido

- **Gitlinks de `tencent-suite` — RESUELTO** (commit `90699fbe6`). Habia **6**
  gitlinks (`mode 160000`) y **ningun `.gitmodules`**:
  - Los 3 de `tencent-suite/` (raiz) eran **muertos**: carpetas vacias (0
    entradas), `.git` ya borrado, y apuntaban a los mismos commits que los de
    `ia-services/`. Se quitaron del indice y se borraron las carpetas.
  - Los 3 de `ia-services/tencent-suite/` son **legitimos**: clones limpios, en
    `main`, con los SHAs exactos de los gitlinks, y remotos a los repos publicos
    de Tencent. Solo les faltaba el `.gitmodules`, que se anadio. Con el,
    `git submodule update --init` los reconstruye en un clon nuevo.
  - Nota: los 639 ficheros (266/278/95) **nunca estuvieron trackeados como
    ficheros** — solo como punteros. Eso es correcto para codigo de terceros.
- **Los 11 `docker-compose*.yml` del repo — medido.** Contando los servicios que
  declara cada uno y buscando quien lo cita:

  | fichero | servicios | quien lo cita | veredicto |
  |---|---|---|---|
  | `config/docker-compose.yml` | 11 | `scripts/deploy/compose.sh`, docs, tests | **canonico** |
  | `config/docker-compose.prod.yml` | 18 | `deploy_prod.sh` (bien); `deploy.sh:93`, `deploy.ps1:125` (ruta desnuda) | superconjunto real |
  | `config/docker-compose.slim.yml` | 10 | `startup_aig.ps1:214` — **ruta rota** | arreglado, ver abajo |
  | `config/docker-compose.monitoring.yml` | 4 | `deploy.sh:89`, `deploy.ps1:121` (ruta desnuda) | real, mal invocado |
  | `config/docker-compose.enterprise.yml` | 1 | `scripts/deploy/tenant_bootstrap.py:178` (correcto) | real |
  | `config/docker-compose.core.yml` | 4 | `docker-auto-start-core.sh` (ruta muerta); `deploy_prod.sh --core` (ruta rota) | pila E-36 obsoleta |
  | `config/docker-compose.universes.yml` | **0** | `reorganize_workspace.py:57` (solo lo lista) | plantilla vacia |
  | `docker/docker-compose.yml` | 5 | **nadie** | proyecto IoT ajeno |
  | `docker/docker-compose-aig.yml` | 11 | **nadie** | duplicado derivado |
  | `multi-region/docker-compose.multi.yml` | 7 | `docs/MULTI_REGION.md` | modulo de feature |
  | `load-testing/docker-compose.load.yml` | 10 | `load-testing/README.md` | modulo de feature |

- **CORRECCION: `docker-compose.universes.yml`.** La afirmacion "0 servicios" era
  correcta, pero el fichero vive en **`config/`**, no en la raiz. Sigue siendo una
  plantilla: un unico ejemplo **comentado** mas una red externa. No hay nada que
  borrar; si molesta, es documentacion.
- **CORRECCION: la pila E-36 "nadie la referencia" era impreciso.** La cadena
  real es `scripts/deploy/docker-auto-start-core.sh` (apunta a
  `/mnt/c/.../aig-MONOREPO/infra/docker`, ruta que **no existe**) →
  `config/docker-compose.core.yml:51` → `config/Dockerfile.daniela`. Y
  `config/Dockerfile` (auto-generado, cabecera "AP-14") no lo cita **nadie**.
  Confirmado ademas que **los 6 ficheros que `Dockerfile.daniela` copia no
  existen** (`daniela_os.py`, `aig_core.py`, `model_router.py`,
  `api_gateway.py`, `aig_adapters.py`, `aig_config.json`): el build
  muere en el primer `COPY`. No es que este obsoleta "por las rutas", es que es
  inconstruible. `deploy_prod.sh --core` apuntaba a `docker-compose.core.yml`
  **sin** `config/`; **arreglado** (ahora falla por el Dockerfile, que es el
  error honesto, y no por una ruta mal puesta).
- **CORRECCION: `tests/daniela/test_daniela_backend.py.obsoleto`.** Ya no existe:
  esa afirmacion quedo obsoleta.
- `scripts/utils/auditar_raices.py` tenia marcadores obsoletos (`daniela-os`,
  `config`) y daba 44 falsos positivos. **RESUELTO** — ver 4.4, que ademas
  descubrio un problema mayor.
- `aig/` es un shell de 1 fichero (un log, 20 KB), `research/` tiene un solo
  `hitl_audit.log` (1 KB), `tenants/` y `output-assets/` estan **vacios**, y
  `prototypes/` son 63 ficheros / 20 MB. Confirmados por conteo.
- **El vendor de Cesium se instalaba en la ruta vieja — RESUELTO.** Dos paths que
  quedaron en `aig/gev/` tras el aplanado:
  - `scripts/setup_gev_vendor.py` escribia en
    `<repo>/aig/gev/vendor/cesium`. Esa carpeta ya no existe, asi que
    copiaba/descargaba 22 MB a una ruta muerta y el aviso del Dockerfile ("falta
    el vendor de Cesium") seguia saltando en cada build sin explicacion.
  - `.gitignore` ignoraba `aig/gev/vendor/`. Al cambiar la ruta, los
    22 MB de Cesium de terceros **dejaron de estar ignorados**: un `git add -A`
    los habria commiteado. Ahora ignora `gev/vendor/`.
- **Los comandos de despliegue de la documentacion no funcionan — RESUELTO.**
  `docker compose` (plugin v2) no esta instalado (`unknown command`); solo
  `docker-compose` (suelto). Y sin `--env-file .env` se despliega el
  `config/.env` viejo con placeholders en vez del `.env` real de la raiz (hay dos
  `.env` distintos: raiz 42 KB del 20/09, `config/` 32 KB del 17/09). El repo YA
  tenia el envoltorio que resuelve ambas cosas, `scripts/deploy/compose.sh`, y su
  cabecera lo documenta; la documentacion no lo usaba. Corregido en
  `docs/DESPLIEGUE-GODS-EYE.md` y `docs/VISOR-COMPLETO.md`.
- **Dos proyectos compose llamados `aig`.** Los 6 contenedores huerfanos
  (`aig-dashboard`, `aig-epic-pc`, `aig-frontend`, `aig-frontend-v1`,
  `aig-frontend-v2`, `aig-optimization`) vienen del `docker-compose.yml` de la
  RAIZ que **ya no existe** (se movio a `config/`), con imagenes del 17-18/09.
  Como no hay fichero que los declare, `docker rm` es irreversible y
  `compose down` del stack actual no los toca. Retirados los dos que no
  referenciaba nadie (`aig-frontend-v1`, `aig-frontend-v2`). Los otros cuatro
  siguen: `aig-epic-pc` y `aig-frontend` son **backends vivos de nginx**
  (`$up_epic_pc`, `$up_frontend`), asi que borrarlos deja `/epic-pc` y `/frontend`
  en 502.
- **`startup_aig.ps1` no encontraba su compose — ARREGLADO.** Buscaba
  `docker-compose.slim.yml` en la **raiz** (`$aigRoot\docker-compose.slim.yml`)
  cuando vive en `config/`. No es un script cualquiera: `register_startup.ps1:8`
  lo registra como auto-arranque de Windows. El fallo era **silencioso** — hacia
  `Write-Log "not found" ERROR` y `return`, asi que el arranque del PC terminaba
  sin levantar nada y sin que nadie viera un error. Ahora resuelve ambas
  ubicaciones, con el mismo patron que `deploy_prod.sh`.
- **`deploy.sh` y `deploy.ps1` no calculan la raiz del repo.** Ninguno hace `cd`
  ni deriva la raiz de `$PSScriptRoot`/`BASH_SOURCE` (comprobado: cero
  coincidencias). Usan rutas relativas **desnudas** (`-f docker-compose.prod.yml`,
  `-f docker-compose.monitoring.yml`), que solo resuelven si se invocan desde
  `config/`. Desde la raiz fallan. Es exactamente la clase del bug de
  `deploy_prod.sh` ya corregido, y estos dos se quedaron fuera del arreglo.
  **No se han tocado**: son los scripts legados de "21 engines" (ver abajo) y
  conviene decidir su retirada antes de invertir en arreglarlos.
- **Son el origen de los contenedores huerfanos.** `deploy.sh` declara 19 engines
  (`epic_pc`, `optimization`, `frontend_v1`, `frontend_v2`, `dashboard`,
  `infra_opt`, `agent_mobile`, ...) y `deploy.ps1` construye "all 19 engine
  images". Esos nombres son **exactamente** los contenedores huerfanos de arriba
  (`aig-epic-pc`, `aig-optimization`, `aig-frontend-v1/v2`, `aig-dashboard`).
  Queda explicado de donde salieron: no son restos de un compose borrado, son la
  salida de estos dos scripts.
- **`config/docker-compose.prod.yml` renombra servicios.** Declara **18**
  servicios (los 11 canonicos mas `gateway`, `orchestrator` y los 9
  `engine/*`), pero cambia `infra` -> `infra_opt` y `agent` -> `agent_mobile`.
  Los contextos y Dockerfiles de los 18 **existen** (comprobado uno a uno), asi
  que no es un stack fantasma: es un perfil mas grande. El problema es que
  levantar `prod.yml` crea un **conjunto de contenedores distinto** al canonico
  para los mismos dos servicios. Es una fuente de deriva, no un fichero muerto.
- **`docker/docker-compose-aig.yml` es un duplicado derivado.** Declara los
  **mismos 11 servicios, en el mismo orden** que el canonico, pero el fichero
  difiere (10 636 vs 10 323 bytes). Nadie lo referencia. Es la trampa clasica de
  este repo: dos ficheros que aparentan ser el mismo, se editan por error y
  divergen. `docker/docker-compose.yml`, en el mismo directorio, es un stack
  **IoT ajeno** (homeassistant, n8n, nodered, esphome, grafana) tambien sin
  referencias.
- **`config/Dockerfile` hace `COPY . .` del repo entero.** Auto-generado
  ("AP-14"), sin ninguna referencia. Si alguien lo usara alguna vez, meteria
  `.env`, `archives/` y las credenciales en la imagen. Es un fichero inerte hoy,
  pero de los que conviene borrar en vez de dejar "por si acaso".
- **Guard nuevo: `test_compose_citado_por_un_script_existe`.** El guard anterior
  (`test_scripts_deploy_referencian_rutas_existentes`) solo miraba rutas **con
  `/`**, y `_existe()` descarta las que empiezan por `$`. Por eso las dos formas
  que mas se usan aqui —`-f docker-compose.X.yml` desnudo y
  `"$aigRoot\docker-compose.X.yml"`— se le escapaban por completo. Eso es lo que
  dejo pasar el fallo de `startup_aig.ps1` durante dos dias. El nuevo extrae
  **cualquier** `docker-compose*.yml` citado, con o sin prefijo, y exige que
  exista en la raiz o bajo `config/`. Verificado por sabotaje: renombrar el
  compose a `docker-compose.slim-OBSOLETO.yml` pone rojo **solo** ese script
  (25 verdes, 1 rojo), y se restauro despues.

### 4.4 Segunda pasada: la profundidad host/contenedor (RESUELTO)

Al reparar el auditor de raices aparecio la clase de fallo mas peligrosa de toda
la reestructura, porque **la herramienta que debia detectarla era la que estaba
rota**.

**El auditor daba 45 falsos positivos.** Su marcador de raiz era
`("daniela-os", "config")`; `daniela-os/` ya no existe en la raiz, asi que
`es_raiz()` devolvia `False` siempre y todo `parents[N]` del repo salia como
ROTO. Un marcador obsoleto no da error: da 45 falsos positivos.

**Al repararlo, 56 ficheros salieron como ROTOS. No lo eran.**

```
mobile-app/pixel/context_engine.py        parents[1]
mobile-app/pixel/context/context_engine.py parents[2]
```

Los dos son **correctos en el contenedor**, porque el Dockerfile aplana un nivel:

```dockerfile
COPY --chown=appuser:appuser ./mobile-app/pixel/ ./pixel/    # Dockerfile:31
```

- host: `mobile-app/pixel/x.py` → raiz = `parents[2]`
- contenedor: `/app/pixel/x.py` → raiz = `parents[1]`

Es el mismo caso que `gev/daniela-os/server.py`, que ya se documentaba como
"no vale ningun indice fijo". Si se hubiera lanzado `--aplicar`, el script habria
sumado 1 a los 56 indices, arreglando el host y **rompiendo produccion**.

Arreglos:

| Que | Antes | Ahora |
|---|---|---|
| `auditar_raices.py` | clasificaba todo como ROTOS | lee los remaps de los Dockerfiles y separa **ROTOS** de **AMBIVALENTES**; `--aplicar` no toca los ambiguos |
| `core/health_checks.py::_raiz_repo()` | solo `.git` y `tests/` (excluidos de la imagen) | cae a marcadores que si viajan: `core`, `agents`, `gev` |
| `core/health_checks.py::check_working_tree()` | `degraded` permanente en el contenedor | `unknown` (no degrada) si el arbol es una imagen |
| `server.py::_base_proyecto()` | marcador `optimization/` | `core` + `gev` |

Medido dentro del contenedor `aig-daniela`:

```
_raiz_repo() con marcadores que viajan      -> /app        OK
_raiz_repo() con el marcador viejo          -> /app/core   MAL
_base_proyecto() con (core, gev)       -> /app        OK
_base_proyecto() con optimization           -> /           MAL
```

**Y tres tests llevaban desde la reestructura saltandose en silencio.**
`tests/core/test_integridad_despliegue.py` buscaba `daniela-os/` en la raiz y
hacia `pytest.skip` cuando no lo encontraba — o sea, dejaron de comprobar nada sin
que nadie se enterase. Al reparar la ruta, los skips bajaron de 29 a 26.

Guardias nuevas, todas verificadas **por mutacion** (se rompe lo vigilado y el
test falla):

- el Dockerfile debe copiar cada carpeta que `server.py` mete en `sys.path` — es
  exactamente la regresion que dejo 5 fases muertas en silencio;
- los marcadores de `_base_proyecto()` deben existir en el host **y viajar en la
  imagen** (un marcador como `engine/` existe en el repo pero no se copia);
- la fase `frontend` retirada no puede volver a medias.

**Retirado:** `scripts/deprecar_frontend_legacy.py`. Su trabajo (apagar el
dashboard viejo) lo hizo el archivado de `frontend/` en `archives/frontend/`, y
sus dos rutas (`frontend/`, `aig/archive/`) ya no existen: solo podia
fallar.

### 4.5 El despliegue no estaba actualizado — RESUELTO

Hallazgo de la misma pasada, y probablemente el mas importante para el usuario:

```
imagen aig-daniela  creada: 2026-09-21T20:13:01Z   (antes de la reestructura)
contenedor aig-daniela    Up 13 hours (healthy)
```

Comprobado dentro del contenedor:

| Comprobacion | Resultado |
|---|---|
| `/app/optimization` (nombre nuevo) | **NO existe** |
| `/app/aig-optimization` (nombre viejo) | existe |
| `/app/aig-shared` (nombre viejo) | existe, junto a `/app/shared` |
| `/app/frontend` | existe (hoy esta en `archives/`) |
| `/app/server.py` con el arreglo de 3 profundidades | **NO** (0 coincidencias) |

O sea: **la reestructura estaba en disco y commiteada, pero produccion seguia
ejecutando el codigo del 21 de septiembre.** Por eso el contenedor registraba 506
rutas y el host 451: no era una discrepancia de configuracion, era codigo distinto.

El despliegue "se veia sano" porque el codigo viejo y los nombres viejos eran
coherentes entre si. El fallo aparecia en cuanto se reconstruyera la imagen.

#### Resuelto el 2026-09-22: reconstruido y redesplegado

| Comprobacion | Antes | Ahora |
|---|---|---|
| `routes` en `/api/status` de Daniela | 506 (codigo viejo) | **451** (= el host) |
| `failed_phases` | — | **`[]`** |
| fases registradas | — | 16 (todas) |
| vendor de Cesium dentro de la imagen | — | `/app/gev/vendor/cesium/Cesium.js`, 22 MB |
| `aig-agent` | — | Up (healthy) |
| `aig-hermes` | — | Up (healthy) |
| `aig-nginx` | Up 18 h, sin recrear | sirve `/api/status` con 200 |

**Los tres fallos encadenados** que hubo que resolver para llegar aqui. Los tres
son de la misma familia: un `COPY` que no cubre lo que el codigo importa.

1. `.dockerignore` excluia `mobile-app/`, y `pixel/` vive ahi dentro desde la
   reestructura. El build moria en `COPY ./mobile-app/pixel/ ./pixel/`. Arreglado
   con `!mobile-app/pixel` + `!mobile-app/pixel/**`.
2. `agents/api/Dockerfile` solo copiaba `./agents/api/`, pero
   `swarm/swarm_intelligence.py:3` importa el modulo plano `swarm_intelligence`,
   que vive en `agents/` —un nivel mas arriba— y que a su vez necesita
   `core.llm_client`. `aig-agent` moria en bucle con
   `ModuleNotFoundError: No module named 'swarm_intelligence'`.
3. `ia-services/hermes/Dockerfile` no instalaba `shared/`, asi que heredaba el
   `aig_shared` de `aig-base:latest` (creada 2026-09-18T20:44), **anterior** a
   `shared/aig_shared/auth/middleware.py` (22:15 del mismo dia). `aig-hermes`
   moria con `No module named 'aig_shared.auth.middleware'`. La base se comprobo a
   mano: su `aig_shared/auth/` solo contiene `__init__.py`.

#### Deuda que deja este episodio

`aig-base:latest` sigue siendo del 2026-09-18 y **sigue trayendo un `aig_shared`
viejo**. Cualquier servicio que confie en la base en vez de reinstalar `./shared/`
repetira el fallo de hermes. Dos salidas, ninguna hecha todavia:

* reconstruir la base — una sola vez, pero invalida la cache de todas las imagenes
  derivadas, que son casi todas; o
* mantener el patron de `gev/daniela-os/Dockerfile:62` ("ya viene instalado
  en aig-base, se reinstala para asegurar la ultima version") en cada servicio.

Daniela ya habia elegido lo segundo; hermes ahora tambien.

**Medido en todos los servicios desplegados**, no solo en hermes. La regla no es
"todos instalan `aig_shared`" —eso obligaria a compilar el paquete en servicios que
no lo usan—, sino **el que lo importa, lo instala**:

| Servicio | su `server.py` importa `aig_shared` | su Dockerfile lo instala |
|---|---|---|
| daniela | si | si |
| hermes | si | si (tras este arreglo) |
| infra, agent, security, perf | no | no hace falta |

La correspondencia se cumple. Para que siga cumpliendose hay un test parametrizado
sobre TODOS los servicios del compose
(`test_servicio_que_importa_aig_shared_lo_instala`): recorre el `CMD` de cada
Dockerfile, mira si su entrypoint importa `aig_shared` y, si lo hace, exige el
`COPY` de `./shared/` y su instalacion. Verificado por mutacion **en las dos
direcciones**: quitar el `pip install` de hermes lo pone rojo, y anadir un import
de `aig_shared` a un servicio que no lo instala **tambien**.

Buscando con ese criterio aparecio un unico infractor mas: `optimization/Dockerfile`.
Su `server.py:12` importa el middleware a nivel de modulo (sin `try/except`), asi
que habria muerto igual que hermes. Esta **dormido** —`optimization/` no figura en
`config/docker-compose.yml`; solo lo consume Daniela como libreria, y ahi si
funciona porque Daniela instala `shared/`—, pero se ha arreglado con el mismo patron
para no dejar la mina a quien lo reconstruya. La imagen no se ha construido: no hay
servicio que la use.

### 4.6 Tercera pasada: la relacion host/contenedor puede INVERTIRSE

La seccion 4.4 documentaba el caso en que la imagen "aplana" un directorio, de modo
que un `parents[N]` se queda corto en el host y largo en el contenedor. El servicio
`agent` anadio una vuelta de tuerca: **la relacion puede invertirse**, y entonces
no existe ningun `N` que valga en los dos sitios.

`agents/api/server.py` resolvia la carpeta de los modulos planos de `agents/` con
`os.path.join(BASE, "agents")`, donde `BASE` salia de **tres** `dirname`
encadenados:

| | `server.py` | `swarm_intelligence.py` | relacion |
|---|---|---|---|
| checkout | `<raiz>/agents/api/server.py` | `<raiz>/agents/` | **POR ENCIMA** |
| imagen | `/app/server.py` | `/app/agents/` | **POR DEBAJO** |

En el checkout `BASE` da la raiz del repo y funciona. En la imagen `BASE` cae en
`/`, se insertaba `/agents` en el `sys.path` y el contenedor moria en bucle con
`ModuleNotFoundError: No module named 'swarm_intelligence'`.

La reparacion esta en `_dir_modulos_agentes()`, que comprueba las dos formas
legitimas usando el propio fichero importable como marcador en vez de contar
niveles. La sujetan tres tests nuevos, **los tres verificados por mutacion**
(quitar el `COPY`, volver al calculo por niveles y cambiar el destino: cada uno
hace fallar el test que le corresponde).

Detalle que se cuela facil y conviene no perder: el destino del `COPY` tiene que
ser `/app/agents/`, **no** `/app/`. El modulo deriva su raiz con
`Path(__file__).resolve().parents[1]`, y de ahi cuelga el registro
`data/swarm/exec_log.jsonl`. Con `/app/agents/` ese `parents[1]` vale `/app`
—igual que en el checkout—; copiandolo a `/app/` valdria `/` y el log se
escribiria fuera del servicio. Como `_log_exec()` esta envuelto en `try/except`
("nunca rompe la mision"), el sintoma habria sido un log que se pierde **en
silencio**, no un error.

---

## 5. Ideas para escalado

### A. Lo que hoy impide escalar

**1. `sys.path` es el mecanismo de resolucion. Eso no escala.**
Hoy hay 25 modulos `server.py`, 8 carpetas `shared` y `optimization` duplicado.
Cada modulo nuevo multiplica la probabilidad de colision, y el ganador depende
del **orden de insercion**, que depende de que tests hayan corrido antes. Ya nos
ha mordido 4 veces (`shared`, `optimization`, `scheduler`, `i18n`).

El salto a escalado real es **paquetes instalables**: `pip install -e` por
servicio, imports cualificados (`from aig_shared.auth import ...`,
`from scale_engine.optimization import ...`), y **cero `sys.path.insert`**.
Sin eso, no se puede partir el repo en varios repos ni meter CI por servicio.

**2. Cuatro copias del mismo esqueleto de microservicio.**
`infra-opt`, `perf-opt`, `sec-opt` y `optimization` tienen **exactamente la misma
forma**: `Dockerfile __init__.py server.py shared/ web/` + carpetas de dominio.
Son 4 servicios, 4 Dockerfiles, 4 `shared/`, 4 `server.py`. Deberian ser **un
servicio con modulos de dominio**, como ya se hizo con `engine/` (10 motores en
1 carpeta, 88 ficheros).

**3. Siete ficheros de compose con ~50 definiciones de servicio.**
`prod` 18, `slim` 12, `docker-compose.yml` 12, `core` 4, `monitoring` 3,
`enterprise` 1, `universes` **0**. Se solapan y divergen. El patron que escala es
**1 base + overlays por perfil**: `compose.yaml` + `compose.override.prod.yml`,
`compose.override.monitoring.yml`. Docker Compose ya lo soporta de serie.

**4. `archives/` ocupa el 64% del arbol (2.7 GB).**
Sobra del repo. A un repo `aig-archives` aparte, a un release, o a LFS. Eso solo
ya baja el `git clone` de 4.2 GB a ~1.5 GB y hace viable tener el repo en varias
maquinas y en CI.

**5. 63 carpetas en la raiz.**
El patron que funciono fue `engine/`. Repetirlo: `services/`, `domains/`,
`clients/`. Una raiz de 10-15 entradas es navegable; una de 63 no lo es, y cada
persona nueva tiene que aprender donde esta cada cosa.

### B. Escalado de ejecucion

**6. Paralelizar la suite.** 1137 tests en 79 s en un proceso. Con
`pytest-xdist -n auto` y los nombres ambiguos ya resueltos por paquetes, esto
baja a ~15-20 s. Es el habilitador de CI por servicio.

**7. Retirar los 6 contenedores huerfanos** (`aig-dashboard`, `aig-epic-pc`,
`aig-frontend`, `aig-frontend-v1`, `aig-frontend-v2`, `aig-optimization`) — ya
aprobado, pendiente de ejecutar.

**8. Enganchar `load-testing/` (2.9k lineas) a `perf_tuning/slo.py`.**
Hoy existen las dos piezas y no se hablan. Un SLO por servicio es lo que
convierte "escala" en algo medible.

**9. `multi-region/` ya tiene `dns_sim.py`, su propio compose y
`Dockerfile.regions`.** Es la pieza de escalado geografico y esta aislada: no la
referencia ningun compose principal. Decidir si es estrategia real o prototipo.

**10. `gev/daniela-os/server.py` registra 452 rutas en 8.7 s al importar.**
Todo el registro es sincrono y en el import. En un arranque en frio de un
contenedor eso es tiempo muerto. Merece un perfilado y, si crece, registro
perezoso por blueprint.

### C. Escalado de negocio (lo que parece el objetivo real)

**11. `tenants/` esta vacio (0 bytes) y `supabase/migrations` existe.** El
remoto ya habla de *white-label* y rutas de tenant (`b7215ac66 fix(whitelabel):
compose enterprise invalido, rutas de tenant`). Ese es el eje de escalado
comercial: **un binario, N tenants**. Hoy `tenants/` no tiene nada, asi que el
multi-tenant esta declarado pero no implementado.

**12. `ia-services/` (244 MB) ya agrupa servicios de IA externos**
(`tencent-suite`, `hermes`). Es la forma correcta de aislar dependencias
pesadas (modelos 3D, video) del nucleo. Consolidar ahi todo lo que traiga
dependencias que el nucleo no necesita.

**13. `prototypes/` (19.8 MB) con `assembler_ffmpeg.py`, `brand_studio`...** Esta
en el repo de produccion. A `archives/` o a un repo de I+D.

### D. Orden sugerido

1. Resolver la divergencia y publicar (bloquea todo lo demas).
2. Retirar `archives/` del repo. **−2.7 GB, el mayor retorno por esfuerzo.**
3. Convertir los 4 servicios-esqueleto en 1 (`infra-opt`, `perf-opt`, `sec-opt`,
   `optimization`).
4. Colapsar los 7 compose a 1 base + overlays.
5. Paquetes instalables + eliminar `sys.path.insert`. **Es el cambio caro y el
   que desbloquea el resto.**
6. `pytest-xdist` en CI.
7. Multi-tenant de verdad (`tenants/`).

---

## 6. Como reproducir la verificacion

```bash
# La suite entera (tiene que dar 0 fallos)
.venv/Scripts/python.exe -m pytest tests/ -q

# Que ningun COPY de Dockerfile apunte a una ruta que no existe, y que el
# Dockerfile de Daniela provea todo lo que server.py mete en sys.path
.venv/Scripts/python.exe -m pytest tests/core/test_integridad_despliegue.py -q

# Que Daniela registre todas las fases (failed_phases tiene que ser [])
.venv/Scripts/python.exe -m pytest tests/daniela/test_daniela_fases.py -q

# Auditoria de parents[N]: tiene que dar ROTOS: ninguno.
# Los AMBIVALENTES son esperados (correctos en el contenedor, erroneos en el
# host) y NO se auto-corrigen: --aplicar los ignora a proposito.
.venv/Scripts/python.exe scripts/utils/auditar_raices.py

# Estado real del remoto (git fetch NO escribe los refs en este repo)
git ls-remote --heads origin main

# ¿Esta desplegado el codigo actual? (ver 4.5)
docker image inspect $(docker inspect aig-daniela --format '{{.Config.Image}}') \
  --format 'creada: {{.Created}}'
docker exec aig-daniela sh -c 'ls -d /app/optimization /app/aig-optimization 2>&1'
```

Resultado esperado hoy: `ROTOS: ninguno`, `AMBIVALENTES (56)`, y la imagen
`aig-daniela` **anterior** al 2026-09-22 (o sea, el despliegue pendiente).
