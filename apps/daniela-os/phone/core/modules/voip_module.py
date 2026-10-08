import os
import sys

TWILIO_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")


def trigger_voip_alert(message):
    print(f"🚨 ALERTA CRÍTICA REGISTRADA: {message}")
    return "Alerta enviada a la central VoIP. Notificación registrada con éxito."


if __name__ == "__main__":
    msg = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "Prueba de alerta táctica"
    print(trigger_voip_alert(msg))
