# 🗣️ B-3 — Voz offline con Piper (2026-09-15)

> **El plan decía:** *"E27 (voz offline) está MEDIA HECHA: `voice_pipeline.py`
> existe con 9 rutas. Solo falta el motor."*
>
> **Medido:** las tres afirmaciones eran falsas. Había que arreglar la premisa
> antes de tocar código.

---

## 1. Lo que el plan decía, y lo que hay de verdad

| El plan decía | Real, medido |
|---|---|
| "9 rutas" | **4 rutas** reales (`/api/voice/{speak,listen,status,voices}`) |
| "media épica hecha" | El pipeline existe, **pero su motor de voz no es offline** |
| "solo falta el motor" | Faltaba el motor **y** el modelo **y** el binario de espeak |
| "usar edge-tts" | edge-tts **sí** está (7.2.8) — pero **no es offline** |

También: `stt_available` es **`false`**. `faster-whisper` **no está instalado**,
así que `POST /api/voice/listen` **no puede funcionar hoy** en el PC.

---

## 2. El problema real: edge-tts **no es offline**

El plan llamaba a esto "voz offline", pero el motor que hay instalado **no lo es**:

| | edge-tts (lo que había) | Piper (lo que se añade) |
|---|---|---|
| Dónde sintetiza | **Servidores de Microsoft** | **En tu CPU** |
| ¿Necesita internet? | **Sí, siempre** | **No** |
| El texto sale de tu máquina | **Sí** | **No** |
| Estabilidad | Cliente **no oficial** de un servicio interno de Edge; ya se ha roto por cambios del servidor | Versión fijada en `requirements.txt` |

Esto importa **en este repo en concreto**: el resto de Daniela OS funciona por red
local (`192.168.1.133`), así que exigir internet **solo para la voz** no cuadra.
Y en el móvil (Termux) ya se usa el TTS de Android, que sí es local — había una
incoherencia entre dispositivos.

---

## 3. Lo que se hizo

**`agents/piper_engine.py`** (+ shim `scripts/piper_engine.py`).

**Es aditivo, no sustitutivo.** No se tocó nada de `voice_pipeline.py`: edge-tts
sigue funcionando igual. Aporta **un motor más**, y el diseño es que si Piper no
está, se cae a edge-tts — nunca al revés.

| Ruta | Código | Qué hace |
|---|---|---|
| `GET /api/voice/piper/status` | 200 | Motor disponible, voces instaladas, cuáles están en memoria |
| `GET /api/voice/piper/voices` | 200 | Instaladas + recomendadas (`?catalogo=true` consulta la red) |
| `POST /api/voice/piper/prepare` | 200 / 400 / 500 | Descarga una voz (**internet una sola vez**) |
| `POST /api/voice/piper/say` | 200 / 400 | Texto → WAV |

### La voz elegida: `es_AR-daniela-high`

El catálogo de Piper tiene **176 voces**, **9 en español**. Se eligió
`es_AR-daniela-high` porque es una voz española **llamada daniela** y `high` es la
mejor calidad disponible. Encaja con el personaje.

### Medido en este PC (CPU, sin GPU)

```
Carga del modelo          2,59 s   (una vez, perezosa)
Síntesis de 3,19 s audio  1,53 s   → factor 0,5x (2x más rápido que real)
Modelo en disco           109 MB   (ignorado por git: regla `data/`)
Voces en español           9
```

**Verificado por HTTP** (la propia ruta devuelve las medidas, sin calcularlas a mano):

```json
POST /api/voice/piper/say  {"texto": "Hola, soy Daniela, y funciono sin internet."}
→ 200 {"ok": true, "motor": "piper", "voz": "es_AR-daniela-high",
       "sintesis_s": 1.35, "audio_s": 2.36, "factor_tiempo_real": 0.57,
       "bytes": 103980}
```

El factor está entre **0,5x y 0,6x** según la frase: **entre 1,7 y 2 veces más rápido
que tiempo real**. La medida se puede reproducir sin fiarse de este documento.

**La prueba que importa:** se sintetizó con **el socket bloqueado a propósito**
(`socket.socket = bloquea`) y funcionó. Eso es offline de verdad.

⚠️ **La carga es perezosa a propósito.** Cargar el modelo son ~2,6 s, y el
pipeline se construye al importar el módulo. Hacerlo en `__init__` retrasaría el
arranque del servidor por una función que a lo mejor nadie usa.

---

## 4. 🔴 Un bug real que encontraron los tests

**El error de síntesis se enmascaraba, y el fichero corrupto se quedaba en disco.**

`wave.open(..., "wb")` deja el fichero **sin cabecera válida** hasta que se cierra.
Si el motor falla a mitad, el `__exit__` del `with` intenta parchear la cabecera,
también falla, y **sustituye la excepción original**. Comprobado:

```python
with wave.open(p, "wb"):
    raise RuntimeError("ERROR DEL MOTOR")
# lo que ve el except:  wave.Error: '# channels not specified'
```

O sea: el usuario recibiría *"canales no especificados"* en vez de *"modelo
corrupto"*. El diagnóstico sería imposible.

Se arregla **cerrando a mano** (sin `with`), para poder quedarse con el error
original. Y de paso se **borra el WAV a medias**: `wave.open("wb")` crea el
fichero antes de que se escriba nada, así que un fallo dejaba un WAV de 0 bytes
en disco — un fichero corrupto **que parece bueno**, y alguien lo reproduciría
pensando que la voz está rota.

Los dos comportamientos tienen test de regresión.

> **Lección general:** `with wave.open(...)` **enmascara la excepción real**. Si
> envuelves algo que puede fallar, comprueba que el error que ves es el que
> ocurrió de verdad.

---

## 5. Tests: 39 nuevos, suite en 152

`tests/agents/test_piper_engine.py` — 152 pasan (113 + 39), 0 fallos.

**Regla propia de este fichero:** ningún test descarga un modelo ni sintetiza de
verdad (109 MB y segundos por frase dejarían la suite inutilizable). Se prueba la
lógica con el motor simulado, y hay **un** test marcado `slow` que sí sintetiza —
pero **se salta solo** si la voz no está descargada, para que la suite siga
corriendo en una máquina limpia.

| Test | Qué cubre |
|---|---|
| `test_un_fallo_de_sintesis_no_lanza_y_se_registra` | el bug del error enmascarado + el WAV a medias |
| `test_un_fallo...` (misma familia) | que el error real llegue al usuario |
| `test_sin_piper_el_estado_lo_explica_y_no_revienta` | que el módulo sea importable sin Piper |
| `test_la_plantilla_del_env_no_se_usa_como_ruta` | la trampa `YOUR_VALUE_HERE` |
| `test_prepare_rechaza_nombres_peligrosos` (×6) | el nombre se concatena a una **ruta** y a un **descargador** |
| `test_las_voces_se_leen_del_disco_no_de_una_lista` | copiar un `.onnx` a mano debe funcionar |
| `test_texto_demasiado_largo_se_recorta` | el límite de 1000 caracteres |
| `test_voices_no_consulta_el_catalogo_sin_pedirlo` | que la ruta sea offline salvo que se pida |

⚠️ **Saneado en `prepare`:** el nombre de la voz viene de JSON y se usa como
**nombre de fichero** y se pasa a un **descargador**. Se valida con
`re.fullmatch(r"[A-Za-z0-9_\-]{1,64}")`. Travesía de directorios → **400**.

---

## 6. Estado

- **`agents/piper_engine.py`** + shim, registrado en `daniela_os.py`
  con `except Exception` → **397 rutas** (393 + 4).
- `piper-tts==1.8.0` en `requirements.txt`.
- Voz descargada: `data/voice_pipeline/piper_voices/es_AR-daniela-high.onnx`
  (**109 MB, ignorada por git** — correcto).
- `onnxruntime 1.30.0`, `flatbuffers`, `pathvalidate` (dependencias).

### ⏳ Lo que sigue sin funcionar (y no es culpa de este módulo)

**`POST /api/voice/listen` no funciona en el PC**: `faster-whisper` no está
instalado (`stt_available: false`). La entrada de voz por micrófono es otro
trabajo — y en el móvil sí funciona por `termux-speech-to-text`.

**No se ha conectado Piper a `voice_pipeline.py`.** Es deliberado: este módulo
expone las rutas nuevas y deja el pipeline existente intacto. Cablear el
*fallback* (Piper primero, edge-tts si falta) es un cambio pequeño y aparte, y
conviene decidirlo con el resto de la arquitectura de voz.
