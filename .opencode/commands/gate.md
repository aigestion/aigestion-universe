# /gate — valida la suite contra la línea base

Ejecuta el gate de calidad del monorepo y devuelve veredicto GO/NO-GO.

## Gate
```bash
python3 -m pytest tests/ -q --tb=no \
  -p no:cacheprovider --continue-on-collection-errors
```

## Criterio
- **GO**: 0 fallos/errores nuevos **por nombre** vs la línea base vigente
  (ver `handoff.md`, sección Pendiente).
- **NO-GO**: cualquier fallo nuevo → listar nombres exactos, no commitear.
- **GO (+bonus)**: bajan los fallos preexistentes sin cambiar nada más.

Para validaciones delegadas usa el agente `gatekeeper`
(`.opencode/agents/gatekeeper.yaml`).
