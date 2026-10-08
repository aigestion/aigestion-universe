import logging
import os

from cryptography.fernet import Fernet

KEY_FILE = os.path.expanduser("~/daniela-os/secret.key")
GRAPH_FILE = os.path.expanduser("~/daniela-os/graph_memory.json")
ENCRYPTED_FILE = os.path.expanduser("~/daniela-os/graph_memory.json.enc")


def _get_or_create_key():
    """Obtiene o genera la clave maestra de cifrado local (AES-Fernet)."""
    if not os.path.exists(KEY_FILE):
        key = Fernet.generate_key()
        with open(KEY_FILE, "wb") as f:
            f.write(key)
        os.chmod(KEY_FILE, 0o600)  # Permisos restringidos
    with open(KEY_FILE, "rb") as f:
        return f.read()


def encrypt_graph() -> bool:
    """Cifra graph_memory.json con la clave local."""
    if not os.path.exists(GRAPH_FILE):
        logging.error("No se encontró graph_memory.json para cifrar.")
        return False

    key = _get_or_create_key()
    fernet = Fernet(key)

    with open(GRAPH_FILE, "rb") as f:
        data = f.read()

    encrypted_data = fernet.encrypt(data)

    with open(ENCRYPTED_FILE, "wb") as f:
        f.write(encrypted_data)

    return True


def backup_to_gdrive() -> str:
    """Pipeline principal: Cifra localmente y simula/ejecuta la subida a Google Drive."""
    if not encrypt_graph():
        return "❌ [BACKUP]: Fallo al cifrar el Knowledge Graph."

    file_size = os.path.getsize(ENCRYPTED_FILE)

    # Verificación de credenciales de Google
    credentials_path = os.path.expanduser("~/daniela-os/credentials.json")
    if not os.path.exists(credentials_path):
        return f"🔐 [SOVEREIGN BACKUP]: Cifrado local EXITOSO ({file_size} bytes en 'graph_memory.json.enc'). Coloca 'credentials.json' para activar el envío a Google Drive."

    try:
        from google.oauth2.service_account import Credentials
        from googleapiclient.discovery import build
        from googleapiclient.http import MediaFileUpload

        creds = Credentials.from_service_account_file(
            credentials_path, scopes=["https://www.googleapis.com/auth/drive.file"]
        )
        service = build("drive", "v3", credentials=creds)

        file_metadata = {"name": "graph_memory.json.enc"}
        media = MediaFileUpload(ENCRYPTED_FILE, mimetype="application/octet-stream")

        uploaded = (
            service.files().create(body=file_metadata, mediaBody=media, fields="id").execute()
        )
        return f"☁️ [GOOGLE DRIVE]: Respaldo cifrado subido con éxito. File ID: {uploaded.get('id')}"

    except Exception as e:
        return f"⚠️ [BACKUP ERROR]: Cifrado correcto pero fallo al subir a Drive: {e}"


if __name__ == "__main__":
    print(backup_to_gdrive())
