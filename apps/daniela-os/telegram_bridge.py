import json
import time

import telepot

# Inserta aquí tu TOKEN de BotFather
TOKEN = "TU_TOKEN_AQUI"
bot = telepot.Bot(TOKEN)


def listener(msg):
    content_type, chat_type, chat_id = telepot.glance(msg)
    if content_type == "text":
        nombre = msg["from"]["first_name"]
        texto = msg["text"]

        # Cargar Lista Blanca
        with open("family_whitelist.json") as f:
            whitelist = json.load(f)["familia"]

        # Si es familia, alertar en PIP
        if nombre in whitelist:
            alerta = {"remitente": nombre, "texto": texto}
            with open("current_alert.json", "w") as f:
                json.dump(alerta, f)
            print(f"✅ Alerta de {nombre} recibida.")


bot.message_loop(listener)
while True:
    time.sleep(10)
