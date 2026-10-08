### ECC Epic Plan: aig Monorepo Optimization

#### Project Context

* **Repo** : aig/AIG (renamed from aig-MONOREPO)
* **Stack** : Python/Kotlin/Android, Docker, 23+ microservices, observability stack
* **Current Issues** : GitHub Actions broken (repo rename), fragmented configs, no unified agent workflow

---

#### Phase 1: ECC Integration & Setup (Week 1)

##### 1.1 Project-Level ECC Config

```
# Add ECC plugin to project opencode config
cat > .opencode/opencode.json << 'EOF'
{
  "plugin": ["ecc-universal"],
  "$schema": "https://opencode.ai/config.json"
}
EOF
```

##### 1.2 AGENTS.md at Root (Universal Cross-Tool)

```
# aig Monorepo - Agent Instructions

## Project Identity
Autonomous AI Service Management & Edge Orchestrator
- **Core**: Daniela AI (12,480 memory nodes, 96% empathy)
- **Gateway**: Hermes (10 cognitive skills, 3 memory tiers)
- **19 Federated Engines**: Core, Data, Perf, UX, Security, Automation
- **Mobile**: Android Kotlin + Jetpack Compose (Min SDK 26)

## Architecture Rules
- Monorepo with `config/docker-compose.yml` (23 services)
- Python 3.11 + uv, Kotlin 2.2.10 + Gradle 9.3.1
- Zero-cost mandate: No paid GitHub tiers, no LFS, no GHCR
- Tests: pytest + ruff (BLE001, S110, UP017 ignored)
- Android: AGP 9.1.1, Min SDK 26, Target SDK 36

## Agent Workflows
1. **Orchestrator** → Decompose epic → Delegate to specialized agents
2. **Code Reviewer** → Security + Performance + Style (ruff baseline)
3. **Test Generator** → Coverage gaps → pytest + Android instrumented
4. **Deploy Manager** → Docker compose → Health gate (13 services)
5. **Monitor** → Prometheus/Grafana/Loki/Tempo alerts
```

##### 1.3 ECC Skills for aig

```
# Install aig-specific skills
opencode skill create aig-orchestrator
opencode skill create aig-deploy
opencode skill create aig-android
opencode skill create aig-observability
```

---

#### Phase 2: Agent Specialization (Week 2)

##### 2.1 Core Agents (.opencode/agents/)

| Agent | Purpose | ECC Skill |
| --- | --- | --- |
| orchestrator | Epic decomposition, task delegation | orch-pipeline |
| code-reviewer | Security, perf, style gates | security-review, codehealth-mcp |
| test-engineer | Coverage, pytest, Android tests | tdd-workflow, e2e-testing |
| deploy-engineer | Docker, health gates, rollback | deployment-patterns, kubernetes-patterns |
| android-lead | Kotlin, Compose, Gradle | android-patterns (custom) |
| observability | Prometheus, Grafana, Loki, Tempo | production-audit, dashboard-builder |

##### 2.2 Hook Automation (.opencode/hooks/)

```
{
  "preToolUse": ["auto-format", "typecheck", "security-scan"],
  "postToolUse": ["test-related", "update-docs"],
  "sessionStart": ["context-budget", "load-memory"],
  "sessionEnd": ["save-session", "cost-report"]
}
```

---

#### Phase 3: CI/CD & Automation (Week 3)

##### 3.1 GitHub Actions Fix (Repo Rename Issue)

```
# .github/workflows/ci.yml - Use GitHub-hosted runners only
jobs:
  prepare:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Upload source
        uses: actions/upload-artifact@v4
        with:
          name: source-code
          path: "**/*"
          retention-days: 1
  
  test:
    runs-on: ubuntu-latest
    needs: prepare
    steps:
      - uses: actions/download-artifact@v4
        with: { name: source-code, path: . }
      # ... pytest, ruff, Android
```

##### 3.2 ECC Commands for Daily Work

```
/plan "Add new engine to monorepo"
/orch-add-feature "engine/new-feature"
/orch-build-mvp "android/payment-module"
/tdd "test-coverage-improvement"
/security-scan
/cost-report
```

---

#### Phase 4: Advanced Optimization (Week 4+)

##### 4.1 Memory Vault Integration

```
# Initialize project memory
ecc memory init --scope project

# Handoff between agents
ecc memory handoff --from orchestrator --target code-reviewer \
  --title "Review PR #42: New payment engine" \
  --body-file ./handoff.md

# Recall context
ecc memory search "payment engine" --target-harness opencode
```

##### 4.2 Continuous Learning v2

```
/instinct-status        # Show learned patterns
/evolve                 # Cluster instincts into skills
/instinct-export        # Share with team
```

##### 4.3 Token Optimization

```
// ~/.claude/settings.json or project .opencode/
{
  "model": "sonnet",
  "env": {
    "MAX_THINKING_TOKENS": "10000",
    "CLAUDE_AUTOCOMPACT_PCT_OVERRIDE": "50",
    "CLAUDE_CODE_SUBAGENT_MODEL": "haiku"
  }
}
```

##### 4.4 Multi-Harness Strategy

| Harness | Config | Use Case |
| --- | --- | --- |
| **OpenCode** | .opencode/ | Primary (local, full control) |
| **Claude Code** | ~/.claude/ + plugin | Deep reasoning, architecture |
| **Codex** | .codex/ + plugin | Native multi-agent, sandbox |
| **Cursor** | .cursor/ | IDE-integrated, rules/agents |
| **GitHub Copilot** | .github/copilot-instructions.md | VS Code chat, prompts |

---

#### Epic Ideas for aig

##### 🏗️ Architecture Epics

1. **Unified Engine Registry** - Auto-discover 19 engines via ECC skill
2. **Cross-Engine Orchestration** - Hermes + Swarm + Raft consensus
3. **Memory Semantic Vault** - Vector search across 12,480 nodes
4. **Mobile Edge Sync** - Android ↔ PC challenge-response pairing

##### 🔧 DevOps Epics

5. **Zero-Downtime Deploy** - Blue/green with health gates
6. **Cost-Aware LLM Pipeline** - Route to haiku/sonnet/opus by task
7. **Autonomous Rollback** - Metrics-driven (p95 > 500ms → rollback)
8. **Supply Chain Security** - AgentShield + SBOM + sigstore

##### 📱 Android Epics

9. **Offline-First Sync** - Sovereign offline node + conflict resolution
10. **Battery-Aware Scheduling** - Adaptive saver + predictive preload
11. **PWA + Native Bridge** - Shared Kotlin/JS logic via Compose Multiplatform

##### 🧠 AI/ML Epics

12. **Daniela Consciousness v5** - 50 dimensions across 5 domains
13. **Skill Auto-Generation** - From git history via /skill-create
14. **Continuous Evaluation** - Batch + streaming eval for agents

---

#### Quick Wins (This Week)

```
# 1. Fix GitHub Actions (repo rename bug)
gh api -X PATCH /repos/aig/AIG -F name=AIG

# 2. Add ECC to project
cat > .opencode/opencode.json << 'EOF'
{"plugin": ["ecc-universal"]}
EOF

# 3. Create AGENTS.md
# (see Phase 1.2 above)

# 4. Run first ECC commands
opencode
/plan "Audit monorepo structure and suggest consolidation"
/skill-create --instincts
/security-scan

# 5. Configure hooks
cat > .opencode/hooks.json << 'EOF'
{
  "preToolUse": [".opencode/hooks/pre-tool-use.js"],
  "postToolUse": [".opencode/hooks/post-tool-use.js"]
}
EOF
```

---

#### Success Metrics

| Metric | Target | ECC Tool |
| --- | --- | --- |
| Test coverage | >90% | /tdd, /test-coverage |
| Deploy frequency | Daily | /orch-build-mvp, /deploy |
| MTTR | <15min | /orch-fix-defect, /security-scan |
| Token cost/session | <$0.50 | /cost-report, sonnet/haiku routing |
| Agent autonomy | 80% tasks | /instinct-status, /evolve |
| Android build time | <5min | Gradle cache + /orch-build-mvp |

---

#### Next Steps

1. **Run** : opencode from repo root → /plan "Full monorepo audit"
2. **Create** : aig-specific skills in .opencode/skills/
3. **Configure** : MCP servers (GitHub, Context7, Memory, Playwright)
4. **Automate** : GitHub Actions with artifact-based checkout
5. **Scale** : Add Codex/Cursor configs for team members