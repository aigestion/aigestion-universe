# aigestion.net - Asistente Virtual Enterprise

## Variables de Entorno

```bash
# Server
PORT=3001
NODE_ENV=production

# LLM Provider (gratuito)
LLM_PROVIDER=qwen
QWEN_API_KEY=your_qwen_api_key_here
DEEPSEEK_API_KEY=your_deepseek_api_key_here

# Database
REDIS_URL=redis://localhost:6379

# Channels
WHATSAPP_TOKEN=your_whatsapp_token
TELEGRAM_TOKEN=your_telegram_token
```

## Inicio Rápido

```bash
# Instalar dependencias
npm install

# Configurar variables
cp .env.example .env
# Editar .env con tus keys

# Iniciar
npm start
```

## API Endpoints

| Endpoint | Método | Descripción |
|----------|--------|-------------|
| `/api/status` | GET | Estado del asistente |
| `/api/chat` | POST | Enviar mensaje |
| `/api/voice` | POST | Enviar audio |
| `/api/metrics` | GET | Métricas de uso |

## Ejemplo de Uso

```bash
curl -X POST http://localhost:3001/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Hola, ¿qué puedes hacer?", "channel": "web"}'
```

## Licencia

MIT - aigestion.net
