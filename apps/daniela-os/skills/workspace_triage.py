import logging
import os

from google import genai

CREDENTIALS_PATH = os.path.expanduser("~/daniela-os/credentials.json")
TOKEN_PATH = os.path.expanduser("~/daniela-os/token.json")


def _get_workspace_services():
    """Autentica y devuelve los clientes de Gmail y Drive."""
    if not os.path.exists(CREDENTIALS_PATH) and not os.path.exists(TOKEN_PATH):
        return None, None
    try:
        from google.oauth2.credentials import Credentials
        from googleapiclient.discovery import build

        creds = None
        if os.path.exists(TOKEN_PATH):
            creds = Credentials.from_authorized_user_file(TOKEN_PATH)

        if not creds or not creds.valid:
            return None, None

        gmail_service = build("gmail", "v1", credentials=creds)
        drive_service = build("drive", "v3", credentials=creds)
        return gmail_service, drive_service
    except Exception as e:
        logging.error(f"Error al autenticar Workspace: {e}")
        return None, None


def process_unread_emails() -> str:
    """Lee correos no leídos, analiza importancia con Gemini y retorna un resumen."""
    gmail_service, _ = _get_workspace_services()
    if not gmail_service:
        return "🔐 [WORKSPACE TRIAGE]: Se requiere 'credentials.json' o 'token.json' configurado en la raíz para conectar con Google Workspace."

    try:
        results = (
            gmail_service.users()
            .messages()
            .list(userId="me", q="is:unread", maxResults=5)
            .execute()
        )
        messages = results.get("messages", [])

        if not messages:
            return "📥 [GMAIL]: No hay correos no leídos en la bandeja de entrada."

        summaries = []
        api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")

        for msg in messages:
            msg_data = gmail_service.users().messages().get(userId="me", id=msg["id"]).execute()
            snippet = msg_data.get("snippet", "")
            headers = msg_data.get("payload", {}).get("headers", [])
            subject = next(
                (h["value"] for h in headers if h["name"].lower() == "subject"), "Sin Asunto"
            )
            sender = next(
                (h["value"] for h in headers if h["name"].lower() == "from"), "Desconocido"
            )

            # Clasificación con Gemini
            if api_key:
                client = genai.Client(api_key=api_key)
                prompt = f"Analiza este email:\nDe: {sender}\nAsunto: {subject}\nTexto: {snippet}\n\nDetermina la categoría (LEAD, FACTURA, NOTIFICACION, SPAM) y genera un resumen de 1 línea."
                res = client.models.generate_content(model="gemini-3.6-flash", contents=prompt)
                analysis = res.text.strip()
            else:
                analysis = f"Categoría: PENDIENTE | Snippet: {snippet[:60]}"

            summaries.append(f"• De: {sender} | Asunto: {subject}\n  └ AI Analysis: {analysis}")

        return f"📬 [WORKSPACE TRIAGE]: {len(messages)} correo(s) procesado(s):\n\n" + "\n".join(
            summaries
        )

    except Exception as e:
        return f"❌ [GMAIL ERROR]: {e}"


if __name__ == "__main__":
    print(process_unread_emails())
