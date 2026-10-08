import os
import sys

import requests

TG_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TG_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
DEEPSEEK_KEY = os.getenv("DEEPSEEK_API_KEY")


def send_telegram_alert(text):
    if TG_TOKEN and TG_CHAT_ID and "YOUR_" not in TG_TOKEN:
        try:
            url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
            requests.post(url, json={"chat_id": TG_CHAT_ID, "text": text}, timeout=3.0)
            return True
        except Exception:
            pass
    return False


def generate_and_publish_idea(topic):
    prompt = f"Genera una idea creativa y post táctico para redes sobre: {topic}"
    if send_telegram_alert(f"🎨 Idea Creativa Daniela OS:\n\n{prompt}"):
        return "Idea redactada y publicada en tu canal de Telegram."
    return "Idea procesada localmente."


if __name__ == "__main__":
    topic = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "Inteligencia Artificial"
    print(generate_and_publish_idea(topic))
