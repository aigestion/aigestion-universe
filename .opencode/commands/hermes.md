# /hermes - Trabaja con Hermes Gateway (puerto 9300 API, 3200 Dashboard)

Trabaja con **Hermes** - gateway cognitivo (10 skills, 3 tiers memoria: Episódica/Semántica/Procedural).

## Ámbito
- `ide/hermes/` - código principal (server.py puerto 9300, web/ dashboard puerto 3200)
- `docker/hermes-epic/` - despliegue "epic" (config para aig/daniela-os)
- `config/docker/` - servicios hermes en compose

## Puertos
- **9300**: API Hermes (REST, skills, memoria, integración)
- **3200**: Dashboard completo Windows Desktop (web/index.html + API status)

## Operaciones típicas
- Añadir/ajustar skill cognitivo
- Gestionar transición tiers memoria
- Routing cross-engine (19 engines federados)
- Debug memoria / consenso
- Dashboard Windows: http://localhost:3200

## Reglas
- Gate antes de commit
- Nunca push
EOF