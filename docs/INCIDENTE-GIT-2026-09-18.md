# INCIDENTE — Pérdida del índice de objetos de `.git` (2026-09-18)

**Estado: RESUELTO.** Ninguna línea de código se perdió. El historial se recuperó
íntegro desde el remoto. La única pérdida real son 2 ramas basura locales y un
`stash` (ver *Pérdidas*).

---

## 1. Qué se observó

Mientras se preparaba E-33, un comando (`git stash push` para comprobar si 2
tests eran preexistentes) recibió SIGTERM. A partir de ahí:

```
$ git status
fatal: not a git repository (or any of the parent directories): .git
```

`.git` existía, pero git no lo reconocía. Medido:

| Elemento | Antes | Después |
|---|---|---|
| Tamaño de `.git` | ~1,87 GiB | 15 MB |
| `.git/objects/pack/*.pack` | 5 packs | **0 packs** (solo quedaban los `.idx`) |
| `.git/refs/` | presente | **ausente** |
| `.git/logs/` | presente | **ausente** |
| Objetos sueltos | muchos | 36 directorios |
| `multi-pack-index` | 1,9 MB | 1,9 MB (**apuntando a packs borrados**) |

Git exige que existan `.git/HEAD`, `.git/objects` **y `.git/refs`** para considerar
válido un repositorio. Al faltar `refs/`, cualquier comando devolvía
*"not a git repository"* — lo que despista, porque **no** es un problema de
permisos ni de `safe.directory`.

## 2. Lo que NO se perdió (lo importante)

- **El árbol de trabajo, intacto**: 231 `.py` en la raíz, `daniela_os.py`,
  `model_router.py`, `aig_core.py`, `pyproject.toml` y los 3 informes del día.
  Comprobado fichero a fichero, sin usar git.
- **Las ediciones de E-33**, presentes en el árbol (se respaldaron antes de tocar nada).
- **Todo el historial commiteado**: `origin/universo-v1` estaba en `b83426649`,
  exactamente el HEAD local. Nada de lo empujado se perdió.

## 3. Causa

**El detonante está identificado; el proceso exacto que borró los packs, no.**

El repositorio tenía **`maintenance.auto = true`** en la configuración global. Eso
hace que, **después de cualquier comando de git**, se dispare en segundo plano
`git maintenance run --auto`, cuyas tareas por defecto incluyen **`gc`**
(`repack` + `prune`). Y el `gc` de `maintenance` **no queda desactivado por
`gc.auto`**: son dos umbrales distintos.

El repo arrastraba además **~1,4 GB de objetos inalcanzables** — restos de antes del
`git filter-repo` del 11-sep, exactamente los 5 directorios borrados que ya detectó
`docs/AUDITORIA-2026-09-18.md`. Un `repack` + `prune` **borra precisamente eso**.

Encaja con todo lo observado: un `git stash push` disparó el mantenimiento en
segundo plano; el `repack`/`prune` eliminó los packs antiguos (los `.pack` sí, sus
`.idx` no llegaron a limpiarse) y los objetos sueltos, dejando `.git` en 15 MB y sin
`refs/`. El proceso murió a mitad (SIGTERM), de ahí la inconsistencia.

Es decir: el "daño" fue, en el fondo, **la compactación que el propio repo ya tenía
pendiente** (E-48). El efecto secundario fue dejar el repositorio inservible.

> ⚠️ Nota de método: `git status` decía *"not a git repository"*, que sugiere
> corrupción o permisos. La causa real era un directorio (`refs/`) ausente.
> **Ante un error de git, medir qué falta en disco antes de teorizar.**

### Efecto colateral descubierto después: cada `git push` borra `refs/remotes/*`

En este entorno, **`git push` deja `refs/remotes/` vacío**: informa `b83426649..98cf81cb7`
y sale con exit 0, pero los refs de seguimiento remoto desaparecen (y con ellos el
`upstream`, de modo que `git status -sb` pasa a mostrar `[gone]`). Pasa lo mismo con
`git fetch`. **Escribir el fichero suelto a mano sí funciona** (probado: un ref escrito
así sobrevivió intacto), pero **vuelve a desaparecer en el siguiente `push`/`fetch`**.

**Causa: NO identificada.** Dos hipótesis probadas y **descartadas** por medición:

| Hipótesis | Prueba | Resultado |
|---|---|---|
| `maintenance.auto=true` (global) | `git config maintenance.auto false` + push | **refs perdidos igual** → no es la causa |
| `core.fsmonitor` | `git config core.fsmonitor false` + fetch | **refs perdidos igual** → no es la causa |

Se dejaron como defensa en profundidad `gc.auto=0` y `maintenance.auto=false` (esta
última sí explica probablemente el **podado de packs** original, pero **no** el borrado
de refs). `core.fsmonitor` se **revirtió a `true`** (su valor original) para no dejar
cambios innecesarios.
Mitigación práctica (la que funciona): usar siempre refspec explícito
(`git push origin HEAD:main`), comprobar el remoto con `git ls-remote origin` —**no** con
`git status -sb`, que miente— y **reescribir los 6 refs sueltos** de `refs/remotes/origin/`
tras cada operación de red.

## 4. Recuperación (pasos ejecutados)

1. **Respaldo primero**, fuera del repo:
   `C:\Users\Alejandro\aig-recuperacion-2026-09-18\` con las 2 ediciones (con su
   `sha256`), `packed-refs`, `config`, `index`, `HEAD`, `filter-repo/` y los objetos sueltos.
2. Recrear la estructura mínima: `mkdir -p .git/refs/heads .git/refs/tags
   .git/refs/remotes/origin .git/logs/refs/heads` → git vuelve a reconocer el repo.
3. `git -c gc.auto=0 fetch origin --prune` → 11.621 objetos, 435 MiB, un pack nuevo.
4. Borrar los refs **rotos** (apuntaban a objetos ya inexistentes):
   `feature/darwin-api`, `ui-stable`, `uistable-flat`, `refs/stash` y **los 20 tags**.
   Los 20 tags y 5 de esas ramas **sí están en el remoto** y se volvieron a traer.
5. Borrar los `.idx` huérfanos (sin `.pack`) y el `multi-pack-index` caducado
   → `git fsck` pasa de decenas de `failed to load pack` a **limpio (exit 0)**.
6. Recrear `refs/heads/universo-v1` en `b83426649` y los 6 `refs/remotes/origin/*`.

**Anomalía (con causa identificada, ver §3):** en este entorno, `git fetch` y
`git push` informan éxito (**exit 0**) pero **no persisten** los refs bajo
`refs/remotes/`; `git update-ref` sobre esa ruta tampoco. Escribir el fichero suelto
a mano **sí** funciona, y desde que `maintenance.auto=false` **se mantienen**.
No afecta a `commit`, `push` (con refspec explícito) ni al árbol; **sí** afectaría a
`git pull` sin `git fetch` previo.

## 5. Verificación final

```
git log --oneline -3   -> 801004bdb, b83426649, a770d7fc1   (historial intacto)
git status --short     -> solo aig_core.py, daniela_os.py (ediciones de E-33)
git fsck               -> limpio
git branch -a          -> universo-v1 + 6 remotos/origin/*
HEAD == origin/universo-v1
git tag                -> 20 tags restaurados
```

## 6. Pérdidas reales (asumibles)

| Qué | Estado |
|---|---|
| `refs/stash` (1 stash de seguridad) | **perdido**: sus objetos eran inalcanzables y se podaron. Nunca se empuja un stash. |
| `uistable-flat` | **perdida**: rama solo local, ya marcada como "sobra" en la memoria del proyecto |
| `feature/darwin-api`, `ui-stable` (locales) | recreadas desde el remoto (estaban desfasadas) |
| 20 tags locales | **recuperados** desde el remoto |
| ~1,4 GB de objetos inalcanzables | eliminados (era el objetivo de E-48 de todas formas) |

## 7. Prevención aplicada

- **`git config maintenance.auto false`** en este repo. Es **la medida que ataca la
  causa**: desactiva el mantenimiento en segundo plano que se dispara tras cada
  comando (cuyo `gc` **no** lo frena `gc.auto`). A partir de ahora la recolección de
  basura es **siempre explícita**.
- **`git config gc.auto 0`** en este repo (defensa en profundidad, para el `gc`
  implícito).
- El respaldo `C:\Users\Alejandro\aig-recuperacion-2026-09-18\` se conserva.

> Lección general: en un repositorio con mucha basura inalcanzable, **`maintenance.auto`
> es peligroso** y **nunca hay que interrumpir un `git` que pueda estar repackando**.

## 8. Pendiente / recomendado

1. **Repack para deduplicar**: hay 2 packs (1,2 GB + 456 MB) porque el segundo
   `fetch` volvió a bajar objetos que el índice roto le ocultaba. Un
   `git repack -a -d` los unifica. **Hacerlo con el repo ya sano y sin interrumpir.**
2. Investigar por qué `git fetch` no persiste `refs/remotes/*` en este entorno.
3. **Copia de seguridad fuera del repo** (un `git bundle` periódico) — hoy el único
   respaldo real es GitHub.
