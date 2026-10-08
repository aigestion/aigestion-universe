ECC integration complete for aig monorepo.

#### Project: aig (aig/AIG)

Autonomous AI Service Management & Edge Orchestrator

#### Architecture

* 19 Federated Engines (Core, Data, Perf, UX, Security, Automation)
* Daniela AI Core (50 Omnipresente dimensions, 12,480 memory nodes, 96% empathy)
* Hermes Gateway (10 cognitive skills, 3 memory tiers)
* Swarm Intelligence + Raft Consensus + Cross-Engine Orchestrator
* Android Edge Node (Kotlin + Compose, Pixel integration via Termux)

#### ECC Integration Status

✅ Submodule added: ECC/ (affaan-m/ECC) ✅ Global OpenCode install: ~/.config/opencode/ (full profile) ✅ Project config: .opencode/opencode.json with ecc-universal plugin ✅ AGENTS.md: Universal cross-tool instructions at root ✅ 4 aig-specific skills created:

* aig-orchestrator (master orchestration)
* aig-deploy (Docker compose + health gates)
* aig-android (Kotlin/Compose + Pixel + Termux)
* aig-observability (Prometheus/Grafana/Loki/Tempo)
  ✅ Hooks configured:
* preToolUse: auto-format (ruff/prettier), typecheck, security scan
* postToolUse: related tests, doc updates, cost tracking
* sessionStart: git status, memory vault, context budget
* sessionEnd: session summary, cost estimate, handoff reminder
  ✅ Commands added:
* aig-audit (full monorepo audit)
* aig-deploy (health-gated deploy)
* aig-android (build/test/Pixel/deploy)
* aig-observability (dashboards/metrics/logs/traces)

#### Key Files

* AGENTS.md: Universal agent instructions
* .opencode/opencode.json: Plugin + hooks config
* .opencode/hooks/: pre/post tool, session start/end
* .opencode/skills/aig-*: 4 custom skills
* .opencode/commands/aig-*: 4 custom commands
* ECC/: Submodule (affaan-m/ECC)

#### Session 2026-09-29 - COMMITTED & PUSHED (49df7ca -> origin/main)

All work below is committed and pushed. Safe to git pull from mobile.

##### Working NOW (verified live)

* LiteLLM gateway :4000 (auth sk-aig-master-key) -> local deepseek-coder-1b (~6s, ES ok)
* aig-ml sidecar :9810 (24 routes, 0 failed) + Qdrant :6333
* RAG end-to-end verified: add -> retrieve (0.40) -> synthesize
* LangGraph orchestrator compiles, status endpoint returns found
* mem0 manager active; Daniela 473 routes 0 failed; Grafana/Prometheus healthy

##### Stack (all healthy unless noted)

daniela:9200, hermes:9300, litellm:4000 (+postgres), ml:9810, qdrant:6333, grafana:3000, prometheus:9090, loki:3100, tempo:3200, pyroscope:4040 NOTE: litellm/pyroscope show "(unhealthy)" = cosmetic (no curl in minimal images). APIs respond.

##### Pending (needs user action - keys/accounts)

1. Groq org restricted -> contact Groq support
2. Together key invalid (CXJmJVxJnGi9C8uVWaTjn rejected) -> regenerate at api.together.ai
3. DeepInfra needs balance (402) -> add credits
4. OpenRouter free slugs 404 -> check current free model IDs
5. LANGFUSE_PUBLIC_KEY/SECRET_KEY -> add to .env to close observability loop
6. GitHub Actions platform bug (rename) -> support ticket; workaround ubuntu-latest active

##### Next dev tasks

1. Wyoming binaries (whisper-cli, piper) install + voice loop test
2. Ingest Daniela memory nodes into RAG: POST /api/rag/ingest-memory (ml:9810)
3. Langfuse keys + verify one traced LLM call
4. Temporal worker test with proper module file

##### Mobile (Termux) quick commands

```
cd ~/aig && git pull origin main
# health
curl -s http://MINIPC_IP:9200/api/status
curl -s http://MINIPC_IP:9810/api/status
curl -s -H "Authorization: Bearer sk-aig-master-key" http://MINIPC_IP:4000/v1/models
# chat via gateway
curl -H "Authorization: Bearer sk-aig-master-key" -H "Content-Type: application/json" \
  -d '{"model":"deepseek-coder-1b","messages":[{"role":"user","content":"hola"}]}' \
  http://MINIPC_IP:4000/v1/chat/completions
# RAG query
curl -X POST -H "Content-Type: application/json" \
  -d '{"question":"Que modelos prefiere Daniela?"}' http://MINIPC_IP:9810/api/rag/query
```

Replace MINIPC_IP with Tailscale IP (100.98.235.124) when off-LAN. Secrets (.env) are git-ignored: copy .env to phone separately, never commit.

#### Zero-Cost Constraints

* No paid GitHub tiers
* No LFS, no GHCR, no Codespaces
* GitHub Actions currently broken (repo rename bug - platform issue)
* Use GitHub-hosted runners (free tier) for CI

#### Memory Vault

Project scope initialized at: C:\Users\Alejandro.ecc\memory\project