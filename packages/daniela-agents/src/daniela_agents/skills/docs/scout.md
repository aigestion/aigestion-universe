# Skill: Scout

Descubre información relevante 24/7.

## Capacidades
- Escanear canales de YouTube
- Escanear feeds RSS
- Escanear Reddit
- Descargar videos interesantes

## Uso
```python
from phone.agents.scout.scout import ScoutAgent

scout = ScoutAgent()
result = scout.run()
```

## Configuración
```json
{
  "channels": ["@veritasium", "@3blue1brown"],
  "feeds": ["https://news.ycombinator.com/rss"]
}
```
