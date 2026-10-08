import logging
from datetime import datetime

from skills import alerts, workspace

TRIAGE_LOG = "triage_history.json"


def analyze_and_triage_inbox(emails_raw):
    """
    Procesamiento de correos con análisis de urgencia.
    Clasifica en: CRÍTICO, FINANCIERO, INFORMATIVO o SPAM.
    """
    try:
        results = []
        critical_count = 0

        for item in emails_raw:
            subject = item.get("subject", "").lower()
            sender = item.get("sender", "Desconocido")

            if any(
                w in subject for w in ["urgente", "asunto crítico", "pago", "factura", "contrato"]
            ):
                category = "CRÍTICO"
                draft = f"Hola, he recibido tu mensaje referente a '{item.get('subject')}'. Lo revisaré a la brevedad."
                workspace.manage_gmail("Create Draft", draft)
                critical_count += 1
            elif "banco" in subject or "pago" in subject:
                category = "FINANCIERO"
            elif "newsletter" in subject or "oferta" in subject:
                category = "SPAM"
            else:
                category = "INFORMATIVO"

            results.append(
                {
                    "sender": sender,
                    "subject": item.get("subject"),
                    "category": category,
                    "time": datetime.now().strftime("%H:%M:%S"),
                }
            )

        if critical_count > 0:
            alerts.send_alert(
                "Gmail Sentinel",
                f"🚨 ¡Atención! {critical_count} correo(s) crítico(s) detectado(s). Borradores listos.",
            )

        return f"📩 [TRIAGE COMPLETADO]: {len(results)} correos procesados. {critical_count} urgentes con borrador generado."
    except Exception as e:
        logging.error(f"Error en Triage Sentinel: {e}")
        return f"Error en Triage: {e}"
