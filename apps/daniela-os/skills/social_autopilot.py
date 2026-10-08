import json
import logging
import os
from datetime import datetime

QUEUE_FILE = os.path.expanduser("~/daniela-os/social_queue.json")


def _init_queue():
    if not os.path.exists(QUEUE_FILE):
        with open(QUEUE_FILE, "w", encoding="utf-8") as f:
            json.dump([], f, ensure_ascii=False)


def schedule_post(platform, content):
    """
    Skill #26: Social Autopilot.
    Añade un post a la cola de publicación automática.
    """
    _init_queue()
    try:
        with open(QUEUE_FILE, "r+", encoding="utf-8") as f:
            queue = json.load(f)
            item = {
                "id": len(queue) + 1,
                "platform": platform,
                "content": content,
                "status": "scheduled",
                "timestamp": datetime.now().isoformat(),
            }
            queue.append(item)
            f.seek(0)
            json.dump(queue, f, ensure_ascii=False, indent=2)
            f.truncate()
        return (
            f"📱 [SOCIAL AUTOPILOT]: Post programado para {platform.upper()} (ID: #{item['id']})."
        )
    except Exception as e:
        logging.error(f"Error en Social Autopilot: {e}")
        return f"⚠️ [AUTOPILOT ERROR]: {e}"


def list_queue():
    _init_queue()
    try:
        with open(QUEUE_FILE, encoding="utf-8") as f:
            queue = json.load(f)
        if not queue:
            return "📱 [SOCIAL AUTOPILOT]: La cola de publicaciones está vacía."
        posts = "\n".join(
            [f"• #{p['id']} [{p['platform'].upper()}]: {p['content'][:80]}..." for p in queue]
        )
        return f"📋 [COLA DE PUBLICACIONES]:\n{posts}"
    except Exception as e:
        return f"⚠️ [AUTOPILOT ERROR]: {e}"
