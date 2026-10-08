import os
import json
import base64
import time
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

BASE_DIR = os.path.expanduser("~/daniela-os")
TOKEN_PATH = os.path.join(BASE_DIR, "token.json")
TMP_DIR = os.path.join(BASE_DIR, "tmp_invoices")
VAULT_FILE = os.path.join(BASE_DIR, "memory_vault.json")

os.makedirs(TMP_DIR, exist_ok=True)

def get_or_create_drive_folder(drive_service, folder_name, parent_id=None):
    query = f"name = '{folder_name}' and mimeType = 'application/vnd.google-apps.folder' and trashed = false"
    if parent_id:
        query += f" and '{parent_id}' in parents"
    
    results = drive_service.files().list(q=query, fields="files(id, name)").execute()
    items = results.get('files', [])
    
    if items:
        return items[0]['id']
    
    folder_metadata = {
        'name': folder_name,
        'mimeType': 'application/vnd.google-apps.folder'
    }
    if parent_id:
        folder_metadata['parents'] = [parent_id]
        
    folder = drive_service.files().create(body=folder_metadata, fields='id').execute()
    return folder.get('id')

def save_to_vault(invoice_info):
    vault = []
    if os.path.exists(VAULT_FILE):
        try:
            with open(VAULT_FILE, 'r') as f:
                vault = json.load(f)
        except: vault = []
    
    entry = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "type": "invoice_extracted",
        "data": invoice_info
    }
    vault.append(entry)
    with open(VAULT_FILE, 'w') as f:
        json.dump(vault, f, indent=4)

def run(context):
    if not os.path.exists(TOKEN_PATH):
        return "❌ [INVOICE EXTRACTOR]: Falta token.json. Ejecuta auth_gdrive.py primero."

    try:
        creds = Credentials.from_authorized_user_file(TOKEN_PATH)
        gmail_service = build('gmail', 'v1', credentials=creds)
        drive_service = build('drive', 'v3', credentials=creds)

        # Buscar correos con adjuntos y palabras clave financieras
        query = 'has:attachment (factura OR invoice OR recibo OR ticket)'
        results = gmail_service.users().messages().list(userId='me', q=query, maxResults=5).execute()
        messages = results.get('messages', [])

        if not messages:
            return "🧾 [INVOICE EXTRACTOR]: No se encontraron facturas o recibos adjuntos pendientes."

        root_folder_id = get_or_create_drive_folder(drive_service, "Daniela_OS_Facturas")
        period_folder_name = time.strftime("%Y-%m")
        period_folder_id = get_or_create_drive_folder(drive_service, period_folder_name, parent_id=root_folder_id)

        processed_files = []

        for msg in messages:
            m = gmail_service.users().messages().get(userId='me', id=msg['id'], format='full').execute()
            payload = m.get('payload', {})
            parts = payload.get('parts', [])

            for part in parts:
                filename = part.get('filename')
                body = part.get('body', {})
                attachment_id = body.get('attachmentId')

                if filename and attachment_id:
                    ext = os.path.splitext(filename)[1].lower()
                    if ext in ['.pdf', '.jpg', '.jpeg', '.png']:
                        # Descargar adjunto desde Gmail
                        attachment = gmail_service.users().messages().attachments().get(
                            userId='me', messageId=msg['id'], id=attachment_id
                        ).execute()

                        file_data = base64.urlsafe_b64decode(attachment['data'].encode('UTF-8'))
                        local_filepath = os.path.join(TMP_DIR, filename)

                        with open(local_filepath, 'wb') as f:
                            f.write(file_data)

                        # Subir a Google Drive
                        media = MediaFileUpload(local_filepath, resumable=True)
                        drive_file_metadata = {
                            'name': f"[{time.strftime('%Y%m%d')}]_{filename}",
                            'parents': [period_folder_id]
                        }

                        drive_file = drive_service.files().create(
                            body=drive_file_metadata, media_body=media, fields='id, webViewLink'
                        ).execute()

                        # Limpiar archivo temporal
                        os.remove(local_filepath)

                        info = {
                            "filename": filename,
                            "drive_id": drive_file.get('id'),
                            "link": drive_file.get('webViewLink')
                        }
                        save_to_vault(info)
                        processed_files.append(f"• **{filename}** -> [Ver en Drive]({drive_file.get('webViewLink')})")

        if not processed_files:
            return "🧾 [INVOICE EXTRACTOR]: Correos analizados pero sin adjuntos en formato compatible (PDF/Imagen)."

        return (
            f"🧾 *[EXTRACTOR DE FACTURAS - GOOGLE DRIVE]*\n\n"
            f"📂 **Carpeta Destino:** `/Daniela_OS_Facturas/{period_folder_name}/`\n\n" +
            "\n".join(processed_files)
        )

    except Exception as e:
        return f"❌ [INVOICE EXTRACTOR]: Error durante la extracción: {str(e)}"
