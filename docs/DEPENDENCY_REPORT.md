# Informe de Dependencias — C:\Users\Alejandro\aig

Generado: 2026-09-06  |  Alcance: raíz + subcarpetas (excluye `.venv`, `.git`, `assets`, `data`, `rostros`, `node_modules`, `backup_patches`, `output`, `content_output`, `drive-reports`, `knowledge-db`)
Archivos escaneados: 1281 Python, 10 JS/Node

---

## 1. Manifiestos declarados

### 1.1 Python — `requirements.txt` (raíz)
| Paquete | Versión declarada | Estado real en `.venv` |
|---|---|---|
| flask | >=3.0.0 | Werkzeug 3.1.8 + Jinja2 3.1.6 instalados (Flask no aparece en `pip list` — **ausente del venv**) |
| google-genai | >=0.3.0 | **No instalado** |
| google-api-python-client | >=2.100.0 | **No instalado** (httplib2 0.32.0 sí, uritemplate 4.2.0 sí) |
| google-auth | >=2.20.0 | **No instalado** (pyasn1 0.6.4, oauthlib 3.3.1 sí) |
| google-auth-oauthlib | >=1.0.0 | **No instalado** |
| edge-tts | >=6.1.0 | **No instalado** |
| requests | >=2.31.0 | 2.34.2 ✓ |
| Pillow | >=10.0.0 | 12.3.0 ✓ |
| numpy | >=1.24.0 | 2.5.2 ✓ |
| asyncio-mqtt | >=0.16.0 | **No instalado** (sí está `paho-mqtt 2.1.0` — sustituto MQTT presente) |

**Conclusión Python:** el `requirements.txt` declara 10 paquetes pero solo 3 (requests, Pillow, numpy) están realmente instalados. El entorno está **muy desincronizado** con el manifiesto. Las suites de Google, edge-tts y asyncio-mqtt faltan.

### 1.2 Node — `metaverse-package.json` (raíz)
```json
"dependencies": { "ws": "^8.16.0" }
```
Solo se importa `ws` en `metaverse_server.js`. No hay `node_modules` instalado.

### 1.3 Node — `decentraland\package.json`
```json
"devDependencies": { "@dcl/sdk": "^7.0.0" }
```
No hay código fuente en esa carpeta que consuma el SDK; el manifiesto es declarativo para un proyecto Decentraland separado.

---

## 2. Imports reales en el código

### 2.1 Top imports Python (los recuentos altos en `sys`/`unittest`/`pytest` provienen mayoritariamente de tests y de scaffolding)

**Stdlib (no requieren instalación):**
`os` (227), `sys` (995), `json` (159), `subprocess` (105), `time` (76), `datetime` (58), `typing` (56), `dataclasses` (42), `pathlib` (31), `re` (28), `__future__` (21), `logging` (19), `importlib` (16), `threading` (16), `argparse` (15), `urllib` (13), `asyncio` (13), `hashlib` (12), `sqlite3` (9), `collections` (9), `base64` (9), `shutil` (4), `functools` (4), `enum` (4), `traceback` (5), `textwrap` (3), `uuid` (3), `random` (3), `http` (3), `socket` (3), `platform` (2), `inspect` (2), `hmac` (2), `ast` (2), `math` (2), `socketserver` (2), `shlex` (1), `signal` (1), `imaplib` (1), `calendar` (1), `concurrent` (1), `py_compile` (2)

**Dependencias de terceros REALMENTE USADAS en código (no stdlib):**

| Paquete | Usos | ¿En requirements.txt? | ¿Instalado en .venv? |
|---|---:|---|---|
| google (genai/ai/...) | 75 | parcial (solo google-genai) | NO |
| googleapiclient | 14 | sí | NO |
| google_auth_oauthlib | 3 | sí | NO |
| flask | 20 | sí | NO |
| requests | 25 | sí | sí |
| PIL (Pillow) | 9 | sí | sí |
| numpy | 6 | sí | sí |
| edge_tts | 11 | sí | NO |
| rich | 14 | NO | NO |
| reportlab | 4 | NO | NO |
| telegram | 4 | NO | NO |
| dotenv | 3 | NO | NO |
| faster_whisper | 3 | NO | NO |
| gtts | 2 | NO | NO |
| speech_recognition | 2 | NO | NO |
| psutil | 2 | NO | NO |
| firebase_admin | 2 | NO | NO |
| eth_account | 2 | NO | NO |
| jinja2 | 1 | NO (transitivo de Flask) | sí (3.1.6) |
| paho-mqtt | 0 (pero instalado) | NO (sustituye asyncio-mqtt) | sí |

**Módulos internos del proyecto** (no son dependencias externas): `skills`, `core`, `message_broker`, `pixel_bridge_hub`, `daniela_os_core`, `auth_system`, `billing_system`, `daniela_self_improvement`, `agent_calendario`, `agent_correo`, `agent_documentos`, `agent_redes`, `agent_vigia`, `dual_mode_switch`, `verificar_rostro`, `monitor_recursos`, `email`, `telegram` (cuidado: choca con `python-telegram-bot`).

### 2.2 JS / Node
| Import | Usos | Notas |
|---|---:|---|
| ws | 1 | declarado en metaverse-package.json |
| http, fs, path | 1 cada uno | stdlib de Node |
| /static/js/api-client.js | 2 | ruta local, no dependencia npm |

---

## 3. Huecos críticos

### 3.1 Declarado en requirements.txt pero NO usado en el código
- `asyncio-mqtt` — 0 imports; el código usa `paho-mqtt` (que sí está instalado).

### 3.2 Usado en el código pero NO declarado en requirements.txt
Faltan al menos: **rich, reportlab, telegram (python-telegram-bot), python-dotenv, faster-whisper, gTTS, SpeechRecognition, psutil, firebase-admin, eth-account**. Cualquier intento de ejecutar el código fuera del `.venv` actual fallará en frío.

### 3.3 Declarado pero NO instalado
`flask`, `google-genai`, `google-api-python-client`, `google-auth`, `google-auth-oauthlib`, `edge-tts`. Toda la integración con Gemini/Google Workspace/TTS está **no ejecutable** desde un entorno limpio.

---

## 4. Recomendaciones

1. **Regenerar `requirements.txt`** escaneando los imports: como mínimo añadir
   ```
   flask, google-genai, google-api-python-client, google-auth, google-auth-oauthlib,
   edge-tts, requests, Pillow, numpy,
   rich, reportlab, python-telegram-bot, python-dotenv,
   faster-whisper, gTTS, SpeechRecognition, psutil, firebase-admin, eth-account
   ```
   y eliminar `asyncio-mqtt` (sustituido por `paho-mqtt`).

2. **Reconciliar `requirements.txt` con el venv** actual (`pip freeze > requirements.txt`) o, mejor, fijar versiones exactas e instalar todo en un entorno limpio para verificar que el código arranca.

3. **Instalar `node_modules`** del proyecto metaverse (`npm install` dentro de la carpeta con `metaverse_server.js`) antes de probarlo; la dependencia `ws` no está descargada.

4. **Migrar `requirements.txt` a `pyproject.toml`** (PEP 621) — actualmente es el único manifiesto y mezcla dependencias runtime con pinning de versiones.

5. **Quitar imports muertos**: hay archivos en la raíz que ya no se usan (`daniela_v7_advanced.py`, `daniela_v8_cyber.py`, `daniela_v85_sovereignty.py`, `daniela_v9_core.py`, `daniela_v10_core.py`, etc.) — reducen la superficie de dependencias.
