# 🔒 B-1 Paso 2 — la isla elegida: `integrity_guard` (2026-09-15)

> **Pregunta:** de las 11 islas `CANDIDATO`, ¿cuál se adapta primero?
>
> **Respuesta: `plugins/integrity_guard.py`.** Es la única de las tres finalistas
> que aporta algo que el repo **no tiene**, y no duplica nada.

---

## 1. Cómo se eligió (leyendo, no adivinando)

El diagnóstico de B-1 (Paso 1) dejó 11 plugins en `CANDIDATO`. Se leyeron los
tres que parecían más sustanciales:

| Candidata | Líneas | Veredicto | Por qué |
|---|---|---|---|
| `memory.py` | 26 | ❌ **Descartada** | **Duplicaría** lo que ya funciona: `memory_vault.py` (grafo + recall) y `memory_semantic.py` (vectorial, E-28). Sería el cuarto sistema de memoria |
| `scheduler.py` | 79 | ❌ **Descartada** | Hace `importlib.import_module(f"plugins.{nombre}")` y **ese paquete no existe** (no hay `plugins/__init__.py`, y `daniela_os.py` no importa `plugins.` para nada). Además ejecuta plugins a ciegas, incluido `cleaner.py`, que borra recursivamente |
| **`integrity_guard.py`** | 54 | ✅ **ELEGIDA** | Aporta detección de **mutación de ficheros**, que el repo no tiene en ninguna forma |

### Por qué no vale `epic-pc/file-integrity/file_integrity.py`

Existe (113 líneas) y usa sha256, así que *parece* que ya está cubierto. **No lo
está**, y la diferencia importa:

| | `epic-pc/file-integrity` | `integrity_guard` |
|---|---|---|
| Qué es | Un **auditor**: escanea y deja un registro histórico | Un **detector**: compara contra un sello y **falla** si algo cambió |
| Cuándo avisa | Cuando se lo pides | Cuando **algo se movió sin que lo pidieras** |
| Valor | Consulta | **Alarma** |

Son complementarios. El auditado responde *"enséñame lo que hay"*; este responde
*"esto no estaba así"*.

---

## 2. Por qué esto importa **en este repo concreto**

No es una utilidad genérica. Este proyecto tiene un historial documentado de
cambios que nadie hizo a propósito:

- El merge del PR #109 **resucitó 226 copias** de módulos en la raíz.
- `.gitignore` **desapareció** una vez.
- El `.env` de la raíz se **sobrescribió** con 12 claves; las demás quedaron
  vacías **sin dar error** (`DANIELA_PIN`, `GEMINI_API_KEY` y todas las `PIXEL_*`).
- 10 ficheros que no eran tests llamaban a `patch_backend_and_frontend()` **al
  importarse** y reescribían `app_daniela.py` e `index.html`.
- 935 ficheros con `SyntaxError` auto-generados por `autoprog_engine`.

Todos son exactamente la clase de cosa que esta herramienta caza. La causa
probable que devuelve cada alerta está escrita **para este repo**: "suele ser una
COPIA resucitada por un merge", no "fichero corrupto".

---

## 3. Lo que se arregló del plugin original

El original tenía 54 líneas y **cuatro defectos reales**, no de estilo:

### 🔴 1. `os.walk(BASE_DIR)` sin filtrar

Recorrería `.venv/` (miles de ficheros), `.git/` (**1,9 GB**) y `node_modules/`.
Medido: con los filtros puestos son **1638 ficheros**; sin ellos el manifiesto
pasaría de cientos a decenas de miles.

Se añaden `EXCLUDES` (por parte y por prefijo) y un **tope duro** de 5000
ficheros. El tope degrada a informe **parcial y lo dice** ("⚠️ el sello es
PARCIAL") en vez de colgarse: un manifiesto incompleto que parece completo es
peor que no tenerlo.

### 🔴 2. No detectaba ficheros **borrados**

El bucle original era:

```python
for path, h in current.items():        # ← solo recorre lo que EXISTE ahora
    if path not in stored: ...         # nuevo
    elif stored[path] != h: ...        # modificado
```

Si un `.py` se borra, **no está en `current`**, así que nunca entra al bucle y el
borrado pasa inadvertido. Ahora se comprueba en las dos direcciones.

### 🔴 3. Rutas a `~/daniela-os`

Que en este PC **no existe**. Ahora la base es la raíz del repo, y
`DANIELA_BASE_DIR` la puede cambiar — es la **opción A** del diseño pendiente,
aplicada aquí como piloto en un solo fichero.

### 🔴 4. El manifiesto se auditaba a sí mismo

Defecto descubierto **al probar el ciclo completo**, no al leer el código: el
manifiesto cae dentro del árbol que vigila, así que la escritura del sello
aparecía como `NUEVO` en la comprobación siguiente → **un falso positivo
permanente**, que además esconde los de verdad. Se excluye explícitamente.

También: `verify_integrity()` devolvía `None` cuando todo iba bien (nada que
decir). Ahora devuelve un resultado estructurado, que es lo que se puede poner
en un JSON.

---

## 4. Rutas expuestas

| Ruta | Código | Qué hace |
|---|---|---|
| `GET /api/integrity/status` | 200 | ¿Hay sello? ¿de cuándo? ¿sobre cuántos ficheros? |
| `POST /api/integrity/sign` | 200 / 500 | Sella el árbol. `?dry_run=true` cuenta **sin** escribir |
| `GET /api/integrity/check` | 200 / **409** / 400 | Audita contra el sello |
| `GET /api/integrity/manifest` | 200 / 404 | El manifiesto (hashes recortados a 12 chars) |

**Por qué `409` y no `500` en `check`:** *"hay cambios"* es un **resultado
legítimo**, no un fallo del servidor. El cliente puede distinguirlo. Y `400` si
no hay sello, que es un estado distinto de "está todo cambiado".

### Medido sobre el repo real (1640 ficheros)

```
SELLAR:    0.46 s
VERIFICAR: 0.29 s
```

El propio guard cazó los 4 ficheros de su primera sesión y **ningún otro**:

```
⚠️  4 cambios desde el sello.
  MODIFICADO  agents/integrity_guard.py
  MODIFICADO  daniela_os.py
  NUEVO       scripts/integrity_guard.py
  NUEVO       tests/core/test_integrity_guard.py
```

---

## 5. Tests: 40 nuevos, suite en 113

`tests/core/test_integrity_guard.py` — 113 pasan (73 + 40), 0 fallos.

**La regla más importante de esta suite:** ningún test puede escribir en el
manifiesto real. `POST /api/integrity/sign` es una ruta que **escribe**; si un
test la llamara contra el manifiesto de producción, dejaría el repo "sellado"
con hashes falsos y `/api/integrity/check` reportaría cambios inexistentes para
siempre. Hay un test dedicado a comprobarlo.

Incluye las regresiones de los cuatro defectos:

| Test | Defecto que cubre |
|---|---|
| `test_detecta_fichero_borrado` | #2 — el bucle solo miraba `current` |
| `test_el_manifiesto_nunca_se_audita_a_si_mismo` | #4 — el falso positivo eterno |
| `test_listar_ficheros_respeta_el_tope` + `test_sello_parcial_lo_avisa` | #1 — el tope |
| `test_plantilla_del_env_no_se_usa_como_ruta` | #3 — `YOUR_VALUE_HERE` |
| `test_exclusion_por_prefijo_no_confunde_mediacion_con_media` | el `startswith` ingenuo |
| `test_arbol_intacto_da_cero_alertas` | que no dé **falsos positivos** |
| `test_verificar_no_escribe_nada` | que una lectura no mute el estado |

> El test `test_exclusion_por_prefijo_no_confunde_mediacion_con_media` cubre una
> trampa concreta: `"mediacion.js".startswith("media")` es `True`, así que
> excluir `static/media` a pelo excluiría también `static/mediacion.js`. Se
> compara con barra (`static/media/`).

---

## 6. Estado

- **`agents/integrity_guard.py`** + shim **`scripts/integrity_guard.py`**.
- Registrado en `daniela_os.py` con `except Exception` → **393 rutas** (389 + 4).
- `data/integrity_guard/` ya está cubierto por la regla `data/` del `.gitignore`.
- **Pendiente:** sellar el árbol es una decisión tuya, no un efecto de instalar
  esto. `POST /api/integrity/sign` (o `python integrity_guard.py sign`).
