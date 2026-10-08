# Skill: Code Quality

Analiza y mejora la calidad del código automáticamente.

## Capacidades
- Lint con ruff
- Type check con mypy
- Búsqueda de TODOs y FIXMEs
- Estadísticas de código
- Análisis de complejidad

## Uso
```python
from tools.code_tools import run_lint, run_type_check, get_file_stats, find_todos
```

## Configuración
```json
{
  "ruff_rules": ["E", "F", "W", "I"],
  "mypy_strict": false,
  "max_complexity": 10
}
```

## Métricas
- Errores lint: 0
- Type errors: 0
- TODOs pendientes: 0
- Cobertura tests: 80%+
