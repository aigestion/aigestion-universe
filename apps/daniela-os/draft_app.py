import importlib
import os
import pkgutil
import threading
import time

from flask import Flask, jsonify, request

from google import genai

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PLUGINS_DIR = os.path.join(BASE_DIR, "plugins")
app = Flask(__name__)
client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))

# Estado Global del Sentinel
SENTINEL_ALERT = "✅ Sistema estable."


def sentinel_daemon():
    global SENTINEL_ALERT
    sentinel = importlib.import_module("plugins.sentinel")
    while True:
        # Ejecutar chequeo cada 30 segundos
        result = sentinel.run(None)
        if result and "✅" not in result:
            SENTINEL_ALERT = result
        else:
            SENTINEL_ALERT = "✅ Sistema estable."
        time.sleep(30)


# Iniciar hilo de vigilancia
threading.Thread(target=sentinel_daemon, daemon=True).start()

loaded_plugins = {}
for _loader, module_name, _is_pkg in pkgutil.iter_modules([PLUGINS_DIR]):
    module = importlib.import_module(f"plugins.{module_name}")
    loaded_plugins[module_name] = module


@app.route("/api/alert", methods=["GET"])
def get_alert():
    return jsonify({"alert": SENTINEL_ALERT})


@app.route("/api/chat", methods=["POST"])
def chat_api():
    data = request.json or {}
    message = data.get("message", "")
    for name, module in loaded_plugins.items():
        if name in message.lower():
            return jsonify({"response": module.run(message), "agent": "PLUGIN"})
    response = client.models.generate_content(model="gemini-3.7-flash", contents=message)
    return jsonify({"response": response.text, "agent": "OPERATOR"})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8085)
