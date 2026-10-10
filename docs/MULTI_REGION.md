# aig Multi-Region Deployment (Phase 4)

## Architecture Overview

```
                    ┌─────────────────────────────┐
                    │       Global Load Balancer   │
                    │         :8080                │
                    │   (GeoDNS / Round-Robin /    │
                    │    Weighted Routing)          │
                    └──────────┬──────────────────┘
                               │
              ┌────────────────┼────────────────┐
              │                │                │
     ┌────────▼──────┐ ┌──────▼──────┐ ┌───────▼─────┐
     │  EU-West       │ │  US-East    │ │  AP-South   │
     │  (Madrid)      │ │  (Virginia) │ │  (Mumbai)   │
     │                │ │             │ │             │
     │ ┌────────────┐ │ │ ┌─────────┐│ │ ┌─────────┐│
     │ │ Service    │ │ │ │ Service ││ │ │ Service ││
     │ │ :8080      │ │ │ │ :8080   ││ │ │ :8080   ││
     │ └────────────┘ │ │ └─────────┘│ │ └─────────┘│
     │ ┌────────────┐ │ │ ┌─────────┐│ │ ┌─────────┐│
     │ │ Redis      │ │ │ │ Redis   ││ │ │ Redis   ││
     │ │ Primary    │ │ │ │ Primary ││ │ │ Primary ││
     │ ├────────────┤ │ │ ├─────────┤│ │ ├─────────┤│
     │ │ Redis Rep1 │ │ │ │         ││ │ │         ││
     │ │ Redis Rep2 │ │ │ │         ││ │ │         ││
     │ └────────────┘ │ │ └─────────┘│ │ └─────────┘│
     └────────────────┘ └────────────┘ └─────────────┘
              │                │                │
              └────────────────┼────────────────┘
                      Cross-Region Replication
```

## Region Configurations

| Region     | Primary Host                          | Replicas        | Latency Threshold | Failover Order |
|------------|---------------------------------------|-----------------|-------------------|----------------|
| eu-west    | eu-west-primary.aig.local:8080        | 2 replicas      | 150ms             | 0 (primary)    |
| us-east    | us-east-primary.aig.local:8080        | 1 replica       | 200ms             | 1              |
| ap-south   | ap-south-primary.aig.local:8080       | 1 replica       | 250ms             | 2              |

## Failover Flow

```
Health Check (5s interval)
         │
         ▼
  Consecutive Failures >= 3?
         │
    Yes  │  No → Continue
         ▼
  Mark Region DOWN
         │
         ▼
  Find Next Healthy Region
  in Failover Chain
         │
         ▼
  Update DNS (Simulate)
         │
         ▼
  Emit Notification
         │
         ▼
  Wait for Restore
  (30s cooldown)
```

**Failover Chains:**
- `eu-west` → `us-east` → `ap-south`
- `us-east` → `ap-south` → `eu-west`
- `ap-south` → `eu-west` → `us-east`

## Routing Strategies

### GeoDNS (Default)
Routes requests to the geographically closest region using Haversine distance.

### Round-Robin
Distributes requests evenly across all regions in order.

### Weighted (Canary)
Routes based on configurable weights per region. Useful for canary deployments:
- Set `canary_weights = [CanaryWeight("eu-west", 0.1)]` to send 10% of traffic to eu-west.

## Replication

- **Conflict Resolution:** Last-write-wins (default), merge, or manual
- **SQLite WAL Mode:** Concurrent reads during replication
- **Cross-Region Sync:** `sync_data(source, target, data_type)` merges records by timestamp/version

## Deployment Guide

### Prerequisites
- Docker & Docker Compose
- Python 3.11+

### Start Multi-Region Stack

```bash
cd C:\Users\Alejandro\aig
docker compose -f multi-region/docker-compose.multi.yml up -d
```

### Services

| Service          | Internal Port | External Port |
|------------------|---------------|---------------|
| Global LB        | 8080          | 8080          |
| EU-West          | 8080          | 8081          |
| US-East          | 8080          | 8082          |
| AP-South         | 8080          | 8083          |
| EU-West Redis    | 6379          | 6380          |
| US-East Redis    | 6379          | 6381          |
| AP-South Redis   | 6379          | 6382          |

### Verify Deployment

```bash
# Health check
curl http://localhost:8080/health

# Route a request
curl "http://localhost:8080/route?lat=40.4168&lon=-3.7038"

# Check failover status
curl http://localhost:8080/failover/status
```

### Run Tests

```bash
cd C:\Users\Alejandro\aig
python -m pytest tests/integration/test_multi_region.py -v
```
