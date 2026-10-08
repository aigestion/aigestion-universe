import datetime
import os

from skills.workspace_triage import _get_workspace_services

SHEET_ID = os.environ.get("GOOGLE_SHEET_ID")


def log_event(category: str, message: str, status: str = "INFO") -> str:
    if not SHEET_ID:
        return "⚠️ [TELEMETRY]: Falta GOOGLE_SHEET_ID."

    _, drive_service = _get_workspace_services()  # Reutilizamos Auth
    # Usamos sheets service desde drive_service o importando sheets
    from googleapiclient.discovery import build

    _get_workspace_services()[0].credentials if hasattr(
        _get_workspace_services()[0], "credentials"
    ) else None

    # Nota: Para simplificar, asumimos que sheets está habilitado en GCP
    service = build(
        "sheets",
        "v4",
        credentials=_get_workspace_services()[0]._credentials
        if hasattr(_get_workspace_services()[0], "_credentials")
        else None,
    )

    timestamp = datetime.datetime.now().isoformat()
    values = [[timestamp, category, message, status]]

    try:
        service.spreadsheets().values().append(
            spreadsheetId=SHEET_ID, range="Logs!A1", valueInputOption="RAW", body={"values": values}
        ).execute()
        return "📊 [TELEMETRY]: Evento registrado en Sheets."
    except Exception as e:
        return f"❌ [TELEMETRY ERROR]: {e}"
