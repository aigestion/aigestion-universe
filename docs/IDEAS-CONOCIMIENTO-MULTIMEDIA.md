# Ideas epicas: conocimiento multimedia para aig y Daniela

Objetivo: que Daniela obtenga contexto de TODOS los cuadernos de NotebookLM
y de cualquier fuente multimedia, con coste cero y corriendo en el mini PC.

> Nota honesta: los cuadernos de NotebookLM son privados (login Google, sin
> API publica). El flujo es exportar -> soltar en `data/notebooklm_inbox/` ->
> el ingestor lo convierte en conocimiento. Nada sale del PC.

## Estado: implementado (2026-10-01)

1. **Inbox universal** (`scripts/ai/notebooklm_ingest.py`):
   audio (.mp3/.wav/.m4a/.ogg/.opus/.flac/.webm) via faster-whisper CPU,
   PDF via pypdf, .txt/.md directos, YouTube via .url/.link o `--youtube`
   (yt-dlp + transcripcion). `--once` / `--watch`.
2. **Doble destino**: nota Markdown con frontmatter en `docs/NotebookLM/`
   (boveda Obsidian) + chunks en RAG (Qdrant) via `POST /api/rag/add`.
3. **Multi-cuaderno**: cada subcarpeta de inbox es un cuaderno ->
   coleccion propia `nb_<slug>` + subcarpeta en Obsidian + indice por cuaderno.
4. **Endpoint de contexto** (`POST /api/rag/context` en aig-ml:9810):
   `{"question": "...", "notebooks": [...]}` o sin filtro (= todos los
   cuadernos). Devuelve bloque de contexto con citas listo para prompts.
   **Es lo que Daniela llama para "obtener contexto de los cuadernos".**
5. `GET /api/rag/collections`: lista cuadernos indexados.

## Ideas epicas pendientes (ordenadas por valor/coste)

1. **Audio Overviews bidireccionales**: Daniela resume su propio vault con
   TTS (ElviraNeural, ya en .env) y re-ingiere el audio como memoria
   episodica. Cierra el loop conocimiento -> voz -> conocimiento.
2. **YouTube directo en chat**: pega un link y Daniela lo transcribe,
   resume y cita con timestamps (el ingestor ya sabe; falta el comando).
3. **Grafo semantico auto**: entidades extraidas de notas -> canvas de
   Obsidian + metadata en Qdrant para saltos entre cuadernos.
4. **Colecciones por proyecto**: namespace RAG por proyecto (aig, Pixel,
   gestorias) ademas de por cuaderno; `POST /api/rag/context` ya acepta
   lista arbitraria de colecciones.
5. **Voz de WhatsApp/Telegram -> memoria**: audios reenviados al inbox
   se transcriben y van a mem0 como memoria episodica fechada.
6. **Capturas del Pixel -> OCR -> RAG**: Termux comparte imagenes al inbox;
   anadir OCR (tesseract) al ingestor para `.png/.jpg`.
7. **Dedup semantica al ingerir**: antes de indexar, buscar si el contenido
   ya existe (score > 0.95) y saltarlo con aviso.
8. **Loop NotebookLM como profesor**: exportar vault a NotebookLM como
   fuentes -> generar Audio Overview -> reimportar el audio (ya soportado).
9. **Evaluacion de calidad**: cada respuesta RAG guarda fuentes; Langfuse
   puntua utilidad para reordenar (rerank) futuros contextos.
10. **Modo offline total en Pixel**: GGUF + Qdrant local en Termux con el
    mismo esquema `nb_<slug>` y sync diferido al mini PC.

## Como lo usa Daniela (ejemplo)

```bash
# 1. Exportar de NotebookLM y soltar en data/notebooklm_inbox/Mi Cuaderno/
# 2. Ingerir:
python scripts/ai/notebooklm_ingest.py --once
# 3. Daniela pide contexto (cualquier agente/servicio con HTTP):
curl -X POST http://localhost:9810/api/rag/context \
  -H "Content-Type: application/json" \
  -d '{"question": "que dice el cuaderno sobre X?", "top_k": 5}'
# 4. Pegar "context" en el prompt del LLM junto a la pregunta.
```

## Limites conocidos

- Transcripcion `tiny` es rapida pero imprecisa; usar `--model base/small`.
- El LLM local 1B sintetiza flojo en abstracto; con claves cloud válidas
  el mismo endpoint usa modelos grandes sin cambiar codigo.
- Sin claves Together/DeepInfra/Groq válidas, todo corre 100% local.
