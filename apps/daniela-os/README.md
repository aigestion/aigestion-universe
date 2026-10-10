# AIGestion

Plataforma de IA para gestorias fiscales, contables y PYMEs.

## Descripcion

AIGestion es una plataforma modular de inteligencia artificial que automatiza tareas repetitivas de gestoria: clasificacion de emails, auditoria de facturas, generacion de contenido, analisis de reuniones y mucho mas.

## Arquitectura

```
Daniela OS (Flask) → AIGestion Core → 10 Modulos Quick Win
                            ↓
                    Auth + Billing + Analytics
                            ↓
                    API Gateway + Docker + Nginx
```

## Modulos

| Modulo | Descripcion | Estado |
|--------|-------------|--------|
| Daniela Proactive Engine | Motor proactivo con analisis de calendario | ✅ |
| Email Zero Inbox | Clasificacion inteligente de emails | ✅ |
| Smart Invoice Auditor | OCR, duplicados, fraude | ✅ |
| Meeting Intelligence | Transcripcion y action items | ✅ |
| Sentiment Dashboard | Analisis de sentimiento en espanol | ✅ |
| Social Media Command Center | Centro de comando para redes | ✅ |
| Customer Support Automation | FAQ matching, tickets, escalamiento | ✅ |
| Code Generation Agent | NL → Codigo con tests | ✅ |
| Content Factory AI | Fabrica de contenido multi-plataforma | ✅ |
| Swarm Intelligence | Coordinador multi-agente | ✅ |

## Quick Start

### Requisitos

- Python 3.11+ (el pyproject raiz exige >=3.11)
- Docker y Docker Compose (opcional)

### Instalacion local

```bash
# Clonar repo
git clone https://github.com/aigestion/AIG.git
cd AIG

# Crear venv
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
.venv\Scripts\activate      # Windows

# Instalar dependencias
pip install -r requirements.txt

# Iniciar Daniela OS
python daniela_os.py

# En otra terminal: API Gateway
python api_gateway.py --port 8080
```

### Docker

```bash
docker-compose up -d
```

Servicios disponibles:
- Daniela OS: http://localhost:5000
- API Gateway: http://localhost:8080
- Admin Panel: http://localhost:5001/admin
- Nginx: http://localhost

## Uso

### Chat con Daniela

```bash
curl -X POST http://localhost:5000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "genera contenido para blog sobre IA"}'
```

### API Gateway

```bash
# Obtener token
curl -X POST http://localhost:8080/v1/admin/token \
  -d '{"api_key": "tu-api-key"}'

# Consultar
 curl -X POST http://localhost:8080/v1/ask \
  -H "Authorization: Bearer <token>" \
  -d '{"query": "analiza sentimiento: estoy muy feliz"}'
```

### Pipeline

```bash
curl -X POST http://localhost:8080/v1/pipeline \
  -H "Authorization: Bearer <token>" \
  -d '{"steps": [
    {"module": "content_factory", "action": "generate", "params": {"topic": "IA", "platform": "twitter"}},
    {"module": "social_media", "action": "generate_post", "params": {"topic": "IA"}}
  ]}'
```

## Tiers

| Tier | Precio | Requests/dia | Modulos | API |
|------|--------|-------------|---------|-----|
| Free | €0 | 100 | 3 basicos | No |
| Pro | €29/mes | 1,000 | Todos | Si |
| Enterprise | €99/mes | Ilimitado | Todos + White-label | Si |

## Comandos Slash (Daniela OS)

| Comando | Descripcion |
|---------|-------------|
| `/core <query>` | Consulta directa al core |
| `/content <tema>` | Generar contenido |
| `/swarm <objetivo>` | Coordinar swarm |
| `/code <desc>` | Generar codigo |
| `/email <texto>` | Clasificar email |
| `/invoice <datos>` | Auditar factura |
| `/sentiment <texto>` | Analizar sentimiento |
| `/social <tema>` | Generar post social |
| `/support <query>` | Soporte automatico |
| `/meeting <transcripcion>` | Analizar reunion |
| `/proactive` | Ver alertas del calendario |
| `/help` | Mostrar ayuda |

## Estructura del proyecto

```
.
├── adapters.py       # Adapters del ecosistema
├── adapters.py       # Adaptadores de modulos
├── daniela_os.py               # Dashboard web + chat
├── api_gateway.py              # API publica (JWT + rate limit)
├── auth_system.py              # OAuth2 + JWT + roles
├── billing_system.py           # Suscripciones + Stripe
├── admin_panel.py              # Panel de administracion
├── analytics.py                # Metricas y reportes
├── plugin_system.py            # Sistema de plugins
├── white_label.py              # White-label Enterprise
├── enterprise_onboarding.py    # Onboarding Enterprise
├── connectors/                 # Conectores externos
│   └── google_workspace.py
├── static/                     # Landing page
│   └── landing.html
├── Dockerfile                  # Container
├── docker-compose.yml          # Stack Docker
├── nginx.conf                  # Reverse proxy
└── docs/                       # Documentacion
```

## Variables de entorno

| Variable | Descripcion | Default |
|----------|-------------|---------|
| `GEMINI_API_KEY` | API key de Google Gemini | - |
| `GOOGLE_API_KEY` | API key de Google | - |
| `AIGESTION_JWT_SECRET` | Secret para JWT | change-me |
| `DANIELA_PIN` | PIN de acceso | **(configúralo tú en `.env`)** |
| `STRIPE_WEBHOOK_SECRET` | Secret de Stripe | - |

## Testing

```bash
# Test core
python adapters.py status

# Test Daniela OS
python daniela_os.py --test-core

# Test analytics (canónico tras la ola de dedup)
python ../scripts/core/analytics.py --dashboard
```

## Contribuir

1. Fork el repositorio
2. Crea una rama (`git checkout -b feature/nueva-feature`)
3. Commit (`git commit -m 'feat: nueva feature'`)
4. Push (`git push origin feature/nueva-feature`)
5. Abre un Pull Request

## Licencia

MIT License - AIGestion Team 2026
