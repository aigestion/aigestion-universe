import json
import logging
import os
from datetime import datetime

POSTS_FILE = "social_posts.json"


def generate_social_content(topic):
    try:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Generador estructurado de contenido multimedial
        post_data = {
            "timestamp": timestamp,
            "topic": topic,
            "content": {
                "twitter_thread": [
                    f"🧵 1/3 {topic.capitalize()}: La revolución que está cambiando las reglas.",
                    "2/3 El impacto clave está en la automatización local y soberana.",
                    "3/3 ¿Qué opinas de este avance? Te leo en comentarios. 🚀",
                ],
                "linkedin_post": f"🚀 **{topic.upper()}**\n\nEl desarrollo de tecnología local nos permite escalar sin depender de infraestructuras de terceros. Puntos clave:\n\n• Soberanía de datos\n• Latencia cero\n• Control total\n\n¿Cómo lo estás aplicando en tu flujo de trabajo?",
                "reel_script": f"🎬 [HOOK]: ¿Sabías esto sobre {topic}?\n[BODY]: Explicación rápida de 15 segundos sobre la importancia de procesar localmente.\n[CTA]: Guarda este reel para después.",
            },
        }

        history = []
        if os.path.exists(POSTS_FILE):
            with open(POSTS_FILE, encoding="utf-8") as f:
                try:
                    history = json.load(f)
                except Exception:
                    history = []

        history.append(post_data)

        with open(POSTS_FILE, "w", encoding="utf-8") as f:
            json.dump(history, f, ensure_ascii=False, indent=2)

        logging.info(f"Post de redes generado para: {topic}")
        return f"📱 Contenido generado para '{topic}': Hilo X (3 tuits), Post LinkedIn y Script de Reel guardados en social_posts.json"
    except Exception as e:
        logging.error(f"Error generando post: {str(e)}")
        return "Error al procesar la estrategia de contenido."
