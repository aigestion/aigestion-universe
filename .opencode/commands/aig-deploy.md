# /aig-deploy - Deploy stack aig con health gates y rollback

Despliega stack Docker Compose (14/23/10/5 servicios según perfil) con gates.

## Perfiles
- `slim` (10): `docker compose -f config/docker/docker-compose.slim.yml up -d`
- `core` (14): `docker compose -f config/docker/docker-compose.yml up -d`
- `prod` (23): `docker compose -f config/docker/docker-compose.prod.yml up -d`
- `observability` (5): `docker compose -f config/docker/docker-compose.observability.yml up -d`

## Health Gate (ci_health_gate.py)
18 servicios vigilados:
- daniela:9200, hermes:9300, infra_opt:9700, agent_mobile:9800
- security:9999, perf:9998, gateway:8080, orchestrator:9900
- intel/auto/data/secure/devtools/ecosystem/ux/scale_engine
- chaos_engine, brand_studio

## Rollback automático
Si health gate falla en 3 checks consecutivos (30s c/u):
```bash
docker compose -f <profile> down
docker compose -f <profile> up -d  # versión anterior (tag previo)
```

## Caddy routes (solo stack prod)
- `daniela.localhost` → 9200
- `hermes.localhost` → 9300
- 14 rutas engines (intel, auto, data, secure, devtools, ecosystem, ux, scale, chaos, brand, etc.)

## Uso
```bash
/aig-deploy core      # deploy core (14 servicios)
/aig-deploy prod      # deploy prod (23 servicios)
/aig-deploy rollback  # rollback a versión anterior
/aig-deploy status    # health check all 18
```