# Daniela unificada — todo conectado

**Fecha:** 2026-09-21 · Daniela OS v2.0

---

## 0. La idea

> *"Daniela Omnipresente es Daniela. Unifica e integralo todo. Daniela es todo."*

Antes Daniela estaba partida en dos mundos que no se hablaban:

- `daniela-os/server.py` — el servidor real (131 módulos, puerto 9200)
- `aig/` — el visor 3D, el OSINT, el negocio… **sin que nadie los registrara**

Resultado: el visor funcionaba suelto en el 8090 y **no existía** dentro del
servidor de verdad. Dos productos, un solo nombre.

Ahora hay **una sola llamada**:

```python
from aig.daniela import registrar
registrar(app)        # <- y Daniela queda completa
```

Y esa llamada ya está dentro de `daniela-os/server.py`, como una fase
más, junto a `ambient`, `consciousness`, `guardian`…

**Un servidor. Un puerto (9200). Un producto.**

---

## 1. Lo que se ha conectado

### 1.1 Los botones del Command Center → backends reales

Antes los 5 botones del modal de la Sede imprimían texto fijo y
`[pendiente de conectar al backend]`. Ahora llaman a endpoints reales:

| Botón | Endpoint | Backend real | Estado |
|---|---|---|---|
| Astra Document Sniper | `GET /api/cc/astra` | `MemoryVault.stats()` (RAG) | ✅ |
| Voice Briefing Agent | `GET /api/cc/voz` | `PiperEngine` + briefing compuesto | ✅ |
| Inbox Zero Drafter | `GET /api/cc/inbox` | `EmailZeroInbox` | ✅ |
| Life Telemetry HUD | `GET /api/cc/telemetria` | `shutil` + `psutil` + `core.health_checks` | ✅ |
| Command & Control | `GET /api/cc/consola` | `app.url_map` + agentes reales | ✅ |

**Nada está inventado.** Cuando un subsistema no está disponible se declara
`conectado: false` con el motivo, en vez de devolver datos falsos. Ejemplos
reales de la última prueba:

- Astra: `docs: 0` → *"Indice vacio: la memoria semantica no tiene documentos."*
- Inbox: *"Clasificador operativo, pero NO hay buzon IMAP configurado."*
- Voice: `tts_disponible: false` → *"Piper no instalado: el briefing se sirve como texto."*
- Consola: `rutas_total: 24`, `agentes: 13`

### 1.2 Facturación real (Stripe)

`handle_stripe_webhook` era un **stub**: devolvía `{"status": "processed"}` y no
tocaba la base de datos. Mentía. Ahora:

- `invoice.payment_succeeded` → inserta el pago, marca la factura como pagada y
  **la crea si Stripe la tiene y nosotros no** (si no, el ingreso no aparecía)
- `customer.subscription.deleted` → `status='cancelled'` + `cancelled_at`
- `customer.subscription.updated` → estado y plan
- **Idempotencia**: Stripe reenvía eventos; el segundo se detecta como
  `duplicado` por `provider_payment_id` y no se cobra dos veces
- Si llega un pago de una suscripción desconocida → `sin_suscripcion`, no un
  falso "processed"

**Firma obligatoria y a fallar cerrado** (`verificar_firma_stripe`):
sin `STRIPE_WEBHOOK_SECRET` **no se procesa nada** (503). Con secreto, la firma
se valida por HMAC-SHA256 y ventana de tolerancia de 300 s.

Rutas: `GET /api/billing/planes` · `GET /api/billing/mrr` (solo admin) ·
`POST /api/billing/stripe/webhook`.

**Bug corregido de paso:** `DB_NAME` era relativo (`billing.db`), así
que el mismo código escribía en bases **distintas** según el directorio de
trabajo. Había dos ficheros vacíos en el repo (raíz y `data/`). Ahora es una
ruta absoluta, configurable con `AIGESTION_BILLING_DB`.

### 1.3 Alta de clientes desde el visor

`POST /api/globe/cliente` (solo admin) + formulario en el panel lateral.
Geocodifica la dirección de verdad (Nominatim) y **deriva el MRR del plan**:

- Si no indicas MRR, se toma de `PRECIO_TIER` (free 0 €, pro 29 €, enterprise 99 €)
- Un `mrr=0` explícito se respeta (descuentos, pruebas)

`comprobar_tiers()` compara el espejo local con `core/billing_system.TIERS` y
detecta divergencias. Verificado: `{'ok': True, 'divergencias': {}}`.

### 1.4 Capas OSINT dentro del visor

Los feeds de God's Eye View entran en **nuestro** globo vía
`core/gev_bridge.py`. Daniela no depende de la interfaz de GEV, solo de sus
datos.

| Capa | Fuente | Necesita GEV | Verificado |
|---|---|---|---|
| `sismos` | USGS directo | **no** | ✅ M5.7 · south of Africa |
| `vuelos` | OpenSky vía GEV | sí | ✅ 4 vuelos a 5,4 km de la sede |
| `militares` | adsb.lol vía GEV | sí | ✅ |
| `incendios` | NASA FIRMS | sí + clave | ⚠️ requiere clave |
| `barcos` | AISStream | sí + clave | ⚠️ requiere clave |
| `camaras` | CCTV público | sí | ✅ |

Cada capa informa de su estado real. Si GEV no responde, la capa se marca
`sin_gev` con el motivo y el checkbox queda deshabilitado — no un globo vacío
sin explicación.

**Decisión de diseño:** el AOI por defecto (radio alrededor de la Sede) se
aplica solo a capas de interés local. Los **sismos** se sirven globales: con
150 km daban 0 resultados casi siempre y ocultaban justo lo que importa.

---

## 2. Idioma: español por defecto, inglés opcional

Un solo catálogo es la fuente de verdad: `aig/gev/i18n.py`.

Resolución, por orden: `?lang=` → cookie `daniela_lang` → `Accept-Language` →
**`es`**.

El visor aplica las cadenas con atributos `data-i18n` y el botón **ES/EN** de la
cabecera; la elección se recuerda en `localStorage`.

```bash
GET /api/i18n        # idioma resuelto
GET /api/i18n/en     # forzar inglés
GET /api/idiomas     # {"defecto": "es", "soportados": [es, en]}
```

En el contenedor: `ENV DANIELA_LANG=es`.

---

## 3. Cómo verificarlo

```bash
# 1. Daniela completa (visor dentro)
python daniela-os/server.py

# 2. Endpoints clave
curl http://127.0.0.1:9200/gods-eye
curl http://127.0.0.1:9200/api/globe/data
curl http://127.0.0.1:9200/api/i18n
curl http://127.0.0.1:9200/api/globe/osint
curl http://127.0.0.1:9200/api/globe/osint/sismos?min_mag=4.5
curl http://127.0.0.1:9200/api/cc/consola
curl http://127.0.0.1:9200/api/billing/planes
```

Resultado esperado: **29 rutas de aig** registradas y las **5 fases** OK.

---

## 3.b Visor completo: el God's Eye View original

El visor propio tiene 6 capas OSINT; el proyecto original tiene **21 capas
registradas (18 visibles)** y toda su superficie de control. No se puede
reimplementar sin perder fidelidad, y **no se puede servir como estatico**: sus
22 proveedores de `/api/*` son middleware de Vite, y su servidor manda
`X-Frame-Options: DENY` (no admite iframe).

La fase `visor_completo` lanza el servidor del original como servicio y lo
expone bajo el mismo origen de Daniela en **`/gods-eye/pro/`** con proxy inverso.
Desde el visor propio hay un boton **"Visor completo"** que lleva ahi.

Detalles completos, requisitos (necesita Node >=24.14) y verificacion:
**[`VISOR-COMPLETO.md`](VISOR-COMPLETO.md)**.

---

## 4. Lo que sigue SIN estar conectado (honestidad)

| Cosa | Estado | Qué falta |
|---|---|---|
| TTS real (voz) | Piper no instalado | `pip install piper-tts` + voces |
| Buzón de correo | sin IMAP configurado | `IMAP_HOST` + credenciales |
| Incendios / barcos | requieren clave | clave FIRMS / AISStream en GEV |
| Cobros reales | código listo | `STRIPE_WEBHOOK_SECRET` + endpoint en Stripe |
| Índice RAG | 0 documentos | ingerir documentos |
| Vendor de Cesium | 22 MB, gitignored | `python scripts/setup_gev_vendor.py` |
| Rutas de `WHITE-LABEL.md` | equivocadas | los compose están en `config/` |

Ninguna de estas se ha simulado ni maquillado: todas se reportan como lo que
son.
