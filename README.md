# aigestion.net — Autonomous AI Service Management & Edge Orchestrator

Daniela OS: your personal AI, renamed by you. Runs on phone, desktop, server.
19 federated engines, neural core (12,480 memory nodes, 96% empathy, Coherent Level 4),
swarm intelligence with Raft consensus, zero cloud cost — your infrastructure.

> **Status:** early alpha · MIT license · public repos

---

## Why

- **One gateway, 19 engines.** Cross-engine orchestration routes any task to the right engine in <30 ms.
- **Edge native.** Runs on your Pixel, your PC, your k3s cluster. Your data never leaves your metal.
- **Zero cloud cost.** Local-first. BYOK with zero markup — we never touch your tokens.
- **Privacy first.** FIPS 140-3 aligned AES-256-GCM, zero-knowledge, post-quantum hybrid readiness.

## Architecture

```
aigestion-universe/
├── apps/                     # Deployable applications
│   ├── landing/              # aigestion.net marketing site (Next.js + React Three Fiber)
│   ├── daniela-shell/        # Neural Shell — primary UI (Next.js + R3F, port 8083)
│   ├── daniela-desktop/      # Tauri 2.0 Windows/macOS desktop wrapper
│   ├── android-app/          # Native Android (Kotlin + Jetpack Compose)
│   ├── mobile-pwa/           # PWA + Termux edge services (30 endpoints)
│   ├── daniela-embodiment/   # Robotics (ROS 2 + MuJoCo)
│   ├── daniela-research/     # Research environments
│   ├── daniela-simulation/   # Simulation worlds
│   └── daniela-tools-gateway/# BYOK tool/MCP unification
├── packages/                 # Shared libraries
│   ├── daniela-core/         # Python core: brain, memory, orchestrator, life, security
│   ├── daniela-grpc/         # gRPC contracts
│   ├── daniela-obsidian/     # Obsidian vault sync
│   ├── daniela-sdk/          # Public SDK
│   ├── three-daniela/        # 3D/React Three Fiber components
│   └── ui/                   # Shared UI kit
├── configs/                  # Prometheus / Grafana / Loki / Tempo
├── Caddyfile                 # Reverse proxy + TLS (aigestion.net + subdomains)
├── docker-compose.yml        # Full stack (core, postgres+pgvector, redis, caddy, observability)
└── turbo.json                # Turborepo pipeline
```

## Ports

| Port | Service | Notes |
|------|---------|-------|
| 80/443 | Caddy | Reverse proxy + auto-TLS |
| 3000 | Daniela Shell | Next.js frontend |
| 3001 | Landing | Marketing site |
| 9200 | Daniela Core | FastAPI backend (39 API endpoints) |
| 3000 | Grafana | Dashboards |
| 9090 | Prometheus | Metrics |
| 3100 | Loki | Logs |
| 3200 | Tempo | Traces |

> Protected ports (do not collide): 9300 Hermes API, 3200 Hermes dashboard, 9700 infra, 9998 perf.

## Quick start

```bash
# Prereqs: Python 3.11+, Node 22+, pnpm, Docker
cp .env.example .env          # fill in SECRET_KEY, etc.

# Core backend
cd packages/daniela-core
uv sync --extra dev
uvicorn api:create_app --factory --port 9200

# Frontend (landing)
cd apps/landing
pnpm install && pnpm dev      # http://localhost:3001

# Full stack
docker compose up -d          # core + postgres + redis + caddy + observability
```

Then open http://localhost:3001 (landing) and http://localhost:9200/docs (API).

## Daniela Core API

FastAPI app with these route groups (all under `/api/v1/`):

- **brain** — cognitive processing (`POST /brain/process`)
- **memory** — three-tier vault: episodic / semantic / procedural, with decay + consolidation
- **orchestrator** — swarm delegation + Raft consensus across 19 engines
- **persona** — rename Daniela, tune empathy/creativity/formality/humor
- **life** — admin-only autonomous existence: goals, mood, proactive suggestions
- **voice** — on-device TTS/STT
- **agents** — sub-agent swarm registry + dispatch
- **tools** — BYOK tool/MCP gateway, zero markup
- **admin** — AES-256-GCM encryption, challenge-response pairing, Merkle-style audit log

## Security model

- AES-256-GCM authenticated encryption (FIPS 140-3 aligned)
- HMAC-SHA256 challenge-response pairing (PC ↔ Pixel)
- Append-only, tamper-evident audit log (hash-chained)
- Secrets redaction for logs
- Zero-knowledge: keys stay on your device; BYOK keys never marked up

## Business model

| Tier | Price | Highlights |
|------|-------|------------|
| Local | Free forever | Full Daniela OS on your hardware, no account |
| Pro | $29/user/mo | Multi-device sync, cloud LLM routing, swarm |
| Enterprise | $199/user/mo | FIPS 140-3 + HSM, SSO/SCIM, audit, 99.9% SLA |

BYOK, zero markup. Price-match any competitor +10%.

## Repos (this monorepo is `aigestion-universe`)

- **aigestion-universe** — this repo (Turborepo: apps + packages)
- **aigestion-core** — PyPI distribution of `daniela-core`
- **aigestion-infra** — Terraform + FluxCD + k3s GitOps
- **aigestion-robotics** — ROS 2 + hardware configs

## Development

```bash
# Python (core)
cd packages/daniela-core
ruff check . && mypy . && pytest -q

# TypeScript (apps)
pnpm -r lint && pnpm -r typecheck
```

## License

MIT — see [LICENSE](LICENSE).
