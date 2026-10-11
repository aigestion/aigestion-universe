#!/usr/bin/env python3
# shim_http.py - Shim HTTP para comunicación capas
# Source: indicaciones.txt conversacion 1 - Bridge Hermes/Daniela

import json

# Puerto Shim HTTP. 5001 para no chocar con daniela_os.py, que es el
# backend canonico en el 5000 (el que usa la app Android).
# Se puede sobreescribir con la variable de entorno SHIM_PORT.
import os as _os
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

SHIM_PORT = int(_os.getenv("SHIM_PORT", "5001"))

# Puente entre capas (Hermes ↔ Daniela)
class ShimHandler(BaseHTTPRequestHandler):
    request_queue_size = 5

    def do_GET(self):
        if self.path == "/health":
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"status": "healthy", "port": SHIM_PORT}).encode())
        elif self.path == "/status":
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"status": "operational", "layers": ["hermes", "daniela", "agents"]}).encode())
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length)

        # Ruteo simple de mensajes entre capas
        try:
            mensaje = json.loads(body)
            origen = mensaje.get("origen", "unknown")
            destino = mensaje.get("destino", "unknown")
            accion = mensaje.get("accion", "unknown")

            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({
                "status": "received",
                "origen": origen,
                "destino": destino,
                "accion": accion,
                "shim_port": SHIM_PORT
            }).encode())
        except json.JSONDecodeError:
            self.send_response(400)
            self.end_headers()

    def log_message(self, format, *args):
        # Silenciar logs por defecto para reducir ruido
        pass

# Servidor Shim
shim_server = HTTPServer(("0.0.0.0", SHIM_PORT), ShimHandler)

def iniciar_shim():
    """Iniciar shim HTTP en hilo separado"""
    thread = threading.Thread(target=shim_server.serve_forever, daemon=True)
    thread.start()
    print(f"Shim HTTP iniciado en puerto {SHIM_PORT}")

def detener_shim():
    """Detener servidor Shim"""
    shim_server.server_close()

# Funciones de ayuda para routing entre capas
def enviar_a_daniela(mensaje):
    print(f"[SHIM] Enviando a Daniela: {mensaje}")


def enviar_a_hermes(mensaje):
    print(f"[SHIM] Enviando a Hermes: {mensaje}")


def enviar_a_agentes(mensaje):
    print(f"[SHIM] Enviando a Agentes: {mensaje}")

# Punto de entrada
if __name__ == "__main__":
    iniciar_shim()
    print("Shim HTTP activo. Esperando conexiones...")
    try:
        import time
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        detener_shim()
        print("Shim HTTP detenido")
