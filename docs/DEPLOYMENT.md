# aig Deployment Guide — Universo v1

> Complete deployment instructions for all environments (21 services + gateway + orchestrator + monitoring).

## Prerequisites

| Requirement | Version | Purpose |
|-------------|---------|---------|
| Docker | 20.10+ | Container runtime |
| Docker Compose | 2.0+ | Multi-container orchestration |
| Python | 3.11+ | Service runtime |
| Redis | 7.0+ | Cache and message broker |
| Git | 2.30+ | Source control |

### Optional
- **NATS**: 2.x — For production event bus (falls back to in-memory)
- **Prometheus**: latest — Metrics collection
- **Grafana**: latest — Metrics visualization

## Quick Start — Universo v1

```bash
# Clone the repository (branch universo-v1)
git clone <repo-url> aig
cd aig
git checkout universo-v1

# Copy environment template
cp .env.master.example .env

# Option A: one-command deploy (recommended)
./deploy.sh
# Windows:
.\deploy.ps1

# Option B: Docker Compose directly
docker-compose up -d

# Option C: production stack
docker-compose -f docker-compose.prod.yml up -d

# Option D: production + monitoring (Prometheus :9090 + Grafana :3000)
docker-compose -f docker-compose.prod.yml -f docker-compose.monitoring.yml up -d

# Verify all 21 services + gateway + orchestrator
curl http://localhost:9997/api/services
curl http://localhost:8080/health
curl http://localhost:9900/api/cross/status
curl http://localhost:9910/api/chaos/status
curl http://localhost:9911/api/regions/status

# Run CI health gate (fails if any service offline)
python scripts/ci_health_gate.py --all --fail-on-offline
```

### Docker Compose Services

```bash
# Start core stack
docker-compose up -d

# Start production stack
docker-compose -f docker-compose.prod.yml up -d

# Start production + monitoring (Prometheus :9090 + Grafana :3000)
docker-compose -f docker-compose.prod.yml -f docker-compose.monitoring.yml up -d

# Legacy: monitoring profile on base compose
docker-compose --profile monitoring up -d

# View logs
docker-compose logs -f daniela-os

# Stop all
docker-compose down
```

### deploy.sh / deploy.ps1

One-command wrappers (build → up → health gate):

```bash
./deploy.sh            # Linux/Mac: core or prod + gate
.\deploy.ps1           # Windows equivalent
./deploy.sh --prod --monitoring   # prod + Prometheus/Grafana
```

Both scripts run `scripts/ci_health_gate.py` at the end and exit non-zero on failure.

### Health Gate Usage (CI/CD Total)

```bash
# Gate all 21 services + gateway + orchestrator
python scripts/ci_health_gate.py --all --fail-on-offline

# Gate specific engines
python scripts/ci_health_gate.py --engines daniela,hermes,chaos,regions --fail-on-offline

# In CI (GitHub Actions / ci_runner.py)
python ci_runner.py --gate
pytest tests/core/test_ci_health_gate_core.py tests/core/test_regions_active.py tests/performance/test_chaos.py -v
```

## Manual Setup

### 1. Install Dependencies

```bash
# Create virtual environment
python -m venv .venv
.venv\Scripts\activate  # Windows
# source .venv/bin/activate  # Linux/Mac

# Install shared library
pip install -e aig-shared/

# Install main requirements
pip install -r requirements.txt
```

### 2. Start Redis

```bash
# Docker
docker run -d --name aig-redis -p 6379:6379 redis:7-alpine

# Or local install
redis-server
```

### 3. Start Services

Each service runs independently on its assigned port:

```bash
# Terminal 1: Epic PC
cd epic-pc
python main.py  # Port 5020

# Terminal 2: Daniela Omnipresente
cd daniela-omnipresente
python server.py  # Port 9200

# Terminal 3: Hermes Epic
cd hermes-epic  # (if exists)
python server.py  # Port 9300

# Terminal 4: AIG Optimization
cd aig-optimization
python server.py  # Port 9400

# Terminal 5: Frontend V1
cd frontend-optimization
python server.py  # Port 9500

# Terminal 6: Frontend V2
cd frontend-opt2
python server.py  # Port 9600

# Terminal 7: Infra Optimization
cd infra-opt
python server.py  # Port 9700

# Terminal 8: Agent & Mobile
cd agent-opt
python server.py  # Port 9800

# Terminal 9: Security & Monitoring
cd sec-opt
python server.py  # Port 9999

# Terminal 10: Performance & Quality
cd perf-opt
python server.py  # Port 9998

# Terminal 11: Unified Dashboard
cd daniela-os/unified-dashboard
python server.py  # Port 9997
```

### 4. Start Health Check Monitor

```bash
python health_check.py
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `sqlite:///aig.db` | Primary database URL |
| `REDIS_URL` | `redis://localhost:6379/0` | Redis connection string |
| `NATS_URL` | `nats://localhost:4222` | NATS event bus URL |
| `JWT_SECRET` | `change-me-in-production` | JWT signing secret |
| `SERVICE_BASE_URL` | `http://localhost` | Base URL for inter-service calls |
| `GEMINI_API_KEY` | — | Gemini AI API key |
| `GOOGLE_API_KEY` | — | Google API key |
| `DANIELA_PIN` | — | Daniela access PIN |
| `FLASK_ENV` | `production` | Flask environment |
| `DEBUG` | `false` | Debug mode toggle |

### Service Port Configuration

Ports are defined in `aig-shared/aig_shared/config/__init__.py`:

```python
SERVICE_PORTS = {
    "epic_pc": 5020,
    "daniela_omnipresente": 9200,
    "hermes_epic": 9300,
    "aig_optimization": 9400,
    "frontend_v1": 9500,
    "frontend_v2": 9600,
    "infra_opt": 9700,
    "agent_mobile": 9800,
    "sec_monitoring": 9999,
    "perf_quality": 9998,
}
```

## Health Monitoring

### Automated Health Check

```bash
# Run continuous health check (30s interval)
python health_check.py
```

**Output:**
```
============================================================
aig Health Check - 14:32:15
============================================================
✅ Epic PC                       (5020): online
✅ Daniela Omnipresente          (9200): online
❌ Hermes Epic                   (9300): offline
✅ AIG Optimization              (9400): online
✅ Frontend V1                   (9500): online
...

------------------------------------------------------------
Summary:
  Online: 9/10
  Health Score: 90%
```

### Prometheus Integration

```bash
# Start with monitoring profile
docker-compose --profile monitoring up -d prometheus

# Access Prometheus UI
# http://localhost:9090
```

**Scrape targets** (configure in `prometheus.yml`):
- All services expose `/metrics` endpoint
- Dashboard aggregates metrics from all services

### Grafana Dashboards

```bash
# Access Grafana
# http://localhost:3000 (default credentials: admin/admin)
```

**Pre-configured dashboards:**
- Service health overview
- Request latency distribution
- Error rate trends
- Resource utilization

### Service Registry Health

The dashboard continuously monitors service health:

```python
# Health criteria:
# - TCP connection on service port
# - HTTP 200 from status endpoint
# - Heartbeat within last 30 seconds
```

## Scaling

### Docker Compose Scaling

```bash
# Scale a service to N replicas
docker-compose up -d --scale daniela-os=3
docker-compose up -d --scale agent_mobile=2

# Check running containers
docker-compose ps

# View logs for specific replica
docker-compose logs -f daniela-os_1
```

### Auto-Restart Policy

All services use `restart: unless-stopped`:

```yaml
services:
  daniela-os:
    restart: unless-stopped  # Auto-restart on failure
```

### Connection Pooling

The `aig-optimization` service provides connection pooling:

```
aig-optimization:9400 → conn/connection_pool.py
```

- Shared database connections
- Redis connection multiplexing
- HTTP keepalive for inter-service calls

### Load Balancing

Nginx upstream configuration:

```nginx
upstream daniela_backend {
    server daniela-os:5000;
    keepalive 32;
}
```

## Troubleshooting

### Service Won't Start

```bash
# Check if port is in use
netstat -ano | findstr :9200

# Kill process on port
taskkill /PID <pid> /F

# Check service logs
docker-compose logs daniela-os
```

### Database Locked (SQLite)

```bash
# SQLite WAL mode is enabled by default
# If locked, check for zombie processes
# Services use: PRAGMA journal_mode=WAL
# Services use: PRAGMA synchronous=NORMAL
```

### Redis Connection Refused

```bash
# Verify Redis is running
docker ps | grep redis

# Test connection
redis-cli ping

# Restart Redis
docker-compose restart redis
```

### Event Bus Issues

```bash
# Check NATS availability
# In-memory bus is used as fallback
# Check logs for: "NATS not available, using in-memory bus"

# Verify NATS (if running)
nats-cli server info
```

### Dashboard Shows Services Offline

```bash
# 1. Check service is running
curl http://localhost:9200/api/status

# 2. Check dashboard can reach service
curl http://localhost:9997/api/services

# 3. Check WebSocket connection
# Open browser console, look for 'status_update' events
```

### SSL Certificate Issues

```bash
# Regenerate self-signed certificate
cd ssl
openssl req -x509 -newkey rsa:4096 -keyout key.pem -out cert.pem -days 365 -nodes

# Restart nginx
docker-compose restart gateway
```

### Performance Issues

```bash
# Check system metrics
curl http://localhost:5001/api/health

# Monitor request latency
curl http://localhost:9997/api/services | jq '.status'

# Check Redis cache hit rate
redis-cli INFO stats
```

## Port Reference — 21 + Infra

| Port | Service | Category | Status path |
|------|---------|----------|-------------|
| 5020 | Epic PC | Core | `/api/status` |
| 9200 | Daniela Omnipresente | AI | `/api/status` |
| 9300 | Hermes Epic | AI | `/api/status` |
| 9400 | AIG Optimization | Infrastructure | `/api/opt/status` |
| 9500 | Frontend V1 | Frontend | `/api/frontend/status` |
| 9600 | Frontend V2 | Frontend | `/api/frontend2/status` |
| 9700 | Infra Optimization | Infrastructure | `/api/infra/status` |
| 9800 | Agent & Mobile | AI | `/api/agent/status` |
| 9997 | Unified Dashboard | Dashboard | `/api/status` |
| 9998 | Performance & Quality | Quality | `/api/perf/status` |
| 9999 | Security & Monitoring | Security | `/api/secure/status` |
| 9850 | Intel Engine | AI | `/api/intel/status` |
| 9860 | Auto Engine | AI | `/api/auto/status` |
| 9870 | Data Engine | Data | `/api/data/status` |
| 9880 | Secure Engine | Security | `/api/secure_engine/status` |
| 9890 | DevTools Engine | DevX | `/api/devtools/status` |
| 9840 | Ecosystem Engine | AI | `/api/ecosystem/status` |
| 9830 | UX Engine | Frontend | `/api/ux/status` |
| 9820 | Scale Engine | Infra | `/api/scale/status` |
| 9910 | Chaos Engine | Resilience | `/api/chaos/status` |
| 9911 | Regions Server | Resilience | `/api/regions/status` |
| 8080 | API Gateway (Python) | Infrastructure | `/health` |
| 9900 | Cross-Engine Orchestrator | Infrastructure | `/api/cross/status` |
| 8090 | Mobile PWA / API | Mobile | `/` |
| 5001 | Daniela Jarvis Backend (legacy) | Monitoring | `/api/health` |
| 6379 | Redis | Infrastructure | — |
| 80/443 | Nginx Gateway | Infrastructure | `/health` |
| 9090 | Prometheus | Monitoring | `/-/healthy` |
| 3000 | Grafana | Monitoring | `/api/health` |
