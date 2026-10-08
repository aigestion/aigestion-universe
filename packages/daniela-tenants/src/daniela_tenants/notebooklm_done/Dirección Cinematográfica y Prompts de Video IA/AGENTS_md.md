### aig Monorepo - Agent Instructions

#### Project Identity

**Autonomous AI Service Management & Edge Orchestrator**

* **Core** : Daniela AI (12,480 memory nodes, 96% empathy, Coherent Level 4)
* **Gateway** : Hermes (10 cognitive skills, 3 memory tiers: Episodic/Semantic/Procedural)
* **19 Federated Engines** : Core, Data & Security, Performance, Experience, Automation
* **Mobile** : Android Kotlin + Jetpack Compose (Min SDK 26, Target SDK 36)
* **Orchestration** : Swarm Intelligence + Raft Consensus + Cross-Engine Gateway

#### Architecture Rules

* **Monorepo** : config/docker-compose.yml (23 services), config/docker-compose.observability.yml, config/docker-compose.prod.yml (27), config/docker-compose.slim.yml (4)
* **Python** : 3.11 + uv, pyproject.toml with [dev] extras
* **Android** : Kotlin 2.2.10, Gradle 9.3.1, AGP 9.1.1, Compose Material 3
* **Zero-Cost Mandate** : No paid GitHub tiers, no LFS, no GHCR, no Codespaces
* **Tests** : pytest tests/ -m "not network and not android" -q --tb=no -p no:cacheprovider + ruff (ignore BLE001, S110, UP017)
* **Lint Baseline** : .quality-baseline/ruff-count.txt (0 errors)

#### Core Services (13/13 Healthy)

daniela, hermes, infra, agent, security, perf, orchestrator, caddy, prometheus, grafana, redis, gods-eye, daniela

#### Key Endpoints

* **Caddy** : api.localhost → handles /gods-eye/* proxy to daniela:9200
* **Daniela Core** : Port 9200 (Omnipresente 50 dimensions)
* **Hermes** : Port 9900 (Cross-Engine Orchestrator)
* **Swarm** : Port 8080 (Raft Consensus)
* **Grafana** : Dashboards (Tempo, Loki, Prometheus auto-provisioned)
* **Prometheus** : Alerts at config/prometheus/alerts.yml

#### Android App Structure

* android_app/mobile-app/ - PWA frontend
* android_app/pixel/ - Pixel Python services (30 endpoints via Termux API Gateway)
* connectors/pairing.py - PC↔Pixel challenge-response pairing
* connectors/termux_api_gateway.py - 30 endpoints for Pixel integration

#### Agent Workflows

1. **Orchestrator** → Decompose epic → Delegate to specialized agents
2. **Code Reviewer** → Security + Performance + Style (ruff baseline)
3. **Test Engineer** → Coverage gaps → pytest + Android instrumented
4. **Deploy Engineer** → Docker compose → Health gate (13 services)
5. **Monitor** → Prometheus/Grafana/Loki/Tempo alerts
6. **Android Lead** → Kotlin, Compose, Gradle optimization

#### ECC Skills to Use

* orch-pipeline, orch-add-feature, orch-build-mvp, orch-fix-defect
* security-review, codehealth-mcp, security-scan
* tdd-workflow, e2e-testing, test-coverage
* deployment-patterns, kubernetes-patterns, docker-patterns
* continuous-learning-v2, strategic-compact, context-budget
* production-audit, dashboard-builder, canary-watch

#### Daily Commands

```
/plan "Task description"
/orch-add-feature "engine/feature-name"
/orch-build-mvp "android/module"
/tdd "test-improvement"
/security-scan
/cost-report
/instinct-status
/evolve
```

#### Memory Vault

```
ecc memory init --scope project
ecc memory handoff --from orchestrator --target code-reviewer --title "PR Review" --body-file ./handoff.md
ecc memory search "query" --target-harness opencode
```

#### Cross-Tool Config

* **OpenCode** : .opencode/ (primary, local control)
* **Claude Code** : ~/.claude/ + plugin (deep reasoning)
* **Codex** : .codex/ + plugin (native multi-agent)
* **Cursor** : .cursor/ (IDE-integrated)
* **GitHub Copilot** : .github/copilot-instructions.md (VS Code chat)