import logging
import os
import subprocess

from skills import alerts


def check_for_intruders():
    """
    Skill #25: Agente de Seguridad.
    Captura una imagen de urgencia y dispara una alerta de sistema.
    """
    frame_path = os.path.expanduser("~/daniela-os/static/security_alert.jpg")
    try:
        subprocess.run(["termux-camera-photo", "-c", "0", frame_path], check=True)
        alerts.send_alert("SEGURIDAD", "Posible intrusión detectada. Imagen capturada.")
        logging.info("Security Monitor: Alerta de intrusión activada.")
        return f"🚨 [SEGURIDAD]: Alerta activada. Foto capturada en {frame_path}"
    except Exception as e:
        logging.error(f"Error en Security Monitor: {e}")
        return f"⚠️ [SECURITY ERROR]: {e}"
