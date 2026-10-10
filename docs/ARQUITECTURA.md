# 🏗️ Arquitectura de aig / Daniela OS

**Estado:** vigente · Última verificación: 14 sep 2026, ejecutando el sistema real
**Comprobado con:** `python -c "import daniela_os; print(len(list(daniela_os.app.url_map.iter_rules())))"` → **397**

Este documento describe **lo que hay de verdad**, no lo que se pretendía construir.
Todo lo que dice aquí está verificado ejecutando el código, no leyéndolo.

---

## 1. Vista general

aig es dos cosas a la vez:

1. **Un producto SaaS** para gestorías (email, facturas, reuniones, contenido) —
   con tiers de pago, auth, billing y API pública.
2. **Daniela OS**, una plataforma personal que controla un Pixel 8a desde el PC.

Comparten base de código. La app que se arranca es `daniela_os.py`.

```
                         ┌──────────────────────────────┐
                         │      daniela_os.py           │
                         │   Flask · 397 rutas          │
                         │   puerto 5000                │
                         └──────────────┬───────────────┘
                                        │
              ┌─────────────────────────┼─────────────────────────┐
              │                         │                         │
      ┌───────▼────────┐      ┌─────────▼─────────┐     ┌─────────▼────────┐
      │  aig/    │      │  Puente al Pixel  │     │   Autonomía      │
      │  core, agents, │      │  178 rutas        │     │  self_healing,   │
      │  content, sil  │      │  /api/pixel/*     │     │  blackbox, sil   │
      └────────────────┘      └─────────┬─────────┘     └──────────────────┘
                                        │
                                  adb / HTTP
                                        │
                              ┌─────────▼─────────┐
                              │    Pixel 8a       │
                              │  Termux, sin root │
                              └───────────────────┘

  Aparte, en otro puerto:  api_gateway.py (8080) → API pública con JWT
```

---

## 2. Cómo arranca el sistema

`daniela_os.py` es un único fichero que actúa de **orquestador**. Su patrón es
siempre el mismo, repetido ~122 veces:

```python
try:
    from tunnel_guard import get_instance, register_tunnel_guard_routes
    _tg = get_instance()
    register_tunnel_guard_routes(app)
except Exception as e:                      # ⚠️ Exception, NO ImportError
    print(f"[Tunnel Guard] No disponible: {e}")
```

**Por qué `except Exception` y no `except ImportError`:** un `SyntaxError`, un
`ModuleNotFoundError` por dependencia ausente (p. ej. `sqlalchemy`) o un error de
nombre en tiempo de import **no son** `ImportError`. Con `except ImportError` el
sistema **no arrancaría**. Es deliberado: un módulo roto no debe tumbar el resto.

**Consecuencia que hay que tener presente:** si un módulo falla, el sistema arranca
igual y **solo verás una línea en la consola**. No hay test que lo detecte.
Si un endpoint no responde, mira el arranque antes de buscar el bug en el código.

### Los dos ficheros de entorno

```python
load_dotenv(_REPO_ROOT / ".env")           # raíz  — tiene prioridad por clave
load_dotenv(_REPO_ROOT / "config" / ".env") # config/ — rellena huecos
```

Históricamente solo se leía el de la raíz. Cuando ese se quedó con 12 claves, 75
módulos se quedaron **sin API key y sin avisar**. Ahora se cargan los dos y se
avisa de las claves críticas que falten. Ver [[INSTALACION]].

---

## 3. Estructura del repositorio

```
C:\Users\Alejandro\aig\
│
├── daniela_os.py            🚀 app principal (Flask, 397 rutas)
├── api_gateway.py           API pública separada (puerto 8080, JWT)
├── admin_panel.py           panel de administración
├── termux_v2_roadmap.py     hoja de ruta E-01..E-34 (28/28 hechas)
├── sitecustomize.py         mete scripts/ en sys.path
│
├── aig/               📦 paquete por dominio (código "oficial")
│   ├── core/                orquestador + adapters de módulos
│   ├── agents/              9 personajes + swarm
│   ├── content/             fábrica de contenido, brand kit
│   ├── pixel/               40 módulos del puente al teléfono
│   └── sil/                 motor de auto-mejora
│
├── scripts/                 🔧 herramientas, shims y código histórico
│   ├── check_env.py         ⭐ diagnóstico del entorno
│   ├── repo_status.py       ⭐ estado real del repo
│   └── archive/             código muerto (excluido de escaneos)
│
├── tests/                   ✅ 162 tests verdes (ver sección 7)
├── data/<modulo>/           datos de cada módulo
├── static/                  frontend, landing, brand
└── docs/                    📚 documentación ([[INDEX]])
```

---

## 4. Los 397 endpoints

### Por área

| Prefijo | Rutas | Qué controla |
|---|---:|---|
| `/api/pixel/*` | **178** | El Pixel 8a (37 submódulos, ver abajo) |
| `/api/docker/*` | 15 | Marketplace de Docker y despliegues |
| `/api/*` (raíz) | 14 | Chat, estado, salud general |
| `/api/mesh/*` | 11 | Red mesh entre dispositivos |
| `/api/ar/*` | 11 | Escena WebXR y anclas espaciales |
| `/api/blackbox/*` | 9 | Caja negra forense (buffer de 5 min) |
| `/api/local/*` | 9 | Cerebro local vía Ollama |
| `/api/iot/*` | 8 | Integración IoT real |
| `/api/brain/*` | 8 | Memoria y cerebro |
| `/api/vault/*` | 8 | Caja fuerte de secretos |
| `/api/guard/*` | 8 | Vigilante de túneles (security) |
| `/api/urban/*` | 8 | Nodos urbanos (tiempo, mapas) |
| `/api/agents/*` | 8 | Marketplace de agentes |
| `/api/personas/*` | 7 | Sistema de personalidades |
| `/api/plugins/*` | 7 | Tienda de plugins |
| `/api/ci/*` | 6 | CI real |
| `/api/router/*` | 6 | Enrutador de modelos de IA |
| `/api/predictive/*` | 6 | Motor predictivo |
| `/api/healing/*` | 6 | Auto-reparación |
| resto | 31 | connections, voice, edge, court, invoice, economy, gamification, universes, expediente, cad, media, dna, auth, content, scoreboard |

### Desglose de `/api/pixel/*` (los 178)

El teléfono se controla por **37 submódulos independientes**:

| Submódulo | Rutas | Función |
|---|---:|---|
| `/api/pixel/adb` | 11 | Espejo de pantalla y control ADB |
| `/api/pixel/ui` | 10 | UI nativa y widgets de Termux |
| `/api/pixel/ir` | 9 | Mando universal por infrarrojos |
| `/api/pixel/core` | 8 | Núcleo del puente |
| `/api/pixel/context` | 8 | Contexto y sensores del teléfono |
| `/api/pixel/nfc` / `nfckey` | 16 | NFC: automatización y llaves |
| `/api/pixel/serial` | 8 | Puerto serie (Arduino / ESP32) |
| `/api/pixel/hub` | 8 | Centro de contexto |
| `/api/pixel/geofence` | 7 | Geovallas |
| `/api/pixel/daemon` | 7 | Demonio 24/7 |
| `/api/pixel/rtt` | 7 | WiFi RTT (posicionamiento interior) |
| `/api/pixel/desktop` | 7 | Modo escritorio |
| `/api/pixel/notify` | 6 | Notificaciones |
| `/api/pixel/aware` | 6 | WiFi Aware |
| `/api/pixel/wallpaper` | 6 | Fondo de pantalla vivo |
| `/api/pixel/stereo` | 6 | Visión estéreo (profundidad) |
| `/api/pixel/bt` | 6 | Bluetooth |
| `/api/pixel/vitals` | 6 | Monitor de salud |
| `/api/pixel/files` | 5 | Sincronización de ficheros |
| `/api/pixel/vision` | 5 | Visión por IA |
| otros 17 | 29 | sensors, clipboard, security, hud, battery, torch, camera… |

---

## 5. 🚨 El problema de las copias duplicadas

**Esto es lo más importante que hay que entender antes de editar código.**

El ADR-001 ([[ADR-REPO-LAYOUT]]) definió mover el código a `aig/<dominio>/`
dejando un *shim* en la raíz. Se ejecutó en la Fase 2. **El refactor se deshizo:**
el merge del PR #109 resucitó las copias de la raíz.

Hoy conviven **tres capas** por cada módulo:

```
tunnel_guard.py               ← 1.133 líneas   ✅ ESTE es el que se ejecuta
aig/pixel/tunnel_guard.py ← 1.155 líneas  ❌ DISTINTO, no se usa
scripts/tunnel_guard.py       ← shim
```

### Cómo saber cuál se ejecuta (hazlo SIEMPRE antes de editar)

```bash
./.venv/Scripts/python.exe -c "import tunnel_guard; print(tunnel_guard.__file__)"
```

Resultado actual: **gana la raíz**. Se debe a que `sitecustomize.py` mete `scripts/`
en `sys.path`, y la raíz siempre está primero.

### Impacto

| Si editas… | Efecto real |
|---|---|
| `aig/pixel/tunnel_guard.py` | **NINGUNO.** El código que corre es el de la raíz |
| `tunnel_guard.py` (raíz) | El cambio se aplica ✅ |
| `scripts/tunnel_guard.py` (shim) | Probablemente nada |

Esto ya ha costado horas perdidas. La regla es simple: **comprueba `__file__`
antes de tocar un módulo.**

### Camino de salida

Dos opciones, y solo una se puede elegir:

- **Opción A (recomendada).** La raíz manda. Mover los 226 `.py` a
  `aig/pixel/` con `git mv`, en lotes pequeños, verificando `__file__`
  después de cada lote.
- **Opción B.** La raíz manda y `aig/pixel/` se archiva. Más rápido, pero
  se pierde el trabajo del ADR-001.

**No hagas esto antes de arreglar los tests** (ver sección 7): mover 226 ficheros
sin red de seguridad es pedir un desastre.

---

## 6. Cómo añadir un módulo nuevo

Procedimiento verificado, aprendido a base de romper cosas:

1. **Código en `aig/pixel/X.py`** y datos en `data/X/`.
   Rutas de datos siempre con `_REPO_ROOT`, nunca `dirname(__file__)` a secas.
2. **Blueprint con nombre único y `endpoint=` explícito.** Dos módulos con una
   función `_status` sin `endpoint=` revientan el arranque con
   *"overwriting an existing endpoint"*.
3. **`get_instance()` + `register_X_routes(app)`.** En `daniela_os.py`, envuélvelo
   en `try/except Exception` (ver sección 2).
4. **Nunca `os.system` ni `shell=True`.** Usa `subprocess.run(list_args)`.
5. **Nunca `PIPE` + `timeout`.** Se bloquea para siempre si el proceso nieto
   sobrevive. Usa `tempfile.TemporaryFile` y mata el árbol de procesos.
6. **`es_android()` antes de `cmd` o `dumpsys`.** En Windows existe `cmd.exe`,
   así que sin la comprobación hay falsos positivos.
7. **Llamadas a servicios locales con `proxies={"http": None, "https": None}`.**
   Con `HTTP_PROXY` puesto, `localhost` rebota y devuelve 502.
8. **Commits con `-F fichero`**, nunca `-m` con backticks (bash los ejecuta).

---

## 7. Los tests: ✅ RESUELTO (2026-09-14)

```bash
$ ./.venv/Scripts/python.exe -m pytest tests/ -m "not network" -q
..................................................    [100%]
50 passed, 3 deselected
```

**Antes:** 0 tests ejecutados y 5 errores de colección que abortaban la suite
entera. **Ahora: 162 verdes.** (24 tras A-1, +26 con E-28, +23 con B-1/P1, +40 con B-1/P2, +39 con B-3, +10 con la limpieza del .env)

### Qué estaba roto, y la causa de cada cosa

| Test | Error | Causa real |
|---|---|---|
| `test_daniela.py` | `cannot import name 'DB_NAME'` | El símbolo **nunca existió** en `server.py` |
| `test_daniela_backend.py` | `cannot import name 'MEMORY_FILE'` | Ídem; testeaba un módulo inventado. **Cuarentenado** como `.obsoleto` |
| `test_core.py` | `ValueError: No API key` | **Al importarse**, durante la colección: tira toda la suite |
| `test_and_fix_camera.py` | `FileNotFoundError [WinError 2]` | Binarios de Android en Windows. Movido a `scripts/checks/` |
| `test_auditoria.py` | `FileNotFoundError [WinError 2]` | Ídem |

Además: **10 de los 19 ficheros de `tests/` no eran tests** (0 funciones `test_`,
solo `print()`). Movidos a `scripts/checks/`. Uno de ellos,
`camera_diagnostico.py`, **reescribía `app_daniela.py` e `index.html` al
importarse**: solo ejecutar pytest podía mutar el código fuente.

### Las tres reglas que hacen que no vuelva a pasar

1. 🔴 **Un test NUNCA levanta un servidor real.** Usar el fixture `client`
   (`app.test_client()`): es en memoria, no abre puertos y no necesita el server
   vivo. Los 15 tests que fallaban hacían `subprocess.Popen("app_daniela.py")` —
   **un fichero que no existe**.
2. 🔴 **Nada de código ejecutable a nivel de módulo.** Un `ValueError` al importar
   **aborta la colección entera**, no un test suelto. Todo va dentro de funciones
   o de fixtures.
3. 🔴 **Un test no debe tocar datos de producción.** Usar `tmp_path`. Hay un test
   que verifica que `search()` es **lectura pura** comparando el md5 de la BD.

```bash
# Solo lo que no sale a internet (lo que se usa en el día a día)
pytest tests/ -m "not network"
# Todo, incluidos los que llaman a APIs externas
pytest tests/
```

Markers registrados en `tests/conftest.py`: `network`, `android`, `slow`.

---

## 8. Las "islas": código escrito pero no conectado

Hay ~250 módulos en directorios que **no están registrados en `daniela_os.py`**
(0 referencias, verificado con `grep`):

| Directorio | Módulos | Estado |
|---|---:|---|
| `epic-pc/` | 65 | "62 sistemas de IA" — sin integrar |
| `daniela-omnipresente/` | 65 | Tiene **su propio `server.py`** |
| `hermes-epic/` | 59 | Huérfano, **sin commitear**, sin referencias |
| `phone_deploy/` | 48 | Generado desde raíz |
| `skills/` | 47 | Catálogo de skills |
| `plugins/` | 32 | Catálogo de plugins |
| `daniela-jarvis/` | 2.069 ficheros | Incluye `node_modules` |

**Consecuencia práctica:** los commits dicen "+62 sistemas", "+114 sistemas", pero
esas rutas **no están en las 397**. Las 397 vienen de los módulos ya integrados.
No es que estén mal escritos: es que **no están conectados**.

Decisión pendiente, por cada uno: *se integra como blueprint* o *se archiva en
`scripts/archive/`*. Dejarlos sin decidir es deuda que crece.

---

## 9. Deuda técnica conocida

| Problema | Magnitud | Nota |
|---|---|---|
| Copias divergentes raíz / `aig/pixel` | 226 `.py` en raíz | Ver sección 5 |
| ~~Tests no ejecutan~~ | ✅ **RESUELTO** — 162 tests verdes | Ver sección 7 |
| Claves sin rotar | 4, una **publicada en el historial** | Ver `INVENTARIO-CLAVES.md` |
| Volcados del `.env` dentro del repo | `data/tunnel_guard/backups/`, `config/env/.env.master` | Ignorados, pero es deuda de seguridad |
| `.git` | **1,9 GB** | GitHub avisa a partir de 1 GB |
| Commits automáticos | 148 "Auto-backup Daniela OS" | Ruido en el historial |
| Subrepos sin `.gitmodules` | 3 (`tencent-suite/Hunyuan*`) | Al clonar salen carpetas vacías |
| Binarios trackeados | `oficina3d.glb` 90 MB, `static/media/*.mp4` 2,7 MB | `*.glb` **ya van por Git LFS** (2026-09-29) + se borró el duplicado `assets/3d/` (165 MB). Los `.mp4` siguen pendientes |

---

## 9-bis. Memoria semántica (E-28)

**Dos capas, y las dos son necesarias:**

| Capa | Fichero | Cómo recupera | Estado |
|---|---|---|---|
| Léxica + grafo | `agents/memory_vault.py` | Solape de tokens (TF en Python) + expansión a 1 salto del grafo | ✅ Ya existía |
| **Vectorial** | **`agents/memory_semantic.py`** | **KNN sobre `sqlite-vec`** | ✅ **Nuevo (2026-09-14)** |

Se leen **la misma tabla** `rag_docs`. La capa vectorial guarda sus vectores en una
tabla virtual aparte (`rag_vecs`), así que si falla, el vault sigue funcionando.

**Por qué `sqlite-vec` y no Pinecone/Chroma:** es una extensión de SQLite. Cero
servicios, cero cuota, cero latencia de red, y **funciona igual en el PC y en el
móvil** (el home de Termux es inaccesible por adb, así que un servicio externo no
es viable allí). `memory_rag.db` ya era SQLite: no hay migración.

**Los embeddings son intercambiables** por variable de entorno:

```bash
MEMORY_EMBED_PROVIDER=hashing            # por defecto: sin red, sin modelo, determinista
MEMORY_EMBED_PROVIDER=ollama MEMORY_EMBED_MODEL=nomic-embed-text   # semántica real, local
MEMORY_EMBED_PROVIDER=gemini MEMORY_EMBED_MODEL=text-embedding-004 # requiere clave AIza válida
```

⚠️ **Cambiar de proveedor invalida los vectores ya guardados** (otra dimensión, otro
espacio): hay que hacer `reindex`.

```bash
./.venv/Scripts/python.exe agents/memory_semantic.py stats
./.venv/Scripts/python.exe agents/memory_semantic.py index
./.venv/Scripts/python.exe agents/memory_semantic.py search "proveedor Garcia" --top 5
```

**Dos trampas que costaron tiempo (documentadas por si reaparecen):**

1. 🔴 **`sqlite-vec` devuelve distancia L2, no coseno**, y no lo dice. Restarle 1 a
   pelo daba scores de `0.000` en todo: la búsqueda parecía funcionar sin discriminar
   nada. Para vectores unitarios vale `cos = 1 - L2²/2`. Ver `_l2_a_coseno()`.
2. 🔴 **`search()` llamaba a `_tabla_ok()`, que hace `CREATE VIRTUAL TABLE`.** Una
   consulta de lectura escribía en la BD (12 KB → 36 KB). Ahora `search()` usa
   `_tabla_existe()`, que solo lee el esquema.

**Además:** el `.env` del repo tiene `OLLAMA_URL=YOUR_VALUE_HERE`. Un
`os.getenv("OLLAMA_URL", defecto)` devuelve **la plantilla**, porque la clave existe,
y urllib revienta con `ValueError: unknown url type`. Es el mismo patrón que
`METAMASK_PRIVATE_KEY`: una plantilla leída como valor real. `_url_util()` lo filtra.

---

## 9-ter. El estado de las islas (B-1)

**`agents/plugin_health.py`** (+ shim `scripts/plugin_health.py`) mide el
estado real de los 32 ficheros de `plugins/`, que es la isla más grande del repo.

| Ruta | Qué hace |
|---|---|
| `GET /api/plugins/health` | Resumen + estado de los 31 |
| `GET /api/plugins/health/<nombre>` | Detalle de uno (nombre saneado: `[A-Za-z0-9_]`, 404 si no existe) |

`?importar=false` da la auditoría **estática**: instantánea, sin subprocesos.

**Por qué existe:** el plan decía "conectar `invoice_extractor.py` como piloto".
Medido, no era viable (**4 bloqueos independientes**, ver
[[B1-PILOTO-ISLAS-DIAGNOSTICO]]). Y no era un caso aislado:

| Problema medido | Cuántos |
|---|---|
| Hardcodean `~/daniela-os` (**no existe en este PC**) | **18 / 32** (56 %) |
| Usan comandos de Linux/Android (`ip`, `pm`, `dumpsys`) | varios |
| 🔴 **No se pueden ni importar** | **6 / 32** |

Los 6 que no importan (`audio_listener`, `file_analyzer`, `memory_analyzer`,
`security_cam`, `vision`, `visual_sentinel`) instancian `genai.Client()` **a nivel
de módulo** → `ValueError` durante el `import`. Conectarlos a `daniela_os.py`
**tumbaría el arranque entero**. Es **el mismo defecto sistémico** que dejó la suite
sin ejecutar ni un test (sección 7). Además usan `model="gemini-3.7-flash"`, que
**no es un modelo real**.

⚠️ **Importa cada plugin en un SUBPROCESO**, para que los efectos secundarios de
plugins ajenos no ensucien el proceso del servidor. Nunca importa `plugins/` en
el proceso principal.

**Resultado medido:** `17 ADAPTAR · 11 CANDIDATO · 6 ROTO · 2 INCOMPLETO`. Los 11
`CANDIDATO` (`memory`, `scheduler`, `notifier`, `uptime`, `web_scout`, `briefing`,
`sentinel`, `tts_bridge`, `battery_check`, `power_saver`, `network_test`) son la
lista corta de lo rescatable **sin credenciales**.

### Los tres contadores, y por qué no es uno

**Un contador que mezcla "falló" con "no se evaluó" produce un informe que miente
con seguridad.** La primera versión tenía `rotos = not importable`, así que
`--sin-importar` marcaba los **31** como `ROTO`: en modo estático no se intenta el
import, y `importable` se queda en su default `False`. La salida *parecía*
razonable. Ahora se exponen tres estados separados:

```bash
./.venv/Scripts/python.exe agents/plugin_health.py --sin-importar
#   31 plugins | 0 importan | 0 rotos | 31 sin probar (estatico)

./.venv/Scripts/python.exe agents/plugin_health.py
#   31 plugins | 25 importan | 6 rotos
```

### Decisión de diseño pendiente

Los 18 plugins con `~/daniela-os` apuntan a **Termux en el móvil** (donde esa
carpeta sí existe) pero a veces corren en el PC. Afecta a 18 ficheros, así que no
se aplica sin confirmación. Recomendación: **`DANIELA_BASE_DIR`** con defecto
`~/daniela-os` (el mismo código corre en ambos sitios). Ver §5 del diagnóstico.

### Paso 2 — la isla adaptada: `integrity_guard`

De las 11 `CANDIDATO` se eligió **`plugins/integrity_guard.py`** y se montó como
producto real. Documentado en [[B1-PASO2-INTEGRITY-GUARD]].

**`agents/integrity_guard.py`** (+ shim `scripts/integrity_guard.py`)
detecta si un fichero del proyecto **cambió por su cuenta**: se sella el árbol una
vez y cualquier mutación posterior sale como alerta con su **causa probable**.

| Ruta | Código | Qué hace |
|---|---|---|
| `GET /api/integrity/status` | 200 | ¿Hay sello? ¿de cuándo? ¿cuántos ficheros? |
| `POST /api/integrity/sign` | 200 / 500 | Sella el árbol (`?dry_run=true` cuenta sin escribir) |
| `GET /api/integrity/check` | 200 / **409** / 400 | Audita contra el sello |
| `GET /api/integrity/manifest` | 200 / 404 | El manifiesto (hashes recortados) |

**Por qué `409` y no `500`:** *"hay cambios"* es un **resultado legítimo**, no un
fallo del servidor. `400` = no hay sello, que es un estado distinto.

⚠️ **No confundir con `epic-pc/file-integrity/file_integrity.py`**: aquello es un
**auditor** (escanea y deja registro), esto es un **detector** (falla cuando algo
se movió). Son complementarios.

**Por qué existe en este repo concreto:** aquí han pasado cosas como que un merge
resucitara 226 copias, que `.gitignore` desapareciera, o que el `.env` se
sobrescribiera y las claves quedaran **vacías sin dar error**. La causa probable
de cada alerta está escrita para este repo: *"suele ser una COPIA resucitada por
un merge"*.

**Cuatro defectos reales del plugin original, corregidos** (los cuatro tienen test
de regresión):

1. `os.walk(BASE_DIR)` **sin filtrar** → entraría en `.venv` y `.git` (1,9 GB).
   Medido: con filtros son **1640 ficheros**; sellado en **0,46 s** y verificado
   en **0,29 s**.
2. 🔴 **No detectaba ficheros BORRADOS**: el bucle recorría `current` (lo que
   existe ahora), así que borrar un `.py` pasaba inadvertido.
3. Rutas a `~/daniela-os` → ahora la base es el repo, con `DANIELA_BASE_DIR`
   (opción A del diseño, aplicada aquí como **piloto en un solo fichero**).
4. 🔴 **El manifiesto se auditaba a sí mismo**: cae dentro del árbol vigilado, así
   que la escritura del sello salía como `NUEVO` en la siguiente comprobación →
   **falso positivo permanente**. Descubierto **al probar el ciclo completo**, no
   al leer el código.

⚠️ **Regla crítica de sus tests:** ningún test puede escribir en el manifiesto
real. `POST /api/integrity/sign` **escribe**; si un test la llamara contra el de
producción, dejaría el repo "sellado" con hashes falsos y todo saldría como
cambiado para siempre. Hay un test dedicado a comprobarlo.

**Pendiente (decisión tuya):** sellar el árbol no es un efecto de instalar esto.
Se hace con `POST /api/integrity/sign` o `python integrity_guard.py sign`.

---

## 10. Verificación rápida (copia y pega)

```bash
# ¿Cuántas rutas tengo ahora mismo?
PYTHONPATH="C:/Users/Alejandro/aig" ./.venv/Scripts/python.exe -c \
  "import warnings; warnings.filterwarnings('ignore'); import daniela_os; \
   print('rutas:', len(list(daniela_os.app.url_map.iter_rules())))"

# ¿Qué módulo se ejecuta de verdad?
./.venv/Scripts/python.exe -c "import tunnel_guard; print(tunnel_guard.__file__)"

# ¿Está el entorno completo?
./.venv/Scripts/python.exe scripts/check_env.py

# ¿Cuál es el estado real del repo?
./.venv/Scripts/python.exe scripts/repo_status.py

# ¿Se ejecuta algún test?
./.venv/Scripts/python.exe -m pytest tests/ -q

# ¿Cómo están las 31 islas de plugins/?
PYTHONPATH="C:/Users/Alejandro/aig" ./.venv/Scripts/python.exe \
  agents/plugin_health.py

# ¿Cambió algo en el proyecto sin que lo supieras?
PYTHONPATH="C:/Users/Alejandro/aig" ./.venv/Scripts/python.exe \
  agents/integrity_guard.py check
```

---

## Documentos relacionados

- [[INDEX]] — índice general
- [[INSTALACION]] — cómo ponerlo en marcha
- [[ADR-REPO-LAYOUT]] — la decisión original de estructura
- [[AUDITORIA-CAMBIOS-2026-09-14]] — auditoría y plan por bloques
- [[B1-PILOTO-ISLAS-DIAGNOSTICO]] — por qué las islas no son código listo
- [[B1-PASO2-INTEGRITY-GUARD]] — la isla que sí se adaptó, y sus 4 defectos
- [[SKILLS-PACKAGING]] — inventario de skills y plugins
