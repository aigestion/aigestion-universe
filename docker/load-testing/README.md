# aig Load Testing Suite

Comprehensive load testing for all 19 aig engines using k6 and Locust.

## Engines Tested

| Engine | Port | Endpoint | Category |
|--------|------|----------|----------|
| epic_pc | 5020 | /api/status | Core |
| daniela | 9200 | /api/status | Core |
| hermes | 9300 | /api/status | Core |
| optimization | 9400 | /api/opt/status | AI |
| frontend_v1 | 9500 | /api/frontend/status | Frontend |
| frontend_v2 | 9600 | /api/frontend2/status | Frontend |
| infra_opt | 9700 | /api/infra/status | AI |
| agent_mobile | 9800 | /api/agent/status | AI |
| security | 9999 | /api/secure/status | Cross-cutting |
| perf | 9998 | /api/perf/status | Cross-cutting |
| dashboard | 9997 | /api/status | Core |
| intel_engine | 9850 | /api/intel/status | Intel |
| auto_engine | 9860 | /api/auto/status | Intel |
| data_engine | 9870 | /api/data/status | Intel |
| secure_engine | 9880 | /api/secure_engine/status | Intel |
| devtools_engine | 9890 | /api/devtools/status | DevOps |
| ecosystem_engine | 9840 | /api/ecosystem/status | DevOps |
| ux_engine | 9830 | /api/ux/status | DevOps |
| scale_engine | 9820 | /api/scale/status | DevOps |

## Test Types

### 1. Smoke Test (`k6/smoke.js`)
- **Purpose**: Quick validation all endpoints respond
- **Load**: 1 VU for 30 seconds
- **Thresholds**: p95 < 500ms, error_rate < 1%

### 2. Load Test (`k6/load.js`)
- **Purpose**: Normal operational load
- **Load**: Ramp to 50 VUs over 2min, hold 5min, ramp down
- **Thresholds**: p95 < 1s, p99 < 2s, error_rate < 2%

### 3. Stress Test (`k6/stress.js`)
- **Purpose**: Find breaking point
- **Load**: Ramp to 200 VUs over 5min
- **Thresholds**: p95 < 3s, p99 < 5s, error_rate < 10%

### 4. Soak Test (`k6/soak.js`)
- **Purpose**: Detect memory/connection leaks
- **Load**: 50 VUs for 1 hour
- **Thresholds**: p95 < 2s, p99 < 4s, error_rate < 5%, drift < 2x

### 5. Spike Test (`k6/spike.js`)
- **Purpose**: Test circuit breakers, auto-scaling
- **Load**: Sudden burst 10 to 100 VUs
- **Thresholds**: p95 < 5s, p99 < 10s, error_rate < 15%

## Quick Start

### Prerequisites
- Docker & Docker Compose
- All 19 engines running on their respective ports
- k6 installed locally (optional, for direct runs)

### Run All Tests (Docker Compose)
```bash
cd load-testing
docker-compose -f docker-compose.load.yml up --build
```

### Run Individual k6 Tests
```bash
# Smoke test
k6 run k6/smoke.js

# Load test
k6 run k6/load.js

# Stress test
k6 run k6/stress.js

# Spike test
k6 run k6/spike.js

# Soak test (1 hour)
k6 run k6/soak.js
```

### Run with run_all.sh
```bash
chmod +x run_all.sh
./run_all.sh                    # Run all tests
./run_all.sh --smoke-only       # Only smoke test
./run_all.sh --soak             # Include soak test
./run_all.sh --skip-checks      # Skip service checks
```

### Run Locust Tests
```bash
# Standalone
docker run --rm -v $(pwd)/locust:/locust locustio/locust \
  -f /locust/locustfile.py --headless -u 50 -r 5 --run-time 5m

# Distributed (master + workers)
docker-compose -f docker-compose.load.yml up locust-master locust-worker-1 locust-worker-2
```

## Reports

Reports are generated in `k6/reports/`:
- JSON summaries: `{test}-summary-{timestamp}.json`
- HTML reports: `{test}-{timestamp}.html`

## Grafana Dashboard

Access at http://localhost:3000 (admin/admin)
- Pre-configured InfluxDB datasource
- Load test dashboard: "aig Load Test Dashboard"

## Prometheus/Alertmanager

- Prometheus: http://localhost:9090
- Alertmanager: http://localhost:9093

## CI/CD Integration

```yaml
# GitHub Actions example
- name: Run Load Tests
  run: |
    cd load-testing
    ./run_all.sh --skip-checks
```

Exit codes:
- 0: All tests passed
- 1: One or more tests failed

## Configuration

### Environment Variables
```bash
# k6
K6_OUT=influxdb=http://influxdb:8086/k6
K6_WEB_DASHBOARD=true

# Locust
LOCUST_MODE=standalone|master|worker
LOCUST_MASTER_HOST=locust-master
LOCUST_WORKER_COUNT=4
```

### Customizing Engine Weights
Edit `ENGINE_WEIGHTS` in k6 scripts or `locustfile.py` to adjust traffic distribution.

## Troubleshooting

### Services Not Reachable
```bash
# Check all ports
for port in 5020 9200 9300 9400 9500 9600 9700 9800 9999 9998 9997 9850 9860 9870 9880 9890 9840 9830 9820; do
  nc -zv localhost $port
done
```

### High Error Rates
1. Check engine logs
2. Verify database connections
3. Check circuit breaker status
4. Review resource limits

### Performance Degradation
1. Run soak test to detect leaks
2. Check memory/CPU on engine hosts
3. Review database connection pools
4. Check for GC pauses

## Directory Structure

```
docker/load-testing/
├── k6/
│   ├── smoke.js       # Smoke test
│   ├── load.js        # Load test
│   ├── stress.js      # Stress test
│   ├── soak.js        # Soak test
│   ├── spike.js       # Spike test
│   └── reports/       # Generated reports
├── locust/
│   ├── locustfile.py  # Locust test scenarios
│   ├── requirements.txt
│   └── entrypoint.sh
├── grafana/
│   ├── datasources/
│   └── dashboards/
├── prometheus/
│   └── prometheus.yml
├── alertmanager/
│   └── alertmanager.yml
├── Dockerfile.k6
├── Dockerfile.locust
├── docker-compose.load.yml
├── run_all.sh
└── README.md
```