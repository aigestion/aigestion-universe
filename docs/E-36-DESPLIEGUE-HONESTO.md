# E-36 · Despliegue honesto y contenedor que se reconstruye

**Fecha:** 18 sep 2026 · **Commit:** `5320d8289` · **Estado:** hecho
**Camino crítico:** E-36 ✅ → E-33 ✅ → E-45 ✅ → E-46 ✅ *(cerrado)*

---

## 1. El problema, medido

El plan decía: *"el CD finge desplegar"*. Es cierto, pero se quedaba corto. Lo
medido es **cuatro** capas de mentira, no una.

### 1.1 Tres workflows distintos decían que habían desplegado

| Fichero | Qué decía | Qué hacía |
|---|---|---|
| `cd-21.yml` (`deploy-prod`) | `"Production deployment completed (compose step enabled per repo)."` | La orden `docker compose` estaba **comentada** (líneas 264-265) |
| `cd.yml` (`deploy-production`) | `"Production deployment completed"` | Igual: comentada |
| `cd.yml` (`health-checks`) | `"✓ Placeholder check passed"` ×11 y luego `"All services are healthy!"` | Los `curl` estaban comentados. **No podía fallar nunca** |
| `auto-deploy.yml` (`deploy`) | `"Deploy triggered at …"`, `"Post-deploy health check…"`, `"ROLLBACK TRIGGERED"` | Solo `echo`. El "rollback" no revertía nada |

### 1.2 No existe destino de despliegue (la causa real)

```console
$ gh api repos/aig/aig-MONOREPO/actions/runners
{"total_count":0,"runners":[]}

$ gh secret list
GEMINI_API_KEY · GOOGLE_API_KEY · GOOGLE_SEARCH_CX · GROQ_API_KEY
MASTER_ENV_B64 · NEON_API_KEY
```

* **Cero runners autoalojados.**
* **Cero secretos de despliegue** (ni `DEPLOY_HOST`, ni `SSH_KEY`, ni registro).
* El PC está en una red doméstica, sin ingreso público.

Un runner de GitHub **no tiene camino de red hasta este PC**. Por eso la orden
estaba comentada: no es que alguien se olvidara, es que **no puede funcionar**.
El error no fue comentarla; fue **seguir diciendo que había desplegado**.

### 1.3 Dónde está la producción de verdad

```console
$ docker ps --format '{{.Names}}\t{{.Status}}'
aig-epic-pc        Up 15 hours (healthy)
aig-daniela        Up 15 hours (healthy)
aig-hermes         Up 15 hours (healthy)
… 19 contenedores
aig-daniela  Up 3 days (healthy)      <-- el "congelado el 13-sep"
```

Producción **es este PC**. Y ya existía un script local para desplegar
(`./deploy.sh`, `./deploy.ps1`), pero estaba **roto** y no lo llamaba nadie.

---

## 2. Tres bugs más, encontrados midiendo el camino de despliegue

### 2.1 El health gate que decide si el despliegue está bien… mentía

`scripts/ci_health_gate.py` aceptaba solo `{"alive","online","active"}`.
Vocabulario **real** de los 21 motores, medido:

| Palabra | Motores |
|---|---|
| `alive` | 10 |
| `ok` | 3 |
| `running` | 5 |
| `active` | 1 |
| `operational` | 1 |
| *(sin campo `status`)* | 1 (`regions`) |

Resultado antes del arreglo:

```
total 21 · sanos 14 · pct 66.67 · pasa False
   intel_engine     CAIDO unexpected-status: 'operational' (http 200)
   data_engine      CAIDO unexpected-status: 'running' (http 200)
   secure_engine    CAIDO unexpected-status: 'running' (http 200)
   devtools_engine  CAIDO unexpected-status: 'running' (http 200)
   ecosystem_engine CAIDO unexpected-status: 'running' (http 200)
   scale_engine     CAIDO unexpected-status: 'running' (http 200)
   regions          CAIDO unexpected-status: None (http 200)
```

**7 de 21 motores sanos reportados como caídos.** Un gate que miente en un
tercio de los casos no sirve para decidir un despliegue: `--fail-under 95` no se
alcanza nunca, y eso enseña a ignorar el rojo.

Después:

```
total 21 · sanos 21 · pct 100.0 · pasa True   (exit 0)
```

### 2.2 `deploy.sh` / `deploy.ps1` comprobaban una ruta que da 404

Los dos probaban `http://localhost:<puerto>/status`. Medido:

| URL | Código |
|---|---|
| `http://localhost:9997/status` | **404** |
| `http://localhost:9997/api/status` | **200** |
| `http://localhost:5020/status` | **404** |
| `http://localhost:5020/api/status` | **200** |

Con la ruta mala, los 19 motores salían `OFFLINE` **estando sanos**. Un
despliegue correcto se reportaba como fallo total.

### 2.3 En este PC no existe el plugin `docker compose`

```console
$ docker compose version
docker: unknown command: docker compose
$ docker-compose version
Docker Compose version v5.5.1
```

`deploy.sh` **comprobaba** `docker-compose` pero luego **invocaba**
`docker compose` → con `set -e`, el script moría en el paso 4. Los workflows de
GitHub sí tienen el plugin (runner Ubuntu), así que ahí no se nota: **es un
fallo que solo aparece en la máquina donde de verdad se despliega.**

### 2.4 El proxy del entorno convierte "no hay nadie" en un 502

Con `HTTP_PROXY=http://127.0.0.1:15765` puesto:

| Puerto | Con proxy | Sin proxy |
|---|---|---|
| 8082 (caído) | **502** | **000** |
| 8080 (vivo) | 200 | 200 |

El proxy **enmascara un servicio caído como error de gateway**. Para una URL
local el proxy no aporta nada, así que el gate lo desactiva
(`instalar_opener_sin_proxy()`), y `deploy.sh` usa `curl --noproxy '*'`.

---

## 3. Qué se ha cambiado

| Fichero | Cambio |
|---|---|
| **`scripts/deploy_prod.sh`** | **NUEVO.** El despliegue de verdad: preflight (docker, compose, compose válido, commit), `build`, `up -d --remove-orphans`, espera, y **health gate que puede fallar** (sale != 0 si no llega al umbral). Detecta `docker compose` o `docker-compose`. Tiene `--dry-run`, `--no-build`, `--wait`, `--services`, `--fail-under`. **No toca git.** |
| `scripts/ci_health_gate.py` | Vocabulario medido + `status_key` por motor (`regions`) + `es_base_local()` / `instalar_opener_sin_proxy()` + flags `--noproxy` / `--proxy` |
| `.github/workflows/cd-21.yml` | `deploy-prod` renombrado a *"Produccion: publicar imagenes + instrucciones (NO despliega)"*; verifica las imágenes en GHCR (advisory), escribe el comando real en el step summary y emite `::warning::`. `deploy-staging` renombrado a lo que hace |
| `.github/workflows/cd.yml` | Se quita el `"Production deployment completed"`; el job de health checks pasa a **auto-test del gate** (debe devolver != 0 sin servicios, o el gate miente) |
| `.github/workflows/auto-deploy.yml` | El `tar` **se sube** de verdad (`upload-artifact`, 7 días); el job `deploy` deja de fingir |
| `.github/workflows/ci.yml` | `"Deploy to Local"` → *"Arrancar el stack en el runner (no es produccion)"* |
| `deploy.sh` | Detecta el compose real · `/status` → `/api/status` · `--noproxy '*'` |
| `deploy.ps1` | Lo mismo + `[System.Net.WebRequest]::DefaultWebProxy = $null` |
| `scripts/deploy.sh` | **Guardia de Termux**: sin `PREFIX` con `com.termux` no se ejecuta (hace `pkill -9 -f python3` y `git push --force` a main) |
| **`tests/core/test_deploy_honesto.py`** | **NUEVO.** 26 tests |

---

## 4. Cómo se despliega ahora

```bash
# 1. Traer el código
git pull

# 2. Desplegar de verdad (reconstruye y VERIFICA)
./scripts/deploy_prod.sh

# Ver qué haría, sin tocar nada:
./scripts/deploy_prod.sh --dry-run

# Solo recrear, sin reconstruir:
./scripts/deploy_prod.sh --no-build
```

Salida esperada (medida):

```
>> 1. Comprobando el entorno
   [OK] docker disponible
   [OK] compose: docker-compose (Docker Compose version v5.5.1)
   [OK] docker-compose.prod.yml presente
   [OK] python: .venv/Scripts/python.exe
>> 3. Validando docker-compose.prod.yml
   [OK] compose valido (23 servicios definidos)
```

Y en CI, en un `workflow_dispatch` con `environment: prod`, el job de producción
ahora **dice la verdad**:

> **Este workflow NO despliega en produccion.** No hay runner autoalojado ni
> destino remoto: la produccion es el PC del usuario.
> Para desplegar de verdad: `git pull && ./scripts/deploy_prod.sh`

---

## 5. Cómo se ha verificado

| Comprobación | Resultado |
|---|---|
| Health gate contra el PC real | `21/21 sanos, 100%, exit 0` (antes `14/21, 66.67%, exit 1`) |
| `deploy_prod.sh --dry-run` | exit 0, no toca nada |
| Guardia de Termux | `bash scripts/deploy.sh` → exit 1, *"SOLO para Termux"* |
| Los 5 workflows parsean | OK |
| Suite completa con el filtro del CI | **975 passed, 0 failed** (antes 949) |
| **Los tests probados en su rama de fallo** | Se reintrodujo `echo "Production deployment completed"` en `cd-21.yml` → el test falló con el mensaje exacto; revertido → verde |

---

## 6. Lo que NO se ha podido verificar (y por qué)

* **Un run verde en GitHub Actions.** La cuota de Actions está agotada: los jobs
  fallan con `steps: []` y `runner_name: ''` (no es el código — ver
  [[INCIDENTE-GIT-2026-09-18]] §5 y `MEMORY.md` regla 9). Los YAML parsean y los
  tests pasan, pero **el verde real no se ha observado**.
* **Un `deploy_prod.sh` completo (sin `--dry-run`).** Reconstruir 23 servicios
  es pesado y cambiaría el estado de los contenedores que el usuario tiene
  levantados. El preflight y el camino de error sí están ejercitados.

---

## 7. Lecciones

1. **Un "no se puede" no autoriza un "digo que sí".** Lo que estaba mal no era
   comentar la orden imposible, sino imprimir "completado" después.
2. **Un health check que no puede fallar no es un health check.** El de `cd.yml`
   imprimía 11 ✓ y no tenía ni un `curl` activo.
3. **El gate que decide si el despliegue está bien también puede mentir.** 7 de
   21 falsos negativos: peor que no tener gate, porque enseña a ignorar el rojo.
4. **Los fallos de "solo en la máquina real" no aparecen en CI.** El plugin
   `docker compose` existe en el runner y no en el PC: el CI nunca lo habría
   detectado.
5. **Una ruta inventada da 404 y parece un servicio caído.** `/status` vs
   `/api/status`: 19 falsos `OFFLINE`.
6. **El proxy convierte "caído" en 502.** Un 502 parece un problema del gateway;
   la causa real era "no hay nadie escuchando".

---

## Enlaces

[[EPICAS-ARREGLO-2026-09-18]] · [[RESET-ARQUITECTURA-2026-09-18]] ·
[[AUDITORIA-2026-09-18]] · [[INCIDENTE-GIT-2026-09-18]] · [[INDEX]]
