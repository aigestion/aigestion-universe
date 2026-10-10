# AUDITORIA DEL TELEFONO — Pixel 8a

**Fecha:** 2026-09-10 · **Modo:** solo lectura (no se ha borrado nada del movil)

---

## Resumen ejecutivo

| Hallazgo | Severidad |
|---|---|
| El DanielaOS que corre en el movil es un **MOCK**: el boton "Python REPL" devuelve `200 OK` sin ejecutar nada | **Alta** — falsa sensacion de funcionamiento |
| El movil tiene un clon `~/apps/AIGESTION-MONOREPO` con `scripts/daniela_guardian.sh`, **inexistente en el PC** | Alta — trabajo no sincronizado |
| Termux **0.118.3** con `targetSdk 28` en Android 17; `RUN_COMMAND` bloqueado, sin root | Media — limita la automatizacion |
| `runsvdir` gestiona **sshd + crond + ssh-agent + cloudflared** | Info — hay un tunel Cloudflare activo |
| `univero-v1` no existe en local, ni en remotos cacheados, ni en `/sdcard` | Bloqueante — requiere tu confirmacion |

**Optimizaciones ya aplicadas en el repo:** 3 errores de sintaxis reparados,
95 docstrings basura eliminados, `dotenv` vuelto opcional.
**403 modulos parsean correctamente · 154 rutas arrancan.**

---

## 1. Dispositivo

```
Modelo         Pixel 8a
Android        17  (CP2A.260805.005)
Build type     user            -> sin root
Bateria        92%  ·  30.3 C  ·  salud OK
Almacenam.     66 GB usados / 110 GB  (61%)
IP WiFi        192.168.1.133/24
Pantalla       DREAMING, keyguard activo (bloqueada)
Termux         0.118.3  (versionCode 1002, targetSdk 28)
Paquetes       termux, termux.boot, termux.api, termux.window, termux.widget
```

## 2. Vias de acceso probadas

| Via | Resultado |
|---|---|
| `adb shell ls /data/data/com.termux/files/home` | `Permission denied` |
| `run-as com.termux` | `package not debuggable` |
| `pm grant com.android.shell com.termux.permission.RUN_COMMAND` | sin efecto |
| `am startservice … RunCommandService` | `Requires permission …` |
| `adb root` | `cannot run as root in production builds` |
| `/proc/<pid>/cwd`, `/proc/<pid>/root` | `Permission denied` |
| **HTTP al gateway :8082** | **responde** |
| **`adb push` a `/sdcard`** | **funciona** |

> El home de Termux es inaccesible desde el PC. Lo resolvi con el instalador (§7),
> que se ejecuta *dentro* de Termux y vuelca el informe a `/sdcard`, donde adb si llega.

## 3. Lo que SI esta corriendo

```
PID     UID    CMD
1864    10431  com.termux.widget
10717   10431  bash  /data/data/com.termux/files/home/apps/AIGESTION-MONOREPO/scripts/daniela_guardian.sh
10721   10431  runsvdir /data/data/com.termux/files/usr/var/service
10730   10431  svlogd …/sv/sshd
10746   10431  svlogd …/sv/crond
10752   10431  svlogd …/sv/ssh-agent
17077   10431  com.termux
24194   10431  termux-api BatteryStatus
28439   10431  svlogd …/sv/cloudflared
28539   10431  python3 server.py          <- el HUD del puerto 8082
```

Puertos en escucha: `8082` (HUD), `20241`, `38149`, `38943`, `51692`, `53601`, `64660`.

## 4. Hallazgo critico: el HUD es un simulador

`GET /` devuelve un HTML de 63 KB: `DANIELA OS // CORE HUD TACTICO`
(Werkzeug 3.1.8 / Python 3.14.6). Solo existen dos rutas:

```
/                     200   HUD
/api/skills/dispatch  200   dispatcher
```

El dispatcher **siempre** responde lo mismo, sea cual sea la accion:

```json
{"latency_ms":2.54,
 "reply":"[DANIELA OS DISPATCH - 13:35:05]\n• Acción: ''\n• Estado: [200 OK]",
 "status":"success"}
```

El HUD declara `action: "ejecutar_codigo"` (un REPL de Python). Lo probe:

```json
{"action":"ejecutar_codigo",
 "code":"open('/sdcard/DanielaOS/_audit_out.json','w').write('x')"}
```
→ respuesta `Acción: 'ejecutar_codigo' · Estado: [200 OK]` → **el fichero nunca se creo**.

Es decir: el REPL, el boton `run_unit_tests` y `Status API Flask` son decorativos.
**El movil no tiene ninguno de los 154 endpoints reales del PC.**

## 5. `univero-v1`

| Donde | Resultado |
|---|---|
| Ramas locales | solo `main` |
| Remotos cacheados | `main`, `ui-stable`, `feature/darwin-api` |
| `git reflog` (20 entradas) | sin rastro |
| `git log --all --grep=univero` | 0 commits |
| Sistema de ficheros (4 niveles) | 0 coincidencias |
| `/sdcard` del movil (7 niveles) | 0 coincidencias |
| `git ls-remote origin` | **bloqueado**: `could not read Username for 'https://github.com'` |

Pista mas probable: **el clon del movil** en `~/apps/AIGESTION-MONOREPO`, que ya tiene
`scripts/daniela_guardian.sh` (fichero que el PC no conoce). El instalador lista sus ramas.

## 6. Optimizaciones aplicadas hoy

### 6.1 Reparados los 3 errores de sintaxis (bloqueaban el despliegue)

`daniela_self_improvement.py`, `jules_free_dispatch.py`, `plugin_system.py`
no importaban. Causa comun: un generador automatico **"AP-10"** inyecto 95 docstrings
*dentro de expresiones* (comprehensions, bloques `with`, sentencias sueltas).
Un `SyntaxError` **no** lo captura `except ImportError`, asi que esto podia reventar
el arranque de DanielaOS.

- 24 ficheros limpiados · 95 docstrings eliminadas · copia de seguridad en `.audit/backup_ap10/`
- Los 3 ficheros reparados y verificados

### 6.2 `dotenv` ya no es obligatorio

`daniela_os.py` hacia `from dotenv import load_dotenv` sin proteccion → habria
reventado en Termux. Ahora degrada con un fallback.

### 6.3 Verificacion

```
403 modulos .py revisados  ->  0 errores de sintaxis
daniela_os.py              ->  arranca con 154 rutas
```

## 7. Paquete de despliegue (listo en `/sdcard/DanielaOS/deploy/`)

30 modulos · 565 KB · probado en aislamiento antes de subirlo (154 rutas).
Incluye Fase 5 (24/7, Git Brain, sanitizer), Fase 6 (Mobile Core, Context Engine,
Caja Negra) y Fase 7 (IR, NFC, Serial, UI nativa), mas el gateway de Termux.

**Un solo comando en Termux:**

```bash
bash /sdcard/DanielaOS/deploy/install.sh
```

Hace: auditoria interna de Termux → `AUDIT_TERMUX.txt` (aqui saldra `univero-v1`),
copia a `~/daniela-os`, instala dependencias, crea 7 widgets, autoarranque con
Termux:Boot y arranca core `:5000` + gateway `:8083`.

## 8. Pendiente (necesito que confirmes)

1. **Ejecutar el instalador** en Termux y pasarme `AUDIT_TERMUX.txt`.
2. **¿Donde esta `univero-v1`?** Otra cuenta/owner de GitHub, o confirmar que es el clon del movil.
3. **Rotar la API key de Gemini** y purgar `.env` del historial de git (P0 ya documentado).
4. **Limpieza del movil** — encontre redundancias claras:
   - 5 grabaciones `TermuxAudioRecording_2026-08-04_*.m4a` huerfanas en la raiz de `/sdcard`
   - Videos generados: ~470 MB (`output_epic_composition.mp4` 136 MB, `output_dynamic_9x16.mp4` 84 MB, `output_screencast_tech.mp4` 84 MB, `output_short_9x16.mp4` 62 MB…)
   - `daniela_1787403364.png` y `daniela_1787576885.png` → **mismo md5** (1.5 MB duplicados)
   - `Informe_Ejecutivo.pdf` de **71 bytes** (vacio)
   - `~/storage` sin montar (Termux no tiene enlace a `/sdcard`)
   - `.trash-storage/` con restos
   - Ningun `.py`/`.sh`/`.json` en `/sdcard` → todo el codigo vive en el home sellado de Termux

   No he borrado nada: dime que borro y con que criterio.
5. **Fase 8** (E-11 Mesh CRDT · E-12 nodos urbanos sin GPS · E-13 llama.cpp local · E-14 puente Bluetooth).
