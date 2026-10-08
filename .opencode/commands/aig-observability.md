# /aig-observability - Stack completo (Prometheus, Grafana, Loki, Tempo)

Observabilidad auto-provisionada via Docker Compose.

## Servicios
- **Prometheus**: `config/prometheus/` + alerts.yml
- **Grafana**: dashboards auto (Tempo, Loki, Prometheus)
- **Loki**: logs agregados (puerto 3100)
- **Tempo**: traces distribuidos (puerto 3201, movido de 3200 para Hermes Dashboard)
- **Caddy**: ingress + TLS local (daniela.localhost, hermes.localhost)

## Dashboards clave
- **System**: CPU, RAM, disco, red por servicio
- **Daniela Core**: memoria nodos, empatía, latencia 50-dim
- **Hermes**: skills cognitivos, tiers memoria, hit-rate (puerto 3200 dashboard completo)
- **Swarm**: Raft leader, consenso latency, engine health
- **Android**: build time, APK size, test results
- **Business**: tenants activos, requests/min, error rate

## Alertas (config/prometheus/alerts.yml)
- `DanielaCoreDown` (port 9200)
- `HermesGatewayDown` (port 9300)
- `SwarmConsensusFailure` (port 8080)
- `HighErrorRate` (>5% 5min)
- `HighLatencyP99` (>2s)
- `DiskSpaceCritical` (<10%)

## Uso
```bash
# Stack observabilidad (5 servicios)
docker compose -f config/docker/docker-compose.observability.yml up -d

# Grafana: http://localhost:3000 (admin/admin)
# Prometheus: http://localhost:9090
# Loki: http://localhost:3100
# Tempo: http://localhost:3200

# Ver alerts
curl http://localhost:9090/api/v1/alerts
```