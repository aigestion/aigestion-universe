import os
from datetime import UTC
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# Scopes ampliados para todo el Google Workspace
SCOPES = [
    "https://www.googleapis.com/auth/drive",
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/calendar.readonly",
    "https://www.googleapis.com/auth/tasks",
]


def get_google_service(api_name, api_version):
    creds = None
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists("credentials.json"):
                return None
            flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
            creds = flow.run_local_server(port=0)
        with open("token.json", "w") as token:
            token.write(creds.to_json())

    return build(api_name, api_version, credentials=creds)


def search_drive_files(query_name=""):
    try:
        service = get_google_service("drive", "v3")
        if not service:
            return "Falta credentials.json."

        q = "trashed = false"
        if query_name:
            q += f" and name contains '{query_name}'"

        results = (
            service.files()
            .list(q=q, pageSize=5, fields="files(id, name, mimeType, webViewLink)")
            .execute()
        )

        files = results.get("files", [])
        if not files:
            return f"No encontré archivos en Drive sobre '{query_name}'."

        res = f"Encontré {len(files)} archivos en Drive: "
        for f in files:
            res += f"• {f['name']} "
        return res
    except Exception as e:
        return f"Error en Drive: {str(e)}"


def get_calendar_events():
    try:
        service = get_google_service("calendar", "v3")
        if not service:
            return "Google Calendar no configurado."

        # Obtener los siguientes 3 eventos
        from datetime import datetime

        now = datetime.now(UTC).isoformat()
        events_result = (
            service.events()
            .list(
                calendarId="primary",
                timeMin=now,
                maxResults=3,
                singleEvents=True,
                orderBy="startTime",
            )
            .execute()
        )
        events = events_result.get("items", [])

        if not events:
            return "No tienes eventos próximos en Google Calendar."

        res = "Tus próximos eventos son: "
        for event in events:
            start = event["start"].get("dateTime", event["start"].get("date"))
            res += f"• {event.get('summary', 'Sin título')} ({start}) "
        return res
    except Exception as e:
        return f"Error en Calendar: {str(e)}"


def scan_local_storage(search_term=""):
    base_paths = [
        os.path.expanduser("~/daniela-os/static/uploads"),
        "/sdcard/Download",
        "/sdcard/Documents",
    ]
    found_files = []
    for bp in base_paths:
        if os.path.exists(bp):
            for path in Path(bp).rglob("*"):
                if path.is_file():
                    if not search_term or search_term.lower() in path.name.lower():
                        found_files.append(path.name)
                        if len(found_files) >= 5:
                            break

    if not found_files:
        return "Sin coincidencias en archivos locales."
    return f"Archivos locales: {', '.join(found_files)}"
