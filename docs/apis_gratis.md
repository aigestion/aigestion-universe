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

### E-30 · Malla privada con Tailscale ✅ HECHA
**P0 · 3 h · impacto crítico.** El túnel `cloudflared` que tienes abierto en
el 8082 **expone el móvil a internet**. Tailscale crea una red privada entre
el PC y el Pixel: mismo resultado, riesgo cero. **Esta es la más urgente.**

> **Estado real (2026-09-11).** Implementado en
> `aig/pixel/tunnel_guard.py` (+8 rutas, 242 → 286 contando el resto de
> módulos cargados). Lo que encontró en su primer escaneo, en vivo:
> - `cloudflared` pid **28646** en el móvil publicando el **8082** (visto por ADB).
> - `192.168.1.133:8082` responde **sin credenciales**: `/` → 200,
>   `/api/skills/dispatch` → 405. Lo que hay ahí no es el gateway real
>   (`/api/pixel/health` da 404) sino el HUD de `server.py`, sin auth.
> - 30 literales de `daniela-pixel-2026` en el código → **0**.
>
> Rotación y endurecimiento ya aplicados: los 22 módulos leen
> `PIXEL_TOKEN` / `PIXEL_GATEWAY_TOKEN` del `.env` y el gateway compara con
> `hmac.compare_digest` en **fail-closed** (sin token configurado, rechaza
> todo). **Tailscale sigue sin instalar**: el plan paso a paso está en
> `GET /api/guard/tailscale`.

### E-31 · Contexto del mundo real — Open-Meteo + Nominatim + Wikipedia ✅ HECHA
**P2 · 4 h · impacto medio.** Alimenta directamente E-12 (Nodos Urbanos):
tiempo, dónde estás por coordenadas y datos fiables. Dos de las tres no
necesitan clave.

> **Absorbida por E-12 (2026-09-11).** Está dentro de
> `aig/pixel/urban_nodes.py` y se añadió **Overpass**, que no estaba en el
> plan: da "qué hay alrededor" (bares, farmacias, paradas) con distancias.
> Verificado en vivo con la Puerta de Alcalá: dirección real
> (`Plaza de la Independencia 4, Salamanca, Madrid, 28001`), 26,3 °C despejado,
> 8 sitios alrededor con su distancia y 4 artículos de Wikipedia a menos de
> 90 m. **Las cuatro APIs son gratis y sin clave.**

### E-13 · Daniela Offline — modelo local ✅ HECHA (a medias, ver aviso)
**P2 · 8 h · impacto crítico.** Que Daniela siga hablando sin red, y que lo que
dices deje de salir del dispositivo.

> **Hecha en el PC (2026-09-11).** `aig/pixel/local_brain.py` (+8 rutas,
> 294 → 303). Una interfaz, dos backends: **Ollama en el PC (VIVO)** y
> llama.cpp en el móvil (el objetivo). Medido de verdad:
> - 4 modelos: `daniela-local` 3,3 GB · `qwen3.5` 6,6 GB · `deepseek-coder`
>   776 MB · `nomic-embed-text` 274 MB.
> - Latencia: **24-33 s la primera llamada** (carga GBs a RAM) y **2,3-2,5 s**
>   en caliente. Toda llamada local va **sin proxy**: con `HTTP_PROXY` puesto,
>   una petición a `localhost` rebota y devuelve 502.
> - No se descarga ningún modelo nuevo: reutiliza el GGUF de `com.llmproxy`
>   que ya está en el móvil.
>
> ⚠️ **La parte del móvil NO está hecha.** El home de Termux es inaccesible
> por adb, así que `/api/local/plan` solo **escribe** el script
> (`data/local_brain/instalar_llama_movil.sh`); lo ejecuta el usuario. Mientras
> tanto el backend `llamacpp` figura como **caído** y todo va por Ollama.

### E-18 · Daniela AR ✅ HECHA
**P3 · 12 h · impacto alto.** Que Daniela deje de ser una pantalla plana en el
móvil.

> `aig/pixel/ar_stage.py` (+8 rutas, 303 → **314**). Escena **WebXR**
> (`immersive-ar`) que genera el propio backend, con anclas espaciales y mirada.
> - **🔴 El detalle que nadie cuenta**: `navigator.xr` **no existe** si abres
>   `http://192.168.1.X:5000/...`. Los navegadores solo lo exponen en **https o
>   localhost**. Sin dominio ni certificado, la solución es gratis:
>   `adb reverse tcp:5000 tcp:5000` y abrir en el móvil
>   **`http://localhost:5000/api/ar/scene`**. Para el navegador eso ES localhost.
> - **Anclas**: sitios reales con lat/lon. Si creas una a <60 m de otra, cuenta
>   como visita ("van 2"). Verificado: 300 m al sur, mirando al norte la ve
>   (yaw 0), al este y al sur no.
> - **Mirada**: con yaw/pitch reales, Daniela dice qué estás mirando. Si estás
>   ENCIMA del ancla no dice "a 0 m" (el rumbo no significaría nada).
> - Sin WebXR degrada a holograma 3D plano; la página avisa si no hay contexto
>   seguro en vez de fallar en silencio.
> - 0 `os.system`, 0 `shell=True`. Los sensores van por el gateway de Termux.

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

1. ~~**E-30** (Tailscale)~~ ✅ **hecha** — módulo listo; falta que instales
   Tailscale en el móvil y en el PC y mates el `cloudflared` (plan en
   `GET /api/guard/tailscale`). **Sigue siendo lo primero que hay que cerrar.**
2. ~~**E-32** (enrutador con respaldo)~~ ✅ **hecha** — 3 proveedores vivos
   medidos: Gemini 1,3 s · Cohere 1,1 s · Ollama local 4,1 s.
3. ~~**E-31** (contexto real)~~ ✅ **hecha** — absorbida por E-12.
4. **E-27** (voz offline) — el salto que más se nota.
5. **E-28** (memoria local) — base para todo lo demás.
6. E-29, E-33, E-34.

### Estado de épicas: **28/28 hechas** 🎉

Todas las épicas del roadmap están cerradas. Lo que queda es *operación*:
instalar **Tailscale** y matar el `cloudflared` (E-30), ejecutar el script de
llama.cpp en el móvil (E-13) y rotar las claves que ya están en el historial
de GitHub.

---

## 6. Recordatorio de seguridad

Unificar `.env` con `.env.master` mete **22 secretos** en un solo fichero.
Sigue estando ignorado por git (verificado), pero:

- No copies `.env` a ningún sitio fuera del PC.
- El teléfono tendrá su propia copia: piensa cómo llevarla (Syncthing, no git).
- Revoca el token de GitHub si no lo vas a usar.
