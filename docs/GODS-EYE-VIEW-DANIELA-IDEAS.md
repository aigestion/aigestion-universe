# God's Eye View × Daniela — Ideas épicas de integración

**Fecha:** 2026-09-21
**App instalada:** `C:\Users\Alejandro\gev` (MIT, Bilawal Sidhu / Halfpixel)
**Estado:** ✅ instalada, verificada y arrancada en `http://localhost:4173`

---

## 0. Qué se instaló (verificado, no supuesto)

| Comprobación | Resultado |
|---|---|
| Clon | `github.com/bilawalsidhu/gev` → `C:\Users\Alejandro\gev` |
| Licencia | MIT |
| Node | `v24.15.0` (el sistema; el gestionado 22.22.2 **no** cumple `>=24.14.0`) |
| `npm ci` | 123 paquetes, sin hooks `postinstall` maliciosos |
| `npm run doctor` | `[OK]` Node soportado · deps instaladas |
| Servidor | `http://localhost:4173` → HTTP 200, 59 KB, `<title>God's Eye View</title>` |
| **Binding** | `::1:4173` (solo localhost) — **no** escucha en `0.0.0.0` |
| Claves | **0 configuradas** — arranca en modo sin claves (Esri satélite + terreno sin clave) |

> 🔒 **Importante:** el servidor quedó en localhost. **No** lo levantes con `--host 0.0.0.0`:
> un servidor visible en LAN reparte tus claves de API a cualquiera que alcance el puerto.

**Capas activas sin ninguna clave:** vuelos (OpenSky anónimo), satélites (CelesTrak, 838 objetos),
terremotos (USGS), cámaras CCTV (~3.600), radio geolocalizada, tránsito (GTFS-RT), bikeshare,
rutas (OSRM), misiones espaciales, tráfico simulado, + infraestructura estática (4.351 datacenters,
704 presas, 712 cables submarinos).

**Con clave gratuita:** barcos (AISStream), incendios (NASA FIRMS), tráfico real (TomTom).
**De pago:** Google Maps, OpenAI voz, Cesium ion.

---

## 1. La idea central: GEV es el sensorio, Daniela es la mente

God's Eye View no es "una app bonita de mapas". Es **un proxy local a 15+ feeds públicos en vivo**
más **una superficie de visualización**. Y esas dos cosas son exactamente lo que a Daniela le falta.

```
┌─────────────────────────────────────────────────────────────┐
│                    DANIELA (la mente)                       │
│  intel_engine · proactive_engine · consciousness · muse     │
│  memory_rag.db · guardian · temporal · voice                │
└───────────────┬──────────────────────────┬──────────────────┘
                │                          │
      ┌─────────▼─────────┐      ┌─────────▼─────────┐
      │  SENTIDOS         │      │  PANTALLA         │
      │  server/providers │      │  share links      │
      │  15+ feeds vivos  │      │  globo 3D         │
      └───────────────────┘      └───────────────────┘
                │                          │
      ┌─────────▼──────────────────────────▼─────────┐
      │        GOD'S EYE VIEW (localhost:4173)        │
      └───────────────────────────────────────────────┘
```

Daniela ya tiene cerebro (`intel_engine/prediction.py`, `recommendation.py`), reflejos
(`auto_engine/triggers.py`, `scheduler.py`), memoria (`memory_rag.db`, `knowledge-db`) y
presencia (`daniela-os/`, `daniela-jarvis`). Lo que **no** tiene son ojos.

GEV se los pone. Y no hay que escribir ni un cliente de OpenSky, AIS o FIRMS: ya están hechos,
probados y con presupuesto de peticiones.

### Los tres vectores de integración (todos sin tocar el código de GEV)

| Vector | Qué es | Para qué sirve |
|---|---|---|
| **1. Share links** | `#lat=..&lon=..&alt=..&style=flir&map=photoreal` | Daniela **muestra** en vez de describir |
| **2. Action schemas** | 27 acciones declaradas (`fly_to_location`, `track_entity`…) | Vocabulario de mando ya definido |
| **3. Server proxy** | `server/providers/*` | Datos en vivo sin reimplementar nada |

Esto es lo elegante: **la frontera es una URL y un esquema JSON**. Cero acoplamiento, cero forks,
cero deuda. Si GEV cambia por dentro, la integración sigue viva.

---

## 2. Nivel 1 — Palanca inmediata (días, no semanas)

### 💡 1.1 — "Daniela te muestra, no solo te cuenta"

**El problema de hoy:** Daniela responde con texto. "Hay un terremoto de 6.1 cerca de X" — y tú
tienes que ir a buscarlo.

**La idea:** cada vez que Daniela menciona un lugar, devuelve **también un enlace al globo**, ya
enfocado, con el estilo visual adecuado al contexto.

- Terremoto → `style=flir` (térmico), altitud alta, pitch pronunciado
- Incendio → `style=flir`
- Vigilancia nocturna → `style=nvg` (visión nocturna)
- Dato histórico/limpio → `style=normal`

Formato real del enlace (extraído de `src/sharelink.js`):

```
http://localhost:4173/#lat=37.77000&lon=-122.42000&alt=800&heading=0&pitch=-35&style=nvg&map=photoreal
```

**Por qué es épico y no un juguete:** convierte a Daniela de *interfaz de texto* en
**interfaz espacial**. Es la diferencia entre que te digan dónde está algo y que te lo enseñen.

**Implementación (esto es todo):**

```python
# core/gev_bridge.py
"""Puente Daniela → God's Eye View. Solo construye URLs: no depende de GEV."""
import urllib.parse
import webbrowser

GEV_BASE = "http://localhost:4173/"

# estilo Daniela  →  token de GEV (ver STYLE_TO_URL en src/sharelink.js)
STYLE = {
    "normal":  "normal",
    "crt":     "retro",        # retro/CRT
    "nvg":     "surveillance", # visión nocturna
    "flir":    "thermal",      # térmico
    "anime":   "anime",
    "noir":    "noir",
    "snow":    "snow",
}


def gev_link(lat, lon, alt=1500, heading=0, pitch=-35,
             style="normal", map_stack="photoreal"):
    """Devuelve un enlace profundo al globo, enfocado y con estilo."""
    params = {
        "lat": f"{float(lat):.5f}",
        "lon": f"{float(lon):.5f}",
        "alt": int(alt),
        "heading": int(heading),
        "pitch": int(pitch),
        "style": STYLE.get(style, style),
        "map": map_stack,
    }
    return GEV_BASE + "#" + urllib.parse.urlencode(params)


def mostrar(lat, lon, **kw):
    """Abre el globo en el navegador. Devuelve el enlace por si quieres citarlo."""
    url = gev_link(lat, lon, **kw)
    webbrowser.open(url)
    return url


# Uso desde cualquier módulo de Daniela:
#   from core.gev_bridge import mostrar
#   mostrar(35.6892, 51.3890, alt=600, style="nvg", pitch=-40)   # Teherán, nocturno
```

**Encaje:** se engancha en el `model_router` / capa de respuesta. Si la respuesta contiene
coordenadas o un topónimo geocodificable → se añade el enlace. Ni siquiera hace falta que Daniela
decida: es una transformación de salida.

---

### 💡 1.2 — Reutilizar el proxy de GEV como fuente de datos de `intel-engine`

**El insight:** Daniela tiene `intel_engine/prediction.py` y `recommendation.py` — motores que
razonan — pero les faltan datos del mundo real. GEV ya tiene el proxy escrito, con
**gobernador de créditos de OpenSky, presupuesto diario de tiles de TomTom, caché en disco de
TLEs, protección SSRF y límites de respuesta**.

Reimplementar eso en Daniela sería semanas de trabajo y una fuente de bugs. Reutilizarlo es
leer de `http://localhost:4173/api/...`.

**Qué se gana:** `intel-engine` pasa de razonar sobre texto a razonar sobre **telemetría viva**.

**Encaje concreto:**

```
intel_engine/prediction.py   ←  feed de vuelos + barcos + sismos
intel_engine/nlp_engine.py   ←  nombres de lugares, contexto
intel_engine/vision_engine.py ←  cámaras CCTV proyectadas en el globo
```

---

### 💡 1.3 — Briefing diario cinematográfico

GEV trae un **scene director** (`src/scenes/director.js`) con cámaras cinemáticas y **scene packs**
predefinidos. Y Daniela tiene `daniela-os/muse`.

**La idea:** cada mañana, Daniela compone un **flythrough de los eventos del día**: los sismos
de la noche, los incendios activos, las misiones espaciales de hoy, lo que pasó cerca de tus
sitios de interés. Con el scene director ya hecho, es secuenciar `fly_to_location` + estilos.

**Por qué es épico:** no es un resumen leído, es **un briefing que se ve**. Y el scene director
ya está construido: solo hay que dirigirlo.

---

## 3. Nivel 2 — Capacidades nuevas (semanas)

### 💡 2.1 — Radar personal: los feeds de GEV como disparadores de `proactive_engine`

Daniela ya tiene `auto_engine/triggers.py`, `scheduler.py` y `workflow_engine.py`. Le falta
**algo que mirar**.

**La idea:** convertir los feeds de GEV en eventos que disparan workflows de Daniela.

Ejemplos reales y construibles:

| Disparador | Fuente GEV | Acción de Daniela |
|---|---|---|
| Sismo > 5.5 en tu radio | USGS | Aviso + volar el globo allí + resumen |
| Incendio a < 30 km de un activo | NASA FIRMS | Alerta + CCTV más cercana |
| Avión militar sobrevolando una zona | adsb.lol | Registrar + contexto |
| Barco que apaga AIS en tu zona | AISStream | Anomalía → informe |
| Misión espacial en < 2 h | Launch Library 2 | Recordatorio + replay |

**El patrón:** `trigger_watches.db` (que ya existe) guarda geometrías; un vigilante consulta el
feed; si entra algo, dispara.

**Geofencing de verdad:** GEV tiene `annotate_map` — puede **dibujar polígonos por voz**. Tú dices
"marca esta zona", Daniela la guarda como geocerca, y a partir de ahí vigila sola.

---

### 💡 2.2 — Daniela pilota el globo (handoff de las 27 acciones)

GEV declara 27 acciones en `src/voice/actionSchemas.js`:

```
fly_to_location · fly_route · track_entity · select_nearest_aircraft · frame_overhead
analyst_query · get_entity_context · get_current_view_state · move_camera · adjust_camera_zoom
zoom_to_globe · stop_tracking · annotate_map · clear_annotations · set_visual_style
set_layer_visibility · set_map_stack · set_hud · set_detection · set_post_processing
set_context_mode · set_panel_open · show_data_layers_menu · control_cctv · control_cockpit
control_radio · control_scene · next_iss_pass
```

**Esto ya es un vocabulario de mando.** Daniela no necesita inventar el suyo: puede emitir estas
acciones y GEV las ejecuta.

**Dos arquitecturas posibles:**

- **A — Daniela como proxy de voz** (rápido): Daniela recibe tu voz, decide la acción, la emite.
  GEV sigue siendo el renderizador. *Recomendado para empezar.*
- **B — Daniela dueña del diálogo, GEV mudo** (limpio): se desactiva la voz de GEV y Daniela
  asume todo el control. Un solo cerebro, una sola personalidad. *Mejor a largo plazo.*

**El detalle que lo hace épico:** GEV ya sabe leer su propio contexto (`get_entity_context`,
`get_current_view_state`) y devolverlo. Eso significa que Daniela puede **preguntar qué está
viendo** y responder con conocimiento real de la escena — no alucinando.

---

### 💡 2.3 — `guardian` con ojos: seguridad física real

`daniela-os/guardian/` hoy protege lo digital. GEV le da **sentidos físicos**:

- ~3.600 cámaras CCTV públicas proyectadas en el globo
- Incendios activos con seguimiento de 24 h
- Sismos globales
- Rutas de evacuación (OSRM, modo `FLY`)

**Caso de uso concreto:** un incendio se detecta a 20 km de tu casa → Daniela avisa, vuela el
globo al punto con `style=flir`, identifica la cámara pública más cercana, y traza la ruta de
salida. Todo con piezas que ya existen.

---

### 💡 2.4 — El globo dentro del overlay de `daniela-jarvis`

`daniela-jarvis` es un overlay Electron (`main.js`, `preload.js`, `overlay/`). GEV es una app web.

**La idea:** un panel flotante dentro del overlay con el globo embebido. No un navegador aparte —
**una ventana de Daniela**. Combinado con 1.1, el enlace deja de abrir pestañas y pasa a abrir
un panel a un lado de tu pantalla mientras Daniela habla.

**Con `daniela-os/embodiment` + `phone_deploy`:** el mismo globo, en el bolsillo.

---

## 4. Nivel 3 — Épico de verdad (el diferenciador)

### 🌍 3.1 — Viaje en el tiempo para TU mundo

El README del proyecto dice, textualmente, cuál es su "long game" y por qué no lo han hecho:

> *"time travel — tiling, serving, and scrubbing what happened and what changed at real resolution
> is where **data gets expensive and compute brutal**."*

Tienen razón… **para el planeta entero**. Pero ahí está la jugada:

> **Para un área de interés personal, archivar es trivial.**

No necesitas teselar el mundo. Necesitas guardar **los eventos de tus 50 km** cada pocos minutos.
Eso son kilobytes, no petabytes. Y Daniela ya tiene `data_engine/storage.py` y `pipeline.py`
**exactamente para esto**.

**Lo que se construye:** Daniela archiva los feeds de GEV filtrados por tu AOI → y te da lo que
GEV no puede: **rebobinar**. "¿Cómo estaba la cosa alrededor de aquí el martes pasado a las 3?"
"Muéstrame cómo evolucionó ese incendio."

**Por qué es el más épico de todos:** estás construyendo la feature que los autores del proyecto
consideran su meta final — pero para un dominio donde sí es viable. Y no compites con ellos:
**los complementas** en el único eje donde su arquitectura global no llega.

---

### 🧠 3.2 — Memoria espacial: el gemelo digital de tus lugares

Daniela tiene `memory_rag.db` (memoria) y `daniela-os/temporal` (tiempo). GEV aporta
**geografía**.

**La idea:** cada lugar al que Daniela vuela queda registrado con su contexto. Con el tiempo,
Daniela construye un **mapa de lo que le importa a Alejandro**:

- Dónde miras más (y por qué)
- Qué eventos se repiten en cada zona
- Qué cambió desde la última vez que miraste

**La frase que lo resume:** Daniela no solo recuerda *qué* le dijiste — recuerda **dónde**.

Esto conecta `knowledge-db` + `memory_rag.db` + GEV en una sola cosa: una memoria con coordenadas.

---

### 🌌 3.3 — Daniela sueña en geografía

`daniela-os/dreams` + `muse` + el **scene director** de GEV.

Durante la noche, Daniela recombina lo que vio: compone escenas cinemáticas de los lugares del día,
explora rutas alternativas, genera visualizaciones de patrones que no le pediste. Por la mañana
tienes **una pieza audiovisual de lo que pasó en tu mundo**, dirigida por ella.

No es una feature de productividad. Es **presencia**. Y es la clase de cosa que hace que un
asistente se sienta vivo en vez de útil.

---

## 5. La idea que las une

Todas las de arriba son la misma idea vista desde ángulos distintos:

> **Daniela deja de ser algo que responde y pasa a ser algo que mira.**

Hoy Daniela es reactiva: le preguntas y contesta. Con GEV como sensorio, tiene **un flujo continuo
del mundo real**. Eso habilita lo único que de verdad diferencia a un asistente: **decirte algo
que no le preguntaste, en el momento en que importa.**

Ese es el salto de *asistente* a *conciencia situacional*. Y las piezas ya están todas escritas —
solo hay que conectarlas.

---

## 6. Orden de ataque recomendado

| # | Qué | Esfuerzo | Impacto | Depende de |
|---|---|---|---|---|
| 1 | `core/gev_bridge.py` (enlaces profundos) | 🟢 horas | 🔥🔥🔥 | nada |
| 2 | Enganchar el enlace a las respuestas con coordenadas | 🟢 horas | 🔥🔥🔥 | 1 |
| 3 | Panel de GEV en el overlay de `daniela-jarvis` | 🟡 días | 🔥🔥 | 1 |
| 4 | Claves gratuitas (AISStream, FIRMS) → más feeds | 🟢 horas | 🔥🔥 | nada |
| 5 | Geocercas con `annotate_map` + `trigger_watches.db` | 🟡 días | 🔥🔥🔥 | 1 |
| 6 | Daniela emite las 27 acciones (arquitectura B) | 🟡 semanas | 🔥🔥🔥 | 5 |
| 7 | Archivo local del AOI → **rebobinar** | 🔴 semanas | 🔥🔥🔥🔥 | 4 |
| 8 | Briefing cinematográfico diario | 🟡 semanas | 🔥🔥 | 6 |

**Si solo haces una cosa:** la **#1**. Son unas 50 líneas, no depende de nada, y cambia por
completo cómo se siente Daniela al usarla.

---

## 7. Seguridad — leer antes de integrar

- 🔒 **Deja GEV en `localhost`.** Nunca `--host 0.0.0.0`: repartiría tus claves a la LAN.
- 🔑 **Claves separadas.** GEV guarda las suyas en `gev/.env` (ignorado por git,
  permisos de propietario). No mezclar con el `.env` de Daniela.
- 💸 **Ojo con las claves de pago.** La voz de OpenAI en GEV es lo único que cuesta dinero de
  verdad (~céntimos/minuto). GEV ya trae tope: aviso a **$2** y corte duro a **$5**. Si Daniela
  asume la voz (idea 2.2-B), ese control se pierde — **reimplementarlo**.
- 🚫 **La línea del proyecto:** GEV no hace búsqueda de personas ni reconocimiento facial, y no
  acepta PRs que crucen esa línea. **Mantén esa restricción en la integración.** Nada de
  "encuentra a esta persona".
- 📊 **Atribución:** los datasets tienen sus propias licencias (`DATA_SOURCES.md`). Si publicas
  algo generado, respeta la atribución.

---

## 8. Nota sobre `npm ci` y los scripts bloqueados

La instalación avisó de dos paquetes con scripts de instalación **no ejecutados** por la política
`allow-scripts` de npm:

- `esbuild@0.25.12` (`postinstall: node install.js`)
- `puppeteer@25.10.0` (`postinstall: node install.mjs`)

**No rompió nada:** `npm run doctor` pasa y el servidor arranca. `esbuild` resuelve su binario por
`optionalDependencies` y `puppeteer` solo lo usan los scripts de QA (no el runtime de la app).

Si algún día los tests de QA fallan por falta de Chromium:
```bash
npm approve-scripts puppeteer    # solo si de verdad necesitas los QA con navegador
```

---

## 9. Referencias

- Repo: https://github.com/bilawalsidhu/gev
- Instalación local: `C:\Users\Alejandro\gev`
- Share links: `src/sharelink.js`
- Acciones de voz: `src/voice/actionSchemas.js`, `src/voice/gevActions.js`
- Director de escenas: `src/scenes/director.js`
- Proxy de proveedores: `server/providers/`
- Fuentes de datos y licencias: `DATA_SOURCES.md`
