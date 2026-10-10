# LIMPIEZA DEL `.ENV` — 5 claves que funcionaban POR ACCIDENTE

**Fecha:** 2026-09-14 · **Script:** `scripts/limpiar_env.py` · **Tests:** `tests/core/test_limpiar_env.py` (10)

---

## 1. Qué decía el plan, y qué había de verdad

El plan de `IDEAS-EPICAS-SIGUIENTES-PASOS.md` decía:

> *"Agrupar las 273 plantillas `YOUR_VALUE_HERE` bajo un comentario; unificar
> `PIXEL_TOKEN`/`PIXEL_GATEWAY_TOKEN` (confirmado: mismo valor)."*

Al medirlo, **las dos mitades de la propuesta estaban mal**:

| Propuesta | Lo que se midió |
|---|---|
| "Agrupar las 273 plantillas" | El fichero **ya está agrupado**: 63 bloques `# ── SECCIÓN ──`. Las plantillas no están sueltas, están dentro de su sección con su clave real al lado. Reagruparlas todas sería un diff enorme **sin ganancia**. |
| "Unificar `PIXEL_TOKEN` / `PIXEL_GATEWAY_TOKEN`" | 🔴 **NO se pueden unificar: son un ALIAS en uso.** El gateway de Termux lee `PIXEL_GATEWAY_TOKEN`; ~10 módulos leen `PIXEL_TOKEN`; y `ar_stage.py` hace **fallback entre las dos**. Borrar una rompe la cadena. |

Que el plan se equivoque **ya es costumbre** (van 4 veces: B-1 elección, B-1 rutas,
B-3, y esta). Pero esta vez la medición destapó algo **mejor** que lo planeado.

---

## 2. 🔴 El hallazgo de verdad: 5 claves definidas DOS veces

En un `.env`, **cuando una clave aparece dos veces, gana la ÚLTIMA**. Y aquí había
**15 claves duplicadas**, de las cuales **5 con valores en conflicto**:

| Clave | 1.ª aparición | 2.ª aparición (la que gana) |
|---|---|---|
| `GROQ_MODEL` | `YOUR_VALUE_HERE` (L25) | `llama-3.3-70b-versatile` (L717) |
| `GEMINI_MODEL` | `YOUR_VALUE_HERE` (L39) | `gemini-1.5-flash` (L716) |
| `OLLAMA_HOST` | `YOUR_VALUE_HERE` (L203) | `http://localhost:11434` (L721) |
| `SUPABASE_ANON_KEY` | `YOUR_VALUE_HERE` (L250) | `sb_publishable_5_hWa…` (L711) |
| `SUPABASE_URL` | `YOUR_VALUE_HERE` (L251) | `https://nbymcxvlcfyhebzjurml…` (L709) |

**En las 5, la plantilla va PRIMERO y el valor real va ÚLTIMO.**

### Por qué esto es un peligro y no una curiosidad

El fichero **funciona**, pero **solo por el orden de las líneas**. No hay nada que
lo garantice. Si alguien:

- **ordena el fichero alfabéticamente** (algo que hace cualquiera "para limpiarlo"),
- **borra lo que parece un duplicado**,
- o **genera el `.env` desde otra herramienta** que no respete el orden,

entonces `SUPABASE_URL`, `SUPABASE_ANON_KEY`, `GEMINI_MODEL`, `GROQ_MODEL` y
`OLLAMA_HOST` **vuelven a `YOUR_VALUE_HERE` EN SILENCIO**.

Es exactamente el mismo patrón que ya ha mordido a este proyecto dos veces con
`DANIELA_PIN` y las `PIXEL_*`: **una clave que llega vacía o con plantilla sin dar
ningún error**. Y este es peor, porque el fallo no está en el valor: está en que
**el orden importa y nadie lo sabe**.

**Alcance medido:** 16 ficheros `.py` leen estas 5 claves
(`GEMINI_MODEL` 7, `SUPABASE_URL` 4, `OLLAMA_HOST` 4, `SUPABASE_ANON_KEY` 1).

---

## 3. Qué hace `scripts/limpiar_env.py`

```bash
python scripts/limpiar_env.py --dry-run   # solo informa
python scripts/limpiar_env.py --aplicar   # escribe (con copia .bak y check)
```

1. **Deja UNA sola línea activa por clave**, con el valor que gana.
2. 🔴 **NO borra NINGUNA línea.** La aparición descartada se **comenta**:
   ```
   # (descartado arriba, ganaba la ultima) GROQ_MODEL=YOUR_VALUE_HERE
   ```
   Así el cambio es auditable y reversible, y el recuento de líneas **no baja**
   (726 → 726). Borrar es donde está el riesgo; en el fichero más crítico del repo
   no se borra nada.
3. **No mueve las claves de sitio.** Reordenar 561 claves sería un diff ilegible.
4. **Copia de seguridad** `.env.env.bak-envclean-<fecha>` — que cae en la regla
   `*.env.bak-*` del `.gitignore` (**verificado con `check-ignore --no-index`**;
   un backup con claves reales jamás debe poder commitearse).

### El invariante (la parte que de verdad importa)

Antes y después se cargan las dos versiones con `dotenv_values` y se exige que el
resultado sea **idéntico**. Si no lo es, **restaura y sale con código 1**.

⚠️ **Detalle que me mordió:** `dotenv_values()` devuelve un **`OrderedDict`**, y
`OrderedDict.__eq__` **SÍ mira el orden** (a diferencia de un `dict` normal).
La primera ejecución dio "NO ES EQUIVALENTE" con **0 diferencias de valor**: era
falso positivo, porque comentar `GROQ_MODEL` en la L25 hace que esa clave entre
más tarde en el OrderedDict. **A `load_dotenv()` el orden le da igual** — es como
lee la app — así que comparar por orden era exigir de más. Se compara
`dict(...) == dict(...)`.

> Lección: **un test que exige de más rechaza cambios buenos.** El invariante tiene
> que medir lo que le importa al consumidor real, no lo que es fácil de comparar.

### El camino peligroso está probado

El script tiene una rama de "restaurar si algo va mal", y esa rama **se probó
saboteándola a propósito** (un `dotenv_values` falso que se inventa una diferencia
en la segunda llamada). Resultado: detectó el fallo, imprimió la clave culpable
(`A: '2' -> 'SABOTAJE'`), **restauró el fichero byte a byte** y devolvió 1.

Un test que solo cubre el camino feliz no vale nada en un script que reescribe el
`.env`.

---

## 4. Verificación

```
Antes :  726 líneas · 561 claves · 5 en conflicto
Después: 726 líneas · 561 claves · 0 en conflicto

check_env.py        -> 561 claves, claves críticas OK
rutas               -> 397 (sin cambios)
tests               -> 162 verdes (152 + 10 nuevos)
claves perdidas     -> 0 · claves nuevas -> 0 · valores distintos -> 0
idempotente         -> 2.ª pasada: "No hay duplicados con valores en conflicto"
Runtime (load_dotenv): las 8 claves comprobadas resuelven al valor REAL
                        (ninguna a YOUR_VALUE_HERE ni vacía)
```

Copia de seguridad: `.env.env.bak-envclean-20260915_003151` (**ignorada por git**).

---

## 5. Lo que NO se hizo, y por qué

- **No se unificaron `PIXEL_TOKEN` / `PIXEL_GATEWAY_TOKEN`.** Medido: son un alias
  con fallback en `ar_stage.py` y las leen módulos distintos de los dos lados.
  **La propuesta del plan era incorrecta.** Se dejan las dos, con nota.
- **No se reagruparon las 273 plantillas.** El fichero ya tiene 63 secciones.
- **No se tocó `config/.env`** (557 claves). El `.env` de la raíz es el que se carga;
  cambiar los dos a la vez multiplica el riesgo sin necesidad.
- **No se borró ninguna clave**, ni duplicada ni plantilla.

## 6. 🔍 Segunda pasada: `config/.env` — auditado, y da 0

Al limpiar el `.env` de la raíz quedó pendiente auditar `config/.env` (557 claves).
Hecho, y el resultado **no es lo que parecía**:

### Lo que se midió

| Comprobación | Resultado |
|---|---|
| Duplicados **en conflicto** en `config/.env` | **0** (los 7 duplicados que tiene son `VITE_*` con el valor idéntico) |
| ¿Está trackeado en git? | **No.** Ignorado por `config/.gitignore:2` → **nunca se filtró** |
| **¿Cuántas claves aporta que no esté ya la raíz?** | 🔴 **0. Ninguna.** |

**Hipótesis que se descartó:** pensé que `config/.env` tenía el *mismo* bug de orden
(real primero, plantilla después → gana la plantilla, y el valor se pierde). **Es falso.**
Esas 5 claves aparecen **una sola vez** en `config/.env`, simplemente **sin rellenar**:
es una foto más antigua (12 sep) que nunca se actualizó.

**Lo importante:** el `.env` de la raíz es un **superconjunto estricto**. Las 283 claves
con valor de `config/.env` están **todas** también en la raíz.

### Por qué sigue siendo un riesgo (menor, pero real)

`daniela_os.py` carga **los dos** a propósito, y el comentario dice:

> *"el de la raiz tiene prioridad y `config/.env` rellena los huecos"*

Medido: **rellena 0 huecos.** Es decir, hoy `config/.env` es **peso muerto** que:

1. **Duplica 283 credenciales** en disco sin aportar nada.
2. Tiene **5 claves en PLANTILLA** (`SUPABASE_URL`, `SUPABASE_ANON_KEY`, `GEMINI_MODEL`,
   `GROQ_MODEL`, `OLLAMA_HOST`) que **activarían un valor malo** si algún día se quitara
   la clave de la raíz — porque `load_dotenv` **sí** rellenaría el hueco, con la plantilla.
3. Y el comentario del código afirma una función ("rellena huecos") que **ya no cumple**,
   así que el siguiente que lea ese comentario dará por hecho algo falso.

### Qué se hizo (conservador)

**No se ha borrado `config/.env`** — puede tener usos fuera de este arranque, y borrar
283 credenciales sin permiso no es mi decisión. Lo que se ha hecho es **convertir la
afirmación del comentario en una comprobación en runtime**:

```
[env] config/.env no aporto ninguna clave nueva (el .env de la raiz ya las tenia todas).
```

`daniela_os.py` ahora **mide** cuántas claves aporta el segundo fichero y lo dice al
arrancar. Si algún día aporta alguna, lo verás en consola. Un fichero que "rellena
huecos" y no rellena ninguno acaba pudriendo en silencio; ahora no puede.

La lógica se probó **en los dos sentidos**: con un `config/.env` de prueba que sí
aportaba una clave, el contador la detectó. No basta con ver "0" y creerse el 0.

### Decisión que te toca a ti

Tres opciones, de menor a mayor agresividad:

| Opción | Qué implica |
|---|---|
| **A. Dejarlo como está** | Ahora avisa en consola. Coste 0, riesgo 0. El fichero sigue duplicando credenciales |
| **B. Rellenar los 5 huecos** | Copiar los 5 valores de la raíz a `config/.env` para que deje de tener plantillas peligrosas. Sigue siendo redundante, pero deja de ser una trampa |
| **C. Borrarlo** | Elimina 283 credenciales duplicadas y el riesgo de la capa confusa. **Requiere comprobar antes** que nada más lo usa (yo solo he mirado este repo) |

**Mi recomendación: B.** Es barato, elimina la trampa de las plantillas, y no rompe
nada de lo que hoy funciona. C es más limpio pero toca un fichero que no es mío.

