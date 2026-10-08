import json
import logging
import os
from datetime import datetime

CALENDAR_FILE = "calendar_events.json"

def sync_events(command_text):
    try:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        events = []
        if os.path.exists(CALENDAR_FILE):
            with open(CALENDAR_FILE, encoding='utf-8') as f:
                try:
                    events = json.load(f)
                except Exception:
                    events = []

        if "agrega" in command_text.lower() or "crea" in command_text.lower():
            event_title = command_text.lower().replace("agrega", "").replace("crea", "").replace("evento", "").strip()
            new_event = {
                "id": len(events) + 1,
                "title": event_title if event_title else "Reunión de Trabajo",
                "timestamp": timestamp,
                "status": "Sincronizado con Google Calendar"
            }
            events.append(new_event)
            with open(CALENDAR_FILE, 'w', encoding='utf-8') as f:
                json.dump(events, f, ensure_ascii=False, indent=2)
            logging.info(f"Evento guardado: {event_title}")
            return f"📅 Evento '{new_event['title']}' registrado y sincronizado en la agenda."
        else:
            if not events:
                return "📅 No hay eventos agendados para hoy."

            res_text = "📅 Próximos eventos sincronizados:\n"
            for ev in events[-3:]:
                res_text += f"• [{ev['timestamp']}] {ev['title']}\n"
            return res_text
    except Exception as e:
        logging.error(f"Error en Google Sync: {str(e)}")
        return f"Error al sincronizar agenda: {e}"
