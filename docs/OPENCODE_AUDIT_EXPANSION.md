# OpenCode Configuration Audit & Expansion Plan

**Date**: 2026-10-05
**Status**: Post-wave5 (7 commits), gate GO
**Scope**: Global IDE compatibility (OpenCode, Claude Code, Codex, Cursor, Copilot)

---

## 1. Current State Audit

### 1.1 Skills (20 total)

| Category | Skills | Status |
|----------|--------|--------|
| **aig-native** (7) | `aig-android`, `aig-dedup`, `aig-deploy`, `aig-observability`, `aig-orchestrator`, `aig-triage`, `gate` | Core |
| **ECC Core** (13) | `agent-architecture-audit`, `agentic-engineering`, `blueprint`, `continuous-learning-v2`, `deployment-patterns`, `docker-patterns`, `eval-harness`, `intent-driven-development`, `orch-pipeline`, `production-audit`, `security-review`, `tdd-workflow`, `verification-loop` | Imported |

**Gaps**: No skills for:
- Android/Kotlin-specific patterns (Jetpack Compose, Gradle, Hilt)
- Swarm/Raft consensus operations
- Cross-engine gateway patterns
- Daniela OS memory/empathy orchestration
- Phone/Pixel/Termux runtime patterns
- Caddy ingress + local DNS
- Observability stack (Grafana/Loki/Tempo/Prometheus) provisioning
- Zero-cost CI/CD patterns (GitHub Actions free tier)

### 1.2 Agents (13 total)

| Agent | Role | Port | Coverage |
|-------|------|------|----------|
| `aig-orchestrator` | Epic decomposition to delegation | - | Yes |
| `aig-dedup` | Folder deduplication | - | Yes |
| `aig-deploy` | Docker compose + health gates | - | Yes |
| `aig-observability` | Dashboards, alerts, SLOs | - | Yes |
| `aig-android` | Kotlin + Compose + Gradle | - | Yes |
| `aig-flaky` | Flaky test detection | - | Yes |
| `aig-perf` | Performance optimization | - | Yes |
| `aig-security` | Security review | - | Yes |
| `daniela-core` | Memory (12,480 nodes), empathy 96%, 50-dim | 9200 | Yes |
| `hermes-gateway` | 10 cognitive skills, 3 memory tiers | 9300/3200 | Yes |
| `swarm-coordinator` | Raft consensus, 19 engines | 8080 | Yes |
| `phone-runtime` | Pixel + Termux, pairing | - | Yes |
| `gatekeeper` | Quality gate (pytest vs baseline) | - | Yes |

**Gaps**: No agents for:
- **Code Reviewer** (security + perf + style)
- **Test Engineer** (coverage gaps, Android instrumented)
- **Deploy Engineer** (Docker compose health gates)
- **Monitor** (Prometheus/Grafana/Loki/Tempo)
- **Android Lead** (Kotlin, Compose, Gradle optimization)
- **Data Engineer** (SQLite/PostgreSQL, migrations, RAG)
- **Frontend Engineer** (PWA, Termux API, WebView)

### 1.3 MCP Servers (3 configured)

| Server | Purpose | Status |
|--------|---------|--------|
| `filesystem` | Local repo access | Yes |
| `memory` | Cross-session memory | Yes |
| `github` | GitHub API (needs GITHUB_TOKEN) | Needs token |

**Missing MCP servers**:
- `sqlite` / `postgres` - Direct DB access for Daniela OS
- `docker` - Container orchestration
- `prometheus` / `grafana` - Observability queries
- `redis` - Cache/session management
- `android` / `adb` - Pixel device control

### 1.4 Commands (16)

| Command | Type | Agent |
|---------|------|-------|
| `aig-audit`, `aig-deploy`, `aig-android`, `aig-observability`, `gate` | Subtask | - |
| `orch-add-feature`, `orch-fix-defect`, `orch-build-mvp` | Agent | `aig-orchestrator` |
| `daniela-core`, `hermes`, `swarm`, `phone` | Agent | Respective |
| `sync`, `cost`, `instinct` | Template | - |

---

## 2. Expansion Plan

### 2.1 New Skills to Create (Priority Order)

| Skill | Description | Source |
|-------|-------------|--------|
| `aig-kotlin-compose` | Jetpack Compose patterns, Gradle 8.6, Hilt DI, Compose 1.5.8, Material 3 | aig-android |
| `aig-swarm-raft` | Raft consensus, leader election, cross-engine task distribution | swarm-coordinator |
| `aig-cross-engine` | Gateway patterns, service discovery, health checks | hermes-gateway |
| `aig-daniela-memory` | 12,480 nodes, empathy 96%, Episodic/Semantic/Procedural tiers | daniela-core |
| `aig-phone-runtime` | Pixel/Termux, pairing, offline-first sync, Termux API 30 endpoints | phone-runtime |
| `aig-caddy-ingress` | Local DNS (daniela.localhost, hermes.localhost), TLS, engine routes | Caddy config |
| `aig-observability-stack` | Grafana provisioning, Loki/Tempo/Prometheus, alerts, SLOs | aig-observability |
| `aig-zero-cost-ci` | GitHub Actions free tier, no GHCR/LFS/Codespaces, self-hosted runners | AGENTS.md |
| `aig-android-instrumented` | Espresso/UI Automator, connectedAndroidTest, Gradle managed devices | aig-android |
| `aig-daniela-jarvis` | PC properties, gods-eye-view, epic-pc | docker/epic-pc |
| `aig-sqlite-migrations` | Safe migrations, expand-contract, WAL mode, concurrent indexes | core/db |

### 2.2 New Agents to Create (Priority Order)

| Agent | Role | Triggers |
|-------|------|----------|
| `aig-code-reviewer` | Security + Performance + Style (ruff baseline) | PR review, /code-review |
| `aig-test-engineer` | Coverage gaps to pytest + Android instrumented | /test-coverage, /e2e-testing |
| `aig-deploy-engineer` | Docker compose to health gates (18 services) | /aig-deploy, /canary-watch |
| `aig-monitor` | Prometheus/Grafana/Loki/Tempo alerts | /aig-observability, /canary-watch |
| `aig-android-lead` | Kotlin, Compose, Gradle optimization | /aig-android, /orch-build-mvp android |
| `aig-data-engineer` | SQLite/PostgreSQL, migrations, RAG, vector DB | /orch-add-feature data |
| `aig-frontend-engineer` | PWA, Termux API, WebView, offline-first | /orch-add-feature phone |

### 2.3 New MCP Servers to Add

| Server | Config | Purpose |
|--------|--------|---------|
| `sqlite` | `@modelcontextprotocol/server-sqlite` | Direct daniela.db, auth.db, billing.db access |
| `postgres` | `@modelcontextprotocol/server-postgres` | Production PostgreSQL |
| `docker` | `@modelcontextprotocol/server-docker` | Container orchestration, health checks |
| `prometheus` | `@modelcontextprotocol/server-prometheus` | Metrics queries, alerting rules |
| `grafana` | `@modelcontextprotocol/server-grafana` | Dashboard provisioning, datasource management |
| `redis` | `@modelcontextprotocol/server-redis` | Cache, sessions, rate limiting |
| `adb` | Custom (Python) | Pixel device control, logcat, screencap |

### 2.4 Cross-IDE Configuration Files

Create configuration files for each IDE that reference the same `.opencode/` source of truth:

| IDE | Config File | Content |
|-----|-------------|---------|
| **Claude Code** | `~/.claude/CLAUDE.md` | Symlink to `.opencode/instructions/INSTRUCTIONS.md` + agent/skill refs |
| **Codex** | `.codex/config.toml` | Native multi-agent plugin config pointing to `.opencode/` |
| **Cursor** | `.cursor/rules/` | `.mdc` rules synced from `.opencode/skills/*/SKILL.md` |
| **VS Code / Copilot** | `.github/copilot-instructions.md` | Chat instructions referencing AGENTS.md |
| **Windsurf** | `.windsurf/` | Cascade rules from skills |
| **Zed** | `.zed/` | Agent configs from `.opencode/agents/` |

---

## 3. Implementation: Expanded `.opencode/opencode.json`

```json
{
  "$schema": "https://opencode.ai/config.json",
  "plugin": [
    "ecc-universal",
    "file:///C:/Users/Alejandro/.config/opencode/plugins/ecc-hooks.ts",
    "file:///C:/Users/Alejandro/.config/opencode/plugins/daniela_os_bridge.js"
  ],
  "instructions": [
    "AGENTS.md",
    ".opencode/instructions/INSTRUCTIONS.md"
  ],
  "skills": {
    "paths": [
      ".opencode/skills"
    ]
  },
  "model": "litellm/openrouter-free",
  "mcp": {
    "filesystem": {
      "type": "local",
      "command": ["cmd", "/c", "npx", "-y", "@modelcontextprotocol/server-filesystem", "C:\\Users\\Alejandro\\aig"],
      "enabled": true,
      "timeout": 30000
    },
    "memory": {
      "type": "local",
      "command": ["cmd", "/c", "npx", "-y", "@modelcontextprotocol/server-memory"],
      "enabled": true,
      "timeout": 30000
    },
    "github": {
      "type": "local",
      "command": ["cmd", "/c", "npx", "-y", "@modelcontextprotocol/server-github"],
      "enabled": true,
      "timeout": 30000,
      "env": { "GITHUB_PERSONAL_ACCESS_TOKEN": "${GITHUB_TOKEN}" }
    },
    "sqlite": {
      "type": "local",
      "command": ["cmd", "/c", "npx", "-y", "@modelcontextprotocol/server-sqlite", "data/daniela.db"],
      "enabled": true,
      "timeout": 30000
    },
    "postgres": {
      "type": "local",
      "command": ["cmd", "/c", "npx", "-y", "@modelcontextprotocol/server-postgres"],
      "enabled": true,
      "timeout": 30000,
      "env": { "POSTGRES_URL": "${DATABASE_URL}" }
    },
    "docker": {
      "type": "local",
      "command": ["cmd", "/c", "npx", "-y", "@modelcontextprotocol/server-docker"],
      "enabled": true,
      "timeout": 30000
    },
    "prometheus": {
      "type": "local",
      "command": ["cmd", "/c", "npx", "-y", "@modelcontextprotocol/server-prometheus", "http://localhost:9090"],
      "enabled": true,
      "timeout": 30000
    },
    "grafana": {
      "type": "local",
      "command": ["cmd", "/c", "npx", "-y", "@modelcontextprotocol/server-grafana", "http://localhost:3000"],
      "enabled": true,
      "timeout": 30000
    },
    "redis": {
      "type": "local",
      "command": ["cmd", "/c", "npx", "-y", "@modelcontextprotocol/server-redis", "redis://localhost:6379"],
      "enabled": true,
      "timeout": 30000
    }
  },
  "command": {
    "aig-audit": {
      "description": "Full monorepo audit - health checks, dependencies, security, performance",
      "template": "{file:commands/aig-audit.md}\n\n$ARGUMENTS",
      "subtask": true
    },
    "aig-deploy": {
      "description": "Deploy aig stack with health gates and rollback",
      "template": "{file:commands/aig-deploy.md}\n\n$ARGUMENTS",
      "subtask": true
    },
    "aig-android": {
      "description": "Android development commands - build, test, Pixel sync, deploy",
      "template": "{file:commands/aig-android.md}\n\n$ARGUMENTS",
      "subtask": true
    },
    "aig-observability": {
      "description": "Observability commands - dashboards, alerts, logs, traces, SLOs",
      "template": "{file:commands/aig-observability.md}\n\n$ARGUMENTS",
      "subtask": true
    },
    "gate": {
      "description": "Quality gate - suite contra la linea base, veredicto GO/NO-GO",
      "template": "{file:commands/gate.md}\n\n$ARGUMENTS",
      "subtask": true
    },
    "orch-add-feature": {
      "description": "Orchestrate adding a new feature end-to-end via orch-pipeline",
      "agent": "aig-orchestrator",
      "template": "/orch-add-feature $ARGUMENTS"
    },
    "orch-fix-defect": {
      "description": "Orchestrate fixing a bug via orch-pipeline",
      "agent": "aig-orchestrator",
      "template": "/orch-fix-defect $ARGUMENTS"
    },
    "orch-build-mvp": {
      "description": "Bootstrap MVP from spec via orch-pipeline",
      "agent": "aig-orchestrator",
      "template": "/orch-build-mvp $ARGUMENTS"
    },
    "daniela-core": {
      "description": "Daniela OS core operations - memory, empathy, orchestration",
      "agent": "daniela-core",
      "template": "Trabaja con Daniela Core (puerto 9200): $ARGUMENTS"
    },
    "hermes": {
      "description": "Hermes gateway operations - cognitive skills, memory tiers",
      "agent": "hermes-gateway",
      "template": "Trabaja con Hermes (puerto 9300): $ARGUMENTS"
    },
    "swarm": {
      "description": "Swarm intelligence - Raft consensus, cross-engine coordination",
      "agent": "swarm-coordinator",
      "template": "Coordinacion Swarm (puerto 8080): $ARGUMENTS"
    },
    "phone": {
      "description": "Daniela OS Phone - Pixel/Termux runtime, agents, pairing",
      "agent": "phone-runtime",
      "template": "Daniela OS Phone (daniela-os/phone/): $ARGUMENTS"
    },
    "sync": {
      "description": "Sync memory vault across agents (Claude, Codex, Hermes, OpenCode)",
      "template": "ecc memory sync && ecc memory handoff --from $ARGUMENTS"
    },
    "cost": {
      "description": "Cost tracking and budget report",
      "template": "/cost-report $ARGUMENTS"
    },
    "instinct": {
      "description": "Instinct status and evolution",
      "template": "/instinct-status && /evolve $ARGUMENTS"
    },
    "code-review": {
      "description": "Security + Performance + Style review",
      "agent": "aig-code-reviewer",
      "template": "Revisa el diff actual: $ARGUMENTS"
    },
    "test-coverage": {
      "description": "Coverage gaps to pytest + Android instrumented",
      "agent": "aig-test-engineer",
      "template": "Analiza cobertura y genera tests faltantes: $ARGUMENTS"
    },
    "e2e-testing": {
      "description": "Playwright E2E + Android instrumented tests",
      "agent": "aig-test-engineer",
      "template": "Ejecuta tests E2E: $ARGUMENTS"
    },
    "canary-watch": {
      "description": "Post-deploy verification + metrics watch",
      "agent": "aig-monitor",
      "template": "Verifica deploy y vigila metricas: $ARGUMENTS"
    },
    "db-migrate": {
      "description": "Safe SQLite/PostgreSQL migrations",
      "agent": "aig-data-engineer",
      "template": "Genera migracion: $ARGUMENTS"
    },
    "android-build": {
      "description": "Gradle build + instrumented tests",
      "agent": "aig-android-lead",
      "template": "Build Android: $ARGUMENTS"
    },
    "pwa-sync": {
      "description": "PWA + Termux offline-first sync",
      "agent": "aig-frontend-engineer",
      "template": "Sincroniza PWA/Termux: $ARGUMENTS"
    }
  },
  "agent": {
    "default": { "model": "litellm/openrouter-free" }
  }
}
```

---

## 4. Implementation Steps

### Phase 1: Core Expansion (Week 1)
1. Create 10 new skills in `.opencode/skills/`
2. Create 7 new agents in `.opencode/agents/`
3. Add 7 MCP servers to `.opencode/opencode.json`
4. Add 7 new commands to `.opencode/opencode.json`

### Phase 2: Cross-IDE Sync (Week 2)
1. Generate `~/.claude/CLAUDE.md` from AGENTS.md + INSTRUCTIONS.md
2. Create `.codex/config.toml` for Codex native plugin
3. Create `.cursor/rules/*.mdc` from skills
4. Create `.github/copilot-instructions.md` for VS Code
5. Create `.windsurf/` configs

### Phase 3: Advanced Features (Week 3)
1. Custom `adb` MCP server for Pixel control
2. `continuous-learning-v2` hooks for instinct capture
3. `verification-loop` 6-phase gate integration
4. Cross-IDE memory vault sync (`ecc memory sync`)

---

## 5. Validation Checklist

| Check | Command | Expected |
|-------|---------|----------|
| All skills load | `opencode skill list` | 30 skills |
| All agents load | `opencode agent list` | 20 agents |
| MCP servers connect | `opencode mcp list` | 10 servers |
| Commands work | `opencode run <cmd>` | All 23 commands |
| Cross-IDE sync | `ecc memory sync` | No errors |
| Gate passes | `opencode run gate` | GO |

---

## 6. Risk Mitigation

| Risk | Mitigation |
|------|------------|
| MCP server conflicts | Namespace each server, use different ports |
| Skill/agent name collisions | Prefix aig- for native, ecc- for ECC |
| Context window overflow | Use `context-budget` skill, strategic compact |
| Token cost (openrouter-free) | Route simple tasks to gemma-2-9b, complex to nemotron-3-ultra |
| Zero-cost mandate | Self-hosted runners, no GHCR/LFS/Codespaces |

---

## 7. Next Actions

1. **Approve this plan** - I'll implement Phase 1 (skills + agents + MCP + commands)
2. **Review new skill specs** - I'll create each `.opencode/skills/<name>/SKILL.md`
3. **Review new agent specs** - I'll create each `.opencode/agents/<name>.yaml`
4. **Deploy cross-IDE configs** - Generate configs for all 6 IDEs