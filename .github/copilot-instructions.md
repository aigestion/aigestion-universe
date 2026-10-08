# GitHub Copilot Instructions - aig Monorepo

## Project Overview
**Autonomous AI Service Management & Edge Orchestrator**
- **Core**: Daniela AI (12,480 memory nodes, 96% empathy, Coherent Level 4)
- **Gateway**: Hermes (10 cognitive skills, 3 memory tiers: Episodic/Semantic/Procedural)
- **19 Federated Engines**: Core, Data & Security, Performance, Experience, Automation
- **Mobile**: Android Kotlin + Jetpack Compose (Min SDK 24, Target SDK 34)
- **Orchestration**: Swarm Intelligence + Raft Consensus + Cross-Engine Gateway

## Key Files to Reference
- `AGENTS.md` - Architecture, services, ports, agent workflows
- `.opencode/instructions/INSTRUCTIONS.md` - OpenCode project instructions
- `docs/ESTANDARES-ORGANIZACION.md` - Folder/naming standards
- `docs/ADR-*.md` - Architectural decisions

## Coding Standards

### Python (3.11 + uv)
- Ruff baseline: 0/0 (`python scripts/utils/ratchet_ruff.py`)
- Type hints required
- Snake_case for files/functions
- No hardcoded secrets (use `${env:VAR}` placeholders)

### Android (Kotlin + Jetpack Compose)
- Kotlin 1.9.22, Gradle 8.6, AGP 8.3.0
- Compose 1.5.8, Material 3
- Package: `com.aigestion.mobile`
- Min SDK 24, Target SDK 34

### Naming Rules (ESTANDARES-ORGANIZACION.md)
| Term | Meaning |
|------|---------|
| `android` | Platform (connectors/scripts/marker) |
| `android-app` | App only |
| `pixel` | Hardware (Pixel 8a) |
| `termux` | Runtime on phone |
| `mobile-app` | PWA tree (36-byte pointer in root) |

## Architecture Rules

### Ports
- **Daniela Core**: 9200
- **Hermes**: 9300 (API) / 3200 (Dashboard)
- **Swarm**: 8080 (Raft)
- **Orchestrator**: 9900
- **Engines**: 9820-9920 (10 engines)

### Docker Compose Stacks
- `docker-compose.yml` (14 services) - legacy
- `docker-compose.prod.yml` (23) - production
- `docker-compose.slim.yml` (10) - minimal
- `docker-compose.observability.yml` (5) - Grafana/Loki/Tempo

## Quality Gates (Non-negotiable)
1. **Gate before commit**: `uv run pytest tests/ -q --tb=no -p no:cacheprovider --continue-on-collection-errors` vs baseline by test NAME
2. **Ruff ratchet**: `python scripts/utils/ratchet_ruff.py` (ceiling 0)
3. **Never push** - owner handles push/key rotation
4. **Never commit secrets** - `.env` only, `${env:...}` placeholders in config

## Agent Workflows
1. **Orchestrator** → Decompose epic → Delegate
2. **Code Reviewer** → Security + Performance + Style
3. **Test Engineer** → Coverage gaps → pytest + Android instrumented
4. **Deploy Engineer** → Docker compose → Health gate (18 services)
5. **Monitor** → Prometheus/Grafana/Loki/Tempo alerts
6. **Android Lead** → Kotlin, Compose, Gradle optimization

## Common Patterns

### Database Access
```python
# Use canonical paths
from core.config.paths import DANIELA_DB, AUTH_DB

# Env vars override
# DANIELA_AUTH_DB=/custom/path/auth.db
```

### LLM Routing
```python
# Core router (v3 solo gratis)
from core.model_router import EnrutadorModelos, get_instance

router = get_instance()
result = router.responder("prompt", max_tokens=512)
```

### Cross-Device Sync
```python
# PC <-> Phone
from core.cross_device_sync import sync_bp

POST /api/sync/push {"device": "pc", "key": "brain", "value": {...}}
GET /api/sync/pull?device=phone&since=timestamp
```

## Security
- No hardcoded keys in code/config
- `.env` for local secrets (git-ignored)
- `${env:VAR}` placeholders in docker-compose
- Rotate any key that reached git history

## Zero-Cost Mandate
- No paid GitHub tiers
- No LFS, no GHCR, no Codespaces
- Self-hosted runners for Android/Docker
- GitHub Actions free tier (2000 min/mo)