# Mercado y alineamiento de producto — Aigestion

**Fecha:** 2026-10-04
**Estado:** análisis + roadmap (no toca código)
**Sustituye como referencia estratégica a:** `docs/ROADMAP_MASTER.md` (stale, dominio histórico `aig.net`), `docs/PHASES.md` (stale, todas DONE) y a la §5 de `docs/MODELO-NEGOCIO-AIGESTION.md` (el canal de gestorías pasa a ser *una vía más*, no el producto).

> **Una frase:** Aigestion no vende software de gestión ni vende gestorías.
> Vende **un universo por persona y por negocio**, con IA que trabaja dentro,
> donde **cada usuario entra con su cuenta Google y aporta sus propias APIs y
> conexiones**, y donde la infraestructura corre en nuestra nube *o* en el
> servidor del propio usuario (híbrido).

---

## 1. Tesis reinventada

### 1.1 El producto tiene dos lados, no uno

El documento anterior (`docs/MODELO-NEGOCIO-AIGESTION.md:135-151`) describía
una sola jugada: vender la plataforma a gestorías que la revenden a sus
clientes (B2B2B). Esa jugada sigue siendo **válida pero deja de ser el centro**.

| | **Lado admin (operador)** | **Lado usuario final** |
|---|---|---|
| Quién | Tú / white-label Enterprise | Cualquier persona o negocio |
| Entra con | Credenciales propias, CLI | **Cuenta Gmail/Google** |
| Aporta | Infraestructura (23 servicios) | **Sus APIs y sus conexiones** (BYOK) |
| Ve | El globo con todos los tenants | **Su** universo: sus nodos, sus capas |
| Paga | — | Free / Pro / Enterprise (`docs/MODELO-NEGOCIO-AIGESTION.md:85-99`) |

El concepto de **universo** ya existe en el código, no es una invención de este
documento:

- `static/brand/universe_bible.json` (generado por `content/content_calendar.py:759`)
- `daniela-os/capas_usuario.py` — capas personalizadas por usuario en el visor, con tests en `tests/gev/test_capas_usuario.py`
- Rama `universo-v1` y `config/docker/docker-compose.universes.yml`
- Control de acceso admin/cliente implementado y probado: `core/access.py:37-221` (`Sujeto`, `puede_ver_cliente`, `exigir_operar`, `filtrar_clientes`)

### 1.2 La gestoría es una skill más

`docs/MODELO-NEGOCIO-AIGESTION.md` describe facturación, clientes y tenants.
Todo eso **sigue dentro del producto**, pero como un módulo que un usuario
final o un admin puede usar, no como la definición de la empresa. La misma
plataforma soporta: clínica, tienda multi-sede, comunidad, creator, isla
personal. El `core/business_store.py` es un store más, no el corazón.

### 1.3 BYOK: el usuario aporta sus claves

Hoy las claves salen del *shell* del operador
(`docs/WHITE-LABEL.md:32`: `GEMINI_API_KEY`, `OPENROUTER_API_KEY`). El paso
que redefine el modelo es que **cada usuario configure sus propias conexiones
desde la UI**, algo que ya tiene back-end y rutas listas:

- `core/connections_manager.py:580-616` — `GET/PUT/DELETE/POST /api/connections/*`
- `core/connections_manager.py:154-163` — proveedor `google_oauth` con scopes `gmail.modify` y `drive.file`
- `core/connections_manager.py:417-431` — estado real por proveedor: `configured` / `missing` / `oauth_needed`

Ese back-end es el 80 % de lo que en §1.1 llamamos "aporta sus APIs". Lo que
falta es el front-end de onboarding y el aislamiento por usuario (hoy es por
tenant).

### 1.4 Híbrido: nuestra infra + self-hosted

Decisión ya tomada: **nuestra infraestructura por defecto, con opción
self-hosted** para quien quiera su propio servidor (mismo bundle que
`docs/ADR-022-CANAL-CODIGO-TELEFONOS.md` ya usa para los teléfonos). No son
dos productos: es el mismo artefacto instalado en dos sitios. La regla
`docs/POLITICA-GRATIS.md:3` ("toda herramienta debe poder ser gratuita o
self-hosteable") es coherente con esta vía y con el competidor
open-source que ya existe (ver §3).

---

## 2. Tamaño de mercado y posibilidades expandidas

### 2.1 Mercado global (TAM)

| Segmento | Cifra | Fuente |
|---|---|---|
| AI Agents (global) | 7,84 B$ (2025) → **52,62 B$ (2030)**, CAGR 46,3 % | MarketsandMarkets, ago 2026 |
| AI Agents (global, otra casa) | 10,9 B$ (2026) → **182,9 B$ (2033)**, CAGR 49,6 % | Grand View Research, jun 2026 |
| Agentic AI (global) | 19,33 B$ (2026) → **205,88 B$ (2033)**, CAGR 40,2 % | MarketsandMarkets |
| AI companion (global) | 38,64 B$ (2025) → **415,02 B$ (2034)**, CAGR 30,18 % | Insight Partners |

Cuatro casas, cuatro rangos, una misma conclusión: **el mercado crece a
40-50 % anual durante al menos 7 años**. El desacuerdo entre fuentes (52 B$ vs
183 B$ en 2030) es normal en una categoría tan nueva; lo prudente es usar el
rango bajo.

### 2.2 España (SAM) — donde compiten las 4 vías

| Dato | Cifra | Fuente |
|---|---|---|
| **Agentic AI España** | 84,5 M$ (2025) → **1.292,9 M$ (2030)**, CAGR 47,7 % | MarketsandMarkets, ago 2026 |
| Empresas ES 10+ empleados usando IA | 12,4 % → **21,1 %** (1T 2024 → 1T 2025) | INE |
| Incluyendo microempresas (95 % del tejido) | 4 % (2021) → **14 % (2025)** | CaixaBank Research / INE |
| Empresas de menos de 50 empleados | **18 %** (vs 57 % de las grandes) | CaixaBank Research |
| Población ES que usó IA generativa | **45,1 %** (6ª del mundo) | Microsoft AI Economy Institute, sep 2026 |
| Pymes ES que invertirán en IA en 2026 | **35 %** (eran 22 % en 2025) | YouGov para IONOS |
| Pymes ES que **no** usan IA ni la planean | 45,3 % | Cámara de Comercio de España |
| Principal obstáculo | **45,8 %**: falta de personal cualificado | Banco de España (EBAE) |
| Peso de IA en administración/gestión | 28,7 % de los que ya usan IA | INE / Eurostat |
| Asesorías: automatización de contabilidad | 35 % (41 % resumen de documentos) | Future Ready Accountant 2025 |
| PIB potencial por IA en pymes ES | hasta **120.000 M€** (+8 %/año) | Google / Implement Consulting |

**Lectura:** hay demanda (35 % de pymes va a invertir), hay fricción (45,8 %
se queda sin personal cualificado) y hay un hueco estructural (solo 18 % de
las empresas pequeñas usan IA frente al 57 % de las grandes). El producto
justamente ataca esa fricción: delegar en una IA que ya tiene tus conexiones.

### 2.3 Las 4 vías expandidas (antes había 1)

| # | Vía | Quién paga | Encaja con el producto de hoy | Esfuerzo |
|---|---|---|---|---|
| **A** | **Usuario final individual** (universo personal, companion, productividad) | 29 €/mes Pro, 0 € Free | Alto: globo, capas, Daniela, memoria | Medio (falta login + onboarding) |
| **B** | **Negocio pequeño** (multi-sede, clientes, facturación) | 29-99 €/mes | Muy alto: `business_store`, `access.py`, visor | Bajo: ya está construido |
| **C** | **Self-hosted / open-source** (descarga e instalas en tu servidor) | Soporte / hosting opcional | Alto: ADR-022 ya define el bundle | Medio: empaquetado e instalador |
| **D** | **B2B2B white-label** (gestorías, asesorías, agencias) | Enterprise 99 €/mes × tenant | Total: `scripts/deploy/tenant_bootstrap.py:13-14` | Bajo: ya existe |

La vía D es la única que el documento anterior trataba como *el* modelo. Las
cuatro conviven sin canibalizarse: A y B son la base, C es la puerta de entrada
de quien no confía en la nube, D es la palanca de distribución.

**SOM realista (honesto, abajo-arriba con nuestros precios):**

- 12 meses: 100 usuarios Pro directos (29 €) ≈ **2.900 €/mes ≈ 34.800 €/año**
- + 3 tenants Enterprise (99 €) ≈ 3.564 €/año
- **Total ≈ 38.000 €/año** con coste de infraestructura ≈ 0 € (ver §4)
- Ese SOM es ~0,3 % del mercado agentic-AI español de 2026, es decir: no
  necesitas ganar una cuota relevante para que el negocio cierre.

> Nota: el denominador de empresas españolas por tamaño (CIRCE/INTECO) **no está
> verificado en este documento**; si necesitas un TAM en € para una ronda o un
> banco, medirlo es una tarea aparte, no se estima aquí.

---

## 3. Competencia

### 3.1 Directos en España

| Competidor | Qué hace | Diferencia con nosotros |
|---|---|---|
| **losagents.ai** (Barcelona) | Agentes de IA para empresas | Sin globo 3D, sin universo, sin self-hosted |
| **Hi-Ai** (Valencia) | Equipos de agentes que automatizan pymes (leads, atención, operaciones) | Servicio/consultoría; no es un producto que el usuario habita |
| **Automatiza PyMES** (Cunit, 2026, 1 persona) | Automatización de procesos manuales | Consultoría a medida, sin plataforma propia |
| **IA FOR PYMES** (Reus) | Agentes, chatbots, CRM inteligente | CRM tradicional con IA encima |
| **Asistentes virtuales / consultoras digitales** | Implementan herramientas de terceros (n8n, ChatGPT) | Revenden herramientas; no tienen producto propio |

Ninguno de los cinco ofrece: visor 3D del propio negocio, universo por usuario,
aislamiento multi-tenant por stack ni ejecución en el móvil del usuario. La
competencia española en este segmento es **mayoritariamente servicios**, no
software con producto propio — eso es una ventaja de márgenes.

### 3.2 Plataformas de automatización (sustitutos)

- **n8n / Make / Zapier** — el sustituto real para "mis flujos automatizados".
  n8n self-hosted es gratis y ya está en nuestra lista blanca
  (`docs/POLITICA-GRATIS.md`). No tienen asistente con memoria ni visor.
- **ChatGPT / Gemini / Claude** — el sustituto real para "un asistente que me
  ayude". No tienen mis datos, mis conexiones ni mi globo.

Nuestro ángulo frente a ambos: **contexto persistente + conexiones propias +
visión espacial del negocio**. Frente a n8n: n8n te deja *construir* el flujo;
Aigestion ya lo tiene andando con tu memoria.

### 3.3 Self-hosted / open-source (la vía C ya tiene competidor)

- **OpenClaw** — agente self-hosted, multi-modelo, con WhatsApp / Discord /
  Telegram / Slack. Documentación activa y comunidad. Es el referente de la
  vía C: valida que la demanda de "mi agente en mi servidor" existe, y marca
  el listón de instalación que tenemos que igualar.
- **n8n + claw** — plantillas de agentes self-hosted sobre n8n.
- **BYOK apps** — `byok.tech` ("AI apps without subscriptions") y
  `agentkey.dev` (gestión de credenciales para agentes) validan que BYOK es
  una categoría, no una particularidad nuestra.

### 3.4 Gestorías y software de gestión (el competidor del módulo, no del producto)

El módulo de facturación compite con las gestorías digitales españolas y con
los programas de facturación clásicos. Ahí la ventaja **no** es funcional
(están muy afinados en normativa) sino la combinación: el mismo producto hace
gestión *y* el resto del universo, con IA y BYOK. Por eso la gestoría es una
skill más y no el centro: **no vamos a ganar una batalla funcional contra una
gestoría, y tampoco hace falta**.

---

## 4. Unit economics (híbrido + BYOK)

El trabajo previo de `docs/MODELO-NEGOCIO-AIGESTION.md:158-182` sigue siendo
válido y se refuerza con BYOK:

| Concepto | Free | Pro (29 €) | Enterprise (99 €) |
|---|---|---|---|
| Ingreso/mes | 0 € | 29 € | 99 €/tenant |
| Infraestructura | ~0 € | ~0 € | ~0 € (stack propio del tenant) |
| Coste LLM **con BYOK** | **0 €** (claves del usuario) | **0 €** | **0 €** (o claves del tenant) |
| Coste LLM sin BYOK (plataforma) | <1 € | 1-3 € | 3-10 € |
| **Margen bruto** | negativo leve | **~85-100 %** | **~85-100 %** |

**BYOK cambia el signo del coste LLM**: es el único coste variable real y
pasa a correr a cargo del usuario. La plataforma queda con coste marginal
≈ 0 €.

**Apalancamiento del híbrido:**

- **Nuestra infra**: margen alto, cero trabajo para el usuario, upsell natural.
- **Self-hosted**: margen 0 € en licencia, pero convierte a un escéptico en
  usuario y abre la vía de *soporte/instalación asistida* (única parte del
  negocio con trabajo humano facturable).

**Riesgos de coste, en orden de probabilidad:**

1. **Rate-limits del free tier.** El cuarto pilar de `docs/POLITICA-GRATIS.md:12`
   ("Gemini API: 1500 req/día") es una fuente de 429 documentada en
   `docs/GOOGLE-FREE-TIER-EXPANDIDO.md`. Si el modelo default para usuarios
   Free es el free tier de Google, el usuario Free ve errores 429 en hora punta.
   *Mitigación:* BYOK obligatorio en Free con claves propias, o cola + degradación.
2. **Llamadas del visor.** El visor cuesta 0 € porque usa Esri/OSM sin clave;
   el día que alguien quiera Google 3D, el margen se va.
3. **Soporte con un solo desarrollador.** Igual que
   `docs/MODELO-NEGOCIO-AIGESTION.md:208-210`: vender SLA antes de tener
   guardia es una promesa difícil. Enterprise 99,9 % debería exigir self-managed.

---

## 5. Ventajas defendibles

1. **Visor 3D del negocio** — ninguna competencia española pone tu empresa en
   un globo orbital con nodos de estado. Coste 0 € por diseño (capas sin clave).
2. **Control de acceso implementado y probado** — `core/access.py:37-221`,
   con sujeto, roles, filtrado de clientes y respuestas de denegación. Es
   infraestructura de seguridad real, no un plan.
3. **Runtime en el propio móvil** — `docs/ADR-022-CANAL-CODIGO-TELEFONOS.md`:
   el teléfono ejecuta, no solo consume. La app Android
   (`daniela-os/android-app/`, paquete `com.aigestion.mobile`) y el árbol
   cliente (`frontend/apps/android-app/mobile-app/`) ya despliegan código.
   Ningún competidor español tiene esto.
4. **Memoria de 12.480 nodos y empatía 96 %** (Daniela) — el "contexto
   persistente" que n8n y ChatGPT no tienen.
5. **Bundle híbrido ADR-022** — un mismo artefacto para nube y self-hosted; la
   vía C no necesita producto separado.
6. **Cero dependencia de pago para arrancar** — `docs/POLITICA-GRATIS.md`
   completa el círculo: el coste de entrada para el usuario es 0 €.

---

## 6. Agujeros verificados (con `file:line`)

Todo lo anterior asume cosas que **hoy no existen**. Cada agujero lleva su
evidencia, para que el roadmap de §7 no se apoye en suposiciones.

| # | Agujero | Evidencia | Bloquea |
|---|---|---|---|
| 1 | **Sin login Google de usuario final** — 0 rutas `route("/login\|/signup\|/register")` en la app (los únicos `/login` del repo son paths de test/WAF en `secops/`); el OAuth existente es del operador | `rg 'route\("/(login\|signup\|register)"' → 0 hits`; `scripts/daniela/daniela_os.py:574` (`/auth/google`), `:601` (`/auth/google/callback`) | Vías A y B |
| 2 | **BYOK no está por usuario** — las claves salen del shell, no de la UI | `docs/WHITE-LABEL.md:32`; `core/connections_manager.py:402-415` (store único) | Vía A, §1.3 |
| 3 | **Cobro real no completado** — webhook implementado con firma obligatoria, pero `STRIPE_WEBHOOK_SECRET` está vacío/insuficiente en runtime | `daniela-os/billing.py:126-161`, `:139` ("no se procesa nada sin firma"); `scripts/core/billing_system.py:27`; `.env:149` = `sk_test…` (**modo test**) | Monetización |
| 4 | **Sin checkout** — no hay `checkout.session` en el código de la app | `rg "checkout.session" → 0 hits en *.py` | Monetización |
| 5 | **Landing no servida ni con CTAs reales** — `static/landing.html` existe (656 líneas) pero los 3 botones de precio apuntan a `/` | `static/landing.html:256,269,281` → `href="/"` | Conversión |
| 6 | **~CERRADO 2026-10-04 (P6, commit e6e2da6a)~** Marca unificada en `aigestion.net` (76 ficheros, 147 sustituciones) | era: 63 ficheros con `aig.net` vs 27 con `aigestion.net` | Confianza, SEO, cookies OAuth |
| 7 | **Roadmap maestro stale** — 50 ideas en `⏳`, dominio histórico `aig.net` en título | `docs/ROADMAP_MASTER.md:1,10,19-60` | Alineamiento |
| 8 | **Phase tracker stale** — 11 fases todas DONE sobre `universo-v1` | `docs/PHASES.md:3` | Alineamiento |
| 9 | **Onboarding por CLI** — alta de tenant y de cliente solo por terminal | `scripts/deploy/tenant_bootstrap.py:13-14`; `docs/MODELO-NEGOCIO-AIGESTION.md:194` | Vías A, B |
| 10 | **Precios no públicos** — tabla en doc interno, no en web | `docs/MODELO-NEGOCIO-AIGESTION.md:85-99`, `:196` ("pendiente") | Conversión |

**Ninguno de los 10 agujeros es un problema de arquitectura.** Todos son de
superficie: UI, cobro, dominio y documentación. La plataforma (acceso, globo,
multi-tenant, memoria, runtime móvil) ya está construida.

---

## 7. Roadmap por fases (con criterios medibles)

Ordenado por lo que desbloquea, no por lo que es fácil. Cada fase tiene un
**gate objetivo**: se termina cuando la condición se cumple, no cuando "está
hecho".

### F0 — Marca unificada *(~1 semana, bloquea todo lo demás)* — ~CERRADO 2026-10-04 (P6, commit e6e2da6a)~
- Unificar `aig.net` → `aigestion.net`: hecho en 76 ficheros (147 sustituciones).
- Actualizar `docs/ROADMAP_MASTER.md`, `docs/PHASES.md` y
  `docs/MODELO-NEGOCIO-AIGESTION.md` con punteros a este documento.
- **Gate:** `rg -n "aig\.net" -g '!.venv' --no-ignore` → solo hits en runtime/archivos
  ignorados (0 en código trackeado); `rg "STALE" docs/ROADMAP_MASTER.md docs/PHASES.md` → ambos marcados.

### F1 — Puerta de entrada: login con Google *(~2 semanas)*
- OAuth de usuario final (reutilizar el flujo ya existente del operador).
- Cada usuario = una cuenta con sus propias conexiones.
- **Gate:** un usuario nuevo entra con su Gmail **sin tocar una terminal**,
  y su sesión sobrevive a un reinicio del contenedor.

### F2 — BYOK en la UI *(~2 semanas)*
- Wizard de conexiones sobre `core/connections_manager.py` (rutas ya existen).
- Aislamiento de claves por usuario (hoy es un store único
  `core/connections_manager.py:402-415`).
- **Gate:** 0 claves de API en el servidor para usuarios BYOK; 1 usuario real
  con Gemini + OpenRouter propios respondiendo; test nuevo en `tests/`.

### F3 — Cobro real *(~2 semanas)*
- `STRIPE_WEBHOOK_SECRET` en vivo, checkout de suscripción, página de precios
  pública con los CTAs bien enlazados (`static/landing.html:256,269,281`).
- **Gate:** **1 pago real completado** con firma de webhook verificada en el
  entorno de producción; el evento de `invoice.paid` se refleja en el tier del
  usuario. (Falso positivo = gate roto.)

### F4 — Onboarding en 5 minutos *(~2 semanas)*
- Alta de cliente/usuario desde el visor, no desde la CLI.
- **Gate:** un usuario sin ayuda consigue su **primer nodo en el globo en
  < 5 minutos**, cronometrado, con una cuenta nueva.

### F5 — Reposicionamiento público *(~1 semana, puede ir en paralelo con F1)*
- Reescribir `docs/MODELO-NEGOCIO-AIGESTION.md` (tesis de §1 de este doc),
  landing con las 4 vías (§2.3) y README con `aigestion.net`.
- **Gate:** ningún documento activo apunta al modelo B2B2B como *único* modelo
  sin marcador; `docs/INDEX.md` enlaza este documento entre los que importan.

### F6 — Vía C: self-hosted instalable *(~3 semanas, después de F2)*
- Empaquetar el bundle de ADR-022 como instalador de una sola orden
  (equivalente al `install` de OpenClaw, §3.3).
- **Gate:** instalación limpia en una máquina nueva con un único comando;
  el sistema queda sano (`uv run python scripts/check_gate.py`).

### F7 — Canal D (white-label) *(continuo, ya disponible)*
- `scripts/deploy/tenant_bootstrap.py` ya aprovisiona en 2 minutos; es la vía con
  menos trabajo pendiente y la de ticket alto.
- **Gate:** 1 gestoría/asesoría real en marca blanca pagando Enterprise.

**Los 10 agujeros de §6 caen así:** F0 → #6, #7, #8 · F1 → #1 · F2 → #2 ·
F3 → #3, #4, #10 · F4 → #9 · F5 → #5 y el reposicionamiento.

---

## 8. Riesgos (sin adornos)

1. **Un solo desarrollador.** Todo el plan asume capacidad de una persona; el
   orden de §7 está pensado para eso (primero lo que desbloquea, no lo que
   cuesta menos).
2. **El free tier de Google no es un derecho.** §4.1 — si el 429 se vuelve
   habitual, la experiencia Free se degrada y eso mata la conversión a Pro.
3. **El módulo de gestión no es nuestro foso.** Competimos contra gestorías
   afinadas; nuestro foso es el universo completo (§5), no la facturación.
4. **Línea ética del visor.** Como indica `docs/MODELO-NEGOCIO-AIGESTION.md:213-215`,
   el proyecto del que deriva (God's Eye View) prohíbe búsqueda de personas y
   reconocimiento facial. **Mantener esa línea** — también es protección legal.
5. **Cifras de mercado de casas comerciales.** §2.1 y §2.2 son estimaciones
   de consultoras que venden informes; sirven para dimensionar, no para
   prometer. Las cifras de INE/Eurostat/Cámara de Comercio (§2.2) tienen
   evidencia alta; las de MarketsandMarkets/Grand View, evidencia media.

---

## 9. Fuentes

**Mercado (consultado 2026-10-04):**
- MarketsandMarkets — *AI Agents Market 2025-2030* (ago 2026) y ficha de España (ago 2026)
- Grand View Research — *AI Agents Market 2026-2033* (jun 2026)
- Insight Partners — *AI Companion Market 2025-2034*
- Microsoft AI Economy Institute — *Global AI Diffusion Report* (sep 2026), vía La Ecuación Digital
- INE — *Encuesta de uso de TIC y comercio electrónico en las empresas* (1T 2025)
- CaixaBank Research — *Adopción de IA en la empresa española* (may 2026)
- YouGov para IONOS — *Pymes e IA 2026* (jun 2026), vía MuyCanal
- Cámara de Comercio de España — *Radiografía de adopción de IA*
- Banco de España (EBAE) — obstáculos a la adopción de IA
- Google / Implement Consulting — impacto en PIB español (2025)
- Future Ready Accountant 2025 — asesorías españolas y IA

**Competencia (consultado 2026-10-04):** losagents.ai, Hi-Ai, Automatiza
PyMES, IA FOR PYMES (fichas Tracxn); OpenClaw y plantillas n8n-claw;
byok.tech; agentkey.dev.

**Código:** toda cita `file:line` de §1, §4, §6 fue verificada contra el árbol
el 2026-10-04 (tras marcar como STALE `ROADMAP_MASTER`, `PHASES` y §5 de
`MODELO-NEGOCIO-AIGESTION`; esas ediciones desplazaron sus números de línea).
Las afirmaciones de "0 hits" se reproducen sin exclusiones de directorio:
`route\("/(login|signup|register)"` → 0 rutas de app; `checkout.session` → 0
hits en `*.py`. `"/login"` solo aparece en `secops/` (paths de test y WAF).
