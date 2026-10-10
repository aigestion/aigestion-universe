import os
import json
import subprocess
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from google import genai
from google.genai import types

BASE_DIR = os.path.expanduser("~/daniela-os")
TOKEN_PATH = os.path.join(BASE_DIR, "token.json")

def notify_urgent_email(sender, subject, summary):
    try:
        subprocess.run([
            'termux-tts-speak',
            f"Atención. Correo urgente de {sender}."
        ], timeout=5)
    except Exception:
        pass

    try:
        subprocess.run([
            'termux-notification',
            '--title', f'🔥 [MAIL URGENTE]: {sender}',
            '--content', f'{subject}\n{summary}',
            '--priority', 'high',
            '--sound'
        ], timeout=5)
    except Exception:
        pass

def run(context):
    if not os.path.exists(TOKEN_PATH):
        return "❌ [MAIL SENTINEL]: Falta token.json. Ejecuta auth_gdrive.py primero."

    try:
        creds = Credentials.from_authorized_user_file(TOKEN_PATH)
        gmail_service = build('gmail', 'v1', credentials=creds)
        ai_client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))

        results = gmail_service.users().messages().list(
            userId='me', q='is:unread', maxResults=5
        ).execute()

        messages = results.get('messages', [])
        if not messages:
            return "📬 [MAIL SENTINEL]: Bandeja al día. No hay correos no leídos."

        report = []
        for msg in messages:
            m = gmail_service.users().messages().get(userId='me', id=msg['id'], format='full').execute()
            headers = m.get('payload', {}).get('headers', [])
            
            subject = next((h['value'] for h in headers if h['name'].lower() == 'subject'), 'Sin Asunto')
            sender = next((h['value'] for h in headers if h['name'].lower() == 'from'), 'Desconocido')
            snippet = m.get('snippet', '')

            prompt = (
                f"Analiza este correo entrante:\n"
                f"Remitente: {sender}\nAsunto: {subject}\nExtracto: {snippet}\n\n"
                f"Responde en JSON estricto con las claves:\n"
                f"- 'prioridad': 'URGENTE', 'NORMAL' o 'SPAM'\n"
                f"- 'resumen': 'resumen corto en 1 frase'\n"
            )

            prio, resumen = "NORMAL", snippet[:80]
            try:
                # Timeout de 8 segundos y modelo flash optimizado
                res = ai_client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        timeout=8.0,
                        response_mime_type="application/json"
                    )
                )
                analysis = json.loads(res.text.strip())
                prio = analysis.get("prioridad", "NORMAL")
                resumen = analysis.get("resumen", snippet[:80])
            except Exception:
                pass  # Fallback a clasificacion por defecto si la llamada expira

            if prio == "URGENTE":
                notify_urgent_email(sender, subject, resumen)
                report.append(f"🔥 *[URGENTE]* **{sender}**: {subject}\n  └ __{resumen}__")
            else:
                report.append(f"📩 *[{prio}]* **{sender}**: {subject}\n  └ _{resumen}_")

        return "📬 *[MAIL SENTINEL - TRIAGE NEURONAL]*\n\n" + "\n\n".join(report)

    except Exception as e:
        return f"❌ [MAIL SENTINEL]: Error procesando bandeja: {str(e)}"
