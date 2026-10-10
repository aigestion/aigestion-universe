# ⚙️ Instalación y configuración

**Estado:** vigente · Verificado: 14 sep 2026
**Tiempo estimado:** 15 minutos la primera vez

Guía paso a paso, con **los errores reales que han pasado de verdad** y cómo
evitarlos. Si algo no funciona, mira primero la sección 8 (*Problemas conocidos*).

---

## 1. Requisitos

| Qué | Versión | Nota |
|---|---|---|
| **Python** | 3.11+ | El venv actual usa **3.11.16**. El `README` dice 3.13, pero funciona |
| **Windows** | 10/11 | Entorno actual (`C:\Users\Alejandro\aig`) |
| **Git** | cualquiera reciente | Con acceso al repo |
| **Docker** | opcional | Solo si vas a usar el marketplace |
| **ADB** | opcional | Solo para controlar el móvil |

> **Sobre los ajustes de entorno del sistema:** `HTTP_PROXY` debe estar **vacío**.
> Con un proxy configurado, las llamadas a `localhost` rebotan y devuelven error 502.
> Es una trampa documentada que ya ha costado tiempo.

---

## 2. Instalación paso a paso

### 2.1 Clonar

```bash
git clone https://github.com/aig/aig-MONOREPO.git
cd aig-MONOREPO
```

⚠️ **Aviso para clones nuevos:** el repo tiene 3 subrepos sin `.gitmodules`
(`tencent-suite/Hunyuan3D-2`, `HunyuanDiT`, `HunyuanVideo`). Saldrán **carpetas
vacías**. No son necesarios para arrancar.

También pesa: `.git` son **1,9 GB**. La descarga tardará.

### 2.2 Entorno virtual

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows
source .venv/bin/activate        # Linux/Mac
```

### 2.3 Dependencias

```bash
pip install -r requirements.txt
```

⚠️ **`requirements.txt` está incompleto.** Verificado el 14 sep 2026, faltaba
`sqlalchemy` teniendo el paquete 78 instalados — y sin él `api_gateway.py` **no
arranca**. Instálalo explícitamente:

```bash
pip install sqlalchemy==2.0.35
```

Comprueba qué tienes y qué falta:

```bash
pip install flasgger prometheus-client pyjwt    # los otros 3 que pide requirements
```

### 2.4 ⚠️ La configuración del entorno (el paso crítico)

**Aquí es donde el sistema se rompe en silencio.** Lee esto entero.

Daniela OS lee sus secretos de ficheros `.env`. Históricamente había **dos**, con
contenido distinto:

| Fichero | Claves | ¿Se leía? |
|---|---:|---|
| `.env` (raíz) | 561 | ✅ Sí — **es el que manda** |
| `config/.env` | 557 | ❌ No, hasta el 14 sep 2026 |

El `.env` de la raíz se quedó un día con **solo 12 claves** (las de Supabase).
Resultado: `DANIELA_PIN`, `GEMINI_API_KEY` (la usan **75 módulos**), `GROQ_API_KEY`,
`PIXEL_IP` y `PIXEL_TOKEN` llegaban **vacías, sin dar ningún error**. El fallo se
manifestaba mucho después, en otro módulo, como un "no reconoce la clave" misterioso.

**Ya está arreglado en dos capas:**

1. `daniela_os.py` ahora carga **los dos** ficheros y **avisa en consola** si falta
   alguna clave crítica. El fallo ya no puede ser silencioso.
2. Hay un diagnóstico de un segundo:

```bash
./.venv/Scripts/python.exe scripts/check_env.py
```

Salida esperada (correcta):

```
Raiz    .env         ->  561 claves (33496 bytes)
Config  config/.env  ->  557 claves (32820 bytes)

Todo correcto: las claves criticas estan en el entorno.
```

Si falta algo, te lo dice y lo arregla él solo (haciendo copia antes):

```bash
./.venv/Scripts/python.exe scripts/check_env.py --restore
```

### 2.5 Qué claves necesitas como mínimo

| Clave | Para qué | ¿Obligatoria? |
|---|---|---|
| `GEMINI_API_KEY` | Motor de IA principal (**75 módulos**) | ✅ Sí |
| `DANIELA_PIN` | Acceso por PIN al panel | ✅ Sí |
| `GROQ_API_KEY` | IA de respaldo, más rápida | Recomendada |
| `OPENROUTER_API_KEY` | IA de respaldo | Recomendada |
| `PIXEL_IP` / `PIXEL_TOKEN` | Control del móvil | Solo si usas el Pixel |
| `SUPABASE_URL` / `_KEY` | Cloud y RAG | Solo si usas la nube |

> 🔐 **Las claves nunca se escriben en un documento ni en un commit.** El hook
> *Secret Guard* los bloquea, y `tunnel_guard` los marca como fuga. Ya ha pasado
> con un informe de auditoría que citaba una clave "de ejemplo".

---

## 3. Arrancar

### 3.1 Daniela OS (app principal, puerto 5000)

```bash
PYTHONPATH="C:/Users/Alejandro/aig" ./.venv/Scripts/python.exe daniela_os.py
```

> **`PYTHONPATH` es obligatorio.** `sitecustomize.py` mete `scripts/` en `sys.path`;
> sin él, todo falla con `No module named ...`.

Abre **http://localhost:5000** (dashboard en `/dashboard`).

Opzioni: `--port 5000` `--host 0.0.0.0` `--debug`.

**Qué verás al arrancar:** unas 60 líneas `[Modulo] Routes registered: ...`.
**Esa lista importa**: si un módulo falla, verás `[Modulo] No disponible: ...` y el
sistema seguirá arrancando igual. Si un endpoint no responde, **mira aquí primero**.

### 3.2 API Gateway (puerto 8080, opcional)

Es un **servicio separado**: `daniela_os.py` **no** lo importa.

```bash
./.venv/Scripts/python.exe api_gateway.py --port 8080
```

Necesita `sqlalchemy`. Si falta: `ModuleNotFoundError: No module named 'sqlalchemy'`.

### 3.3 Docker (opcional)

```bash
docker-compose up -d
```

Nginx en `http://localhost`, Daniela OS en 5000, API Gateway en 8080,
panel de admin en `/admin`.

---

## 4. Verificar que todo está bien

```bash
# 1. ¿Está el entorno completo?
./.venv/Scripts/python.exe scripts/check_env.py

# 2. ¿Cuántas rutas arrancan? (esperado: 383)
PYTHONPATH="C:/Users/Alejandro/aig" ./.venv/Scripts/python.exe -c \
  "import warnings; warnings.filterwarnings('ignore'); import daniela_os; \
   print('rutas:', len(list(daniela_os.app.url_map.iter_rules())))"

# 3. ¿Está el PIN cargado?
PYTHONPATH="C:/Users/Alejandro/aig" ./.venv/Scripts/python.exe -c \
  "import warnings; warnings.filterwarnings('ignore'); import daniela_os; \
   print('PIN:', bool(daniela_os.ACCESS_PIN))"
```

Los tres deben dar: `Todo correcto`, `rutas: 383`, `PIN: True`.

---

## 5. Estado real del repositorio

```bash
./.venv/Scripts/python.exe scripts/repo_status.py
```

> 🧨 **`git status -sb` y `git branch -vv` MIENTEN en este repositorio.**
>
> `git fetch` **no persiste los refs remotos**: `.git/refs/remotes/origin/` está
> vacío, y `git update-ref` tampoco consigue crear entradas (falla en silencio,
> con código de salida 0). Consecuencia: `git branch -vv` dice
> `[origin/universo-v1: gone]` cuando la rama **existe perfectamente**.
>
> **Usa `scripts/repo_status.py`** o `git ls-remote`, que sí son fiables.

Estado actual: `main` = `universo-v1` = tu HEAD. Rama única, sin líos.

---

## 6. Despliegue en el móvil (Pixel 8a)

### Lo que funciona

- **`adb push` a `/sdcard`** — el único camino fiable.
- El móvil corre **Termux sin root**.

### Las limitaciones que hay que conocer

| Limitación | Detalle |
|---|---|
| El home de Termux es **inaccesible por adb** | Hay que pedirle al usuario que ejecute los comandos dentro de Termux |
| El DanielaOS del `:8082` es un **mock** | Responde 200/405 sin ejecutar nada |
| Aritmética de shell Android de **32 bits con signo** | Cuidado con contadores grandes |
| `find /sdcard` devuelve 0 | Usa `/storage/emulated/0/` |
| `sort -h` no existe | Usa `sort -rn` |

### Pasos

```bash
adb push <fichero> /sdcard/
# luego, DENTRO de Termux (pídeselo al usuario):
bash /sdcard/DanielaOS/deploy/install.sh
```

Detalle completo en [[AUDITORIA_TELEFONO_PROFUNDA]] y [[ESPLENDOR_TELEFONO]].

---

## 7. Red: cerrar el agujero del túnel

🔴 **Estado actual: hay un `cloudflared` publicando el puerto 8082 SIN autenticación.**

Para cerrarlo: [[TAILSCALE-P0]]. Resumen:

1. El **móvil ya tiene Tailscale** (IP `100.65.50.219`). El **PC no**.
2. Instalar en el PC con la **misma cuenta**: el instalador está en
   `data/instaladores/tailscale-setup-amd64.msi` (pide permisos de administrador).
3. Matar `cloudflared` **desde dentro de Termux**: `pkill cloudflared`.
   **`adb` no puede matarlo** (sin root: *Operation not permitted*).
   ⚠️ No uses `am force-stop com.termux`: mataría también el gateway.

---

## 8. Problemas conocidos y su causa

### "No reconoce la clave" / el PIN no funciona
**Causa:** el `.env` de la raíz se quedó sin claves.
**Solución:** `./.venv/Scripts/python.exe scripts/check_env.py --restore`

### `ModuleNotFoundError: No module named 'X'`
**Causa:** falta `PYTHONPATH`.
**Solución:** añade `PYTHONPATH="C:/Users/Alejandro/aig"` delante del comando.

### `ModuleNotFoundError: No module named 'sqlalchemy'`
**Causa:** `requirements.txt` está incompleto.
**Solución:** `pip install sqlalchemy==2.0.35`

### Un endpoint devuelve 404 pero el código está ahí
**Causa probable:** el módulo falló al registrarse (sección 3.1).
**Solución:** mira la salida del arranque. Busca `[Modulo] No disponible: ...`.

### `git branch -vv` dice que la rama remota "ha desaparecido"
**Causa:** es un falso aviso (ver sección 5).
**Solución:** ignóralo, o usa `scripts/repo_status.py`.

### `git check-ignore fichero` dice que no está ignorado (y sí lo está)
**Causa:** `git check-ignore` **no reporta ficheros ya trackeados**.
**Solución:** para probar la **regla**: `git check-ignore --no-index -v fichero`.
Para probar el **índice**: `git ls-files -i -c --exclude-standard` (debe estar vacío).

### El servidor devuelve 502 en llamadas locales
**Causa:** hay un `HTTP_PROXY` configurado.
**Solución:** vacíalo. En código, pasa `proxies={"http": None, "https": None}`.

### `pytest` no ejecuta ni un test
**Causa conocida y pendiente:** 6 errores de colección (ver [[ARQUITECTURA]] §7).
Los tests piden variables que no existen (`MEMORY_FILE`) o una API key.
**No es un problema tuyo de instalación.**

---

## 9. Copias de seguridad

```bash
powershell -File scripts/cloud_immortal_sync.ps1
```

Respalda **fuera del repositorio**, en `%USERPROFILE%\DanielaBackups\<fecha>\`:
bases de datos, los dos `.env` y las notas de Obsidian conservando su estructura.

> ⚠️ **Un respaldo en el mismo disco no te protege de un fallo del disco.**
> Sube esa carpeta a Google Drive o OneDrive de vez en cuando. El script lo recuerda.

> 📌 **Histórico:** hasta el 14 sep 2026 este script volcaba `.env`, las bases de
> datos y las notas **dentro del propio repositorio**
> (`external-assets/DanielaCloud/`), que se sube a GitHub. Eso filtraba
> credenciales. Corregido en el commit `47d473816`.

---

## Documentos relacionados

- [[INDEX]] — índice general
- [[ARQUITECTURA]] — cómo está montado por dentro
- [[TAILSCALE-P0]] — cerrar el túnel abierto
- [[AUDITORIA-CAMBIOS-2026-09-14]] — estado del proyecto y pendientes
