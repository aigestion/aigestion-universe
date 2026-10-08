import logging

from skills import alerts, designer, rag, video, web


def run_deep_research(topic):
    try:
        logging.info(f"🤖 AGENTE: Iniciando Deep Research para '{topic}'")

        # 1. Búsqueda autónoma de fuentes
        source_url = "https://example.com"
        web_data = web.scrape_url(source_url)
        sources = [{"url": source_url, "content": web_data}]

        # 2. Creación de NotebookLM
        notebook = rag.create_notebook(topic, sources)

        # 3. Generación de Infografía Premium
        infographic_url = designer.generate_infographic(topic, notebook["key_insights"])

        # 4. Generación de Vídeo / Clip PIP
        video_url = video.generate_video_clip(f"presentacion sobre {topic}")

        # 5. Emisión de Alerta al dispositivo
        alerts.send_alert("Deep Research Completo", f"Informe y multimedia listos para '{topic}'")

        return {
            "status": "success",
            "topic": topic,
            "notebook": notebook,
            "infographic": infographic_url,
            "video_url": video_url,
            "summary_text": f"📊 **PROYECTO NOTEBOOKLM**: '{topic}'\n\n• Fuentes Analizadas: {len(sources)}\n• Infografía HD Generada\n• Clip Multimedia preparado en PIP Master\n\n**Insights:**\n"
            + "\n".join([f"  - {k}" for k in notebook["key_insights"]]),
        }
    except Exception as e:
        logging.error(f"Error en Agente Autónomo: {str(e)}")
        return {"status": "error", "message": str(e)}
