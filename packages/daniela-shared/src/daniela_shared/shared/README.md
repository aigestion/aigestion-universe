# AIG Shared

Common libraries for all aig services.

## Installation

```bash
pip install -e ./aig-shared
# Or with NATS support:
pip install -e ./aig-shared[nats]
```

## Modules

| Module | Description |
|--------|-------------|
| `aig_shared.config` | Service configuration, ports, database/Redis/NATS URLs |
| `aig_shared.auth` | JWT encoding/decoding without external dependencies |
| `aig_shared.logging` | Structured JSON logging with correlation IDs |
| `aig_shared.metrics` | Prometheus metrics wrapper with fallback |
| `aig_shared.errors` | Standardized error handling with codes |
| `aig_shared.events` | NATS-based event bus for inter-service communication |
| `aig_shared.utils` | Common utilities (retry, timer, hashing, etc.) |

## Quick Start

```python
from aig_shared import get_logger, get_metrics_registry, create_jwt_handler
from aig_shared.config import get_service_config, get_service_urls
from aig_shared.auth import create_jwt_handler
from aig_shared.errors import AppError, ValidationError
from aig_shared.events import get_event_bus, Event
from aig_shared.utils import generate_id, retry, timer

# Logging
logger = get_logger("my-service")
logger.info("Service started")

# Metrics
metrics = get_metrics_registry("my-service")
request_counter = metrics.counter("requests_total", "Total requests", ["method", "endpoint"])
request_counter.labels(method="GET", endpoint="/api").inc()

# Auth
jwt = create_jwt_handler()
token = jwt.encode({"sub": "user123", "name": "John", "tier": "premium"})

# Events
event_bus = get_event_bus("my-service")
await event_bus.connect()
await event_bus.publish("user.created", Event(type="user.created", payload={"id": "123"}, source="my-service"))

# Utils
user_id = generate_id("usr_")
@retry(max_attempts=3, delay=1.0)
def unreliable_operation():
    ...
```

## Configuration

Environment variables:
- `DATABASE_URL` - Database connection string
- `REDIS_URL` - Redis connection string
- `NATS_URL` - NATS server URL
- `JWT_SECRET` - JWT signing secret
- `SERVICE_BASE_URL` - Base URL for service URLs