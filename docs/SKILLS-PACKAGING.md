# Skills/Plugins — inventario y propuesta de empaquetado (Fase 4)

36 módulos muertos archivados en `scripts/archive/` (cero referencias
en código). Quedan **46 skills + 16 plugins vivos**, con consumidores
reales verificados. NO se empaquetan en esta pasada: varios tienen
integraciones vivas (redes, vault, CI) que merecen ciclo propio con
shims + smoke por dominio, igual que Fase 2.

## Núcleo vivo (no tocar sin plan)

| Módulo | Consumidor verificado |
|--------|----------------------|
| `skills/social_autopilot.py` | `agent_redes` (cola social) |
| `skills/memory.py` | vault / agentes |
| `skills/self_healing.py`, `swarm_manager.py`, `software_architect.py` | SIL / swarm / docs |
| `skills/rag.py`, `pixel_nano_rag.py`, `knowledge_graph.py` | RAG / vault |
| `skills/env_vault.py` | vault PIN / duties |
| `skills/notebooklm_bridge.py` | pipelines notebooklm |
| `skills/local_llm.py`, `ollama_manager.py` | router / edge |
| `skills/security_monitor.py`, `netsec.py` | gate / CI |
| `skills/telemetry_logger.py`, `scheduler.py`, `event_pipeline.py` | daemons |
| `plugins/sentinel.py`, `memory.py`, `notifier.py`, `scheduler.py`, `status.py`, `uptime.py`, `location.py`, `sensors.py`, `vision.py`, `tts_bridge.py`, `security_cam.py`, `gdrive_reporter.py`, `integrity_guard.py`, `power_saver.py`, `memory_analyzer.py`, `briefing.py` | daemons / mobile / plugins runtime (`plugin_system.py`) |

## Propuesta (sesión aparte, patrón Fase 2)

1. `aig/skills/` con los 46 vivos + `__init__.py` ligero.
2. Shims en `skills/` (compat) + `MODULE_SEARCH_PATHS` += skills.
3. `plugin_system.py` → `aig/core/` (es el runtime de plugins).
4. Smoke por dominio: importar cada skill vía shim + paquete,
   `core health`, `sync --check`, ruff. Commit por dominio.
5. Riesgo conocido: imports cruzados skills↔plugins (auditar grafo
   antes de mover, como se hizo con pixel/).

## Archivados esta fase (36, historial preservado)

ambient_lens, api_concierge, app_factory_labs, audio_feedback,
audio_listener, auditor_tactico, backup_manager, battery_check,
canvas_3d_scraper, cdp_automator, chrome_bridge, cleaner,
daily_radio_podcast, file_analyzer, form_automator, ghostwriter,
hardware_ctrl, invoice_extractor, mail_sentinel, net_audit,
network_test, neural_graph_refiner, notebooklm_podcast,
notebooklm_sync, pip_auditor, sadtalker_client, secret_sync,
soundscape_engine, sovereign_voice, spatial_astra, telegram_gateway,
vision_astra, visual_sentinel, visualizer_labs, web_navigator,
web_scout.
