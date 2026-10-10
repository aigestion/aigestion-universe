# GitHub paso a paso (sin saber nada de GitHub)

Tu repo: **https://github.com/aigestion/AIGESTION-MONOREPO**
Tienes **49 commits** en tu PC que aún no están en GitHub.

---

## Antes de nada: dos conceptos

| | Qué es | Dónde vive |
|---|---|---|
| **Git** | Tu histórico de versiones | En tu PC |
| **GitHub** | Una copia en la nube de ese histórico | En internet |

`git commit` = guardar en tu PC (ya lo haces, 49 veces).
`git push` = subir lo guardado a GitHub (esto es lo que nunca has hecho).

Nada de lo que hay en tu PC se ve en internet hasta que haces `push`.
Y nada de lo que ya subiste se borra haciendo más commits.

---

## ⚠️ PASO 0 — Haz esto ANTES de subir nada (5 minutos)

Tu clave de Gemini **ya está en GitHub**. Está en `origin/main`, dentro de un
`.env` que se subió hace tiempo. Empieza por `AIzaSyAGTx…` — en la consola de
Google la reconocerás por ese principio. (No la pego entera aquí a propósito:
el guardián de secretos me paró el commit la primera vez, y hace bien.)

Para verla completa en tu PC, si la necesitas: `git show origin/main:.env`

No es culpa tuya ni se puede borrar con un commit nuevo: el historial guarda
para siempre lo que un día se subió. **La única forma real de arreglarlo es
inutilizar la clave.**

1. Entra en **https://aistudio.google.com/app/apikey**
2. Busca esa clave y pulsa **Delete** (o "Revocar").
3. Pulsa **Create API key** para generar una nueva.
4. Abre el fichero `.env` de tu proyecto y cambia la línea
   `GEMINI_API_KEY=` por la nueva. **No toques nada más del `.env`.**

Hecho esto, da igual quién lea el historial: la clave antigua ya no funciona.

> Buena noticia: tu repo **parece privado** (GitHub responde "Not Found" a
> quien no ha iniciado sesión). Así que la clave no es pública *ahora mismo*,
> pero sigue estando en los servidores de GitHub. Rótala igual.

### Lo que ya limpié por ti (no tienes que hacer nada)

- El PIN estaba quemado en el código como valor por defecto → ya no
  existe; ahora se lee del entorno y, si falta, **el acceso queda cerrado**.
  (No escribo aquí el valor: este fichero está en GitHub. Cámbialo en `.env`.)
- La **contraseña de tu wallet MetaMask** aparecía en `docs/WALLET-AUDIT-REPORT.md`
  → redactada. **Nunca llegó a GitHub.** Cámbiala en MetaMask si la reutilizas
  en algún otro sitio.
- Restos del PIN en `README.md`, `AUDITORIA_V1.md`, `output/`, `static/`,
  `docker-compose.yml` y un `.bak` → redactados.

---

## PASO 1 — Iniciar sesión en GitHub (una sola vez)

Abre la terminal en `C:\Users\Alejandro\aig` y escribe:

```bash
gh auth login
```

Te hará 5 preguntas. Responde exactamente esto:

| Pregunta | Responde |
|---|---|
| Where do you log in? | **`GitHub.com`** |
| What is your preferred protocol? | **`HTTPS`** |
| Authenticate Git with your GitHub credentials? | **`Yes`** |
| How would you like to authenticate? | **`Login with a web browser`** |

Entonces verás algo como:

```
! First copy your one-time code: A1B2-C3D4
Press Enter to open github.com in your browser...
```

1. **Copia ese código** (`A1B2-C3D4`, el tuyo será otro).
2. Pulsa **Enter** → se abre el navegador.
3. Pega el código y pulsa **Authorize GitHub**.

Vuelve a la terminal. Si ves `✓ Logged in as ...`, ya estás dentro.

> Si `gh auth login` te da problemas, dímelo y te paso el método alternativo
> con un token personal (también es sencillo, pero tiene un paso más).

---

## PASO 2 — Subir tu trabajo

```bash
git push origin main
```

La primera vez puede tardar un minuto: son 49 commits. Cuando termine verás
algo como:

```
To https://github.com/aigestion/AIGESTION-MONOREPO.git
   7900cfa..bdb66e9  main -> main
```

**Ya está.** Todo tu trabajo está en la nube.

---

## PASO 3 — Comprobar que salió bien

```bash
git status -sb
```

Tiene que decir **`## main...origin/main`** sin la palabra `ahead`.
Si pone `ahead`, algo no se subió.

También puedes abrir **https://github.com/aigestion/AIGESTION-MONOREPO** y ver
tus ficheros.

---

## Lo que NO debes hacer

| No hagas | Por qué |
|---|---|
| `git push --force` | Reescribe el historial remoto. Si te equivocas, borras trabajo. No lo necesitas. |
| `git reset --hard` | Descarta cambios sin preguntar. |
| Subir el fichero `.env` | Ya está en `.gitignore`, así que no se sube. **No lo quites de ahí.** |
| Borrar la carpeta `.git` | Perderías todo el histórico. |

---

## Para el futuro: la rutina de siempre

Tres comandos, siempre igual:

```bash
git add -A                          # 1. qué quiero guardar (todo)
git commit -m "qué he cambiado"     # 2. guárdalo en el PC
git push origin main                # 3. súbelo a GitHub
```

**Regla de oro: haz `commit` a menudo y `push` al terminar el día.**
Un commit es gratis y te salva si algo se rompe.

---

## Si algo falla

| Mensaje | Qué significa | Qué hacer |
|---|---|---|
| `could not read Username` | No has iniciado sesión | Vuelve al PASO 1 |
| `failed to push some refs` | GitHub tiene algo que tú no | `git pull --rebase origin main` y luego `git push` |
| `non-fast-forward` | Idem: el remoto va por delante | Trae primero los commits remotos y **nunca** uses `--force` |
| `refusing to allow an OAuth App to create or update workflow ... without 'workflow' scope` | Tu sesión de `gh` no tiene permiso para tocar GitHub Actions | `gh auth refresh -h github.com -s workflow` y autoriza de nuevo |
| `Permission denied` | Tu usuario no tiene acceso al repo | Pide que te añadan como colaborador |
| `src refspec main does not match` | Tu rama no se llama `main` | `git branch` y usa el nombre que salga |

---

## Preguntas que seguro te haces

**¿Se borra la clave del historial limpiando el código?**
No. El historial es inmutable. Por eso el PASO 0 es rotar la clave, no borrarla.

**¿Puedo limpiar el historial igualmente?**
Sí, con `git filter-repo` y un `push --force`. Pero reescribe los commits de
cualquiera que trabaje contigo y es fácil meter la pata. **Déjalo para cuando
ya controles lo básico.** Con la clave rotada ya no hay riesgo real.

**¿Se ve mi `.env` en GitHub?**
No. Está en `.gitignore`. Compruébalo tú mismo: `git ls-files | grep '^\.env$'`
no debe devolver nada.
