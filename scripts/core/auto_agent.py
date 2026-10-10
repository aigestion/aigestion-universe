import json
import os
import urllib.request

LOG_PATH = os.path.expanduser('~/daniela-os/server.log')

def inspect_server_errors():
    """Lee las últimas líneas del log buscando excepciones no capturadas."""
    if not os.path.exists(LOG_PATH):
        return "Sin registro de errores."
    try:
        with open(LOG_PATH) as f:
            lines = f.readlines()
            errors = [line for line in lines if "Error" in line or "Exception" in line or "Traceback" in line]
            return "".join(errors[-10:]) if errors else "Sistemas operando sin errores detectados."
    except Exception as e:
        return f"Error leyendo logs: {str(e)}"

def send_iot_webhook(endpoint_url, payload_dict):
    """Envía comandos a dispositivos inteligentes en la red local."""
    try:
        data = json.dumps(payload_dict).encode('utf-8')
        req = urllib.request.Request(endpoint_url, data=data, headers={'Content-Type': 'application/json'}, method='POST')
        with urllib.request.urlopen(req, timeout=3) as response:
            return f"Webhook enviado con éxito (Status: {response.status})"
    except Exception as e:
        return f"Fallo al enviar Webhook IoT: {str(e)}"
