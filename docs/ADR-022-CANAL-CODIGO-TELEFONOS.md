# ADR-022 — Cómo llega el código a los teléfonos: APK por Play Store + bundle pull por HTTPS

**Estado:** aceptado (2026-10-04, decisión delegada por el dueño:
"tú tienes que decidir qué es lo mejor para Android")

**Deriva de:** ADR-016 (árbol único de cliente), ADR-018 (sidecars),
ADR-019 (`phone/` runtime Termux).

## Contexto

Hoy hay **cuatro vías** de meter código en un teléfono y ninguna escala
fuera del Pixel del dueño:

| Vía | Quién la usa | Problema |
|---|---|---|
| `termux_deployer.py` → `adb push` a `/sdcard/DanielaOS/deploy` | admin, USB | exige cable + PC junto al móvil; no sirve para clientes |
| `git pull` en Termux (`~/aig`) | dev en el Pixel | exige PAT por teléfono y todo el monorepo |
| `daniela-os/phone_deploy/` versionado en el repo | nadie lo invoca | es un **bundle de build commiteado**: 35/40 ficheros idénticos a la raíz, 5 con drift |
| APK (Kotlin, `daniela-os/android-app/`) | nadie la publica | sólo habla con el backend por `API_BASE_URL`; no reparte código Python |

Y el dueño fija el objetivo: **la app vale para cualquier teléfono
Android** (el Pixel 8a es suya, personal), el reparto es
**"Play Store + dentro de la app"**, y lo que importa es que sea
**escalable y fácil para el admin**, después para clientes.

Restricción de proyecto: **mandato de coste cero** (sin tiers de pago,
sin LFS, sin GHCR, sin Codespaces, CI en runners gratuitos).

## Decisión

### 1. Un artefacto, tres transportes

Todo el código Python que corre **en el teléfono** se empaqueta en un
único **`phone-bundle` versionado**:

```
phone-bundle-<version>/
  manifest.json     version, created_at, entrypoints, sha256 por fichero
  *.py, templates/, install.sh     (plano, como hoy)
```

El bundle se **genera**, no se edita. Transportes intercambiables sobre
el mismo artefacto:

| Transporte | Quién | Cuándo |
|---|---|---|
| `adb` | admin, cable USB | dev en el Pixel |
| `git` | dev en Termux | iterar sobre el repo |
| **`https` (pull)** | **cualquier teléfono** | **el canal de clientes** |

### 2. La APK es el canal de instalación y el guardián de actualizaciones

- **Play Store** reparte el binario (APK/AAB): instalación y actualización
  de la app base.
- **Dentro de la app**, "Actualizar servicios" baja el
  `manifest.json`, verifica `sha256` de cada fichero, aplica el bundle a
  su directorio de datos, reinicia el servicio y **reporta la versión
  aplicada** al dashboard de admin.
- El admin **nunca necesita ADB** con un teléfono de cliente; sólo
  publica: `publish` → el artefacto → los teléfonos lo recogen.

### 3. Runtime agnóstico (mismo bundle, dos ejecutores)

El mismo bundle corre en **Termux** o en **Linux sobre el móvil**
(proot / distro en Termux): un `launch.sh` detecta `$PREFIX` y
`com.termux` y elige intérprete/arranque. **No embebemos CPython en la
APK** (peso, CVEs y ciclo de vida propio → espíritu de ADR-018); si el
teléfono no tiene ningún intérprete, la app **degrada a la PWA** y avisa.

### 4. Fuente única

- **Árbol cliente** `frontend/apps/android-app/mobile-app/` — servicios
  Python que viajan al teléfono (el "árbol único de cliente" de ADR-016).
- **`daniela-os/phone/`** — runtime de Daniela en Termux (ADR-019).
- **`daniela-os/phone_deploy/` pasa a ser SALIDA DE BUILD**: se genera en
  cada `publish`, deja de ser fuente y deja de versionarse. Esto es lo
  que ya dicen por escrito `scripts/sync_phone_deploy.py`
  ("single source of truth" = la raíz) y `termux_deployer.build()`
  ("la fuente de verdad es la RAIZ"); el drift de 5 ficheros es la
  prueba de que nadie lo cumplía.

### 5. Reparto por LADO, no por carpeta

El criterio que resuelve los duplicados es **dónde se ejecuta el
código**, no en qué carpeta está:

| Lado | Casa | Ficheros |
|---|---|---|
| **PC / admin** | `skills/connectors/android/` | `pairing.py`, `termux_deployer.py`, `android_control.py`, `bt_bridge.py`… |
| **Teléfono** | árbol cliente `frontend/apps/android-app/mobile-app/` | `api/termux_api_gateway.py`, `bridges/pixel/pixel_bridge_hub.py` |
| **Runtime Termux** | `daniela-os/phone/` | servicios/cerebro de Daniela (ADR-019) |

> **Inversión respecto a la nota previa del handoff** ("canónico
> `skills/connectors/android/`"): vale **sólo para el lado PC**. El
> gateway y el hub son código de teléfono y su casa es el árbol cliente,
> que es el que de verdad se empaqueta y reparte. El motivo es que
> `skills/` no está en el bundle: mantener ahí el código de teléfono
> obliga a copiarlo en cada build (eso es exactamente el drift actual).

## Consecuencias

1. **`termux_deployer.py` (lado PC)** → gana
   `skills/connectors/android/`. ~~*Pendiente*~~ **Hecho `3274945f`**
   (2026-10-04): `ROOT`/`BUNDLE` resuelven el repo real y `build()`
   copia los 40 módulos. Se borraron `scripts/`, `scripts/pixel/` y
   `daniela-os/termux_deployer.py`.
2. **`termux_api_gateway.py` y `pixel_bridge_hub.py` (lado teléfono)**
   → gana el árbol cliente. ~~*Pendiente*~~ **Hecho `e1b79fec` y
   `97e25e00`** (2026-10-04): el pairing (`/api/pair/challenge` +
   `hashlib`) se portó al gateway del árbol cliente, los tests
   `test_pairing`/`test_termux_api_gateway` apuntan allí y bloquean las
   copias legacy, y `MODULES` del deployer acepta rutas relativas al
   repo (destino FLAT). Se borraron las copias de `skills/`,
   `daniela-os/` y `phone_deploy/`.
3. **Los importadores planos de `pixel_bridge_hub`** en la fachada
   antigua (`daniela-os/daniela_os.py:55`, `tunnel_guard.py:340`,
   `dual_mode_switch.py:258`, `battery_aware_scheduler.py:145`,
   `pixel_second_screen.py:91` y 3 en `scripts/`) van envueltos en
   `try/except ImportError`: borrar la copia **degrada sin romper**
   (`[Pixel Bridge] Not available`). **Hecho `97e25e00`**: se optó por
   degradarlos (los módulos vivos importan por paquete desde
   `bridges.pixel.…` y no dependen de ellos); `tests/mobile/
   test_pixel_bridge_hub.py` verifica que sigan protegidos.
4. **Nuevo comando de admin**: `publish` (genera `phone-bundle`,
   fija versión, sube artefacto). Sustituye a "ADB y cruza los dedos".
5. **El dashboard `127.0.0.1:8082`** pasa a mostrar, por teléfono, la
   versión del bundle aplicada — es lo que hace fácil al admin.
6. **Play Store exige cuenta de desarrollador** (pago único) y firma
   con el keystore de `.env`: prerequisito documentado, no bloquea el
   desarrollo (el canal `adb`/`git` sigue para el admin).

## Alternativas consideradas

1. **`git pull` en cada teléfono como canal único**: descartado. Exige
   PAT por dispositivo, arrastra todo el monorepo y no distingue
   versión aplicada de rama local.
2. **ADB para todo**: descartado. No escala fuera del escritorio del
   dueño (era justo el problema reportado).
3. **Embeber CPython en la APK**: descartado. +15-30 MB, nuestro
   ciclo de vida de seguridad en vez del del sistema, y duplicaría el
   runtime que ya dan Termux/Linux.
4. **FCM como canal de datos** (tenemos `fcm_real_bridge.py`): se
   reserva como **señal de "hay versión nueva"**, no como transporte:
   el payload de FCM no debe llevar código.
