# Arquitectura Dual: Teléfono + PC

## Visión

AIG funciona en dos entornos complementarios:

| Entorno | Rol | Recursos |
|---|---|---|
| **Teléfono (Termux)** | Runtime 24/7, recolección, agentes ligeros | CPU 8 cores, 8GB RAM, batería |
| **PC (Docker)** | Procesamiento pesado, LLM, almacenamiento, dashboards | CPU 16 cores, 32GB RAM, GPU |

## División de Responsabilidades

### Teléfono (Termux) — "El Sistema Nervioso"
- **Agentes 24/7**: Scout, Social, Caller, Guardian
- **Recolección**: Videos, RSS, Reddit, sensores
- **Ejecución local**: Whisper.cpp, Piper, llama.cpp
- **Comunicación**: MQTT, WebSocket, sync con PC
- **Batería**: Modo ahorro de energía, wake locks

### PC (Docker) — "El Cerebro"
- **Procesamiento pesado**: LLM (Gemini, DeepSeek), embeddings
- **Almacenamiento**: PostgreSQL, Redis, MinIO
- **Dashboards**: Grafana, Prometheus, Daniela Dashboard
- **Contenedores**: n8n, Home Assistant, ESPHome, MQTT
- **GPU**: Entrenamiento, inferencia, video

## Sincronización

```
┌─────────────────────────────────────────────────────────────┐
│                      AIG DUAL                               │
├────────────────────────────┬────────────────────────────────┤
│      TELÉFONO (Termux)     │        PC (Docker)             │
├────────────────────────────┼────────────────────────────────┤
│                            │                                │
│  📱 Agentes 24/7           │  🧠 LLM + Embeddings           │
│  📡 Recolección            │  💾 Almacenamiento             │
│  🎤 Whisper.cpp (STT)      │  🎬 FFmpeg (video pesado)      │
│  🗣️ Piper (TTS)            │  📊 Dashboards                 │
│  🔋 Batería + Sensors      │  🚀 GPU + CPU                  │
│                            │                                │
│  ┌──────────────────────┐  │  ┌──────────────────────────┐  │
│  │  MQTT Client         │  │  │  MQTT Broker             │  │
│  │  WebSocket Client    │  │  │  WebSocket Server        │  │
│  │  Sync Agent          │  │  │  Sync Agent              │  │
│  └──────────────────────┘  │  └──────────────────────────┘  │
│           ↕                │           ↕                    │
│  ┌──────────────────────┐  │  ┌──────────────────────────┐  │
│  │  SQLite (local)      │  │  │  PostgreSQL (central)    │  │
│  │  FAISS (embeddings)  │  │  │  Redis (cache)           │  │
│  └──────────────────────┘  │  └──────────────────────────┘  │
│                            │                                │
└────────────────────────────┴────────────────────────────────┘
```

## Flujo de Datos

### Teléfono → PC
1. Scout descubre video interesante
2. Sube metadata a PC (título, URL, timestamp)
3. PC procesa con LLM (resumen, guion)
4. PC devuelve guion al teléfono
5. Teléfono genera video con Piper + FFmpeg
6. Teléfono publica en redes sociales

### PC → Teléfono
1. PC detecta tendencia (Reddit, Twitter)
2. Envía alerta al teléfono
3. Teléfono graba contenido relevante
4. Teléfono sube datos a PC

## Configuración

### Teléfono (Termux)
```bash
# Variables de entorno
export AIG_MODE="phone"
export AIG_PC_HOST="192.168.1.100"
export AIG_MQTT_HOST="192.168.1.100"
export AIG_SYNC_INTERVAL=300
```

### PC (Docker)
```bash
# Variables de entorno
export AIG_MODE="pc"
export AIG_PHONE_HOST="192.168.1.50"
export AIG_MQTT_HOST="localhost"
export AIG_GPU_ENABLED=true
```

## Recursos Equilibrados

| Recurso | Teléfono | PC |
|---|---|---|
| CPU | 25% (2 cores) | 75% (12 cores) |
| RAM | 2GB | 24GB |
| Almacenamiento | 32GB | 2TB |
| GPU | - | RTX 4090 |
| Red | WiFi 6 | Ethernet 1Gbps |
| Batería | 8000mAh | - |

## Portabilidad del Código

Todo el código es **portable** entre entornos:

```python
# Detectar entorno automáticamente
import os

AIG_MODE = os.getenv("AIG_MODE", "auto")

if AIG_MODE == "auto":
    if os.path.exists("/data/data/com.termux"):
        AIG_MODE = "phone"
    else:
        AIG_MODE = "pc"

# Configuración según entorno
if AIG_MODE == "phone":
    WHISPER_MODEL = "tiny"
    PIPER_MODEL = "en_US-lessac-medium"
    LLM_MODEL = "gemini-2.0-flash"
else:
    WHISPER_MODEL = "large-v3"
    PIPER_MODEL = "en_US-ryan-high"
    LLM_MODEL = "gemini-2.0-flash"
```

## Reglas

1. **Teléfono**: Solo agentes ligeros, recolección, sync
2. **PC**: Procesamiento pesado, LLM, almacenamiento
3. **Sincronización**: MQTT + WebSocket, cada 5 minutos
4. **Fallback**: Si PC no disponible, teléfono usa modelos locales
5. **Batería**: Teléfono entra en modo ahorro si < 20%
