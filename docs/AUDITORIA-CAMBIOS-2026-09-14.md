# Auditoría de los cambios nuevos — 14 sep 2026

**Rama viva:** `universo-v1` @ `7ab9bb27a` (= `origin/universo-v1`, sincronizada ✅)
**Punto de partida de esta auditoría:** `7df2b8bb7` (el HEAD de la auditoría anterior)
**Comprobado ejecutando el código real** con `./.venv/Scripts/python.exe`, no leyendo solo el diff.

---

## 1. Resumen ejecutivo

Desde la última auditoría hay **18 commits nuevos, 511 ficheros y +90.653 líneas**.
El sistema **arranca** y ha pasado de **314 a 383 rutas** (+69).

| Dato | Antes | Ahora |
|---|---|---|
| Rutas Flask | 314 | **383** |
| Ficheros trackeados | ~900 | **1.310** |
| `.py` en la RAÍZ | 4 | **226** ⚠️ |
| Ramas divergentes | main vs universo-v1 (617 vs 387 commits) | **resuelto** ✅ |

### La buena noticia (esto es grande)

El problema de las dos historias duplicadas **está resuelto de hecho**:

- `origin/main` **es ancestro** de `HEAD` → 0 commits de main fuera. universo-v1 **contiene main**.
- `origin/fase-11-seguridad-contexto` **está contenida** en `HEAD` → 0 commits fuera.
- `06df8624` (el `origin/universo-v1` viejo que "no era ancestro") **ahora sí lo es**.
- Local y remoto apuntan al **mismo SHA**.

Traducción: el merge del PR #109 unió las dos líneas. **`universo-v1` es ya la línea única**, y además contiene a main, así que **se puede promocionar a `main` con un push normal, SIN `--force`** (es fast-forward).

---

## 2. 🔴 P0 — Romper y arreglar HOY

### P0-1. El `.env` de la raíz fue SOBRESCRITO y se perdió la configuración viva

**Lo que ha pasado:** el `.env` de la raíz (el único que `load_dotenv()` lee) se reescribió el
**14 sep a las 16:34** y ahora es un fichero de **676 bytes con 12 claves** de Supabase.
Antes tenía 556+ claves.

Comprobado cargando el entorno de verdad:

```
DANIELA_PIN            -> VACIA/NO EXISTE
GEMINI_API_KEY         -> VACIA/NO EXISTE   <-- 75 módulos la usan
GROQ_API_KEY           -> VACIA/NO EXISTE
PIXEL_IP               -> VACIA/NO EXISTE
PIXEL_TOKEN            -> VACIA/NO EXISTE
SUPABASE_URL           -> OK
SUPABASE_SERVICE_KEY   -> OK
```

**La copia buena existe**: `config/.env` (32 KB, 12 sep 21:30, **557 claves con valores reales**:
`GEMINI_API_KEY` 53 chars, `PIXEL_TOKEN` 43, etc.). Pero **nadie lee `config/.env`**.

Además hay un **segundo `.env` clonado en `C:\Users\Alejandro\.env`** (los mismos 676 bytes),
y `scripts/cloud_immortal_sync.ps1` lo copia a `external-assets/DanielaCloud/.env.cloud_bak`
— pero ese backup **no se llegó a crear** (cuando corrió, a las 15:35, el `.env` de HOME aún no existía).

**Arreglo (reversible, haz copia primero):**

```bash
cd /c/Users/Alejandro/aig
cp .env .env.supabase-2026-09-14.bak        # guarda lo nuevo
cat config/.env .env.supabase-2026-09-14.bak > .env   # viejo + Supabase (Supabase gana)
```

Luego **arreglar la causa raíz** para que no vuelva a pasar: o `load_dotenv()` lee `config/.env`,
o `config/.env` deja de existir y hay un único `.env`. Tener dos es una trampa.

### P0-2. La clave `service_role` de Supabase está hardcodeada en 6 ficheros

```
sb_secret_****          <- clave real, NO se escribe aqui (rotar cuanto antes)
```

| Fichero | Línea |
|---|---|
| `scripts/apply_sql_api.py` | 14 (como *default* de un `get`) |
| `scripts/check_rag.py` | 16 (como *default* de un `get`) |
| `scripts/check_rag_fast.py` | 15 (como *default* de un `get`) |
| `scripts/force_sync_rag.py` | 8 (literal pelado) |
| `scripts/test_rag_supabase.py` | 16 (como *default* de un `get`) |
| `test_rag.py` | 6 (literal pelado) |

La `service_role` **salta todas las políticas RLS**: quien la tenga puede leer y borrar toda la
base de datos. Ahora están sin commitear (bien), pero `scripts/` es una carpeta **trackeada**:
el día que hagas `git add scripts/`, se van a GitHub para siempre.

**Arreglo:** rotar la clave en el panel de Supabase y sustituir los 6 literales por
`os.getenv("SUPABASE_SERVICE_KEY")` **sin valor por defecto** (fail-closed).

### P0-3. `credentials.json` está TRACKEADO con el `client_secret` real de Google

```
credentials.json:1: {"installed":{..., "client_secret":"GOCSPX-****", ...}}
```

Un `client_secret` de OAuth **nunca** va en el repo. Está ya en el historial de GitHub.

**Arreglo:** rotarlo en Google Cloud Console, `git rm --cached credentials.json`, añadirlo al
`.gitignore` y dejar un `credentials.json.example`.

### P0-4. Sigue pendiente de la auditoría anterior

- Rotar la `GEMINI_API_KEY` (ya está en el historial de GitHub).
- Rotar los 2 PAT `ghp_` y el resto de los 22 secretos.
- `git filter-repo` para limpiar el historial — **y ahora con más motivo**: el merge del PR #109
  hizo que `06df8624` (la rama "que tenía claves") sea **ancestro** de `universo-v1`,
  y `universo-v1` **ya está empujada**. O sea: esas claves están en el remoto.
- ⚠️ `.env.master` **ha desaparecido** del disco (era el inventario de los 22 secretos reales).
  Solo quedan `.env.master.example`. Sin él se pierde la lista de qué rotar. Si tienes copia, recupérala.

---

## 3. 🟠 P1 — Higiene de repo (barato de arreglar, caro de ignorar)

### P1-1. `.gitignore` no cubre lo nuevo → 132 MB de `.exe` a un `git add .` de distancia

Comprobado con `git check-ignore`, **NO están ignorados**:

| Ruta | Tamaño | Qué es |
|---|---|---|
| `bin/` | **132 MB** | `supabase.exe` (95 MB) + `supabase-go.exe` (41 MB) |
| `hermes-epic/` | 229 KB | 59 módulos `.py` nuevos (ver P2-3) |
| `supabase/` | 17 KB | `migrations/20260914162954_init_rag.sql` |
| `test_rag.py`, `init_rag.sql` | — | scripts de prueba del RAG |

`bin/` **no debe entrar jamás** en el repo (GitHub rechaza >100 MB por fichero).

### P1-2. 4 bases de datos SQLite trackeadas

```
daniela_multiuser.db  memory.db  memory_rag.db  external-assets/DanielaCloud/daniela_memory_sync.db
```

Son **datos de usuario** (memoria, multiusuario) que ahora aparecen como "modificados" en cada
`git status`. El commit `52146ed62` intentó sacarlas y no lo consiguió.

### P1-3. La suite de tests no ejecuta NI UN test

```
Interrupted: 6 errors during collection
tests/test_daniela_backend.py: ImportError: cannot import name 'MEMORY_FILE'
tests/core/test_core.py: ValueError: No API key was provided
tests/test_and_fix_camera.py / test_auditoria.py: FileNotFoundError [WinError 2]
```

Es decir: **no hay red de seguridad**. Cualquier cambio futuro entra a ciegas.

### P1-4. El venv no puede importar `api_gateway.py`

```
api_gateway.py:31: from sqlalchemy import create_engine, text, MetaData
ModuleNotFoundError: No module named 'sqlalchemy'
```

`requirements.txt` pide `sqlalchemy==2.0.35`, el venv tiene 77 paquetes pero no ese.
`api_gateway.py` (el componente con el `hmac.compare_digest` de la E-30) **no arranca**.
Nota: `daniela_os.py` **no importa** `api_gateway`, así que el gateway endurecido no está montado
en el servidor principal; son dos servicios separados.

### P1-5. 3 subrepos anidados sin `.gitmodules`

`tencent-suite/Hunyuan3D-2`, `HunyuanDiT`, `HunyuanVideo` están en el índice como **gitlinks
(modo 160000)** pero **no existe `.gitmodules`** → quien clone el repo verá 3 carpetas vacías.

### P1-6. El repo pesa 1,9 GB de `.git` (y 148 commits "Auto-backup Daniela OS")

El árbol de trabajo es pequeño, pero `.git` son **1,9 GB**. Hay **148 commits automáticos**
"Auto-backup Daniela OS" (puro ruido en el historial) y binarios pesados trackeados:
`assets/oficina3d.glb` (90 MB), un `.mp4` y dos `.wav` en `assets/generated_videos/`.
GitHub avisa a partir de 1 GB.

---

## 4. 🟡 P2 — Arquitectura: el refactor se deshizo

### P2-1. La raíz ha vuelto a tener 226 ficheros `.py`

La Fase 2 movió el código real a `aig/pixel/` (98 ficheros) y dejó shims en `scripts/`.
El merge ha **resucitado** las copias de la raíz. Resultado: **tres copias del mismo módulo**:

```
tunnel_guard.py            ->  raíz: SÍ (1.133 líneas)   aig/pixel: SÍ (1.155 líneas)   scripts/: shim
termux_v2_roadmap.py       ->  raíz: SÍ                  aig/pixel: NO                  scripts/: shim
local_brain.py / urban_nodes.py / ar_stage.py  ->  solo aig/pixel + shim
```

**Y las copias NO son iguales.** Comprobado en tiempo de ejecución:

```
>>> import tunnel_guard
C:\Users\Alejandro\aig\tunnel_guard.py     <-- GANA LA RAÍZ
```

🔴 Consecuencia: **editar `aig/pixel/tunnel_guard.py` no tiene ningún efecto**. El código
que corre es el de la raíz. Esto es exactamente el tipo de trampa que ya nos costó horas antes.

### P2-2. Los directorios nuevos son islas, no están integrados

| Directorio | Ficheros `.py` | ¿Registrado en `daniela_os.py`? |
|---|---|---|
| `epic-pc/` | 65 | **NO** |
| `daniela-omnipresente/` | 65 | **NO** (tiene su propio `server.py`) |
| `phone_deploy/` | 48 | **NO** |
| `skills/` | 47 | **NO** |
| `plugins/` | 32 | **NO** |
| `daniela-jarvis/` | 1 (+`node_modules`, 2.069 ficheros) | **NO** |
| `hermes-epic/` | 59 | **NO** |

`grep` en `daniela_os.py` de `epic-pc|omnipresente|phone_deploy|jarvis|unified_bridge` → **cero
resultados**. Los "+69 rutas" vienen de los módulos viejos ya integrados, no de estos directorios.

O sea: los commits dicen "62 sistemas de IA", "114 sistemas", "50 ideas"... pero **son ~250
ficheros sueltos con su propio servidor**, no rutas del DanielaOS. No es que esté mal; es que
**la cifra engaña** y hay que decidir qué se integra y qué se archiva.

### P2-3. `hermes-epic/` está huérfano y sin commitear

59 módulos (memoria, personalidad, skills, automatización, `hermes_daniela_bridge.py`...)
creados el 13 sep a las 23:39. **No los referencia nadie** en el repo y están sin commitear.
O se integran, o se archivan, o se borran — pero dejarlos ahí sin decidir es deuda.

### P2-4. Limpieza pendiente de ramas

Siguen ahí: `main` local (`70b58eaec`, atrasada), `remoto-main`, `backup-local-main-50commits`,
`universo-v1-flat`, `uistable-flat`, `edicion-apk`, `ui-stable`, `feature/darwin-api`,
`autofix/scratch_gate_smoke.py-1789135109`. Más un **worktree huérfano** en
`C:\Users\Alejandro\worktrees\aig\total-sycamore\aig` (detached en `9fc3a539d`).
Los 2 `stash` de seguridad siguen ahí — **no hacer `stash clear`**.

---

## 5. Siguientes pasos propuestos (por orden)

### Bloque A — ✅ HECHO el 14 sep a las 22:55

| # | Acción | Estado |
|---|---|---|
| 1 | Restaurar el `.env` de la raíz (676 B → 33.496 B, 12 → **561 claves**) | ✅ verificado en runtime |
| 2 | Neutralizar el `.env` duplicado de HOME | ✅ movido a `.env.moved-2026-09-14.txt` |
| 3 | Ampliar `.gitignore` (`bin/`, `hermes-epic/`, `supabase/`, `*.db`, `.env*`, RAG…) | ✅ verificado con `git check-ignore` |
| 4 | Sacar del índice 23 ficheros (11 sensibles + 12 generados) con `git rm --cached` | ✅ ninguno borrado del disco |
| 5 | Blindar `daniela_os.py`: carga los DOS `.env` + aviso de claves que faltan | ✅ 383 rutas, arranca |
| 6 | `scripts/check_env.py` (diagnóstico + `--restore`) y `fill_missing_env.py` | ✅ |
| 7 | Instalar `sqlalchemy==2.0.35` → `api_gateway.py` ya importa | ✅ |

**Copias de seguridad hechas antes de tocar nada:**
`.env.supabase-2026-09-14.bak`, `config/.env.bak-2026-09-14`,
`C:\Users\Alejandro\.env.bak-2026-09-14`, `.gitignore.bak-2026-09-14`,
`.backup-indice-2026-09-14/` (los 10 ficheros sensibles). Todas ignoradas por git.

**⚠️ Pendiente y NO automatizable:** rotar en los paneles la clave `service_role` de
Supabase, el `client_secret` de Google y la `GEMINI_API_KEY`. Hacerlo **antes** del
`git filter-repo`.

### Bloque B — esta semana

5. **Promocionar `universo-v1` a `main`** — ya es fast-forward, sin `--force`:
   `git push origin HEAD:main`. Luego borrar/archivar las 9 ramas muertas y el worktree huérfano.
6. **Sacar los literales de los 6 scripts** (P0-2) y `git rm --cached credentials.json` (P0-3)
   — el `--cached` de `credentials.json` ya está hecho.
7. **Decidir el refactor de estructura** (P2-1): una de las dos, no las dos.
   - Opción A (recomendada): la raíz manda. Mover los 226 `.py` a `aig/pixel/` **solo** con
     `git mv` y borrar los shims duplicados. Verificando `import tunnel_guard.__file__` en cada paso.
   - Opción B: la raíz manda y `aig/pixel/` se archiva. Más rápido, pero pierde el refactor.
8. **Arreglar la suite de tests** (P1-3). Empezar por los 6 errores de colección: sin esto,
   cualquier refactor es a ciegas.
9. **Decidir el destino de los directorios isla** (P2-2): por cada uno, "se integra como blueprint"
   o "se archiva en `scripts/archive/`". Y `hermes-epic/` igual (P2-3).

### Bloque B — ✅ HECHO el 14 sep a las 23:05

| # | Acción | Estado |
|---|---|---|
| 5 | Commit del Bloque A (`47d473816`, 31 ficheros) | ✅ hook Secret Guard: sin secretos |
| 6 | **Promocionar `universo-v1` a `main`** (fast-forward, 834 commits, **0 perdidos**) | ✅ `git push origin HEAD:main` |
| 7 | Etiquetas de archivo para las 10 ramas antes de borrar | ✅ `archivo-2026-09-14-*` |
| 8 | Borrar 6 ramas locales redundantes | ✅ ninguna contenía trabajo perdido |
| 9 | `scripts/cloud_immortal_sync.ps1` reescrito: ya no respalda **dentro** del repo | ✅ ahora en `%USERPROFILE%\DanielaBackups` |
| 10 | `scripts/repo_status.py`: estado real del repo sin fiarse de `git status -sb` | ✅ |

**Estado remoto final:** `main` = `universo-v1` = `6f214e1d0` (tu HEAD). Los tres iguales.

#### 🔴 Trampa nueva descubierta: `git fetch` NO persiste NADA en este repo

`.git/refs/remotes/origin/` está **vacío**. No es solo que `fetch` no lo llene:
**`git update-ref` tampoco consigue crear entradas** — falla en silencio, sin
mensaje de error y devolviendo código de salida 0. Comprobado:

```
$ git update-ref refs/remotes/origin/universo-v1 47d473816
$ git rev-parse refs/remotes/origin/universo-v1
fatal: ... unknown revision          # no se creó nada
```

Consecuencia: **todo comando que compare contra `origin/...` miente**:

| Comando | Lo que dice | La verdad |
|---|---|---|
| `git status -sb` | `## universo-v1...origin/universo-v1` | no lo sabe, no tiene el ref |
| `git branch -vv` | `[origin/universo-v1: gone]` | la rama **sí** existe en GitHub |

**Solución:** usar `git ls-remote origin` (fiable) o `scripts/repo_status.py`.
El upstream de `universo-v1` se configuró a mano (`git config branch.…remote/merge`)
porque `git branch --set-upstream-to` depende del ref cacheado que no existe.
El aviso `: gone` en `git branch -vv` seguirá ahí: es **cosmético**, no hay nada roto.

### Bloque C — cuando haya calma

11. `git filter-repo` para limpiar secretos del historial (**después** de rotarlos, nunca antes).
12. Adelgazar `.git`: parar el auto-backup de 148 commits, sacar `.glb`/`.mp4`/`.wav` del índice
    (Git LFS o fuera), y un `git gc --aggressive` después.
13. Añadir los 3 `.gitmodules` que faltan, o sacar `tencent-suite/` del índice (P1-5).
14. Arreglar la suite de tests (6 errores de colección) — **esto debería subir al Bloque B**:
    sin tests, el refactor del P2-1 se hace a ciegas.
15. Decidir el destino de los directorios isla (P2-2) y de `hermes-epic/` (P2-3).
16. La operación que ya venía pendiente: **Tailscale en el PC**, matar el `cloudflared` que publica
    el 8082 sin auth, y el script de llama.cpp en el móvil.

### Ramas que quedan (4, todas con commits propios que NO están en main)

Se les puso etiqueta `archivo-2026-09-14-*` antes de decidir nada. **No se borraron** porque cada
una aporta algo que main no tiene:

| Rama | Commits fuera de main | Qué aporta |
|---|---|---|
| `ui-stable` / `uistable-flat` | 1 | puerto 5055 con `/api/offload` asíncrono (mismo commit) |
| `feature/darwin-api` | 4 | workflow de CI |
| `autofix/scratch_gate_smoke.py-…` | 1 | parche del auto-fix (probablemente descartable) |

**Etiquetas de archivo creadas (10)** — recuperables siempre, aunque se borre la rama:
```
archivo-2026-09-14-main  remoto-main  backup-local-main-50commits  universo-v1-flat
uistable-flat  edicion-apk  ui-stable  feature-darwin-api
fase-11-seguridad-contexto  autofix-scratch-gate
```

### Lo que NO hay que hacer

- ❌ **No** `git add .` ni `git add -A`.
- ❌ **No** `git push --force` a `universo-v1` ni a `origin/main`.
- ❌ **No** `git stash clear` (hay 2 stashes de seguridad).
- ❌ **No** borrar `aig/pixel/` ni la raíz sin haber decidido el P2-1: el que corre ahora
  es **la raíz**.
- ❌ **No** tocar `main` local: `origin/main` ya está dentro de `universo-v1`.
- ❌ **No** escribir secretos reales en documentos (ni "como ejemplo"): el hook Secret Guard
  los bloquea, y `tunnel_guard` los marca como fuga. Ya pasó con este mismo informe.

---

## 6. Anexo — comandos usados para verificar

```bash
git log --oneline 7df2b8bb7..HEAD                     # 18 commits
git diff --stat 7df2b8bb7 HEAD                        # 511 ficheros, +90.653
git merge-base --is-ancestor origin/main HEAD         # -> main está dentro
git ls-remote --heads origin                          # local == remoto
git check-ignore -v bin hermes-epic supabase          # -> NO ignorados
git grep -nIE '(sb_s|GOCSPX-|AIza|ghp_)' -- ':!*.example'
python -c "import tunnel_guard; print(tunnel_guard.__file__)"   # -> la raíz gana
python -c "from dotenv import load_dotenv; load_dotenv(); ..."  # -> 5 claves vacías
python -m pytest tests/ -q                            # -> 6 errores, 0 tests
```
