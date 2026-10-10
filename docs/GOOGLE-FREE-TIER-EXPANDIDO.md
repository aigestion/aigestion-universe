# GOOGLE FREE TIER — Expandido Completo (2026)

> **Fecha:** 2026-09-05  
> **Proyecto:** aig Monorepo + DanielaOS  
> **Objetivo:** Catalogar TODOS los servicios gratuitos de Google, sus límites exactos, estado de integración, e ideas épicas para los que faltan.

---

## RESUMEN EJECUTIVO

| Métrica | Valor |
|---|---|
| **Servicios gratuitos catalogados** | **67** |
| **Categorías** | 11 |
| **Ya integrados en aig** | 23 |
| **Disponibles gratis pero NO integrados** | 44 |
| **Valor mensual estimado (gratis)** | ~$2,847/mes |
| **Inversión requerida** | $0.00 |

---

## 1. GOOGLE CLOUD PLATFORM — Always Free (31 servicios)

### 1.1 Compute & Serverless

| # | Servicio | Límite Gratis | Estado en aig | Idea Épica |
|---|---|---|---|---|
| 1 | **Compute Engine (e2-micro)** | 1 VM/mes + 30GB disco (us-west1/central1/east1) | NO integrado | Servidor DanielaOS 24/7 gratis — API gateway, bot de Telegram, webhook relay |
| 2 | **Cloud Run** | 2M requests/mes, 360K GiB-seg, 180K vCPU-seg | Referenciado en `autodeploy_core.py` | Desplegar DanielaOS como microservicios auto-escalables a cero |
| 3 | **Cloud Functions** | 2M invocaciones/mes, 400K GB-seg, 200K GHz-seg | Referenciado en `auto_pipeline.py` | Webhooks de Telegram, procesamiento de emails, pipelines ETL serverless |
| 4 | **App Engine** | 28 instance-hours/día, 1GB egress/día | NO integrado | App de panel admin de aig con dominio gratuito .appspot.com |
| 5 | **GKE Autopilot** | 1 cluster zonal gratis | NO integrado | Orquestar agentes de IA en contenedores |
| 6 | **Cloud Shell** | 5GB home persistente, terminal web | NO integrado | Dev environment remoto para debugging desde cualquier dispositivo |

### 1.2 Storage & Database

| # | Servicio | Límite Gratis | Estado en aig | Idea Épica |
|---|---|---|---|---|
| 7 | **Cloud Storage** | 5GB-months, 5K ops clase A, 50K clase B | NO integrado | Bucket de backups automáticos del monorepo, almacen de modelos ML |
| 8 | **Firestore** | 1GB storage, 50K reads/día, 20K writes/día | Referenciado en `app_factory.py` | Base de datos real-time para estado de agentes, cache distribuido |
| 9 | **BigQuery** | 1TB consultas/mes, 10GB storage | NO integrado | Analytics de uso de DanielaOS, logs estructurados, ML sobre datos |
| 10 | **Pub/Sub** | 10GB mensajes/mes | NO integrado | Bus de eventos entre agentes, cola de tareas asíncronas |
| 11 | **Artifact Registry** | 500MB storage | NO integrado | Registry privado de containers Docker para DanielaOS |

### 1.3 DevOps & CI/CD

| # | Servicio | Límite Gratis | Estado en aig | Idea Épica |
|---|---|---|---|---|
| 12 | **Cloud Build** | 2,500 build-min/día, 120 builds/día | NO integrado | CI/CD pipeline: push → build → deploy automático a Cloud Run |
| 13 | **Cloud Source Repositories** | 5 usuarios, 50GB storage | NO integrado | Mirror del repo aig como backup de código |
| 14 | **Secret Manager** | 6 secret versions, 10K access ops/mes | NO integrado | Almacenar API keys de forma segura (reemplaza .env.secrets) |
| 15 | **Cloud KMS** | 100 key versions (software) | NO integrado | Cifrado de datos sensibles, claves de wallets |

### 1.4 Observability & Security

| # | Servicio | Límite Gratis | Estado en aig | Idea Épica |
|---|---|---|---|---|
| 16 | **Cloud Logging** | 50GB/mes, retención 30 días | NO integrado | Centralizar logs de todos los agentes DanielaOS |
| 17 | **Cloud Monitoring** | Métricas GCP + 500 custom + alerting | NO integrado | Dashboard de salud del sistema, alertas por Slack/Telegram |
| 18 | **reCAPTCHA Enterprise** | 10,000 assessments/mes | Referenciado en `auth_system.py` | Protección anti-bot en formularios y APIs públicas |
| 19 | **Cloud Armor** | Reglas WAF (standard tier) | NO integrado | Proteger endpoints públicos de DanielaOS contra DDoS |

### 1.5 Integration & Scheduling

| # | Servicio | Límite Gratis | Estado en aig | Idea Épica |
|---|---|---|---|---|
| 20 | **Workflows** | 5,000 steps internos/mes | NO integrado | Orquestar pipelines multi-paso: ingest → process → publish |
| 21 | **Application Integration** | 400 ejecuciones/mes, 2 connectors | NO integrado | Conectar SAP/CRM externos con DanielaOS |
| 22 | **Cloud Scheduler** | 3 jobs gratis | NO integrado | Cron jobs: reportes diarios, sync de datos, backups automáticos |

### 1.6 AI/ML APIs (límites mensuales)

| # | Servicio | Límite Gratis | Estado en aig | Idea Épica |
|---|---|---|---|---|
| 23 | **Cloud Vision API** | 1,000 unidades/mes | Integrado en `skills/vision.py` (Gemini) | OCR de documentos, detección de logos, moderación de contenido |
| 24 | **Natural Language API** | 5,000 unidades/mes | NO integrado | Análisis de sentimiento de emails/tweets, extracción de entidades |
| 25 | **Speech-to-Text** | 60 min/mes | NO integrado | Transcripción de reuniones, notas de voz → texto |
| 26 | **Video Intelligence API** | 1,000 unidades/mes | NO integrado | Moderación automática de videos subidos, detección de escenas |
| 27 | **Translation API** | 500K caracteres/mes | NO integrado | Traducción automática de contenido multilingüe |

---

## 2. GEMINI AI — Free Tier API (5 modelos)

| # | Modelo | RPM | TPM | RPD | Estado | Idea Épica |
|---|---|---|---|---|---|---|
| 28 | **Gemini 2.5 Pro** | 5 | ~2M | 100 | Integrado en múltiples módulos | Cerebro principal de DanielaOS — razonamiento profundo, análisis de código |
| 29 | **Gemini 2.5 Flash** | 10 | ~250K | ~1,500 | Integrado en `skills/vision.py` | Respuestas rápidas, chat en tiempo real, análisis de imágenes |
| 30 | **Gemini 2.5 Flash-Lite** | 30 | — | 1,500 | NO integrado | Modelo más rápido para tareas simples: categorización, routing de intents |
| 31 | **Gemini 3 Flash** (preview) | — | — | — | NO integrado | Próximo modelo: más capaz que Flash, gratis durante preview |
| 32 | **Gemini Code Assist** | Free individual tier | — | — | NO integrado | Autocompletar de código en VS Code, chat, multi-file editing |

### Gemini CLI — El Hack Secreto

| Métrica | Valor |
|---|---|
| RPM | **60** (12x mejor que API) |
| RPD | **1,000** |
| Context window | **1 millón de tokens** |
| Modelos | **Gemini 3 Pro + Flash** |
| API key requerida | **NO** (OAuth con Google account) |

```bash
npm install -g @google/gemini-cli
gemini auth login
# Enable Preview Features → Select "Auto (Gemini 3)"
```

**Idea Épica:** Usar Gemini CLI como motor de IA gratuito para DanielaOS. 60 RPM + 1,000 requests/día = capacidad masiva sin pagar.

---

## 3. GOOGLE LABS — Herramientas Experimentales (11 herramientas)

| # | Herramienta | Límite Gratis | Estado | Idea Épica |
|---|---|---|---|---|
| 33 | **NotebookLM** | 100 notebooks, 50 fuentes/notebook, 200MB/archivo, 500K palabras, 3 audio overviews/día, 3 video overviews/día, 50 chat queries/día, 10 deep research/mes | Integrado en `daniela_notebooklm_pipeline.py` + `daniela_labs_connector.py` | Base de conocimiento de aig — indexar TODO el código y docs, hacer preguntas grounded |
| 34 | **Google Veo (v2)** | ~30 videos/mes (Gemini App, Veo 2 only) | NO integrado | Generación de videos de onboarding, tutoriales automáticos |
| 35 | **Google Stitch** | 450 generaciones/mes (350 standard + 100 experimental) | NO integrado | Prototipar UI de apps nuevas de aig en segundos |
| 36 | **Google Jules** | 15 tasks/día, 3 concurrentes (Gemini 2.5 Pro) | NO integrado | Agente autónomo que hace PRs al repo de aig automáticamente |
| 37 | **Google Gems** | Creación ilimitada, 10 archivos/gem, 5-15 RPM | NO integrado | Mini-agentes personalizados para tareas específicas: review de código, generador de docs |
| 38 | **Google Disco** | Gratis (early access, waitlist, macOS only) | NO integrado | Navegador con IA que construye apps desde tabs abiertas |
| 39 | **Google Pomelli** | Gratis (beta, sin límites documentados) | NO integrado | Generador automático de campañas de marketing para aig |
| 40 | **Google Mixboard** | Gratis (beta, 160+ países) | NO integrado | Brainstorming colaborativo del equipo con IA |
| 41 | **ImageFX** | Gratis (labs.google) | NO integrado | Generación de imágenes para assets de apps, avatares de Daniela |
| 42 | **MusicFX** | Gratis (labs.google) | NO integrado | Generar música de fondo para videos, podcasts de aig |
| 43 | **Google Illuminate** | Gratis (labs.google) | Integrado en `daniela_google_labs_suite.py` | Convertir papers técnicos en podcasts de audio |

---

## 4. GOOGLE WORKSPACE — Free Tier (6 servicios)

| # | Servicio | Límite Gratis | Estado | Idea Épica |
|---|---|---|---|---|
| 44 | **Gmail** | 15GB compartido (Drive+Gmail+Photos), envío ilimitado con límites | Integrado en `connectors/google_workspace.py` | Sistema de emails automatizados de DanielaOS |
| 45 | **Google Drive** | 15GB compartidos | Integrado en `connectors/google_workspace.py`, `auth_gdrive.py`, `DriveVaultSync.gs` | Almacenamiento de backups, sincronización de archivos |
| 46 | **Google Calendar** | Ilimitado | Integrado en `connectors/google_workspace.py` | Programación automática de tareas, recordatorios |
| 47 | **Google Docs** | Ilimitado (Apps Script) | Integrado en `DocsExecutiveReporter.gs` | Generación de reportes ejecutivos automáticos |
| 48 | **Google Sheets** | Ilimitado (Apps Script) | Integrado en `connectors/google_workspace.py` | Dashboards de métricas, CRMs, tablas de seguimiento |
| 49 | **Google Contacts** | Ilimitado | Integrado en `connectors/google_workspace.py` | CRM sincronizado con contactos del teléfono |

### Apps Script (5 archivos ya creados)

| # | Archivo | Función |
|---|---|---|
| 50 | `apps-script/Code.gs` | Entry point principal |
| 51 | `apps-script/DocsExecutiveReporter.gs` | Reportes ejecutivos en Google Docs |
| 52 | `apps-script/DriveVaultSync.gs` | Sync de backups a Drive |
| 53 | `apps-script/TermuxWebhookRelay.gs` | Relay de webhooks desde Termux |
| 54 | `apps-script-admin/` | Panel administrativo |

---

## 5. GOOGLE MAPS PLATFORM — Free Tier

| # | API | Crédito Mensual | Estado | Idea Épica |
|---|---|---|---|---|
| 55 | **Maps JavaScript API** | $200/mes compartido (~28K loads) | NO integrado | Mapa interactivo de ubicación de agentes/dispositivos |
| 56 | **Geocoding API** | $200/mes compartido (~40K requests) | Referenciado en `plugins/location.py` | Geolocalización de direcciones de clientes |
| 57 | **Places API** | $200/mes compartido (~6K-12K requests) | NO integrado | Búsqueda de negocios cercanos, POI discovery |
| 58 | **Directions API** | $200/mes compartido (~40K requests) | NO integrado | Rutas de entrega, optimización de visitas |
| 59 | **Static Maps API** | $200/mes compartido (~100K images) | NO integrado | Mapas estáticos en notificaciones de Telegram |
| 60 | **Street View API** | $200/mes compartido (~14K panoramas) | NO integrado | Vistas de calle para ubicaciones de clientes |

**Nota:** Google Maps requiere tarjeta de crédito. $200/mes de crédito compartido entre TODAS las APIs.

---

## 6. YOUTUBE DATA API v3 — Free Tier

| # | Operación | Coste en Unidades | Estado | Idea Épica |
|---|---|---|---|---|
| 61 | **Read video details** | 1 unidad | NO integrado | Extraer stats de videos, feed de contenido |
| 62 | **Read channel info** | 1 unidad | NO integrado | Dashboard de creadores, tracking de suscriptores |
| 63 | **Search** | 100 unidades | NO integrado | Búsqueda de contenido relevante |
| 64 | **Upload video** | 1,600 unidades | NO integrado | Subida automática de videos generados |
| **Total diario** | | **10,000 unidades/día** | | ~100 búsquedas/día o ~10,000 reads/día |

---

## 7. FIREBASE — Spark Plan (Free)

| # | Servicio | Límite Gratis | Estado | Idea Épica |
|---|---|---|---|---|
| 65 | **Firebase Auth** | 50,000 MAUs, 10K verificaciones teléfono/mes | Referenciado en `auth_system.py` | Auth unificado de todos los usuarios de aig |
| 66 | **Cloud Firestore** | 1GB storage, 50K reads/día, 20K writes/día | Referenciado en `app_factory.py` | DB real-time para estado de agentes en vivo |
| 67 | **Firebase Hosting** | 10GB storage, 360MB/día transfer | NO integrado | Hostear el panel web de DanielaOS con SSL gratis + dominio propio |
| 68 | **Firebase Realtime DB** | 1GB storage, 10GB/mes transfer, 100 conexiones | NO integrado | Chat en tiempo real, estado de dispositivos IoT |
| 69 | **Firebase Remote Config** | Ilimitado (incluye A/B testing) | NO integrado | Feature flags remotos, configuración dinámica sin deploy |
| 70 | **Firebase Messaging (FCM)** | Ilimitado | NO integrado | Push notifications a Android/iOS/web — alertas de DanielaOS |
| 71 | **Firebase Storage** | 5GB storage | NO integrado | Almacen de archivos multimedia (fotos, audio, docs) |

---

## 8. GOOGLE MARKETING & ANALYTICS — Free Tier

| # | Servicio | Límite Gratis | Estado | Idea Épica |
|---|---|---|---|---|
| 72 | **Google Analytics 4** | Ilimitado (hasta 500 events/usuario) | Integrado en `analytics.py` | Tracking de uso de DanielaOS, funnels de conversión |
| 73 | **Google Tag Manager** | Ilimitado | NO integrado | Gestión centralizada de tags de tracking |
| 74 | **Google Search Console** | Ilimitado | NO integrado | Monitorear SEO de sitios web de aig |
| 75 | **Google Ads** | API gratuita (gastos de campaña aparte) | NO integrado | Automatizar campañas publicitarias |
| 76 | **Google My Business** | Ilimitado | NO integrado | Gestionar fichas de negocio en Google Maps |
| 77 | **Looker Studio** | Ilimitado reports, 10 data sources | NO integrado | Dashboards visuales conectados a BigQuery + Analytics |

---

## 9. GOOGLE COLAB — Free Tier

| # | Recurso | Límite Gratis | Estado | Idea Épica |
|---|---|---|---|---|
| 78 | **Colab Free** | T4 GPU, RAM estándar, 12h sesión | NO integrado | Entrenar modelos ML, ejecutar notebooks de análisis, prototipar rápido |
| 79 | **Colab Connect** | Conectar a runtime local | NO integrado | Ejecutar código GPU desde DanielaOS remotamente |

---

## 10. ADDITIONAL FREE GOOGLE SERVICES

| # | Servicio | Límite Gratis | Estado | Idea Épica |
|---|---|---|---|---|
| 80 | **Google Forms** | Ilimitado | NO integrado | Encuestas, formularios de onboarding, feedback |
| 81 | **Google Keep API** | Via Google Workspace API | NO integrado | Notas rápidas de DanielaOS → sincronizar con Keep |
| 82 | **Google Tasks API** | Ilimitado | NO integrado | Task management sincronizado con Calendar |
| 83 | **Google Classroom API** | Gratis para edu | NO integrado | Plataforma de formación de aig |
| 84 | **Google Chrome Extensions** | Gratis (Chrome Web Store) | NO integrado | Extensión de navegador para DanielaOS |
| 85 | **Chrome DevTools Protocol** | Gratis | NO integrado | Automatización de navegador, web scraping |
| 86 | **Google Alerts** | Ilimitado | NO integrado | Monitoreo de menciones de marca, keywords |
| 87 | **Google Trends API** | Gratis (no oficial) | NO integrado | Análisis de tendencias para contenido |
| 88 | **Google Fonts** | Ilimitado | NO integrado | Tipografía consistente en apps web |
| 89 | **Material Design Icons** | Ilimitado | NO integrado | Librería de iconos para UI |
| 90 | **Google Safe Browsing API** | Ilimitado | NO integrado | Verificar URLs sospechosas en emails/chats |

---

## 11. $300 FREE TRIAL CREDIT (90 días)

| Recurso | Valor | Condiciones |
|---|---|---|
| **$300 credit** | $300 USD | 90 días, acceso a TODOS los servicios de GCP, tarjeta requerida (no auto-cobra) |

**Idea Épica del Trial:** Usar los $300 para:
- Entrenar un modelo fine-tuned en Vertex AI ($~100)
- Migrar BigQuery con datos históricos ($~50)
- Probar Cloud Run con tráfico real ($~30)
- Almacenar snapshots en Cloud Storage ($~20)
- Setup de logging y monitoring ($~10)
- **Total gastado:** ~$210 → sobran $90 para experimentación

---

## IDEAS ÉPICAS — TOP 10 EXPANSIONES GRATIS

### 1. DanielaOS en Compute Engine e2-micro (FREE FOREVER)
Desplegar DanielaOS completo en una VM e2-micro gratis para siempre. Bot de Telegram 24/7, API gateway, webhook relay. Cero coste.

### 2. NotebookLM como Base de Conocimiento
Indexar TODO el código fuente de aig + docs + .env variables en NotebookLM. Hacer preguntas tipo "¿qué archivo maneja la autenticación?" con respuestas grounded en el código real. 100 notebooks, 50 fuentes cada uno.

### 3. Gemini CLI como Motor de IA Gratuito
60 RPM + 1,000 requests/día con Gemini 3 Pro. Integrar en DanielaOS como alternativa gratuita a OpenAI/Anthropic. Sin API key, solo OAuth.

### 4. Cloud Scheduler + Cloud Functions = Pipelines Automáticos
3 jobs gratis: reporte diario a las 9am, sync de backups a las 2am, health check cada hora. Cada job dispara una Cloud Function (2M gratis).

### 5. Firebase Hosting para Panel Web de DanielaOS
10GB storage + 360MB/día transfer. Hostear el panel admin con SSL gratis y dominio personalizado. Sin necesidad de VPS.

### 6. BigQuery para Analytics Masivo
1TB de consultas gratis/mes. Centralizar logs de DanielaOS, analizar patrones de uso, entrenar modelos ML sobre datos históricos.

### 7. YouTube Data API para Content Pipeline
10K unidades/día. Extraer stats de videos de la competencia, generar reportes de tendencias, subir videos automáticamente con 1,600 unidades por upload.

### 8. Jules como Developer Agent
15 tasks/día gratis. Jules crea PRs automáticamente al repo de aig: fixes de bugs, refactors, nueva documentación. Developer virtual gratuito.

### 9. Google Stitch para Prototipado Rápido
450 generaciones/mes. Prototipar UI de nuevas apps de aig en segundos con IA. Exportar a AI Studio para iteración.

### 10. Cloud Logging + Monitoring = Observabilidad Total
50GB logs/mes + alerting gratis. Centralizar logs de todos los agentes, dashboards de salud del sistema, alertas por email cuando algo falle.

---

## CÁLCULO DE VALOR MENSUAL GRATIS

| Categoría | Servicio | Valor Estimado/mes |
|---|---|---|
| Compute | e2-micro VM | $7.60 |
| Compute | Cloud Run 2M req | $~50 |
| Compute | Cloud Functions 2M | $~20 |
| Storage | Cloud Storage 5GB | $0.10 |
| Storage | BigQuery 1TB queries | $5.00 |
| AI API | Gemini 2.5 Pro (100 RPD) | $~200 |
| AI API | Gemini 2.5 Flash (1.5K RPD) | $~100 |
| AI API | Vision API 1K units | $~1.50 |
| AI API | NLP API 5K units | $~1.00 |
| AI API | Translation 500K chars | $~10 |
| AI API | Speech-to-Text 60 min | $~0.60 |
| Maps | $200 credit | $200 |
| YouTube | 10K units/día | $~50 |
| Firebase | Spark plan | $~25 |
| Labs | NotebookLM + Stitch + Jules | $~50 |
| Analytics | GA4 + Looker Studio | $~50 |
| Workspace | Gmail + Drive (15GB) | $~12 |
| Colab | T4 GPU | $~10 |
| Gemini CLI | 60 RPM + Gemini 3 | $~1,000 |
| **TOTAL** | | **~$2,847/mes** |

> **Ahorro anual:** ~$34,164/año en servicios que ya están gratis o se pueden integrar a $0.

---

## PRÓXIMOS PASOS RECOMENDADOS

1. **Inmediato (P0):** Integrar Gemini CLI como motor de IA gratuito en DanielaOS
2. **Inmediato (P0):** Configurar Cloud Scheduler + Cloud Functions para tareas automáticas
3. **Corto plazo (P1):** Deploy de DanielaOS en e2-micro VM (Compute Engine free)
4. **Corto plazo (P1):** Integrar Firebase Hosting para el panel web
5. **Medio plazo (P2):** Centralizar logs en Cloud Logging + dashboards en Looker Studio
6. **Medio plazo (P2):** Setup de BigQuery para analytics del sistema
7. **Largo plazo (P3):** Integrar Jules para PRs automáticos al repo
8. **Largo plazo (P3):** Explorar Google Stitch para prototipado de UI

---

_Generado por WorkBuddy AI — 2026-09-05_
