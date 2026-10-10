# Visor completo: el God's Eye View original dentro de Daniela

Hasta ahora Daniela servia un visor **propio** (`/gods-eye`): un globo Cesium con
6 capas OSINT. El proyecto original (`bilawalsidhu/gev`) tiene **21
capas registradas (18 visibles)**, 7 estilos visuales, HUD, cockpit, CCTV con
calibracion, radio, escenas, voz y 9 ciudades con POIs. Es decir: mucho mas.

Este documento explica como se recupera **todo eso** sin reimplementarlo, y por
que se hizo asi y no de otra forma.

---

## 1. Por que NO se reimplementa ni se embebe

Se comprobaron las dos alternativas "obvias" y **ninguna funciona**:

| Intento | Por que falla |
|---|---|
| `vite build` y servir el `dist/` como estatico | Sus **22 proveedores de `/api/*` son middleware del servidor de desarrollo de Vite** (`server/providers/local.js`). Un build estatico no los ejecuta: tendrias el globo pero **sin datos en vivo**. |
| Meter la app en un `<iframe>` | Su servidor manda **`X-Frame-Options: DENY`** y `Content-Security-Policy: frame-ancestors 'none'` (`build/vite.js`). |
| Reimplementar las capas en el visor propio | Seria un trabajo enorme y **nunca** quedaria igual. Ademas varias capas dependen de esos proveedores. |

Conclusion: para tener **todas las funciones y el aspecto original** hay que
**ejecutar su servidor** y exponerlo bajo el mismo origen de Daniela.

## 2. Como se hace

```
navegador
   |  GET /gods-eye/pro/...        GET /api/cctv/health
   v                                    v
+-------------------------------------------------+
|  Daniela (Flask, un solo origen)                |
|  aig/gev/gev_proxy.py                |
|    - /gods-eye/pro/*   -> proxy inverso         |
|    - 24 prefijos /api/* -> proxy inverso        |
+-------------------------------------------------+
   |  http://127.0.0.1:4173
   v
+-------------------------------------------------+
|  servidor del ORIGINAL (Vite)                   |
|    node .../vite.js --base=/gods-eye/pro/       |
|    + sus 22 proveedores de /api/*               |
+-------------------------------------------------+
```

Se lanza el servidor del original con **`--base=/gods-eye/pro/`**, de modo que
Vite reescribe todas sus rutas de assets y su `import.meta.env.BASE_URL` pasa a
ser `/gods-eye/pro/`. Verificado: la parte de la app que ya respeta `BASE_URL`
recibe el prefijo correcto.

Sus llamadas a `/api/*` son **absolutas** y siguen yendo a la raiz del origen,
asi que se proxean aparte con **reglas explicitas por prefijo** (24 prefijos x2
reglas), nunca con un catch-all.

### Por que `/gods-eye/pro/` y no `/gods-eye/`

El visor propio ya ocupa `/gods-eye` y sirve sus assets en `/gods-eye/static/*`.
Montar el original en `/gods-eye/` habria tapado esas rutas. `/gods-eye/pro/` es
subruta de la promesa y **no sombrea nada**. Desde el visor propio hay un boton
**"Visor completo"** que lleva ahi.

### Sin colisiones de API

Los 24 prefijos del original **no coinciden** con los nuestros (`/api/globe/*`,
`/api/cc/*`, `/api/billing/*`, `/api/i18n`, `/api/idiomas`).

Hay un caso limite que se verifico a proposito: **`/api/cc`** (nuestro Command
Center) es **prefijo de cadena** de **`/api/cctv`** (camaras del original).
Werkzeug casa reglas estaticas **exactas**, asi que conviven sin problema; se
comprobo que `/api/cc/consola` llega a nosotros y `/api/cctv/health` al
original.

## 3. Control de acceso

`/gods-eye/pro/` y las APIs proxeadas exigen **admin o tenant identificado**:

| Situacion | Resultado |
|---|---|
| Sin `aig_ADMIN_SECRET` (desarrollo local) | 200 (admin) |
| Con secreto y sin cabecera | **403** |
| Con secreto y `X-Admin-Secret` correcto | 200 |
| Con `X-Tenant-Slug` (cliente identificado) | 200 |

La gestion del servicio (`/api/gev/arrancar`, `/api/gev/parar`) es **solo admin**.

## 4. Requisitos y degradacion honesta

El visor completo necesita **Node >=24.14 <25** (o >=26 <27, segun el `engines`
del original). El Node gestionado de este entorno es 22.x y **no sirve**; el del
sistema (24.15) si.

Si falta Node o el proyecto original, **Daniela no falla**: el modulo declara
`disponible: false` con el motivo, la ruta responde **503 explicando que falta**,
y el resto de Daniela sigue igual. Es la misma regla de honestidad que usan el
Command Center y las capas OSINT.

Variables de entorno:

| Variable | Para que | Defecto |
|---|---|---|
| `DANIELA_GEV_DIR` | Directorio del proyecto original (solo si lo lanza Daniela) | busca junto al repo, `vendor/gev`, `/opt/gev` |
| `DANIELA_GEV_PORT` | Puerto interno del sidecar | `4173` |
| `DANIELA_NODE` | Binario de Node a usar | el primero que cumpla `engines` |
| `DANIELA_GEV_URL` | **Servidor externo**: si se define, Daniela **no lanza nada** y se limita a proxear. Es como se usa en Docker, donde no hay Node | vacio (modo local) |
| `DANIELA_GEV_MODO` | `dev` (fiel al original, con panel de claves) o `preview` (build estatico, mas ligero) | `dev` |

Con `DANIELA_GEV_URL` definido **no hacen falta ni Node ni el proyecto en la
maquina de Daniela**: solo que el servidor de enfrente responda en
`/gods-eye/pro/`. Por eso la imagen Docker de Daniela sigue siendo solo-Python.

## 5. Uso

```bash
# estado (no arranca nada)
python -m aig.gev.gev_proxy estado

# arrancar / parar el sidecar a mano
python -m aig.gev.gev_proxy arrancar
python -m aig.gev.gev_proxy parar

# verificacion de integracion completa (sin ocupar puerto publico)
python scripts/verificar_visor_completo.py
```

Daniela **precalienta** el sidecar en segundo plano al registrar la fase, para
que la primera visita no espere el arranque en frio de Vite. Si el usuario llega
antes, la propia peticion lo arranca y espera.

## 6. Detalles que costaron tiempo

- **El sidecar debe sobrevivir a quien lo lanza.** Se lanza desacoplado
  (`DETACHED_PROCESS` en Windows, `start_new_session` en POSIX); si no, muere al
  terminar el proceso que lo arranco.
- **`arrancar()` necesitaba candado.** Lo llaman a la vez el precalentamiento y
  la primera visita: sin `threading.Lock` los dos lanzaban Node, `--strictPort`
  mataba a uno, y `_PROC` acababa apuntando al muerto mientras el vivo seguia sin
  dueno. `parar()` decia "no hay sidecar" con el servidor en marcha.
- **Comprobar el puerto no basta.** Hay que comprobar que sirve **nuestra base**:
  quedo antes un Vite con `--base=/gods-eye/` (sin `/pro`) y el puerto respondia
  igual.
- **El proxy de entorno rompe localhost.** Esta maquina tiene `HTTP_PROXY`
  apuntando a `127.0.0.1:14674`, que devuelve **502** a las peticiones a
  localhost. El proxy fuerza `proxies={"http": None, "https": None}` y el sidecar
  se lanza con `NO_PROXY=127.0.0.1,localhost`.
- **No se proxea WebSocket** porque el original no usa ninguno en su servidor: la
  voz pide un token en `/api/realtime/token` y el navegador habla **directo con
  OpenAI**.

## 7. Despliegue con Docker

El visor completo va como **servicio aparte** del stack (`gods-eye`), no dentro
de la imagen de Daniela. Motivos:

- el original exige `engines: >=24.14.0 <25 || >=26 <27`: no vale cualquier Node;
- pesa 458 MB (251 MB solo de `node_modules`) frente a una imagen de Daniela que
  es solo-Python;
- asi Daniela solo habla HTTP con el y se sigue desplegando sin Node.

```
navegador
   |  http://localhost:9200/gods-eye/pro/
   v
+-------------------------- aig_aig-network ----------------------------+
|                                                                             |
|  aig-daniela (:9200)                        aig-gods-eye (:4173)            |
|    DANIELA_GEV_URL=http://gods-eye:4173  -->  vite --base=/gods-eye/pro/     |
|    proxy inverso en /gods-eye/pro/            + sus 22 proveedores /api/*    |
|                                                                             |
+-----------------------------------------------------------------------------+
```

### 7.1 Puesta en marcha

```bash
# 1. Prepara el contexto de build (una vez, o al actualizar el original)
python scripts/setup_gev_docker.py

# 2. Levanta el visor y Daniela
scripts/deploy/compose.sh up -d --build gods-eye daniela

# 3. Comprueba
scripts/deploy/compose.sh ps
curl -s -o /dev/null -w '%{http_code}\n' http://localhost:9200/gods-eye/pro/
```

`scripts/deploy/compose.sh` es un envoltorio de `docker compose` que pasa los
flags correctos desde cualquier directorio. Equivale a:

```bash
scripts/deploy/compose.sh up -d --build
```

### 7.2 Por que hace falta el envoltorio

Tres trampas que no se ven leyendo el compose:

1. **Las rutas relativas se resuelven respecto al compose, no a tu `cwd`.** El
   compose vive en `config/` desde el commit `chore(fase-2)`, que lo movio desde
   la raiz **sin corregir las rutas**: `context: .` apuntaba a `config/` —donde no
   hay ni Dockerfiles ni codigo— y el stack **no se podia reconstruir**. Ahora los
   `context` son `..` y el `name:` esta fijado a `aig`, para que lanzarlo
   desde `config/` no cree una segunda red (`config_aig-network`) y deje fuera los
   contenedores ya levantados.
2. **El `.env` que Compose usa para interpolar tambien sale de `config/`**, no de
   la raiz. Sin `--env-file .env`, las claves de los proveedores saldrian del
   `config/.env` viejo, que tiene placeholders (`OPENAI_API_KEY=YOUR_VALUE_HERE`).
   Comprobado.
3. **`docker.exe` no entiende los caminos de Git Bash**: pasarle
   `/c/Users/.../.env` le hace buscar `C:\c\Users\...\.env`. El envoltorio usa
   rutas relativas con el `cwd` en la raiz del repositorio.

### 7.3 Claves de los proveedores

Todas las claves del original se leen de `process.env` (comprobado: las **48**
variables de `server/` salen de ahi), asi que se pasan por entorno. El compose
inyecta **solo las que el visor usa**, no el `.env` entero: meterlo con `env_file`
arrastraba las 666 variables del repositorio —incluidas las de Stripe, JWT y otros
servicios— a un contenedor que no las necesita.

| Clave | Capa que activa |
|---|---|
| `FIRMS_MAP_KEY` | focos de calor (NASA FIRMS) |
| `AISSTREAM_API_KEY` | barcos AIS en vivo |
| `OPENSKY_CLIENT_ID` / `_SECRET` / `USERNAME` / `PASSWORD` | vuelos con cuenta (sin ella, OpenSky anonimo) |
| `TOMTOM_API_KEY` | teselas de trafico |
| `TFL_APP_KEY` | CCTV de Londres |
| `LL2_API_TOKEN` | lanzamientos (The Space Devs) |
| `OPENAI_API_KEY` (+ `OPENAI_REALTIME_MODEL`, `OPENAI_REALTIME_VOICE`) | voz manos libres |

Las que falten **no rompen nada**: dejan su capa sin datos, igual que hoy (hoy no
hay ninguna configurada salvo `OPENAI_API_KEY`).

`GOOGLE_MAPS_API_KEY` y `CESIUM_ION_TOKEN` son la excepcion: se **incrustan en el
bundle** durante el build (`define` en `build/vite.js`), asi que van como
argumentos de build y cambiarlas exige `--build`, no basta reiniciar.

`GEV_KEY_SETUP_EXTERNAL_KEYS` le dice al panel "POWER UP" que esas claves ya
vienen de fuera, en vez de mostrarlas como ausentes.

### 7.4 `dev` o `preview`

| | `dev` (por defecto) | `preview` |
|---|---|---|
| Que sirve | el codigo fuente, como el `npm run dev` del original | el `dist/` ya construido |
| Panel "POWER UP" (claves en la interfaz) | **si** | no (es solo de dev, por diseno) |
| Datos en vivo | si | **si** (medido: `/api/opensky` devuelve aviones reales) |
| Arranque | mas lento (transforma al vuelo) | mas rapido |

Se deja `dev` por defecto porque es lo **fiel al original**. Para el modo ligero:

```bash
GEV_MODO=preview scripts/deploy/compose.sh up -d --build gods-eye daniela
```

La unica diferencia visible de `preview` es el panel de claves; el resto de la
interfaz es identica (`import.meta.env.DEV` solo decide si se registran utilidades
de QA, no oculta nada).

### 7.5 Actualizar el original

```bash
python scripts/setup_gev_docker.py --forzar
scripts/deploy/compose.sh up -d --build gods-eye
```

`vendor/gev/` es una copia **generada** (~29 MB; sin `node_modules`,
`dist`, `.git`, `docs/` ni `.env`) y no se versiona. El script la rehace desde
`DANIELA_GEV_DIR`, o desde `../gev` si esta al lado del repositorio.

### 7.6 Alternativa: el original en el host

Si prefieres seguir arrancando el original en el host (`npm run dev` en
`../gev`), apunta Daniela ahi y **no** levantes `gods-eye`:

```yaml
      - DANIELA_GEV_URL=http://host.docker.internal:4173
```

Es la via con mas fidelidad y coste de imagen cero; a cambio, el visor solo
aparece mientras el servidor del host este en marcha.

### 7.7 Que se pierde y que no

- **No se pierde nada de la interfaz.** Los 21 registros de capas, los 7 estilos
  visuales, HUD, cockpit, CCTV con calibracion, radio, escenas, voz y los 9
  presets de ciudad vienen con el proyecto original, que se sirve tal cual.
- **El panel de claves solo esta en `dev`** (por diseno del original). En
  `preview` las claves van por entorno, que ademas es lo correcto en un despliegue.
- **Daniela degrada con elegancia**: si `gods-eye` no esta levantado, solo
  `/gods-eye/pro/` responde **503 con el motivo**; `/gods-eye` y el resto de la
  aplicacion siguen igual.

### 7.8 Higiene de build: el `.dockerignore` de la raiz

Todos los compose usan `context: ..`, es decir que el contexto de build es el
**repositorio entero**. Sin un `.dockerignore`, Docker enviaba todo en cada
build:

| Directorio | Tamano |
|---|---|
| `.git` | **1.7 GB** |
| `data/` | 155 MB |
| `vendor/` (vendido del visor) | 32 MB |
| `node_modules` sueltos | variable |

Consecuencia medida: el build de `daniela` tardaba **12 minutos** y terminaba
fallando al instalar `aig-shared`:

```
error: could not delete 'build/lib/aig_shared/ai/cache.py': Permission denied
ERROR: Failed building wheel for aig-shared
```

Ese fallo dejaba la imagen **sin reconstruir**, asi que el contenedor seguia con
el codigo de dias atras: es la razon de fondo de que "el despliegue dejara de
mostrar las opciones del original". No era un problema de rutas ni del visor,
sino de que **la imagen no se podia reconstruir**.

El `.dockerignore` de la raiz excluye `.git`, `data/`, `vendor/`, los
`node_modules`, las caches (`__pycache__`, `.ruff_cache`, `*.egg-info`...) y los
`.env`. El contexto baja de ~2 GB a decenas de MB y el build deja de fallar.

> El servicio `gods-eye` no se ve afectado: su contexto es
> `vendor/gev` y usa su propio `.dockerignore`.

#### El otro motivo por el que no se podia reconstruir: `appuser` contra root

El `.dockerignore` arregla el tamano del contexto, pero el build seguia
fallando. La causa estaba dentro de la imagen:

- `aig-base:latest` fija **`USER appuser`**.
- `appuser` **no puede escribir** en `/usr/local/lib/python3.11/site-packages`
  (comprobado con un `touch` dentro del contenedor).
- En la imagen hay un `/app/aig-shared/build/` **propiedad de root**, de un build
  anterior hecho cuando ese paso corria como root. `appuser` no puede borrarlo,
  asi que el build del wheel moria siempre con:

```
error: could not delete 'build/lib/aig_shared/ai/cache.py': Permission denied
ERROR: Failed building wheel for aig-shared
```

Se arreglo en `daniela-os/Dockerfile`: ese bloque se ejecuta como
`root` (borra el `build/` rancio e instala `aig-shared`) y **se vuelve a
`appuser`** antes de `EXPOSE`, para que el contenedor no corra con privilegios.

**Estado comprobado del despliegue antes del arreglo** (imagen del 18 de
septiembre):

| | Contenedor | Host |
|---|---|---|
| Rutas registradas | **346** | 506 |
| Rutas `/gods-eye/pro` | **0** | 5 |
| `/app/aig/` | **no existe** | 7.5 MB |

Es decir: la imagen desplegada era anterior a toda la integracion de
`aig/`. No es que el visor completo se hubiera "perdido" en el
despliegue: **no habia llegado nunca**, porque la imagen no se podia
reconstruir.
