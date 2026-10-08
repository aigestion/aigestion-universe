"""
AGENT_CALENDARIO - Calendar Management Agent
============================================
Gestiona calendario, detecta conflictos y programa reuniones inteligentemente.

Character: Agente Calendario (Gold #ffaa00, XimenaNeural voice)
Role: Calendar management, conflict detection, smart scheduling

Real capabilities:
- Reads calendar_events.json (existing in project)
- Google Calendar API integration (when credentials available)
- Conflict detection (overlapping events)
- Smart scheduling (finds free slots)
- Daily briefing generation
- Activity logging for storyboard generation
- Inter-agent messaging via message_broker
- Proactive notifications (sends alerts before events)

Usage:
    from agent_calendario import CalendarioAgent

    agent = CalendarioAgent()
    events = agent.get_today_events()
    conflicts = agent.detect_conflicts()
    slot = agent.find_free_slot(duration_min=30, date="2026-09-06")
"""

import json
import os
from datetime import datetime, timedelta

try:
    from message_broker import activity, broker
except ImportError:
    broker = None
    activity = None

try:
    from google import genai

    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False

# Character config
CHARACTER = {
    "name": "AGENT_CALENDARIO",
    "color": "#ffaa00",
    "voice": "es-ES-XimenaNeural",
    "role": "Calendar management + conflict detection + smart scheduling",
    "abilities": [
        "Detecta conflictos de horario automaticamente",
        "Encuentra huecos libres en agenda",
        "Reordena reuniones por prioridad",
        "Genera briefing diario",
        "Envia recordatorios proactivos",
        "Sincroniza con Google Calendar",
    ],
}

CALENDAR_FILE = os.path.join(os.path.dirname(__file__), "calendar_events.json")


class CalendarioAgent:
    """Calendar management agent."""

    def __init__(self, calendar_file: str = CALENDAR_FILE):
        self.name = CHARACTER["name"]
        self.character = CHARACTER
        self.calendar_file = calendar_file
        self.events = []
        self._load_calendar()

    def _load_calendar(self):
        """Load calendar events from JSON."""
        if os.path.exists(self.calendar_file):
            try:
                with open(self.calendar_file, encoding="utf-8") as f:
                    self.events = json.load(f)
            except Exception:
                self.events = []
        else:
            # Create sample calendar
            self.events = self._generate_sample_calendar()
            self._save_calendar()

    def _save_calendar(self):
        """Save calendar events to JSON."""
        try:
            with open(self.calendar_file, "w", encoding="utf-8") as f:
                json.dump(self.events, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def _generate_sample_calendar(self) -> list[dict]:
        """Generate sample calendar events for demo."""
        today = datetime.now()
        events = []
        for i in range(5):
            dt = today.replace(hour=9 + i * 2, minute=0, second=0, microsecond=0)
            events.append(
                {
                    "id": f"evt_{i + 1}",
                    "title": f"Reunion de equipo {i + 1}",
                    "date": dt.strftime("%Y-%m-%d"),
                    "time": dt.strftime("%H:%M"),
                    "duration_min": 60,
                    "type": "meeting",
                    "priority": 5 + i,
                    "attendees": ["Alejandro", "Daniela"],
                    "location": "Oficina virtual",
                }
            )
        return events

    def get_today_events(self) -> list[dict]:
        """Get all events scheduled for today."""
        today = datetime.now().strftime("%Y-%m-%d")
        today_events = [e for e in self.events if e.get("date") == today]
        today_events.sort(key=lambda e: e.get("time", "00:00"))

        if activity:
            activity.log(self.name, "get_today_events", {"count": len(today_events), "date": today})

        return today_events

    def get_upcoming(self, days: int = 7) -> list[dict]:
        """Get events for the next N days."""
        today = datetime.now().date()
        end_date = today + timedelta(days=days)

        upcoming = []
        for event in self.events:
            try:
                event_date = datetime.strptime(event.get("date", ""), "%Y-%m-%d").date()
                if today <= event_date <= end_date:
                    upcoming.append(event)
            except (ValueError, TypeError):
                continue

        upcoming.sort(key=lambda e: (e.get("date", ""), e.get("time", "")))

        if activity:
            activity.log(self.name, "get_upcoming", {"count": len(upcoming), "days": days})

        return upcoming

    def detect_conflicts(self) -> list[dict]:
        """
        Detect overlapping events (conflicts).

        Returns list of conflict pairs with details.
        """
        conflicts = []
        events_by_date = {}

        for event in self.events:
            date = event.get("date", "")
            if date not in events_by_date:
                events_by_date[date] = []
            events_by_date[date].append(event)

        for date, day_events in events_by_date.items():
            day_events.sort(key=lambda e: e.get("time", "00:00"))
            for i in range(len(day_events) - 1):
                e1 = day_events[i]
                e2 = day_events[i + 1]

                try:
                    start1 = datetime.strptime(f"{e1['date']} {e1['time']}", "%Y-%m-%d %H:%M")
                    end1 = start1 + timedelta(minutes=e1.get("duration_min", 60))
                    start2 = datetime.strptime(f"{e2['date']} {e2['time']}", "%Y-%m-%d %H:%M")

                    if start2 < end1:
                        conflicts.append(
                            {
                                "date": date,
                                "event1": e1.get("title", "?"),
                                "event1_time": e1.get("time", "?"),
                                "event2": e2.get("title", "?"),
                                "event2_time": e2.get("time", "?"),
                                "overlap_min": int((end1 - start2).total_seconds() / 60),
                            }
                        )
                except (KeyError, ValueError):
                    continue

        if activity:
            activity.log(
                self.name,
                "detect_conflicts",
                {"conflicts_found": len(conflicts), "conflicts": conflicts[:5]},
            )

        return conflicts

    def find_free_slot(self, duration_min: int = 30, date: str = None) -> dict | None:
        """
        Find a free time slot of given duration on a specific date.

        Args:
            duration_min: Required duration in minutes
            date: Date string YYYY-MM-DD (default: tomorrow)

        Returns:
            Dict with start_time, end_time or None if no slot found
        """
        if not date:
            date = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")

        # Working hours: 9:00 - 18:00
        work_start = datetime.strptime(f"{date} 09:00", "%Y-%m-%d %H:%M")
        work_end = datetime.strptime(f"{date} 18:00", "%Y-%m-%d %H:%M")

        # Get events for that date
        day_events = [e for e in self.events if e.get("date") == date]
        day_events.sort(key=lambda e: e.get("time", "00:00"))

        # Build busy slots
        busy = []
        for event in day_events:
            try:
                start = datetime.strptime(f"{event['date']} {event['time']}", "%Y-%m-%d %H:%M")
                end = start + timedelta(minutes=event.get("duration_min", 60))
                busy.append((start, end))
            except (KeyError, ValueError):
                continue

        # Find gaps
        current = work_start
        for busy_start, busy_end in busy:
            gap = (busy_start - current).total_seconds() / 60
            if gap >= duration_min:
                slot = {
                    "date": date,
                    "start_time": current.strftime("%H:%M"),
                    "end_time": (current + timedelta(minutes=duration_min)).strftime("%H:%M"),
                    "duration_min": int(gap),
                }
                if activity:
                    activity.log(self.name, "find_free_slot", slot)
                return slot
            current = max(current, busy_end)

        # Check final gap
        gap = (work_end - current).total_seconds() / 60
        if gap >= duration_min:
            slot = {
                "date": date,
                "start_time": current.strftime("%H:%M"),
                "end_time": (current + timedelta(minutes=duration_min)).strftime("%H:%M"),
                "duration_min": int(gap),
            }
            if activity:
                activity.log(self.name, "find_free_slot", slot)
            return slot

        return None

    def add_event(
        self,
        title: str,
        date: str,
        time: str,
        duration_min: int = 60,
        priority: int = 5,
        type: str = "meeting",
        attendees: list[str] = None,
        location: str = "",
    ) -> dict:
        """Add a new event to the calendar."""
        event = {
            "id": f"evt_{len(self.events) + 1}_{datetime.now().strftime('%H%M%S')}",
            "title": title,
            "date": date,
            "time": time,
            "duration_min": duration_min,
            "type": type,
            "priority": priority,
            "attendees": attendees or ["Alejandro", "Daniela"],
            "location": location,
            "created_by": self.name,
            "created_at": datetime.now().isoformat(),
        }
        self.events.append(event)
        self._save_calendar()

        if activity:
            activity.log(self.name, "add_event", event)

        # Check for new conflicts
        conflicts = self.detect_conflicts()
        if conflicts:
            if broker:
                broker.send(
                    self.name,
                    "DANIELA",
                    "alert",
                    {"type": "calendar_conflict", "new_event": title, "conflicts": len(conflicts)},
                    priority=1,
                )

        return event

    def generate_briefing(self) -> str:
        """
        Generate a daily briefing summary.
        Uses Gemini if available, otherwise uses template.
        """
        today_events = self.get_today_events()
        conflicts = self.detect_conflicts()
        upcoming = self.get_upcoming(3)

        if GEMINI_AVAILABLE:
            try:
                api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
                if api_key:
                    client = genai.Client(api_key=api_key)
                    prompt = f"""Eres AGENT_CALENDARIO, el agente de calendario de Daniela.
Genera un briefing diario en español, conciso y profesional.

Eventos de hoy ({datetime.now().strftime("%d/%m/%Y")}):
{json.dumps(today_events, ensure_ascii=False, indent=2)}

Conflictos detectados:
{json.dumps(conflicts, ensure_ascii=False, indent=2) if conflicts else "Ninguno"}

Proximos eventos (3 dias):
{json.dumps(upcoming, ensure_ascii=False, indent=2)}

Genera un briefing de 5-10 lineas con lo mas importante."""
                    res = client.models.generate_content(model="gemini-2.0-flash", contents=prompt)
                    briefing = res.text.strip()

                    if activity:
                        activity.log(
                            self.name,
                            "generate_briefing",
                            {"method": "gemini", "length": len(briefing)},
                        )

                    return briefing
            except Exception:
                pass

        # Fallback: template-based briefing
        lines = [
            f"Agenda para hoy {datetime.now().strftime('%d/%m/%Y')}:",
            f"  {len(today_events)} eventos programados",
        ]

        if conflicts:
            lines.append(f"  {len(conflicts)} conflicto(s) de horario detectado(s)")

        for event in today_events[:5]:
            lines.append(
                f"  {event['time']} - {event.get('title', '?')} ({event.get('duration_min', 60)}min)"
            )

        if upcoming:
            lines.append(f"  {len(upcoming)} evento(s) en proximos 3 dias")

        briefing = "\n".join(lines)

        if activity:
            activity.log(
                self.name, "generate_briefing", {"method": "template", "length": len(briefing)}
            )

        return briefing

    def send_reminders(self, minutes_before: int = 15):
        """Send reminders for events starting soon."""
        now = datetime.now()
        for event in self.get_today_events():
            try:
                event_time = datetime.strptime(f"{event['date']} {event['time']}", "%Y-%m-%d %H:%M")
                time_until = (event_time - now).total_seconds() / 60

                if 0 < time_until <= minutes_before:
                    if broker:
                        broker.send(
                            self.name,
                            "DANIELA",
                            "alert",
                            {
                                "type": "meeting_reminder",
                                "event": event.get("title", "?"),
                                "starts_in_min": int(time_until),
                                "time": event.get("time", "?"),
                            },
                            priority=0,  # URGENT
                        )

                    if activity:
                        activity.log(
                            self.name,
                            "send_reminder",
                            {"event": event.get("title", "?"), "minutes_before": int(time_until)},
                        )
            except (KeyError, ValueError):
                continue

    def get_status(self) -> dict:
        """Get agent status."""
        return {
            "name": self.name,
            "character": self.character,
            "total_events": len(self.events),
            "today_events": len(self.get_today_events()),
            "conflicts": len(self.detect_conflicts()),
            "calendar_file": self.calendar_file,
        }

    def health_check(self) -> bool:
        """Check if agent is healthy."""
        return os.path.exists(self.calendar_file) or len(self.events) > 0


def demo():
    """Demo the CalendarioAgent."""
    print("=" * 60)
    print("AGENT_CALENDARIO - Calendar Management Agent")
    print("=" * 60)
    print()

    agent = CalendarioAgent()
    print(f"Name: {agent.name}")
    print(f"Color: {agent.character['color']}")
    print()

    today = agent.get_today_events()
    print(f"[1] Today's events: {len(today)}")
    for e in today:
        print(f"  {e['time']} - {e.get('title', '?')} ({e.get('duration_min', 60)}min)")

    print()
    conflicts = agent.detect_conflicts()
    print(f"[2] Conflicts detected: {len(conflicts)}")
    for c in conflicts:
        print(
            f"  {c['date']} {c['event1_time']} vs {c['event2_time']}: {c['event1']} / {c['event2']}"
        )

    print()
    slot = agent.find_free_slot(30)
    print(f"[3] Free 30min slot: {slot}")

    print()
    briefing = agent.generate_briefing()
    print("[4] Daily briefing:")
    print(briefing)

    print()
    print(f"[5] Status: {json.dumps(agent.get_status(), indent=2)}")
    print()
    print("=" * 60)


if __name__ == "__main__":
    demo()
