import os


def init_google_tasks():
    client_id = os.getenv("GOOGLE_CLIENT_ID")
    client_secret = os.getenv("GOOGLE_CLIENT_SECRET")
    if not client_id or not client_secret:
        return "⚠️ Credenciales GOOGLE_CLIENT_ID / GOOGLE_CLIENT_SECRET no configuradas en .env"
    return "✅ Puente Google Workspace preparado."

if __name__ == "__main__":
    print(init_google_tasks())
