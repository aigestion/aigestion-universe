# Skill: Studio

Crea contenido viral automáticamente.

## Capacidades
- Transcribir videos (Whisper)
- Generar guiones virales
- Generar voz (Piper)
- Crear videos (FFmpeg)

## Uso
```python
from phone.agents.studio.studio import StudioAgent

studio = StudioAgent()
result = studio.run()
```

## Pipeline
```
Video → Whisper → Guion → Piper → FFmpeg → TikTok
```
