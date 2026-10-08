# Skill: AI Assistant

Usa modelos de IA gratuitos para generar contenido, responder preguntas y automatizar tareas.

## Capacidades
- Gemini 2.0 Flash: 1500 req/día gratis
- DeepSeek: gratis con API key
- Qwen: gratis con API key
- Embeddings: Gemini text-embedding-004

## Uso
```python
from tools.ai_tools import gemini_generate, gemini_chat, gemini_embed, deepseek_chat
```

## Configuración
```json
{
  "gemini_api_key": "",
  "deepseek_api_key": "",
  "default_model": "gemini-2.0-flash"
}
```

## Límites gratuitos
- Gemini: 1500 req/día
- DeepSeek: 100 req/día
- Qwen: 1000 req/día
