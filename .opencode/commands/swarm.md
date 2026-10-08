# /swarm - Coordinación Swarm (puerto 8080)

Trabaja con **Swarm Intelligence** - consenso Raft, orquestación cross-engine.

## Ámbito
- `engine/cross_engine/` - orquestador cross-engine (puerto 9900)
- `config/docker/docker-compose*.yml` - servicios swarm
- `chaos_engine` - ingeniería de caos

## Operaciones típicas
- Elección líder Raft / consenso
- Distribución tareas cross-engine
- Health checks 18 servicios vigilados (ci_health_gate.py)
- Chaos experiments

## Reglas
- Gate antes de commit
- Nunca push
EOF