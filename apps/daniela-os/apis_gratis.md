# APIs y Recursos Gratis — inventario y épicas nuevas

Análisis hecho el **2026-09-10** cruzando `.env.master` (656 variables) contra
los 1.605 ficheros del proyecto. Nada de esto es teoría: son conteos reales.

---

## 1. El diagnóstico de un vistazo

| | |
|---|---:|
| Variables en `.env.master` | 656 |
| Variables con pinta de clave/token/URL de servicio | 234 |
| **Referenciadas en algún fichero del proyecto** | **muy pocas** |
| APIs con clave real configurada y **sin usar** | **~20** |

**Conclusión: estás pagando 0 € por recursos que no consumes.** Tienes claves
reales de Anthropic, Cohere, ElevenLabs, HuggingFace, Pinecone, Supabase,
Google Maps, YouTube, Browserless, Make.com, Twilio, Discord… y **ningún
fichero del proyecto las menciona**.

---

## 2. Ya tienes la clave y NO la usas (oro sin tocar)

Verificado una por una contra todo el repo (`.py`, `.yml`, `.sh`, `.js`, `.ts`,
`.json`, `.html`):

| Clave | Estado | Qué te daría gratis |
|---|---|---|
| `GROQ_API_KEY` | ✅ **sí usada** | inferencia rapidísima |
| `TELEGRAM_BOT_TOKEN` | ✅ **sí usada** | bot de Daniela |
| `ANTHROPIC_API_KEY` | ❌ sin usar | Claude como cerebro de respaldo |
| `CLAUDE_API_KEY` | ❌ sin usar | ídem |
| `COHERE_API_KEY` | ❌ sin usar | reranking y embeddings |
| `ELEVENLABS_API_KEY` | ❌ sin usar | **voz de Daniela con calidad real** |
| `HUGGINGFACE_API_KEY` / `HF_TOKEN` | ❌ sin usar | miles de modelos gratis |
| `OPENROUTER_API_KEY` | ❌ sin usar | **acceso a muchos modelos con una sola clave** |
| `GOOGLE_MAPS_JS_API_KEY` | ❌ sin usar | mapas y rutas (clave para E-12) |
| `GOOGLE_*_YOUTUBE_API_KEY` | ❌ sin usar | búsqueda y datos de YouTube |
| `NASA_API_KEY` | ❌ sin usar | fotos astronómicas, efemérides |
| `PINECONE_API_KEY` | ❌ sin usar | memoria vectorial en la nube |
| `SUPABASE_URL` / keys | ❌ sin usar | base de datos + auth gratis |
| `BROWSERLESS_API_KEY` | ❌ sin usar | navegador headless sin montar nada |
| `MAKE_COM_API_KEY` | ❌ sin usar | automatizaciones tipo Zapier |
| `TWILIO_AUTH_TOKEN` | ❌ sin usar | SMS y WhatsApp |
| `DISCORD_WEBHOOK_URL` | ❌ sin usar | avisos a un canal |
| `MINIO_ACCESS_KEY` | ❌ sin usar | S3 propio |
| `OLLAMA_HOST` / `LOCAL_LLM_URL` | ❌ sin usar | **modelo local, coste cero** |
| `N8N_API_KEY` | ❌ sin usar | automatizaciones |
| `GITHUB_PERSONAL_ACCESS_TOKEN` | ❌ sin usar | 🔴 **revócala o úsala** |

> 🔴 La de GitHub es la más delicada: un token `ghp_` de 40 caracteres puede
> hacer push y borrar repositorios. Está en `.env.master` y en tu `.env`.
> **Si no la vas a usar, revócala hoy.**

---

## 3. APIs gratis que FALTAN y encajan con Daniela

Ninguna de estas está en tu `.env`. Todas tienen capa gratuita real:

### Sin clave ni registro (las mejores)

| API | Para qué |
|---|---|
| **Open-Meteo** | Tiempo y previsión. Sin clave, ~10.000 llamadas/día. |
| **Nominatim (OpenStreetMap)** | Geocodificación inversa: "calle X" → coordenadas. Imprescindible para E-12. |
| **Wikipedia / Wikidata** | Respuestas enciclopédicas sin alucinar. Sin clave. |
| **ntfy.sh** | **Notificaciones push al móvil sin cuenta, sin Firebase y sin coste.** Ideal para el Pixel. |
| **DuckDuckGo Instant Answer** | Respuestas rápidas. Sin clave. |

### Con clave gratuita

| API | Capa gratis | Para qué |
|---|---|---|
| **Brave Search** | 2.000 consultas/mes | Buscar en la web sin pagar |
| **Cerebras** | capa gratuita | Inferencia rapidísima de respaldo |
| **Cloudflare Workers AI** | 10.000 neuronas/día | Modelos en el edge, gratis |
| **Google Calendar / CalDAV** | cuota generosa | Que Daniela sepa tu agenda de verdad |
| **Google Fit** | gratis | Salud y actividad real del móvil |

### Locales y de coste cero absoluto (sin internet)

| Recurso | Para qué |
|---|---|
| **Piper TTS** | Voz de Daniela **offline** y natural |
| **OpenWakeWord** | Palabra de activación sin servicios en la nube |
| **Silero VAD** | Detectar cuándo hablas de verdad |
| **Argos Translate** | Traducción español↔inglés sin conexión |
| **FAISS / sqlite-vec** | Memoria vectorial **en el propio Pixel**, sin Pinecone |
| **Ollama / llama.cpp** | Modelo propio en local |

### Infraestructura

| Recurso | Para qué |
|---|---|
| **Tailscale** | Red privada PC↔Pixel, gratis hasta 100 dispositivos. **Sustituye al túnel cloudflared**, que hoy expone tu móvil a internet. |
| **Syncthing** | Sincronización de ficheros PC↔Pixel sin servidor |
| **Mosquitto (MQTT)** | Bus de sensores en casa |

---

## 4. Épicas nuevas (E-27 a E-34)

### E-27 · Voz offline total — Piper + OpenWakeWord + Silero
**P1 · 6 h · impacto alto.** Hoy Daniela depende de la nube para hablar.
En un Pixel sin cobertura, se queda muda. Con Piper (TTS local),
OpenWakeWord (activación) y Silero (VAD) funciona en modo avión.
`free_stack`: los tres son open source, coste 0.

### E-28 · Memoria vectorial en el dispositivo — FAISS / sqlite-vec
**P1 · 5 h · impacto alto.** Pinecone está configurado y sin usar, pero para
un móvil es mejor no depender de la red: FAISS o `sqlite-vec` dan búsqueda
semántica en local, sin latencia y sin cuota.

### E-29 · Avisos push sin Firebase — ntfy.sh
**P2 · 3 h · impacto alto.** Daniela puede avisarte aunque la app esté
cerrada. Sin cuenta, sin servidor, sin coste. `termux-notification` deja de
ser la única vía.

### E-30 · Malla privada con Tailscale
**P0 · 3 h · impacto crítico.** El túnel `cloudflared` que tienes abierto en
el 8082 **expone el móvil a internet**. Tailscale crea una red privada entre
el PC y el Pixel: mismo resultado, riesgo cero. **Esta es la más urgente.**

### E-31 · Contexto del mundo real — Open-Meteo + Nominatim + Wikipedia
**P2 · 4 h · impacto medio.** Alimenta directamente E-12 (Nodos Urbanos):
tiempo, dónde estás por coordenadas y datos fiables. Dos de las tres no
necesitan clave.

### E-32 · Enrutador de modelos con respaldo automático
**P1 · 4 h · impacto alto.** Si Gemini falla o se queda sin cuota, que caiga
solo a Groq → OpenRouter → Cerebras → Ollama local. Aprovecha las claves que
ya tienes paradas. Fin del "no me reconoce la API key" para siempre.

### E-33 · Agenda real — Google Calendar / CalDAV
**P2 · 4 h · impacto medio.** Una asistente que no sabe qué tienes hoy no es
una asistente. Memoria de citas de verdad.

### E-34 · Traducción offline — Argos Translate
**P3 · 2 h · impacto bajo.** Español↔inglés sin internet, útil sobre todo
viajando o sin datos.

---

## 5. Orden recomendado

1. **E-30** (Tailscale) — cierra el agujero del túnel expuesto. **Hoy.**
2. **E-32** (enrutador con respaldo) — usa las claves paradas y mata el bug de la API.
3. **E-27** (voz offline) — el salto que más se nota.
4. **E-28** (memoria local) — base para todo lo demás.
5. E-29, E-31, E-33, E-34.

---

## 6. Recordatorio de seguridad

Unificar `.env` con `.env.master` mete **22 secretos** en un solo fichero.
Sigue estando ignorado por git (verificado), pero:

- No copies `.env` a ningún sitio fuera del PC.
- El teléfono tendrá su propia copia: piensa cómo llevarla (Syncthing, no git).
- Revoca el token de GitHub si no lo vas a usar.
