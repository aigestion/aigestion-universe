<!-- BEGIN:turborepo-agent-rules -->

# This is NOT the Turborepo you know

Turborepo configuration, task behavior, and CLI commands can vary between installed versions and may differ from your training data. Resolve the `turbo` package from this file's directory or relevant workspace; in monorepos, it may not be visible from the repository root. For example, run `node -p "require.resolve('turbo/package.json')"` from a workspace that depends on `turbo`.

Read `docs/README.md` inside that installed package first, then read the relevant pages from its `docs/` directory before changing Turborepo configuration or commands. Heed deprecation notices. These bundled docs match the installed package version and are available without network access.

This block is written and re-added by `turbo` before repository-scoped commands when an AI agent is detected. In the Turborepo source repository, its template is defined in `crates/turborepo-cli/src/cli/agent_guidance.rs`. Removing the managed block while updates are enabled means a later qualifying invocation will add it again. Set `"agentGuidance": false` in the root `turbo.json` or `turbo.jsonc` to opt out; this does not remove an existing block. Keep the block committed with your work to avoid an uncommitted change on the next agent invocation.
<!-- END:turborepo-agent-rules -->


---

# LEGACY CONTENT (merged from aig)

# aig Monorepo - Agent Instructions

## Project Identity
**Autonomous AI Service Management & Edge Orchestrator**
- **Core**: Daniela AI (12,480 memory nodes, 96% empathy, Coherent Level 4)
- **Gateway**: Hermes (10 cognitive skills, 3 memory tiers: Episodic/Semantic/Procedural)
- **19 Federated Engines**: Core, Data & Security, Performance, Experience, Automation
- **Mobile**: Android Kotlin + Jetpack Compose (Min SDK 24, Target SDK 34)
- **Orchestration**: Swarm Intelligence + Raft Consensus + Cross-Engine Gateway

## Architecture Rules
- **Monorepo**: `config/docker/docker-compose.yml` (14 services), `config/docker/docker-compose.prod.yml` (23), `config/docker/docker-compose.slim.yml` (10), `config/docker/docker-compose.observability.yml` (5)
- **Python**: 3.11 + uv, `pyproject.toml` with `[dev]` extras
- **Android**: Kotlin 1.9.22, Gradle 8.6, AGP 8.3.0, Compose 1.5.8, Compose Material 3
- **Zero-Cost Mandate**: No paid GitHub tiers, no LFS, no GHCR, no Codespaces
- **Tests**: `pytest tests/ -q --tb=no -p no:cacheprovider` + ruff (ignore BLE001, S110, UP017)
- **Lint Baseline**: `.quality-baseline/ruff-count.txt` (0 desde el 2026-10-04, medido sin flags via `scripts/utils/ratchet_ruff.py`; no subir sin justificacion)
- **Nombres movil**: `android` = plataforma (connectors/scripts/marker), `android-app` = solo la app, `pixel` = hardware concreto, `termux` = runtime en el movil. No unificar (regla en `docs/ESTANDARES-ORGANIZACION.md`)

## Core Services (18 vigilados por `scripts/core/ci_health_gate.py`)
daniela:9200, hermes:9300 (API) / 3200 (Dashboard), infra_opt:9700, agent_mobile:9800, security:9999 (sin codigo, en profile), perf:9998, gateway:8080, orchestrator:9900

## Daniela OS Components
- **Propiedades de Daniela OS en el PC**: `docker/epic-pc/`, `daniela-os/daniela-jarvis/`
- **Herramientas de Daniela OS**: `gev/` (gods-eye-view), `ide/hermes/` (hermes)

## Key Endpoints
- **Caddy**: `daniela.localhost` → 9200, `hermes.localhost` → 9300
- **Daniela Core**: Port 9200 (Daniela 50 dimensions)
- **Hermes**: Port 9300 (API) / 3200 (Dashboard completo Windows Desktop) (`ide/hermes/`)
- **Cross-Engine Orchestrator**: Port 9900 (`engine/cross_engine/`)
- **Swarm**: Port 8080 (Raft Consensus)
- **Grafana**: Dashboards (Tempo, Loki, Prometheus auto-provisioned)
- **Prometheus**: Alerts at `config/prometheus/alerts.yml`

## Android App Structure
- `frontend/apps/android-app/mobile-app/` - Árbol único de cliente (en raíz `mobile-app` hay un fichero puntero de 36 bytes con el path, no un symlink): PWA frontend + servicios edge Python (`services/`, `bridges/`, `core/`, `api/`)
- `frontend/apps/android-app/mobile-app/api/termux_api_gateway.py` - Termux API Gateway (30 endpoints, incluye `/api/pair/challenge`)
- `daniela-os/android-app/` - App Android nativa (Kotlin + Jetpack Compose, Gradle, paquete `com.aigestion.mobile`)
- `skills/connectors/android/pairing.py` - PC↔Pixel challenge-response pairing

## Agent Workflows
1. **Orchestrator** → Decompose epic → Delegate to specialized agents
2. **Code Reviewer** → Security + Performance + Style (ruff baseline)
3. **Test Engineer** → Coverage gaps → pytest + Android instrumented
4. **Deploy Engineer** → Docker compose → Health gate (18 services)
5. **Monitor** → Prometheus/Grafana/Loki/Tempo alerts
6. **Android Lead** → Kotlin, Compose, Gradle optimization

## ECC Skills to Use
- `orch-pipeline`, `orch-add-feature`, `orch-build-mvp`, `orch-fix-defect`
- `security-review`, `codehealth-mcp`, `security-scan`
- `tdd-workflow`, `e2e-testing`, `test-coverage`
- `deployment-patterns`, `kubernetes-patterns`, `docker-patterns`
- `continuous-learning-v2`, `strategic-compact`, `context-budget`
- `production-audit`, `dashboard-builder`, `canary-watch`

## Daily Commands
```bash
/plan "Task description"
/orch-add-feature "engine/feature-name"
/orch-build-mvp "android/module"
/tdd "test-improvement"
/security-scan
/cost-report
/instinct-status
/evolve
```

## Memory Vault
```bash
ecc memory init --scope project
ecc memory handoff --from orchestrator --target code-reviewer --title "PR Review" --body-file ./handoff.md
ecc memory search "query" --target-harness opencode
```

## Cross-Tool Config
- **OpenCode**: `.opencode/` (primary, local control)
- **Claude Code**: `~/.claude/` + plugin (deep reasoning)
- **Codex**: `.codex/` + plugin (native multi-agent) — no configurado
- **Cursor**: `.cursor/` (IDE-integrated) — no configurado
- **GitHub Copilot**: `.github/copilot-instructions.md` (VS Code chat) — no configurado

