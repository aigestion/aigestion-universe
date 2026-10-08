#!/usr/bin/env python3
"""
aig Connector: Google Workspace
======================================
Integracion con Gmail, Calendar, Drive, Sheets para aig.

Features:
- Leer emails (con filtros)
- Crear eventos de calendario
- Listar/buscar archivos en Drive
- Leer/escribir Sheets

Requiere: credentials.json (OAuth2) o service account.

Autor: aig Team
"""

from __future__ import annotations

import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

# Importacion condicional de Google APIs
try:
    from google.auth.transport.requests import Request
    from google.oauth2 import service_account
    from google.oauth2.credentials import Credentials
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError  # noqa: F401
    GOOGLE_AVAILABLE = True
except ImportError:
    GOOGLE_AVAILABLE = False


class GoogleWorkspaceConnector:
    """Conector unificado para Google Workspace."""

    SCOPES = [
        "https://www.googleapis.com/auth/gmail.readonly",
        "https://www.googleapis.com/auth/gmail.send",
        "https://www.googleapis.com/auth/calendar",
        "https://www.googleapis.com/auth/drive.readonly",
        "https://www.googleapis.com/auth/spreadsheets",
    ]

    def __init__(self, credentials_path: str | None = None, service_account_path: str | None = None):
        self.credentials_path = credentials_path or os.getenv("GOOGLE_CREDENTIALS", "credentials.json")
        self.service_account_path = service_account_path or os.getenv("GOOGLE_SERVICE_ACCOUNT")
        self.creds: Any = None
        self._services: dict[str, Any] = {}

    def authenticate(self) -> bool:
        """Autentica con Google APIs."""
        if not GOOGLE_AVAILABLE:
            print("[Google] Librerias no instaladas. Ejecuta: pip install google-api-python-client google-auth")
            return False

        try:
            # Intentar service account primero (para servidores)
            if self.service_account_path and Path(self.service_account_path).exists():
                self.creds = service_account.Credentials.from_service_account_file(
                    self.service_account_path,
                    scopes=self.SCOPES
                )
                return True

            # OAuth2 user credentials
            token_path = Path(self.credentials_path).parent / "token.json"
            if token_path.exists():
                self.creds = Credentials.from_authorized_user_file(str(token_path), self.SCOPES)

            if not self.creds or not self.creds.valid:
                if self.creds and self.creds.expired and self.creds.refresh_token:
                    self.creds.refresh(Request())
                else:
                    # Necesita autenticacion interactiva (una vez)
                    print("[Google] Se requiere autenticacion. Visita: /auth/google")
                    return False

            return True
        except Exception as e:
            print(f"[Google] Error de autenticacion: {e}")
            return False

    def _get_service(self, name: str, version: str) -> Any:
        """Obtiene o crea un servicio de Google API."""
        key = f"{name}_{version}"
        if key not in self._services:
            if not self.creds:
                raise RuntimeError("No autenticado")
            self._services[key] = build(name, version, credentials=self.creds, cache_discovery=False)
        return self._services[key]

    # ── Gmail ─────────────────────────────────────────────────

    def gmail_list_messages(self, query: str = "", max_results: int = 10) -> list[dict[str, Any]]:
        """Lista emails con filtros."""
        service = self._get_service("gmail", "v1")
        results = service.users().messages().list(userId="me", q=query, maxResults=max_results).execute()
        messages = []
        for msg in results.get("messages", []):
            detail = service.users().messages().get(userId="me", id=msg["id"], format="metadata").execute()
            headers = {h["name"]: h["value"] for h in detail.get("payload", {}).get("headers", [])}
            messages.append({
                "id": msg["id"],
                "subject": headers.get("Subject", "(no subject)"),
                "from": headers.get("From", ""),
                "date": headers.get("Date", ""),
                "snippet": detail.get("snippet", "")[:100],
            })
        return messages

    def gmail_send(self, to: str, subject: str, body: str) -> dict[str, Any]:
        """Envia un email simple."""
        import base64
        from email.mime.text import MIMEText

        service = self._get_service("gmail", "v1")
        message = MIMEText(body)
        message["to"] = to
        message["subject"] = subject
        raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
        sent = service.users().messages().send(userId="me", body={"raw": raw}).execute()
        return {"id": sent["id"], "status": "sent"}

    # ── Calendar ──────────────────────────────────────────────

    def calendar_list_events(self, days: int = 7) -> list[dict[str, Any]]:
        """Lista eventos de los proximos N dias."""
        service = self._get_service("calendar", "v3")
        now = datetime.utcnow().isoformat() + "Z"
        future = (datetime.utcnow() + timedelta(days=days)).isoformat() + "Z"

        events_result = service.events().list(
            calendarId="primary",
            timeMin=now,
            timeMax=future,
            maxResults=50,
            singleEvents=True,
            orderBy="startTime"
        ).execute()

        return [
            {
                "id": e["id"],
                "summary": e.get("summary", "(sin titulo)"),
                "start": e["start"].get("dateTime", e["start"].get("date")),
                "end": e["end"].get("dateTime", e["end"].get("date")),
                "attendees": [a.get("email") for a in e.get("attendees", [])],
            }
            for e in events_result.get("items", [])
        ]

    def calendar_create_event(self, summary: str, start: str, end: str, attendees: list[str] | None = None) -> dict[str, Any]:
        """Crea un evento en el calendario."""
        service = self._get_service("calendar", "v3")
        event = {
            "summary": summary,
            "start": {"dateTime": start, "timeZone": "UTC"},
            "end": {"dateTime": end, "timeZone": "UTC"},
            "attendees": [{"email": e} for e in (attendees or [])],
        }
        created = service.events().insert(calendarId="primary", body=event).execute()
        return {"id": created["id"], "link": created.get("htmlLink", "")}

    # ── Drive ─────────────────────────────────────────────────

    def drive_list_files(self, query: str = "", page_size: int = 10) -> list[dict[str, Any]]:
        """Lista archivos en Google Drive."""
        service = self._get_service("drive", "v3")
        results = service.files().list(q=query, pageSize=page_size, fields="files(id,name,mimeType,modifiedTime)").execute()
        return [
            {
                "id": f["id"],
                "name": f["name"],
                "type": f["mimeType"],
                "modified": f["modifiedTime"],
            }
            for f in results.get("files", [])
        ]

    # ── Sheets ────────────────────────────────────────────────

    def sheets_read(self, spreadsheet_id: str, range_name: str) -> list[list[Any]]:
        """Lee datos de una hoja de calculo."""
        service = self._get_service("sheets", "v4")
        result = service.spreadsheets().values().get(spreadsheetId=spreadsheet_id, range=range_name).execute()
        return result.get("values", [])

    def sheets_write(self, spreadsheet_id: str, range_name: str, values: list[list[Any]]) -> dict[str, Any]:
        """Escribe datos en una hoja de calculo."""
        service = self._get_service("sheets", "v4")
        body = {"values": values}
        result = service.spreadsheets().values().update(
            spreadsheetId=spreadsheet_id,
            range=range_name,
            valueInputOption="RAW",
            body=body
        ).execute()
        return {"updated_cells": result.get("updatedCells", 0)}


# ═══════════════════════════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════════════════════════

def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Google Workspace Connector")
    parser.add_argument("--auth", action="store_true", help="Autenticar")
    parser.add_argument("--emails", action="store_true", help="Listar emails")
    parser.add_argument("--calendar", action="store_true", help="Listar eventos")
    parser.add_argument("--drive", action="store_true", help="Listar archivos")

    args = parser.parse_args()

    conn = GoogleWorkspaceConnector()

    if not conn.authenticate():
        print("[ERROR] No se pudo autenticar")
        return 1

    print("[OK] Autenticado con Google Workspace")

    if args.emails:
        emails = conn.gmail_list_messages("is:unread", max_results=5)
        print(f"\nEmails no leidos ({len(emails)}):")
        for e in emails:
            print(f"  - {e['subject']} | De: {e['from']}")

    if args.calendar:
        events = conn.calendar_list_events(days=7)
        print(f"\nEventos proximos ({len(events)}):")
        for ev in events:
            print(f"  - {ev['summary']} | {ev['start']}")

    if args.drive:
        files = conn.drive_list_files(page_size=5)
        print(f"\nArchivos recientes ({len(files)}):")
        for f in files:
            print(f"  - {f['name']} ({f['type']})")

    return 0


if __name__ == "__main__":
    sys.exit(main())
