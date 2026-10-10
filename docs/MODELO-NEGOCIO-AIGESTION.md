# Modelo de negocio y expansión — aig

**Fecha:** 2026-09-21
**Estado:** implementado el núcleo (código) + estrategia (este documento)

> ⚠️ **Revisado el 2026-10-04 → [[MERCADO-AIGESTION]].**
> Las §1-4 y §6-8 siguen vigentes (precios, unit economics, acceso, riesgos).
> **§5 (white-label a gestorías) ya no es *el* modelo**: es la vía D de cuatro
> (A usuario final, B negocio, C self-hosted, D B2B2B). La tesis actualizada y
> el roadmap con gates están en `docs/MERCADO-AIGESTION.md`.

---

## 1. Qué es aig, en una frase

> **aig no vende software de gestión. Vende un centro de mando:**
> una plataforma donde un negocio ve y opera todo lo suyo — datos, agentes,
> automatizaciones, telemetría — sobre un globo 3D, con una IA (Daniela) que
> trabaja dentro.

La diferencia no es la lista de funciones. Es que **el negocio se ve**. Ningún
competidor de gestión pone tu empresa, tus sedes y tus incidencias en un mapa
del mundo que puedes orbitar.

---

## 2. El cliente es un usuario de negocio

Corrección de modelo importante: **un cliente NO es un contacto en una agenda.**

| Un contacto (modelo viejo) | Un usuario de negocio (modelo aig) |
|---|---|
| Nombre, teléfono, nota | Identidad + marca propia (tenant) |
| Sin relación con el producto | Plan contratado (tier) con límites reales |
| No aparece en ningún sitio | **Nodo en el globo**, con color por estado |
| No genera telemetría | Eventos, incidencias, MRR |
| Se gestiona a mano | Se aprovisiona con `tenant_bootstrap.py` |

Implementado en `aig/core/business_store.py`:

```
Cliente = identidad + tenant_slug + tier + direccion geocodificada
        + estado (activo|alerta|incidencia|inactivo) + eventos + mrr
```

El estado determina el **color del nodo** en el visor: verde, amarillo, rojo.
Eso convierte el panel de clientes en un **cuadro de mando operativo**: de un
vistazo sabes qué cliente está sufriendo.

---

## 3. Jerarquía de acceso (implementada y probada)

```
                    ┌──────────────────────────┐
                    │   ADMIN (tú)             │
                    │   · ve TODAS las empresas│
                    │   · ve la SEDE           │
                    │   · ve agregados y MRR   │
                    └────────────┬─────────────┘
                                 │  no accesible hacia arriba
        ┌────────────────────────┼────────────────────────┐
        ▼                        ▼                        ▼
  ┌───────────┐           ┌───────────┐            ┌───────────┐
  │ Cliente A │           │ Cliente B │            │ Cliente C │
  │ solo lo   │           │ solo lo   │            │ solo lo   │
  │ suyo      │           │ suyo      │            │ suyo      │
  └───────────┘           └───────────┘            └───────────┘
```

**Reglas duras** (`aig/core/access.py`, 10/10 casos verificados):

- Un cliente **nunca** ve la Sede.
- Un cliente **nunca** ve otra empresa — ni su existencia.
- Un cliente **nunca** ve agregados (total de clientes, MRR global): filtrarían
  información de la competencia.
- **Fail-closed**: rol desconocido, tenant vacío o id que no cuadra ⇒ denegado.

> Esto no es un detalle técnico, es la propuesta de valor. Un cliente que
> contrata aig no puede ver a tu otro cliente. Sin eso, no hay negocio
> posible con varios clientes a la vez.

---

## 4. Planes y precios

Los planes **ya existen** en `core/billing_system.py`. El visor los respeta:

| | **Free** | **Pro** | **Enterprise** |
|---|---|---|---|
| Precio mensual | 0 € | **29 €** | **99 €** |
| Precio anual | 0 € | 290 € (−17 %) | 990 € (−17 %) |
| Peticiones/día | 100 | 1.000 | ilimitado |
| Concurrentes | 2 | 10 | 50 |
| Módulos | 3 | todos | todos |
| **Marca blanca** | — | — | ✅ |
| **Visor 3D** | 1 nodo | todos sus nodos | todos + telemetría en vivo |
| SLA | — | — | 99,9 % |
| Soporte | comunidad | email | prioritario |

### Ajustes recomendados

1. **El visor 3D debe ser el gancho de Pro.** Free ve su nodo; Pro ve su negocio
   entero moviéndose. Es la diferencia más visible entre planes y la más barata
   de mostrar.
2. **Enterprise = marca blanca.** Ya está construido (`tenant_bootstrap.py`):
   cada cliente enterprise recibe su propio dominio, su marca y sus bases de
   datos aisladas. Coste marginal ≈ 0, precio ×3,4.
3. **Subir Pro a 39 €** cuando el visor esté en producción. Con el globo como
   diferencial, 29 € está por debajo de lo que el producto sostiene.

---

## 5. La expansión: white-label en una caja

Ya construido y documentado en `docs/WHITE-LABEL.md`:

```bash
python scripts/deploy/tenant_bootstrap.py crear --slug mi-gestoria \
  --brand-name "Mi Gestoria" --domain gestoria.example.com \
  --primary "#0ea5e9" --admin-email admin@example.com
```

Crea `tenants/<slug>/` con sus DBs, su `.env`, su marca y su stack Docker.
**Cero cambios en el código del tenant**: solo mounts y variables.

### Por qué esto es la palanca de expansión

| Vía | Qué cuesta | Qué escala |
|---|---|---|
| Vender aig directo | Soporte por cliente | Lento, alto contacto |
| **Marca blanca a gestorías** | Aprovisionar (2 min) | **Cada gestoría trae sus clientes** |
| API / integraciones | Desarrollo puntual | Medio |

**La jugada:** vender la plataforma a **gestorías y asesorías**, que a su vez
la revenden a sus clientes. Tú no vendes a 1.000 pymes — vendes a 50 gestorías
que ya tienen 20 clientes cada una. El visor 3D es tu argumento de venta hacia
ellos: es lo que ninguna gestoría puede construir sola.

### Estructura de expansión

```
aig (plataforma)
   │
   ├── Enterprise → Gestoría X  (marca blanca, su dominio)
   │                   └── sus clientes (ellos facturan)
   │
   ├── Enterprise → Gestoría Y
   │
   └── Pro/Free → pymes directas
```

Cada gestoría en marca blanca aparece como **un nodo más** en tu globo. Tu
visor se convierte en el mapa de tu propio canal de distribución.

---

## 6. Unit economics (honesto)

**Coste por cliente Free/Pro ≈ 0 €.** Todo el stack funciona con:
- capas de datos públicas sin clave (vuelos, sismos, satélites, cámaras)
- geocodificación gratuita (Nominatim, con caché)
- SQLite local
- LLM: lo único que cuesta de verdad, y está medido (el visor usa $0)

**El coste real es el LLM.** Con Gemini/OpenRouter a los precios actuales, un
cliente Pro con uso normal consume céntimos al mes. El margen bruto de Pro es
alto **siempre que el uso de LLM esté topado** — y ya lo está por tier
(`daily_requests`).

| Concepto | Free | Pro | Enterprise |
|---|---|---|---|
| Ingreso/mes | 0 € | 29 € | 99 € |
| Coste infra | ~0 € | ~0 € | ~0 € (stack propio del tenant) |
| Coste LLM (uso normal) | <1 € | 1–3 € | 3–10 € |
| **Margen bruto** | negativo leve | **~85 %** | **~85 %** |

> El negocio es sano **porque el visor y la geolocalización cuestan 0 €**. Si el
> visor usara APIs de mapas de pago (Google 3D), el margen se iría. Por eso se
> usa Esri/OSM sin clave.

---

## 7. Qué falta para que esto facture

| # | Qué | Estado |
|---|---|---|
| 1 | Modelo de cliente como usuario de negocio | ✅ hecho |
| 2 | Control de acceso admin/cliente | ✅ hecho |
| 3 | Visor 3D con nodos y estados | ✅ hecho |
| 4 | Sede dinámica en el globo | ✅ hecho |
| 5 | Aprovisionamiento de tenants | ✅ ya existía |
| 6 | **Cobro real** (Stripe) | ⚠️ `STRIPE_WEBHOOK_SECRET` sin configurar |
| 7 | **Alta de cliente desde el visor** | ⚠️ existe por CLI/API, falta botón |
| 8 | **Onboarding guiado** (primer cliente en 5 min) | ❌ pendiente |
| 9 | **Página de precios pública** | ❌ pendiente |
| 10 | Métricas de negocio (churn, conversión) | ❌ pendiente |

**El cuello de botella no es el producto: es la cobranza y el onboarding.**
Todo lo difícil (plataforma, aislamiento, visor, acceso) ya está construido.

---

## 8. Riesgos y límites (sin adornos)

- **Multi-tenant por stack, no por proceso.** `WHITE-LABEL.md` lo dice: un
  tenant por stack (`-p <slug>`). Escala a decenas, no a miles, sin refactor.
- **Un solo desarrollador.** El soporte enterprise (SLA 99,9 %) con una persona
  es una promesa difícil de sostener. Vender SLA antes de tener guardia es un
  riesgo real.
- **Dependencia de datos públicos.** Las capas del globo dependen de OpenSky,
  USGS, CelesTrak. Si una cae, se degrada (no se rompe), pero conviene avisarlo.
- **La línea ética del visor.** El proyecto del que deriva (God's Eye View)
  prohíbe explícitamente la búsqueda de personas y el reconocimiento facial.
  **Mantén esa línea.** Es también una protección legal y reputacional.

---

## 9. La apuesta a 12 meses

1. **Ahora:** cerrar cobranza (Stripe) + onboarding en 5 minutos.
2. **Trimestre 1:** 10 clientes Pro directos. El visor como demo de venta.
3. **Trimestre 2:** primera gestoría en marca blanca. Validar el canal.
4. **Trimestre 3:** 5 gestorías → ~100 pymes indirectas.
5. **Trimestre 4:** el globo muestra el canal entero. aig deja de ser una
   herramienta y pasa a ser **infraestructura** de otros negocios.

> **La tesis:** el valor no está en las funciones de gestión — hay cientos.
> Está en **ver el negocio entero de un vistazo, sin poder ver el del vecino**.
> Eso es lo que el visor 3D + el control de acceso acaban de hacer posible.
