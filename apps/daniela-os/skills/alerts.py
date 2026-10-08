import logging
import subprocess


def send_alert(title, content):
    try:
        cmd = [
            "termux-notification",
            "--title",
            f"Daniela OS: {title}",
            "--content",
            content,
            "--priority",
            "high",
        ]
        subprocess.run(cmd, capture_output=True)
        logging.info(f"Notificación enviada: {title} - {content}")
        return f"🔔 Alerta enviada a la barra de estado: '{title}'"
    except Exception as e:
        logging.error(f"Error enviando notificación: {str(e)}")
        return "Error al emitir la alerta en el dispositivo."
