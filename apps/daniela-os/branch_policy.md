# Política de Ramas — Rescate Selectivo (E-16)

> Documento de decisiones. **No ejecutes nada de aquí sin leer la sección 6.**
> Todas las cifras de este documento se midieron contra la API de GitHub
> (`gh api .../compare/main...<rama>`), no contra el ref local: en este repo
> `.git/refs/remotes/origin/` no persiste y `git status -sb` miente.

Fecha del análisis: **2026-09-10** · HEAD de `main` en ese momento: `4389767f`

---

## 1. Foto real de las ramas

| Rama | Adelante | Detrás | Ficheros | + / − | ¿Ancestro común con `main`? | Secretos |
|---|---:|---:|---:|---|---|---:|
| **`main`** | — | — | — | — | — | **limpio** ✅ |
| `feature/darwin-api` | 4 | 329 | 300 | +31.985 / −19 | sí | **11** 🔴 |
| `universo-v1` | 189 | 54 | 63 | +2.856 / −8.612 | sí | **12** 🔴 |
| `ui-stable` | — | — | 3.850 | −270.100 | **NO** ⛔ | **1** 🔴 |
| `edicion-apk` | 0 | 128 | 0 | 0 | sí | 0 ✅ |

### Lo más importante que salió

- **`ui-stable` NO tiene ancestro común con `main`.** La API lo dice literalmente:
  `No common ancestor between main and ui-stable`. Son **dos historias no
  relacionadas**. Por eso aparecen esas −270.100 líneas: no es que "borre"
  código, es que el algoritmo de comparación no tiene base. **Un merge aquí no
  es arriesgado: es imposible sin reescribir todo.**
- **`feature/darwin-api` NO era segura**, al contrario de lo que teníamos
  apuntado. Tiene 11 secretos y 282 de sus 300 ficheros son `archive/`.
- **`edicion-apk` ya está contenida en `main`** (0 commits por delante). No
  aporta nada: es candidata a borrado.

---

## 2. Mapa de secretos

⚠️ No se escriben los valores aquí a propósito. Se identifican por fichero.

### `feature/darwin-api` — 11 secretos

| Fichero | Contenido |
|---|---|
| `.env` (189 B) | 1 clave Gemini (`AIza…`) |
| `.env.master` (30.682 B) | 10: 2 × Gemini `AIza`, 2 × Gemini `AQ.`, 4 × `sk-`, +2 |

### `universo-v1` — 12 secretos

| Fichero | Contenido |
|---|---|
| `.env` (95 B) | **limpio** ✅ |
| `.env.master` (30.682 B) | **el mismo fichero que en darwin-api**: 10 secretos |
| `.env.bak_1787041188` (72 B) | 1 clave Gemini |
| `.env.bak_1787041220` (107 B) | 1 clave Gemini |

> `.env.master` pesa exactamente 30.682 bytes en las dos ramas: es el mismo
> blob. Arreglarlo en un sitio no lo arregla en el otro.

### `ui-stable` — 1 secreto (duplicado)

| Fichero | Contenido |
|---|---|
| `data/client_secret.json` | `client_secret` de Google OAuth (`GOCSPX…`) |
| `data/credentials.json` | **el mismo** secreto duplicado |
| `config/client_secret.json` | sin secreto: solo `client_id` ✅ |

### Lo que NO está expuesto

La clave nueva que me pasaste (`AQ.Ab8RN6LqH…`) **no aparece** en ninguna de
estas ramas. Las dos claves `AQ.` que hay ahí son anteriores y distintas.

---

## 3. Decisión por rama

### `main` → única rama viva

Todo lo demás se congela o se rescatea. Nada se mergea en bloque.

### `feature/darwin-api` → RESCATE SELECTIVO

**Sí rescatar** (verificado: 0 `os.system`, 0 `shell=True`):

- `ai/brain_router.py` (300 líneas) — el valor real de la rama
- `ai/__init__.py`
- `.github/workflows/ci.yml` (29 líneas)

**No rescatar:**

- `aictl.py` → tiene **3 `os.system`**. O se arregla antes, o no entra.
- Los **282 ficheros de `archive/`** — son copias de seguridad viejas.
- `__pycache__/` (3 ficheros) — nunca deberían haberse commiteado.
- `ai/core/enhanced-ai/**/*.db` — bases de datos binarias en git.
- `.env`, `.env.master` → nunca.

### `universo-v1` → RESCATE SELECTIVO

**Sí rescatar** (el trabajo del universo 3D):

- `index_master_universo.html` (504 líneas)
- `index_master_draggable.html` (504 líneas)
- `index_sovereign_master.html` (504 líneas)
- `autofix_engine.py` (121), `swarm_planner.py` (55), `openrouter_core.py` (30)
- `start_daniela.sh` (32) — revisar a mano antes de usar

**No rescatar:**

- `.env.master`, `.env.bak_*` → secretos
- `output/` → 41 ficheros generados
- `daniela_multiuser.db` → binario

Ojo: esta rama **borra** `daniela_universe.html`, `view_3d_office.html`,
`voice_interface.html` y `full_ui_v2.html` respecto al ancestro común. Si ese
HTML te interesa, sácalo del historio **antes** de tocar nada.

### `ui-stable` → CONGELAR, NUNCA MERGEAR

Sin ancestro común. Se marca con un tag y se deja quieta como archivo. Si algún
día hace falta algo de ahí, se copia el fichero a mano, nunca con `git merge`.

### `edicion-apk` → BORRAR

0 commits por delante, 0 ficheros propios. Ya está todo en `main`.

---

## 4. Comandos exactos

### 0. Verificación antes de cualquier cosa

```bash
gh api repos/aigestion/AIGESTION-MONOREPO/compare/main...<rama> \
  --jq '"ahead=" + (.ahead_by|tostring) + " behind=" + (.behind_by|tostring)'
```

Si devuelve `No common ancestor`, **para**: esa rama no se puede mergear.

### 1. Rescate de darwin-api

```bash
# rama plana: los nombres con "/" fallan en silencio en este repo
git fetch origin feature/darwin-api:darwinapi-flat
git checkout -b rescate/darwin-brain-router
git checkout darwinapi-flat -- ai/brain_router.py ai/__init__.py
```

### 2. Rescate de universo-v1

```bash
git fetch origin universo-v1:universo-flat
git checkout -b rescate/universo-3d
git checkout universo-flat -- \
  index_master_universo.html index_master_draggable.html \
  index_sovereign_master.html autofix_engine.py swarm_planner.py openrouter_core.py
```

### 3. Congelar ui-stable

```bash
git tag archive-ui-stable-2026-09-10 909b0366
git push origin archive-ui-stable-2026-09-10
```

### 4. Borrar edicion-apk

⚠️ **Esto borra una rama remota.** Es recuperable solo si tienes el SHA.
Confirma antes de ejecutarlo.

```bash
git push origin --delete edicion-apk
```

---

## 5. Reglas a partir de ahora

1. **Nunca `git merge <rama>` sin antes** haber mirado el `compare` de la API y
   haber escaneado secretos.
2. **Una rama por feature**, borrada al mergear. Nada de ramas "para siempre".
3. **`.env*` no se commitea.** Ya está en `.gitignore`; si un `git add .` lo
   cuela, el `.gitignore` no sirve de nada porque el fichero ya está trackeado.
4. **Antes de rescatar código ajeno**, contar `os.system` y `shell=True`.
5. **Nombres de rama planos** o con un solo prefijo: los `refs` con subcarpetas
   fallan en silencio en este repo.

---

## 6. 🔴 P0: rotación de claves (lo único que de verdad arregla esto)

Borrar ramas **no** borra el historial: las claves siguen accesibles mientras
GitHub conserve los commits. Y aunque se borren, cualquiera que haya clonado el
repo ya las tiene.

Hay que **revocar y regenerar**:

- [ ] 2 claves Gemini `AIza…`
- [ ] 2 claves Gemini `AQ.…` (anteriores, no la nueva)
- [ ] 4 claves `sk-…`
- [ ] 1 `client_secret` de Google OAuth (`GOCSPX…`)
- [ ] **`DANIELA_PIN`** — el actual salió publicado en el historial de git.
      Se cambia en la **línea 1 de `.env`** (`DANIELA_PIN=`), que está fuera de
      git. No escribo el valor aquí porque este fichero sí está en GitHub.

Para limpiar el historial haría falta `git filter-repo` + force-push. **No lo
he hecho**: es destructivo, reescribe todos los SHAs y dejaría cualquier copia
local desincronizada. Primero rota las claves; después, si quieres, limpiamos
el historial con calma.
