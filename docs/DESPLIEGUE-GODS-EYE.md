# Despliegue del Visor God's Eye — siguientes pasos

**Fecha:** 2026-09-21 · Visor v2.0 · **actualizado tras la unificación**

> **Estado actual: los 4 bloqueos de código están resueltos** (ver §0.1).
> Solo queda la parte de infraestructura/credenciales (Stripe, vendor).

---

## 0. Resumen honesto

El visor **funciona en local** (verificado). Al revisar la infraestructura
aparecieron 5 bloqueos reales — encontrados leyendo los ficheros, no
suponiéndolos.

**Corrección importante:** al verificarlo de verdad, el bloqueo 1 resultó ser
mucho mayor de lo que decía la primera versión de esta guía. No era **una**
ruta `COPY` rota: eran **las 7**. El Dockerfile entero estaba congelado en el
layout anterior al refactor de la Fase 2.

| # | Bloqueo | Evidencia | Estado |
|---|---|---|---|
| 1 | **Las 7 rutas `COPY` apuntan a ficheros que ya no existen** | `Dockerfile:6-12` copiaba `./agent_*.py` y `./message_broker.py`; los 7 ficheros viven ahora en `agents/` y `core/` | ✅ **resuelto** |
| 2 | `aig/` nunca se copia a la imagen | 0 coincidencias de `aig` en el Dockerfile | ✅ **resuelto** |
| 3 | El servidor no registraba el visor | 0 coincidencias de `gev` en `server.py` | ✅ **resuelto** |
| 4 | El vendor de Cesium (22 MB) no se copia | está en `.gitignore` | 🟠 aviso en build + script |
| 5 | Rutas equivocadas en `WHITE-LABEL.md` y en el compose | compose en `config/`, doc apuntaba a la raíz | ✅ **resuelto** |

**Bloqueo 5 era más profundo de lo que parecía.** No era solo la documentación:
el `docker-compose.enterprise.yml` era **inválido**. Lo verifiqué con
`docker-compose config`:

- `context: .` resolvía a `<repo>\config` → buscaba
  `config/daniela-os/Dockerfile`, **que no existe** → fallaban todos
  los servicios. Arreglado con `--project-directory .`.
- El overlay definía el servicio `daniela-os`, que **no coincide** con ningún
  servicio del compose base (`daniela`) → no se fusionaban y quedaba un servicio
  sin `image` ni `build` → `invalid compose project`. Renombrado a `daniela`.
- `scripts/deploy/tenant_bootstrap.py` calculaba `REPO_ROOT` como `parents[1]`,
  que resolvía a `<repo>/scripts`: habría creado los tenants en
  `scripts/tenants/`. Y `import white_label` fallaba por falta de ruta.

**Verificado de punta a punta:** crear un tenant de prueba → el perfil
`enterprise` **valida** y todas las rutas resuelven a la raíz del repo
(`tenants/<slug>/…`, `static/tenants/<slug>/…`). Tenant de prueba borrado.

> De paso apareció un bug que afectaba a más sitios: `aig/core/paths.py`
> calculaba `REPO_ROOT = parents[3]`, que resolvía a `C:\Users\Alejandro`
> — **fuera del proyecto**. Corregido a `parents[2]`. `ensure_dirs()` nunca se
> llamó, así que no llegó a crear carpetas en tu home.

> El bloqueo 1 **no lo causé yo**: viene del refactor de reubicación pendiente.
> `message_broker.py` se movió a `core/` y `aig/core/`, pero el Dockerfile
> seguía apuntando a la raíz.

### 0.1 Qué se hizo (verificado)

| Cambio | Fichero | Verificación |
|---|---|---|
| Las 7 rutas `COPY` corregidas + `COPY ./aig/` | `daniela-os/Dockerfile` | **12/12 orígenes existen, 0 rotas** |
| Daniela integra aig en una sola app | `daniela-os/server.py` | fase `aig` añadida |
| Punto de entrada único | `aig/daniela.py` (nuevo) | **4/4 fases OK, 24 rutas** |
| Aviso en build si falta Cesium | `Dockerfile` | `RUN test -f .../Cesium.js` |

**Consecuencia arquitectónica:** como el visor se registra **dentro** de
`daniela-os/server.py`, **ya no hace falta un servicio aparte** en
`docker-compose.yml`. El visor es una parte más de Daniela, en el puerto 9200.
Eso es justo lo que pedías: *"Daniela Omnipresente es Daniela"*.

---

## 1. Despliegue local (funciona hoy, 2 minutos)

Esta es la vía que **ya está probada**. Úsala para enseñar el visor.

```bash
cd C:\Users\Alejandro\aig

# 1. Assets de Cesium (una sola vez, ~22 MB)
python scripts/setup_gev_vendor.py

# 2a. Solo el visor (puerto 8090)
python aig/gev/server.py --puerto 8090

# 2b. O Daniela completa, con el visor dentro (puerto 9200)
python daniela-os/server.py

# 3. Abrir
#    http://127.0.0.1:8090/gods-eye      (solo visor)
#    http://127.0.0.1:9200/gods-eye      (Daniela completa)
```


**Verificación:**

```bash
curl -s -o /dev/null -w "%{http_code}\n" http://127.0.0.1:8090/gods-eye        # 200
curl -s -o /dev/null -w "%{http_code}\n" http://127.0.0.1:8090/api/globe/data  # 200
```

**Para arrancarlo solo, en segundo plano (Windows):**

```powershell
$accion = New-ScheduledTaskAction -Execute "python" `
  -Argument "aig\gev\server.py --puerto 8090" `
  -WorkingDirectory "C:\Users\Alejandro\aig"
Register-ScheduledTask -TaskName "GEVer" -Action $accion `
  -Trigger (New-ScheduledTaskTrigger -AtLogOn) -RunLevel Highest
```

---

## 2. Antes de contenerizar: arreglar los 3 bloqueos

### Paso 2.1 — Resolver `message_broker.py` (obligatorio)

```bash
cd C:\Users\Alejandro\aig

# ¿Dónde está ahora?
ls core/message_broker.py aig/core/message_broker.py

# Opción A (rápida, recomendada): corregir la ruta en el Dockerfile
#   línea 12:  ./message_broker.py  ->  ./core/message_broker.py
#   y ajustar el destino si el import lo espera en /app/agents/
```

> ⚠️ Antes de tocar, decide con el refactor pendiente: los 6 ficheros borrados
> de `scripts/` (`message_broker.py`, `agents.py`, `connections_manager.py`,
> `sil_engine.py`, `autofix_engine.py`, `auto_swarm_dispatcher.ps1`) siguen sin
> commitear. **Ciérralo primero**: commitear el movimiento como *rename* deja el
> árbol limpio y evita que el Dockerfile apunte a fantasmas.

### Paso 2.2 — Copiar `aig/` a la imagen

Añadir al `daniela-os/Dockerfile`, tras la línea 21:

```dockerfile
# Visor 3D unificado (God's Eye Dashboard)
COPY --chown=appuser:appuser ./aig/core/ ./aig/core/
COPY --chown=appuser:appuser ./aig/gev/ ./aig/gev/
```

Y los assets de Cesium. **No los metas en la imagen**: son 22 MB de estáticos.
Mejor montarlos como volumen de solo lectura:

```yaml
# en config/docker-compose.yml, servicio daniela
    volumes:
      - ./aig/gev/vendor:/app/aig/gev/vendor:ro
      - ./aig/data:/app/aig/data
```

> El volumen de `data/` es **imprescindible**: ahí viven `business.db` y el
> historial de la sede. Sin él, cada reinicio borra tus clientes.

### Paso 2.3 — Registrar el visor en el servidor

En `daniela-os/server.py`, donde ya se registran otras rutas:

```python
try:
    import sys, os
    sys.path.insert(0, "/app")
    from aig.gev.server import register_gev_routes
    register_gev_routes(app)
except ImportError as e:
    print(f"[God's Eye] no disponible: {e}")
```

**Verificar que arranca:**

```bash
curl -s -o /dev/null -w "%{http_code}\n" http://localhost:9200/gods-eye
```

---

## 3. Contenerizar (tras arreglar los bloqueos)

```bash
cd C:\Users\Alejandro\aig

# 3.1 Validar la configuración ANTES de construir
scripts/deploy/compose.sh config

# 3.2 Construir
scripts/deploy/compose.sh build daniela

# 3.3 Levantar
scripts/deploy/compose.sh up -d daniela redis nginx

# 3.4 Comprobar
scripts/deploy/compose.sh ps
curl -s -o /dev/null -w "%{http_code}\n" http://localhost:9200/api/status
```

> **Usa siempre `scripts/deploy/compose.sh`, no `docker compose` a pelo.** El
> wrapper resuelve tres trampas que no se ven leyendo el compose:
>
> 1. **`--env-file .env`.** El compose vive en `config/`, y Docker Compose
>    resuelve el `.env` respecto a SU directorio. Sin el flag, las claves de los
>    proveedores salen del `config/.env` viejo (con placeholders tipo
>    `OPENAI_API_KEY=YOUR_VALUE_HERE`) en vez del `.env` real de la raíz.
> 2. **El binario.** El plugin `docker compose` (v2) NO está instalado en esta
>    máquina: solo funciona `docker-compose` (suelto). `docker compose version`
>    responde `unknown command`. El wrapper elige el que haya.
> 3. **Rutas relativas y el cwd**, que tienen que ser la raíz del repo porque
>    `docker.exe` no entiende los caminos de Git Bash.

> **Ojo con las rutas**: `WHITE-LABEL.md` dice `-f docker-compose.yml` pero los
> ficheros están en `config/`. Corrige ese documento o crearás confusión.

### Añadir el visor como servicio propio (opcional)

Si prefieres aislarlo del servicio `daniela`:

```yaml
  gods-eye:
    build:
      context: .
      dockerfile: ./aig/gev/Dockerfile
    container_name: aig-gods-eye
    ports:
      - "127.0.0.1:8090:8090"
    volumes:
      - ./aig/gev/vendor:/app/aig/gev/vendor:ro
      - ./aig/data:/app/aig/data
    environment:
      - aig_ADMIN_SECRET=${aig_ADMIN_SECRET}
    restart: unless-stopped
```

> 🔒 Fíjate en `127.0.0.1:8090:8090`, **no** `8090:8090`. Lo segundo expone el
> visor —y los datos de todos tus clientes— a la red.

---

## 4. Marca blanca para un cliente (cuando toque)

```bash
python scripts/deploy/tenant_bootstrap.py crear --slug gestoria-lopez \
  --brand-name "Gestoría López" --domain gestoria-lopez.example.com \
  --primary "#0ea5e9" --admin-email admin@gestorialopez.com
# GUARDA la password y el PIN: se muestran UNA vez.

python scripts/deploy/tenant_bootstrap.py estado --slug gestoria-lopez
```

Y en el sistema de negocio:

```bash
python aig/core/business_store.py alta \
  --nombre "Gestoría López" \
  --direccion "Calle Mayor 1, Madrid, Spain" \
  --tier enterprise --tenant gestoria-lopez --mrr 99
```

El cliente aparecerá como **nodo nuevo en el globo** automáticamente.

---

## 5. Cobro (Stripe) — lo que falta para facturar

```bash
# 1. Crear la cuenta y obtener las claves
# 2. Configurar el secreto del webhook
export STRIPE_WEBHOOK_SECRET="whsec_..."
# 3. Verificar
python -c "import core.billing_system as b; print(b.TIERS['pro']['price_monthly'])"
```

Sin `STRIPE_WEBHOOK_SECRET` no hay confirmación de pago. **Es el paso que
convierte el proyecto en negocio.**

---

## 6. Verificación completa (checklist)

```bash
# Visor
curl -s -o /dev/null -w "visor    %{http_code}\n" http://127.0.0.1:8090/gods-eye
curl -s -o /dev/null -w "data     %{http_code}\n" http://127.0.0.1:8090/api/globe/data
curl -s -o /dev/null -w "cesium   %{http_code}\n" http://127.0.0.1:8090/gods-eye/vendor/cesium/Cesium.js

# Control de acceso (debe diferir)
curl -s http://127.0.0.1:8090/api/globe/data | grep -o '"sede"' | head -1   # sede
curl -s -H "X-Tenant-Slug: gestoria-lopez" http://127.0.0.1:8090/api/globe/data \
  | grep -c '"sede"'                                                        # 0

# Datos
python aig/core/business_store.py resumen
python aig/core/location.py ver

# Red (debe ser 127.0.0.1, NUNCA 0.0.0.0)
netstat -an | grep 8090 | head -2
```

---

## 7. Rollback

Todo es reversible:

```bash
# Frontend antiguo: ya no hay nada que revertir. El dashboard viejo se archivo
# entero en `archives/frontend/` el 2026-09-22, y `scripts/deprecar_frontend_legacy.py`
# (que movia las vistas una a una) se retiro con el. Para recuperarlo: mover
# `archives/frontend/` a la raiz y restaurar la fase `frontend` en
# `gev/daniela-os/server.py`.

# Contenedor
scripts/deploy/compose.sh down

# Datos de negocio (¡cuidado, esto sí borra!)
#   aig/data/business/business.db
#   aig/data/location/historial.jsonl
# Copia antes: cp -r aig/data aig/data.bak
```

El backup del frontend original está intacto en
`aig/archive/frontend_legacy_backup/` con manifiesto SHA-256.

---

## 8. Orden recomendado

| # | Paso | Esfuerzo | Desbloquea |
|---|---|---|---|
| 1 | **Cerrar el refactor pendiente** (commitear los 6 movimientos) | 🟢 10 min | el build de Docker |
| 2 | Corregir la ruta de `message_broker.py` en el Dockerfile | 🟢 2 min | el build |
| 3 | Registrar el visor en `server.py` | 🟢 5 min | `/gods-eye` |
| 4 | Copiar `aig/` + volúmenes de datos y Cesium | 🟡 30 min | el visor en contenedor |
| 5 | Construir y levantar | 🟡 20 min | despliegue |
| 6 | **Stripe** | 🟡 1–2 h | **facturar** |
| 7 | Onboarding guiado (alta desde el visor) | 🟡 1 día | vender sin ti |
| 8 | Corregir `WHITE-LABEL.md` (rutas) | 🟢 5 min | evitar confusión |

**Si solo haces una cosa:** el **paso 1**. Sin él, el contenedor no se construye
— y es un movimiento de ficheros que ya está hecho en disco, solo falta
commitearlo.

---

## 9. Lo que NO debes hacer

- ❌ `docker compose up` desde la raíz: los compose están en `config/`.
- ❌ `docker compose -f config/docker-compose.yml up` sin `--env-file .env`: usa el
  `config/.env` viejo y despliega placeholders en vez de las claves reales. Para
  eso existe `scripts/deploy/compose.sh`.
- ❌ `docker compose` (plugin v2): no está instalado aquí. Solo `docker-compose`.
- ❌ Exponer el puerto como `8090:8090` o `--host 0.0.0.0`: el visor muestra los
  datos de **todos** tus clientes.
- ❌ Meter Cesium (22 MB) en la imagen: móntalo como volumen de solo lectura.
- ❌ Desplegar sin el volumen de `aig/data/`: perderás los clientes en cada
  reinicio.
- ❌ Vender SLA 99,9 % sin guardia. Es una promesa que un solo desarrollador no
  puede sostener.
