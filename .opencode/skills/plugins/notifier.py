import subprocess

def run(context):
    msg = context
    title = "🤖 Daniela OS"
    
    # Extraer comando si viene formateado como "notifica <mensaje>"
    for prefix in ["notifica", "notificar", "notify", "alerta"]:
        if msg.lower().startswith(prefix):
            msg = msg[len(prefix):].strip()
            break

    if not msg:
        return "❌ [NOTIFIER]: Indica el mensaje para la notificación. Ejemplo: 'notifica Tarea completada'."

    # Soporte para formato "Título | Mensaje"
    if "|" in msg:
        parts = msg.split("|", 1)
        title = parts[0].strip()
        msg = parts[1].strip()

    try:
        # Comando de notificación nativa de Termux:API
        cmd = [
            'termux-notification',
            '--title', title,
            '--content', msg,
            '--priority', 'high',
            '--id', 'daniela_os_alert'
        ]
        subprocess.run(cmd, check=True)
        return f"🔔 [NOTIFIER]: Notificación enviada a la barra de estado: '{title} - {msg}'"
    except FileNotFoundError:
        return "❌ [NOTIFIER]: No se encuentra 'termux-notification'. Asegúrate de tener instalada la app Termux:API."
    except Exception as e:
        return f"❌ [NOTIFIER]: Error al enviar notificación: {str(e)}"
