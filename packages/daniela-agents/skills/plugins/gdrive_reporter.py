import os
import datetime
import importlib

def run(context):
    try:
        # 1. Obtener la Reflexión Neuronal de Gemini 3.7 Flash
        analyzer = importlib.import_module('plugins.memory_analyzer')
        content = analyzer.run("analizar")
        
        # 2. Verificar existencia de credenciales de Google
        creds_path = os.path.expanduser('~/daniela-os/credentials.json')
        token_path = os.path.expanduser('~/daniela-os/token.json')
        
        if not (os.path.exists(creds_path) or os.path.exists(token_path)):
            # Fallback: Guardar copia estructurada local mientras se configuran los tokens
            local_dir = os.path.expanduser('~/daniela-os/drive_reports')
            os.makedirs(local_dir, exist_ok=True)
            report_file = os.path.join(local_dir, f"Informe_{datetime.date.today()}.md")
            
            with open(report_file, 'w') as f:
                f.write(content)
                
            return (
                f"📝 [GDRIVE FALLBACK]: Reporte generado localmente en `{report_file}`.\n"
                f"💡 Coloca tu `credentials.json` en `~/daniela-os/` para sincronización directa con Google Drive."
            )

        # 3. Importar librerías de Google si están instaladas
        from google.oauth2.credentials import Credentials
        from googleapiclient.discovery import build

        SCOPES = ['https://www.googleapis.com/auth/documents', 'https://www.googleapis.com/auth/drive.file']
        creds = Credentials.from_authorized_user_file(token_path, SCOPES)
        
        service_docs = build('docs', 'v1', credentials=creds)

        title = f"Daniela OS - Informe Táctico - {datetime.date.today()}"
        doc = service_docs.documents().create(body={'title': title}).execute()
        doc_id = doc.get('documentId')

        requests = [{'insertText': {'text': content, 'location': {'index': 1}}}]
        service_docs.documents().batchUpdate(documentId=doc_id, body={'requests': requests}).execute()

        return f"✅ [GDRIVE]: Diario de Operaciones exportado a Google Docs. ID: `{doc_id}`"

    except Exception as e:
        return f"❌ [GDRIVE]: Error durante el reporte a Drive: {str(e)}"
