# aig Module Inventory — Universo v1

> Complete module listing across all 21 runtime services + gateway/orchestrator + tooling.

## Summary

| Service | Port | Modules | Description |
|---------|------|---------|-------------|
| Epic PC | 5020 | experiencia (20 sub-systems) | Desktop **experiencia**, no módulo |
| Daniela Omnipresente | 9200 | 107 | AI personality system |
| Hermes Epic | 9300 | — | Comms hub |
| AIG Optimization | 9400 | 5 | Performance engine |
| Frontend V1 | 9500 | 10 | Frontend optimization |
| Frontend V2 | 9600 | 14 | Advanced frontend |
| Infra Optimization | 9700 | 20 | Infrastructure management |
| Agent & Mobile | 9800 | 10 | Agent orchestration |
| Security & Monitoring | 9999 | 8 | Security layer |
| Performance & Quality | 9998 | 10 | Code quality tools |
| Unified Dashboard | 9997 | 1 | Central monitoring |
| Intel Engine | 9850 | — | Intelligence engine |
| Auto Engine | 9860 | — | Automation engine |
| Data Engine | 9870 | — | Data/RAG engine |
| Secure Engine | 9880 | — | Hardened security engine |
| DevTools Engine | 9890 | — | Developer tools |
| Ecosystem Engine | 9840 | — | Plugins/marketplace |
| UX Engine | 9830 | — | UX engine |
| Scale Engine | 9820 | — | Scaling engine |
| Chaos Engine | 9910 | 5 | Chaos engineering |
| Regions Server | 9911 | 7 | Multi-region control plane |
| Cross-Engine Orchestrator | 9900 | 6 | Cross-service workflows |
| API Gateway | 8080 | 1 | Single entrypoint proxy |
| Jarvis Backend (legacy) | 5001 | 1 | System monitoring |
| Mobile App v2 | 8090 | 6 | PWA + mobile backend |
| AI Serving / Service | — | 3 | Model router + serving |
| CI Health Gate | — | 2 | `scripts/ci_health_gate.py`, `ci_runner.py` |
| **aig-shared** | — | **8** | **Shared libraries** |

---

## 1. Epic PC (`:5020`) — experiencia, no módulo

> **Clasificación:** Epic PC es una **experiencia** (el espacio de escritorio
> completo que se vive de punta a punta), no un módulo del inventario. Sus 20
> sub-systems y las carpetas de `epic-pc/` son **partes de esa experiencia**,
> no módulos independientes con ciclo de vida propio: no se habilitan ni
> deshabilitan por separado desde el core.
>
> **No confundir con Daniela OS:** Daniela OS (`gev/daniela-os/`) es la
> **app para el PC de Daniela** (servidor, fases, escritorio); Epic PC es
> **Daniela en el PC** (la experiencia de escritorio).

Desktop experience (experiencia) con 20 sub-systems.

| Parte de la experiencia | Port | Description |
|--------|------|-------------|
| `voice_daemon` | 5010 | Voice AI desktop assistant |
| `neural_wallpaper` | 5011 | AI-generated dynamic wallpaper |
| `file_galaxy` | 5012 | 3D file explorer visualization |
| `notification_brain` | 5013 | Smart notification prioritization |
| `health_hologram` | 5014 | System health holographic display |
| `code_copilot` | 5015 | AI code completion assistant |
| `cross_device` | 5016 | Cross-device telepathy sync |
| `app_launcher` | 5017 | Predictive application launcher |
| `ar_overlay` | 5018 | Augmented reality desktop overlay |
| `living_organism` | 5019 | Desktop as living organism metaphor |
| `main` | 5020 | Main orchestrator |
| `memory_palace` | 5021 | AI memory visualization |
| `dream_logger` | 5022 | Session dream-state logging |
| `context_switcher` | 5023 | Rapid context switching |
| `auto_organizer` | 5024 | AI auto-organization |
| `focus_mode` | 5025 | Distraction-free focus mode |
| `typing_predictor` | 5026 | Next-word prediction |
| `meeting_prepper` | 5027 | Pre-meeting intelligence |
| `meeting_digest` | 5028 | Post-meeting summary |
| `email_brain` | 5029 | Email priority scoring |
| `knowledge_weaver` | 5030 | Knowledge graph builder |

**Otras partes de la experiencia** (en `epic-pc/`):
`achievements/`, `ambient-wallpaper/`, `auto-backup/`, `auto-screenshot/`, `clip-translator/`, `clipboard-history/`, `code-rain/`, `desktop-dj/`, `desktop-karaoke/`, `desktop-macros/`, `desktop-pets/`, `encrypted-notes/`, `file-integrity/`, `file-renamer/`, `file-watcher/`, `firewall-monitor/`, `floating-wiki/`, `flow-builder/`, `focus-timer/`, `game-hub/`, `holo-calendar/`, `keyboard-sounds/`, `meme-generator/`, `music-reactive/`, `network-sentinel/`, `night-mode/`, `parental-controls/`, `password-vault/`, `pixel-dashboard/`, `privacy-dashboard/`, `quick-actions/`, `retro-hub/`, `screen-privacy/`, `smart-launcher/`, `sound-visualizer/`, `stream-overlay/`, `theme-time-machine/`, `threat-dashboard/`, `usb-guardian/`, `vr-desktop/`, `zen-garden/`

---

## 2. Daniela Omnipresente (`:9200`)

AI personality system with 107 modules across 10 phases.

### Ambient Presence (10 modules)
| Module | Description |
|--------|-------------|
| `ambient_sounds.py` | Dynamic ambient sound generation |
| `aura_projection.py` | Visual aura projection on desktop |
| `breathing_light.py` | Breathing light pattern for notifications |
| `desktop_pet.py` | AI companion desktop pet |
| `dual_presence.py` | Dual-screen presence management |
| `ghost_mode.py` | Stealth/ghost mode operation |
| `heartbeat.py` | System heartbeat visualization |
| `notification_breathing.py` | Breathing-based notification system |
| `presence_sensor.py` | Physical presence detection |
| `room_tone.py` | Adaptive room tone generation |

### Consciousness (10 modules)
| Module | Description |
|--------|-------------|
| `attention_awareness.py` | User attention level detection |
| `conflict_resolution.py` | Multi-agent conflict resolution |
| `context_handoff.py` | Context transfer between devices |
| `cross_routines.py` | Cross-device routine coordination |
| `device_handoff.py` | Seamless device handoff |
| `memory_graph.py` | Graph-based memory system |
| `parallel_processing.py` | Parallel thought processing |
| `shared_focus.py` | Multi-user shared focus |
| `split_consciousness.py` | Multi-threaded consciousness |
| `unified_personality.py` | Unified personality across devices |

### Proactive Engine (10 modules)
| Module | Description |
|--------|-------------|
| `anomaly_alerts.py` | Anomaly detection and alerts |
| `auto_organization.py` | Automatic content organization |
| `contextual_suggestions.py` | Context-aware suggestions |
| `duplicate_detection.py` | Duplicate content detection |
| `energy_management.py` | System energy optimization |
| `habit_nudges.py` | Habit formation nudges |
| `meeting_predictor.py` | Meeting schedule prediction |
| `pattern_learning.py` | Behavioral pattern learning |
| `predictive_preload.py` | Predictive content preloading |
| `smart_interruptions.py` | Intelligent interruption management |

### Emotional Intelligence (10 modules)
| Module | Description |
|--------|-------------|
| `achievement_celebration.py` | Achievement celebration system |
| `comfort_mode.py` | Emotional comfort mode |
| `emotional_journaling.py` | Emotional state journaling |
| `growth_tracking.py` | Personal growth tracking |
| `inside_jokes.py` | Shared inside jokes system |
| `legacy_builder.py` | Digital legacy construction |
| `memory_lane.py` | Memory lane visualization |
| `mood_mirror.py` | Mood reflection system |
| `shared_secrets.py` | Shared secrets vault |
| `voice_personality.py` | Voice personality traits |

### Embodiment (10 modules)
| Module | Description |
|--------|-------------|
| `digital_twin.py` | Digital twin representation |
| `gesture_recognition.py` | Gesture recognition system |
| `haptic_language.py` | Haptic feedback language |
| `life_score.py` | Life score calculation |
| `light_painting.py` | Light painting effects |
| `physical_anchor.py` | Physical-world anchoring |
| `proximity_awareness.py` | Proximity detection |
| `spatial_audio.py` | Spatial audio positioning |
| `temperature_feedback.py` | Temperature-based feedback |
| `voice_cloning.py` | Voice cloning system |

### Shared Modules (7 modules)
| Module | Description |
|--------|-------------|
| `cross_device_sync.py` | Cross-device synchronization |
| `voice_activation.py` | Voice activation trigger |
| `unified_bridge.py` | Unified service bridge |
| `sse_server.py` | Server-Sent Events endpoint |
| `health_checker.py` | Service health checker |
| `observability.py` | Observability hooks |
| `connection_pool.py` | Connection pooling |

### Dreams (10 modules)
| Module | Description |
|--------|-------------|
| `sleep_stories.py` | Bedtime story generator |
| `dream_journal.py` | Dream journal with interpretation |
| `lucid_triggers.py` | Lucid dreaming reality checks |
| `white_noise.py` | White/pink/brown noise generator |
| `sleep_cycle.py` | 90-min cycle calculator |
| `nightmare_soother.py` | Post-nightmare grounding protocol |
| `nap_optimizer.py` | Power-nap timer (10/20/90) |
| `dream_symbols.py` | Dream symbol dictionary ES/EN |
| `sleep_score.py` | Sleep score 0-100 with tips |
| `astral_radio.py` | Generative sleep radio (web) |

### Temporal (10 modules)
| Module | Description |
|--------|-------------|
| `anniversary_tracker.py` | Anniversary countdowns |
| `countdown_engine.py` | Event countdowns with milestones |
| `time_capsule.py` | Sealed message capsules |
| `future_letters.py` | Letters to future self |
| `season_mood.py` | Season rituals |
| `milestone_map.py` | Life timeline milestones |
| `deja_vu_log.py` | Deja-vu log |
| `birthday_engine.py` | Birthdays + zodiac |
| `year_progress.py` | Year progress tracker |
| `moment_freezer.py` | Freeze-a-moment capture (web) |

### Social (10 modules)
| Module | Description |
|--------|-------------|
| `gift_oracle.py` | Gift ideas by person/budget |
| `birthday_radar.py` | Upcoming birthdays (30d) |
| `contact_insights.py` | Days-since-contact nudges |
| `family_hub.py` | Family members and events |
| `gratitude_exchange.py` | Gratitude streaks |
| `compliment_generator.py` | Sincere compliments |
| `apology_helper.py` | Apology structure guide |
| `celebration_planner.py` | Party checklists |
| `reunion_optimizer.py` | Best-date voting |
| `love_languages.py` | 5 love languages test (web) |

### Muse (10 modules)
| Module | Description |
|--------|-------------|
| `story_cowriter.py` | Story co-writing with twists |
| `poetry_forge.py` | Haiku/sonnet/free verse + ES rhyme |
| `brainstorm_storm.py` | Timed brainstorming + voting |
| `idea_garden.py` | Idea lifecycle garden |
| `plot_twister.py` | Plot twists by genre |
| `character_lab.py` | Character sheets |
| `world_builder.py` | Worldbuilding toolkit |
| `dialogue_doctor.py` | Dialogue diagnostics |
| `song_sketch.py` | Song structure + ES metrics |
| `muse_roulette.py` | Daily creative prompt (web) |

### Guardian (10 modules)
| Module | Description |
|--------|-------------|
| `checkin_engine.py` | Scheduled check-ins with escalation |
| `sos_beacon.py` | SOS with cancelable countdown |
| `med_reminder.py` | Medication adherence tracking |
| `home_safe.py` | Trip ETA with auto-alert |
| `digital_will.py` | Digital legacy instructions |
| `scam_shield.py` | Scam pattern detector |
| `safe_contacts.py` | Emergency contacts |
| `night_watch.py` | Night security summary |
| `calm_anchor.py` | Anxiety crisis protocol |
| `guardian_summary.py` | Daily guardian digest |

---

## 3. AIG Optimization (`:9400`)

Performance optimization engine.

| Module | Description |
|--------|-------------|
| `cache/cache_manager.py` | Redis caching with fallback |
| `sse/sse_server.py` | Server-Sent Events streaming |
| `health/health_checker.py` | Health check endpoints |
| `observe/observability.py` | Observability instrumentation |
| `conn/connection_pool.py` | Connection pooling |

---

## 4. Frontend V1 (`:9500`)

Frontend optimization suite.

| Module | Description |
|--------|-------------|
| `sw/sw_engine.py` | Service Worker engine |
| `sw/web_manifest.py` | Web app manifest |
| `virtual/virtual_scroll.py` | Virtual scrolling for lists |
| `perf/perf_monitor.py` | Frontend performance monitoring |
| `assets/asset_optimizer.py` | Static asset optimization |
| `assets/frontend_cache.py` | Frontend caching strategy |
| `theme/theme_engine.py` | Dynamic theme engine |
| `ux/ux_enhancements.py` | UX enhancement modules |
| `ux/command_palette.py` | Command palette interface |
| `assets/animation_engine.py` | Animation engine |

---

## 5. Frontend V2 (`:9600`)

Advanced frontend optimization.

| Module | Description |
|--------|-------------|
| `code/code_splitting.py` | Code splitting & lazy imports |
| `assets2/lazy_loading.py` | Lazy loading for assets |
| `perf2/web_workers.py` | Web Worker offloading |
| `render/ssr_engine.py` | Server-side rendering engine |
| `assets2/image_opt.py` | Image optimization pipeline |
| `assets2/font_opt.py` | Font optimization & subsetting |
| `code/tree_shaking.py` | Dead code elimination |
| `perf2/webassembly.py` | WebAssembly integration |
| `web/edge_compute.py` | Edge compute functions |
| `ux2/a11y.py` | Accessibility improvements |
| `security/security.py` | Frontend security headers |
| `ux2/analytics.py` | Privacy-first analytics |
| `web/resource_hints.py` | Resource hint optimization |
| `web/http2.py` | HTTP/2 push & multiplexing |

---

## 6. Infra Optimization (`:9700`)

Infrastructure management — 20 modules across 5 categories.

### Docker Management
| Module | Description |
|--------|-------------|
| `docker/docker_compose.py` | Docker Compose management |
| `docker/nginx_lb.py` | Nginx load balancer config |
| `docker/auto_healing_v2.py` | Auto-healing containers |
| `docker/health_dashboard.py` | Container health dashboard |
| `docker/zero_downtime.py` | Zero-downtime deployments |

### Database Management
| Module | Description |
|--------|-------------|
| `database/sqlite_wal.py` | SQLite WAL mode setup |
| `database/query_optimizer.py` | Query optimization |
| `database/connection_pool.py` | DB connection pooling |
| `database/vector_search.py` | Vector similarity search |
| `database/backup_scheduler.py` | Automated backup scheduler |

### API Infrastructure
| Module | Description |
|--------|-------------|
| `api/redis_rate_limit.py` | Redis-based rate limiting |
| `api/request_caching.py` | HTTP response caching |
| `api/graphql_endpoint.py` | GraphQL API gateway |
| `api/grpc_bridge.py` | gRPC bridge/proxy |
| `api/api_versioning.py` | API version management |

### Monitoring
| Module | Description |
|--------|-------------|
| `monitoring/prometheus_metrics.py` | Prometheus metrics exporter |
| `monitoring/grafana_dashboard.py` | Grafana dashboard configs |
| `monitoring/structured_logging.py` | Structured JSON logging |
| `monitoring/distributed_tracing.py` | Distributed tracing (OpenTelemetry) |
| `monitoring/alert_system.py` | Threshold-based alerting |

---

## 7. Agent & Mobile (`:9800`)

Agent orchestration and mobile integration.

| Module | Description |
|--------|-------------|
| `swarm/swarm_intelligence.py` | Multi-agent swarm coordination |
| `registry/agent_registry.py` | Agent registration & discovery |
| `chain/agent_chain.py` | Agent chaining/pipeline |
| `memory/agent_memory.py` | Agent memory persistence |
| `health/agent_health.py` | Agent health monitoring |
| `mobile/adb_optimization.py` | Android ADB optimization |
| `mobile/battery_saver.py` | Mobile battery optimization |
| `mobile/push_notifications.py` | FCM push notifications |
| `mobile/mobile_offline.py` | Offline mode for mobile |
| `mobile/nfc_connect.py` | NFC pairing connection |

---

## 8. Security & Monitoring (`:9999`)

Security layer with 8 modules.

### Secrets & Auth
| Module | Description |
|--------|-------------|
| `secrets/secrets_management.py` | Vault-based secrets storage |
| `security/security_headers.py` | CSP, CORS, security headers |
| `auth/jwt_refresh.py` | JWT token refresh flow |

### Audit
| Module | Description |
|--------|-------------|
| `audit/ip_whitelist.py` | IP whitelist management |
| `audit/audit_log.py` | Structured audit logging |

### Monitoring
| Module | Description |
|--------|-------------|
| `monitoring2/realtime_metrics.py` | Real-time security metrics |
| `monitoring2/anomaly_detection.py` | Anomaly detection engine |
| `monitoring2/log_aggregator.py` | Centralized log aggregation |

---

## 9. Performance & Quality (`:9998`)

Code quality and performance tools.

### Async I/O
| Module | Description |
|--------|-------------|
| `async_io/async_io.py` | Async I/O operations |
| `async_io/websocket_realtime.py` | WebSocket realtime server |

### Performance
| Module | Description |
|--------|-------------|
| `performance/bg_workers.py` | Background worker pool |
| `performance/http2_server.py` | HTTP/2 server support |
| `performance/brotli_compression.py` | Brotli compression |
| `performance/connection_keepalive.py` | Connection keepalive |

### Quality
| Module | Description |
|--------|-------------|
| `quality/type_hints.py` | Type hint enforcement |
| `quality/auto_formatting.py` | Auto code formatting |
| `quality/test_coverage.py` | Test coverage tracking |
| `quality/ci_cd.py` | CI/CD pipeline config |

---

## 10. Unified Dashboard (`:9997`)

Central monitoring and service registry.

| Component | Description |
|-----------|-------------|
| `server.py` | Flask + SocketIO server |
| Background poller | 5s interval status polling |
| WebSocket emitter | Real-time status broadcast |
| Service registry | Aggregated service view |

---

## 11. Jarvis Backend (`:5001`)

FastAPI system monitoring.

| Endpoint | Description |
|----------|-------------|
| `/api/system/info` | Full system metrics (CPU, RAM, Disk, Network) |
| `/api/system/cpu` | CPU percent, count, frequency, per-core |
| `/api/system/memory` | Memory total, used, available, swap |
| `/api/system/disk` | Disk total, used, free, percent |
| `/api/system/network` | Network bytes/packets sent/received |
| `/api/system/processes` | Top 10 processes by CPU |
| `/api/health` | Health check with threshold warnings |

---

## 12. Intel Engine (`:9850` — `intel_engine/`)

Intelligence engine — research, insights, synthesis.

| Component | Description |
|-----------|-------------|
| `server.py` | Flask/FastAPI server, `GET /api/intel/status` |
| analyzers | Insight extraction, scoring |
| Tests | `tests/core/test_intel.py` |

## 13. Auto Engine (`:9860` — `auto_engine/`)

Automation engine — pipelines, schedulers, autonomous tasks.

| Component | Description |
|-----------|-------------|
| `server.py` | Server, `GET /api/auto/status` |
| pipelines | `auto_pipeline.py`, schedulers, daemons |
| Tests | `tests/core/test_auto.py` |

## 14. Data Engine (`:9870` — `data_engine/`)

Data engine — ingestion, RAG, analytics.

| Component | Description |
|-----------|-------------|
| `server.py` | Server, `GET /api/data/status` |
| ingest/rag | Omni-ingest, vector search, backups |
| Tests | `tests/core/test_data.py` |

## 15. Secure Engine (`:9880` — `secure_engine/`)

Hardened security engine.

| Component | Description |
|-----------|-------------|
| `server.py` | Server, `GET /api/secure_engine/status` |
| guards | Vault, policy enforcement, audit |
| Tests | `tests/security/test_secure.py` |

## 16. DevTools Engine (`:9890` — `devtools_engine/`)

Developer tooling.

| Component | Description |
|-----------|-------------|
| `server.py` | Server, `GET /api/devtools/status` |
| tools | Docs engine, scaffolds, test helpers |
| Tests | `tests/core/test_devtools.py` |

## 17. Ecosystem Engine (`:9840` — `ecosystem_engine/`)

Plugins, marketplace, connectors.

| Component | Description |
|-----------|-------------|
| `server.py` | Server, `GET /api/ecosystem/status` |
| catalog | `agents_catalog.json`, `plugins_catalog.json`, skills |
| Tests | `tests/integration/test_ecosystem.py` |

## 18. UX Engine (`:9830` — `ux_engine/`)

UX engine — themes, layouts, a11y.

| Component | Description |
|-----------|-------------|
| `server.py` | Server, `GET /api/ux/status` |
| ux | Themes, animations, accessibility |
| Tests | `tests/security/test_ux.py` |

## 19. Scale Engine (`:9820` — `scale_engine/`)

Scaling engine.

| Component | Description |
|-----------|-------------|
| `server.py` | Server, `GET /api/scale/status` |
| policies | Autoscale rules, worker pools, load profiles (`load-testing/`) |
| Tests | `tests/core/test_scale.py` |

## 20. Chaos Engine (`:9910` — `chaos_engine/`)

Chaos engineering — guarded, never auto-armed in prod.

| Module | Description |
|--------|-------------|
| `server.py` | Flask server, `GET /api/chaos/status`, `POST /api/chaos/experiments` |
| `faults.py` | Fault injectors: latency, error-rate, kill, partition |
| `experiments.py` | Experiment scenarios + lifecycle |
| `scheduler.py` | Cron/interval scheduling |
| `validators.py` | Steady-state hypothesis checks |
| Tests | `tests/performance/test_chaos.py` |

## 21. Regions Server (`:9911` — `multi-region/`)

Multi-region control plane. See `docs/MULTI_REGION.md`.

| Module | Description |
|--------|-------------|
| `server.py` | Flask server, `GET /api/regions/status`, `/route`, `/failover/*` |
| `load_balancer.py` | GeoDNS / round-robin / weighted routing |
| `failover.py` | 3-strike failover, 30s cooldown, chains |
| `replication.py` | Cross-region sync (last-write-wins) |
| `health_mesh.py` | 5s health checks |
| `dns_sim.py` | DNS simulation |
| `failover_drill.py` | Failover drill runner |
| Tests | `tests/integration/test_multi_region.py`, `tests/core/test_regions_active.py` |

## 22. Cross-Engine Orchestrator (`:9900` — `cross_engine/`)

| Module | Description |
|--------|-------------|
| `server.py` | Flask server, `/api/cross/*` |
| `orchestrator.py` | Dispatch / chain / fan-out workflows |
| `gateway.py` | Engine routing table |
| `connector.py` | Per-engine HTTP connectors |
| `event_bus.py` | Cross-engine event bridge |
| `protocols.py` | Shared schemas / contracts |
| Tests | `tests/integration/test_cross_engine.py` |

## 23. API Gateway (`:8080` — `api_gateway.py`)

| Component | Description |
|-----------|-------------|
| `api_gateway.py` | Reverse proxy `/api/<engine>/*` → 21 engines, JWT, rate limit, CORS, `/health`, `/metrics` |
| `nginx.conf` / `nginx/` | Alt Nginx front (80/443, SSL, `limit_req`) |
| Tests | `tests/core/test_api_gateway.py` |

## 24. Mobile App v2 (`:8090` — `mobile-app/`)

**Árbol único de cliente desde 2026-09-29.** Antes había tres copias
(`mobile-app/` en la raíz, `android_app/mobile-app/` y suelto `android_app/`);
ahora todo vive en `mobile-app/`, incluido lo que colgaba de `android_app/`:

> **«Pixel» no es un dominio**: es el nombre del teléfono. Su código
> (`mobile-app/pixel/`) es código de móvil y vive dentro de `mobile-app/`.

| Component | Description |
|-----------|-------------|
| `manifest.json` / `sw.js` / `index.html` | PWA shell (installable, offline) + importmap de three |
| `css/mobile.css` | Mobile-first OLED theme + escenario del avatar |
| `js/app.js` | Router, SW registration, notifications (módulo ES) |
| `js/api.js` | `AIGApi` client → gateway `:8080` + dashboard `:9997` |
| `js/views.js` | Home / Daniela / Hermes / Settings views |
| `js/daniela-avatar.js` | Avatar 3D de Daniela: estados, voz, animación procedural |
| `assets/daniela3d.glb` | Modelo optimizado 79 MB → 3,2 MB (`gltf-transform`) |
| `vendor/three/` | three.js 0.180 vendorizado para funcionar offline |
| `js/gev.js` / `sensors.js` / `notifications.js` | Puente GEV, sensores, notificaciones |
| `services/{sensors,security,mesh,ui,iot}/` | Código que corre en el teléfono (agrupado por destino) |
| `bridges/{comms,pixel}/` | Puentes Termux/BT/IR/NFC/serie/ADB/FCM + hub del Pixel |
| `core/{autonomy,context,ci}/` | Autonomía (malla, daemon, enrutador), contexto y CI edge |
| `api/` | `termux_api_gateway.py` — 30 endpoints |
| `src/` | Manifiesto Android huérfano |
| Tests | `tests/pixel/test_mobile_v2.py`, `tests/pixel/test_mobile_v2.py` |

`mobile-app/pixel/` y `mobile-app/phone_deploy/` se fusionaron y borraron el
2026-09-29: no hay copias planas.

See `docs/MOBILE.md`.

## 25. AI Serving / Service Layer

| Module | Description |
|--------|-------------|
| `scripts/model_router.py` | Model routing + fallback (GPT/Gemini/Claude/local) |
| `tencent-suite/` / `colab-notebooks/` | Serving harnesses, eval notebooks |
| Tests | `tests/agents/test_ai.py`, `tests/core/test_ml_serving.py` |

## 26. CI Health Gate (`scripts/`)

| Module | Description |
|--------|-------------|
| `scripts/ci_health_gate.py` | Pre/post-deploy gate: polls all 21 `/api/*/status` + gateway/orchestrator, fails CI on offline |
| `ci_runner.py` / `scripts/ci_runner.py` | CI task runner |
| Tests | `tests/core/test_ci_health_gate_core.py` |

```bash
python scripts/ci_health_gate.py --all --fail-on-offline
pytest tests/core/test_ci_health_gate_core.py tests/core/test_regions_active.py -v
```

## aig-shared (`aig-shared/aig_shared/`)

Shared library used by all services.

| Module | Description |
|--------|-------------|
| `config/__init__.py` | Service configuration, port registry, env accessors |
| `registry/__init__.py` | Service registry — register, heartbeat, health check |
| `events/__init__.py` | Event bus — NATS + in-memory fallback |
| `auth/__init__.py` | JWT handler — encode, decode, HS256 |
| `metrics/__init__.py` | Prometheus metrics wrapper with fallback |
| `logging/__init__.py` | Structured JSON logging with correlation IDs |
| `errors/__init__.py` | Standard error types and codes |
| `utils/__init__.py` | Common utilities — hash, retry, timer, sanitize |
