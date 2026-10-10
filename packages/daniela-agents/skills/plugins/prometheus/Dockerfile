FROM prom/prometheus:latest

# Build context is the REPO ROOT. `prometheus.prod.yml` is the full-engine
# scrape config (matches docker-compose.prod.yml service names/ports).
COPY packages/daniela-agents/skills/plugins/prometheus/prometheus.prod.yml /etc/prometheus/prometheus.yml
COPY packages/daniela-agents/skills/plugins/prometheus/alerts.yml /etc/prometheus/alerts.yml

EXPOSE 9090
