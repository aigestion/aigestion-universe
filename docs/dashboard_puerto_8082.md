# Dashboard AIGestion Puerto 8082 - Rutas Configuradas

Basado en `indicaciones.txt` conversacion 1 - "5 rutas en el dashboard :8082"

## Rutas Disponibles (GET)

| Ruta | Descripción | Componente |
|------|-------------|------------|
| `/` | Página principal/dashboard general | `DashboardIndex` |
| `/daniela` | Perfil y estado Directora General | `DanielaProfile` |
| `/equipo` | Organigrama 20 directores + 88 subagentes | `TeamOrgChart` |
| `/swarm` | Distribución de subagentes por dirección | `SwarmView` |
| `/config` | Configuración empresa AIGestion | `CompanyConfig` |

## Endpoints API

| Endpoint | Método | Descripción |
|----------|--------|-------------|
| `/api/v1/status` | GET | Estado general sistema (ruff=0, tests=80/v) |
| `/api/v1/daniela` | GET | Perfil y salud Daniela |
| `/api/v1/team` | GET | Estructura team.json (20 directores, 88 subagentes) |
| `/api/v1/swarm` | GET | Distribución swarm_por_direccion.py |
| `/api/v1/faces` | GET | Lista avatares disponibles (JPEG/SVG) |

## Configuración Técnica

```python
DASHBOARD_CONFIG = {
    "puerto": 8082,
    "host": "0.0.0.0",
    "modo": "produccion",
    "hermes_conectado": True,  # Puerto 9300
    "daniela_conectada": True,  # Bridge activo
    "tests_verdaderos": 80,
    "linter_pass": True,  # ruff=0
    "ultima_actualizacion": "2026-10-08",
}
```

## Integración con Hermes

- Hermes (puerto 9300) provee módulos base
- Dashboard consulta estado salud Hermes/Daniela
- Bridge `hermes_daniela_bridge.py` mantiene sincronización
- Fallback: si Hermes caído, dashboard muestra modo degradado

## Estado Actual
- ✅ Ruff: 0 errores
- ✅ Tests: 80 verdes
- ✅ Linter: Passing
- ⚠️ 8 fallos restantes (expectativas semánticas hilo separado)
- ⚠️ Gate completo se abortó antes de terminar (última cifra: 82/155 fallos totales bajaron)

## Próximos Desarrollos Planificados
1. Integrar OpenClaw sidecar (periférico Telegram → Hermes :9900)
2. Migrar 8 expectativas semánticas pendientes
3. Completar gate full integration
4. Onboarding multi-cliente `{empresa}-daniela`