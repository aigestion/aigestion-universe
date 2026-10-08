# Skill: Content Creation

Crea contenido viral automáticamente para TikTok, YouTube Shorts, Twitter, Instagram.

## Capacidades
- Transcribir videos (Whisper)
- Generar guiones virales (Gemini)
- Generar voz (Piper)
- Crear videos (FFmpeg)
- Descargar videos (yt-dlp)
- Publicar en redes sociales

## Pipeline
```
Video YouTube → yt-dlp → Whisper → Gemini → Guion → Piper → FFmpeg → TikTok
```

## Uso
```python
from tools.content_tools import download_video, transcribe_audio, generate_tts, create_video_from_images
from tools.social_tools import post_to_tiktok, post_to_twitter, post_to_instagram
```

## Configuración
```json
{
  "whisper_model": "base",
  "piper_voice": "en_US-lessac-medium",
  "video_resolution": "1080x1920",
  "video_fps": 30
}
```
