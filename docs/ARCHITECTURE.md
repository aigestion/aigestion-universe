# aig Architecture — Universo v1

> System architecture for the aig monorepo — 21 runtime services, gateway + orchestrator, event-driven, service registry, multi-region + chaos resilience.

## System Overview

aig is an event-driven microservices platform built with Flask/FastAPI. The system comprises **21 runtime services** orchestrated through a central **Unified Dashboard**, a Python **API Gateway** (`api_gateway.py` :8080), a **Cross-Engine Orchestrator** (`cross_engine/server.py` :9900), a **Service Registry** for discovery, and an **Event Bus** (NATS with in-memory fallback) for inter-service communication. Resilience is provided by **Chaos Engine** (:9910) and **Regions server** (:9911, `multi-region/server.py`). Observability via **Prometheus** (:9090) + **Grafana** (:3000). Mobile PWA served on :8090.

```
┌─────────────────────────────────────────────────────────────┐
│                     API Gateway (Nginx)                      │
│                    Ports 80/443 (HTTPS)                      │
└──────────────────────────┬──────────────────────────────────┘
                           │
┌──────────────────────────┴──────────────────────────────────┐
│                    Unified Dashboard                         │
│                    Port 9997 (Flask+SocketIO)                │
│         ┌────────────────────────────────────┐              │
│         │  Service Registry │ Event Aggregator│              │
│         └────────────────────────────────────┘              │
└────┬────────┬────────┬────────┬────────┬────────┬──────────┘
     │        │        │        │        │        │
┌────┴──┐ ┌──┴───┐ ┌──┴───┐ ┌──┴───┐ ┌──┴───┐ ┌──┴───┐
│EpicPC │ │Daniela│ │Hermes│ │AIG   │ │Front │ │Infra │
│:5020  │ │:9200  │ │:9300 │ │Opt   │ │V1/V2 │ │Opt   │
│       │ │       │ │      │ │:9400 │ │:9500 │ │:9700 │
│       │ │       │ │      │ │      │ │:9600 │ │      │
└───────┘ └───────┘ └──────┘ └──────┘ └──────┘ └──────┘
     │
┌────┴──┐ ┌───────────┐ ┌──────────┐ ┌──────────┐
│Agent  │ │Security   │ │Perf&Qual │ │Jarvis    │
│Mobile │ │Monitoring │ │          │ │Backend   │
│:9800  │ │:9999      │ │:9998     │ │:5001     │
└───────┘ └───────────┘ └──────────┘ └──────────┘
```

## Service Map — 21 Runtime Services

| # | Service | Port | Status path | Category | Description |
|---|---------|------|-------------|----------|-------------|
| 1 | **Epic PC** (`epic_pc`) | 5020 | `/api/status` | Core | Desktop experience hub — voice AI, neural wallpaper, file galaxy, notification brain, hologram, code copilot, cross-device telepathy, AR overlay, living organism, memory palace, context switcher, focus mode, meeting prepper, email brain, knowledge weaver |
| 2 | **Daniela Omnipresente** (`daniela`) | 9200 | `/api/status` | AI | AI personality system — ambient presence, consciousness, proactive engine, emotional intelligence, embodiment, cross-device sync, voice activation (57 modules) |
| 3 | **Hermes Epic** (`hermes`) | 9300 | `/api/status` | AI | AI communication and messaging hub |
| 4 | **AIG Optimization** (`optimization`) | 9400 | `/api/opt/status` | Infra | Performance optimization engine — Redis caching, SSE streaming, health checks, observability, connection pooling |
| 5 | **Frontend V1** (`frontend_v1`) | 9500 | `/api/frontend/status` | Frontend | Frontend optimization — service worker, web manifest, virtual scroll, perf monitoring, asset optimization, caching, theme engine, UX enhancements, command palette, animation engine (10 modules) |
| 6 | **Frontend V2** (`frontend_v2`) | 9600 | `/api/frontend2/status` | Frontend | Advanced frontend — code splitting, lazy loading, web workers, SSR engine, image/font optimization, tree shaking, WebAssembly, edge compute, accessibility, security, analytics, resource hints, HTTP/2 (14 modules) |
| 7 | **Infra Optimization** (`infra_opt`) | 9700 | `/api/infra/status` | Infra | Infrastructure management — Docker Compose, Nginx LB, auto-healing, health dashboard, zero-downtime deploys, SQLite WAL, query optimizer, connection pool, vector search, backup scheduler, Redis rate limit, request caching, GraphQL, gRPC bridge, API versioning, Prometheus, Grafana, structured logging, distributed tracing, alert system (20 modules) |
| 8 | **Agent & Mobile** (`agent_mobile`) | 9800 | `/api/agent/status` | AI | Agent orchestration — swarm intelligence, agent registry, agent chain, agent memory, agent health, ADB optimization, battery saver, push notifications, mobile offline, NFC connect (10 modules) |
| 9 | **Security & Monitoring** (`security`) | 9999 | `/api/secure/status` | Security | Security layer — secrets management, security headers, JWT refresh, IP whitelist, audit log, real-time metrics, anomaly detection, log aggregation (8 modules) |
| 10 | **Performance & Quality** (`perf`) | 9998 | `/api/perf/status` | Perf | Code quality — async I/O, WebSocket realtime, background workers, HTTP/2, Brotli compression, connection keepalive, type hints, auto formatting, test coverage, CI/CD (10 modules) |
| 11 | **Unified Dashboard** (`dashboard`) | 9997 | `/api/status` | Dashboard | Central monitoring — service status polling, WebSocket live updates, service registry view, event aggregation |
| 12 | **Intel Engine** (`intel-engine`) | 9850 | `/api/intel/status` | AI | Intelligence engine — research, insights, knowledge synthesis |
| 13 | **Auto Engine** (`auto-engine`) | 9860 | `/api/auto/status` | AI | Automation engine — pipelines, schedulers, autonomous tasks |
| 14 | **Data Engine** (`data-engine`) | 9870 | `/api/data/status` | Data | Data engine — ingestion, RAG, analytics, persistence |
| 15 | **Secure Engine** (`secure-engine`) | 9880 | `/api/secure_engine/status` | Security | Hardened secure engine — vault, guards, policy enforcement |
| 16 | **DevTools Engine** (`devtools-engine`) | 9890 | `/api/devtools/status` | DevX | Developer tools — docs engine, scaffolds, test helpers |
| 17 | **Ecosystem Engine** (`ecosystem-engine`) | 9840 | `/api/ecosystem/status` | AI | Ecosystem — plugins, marketplace, connectors, skills |
| 18 | **UX Engine** (`ux-engine`) | 9830 | `/api/ux/status` | Frontend | UX engine — themes, layouts, accessibility, animations |
| 19 | **Scale Engine** (`scale_engine`) | 9820 | `/api/scale/status` | Infra | Scaling engine — autoscale policies, workers, load profiles |
| 20 | **Chaos Engine** (`chaos-engine`) | 9910 | `/api/chaos/status` | Resilience | Chaos engineering — faults, experiments, scheduler, validators (`chaos_engine/server.py`, `faults.py`, `experiments.py`, `scheduler.py`, `validators.py`) |
| 21 | **Regions Server** (`regions`) | 9911 | `/api/regions/status` | Resilience | Multi-region control plane — LB, failover, replication, DNS sim (`multi-region/server.py`, `load_balancer.py`, `failover.py`, `replication.py`, `health_mesh.py`, `dns_sim.py`) |

### Gateway + Orchestrator + Edge

| Component | Port | Entry point | Description |
|-----------|------|-------------|-------------|
| **API Gateway** | 8080 | `api_gateway.py` | Single entrypoint. Proxies `/api/<engine>/*` → 21 engines. Rate limiting, JWT, CORS, `/health`, `/metrics` |
| **Cross-Engine Orchestrator** | 9900 | `cross_engine/server.py` | Cross-service workflows. `/api/cross/*` (dispatch, chain, fan-out, event bus bridge). Modules: `orchestrator.py`, `gateway.py`, `connector.py`, `event_bus.py`, `protocols.py` |
| **Mobile PWA / API** | 8090 | `mobile-app/` | PWA + mobile backend (v2). Served statically / via container. **Árbol único de cliente** desde 2026-09-29: absorbe `android_app/mobile-app/`, `phone_deploy/` y `pixel/` |
| **Nginx Gateway (alt)** | 80/443 | `nginx.conf` | Reverse proxy, rate limiting, SSL termination (legacy / prod-front) |
| **Prometheus** | 9090 | `prometheus/` + `docker-compose.monitoring.yml` | Metrics collection |
| **Grafana** | 3000 | `grafana/` | Metrics visualization |

### Supporting Infrastructure

| Service | Port | Description |
|---------|------|-------------|
| **Daniela Jarvis Backend** | 5001 | FastAPI system monitoring (CPU, RAM, GPU, Network, Disk) — legacy/support |
| **Redis** | 6379 | Cache and message broker |
| **Nginx API Gateway** | 80/443 | Reverse proxy, rate limiting, SSL termination |
| **Prometheus** | 9090 | Metrics collection (profile: `monitoring`) |
| **Grafana** | 3000 | Metrics visualization |
| **Mobile** | 8090 | PWA + mobile API |

### Event Bus

Dual-mode (`aig-shared/aig_shared/events/` + `cross_engine/event_bus.py`):
- **NATS JetStream** (production): durable messaging, request-response.
- **In-memory** (development): direct calls, no external deps.
- Orchestrator (:9900) bridges cross-engine events (`/api/cross/*`).

### Regions / Chaos (Resilience)

- **Regions server :9911** (`multi-region/server.py`): global LB (:8080 logical), region configs (eu-west Madrid, us-east Virginia, ap-south Mumbai), `failover.py` (3-strike failover, 30s cooldown), `replication.py` (last-write-wins), `health_mesh.py` (5s checks), `dns_sim.py`. See `docs/MULTI_REGION.md`. Compose: `multi-region/docker-compose.multi.yml`.
- **Chaos Engine :9910** (`chaos_engine/server.py`): `faults.py` (latency, error, kill, partition), `experiments.py` (scenarios), `scheduler.py` (cron/interval), `validators.py` (steady-state checks). Guarded — never enabled in prod without explicit flag. Tests: `tests/performance/test_chaos.py`, `tests/core/test_regions_active.py`.

## Port Assignments — Full Table (21 + infra)

| Port | Service | Protocol | Status path |
|------|---------|----------|-------------|
| 5020 | Epic PC | HTTP | `/api/status` |
| 9200 | Daniela Omnipresente | HTTP | `/api/status` |
| 9300 | Hermes Epic | HTTP | `/api/status` |
| 9400 | AIG Optimization | HTTP | `/api/opt/status` |
| 9500 | Frontend V1 | HTTP | `/api/frontend/status` |
| 9600 | Frontend V2 | HTTP | `/api/frontend2/status` |
| 9700 | Infra Optimization | HTTP | `/api/infra/status` |
| 9800 | Agent & Mobile | HTTP | `/api/agent/status` |
| 9999 | Security & Monitoring | HTTP | `/api/secure/status` |
| 9998 | Performance & Quality | HTTP | `/api/perf/status` |
| 9997 | Unified Dashboard | HTTP + WebSocket | `/api/status` |
| 9850 | Intel Engine | HTTP | `/api/intel/status` |
| 9860 | Auto Engine | HTTP | `/api/auto/status` |
| 9870 | Data Engine | HTTP | `/api/data/status` |
| 9880 | Secure Engine | HTTP | `/api/secure_engine/status` |
| 9890 | DevTools Engine | HTTP | `/api/devtools/status` |
| 9840 | Ecosystem Engine | HTTP | `/api/ecosystem/status` |
| 9830 | UX Engine | HTTP | `/api/ux/status` |
| 9820 | Scale Engine | HTTP | `/api/scale/status` |
| 9910 | Chaos Engine | HTTP | `/api/chaos/status` |
| 9911 | Regions Server | HTTP | `/api/regions/status` |
| 8080 | API Gateway - other project (`api_gateway.py`, NOT ours) | HTTP | `/health` + `/v1/*` |
| 8095 | Cross-Engine Gateway (ours) | HTTP | `/api/gateway/*` + `/api/<engine>/*` |
| 9900 | Cross-Engine Orchestrator | HTTP | `/api/cross/*` |
| 8090 | Mobile PWA (nginx container `aig-mobile`) | HTTP | `/` |
| 3002 | FreeLLMAPI router (Docker `freellmapi`, OpenRouter backend) | HTTP | `/v1/*` |
| 5001 | Daniela Jarvis Backend (legacy) | HTTP (FastAPI) | `/api/health` |
| 6379 | Redis | TCP | — |
| 80/443 | Nginx Gateway | HTTP/HTTPS | `/health` |
| 9090 | Prometheus | HTTP | `/-/healthy` |
| 3000 | Grafana | HTTP | `/api/health` |

## Communication Patterns

### HTTP (Primary)
All services expose REST APIs via Flask/FastAPI. The Nginx gateway routes external traffic to internal services. Services communicate directly via HTTP for synchronous calls.

```
Client → Nginx:443 → Service (port N) → Response
```

### WebSocket (Real-time)
The Unified Dashboard uses Flask-SocketIO for live status updates. The dashboard polls all services every 5 seconds and pushes updates to connected clients.

```
Dashboard:9997 ←WS→ Browser (status_update events)
```

### Event Bus (Async)
Two modes available:
- **NATS** (production): JetStream for durable messaging, request-response pattern
- **In-memory** (development): Direct function calls, no external dependencies

```
Service A → Event Bus → Service B
  publish(subject, event)    subscribe(subject, handler)
```

**Event structure:**
```python
Event(
    type="service.startup",       # Event type
    payload={"service": "daniela", "port": 9200},
    source="daniela",              # Originating service
    timestamp="2026-09-17T12:00:00Z",
    correlation_id="uuid-..."     # Optional trace ID
)
```

## Service Registry Flow

```
┌──────────┐     ┌─────────────────┐     ┌──────────────────┐
│ Service  │────>│ register_service │────>│  ServiceRegistry │
│ Startup  │     │   (aig_shared)  │     │  (in-memory)     │
└──────────┘     └─────────────────┘     └────────┬─────────┘
                                                   │
                              ┌─────────────────────┤
                              │                     │
                     ┌────────▼────────┐   ┌───────▼────────┐
                     │ Heartbeat Loop  │   │ Health Check   │
                     │ (30s interval)  │   │ (heartbeat     │
                     │                 │   │  < 30s = OK)   │
                     └────────┬────────┘   └───────┬────────┘
                              │                     │
                              └──────────┬──────────┘
                                         │
                              ┌──────────▼──────────┐
                              │  Dashboard polls     │
                              │  every 5s            │
                              └──────────┬──────────┘
                                         │
                              ┌──────────▼──────────┐
                              │  WebSocket broadcast │
                              │  to connected clients│
                              └─────────────────────┘
```

**Registration flow:**
1. Service starts → calls `register_service(name, host, port, category)`
2. Service sends heartbeat via `POST /api/heartbeat` every 30s
3. Registry marks service as "healthy" if heartbeat < 30s old
4. Dashboard polls all services and broadcasts status via WebSocket

## Data Flow

```
┌─────────┐  HTTP   ┌─────────┐  HTTP   ┌──────────┐
│ Browser │────────>│ Nginx   │────────>│ Dashboard│
│         │         │ :80/443 │         │   :9997  │
└─────────┘         └─────────┘         └────┬─────┘
                                             │ WS
                                       ┌─────▼──────┐
                                       │  Browser   │
                                       │ (real-time)│
                                       └────────────┘

┌─────────┐  HTTP   ┌──────────┐  Event  ┌──────────┐
│ Service │────────>│ Registry │  Bus    │ Service  │
│   A     │         │          │────────>│    B     │
└─────────┘         └──────────┘         └──────────┘
                          │
                    ┌─────▼──────┐
                    │   Redis    │
                    │  :6379     │
                    │  (cache)   │
                    └────────────┘
```

## Security Model

| Layer | Mechanism | Implementation |
|-------|-----------|----------------|
| **Transport** | TLS 1.2/1.3 | Nginx SSL termination with cert.pem/key.pem |
| **Authentication** | JWT | `aig_shared.auth.JWTHandler` — HS256, configurable expiry |
| **Rate Limiting** | Token bucket | Nginx `limit_req_zone` — 10r/s API, 5r/m auth |
| **IP Filtering** | Whitelist | `sec-opt/audit/ip_whitelist.py` |
| **Audit** | Structured logs | `sec-opt/audit/audit_log.py` — all actions logged |
| **Secrets** | Vault | `sec-opt/secrets/secrets_management.py` |
| **Headers** | CSP, CORS | `sec-opt/security/security_headers.py` |
| **Anomaly** | Detection | `sec-opt/monitoring2/anomaly_detection.py` |

## Deployment Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Docker Compose Stack                       │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   Nginx LB   │  │   Prometheus │  │   Grafana    │      │
│  │   :80/:443   │  │   :9090      │  │   (custom)   │      │
│  └──────┬───────┘  └──────────────┘  └──────────────┘      │
│         │                                                    │
│  ┌──────┴──────────────────────────────────────────────┐    │
│  │              aig-net (bridge)                   │    │
│  ├──────────────────────────────────────────────────────┤    │
│  │                                                      │    │
│  │  ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐       │    │
│  │  │Daniela │ │ Epic   │ │ Hermes │ │  AIG   │       │    │
│  │  │  OS    │ │  PC    │ │  Epic  │ │  Opt   │       │    │
│  │  │ :5000  │ │ :5020  │ │ :9300  │ │ :9400  │       │    │
│  │  └────────┘ └────────┘ └────────┘ └────────┘       │    │
│  │                                                      │    │
│  │  ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐       │    │
│  │  │Frontend│ │Frontend│ │ Infra  │ │ Agent  │       │    │
│  │  │  V1    │ │  V2    │ │  Opt   │ │Mobile  │       │    │
│  │  │ :9500  │ │ :9600  │ │ :9700  │ │ :9800  │       │    │
│  │  └────────┘ └────────┘ └────────┘ └────────┘       │    │
│  │                                                      │    │
│  │  ┌────────┐ ┌────────┐ ┌────────┐                   │    │
│  │  │Security│ │ Perf   │ │Dashboard│                  │    │
│  │  │        │ │Quality │ │   v2    │                  │    │
│  │  │ :9999  │ │ :9998  │ │  :9997  │                  │    │
│  │  └────────┘ └────────┘ └────────┘                   │    │
│  │                                                      │    │
│  └──────────────────────────────────────────────────────┘    │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐    │
│  │  Redis :6379  │  Volume: redis-data                   │    │
│  └──────────────────────────────────────────────────────┘    │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

**Key infrastructure components:**
- **Docker Compose**: Orchestrates all services with `restart: unless-stopped`
- **Nginx**: Load balancer, SSL termination, rate limiting, reverse proxy
- **Prometheus**: Scrapes `/metrics` endpoints (profile: `monitoring`)
- **Grafana**: Dashboards for system metrics visualization
- **Redis**: Shared cache, session store, rate limit counters

## Scaling Strategy

### Horizontal Scaling (Docker Compose)
```bash
# Scale specific service to N replicas
docker-compose up -d --scale daniela-os=3
docker-compose up -d --scale agent_mobile=2
```

### Health Checks
- **TCP check**: Quick port connectivity test (1s timeout)
- **HTTP check**: Service-specific status endpoint
- **Heartbeat**: Services POST to `/api/heartbeat` every 30s
- **Registry health**: `ServiceRegistry.check_health()` — heartbeat < 30s = healthy

### Auto-Restart
All services configured with `restart: unless-stopped` in Docker Compose. The `infra-opt/docker/auto_healing_v2.py` module provides application-level auto-healing.

### Load Balancing
- **Nginx upstream**: `keepalive 32` connection pool to backend
- **Rate limiting**: 10 req/s for API, 5 req/min for auth endpoints
- **Connection pooling**: `aig-optimization/conn/connection_pool.py` for shared connections

### Monitoring & Alerting
- **Prometheus metrics**: Request count, latency histograms, error rates
- **Grafana dashboards**: Real-time visualization of all service metrics
- **Structured logging**: JSON logs with correlation IDs for distributed tracing
- **Alert system**: `infra-opt/monitoring/alert_system.py` for threshold-based alerts
