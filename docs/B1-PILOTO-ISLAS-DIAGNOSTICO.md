# 🏝️ B-1 — Piloto "isla → producto": el diagnóstico (2026-09-14)

> **Pregunta:** ¿se puede conectar una isla (`plugins/`) al `daniela_os.py` y que
> aporte rutas útiles?
>
> **Respuesta corta: no todavía, y ahora sé por qué.** Las islas de `plugins/` no
> son "código bueno esperando a ser conectado". Son **código escrito para otra
> máquina** (`~/daniela-os`, comandos de Linux) y para **otra configuración**
> (una API key de Gemini que funcionaba). Conectarlas tal cual **rompería el
> arranque** del sistema que ahora mismo funciona con 387 rutas.
>
> **Qué he hecho en su lugar (Paso 1 HECHO):** el medidor que convierte las 31
> islas en una lista accionable → `/api/plugins/health`. 389 rutas, 23 tests
> nuevos, suite en 73. Detalle en la sección 6.

---

## 1. El plan decía `invoice_extractor`. Lo medí. No sirve como piloto.

`plugins/invoice_extractor.py` (133 líneas) hace algo genuinamente útil: busca
adjuntos de facturas en Gmail y los archiva en Drive. Pero **no puede funcionar
hoy**, por cuatro razones independientes:

| # | Problema | Evidencia |
|---|---|---|
| 1 | Apunta a una carpeta que **no existe** | `BASE_DIR = ~/daniela-os` → **no existe** en esta máquina |
| 2 | Necesita un **token OAuth que no existe** | Espera `~/daniela-os/token.json`. No está |
| 3 | El token hay que **generarlo con navegador** | `credentials.json` es un cliente OAuth `installed`, **no** un token. Requiere autorización interactiva → **solo el usuario** |
| 4 | Escribe la memoria en un **vault equivocado** | `save_to_vault()` escribe en `~/daniela-os/memory_vault.json`, **no** en el del repo |

Consecuencia de conectarlo: la ruta respondería **siempre** con
`❌ Falta token.json`. Una ruta que solo sabe fallar es peor que no tenerla.

---

## 2. Y esto no es un caso aislado: es el patrón de las 32 islas

### 2.1 Apuntan a `~/daniela-os`, que no existe

**18 de los 32** plugins (56 %) hardcodean `os.path.expanduser("~/daniela-os")`
como directorio base. Esa carpeta **no existe en este PC**.

### 2.2 Dan por hecho que corren en Linux/Android

`plugins/net_audit.py` es el ejemplo más claro:

```python
subprocess.run(['ip', 'neighbor'], ...)   # 'ip' no existe en Windows
```

Medido: `which ip` → nada. `arp -a` sí funciona. El código no elige: asume
Linux. Otros usan `pm`, `dumpsys` o `termux` — todos de Android.

### 2.3 🔴 **6 plugins NO SE PUEDEN IMPORTAR** (y esto es lo grave)

Probé a importar los 32. **25 entran, 6 mueren al importar**:

```
audio_listener.py       ValueError: No API key was provided
file_analyzer.py        ValueError: No API key was provided
memory_analyzer.py      ValueError: No API key was provided
security_cam.py         ValueError: No API key was provided
vision.py               ValueError: No API key was provided
visual_sentinel.py      ValueError: No API key was provided
```

**La causa, en una línea de código:**

```python
client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))   # ← nivel de MODULO
```

Tres defectos en esa línea:

1. **Se instancia al importar.** Si la clave falta o no vale, el `ValueError`
   sube durante el `import`. Sobre un módulo conectado a `daniela_os.py`, eso
   **tumba el arranque entero**.
2. **`GOOGLE_API_KEY` es literal `YOUR_VALUE_HERE`** en el `.env` (ver
   `INVENTARIO-CLAVES.md`). Así que hoy siempre falla.
3. **El modelo no existe:** `model="gemini-3.7-flash"`. No es un modelo real.

> ⚠️ Este es **exactamente el mismo defecto** que dejó la suite de tests sin
> ejecutar ni un test en A-1: código con efectos a nivel de módulo que aborta al
> importarse. Aparece en dos sitios distintos del repo. **Es sistémico.**

---

## 3. Por qué esto cambia el orden del plan

El plan asumía: *isla = funcionalidad ya escrita, solo falta la tubería*. Medido,
la realidad es: *isla = funcionalidad escrita para otro entorno; falta la
tubería **y** que sea reejecutable aquí*.

Conectar una isla "tal cual" tiene **dos caminos, y ninguno es el que estaba
previsto**:

| Camino | Qué implica | Riesgo |
|---|---|---|
| **A. Adaptar** la isla a este entorno | Quitar rutas absolutas, portar comandos, hacer el cliente perezoso | Trabajo real, pero acotado y **verificable con tests** |
| **B. Conectar sin adaptar** | Registrar el blueprint y cruzar los dedos | 🔴 **Tumba el arranque** (los 6 que no importan) |

---

## 4. Lo que SÍ propongo hacer, y en qué orden

### Paso 1 · `plugins/health` — el piloto correcto (yo, ahora)

En vez de conectar una isla rota, **construyo la herramienta que hace medible el
estado de las 32 islas**: un módulo que las importa una a una, captura el error
de cada una, y expone el resultado en una ruta. Es pequeño, no necesita
credenciales, y **funciona el primer día**.

Por qué este y no otro:
- **No depende de nada externo** → funciona hoy, no "cuando arregles las claves".
- **Convierte 32 incógnitas en una lista accionable.** Hoy nadie sabe cuáles de
  las 32 islas son rescatables sin probarlas a mano.
- **Es la red de seguridad**: cuando adapte la primera isla de verdad, este
  módulo me dirá si la rompí.
- **Aporta rutas reales** (no un stub): `/api/plugins/health` y
  `/api/plugins/health/<nombre>`.

### Paso 2 · Adaptar UNA isla de verdad — ✅ **HECHO (2026-09-15)**

👉 **Documentado en `docs/B1-PASO2-INTEGRITY-GUARD.md`**

**Se eligió `integrity_guard`.** Se leyeron las tres candidatas antes de decidir:

| Candidata | Veredicto |
|---|---|
| `memory.py` | ❌ **duplicaría** `memory_vault.py` + `memory_semantic.py`, que ya funcionan |
| `scheduler.py` | ❌ hace `import plugins.X` y **ese paquete no existe** |
| **`integrity_guard.py`** | ✅ **aporta algo que el repo NO tiene** |

No vale `epic-pc/file-integrity/file_integrity.py` como sustituto: aquello es un
**auditor** (escanea y deja un registro), esto es un **detector** (falla cuando
algo se movió). Son complementarios.

Resultado: `agents/integrity_guard.py` + shim, **393 rutas** (389 + 4),
**40 tests nuevos** → suite en **113 verdes**. Sellado en 0.46 s, verificado en
0.29 s sobre 1640 ficheros. **Se arreglaron 4 defectos reales** del original
(el más grave: **no detectaba ficheros borrados**).

Otros descartes:
- ❌ `invoice_extractor` — token OAuth + navegador (solo tú)
- ❌ `net_audit` — comando `ip` de Linux, y además **solo lee la tabla ARP**, no
  aporta nada que el propio Daniela OS no tenga ya
- ❌ `cleaner` — **borra ficheros recursivamente** en una ruta que no existe.
  No lo voy a conectar sin que me lo pidas explícitamente.

### Paso 3 · Lo que NO haré sin que me lo pidas

- Conectar los 6 que **no importan** sin arreglarlos antes.
- Tocar `cleaner.py`: borra recursivamente y su ruta base no existe.
- Cambiar la `BASE_DIR` de los 18 a la fuerza. Si los plugins están pensados
  para el móvil (donde `~/daniela-os` sí existe en Termux), forzarlos al PC
  **rompería el móvil**. Hay que decidir el diseño, no parchearlo.
  **Ojo:** en `integrity_guard` **sí se aplicó** (un solo fichero, y el defecto
  apunta al repo). Eso es el piloto de la opción A; los otros 17 siguen esperando
  tu decisión.

---

## 5. La decisión de diseño que necesito de ti

Los 18 plugins con `~/daniela-os` apuntan a **Termux en el móvil** (donde el home
sí existe) pero se ejecutan **a veces en el PC**. Hay tres salidas y no elijo yo
porque depende de cómo quieres usar Daniela:

| Opción | Cómo | Cuándo conviene |
|---|---|---|
| **A. Variable de entorno** | `DANIELA_BASE_DIR` con defecto `~/daniela-os` | Si quieres que el **mismo código** corra en PC y móvil |
| **B. Rutas del repo** | `Path(__file__).parents[1] / "data"` | Si los plugins son **del PC** y el móvil va aparte |
| **C. Detectar entorno** | `es_android()` → elige la base | Si ambos, y quieres automático |

**Mi recomendación: A.** Es la que menos rompe, la más explícita, y ya hay
precedente en el repo (el `.env` decide rutas). Pero no la aplico sin tu OK,
porque afecta a 18 ficheros.

---

## 6. Estado final del Paso 1: ✅ HECHO (2026-09-14)

`agents/plugin_health.py` + shim `scripts/plugin_health.py`, registrado
en `daniela_os.py` con `except Exception`. **389 rutas** (387 + 2), verificado.

### Los números medidos, y por qué son tres y no uno

```
$ python agents/plugin_health.py --sin-importar
  31 plugins | 0 importan | 0 rotos | 31 sin probar (estatico)
     17  ADAPTAR      11  CANDIDATO      2  INCOMPLETO      1  RIESGO

$ python agents/plugin_health.py
  31 plugins | 25 importan | 6 rotos
     12  ADAPTAR      11  CANDIDATO      6  ROTO      2  INCOMPLETO
```

**Por qué la primera línea dice "0 rotos" y la segunda "6 rotos", y las dos son
correctas:** son preguntas distintas. La auditoría estática solo *lee* el código;
no intenta importarlo, así que no puede saber si está roto. Un "no lo he probado"
no es un "está roto".

Esto fue **un bug real**, no una decisión de diseño. La primera versión tenía un
solo contador `rotos = not importable`, y en modo estático `importable` se queda
en su valor por defecto `False` → los 31 salían `ROTO — arreglar antes de
conectar`. La salida *parecía* razonable y era completamente falsa. Arreglado de
dos formas: `_veredicto()` ahora mira `error_import` (el error real) en vez de
`importable`, y el resumen expone los **tres** estados por separado
(`importables` / `rotos` / `sin_probar`). Hay un test de regresión por cada uno.

> **Lección general:** un contador que mezcla "falló" con "no se evaluó" produce
> un informe que miente con seguridad. Separar los estados es lo que hace que el
> número signifique algo.

### El otro bug que encontraron los tests

`auditar_uno()` hacía `path.relative_to(_REPO_ROOT)` sin proteger. Lanza
`ValueError` en cuanto el fichero está **fuera** del repo, contradiciendo el
propio docstring del método ("nunca lanza"). Se veía solo con ficheros en
`tmp_path` — es decir, **solo con tests**. Arreglado con `_ruta_legible()`.

> Esto es exactamente el argumento para tener tests: los dos bugs de este módulo
> aparecieron únicamente porque los tests ejercitan caminos que el uso normal
> (auditar los 31 plugins del repo, siempre desde el repo) nunca toca.

### Rutas expuestas

| Ruta | Qué hace |
|---|---|
| `GET /api/plugins/health` | Resumen + estado de las 31 |
| `GET /api/plugins/health/<nombre>` | Detalle de una (nombre saneado con `fullmatch`) |

`?importar=false` da la auditoría estática (instantánea, sin subprocesos).
Medido: travesía de directorios (`../../etc/passwd`) → **404**; plugin
inexistente → **404**.

### Tests: 23 nuevos, suite en 73

`tests/agents/test_plugin_health.py` — 73 pasan (50 + 23), 0 fallos. Los tests escriben
**sus propios plugins falsos** en `tmp_path` y parchean la constante
`PLUGINS_DIR`, de modo que la suite nunca importa los plugins reales (varios
tienen efectos secundarios al importarse).

---

## 7. Resumen en una frase

**`invoice_extractor` no es un piloto válido** (necesita OAuth interactivo y una
carpeta inexistente), y **las 32 islas no son "código listo sin conectar"** sino
*código escrito para otra máquina* — 18 apuntan a `~/daniela-os`, 6 ni siquiera
se importan. Así que en vez de conectar una isla rota, **he construido el
medidor del estado de las 32** (`/api/plugins/health`), que funciona hoy y
convierte el problema en una lista accionable.
