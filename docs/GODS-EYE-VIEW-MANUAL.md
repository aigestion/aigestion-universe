# God's Eye Dashboard — Manual de usuario y despliegue

**Visor 3D unificado de Daniela OS** · v1.0 · 2026-09-21

---

## 1. Qué es

El **punto de entrada único** de Daniela OS. Un globo 3D donde el negocio se ve:
la Sede, cada empresa cliente y su estado operativo, en tiempo real.

Sustituye al dashboard estático antiguo.

| Antes | Ahora |
|---|---|
| Varios `index_*.html` sueltos | Un visor unificado |
| Listas y tablas | Globo 3D con nodos vivos |
| Sin noción de cliente/empresa | Cada cliente es un nodo con estado |
| Sin control de acceso | Admin ve todo; cliente solo lo suyo |

---

## 2. Arranque rápido

```bash
# 1. Poblar los assets de Cesium (~22 MB, no versionados)
python scripts/setup_gev_vendor.py

# 2. Arrancar el visor (el modulo es daniela-os/gev_server.py desde P1 2026-10-04;
#    `aig/gev/server.py` no existe)
python daniela-os/gev_server.py --puerto 8090

# 3. Abrir
#    http://127.0.0.1:8090/gods-eye
```

Integrado en Daniela OS (recomendado):

```python
from gev.server import register_gev_routes
register_gev_routes(app)
```

> 🔒 **Por defecto escucha solo en `127.0.0.1`.** No uses `--host 0.0.0.0`: el
> visor muestra datos de todos los clientes. Exponerlo a la LAN los filtra.

---

## 3. Uso del visor

### La pantalla

```
┌───────────────────────────────────────────────────────────┐
│ ● God's Eye Dashboard          [empresas] [en globo] [MRR]│
│   Administrador — acceso total      [Sede][Ver todo][⟳]   │
├──────────────┬────────────────────────────────────────────┤
│ NODOS        │                                            │
│ ● Sede       │            GLOBO 3D                        │
│   Alcobendas │     (haz azul = Sede, puntos = empresas)   │
│ ● Gestoría   │                                            │
│   pro·activo │                                            │
└──────────────┴────────────────────────────────────────────┘
```

### Acciones

| Quiero… | Cómo |
|---|---|
| Ver mi sede | Botón **Ir a la Sede** |
| Ver el mundo entero | Botón **Ver todo** |
| Abrir una empresa | Clic en su punto en el globo, o en el panel |
| Abrir el Command Center | Clic en el nodo de la **Sede** |
| Recargar datos | Botón **Refrescar** (o espera: auto cada 60 s) |
| Cerrar un modal | `Esc`, la `×`, o clic fuera |

### El color de cada nodo

| Color | Estado | Significa |
|---|---|---|
| 🟢 Verde | Activo | Operativo, sin incidencias |
| 🟡 Amarillo | Alerta | Telemetría fuera de rango |
| 🔴 Rojo | Incidencia | Error, requiere atención |
| ⚪ Gris | Inactivo | Sin actividad |
| 🔵 Azul | Sede | Tu sede (solo la ves tú) |

La **altura de la columna** de cada empresa indica su plan:
Enterprise > Pro > Free.

### Command Center (clic en la Sede)

Modal holográfico con acceso a las herramientas de Daniela OS:

- **Astra Document Sniper** — ingesta RAG
- **Voice Briefing Agent** — síntesis TTS / resúmenes
- **Inbox Zero Drafter** — triaje de correo y WhatsApp
- **Life Telemetry HUD** — hardware, sensores, ESP32, Termux
- **Command & Control** — terminal de agentes y logs

> ⚠️ Los botones están cableados a la interfaz. El enganche real con cada
> backend de Daniela está marcado en `viewer.js` (`SALIDAS`) y **pendiente**.

### Estructura de empresa (clic en una empresa)

La cámara hace zoom y se despliega:

- **Métricas**: plan, estado, MRR, eventos en 24 h
- **Estructura 3D**: módulos (Dirección, Operaciones, Datos/RAG,
  Automatizaciones, + Integraciones y Marca Blanca según plan) con barra de
  estado
- **Telemetría reciente**: últimos eventos de esa empresa

---

## 4. Gestión de clientes (usuarios de negocio)

```bash
# Alta (geocodifica la dirección automáticamente)
python aig/core/business_store.py alta \
  --nombre "Gestoría López" \
  --direccion "Calle Mayor 1, Madrid, Spain" \
  --tier pro --email hola@gestorialopez.es --mrr 29

# Listar
python aig/core/business_store.py listar

# Cambiar estado -> cambia el color en el globo
python aig/core/business_store.py estado gestoria-lopez incidencia \
  --mensaje "RAG sin responder"

# Resumen del negocio
python aig/core/business_store.py resumen
```

---

## 5. La Sede dinámica

```bash
# Ver la sede actual
python aig/core/location.py ver

# Volver a detectar por IP
python aig/core/location.py detectar --forzar

# Fijarla a mano
python aig/core/location.py fijar 40.4168 -3.7038 --etiqueta "Sede Madrid"

# Historial de cambios
python aig/core/location.py historial
```

También por entorno: `aig_HQ="40.4168,-3.7038,Sede Madrid"`.

> **No rompe el RAG.** El estado vive en `actual.json` y cada cambio se **anexa**
> a `historial.jsonl`. Nunca se sobrescribe: se puede reconstruir dónde estaba
> la sede en cualquier fecha.

---

## 6. Control de acceso

| Rol | Ve la Sede | Ve empresas | Ve agregados | Cómo se identifica |
|---|---|---|---|---|
| **admin** | ✅ | todas | ✅ | sin cabecera de tenant (o `X-Admin-Secret`) |
| **cliente** | ❌ | solo la suya | ❌ | `X-Tenant-Slug: <su-slug>` |

```bash
# Como admin
curl http://127.0.0.1:8090/api/globe/data

# Como cliente
curl -H "X-Tenant-Slug: gestoria-lopez" http://127.0.0.1:8090/api/globe/data
```

> **Fail-closed**: si el rol es desconocido, el tenant está vacío o el id no
> coincide, se **deniega**. Nunca "permitido por defecto".

Para exigir secreto de admin: define `aig_ADMIN_SECRET` y mándalo en
`X-Admin-Secret`.

---

## 7. API

| Método | Ruta | Qué hace |
|---|---|---|
| GET | `/gods-eye` | El visor (HTML) |
| GET | `/api/globe/data` | Nodos del globo (filtrado por rol) |
| GET | `/api/globe/cliente/<id>` | Detalle + estructura 3D |
| POST | `/api/globe/cliente/<id>/estado` | Cambiar estado `{"estado":"alerta"}` |
| GET | `/api/globe/eventos?cliente=<id>` | Telemetría reciente |
| GET | `/api/globe/stream` | SSE de telemetría en vivo |

---

## 8. Despliegue

### Requisitos

- Python 3.10+ con `flask` y `requests`
- Los assets de Cesium (`setup_gev_vendor.py`)
- Opcional: God's Eye View instalado (para las capas OSINT)

### Comprobar que está sano

```bash
curl -s -o /dev/null -w "%{http_code}\n" http://127.0.0.1:8090/gods-eye          # 200
curl -s -o /dev/null -w "%{http_code}\n" http://127.0.0.1:8090/api/globe/data    # 200
python scripts/setup_gev_vendor.py --comprobar                              # OK
```

### Red

| Escenario | Cómo |
|---|---|
| Solo tu máquina (recomendado) | por defecto, `127.0.0.1` |
| Detrás de nginx con auth | proxy a `127.0.0.1:8090` + autenticación propia |
| **Nunca** | `--host 0.0.0.0` sin auth delante |

### Datos y estado (no versionados)

```
aig/data/location/    actual.json, historial.jsonl
aig/data/business/    business.db, geocode_cache.json
aig/gev/vendor/  Cesium (22 MB)
```

---

## 9. Frontend antiguo (ya archivado)

**No hay nada que hacer: el dashboard viejo ya está apagado.**

El 2026-09-22 se archivó la carpeta entera en `archives/frontend/` y se retiró la
fase `frontend` de `gev/daniela-os/server.py`. El script que hacía el apagado
paso a paso (`scripts/deprecar_frontend_legacy.py`) se retiró también: movía las
vistas a `aig/archive/`, rutas que ya no existen.

El nuevo punto de entrada es `/gods-eye` (Visor 3D unificado).

Para recuperar el dashboard antiguo, las tres cosas a la vez:

1. Mover `archives/frontend/` a la raíz del repo.
2. Añadir su `COPY` al Dockerfile de Daniela.
3. Descomentar la fase `("frontend", ...)` en `gev/daniela-os/server.py`.

Hacer solo una de las tres deja la fase fallando en el contenedor; el test
`test_daniela_frontend_sigue_retirada` lo detecta.

---

## 10. Problemas frecuentes

| Síntoma | Causa | Solución |
|---|---|---|
| Globo en negro | Faltan assets de Cesium | `python scripts/setup_gev_vendor.py` |
| "Sin acceso a esa empresa" | Tu rol no es admin | Manda `X-Tenant-Slug` correcto |
| La sede no aparece | Eres cliente | Es intencional: la sede es privada |
| Empresa sin ubicar | Geocodificación falló | `business_store.py ubicar <id> "<dirección>"` |
| La sede está en el sitio raro | Geolocalización por IP | `location.py fijar <lat> <lon>` |
| No llega telemetría | SSE bloqueado por proxy | Revisa `X-Accel-Buffering: no` |

---

## 11. Lo que aún no está conectado

Sé honesto con el estado real:

- **Botones del Command Center** → interfaz lista, backend pendiente.
- **Cobro real (Stripe)** → `STRIPE_WEBHOOK_SECRET` sin configurar.
- **Alta de cliente desde el visor** → funciona por CLI/API, falta el botón.
- **Capas OSINT dentro del visor** → el visor es propio; God's Eye View corre
  aparte en `:4173`. Se pueden integrar reutilizando `core/gev_bridge.py`.
