# aig API Documentation — Universo v1

> Complete API reference for all 21 runtime services + gateway + orchestrator.

## Base URLs — 21 Services + Infra

| Service | Base URL | Status path | Protocol |
|---------|----------|-------------|----------|
| API Gateway (Python) | `http://localhost:8080` | `/health` | HTTP |
| Cross-Engine Orchestrator | `http://localhost:9900` | `/api/cross/*` | HTTP |
| Mobile PWA / API | `http://localhost:8090` | `/` | HTTP |
| Unified Dashboard | `http://localhost:9997` | `/api/status` | HTTP + WebSocket |
| Epic PC | `http://localhost:5020` | `/api/status` | HTTP |
| Daniela Omnipresente | `http://localhost:9200` | `/api/status` | HTTP |
| Hermes Epic | `http://localhost:9300` | `/api/status` | HTTP |
| AIG Optimization | `http://localhost:9400` | `/api/opt/status` | HTTP |
| Frontend V1 | `http://localhost:9500` | `/api/frontend/status` | HTTP |
| Frontend V2 | `http://localhost:9600` | `/api/frontend2/status` | HTTP |
| Infra Optimization | `http://localhost:9700` | `/api/infra/status` | HTTP |
| Agent & Mobile | `http://localhost:9800` | `/api/agent/status` | HTTP |
| Security & Monitoring | `http://localhost:9999` | `/api/secure/status` | HTTP |
| Performance & Quality | `http://localhost:9998` | `/api/perf/status` | HTTP |
| Intel Engine | `http://localhost:9850` | `/api/intel/status` | HTTP |
| Auto Engine | `http://localhost:9860` | `/api/auto/status` | HTTP |
| Data Engine | `http://localhost:9870` | `/api/data/status` | HTTP |
| Secure Engine | `http://localhost:9880` | `/api/secure_engine/status` | HTTP |
| DevTools Engine | `http://localhost:9890` | `/api/devtools/status` | HTTP |
| Ecosystem Engine | `http://localhost:9840` | `/api/ecosystem/status` | HTTP |
| UX Engine | `http://localhost:9830` | `/api/ux/status` | HTTP |
| Scale Engine | `http://localhost:9820` | `/api/scale/status` | HTTP |
| Chaos Engine | `http://localhost:9910` | `/api/chaos/status` | HTTP |
| Regions Server | `http://localhost:9911` | `/api/regions/status` | HTTP |
| Prometheus | `http://localhost:9090` | `/-/healthy` | HTTP |
| Grafana | `http://localhost:3000` | `/api/health` | HTTP |
| Daniela Jarvis Backend (legacy) | `http://localhost:5001` | `/api/health` | HTTP (FastAPI) |
| Nginx Gateway | `https://localhost` | `/health` | HTTPS (80→443 redirect) |

## Common Endpoints

All services expose these standard endpoints:

### `GET /api/status`
Returns service health and metadata.

```bash
curl http://localhost:9200/api/status
```

```json
{
  "name": "Daniela Omnipresente",
  "version": "1.0.0",
  "modules": 57,
  "status": "alive",
  "registry": "active",
  "events": "active"
}
```

### `POST /api/heartbeat`
Updates service heartbeat in the registry. Returns `{"status": "ok"}`.

```bash
curl -X POST http://localhost:9200/api/heartbeat
```

## Service-Specific Endpoints

### Epic PC (`:5020`)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/status` | Service status |
| GET | `/` | Web interface |

### Daniela Omnipresente (`:9200`)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/status` | Full status with phases list |
| POST | `/api/heartbeat` | Heartbeat update |
| GET | `/api/ambient` | Ambient presence data |
| GET | `/api/consciousness` | Consciousness state |
| GET | `/api/emotional` | Emotional intelligence state |
| GET | `/api/routes` | Full route index grouped by prefix |
| GET | `/api/phases` | Phase route counts + failed phases |
| POST | `/api/ai/chat` | Real AI chat via FreeLLMAPI (`{"messages":[...]}`) |
| GET | `/api/ai/health` | AI backend health + key status |
| GET | `/api/ai/models` | Model catalog from router |
| POST | `/api/ai/dream/interpret` | Dream interpretation (`{"dream":"..."}`) |
| POST | `/api/ai/muse/continue` | Story co-writing (`{"story":"...","twist":false}`) |
| GET | `/` | Web interface |
| GET | `/mobile` | Mobile-optimized interface |

### Hermes Epic (`:9300`)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/status` | Service status |
| GET | `/` | Web interface |

### AIG Optimization (`:9400`)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/opt/status` | Status with cache availability |
| GET | `/` | Web interface |

### Frontend V1 (`:9500`)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/frontend/status` | Status (10 modules, 50 ideas) |
| GET | `/` | Web interface |

### Frontend V2 (`:9600`)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/frontend2/status` | Status (14 modules, 50 ideas) |
| GET | `/` | Web interface |

### Infra Optimization (`:9700`)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/infra/status` | Status (15 ideas, 5 modules) |
| GET | `/` | Web interface |

### Agent & Mobile (`:9800`)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/agent/status` | Status (10 ideas, 5 modules) |
| GET | `/` | Web interface |

### Security & Monitoring (`:9999`)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/secure/status` | Status (10 ideas) |
| GET | `/` | Web interface |

### Performance & Quality (`:9998`)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/perf/status` | Status (10 ideas, 5 modules) |
| GET | `/` | Web interface |

### Intel Engine (`:9850`)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/intel/status` | Status |
| GET | `/` | Web interface |

### Auto Engine (`:9860`)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/auto/status` | Status |
| GET | `/` | Web interface |

### Data Engine (`:9870`)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/data/status` | Status |
| GET | `/` | Web interface |

### Secure Engine (`:9880`)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/secure_engine/status` | Status |
| GET | `/` | Web interface |

### DevTools Engine (`:9890`)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/devtools/status` | Status |
| GET | `/` | Web interface |

### Ecosystem Engine (`:9840`)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/ecosystem/status` | Status |
| GET | `/` | Web interface |

### UX Engine (`:9830`)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/ux/status` | Status |
| GET | `/` | Web interface |

### Scale Engine (`:9820`)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/scale/status` | Status |
| GET | `/` | Web interface |

### Chaos Engine (`:9910`)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/chaos/status` | Engine status + armed flag |
| GET | `/api/chaos/experiments` | List experiments |
| POST | `/api/chaos/experiments` | Create/run experiment `{"fault":"latency","target":"daniela","duration_s":60}` |
| POST | `/api/chaos/stop` | Stop running experiment |
| GET | `/api/chaos/validators` | Steady-state validators |

```bash
curl http://localhost:9910/api/chaos/status
curl http://localhost:9910/api/chaos/experiments
curl -X POST http://localhost:9910/api/chaos/experiments \
  -H "Content-Type: application/json" \
  -d '{"fault":"latency","target":"daniela","duration_s":60}'
```

### Regions Server (`:9911`)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/regions/status` | Regions health + active region |
| GET | `/route?lat=..&lon=..` | Geo-route to closest region |
| GET | `/failover/status` | Failover chain + state |
| POST | `/failover/drill` | Trigger failover drill |
| GET | `/health` | Health check |
| POST | `/sync` | Cross-region sync `{"source":"eu-west","target":"us-east"}` |

```bash
curl http://localhost:9911/api/regions/status
curl "http://localhost:9911/route?lat=40.4168&lon=-3.7038"
curl http://localhost:9911/failover/status
```

### Daniela Jarvis Backend (`:5001`)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/system/info` | Full system metrics |
| GET | `/api/system/cpu` | CPU info |
| GET | `/api/system/memory` | Memory info |
| GET | `/api/system/disk` | Disk info |
| GET | `/api/system/network` | Network I/O |
| GET | `/api/system/processes` | Top 10 processes |
| GET | `/api/health` | Health check with subsystem status |

## Gateway Routes (`:8080` — `api_gateway.py`)

Single entrypoint proxying `/api/<engine>/*` → 21 engines.

| Route prefix | Target |
|--------------|--------|
| `/api/epic/*` | `http://localhost:5020` |
| `/api/daniela/*` | `http://localhost:9200` |
| `/api/hermes/*` | `http://localhost:9300` |
| `/api/opt/*` | `http://localhost:9400` |
| `/api/frontend/*` | `http://localhost:9500` |
| `/api/frontend2/*` | `http://localhost:9600` |
| `/api/infra/*` | `http://localhost:9700` |
| `/api/agent/*` | `http://localhost:9800` |
| `/api/secure/*` | `http://localhost:9999` |
| `/api/perf/*` | `http://localhost:9998` |
| `/api/intel/*` | `http://localhost:9850` |
| `/api/auto/*` | `http://localhost:9860` |
| `/api/data/*` | `http://localhost:9870` |
| `/api/secure_engine/*` | `http://localhost:9880` |
| `/api/devtools/*` | `http://localhost:9890` |
| `/api/ecosystem/*` | `http://localhost:9840` |
| `/api/ux/*` | `http://localhost:9830` |
| `/api/scale/*` | `http://localhost:9820` |
| `/api/chaos/*` | `http://localhost:9910` |
| `/api/regions/*` | `http://localhost:9911` |
| `/health` | Gateway self-check |
| `/metrics` | Prometheus metrics |

```bash
# Via gateway (same payload as direct)
curl http://localhost:8080/api/daniela/api/status
curl http://localhost:8080/api/chaos/api/chaos/status
curl http://localhost:8080/api/regions/api/regions/status
curl http://localhost:8080/health

# Direct (preferred for debugging)
curl http://localhost:9200/api/status
curl http://localhost:9910/api/chaos/status
curl http://localhost:9911/api/regions/status
```

## Orchestrator API (`:9900` — `cross_engine/server.py`)

Cross-service workflows + event bus bridge.

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/cross/status` | Orchestrator status |
| POST | `/api/cross/dispatch` | Dispatch action to engine `{"engine":"daniela","action":"run"}` |
| POST | `/api/cross/chain` | Chained call across engines |
| POST | `/api/cross/fanout` | Fan-out to N engines, aggregate |
| GET | `/api/cross/events` | Recent cross-engine events |

```bash
curl http://localhost:9900/api/cross/status
curl -X POST http://localhost:9900/api/cross/dispatch \
  -H "Content-Type: application/json" \
  -d '{"engine":"daniela","action":"ping"}'
curl -X POST http://localhost:9900/api/cross/fanout \
  -H "Content-Type: application/json" \
  -d '{"engines":["daniela","hermes"],"action":"status"}'
```

## Dashboard API (`:9997`)

### `GET /api/services`
Returns all services with live status.

```bash
curl http://localhost:9997/api/services
```

```json
{
  "services": [...],
  "status": {
    "epic_pc": {"status": "online", "port": 5020},
    "daniela": {"status": "online", "port": 9200}
  },
  "timestamp": 1695000000.0,
  "summary": {"total": 11, "online": 9, "offline": 2}
}
```

### `GET /api/services/<service_id>`
Returns status for a specific service.

```bash
curl http://localhost:9997/api/services/daniela
```

### `GET /api/registry`
Returns registered services with registry and event bus status.

```bash
curl http://localhost:9997/api/registry
```

```json
{
  "registered": [
    {
      "name": "daniela",
      "port": 9200,
      "category": "AI",
      "registry": "active",
      "events": "active"
    }
  ]
}
```

### `GET /api/events`
Returns recent events from all services.

```bash
curl http://localhost:9997/api/events
```

### WebSocket Events

Connect to the dashboard via WebSocket:

```javascript
const socket = io('http://localhost:9997');

// Receive status updates (every 5s)
socket.on('status_update', (data) => {
  console.log(data.services, data.summary);
});

// Request manual status update
socket.emit('request_status');
```

**Events emitted by server:**
| Event | Payload | Frequency |
|-------|---------|-----------|
| `status_update` | `{services, status, timestamp, summary}` | Every 5s |

**Events accepted from client:**
| Event | Description |
|-------|-------------|
| `connect` | Client connects, receives initial status |
| `request_status` | Client requests immediate status update |

## Health Check Endpoints

| Service | Endpoint | Check Type |
|---------|----------|------------|
| Dashboard | `GET /api/status` | Aggregated |
| Nginx | `GET /health` | Static 200 |
| Jarvis Backend | `GET /api/health` | CPU/RAM/Disk thresholds |
| All others | `GET /api/status` | Service-specific |

### Health Response Format

```json
{
  "status": "healthy|degraded|unhealthy",
  "checks": {
    "cpu": {"status": "ok|warning", "value": 45.2},
    "memory": {"status": "ok|warning", "value": 67.8},
    "disk": {"status": "ok|warning", "value": 55.1}
  }
}
```

## Event Bus Patterns

### Publish (In-Memory)

```python
from aig_shared.events import get_in_memory_bus, Event

bus = get_in_memory_bus("daniela")
event = Event(
    type="service.startup",
    payload={"service": "daniela", "port": 9200},
    source="daniela"
)
bus.publish_sync("startup", event)
```

### Subscribe (In-Memory)

```python
from aig_shared.events import get_in_memory_bus, Event

bus = get_in_memory_bus("daniela")
def handler(event: Event):
    print(f"Received: {event.type} from {event.source}")

bus.subscribe_sync("startup", handler)
```

### Event Types

| Type | Source | Description |
|------|--------|-------------|
| `service.startup` | Any | Service started |
| `service.shutdown` | Any | Service shutting down |
| `service.heartbeat` | Any | Heartbeat update |
| `health.check` | Dashboard | Health check triggered |
| `status.update` | Dashboard | Status poll completed |

## Example curl Commands

```bash
# Check all 21 service statuses (direct)
for port in 5020 9200 9300 9400 9500 9600 9700 9800 9998 9999 9997 9850 9860 9870 9880 9890 9840 9830 9820 9910 9911; do
  echo "== $port =="; curl -s http://localhost:$port/api/status 2>/dev/null || curl -s http://localhost:$port/api/chaos/status 2>/dev/null || curl -s http://localhost:$port/api/regions/status 2>/dev/null | head -c 300; echo;
done

# Per-engine status paths
curl -s http://localhost:5020/api/status | python -m json.tool
curl -s http://localhost:9400/api/opt/status | python -m json.tool
curl -s http://localhost:9500/api/frontend/status | python -m json.tool
curl -s http://localhost:9600/api/frontend2/status | python -m json.tool
curl -s http://localhost:9700/api/infra/status | python -m json.tool
curl -s http://localhost:9800/api/agent/status | python -m json.tool
curl -s http://localhost:9999/api/secure/status | python -m json.tool
curl -s http://localhost:9998/api/perf/status | python -m json.tool
curl -s http://localhost:9850/api/intel/status | python -m json.tool
curl -s http://localhost:9860/api/auto/status | python -m json.tool
curl -s http://localhost:9870/api/data/status | python -m json.tool
curl -s http://localhost:9880/api/secure_engine/status | python -m json.tool
curl -s http://localhost:9890/api/devtools/status | python -m json.tool
curl -s http://localhost:9840/api/ecosystem/status | python -m json.tool
curl -s http://localhost:9830/api/ux/status | python -m json.tool
curl -s http://localhost:9820/api/scale/status | python -m json.tool
curl -s http://localhost:9910/api/chaos/status | python -m json.tool
curl -s http://localhost:9911/api/regions/status | python -m json.tool

# Gateway + orchestrator
curl http://localhost:8080/health | python -m json.tool
curl http://localhost:8080/api/daniela/api/status | python -m json.tool
curl http://localhost:9900/api/cross/status | python -m json.tool

# Dashboard aggregated status
curl http://localhost:9997/api/services | python -m json.tool

# Jarvis system metrics
curl http://localhost:5001/api/system/info | python -m json.tool

# Health check with threshold
curl http://localhost:5001/api/health | python -m json.tool

# Registry view
curl http://localhost:9997/api/registry | python -m json.tool

# Recent events
curl http://localhost:9997/api/events | python -m json.tool

# Trigger heartbeat
curl -X POST http://localhost:9200/api/heartbeat

# Dispatch skill (core service)
curl -X POST http://localhost:8082/api/skills/dispatch \
  -H "Content-Type: application/json" \
  -d '{"action": "run_unit_tests"}'
```

## Error Responses

All services return consistent error formats:

```json
{
  "error": "ERROR_CODE",
  "message": "Human-readable description",
  "details": {}
}
```

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `INTERNAL_ERROR` | 500 | Unexpected server error |
| `VALIDATION_ERROR` | 400 | Invalid request data |
| `NOT_FOUND` | 404 | Resource not found |
| `UNAUTHORIZED` | 401 | Missing/invalid auth |
| `FORBIDDEN` | 403 | Insufficient permissions |
| `RATE_LIMITED` | 429 | Too many requests |
| `SERVICE_UNAVAILABLE` | 503 | Service offline |
| `TIMEOUT` | 504 | Request timeout |
