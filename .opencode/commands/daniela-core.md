# /daniela-core - Trabaja con Daniela Core (puerto 9200)

Trabaja con **Daniela Core** - la IA omnipresente (12,480 nodos memoria, 96% empatía, Nivel Coherente 4).

## Ámbito
- `daniela-os/daniela-jarvis/` - propiedades PC
- `docker/epic-pc/` - despliegue PC
- `daniela-os/model_router.py` - enrutamiento LLM (v3 solo gratis)
- `daniela-os/auth_system.py`, `billing_system.py`, `white_label.py` - sistemas core
- `core/config/paths.py` - paths canónicos (DANIELA_DB, AUTH_DB, BILLING_DB, WHITELABEL_DB)
- `config/docker/docker-compose*.yml` - servicios daniela (puerto 9200)

## Operaciones típicas
- Añadir memoria / consultar vault
- Ajustar enrutamiento modelos (gemini → openrouter → groq → deepseek → qwen → mistral → ollama)
- Configurar empatía / nivel coherencia
- Desplegar/actualizar stack daniela

## Reglas
- Gate antes de commit: `ruff ratchet` (techo 0) + `pytest` vs baseline
- Nunca push
- Sin secretos en diff
EOF