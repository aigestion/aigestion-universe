import os
import json
import base64
import time
from email.message import EmailMessage
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from google import genai
from google.genai import types

BASE_DIR = os.path.expanduser("~/daniela-os")
TOKEN_PATH = os.path.join(BASE_DIR, "token.json")
VAULT_FILE = os.path.join(BASE_DIR, "memory_vault.json")

def save_draft_event(draft_info):
    vault = []
    if os.path.exists(VAULT_FILE):
        try:
            with open(VAULT_FILE, 'r') as f:
                vault = json.load(f)
        except: vault = []
    
    entry = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "type": "ghostwriter_draft_created",
        "data": draft_info
    }
    vault.append(entry)
    with open(VAULT_FILE, 'w') as f:
        json.dump(vault, f, indent=4)

def run(context):
    if not os.path.exists(TOKEN_PATH):
        return "❌ [GHOSTWRITER]: Falta token.json. Ejecuta auth_gdrive.py primero."

    try:
        creds = Credentials.from_authorized_user_file(TOKEN_PATH)
        gmail_service = build('gmail', 'v1', credentials=creds)
        ai_client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))

        # Consultar mensajes no leídos
        results = gmail_service.users().messages().list(
            userId='me', q='is:unread', maxResults=5
        ).execute()

        messages = results.get('messages', [])
        if not messages:
            return "✍️ [GHOSTWRITER]: No hay correos no leídos pendientes de borrador."

        created_drafts = []

        for msg in messages:
            m = gmail_service.users().messages().get(userId='me', id=msg['id'], format='full').execute()
            headers = m.get('payload', {}).get('headers', [])
            
            subject = next((h['value'] for h in headers if h['name'].lower() == 'subject'), 'Sin Asunto')
            sender = next((h['value'] for h in headers if h['name'].lower() == 'from'), 'Desconocido')
            thread_id = m.get('threadId')
            snippet = m.get('snippet', '')

            prompt = (
                f"Eres Daniela OS, la asistente ejecutiva autónoma del Comandante.\n"
                f"Redacta una respuesta profesional, formal y concisa en español para el siguiente correo entrante.\n\n"
                f"Remitente: {sender}\n"
                f"Asunto Original: {subject}\n"
                f"Extracto del mensaje: {snippet}\n\n"
                f"REGLAS:\n"
                f"- Escribe ÚNICAMENTE el cuerpo del mensaje de respuesta.\n"
                f"- No incluyas líneas de asunto ni firmas adicionales desestructuradas.\n"
                f"- Mantén un tono respetuoso, directo y corporativo."
            )

            try:
                # Motor cambiado a Gemini 3.7 Flash
                res = ai_client.models.generate_content(
                    model="gemini-3.7-flash",
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        timeout=10.0
                    )
                )
                draft_body = res.text.strip()
            except Exception:
                continue

            # Estructurar mensaje MIME para Gmail
            mime_message = EmailMessage()
            mime_message['To'] = sender
            mime_message['Subject'] = f"Re: {subject}" if not subject.lower().startswith("re:") else subject
            mime_message.set_content(draft_body)

            raw_message = base64.urlsafe_b64encode(mime_message.as_bytes()).decode('utf-8')

            draft_object = {
                'message': {
                    'raw': raw_message,
                    'threadId': thread_id
                }
            }

            draft = gmail_service.users().drafts().create(
                userId='me', body=draft_object
            ).execute()

            draft_id = draft.get('id')
            info = {
                "sender": sender,
                "subject": subject,
                "draft_id": draft_id
            }
            save_draft_event(info)

            created_drafts.append(f"• **Re: {subject}** para `{sender}` (Draft ID: `{draft_id}`)")

        if not created_drafts:
            return "✍️ [GHOSTWRITER]: No se requirió la generación de borradores para los correos revisados."

        return (
            "✍️ *[GHOSTWRITER EXECUTIVE (GEMINI 3.7 FLASH) - BORRADORES GENERADOS]*\n\n"
            "Se han redactado y guardado los siguientes borradores en tu Gmail:\n\n" +
            "\n".join(created_drafts)
        )

    except Exception as e:
        return f"❌ [GHOSTWRITER]: Error generando borradores: {str(e)}"
