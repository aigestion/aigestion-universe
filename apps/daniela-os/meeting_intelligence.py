"""
Meeting Intelligence
====================
Transcripcion, resumen ejecutivo y action items de reuniones.

Quick Win #5: Integra con edge-tts y sistema existente.
"""

import json
import logging
import os
import re
from dataclasses import dataclass
from datetime import datetime

logging.basicConfig(level=logging.INFO, format="%(asctime)s [MEETING] %(message)s")
logger = logging.getLogger(__name__)


@dataclass
class MeetingSummary:
    """Resumen de una reunion."""

    meeting_id: str
    title: str
    date: str
    duration_minutes: int
    participants: list[str]
    summary: str
    action_items: list[dict]
    key_decisions: list[str]
    next_meeting: str | None


class MeetingIntelligence:
    """Sistema de inteligencia para reuniones."""

    def __init__(self):
        self.history_file = "meeting_history.json"
        self.meetings = self._cargar_historial()

    def _cargar_historial(self) -> list[dict]:
        """Carga historial de reuniones."""
        if os.path.exists(self.history_file):
            with open(self.history_file, encoding="utf-8") as f:
                return json.load(f)
        return []

    def transcribir_audio(self, audio_path: str) -> str:
        """
        Transcribe audio de reunion a texto.
        Placeholder - en produccion usaria Whisper o similar.
        """
        logger.info(f"Transcribiendo: {audio_path}")
        # Simulacion de transcripcion
        return """
        [00:00] Juan: Buenos dias a todos. Hoy vamos a revisar el proyecto Alpha.
        [00:05] Maria: Si, tenemos el diseno listo pero necesitamos mas tiempo para testing.
        [00:12] Pedro: Yo puedo ayudar con los tests este fin de semana.
        [00:18] Juan: Perfecto. Entonces el lanzamiento sera el proximo martes.
        [00:25] Maria: De acuerdo. Tambien necesitamos actualizar la documentacion.
        [00:30] Pedro: Yo me encargo de eso.
        [00:35] Juan: Algo mas? No? Perfecto. Proxima reunion lunes que viene.
        """

    def extraer_participantes(self, transcript: str) -> list[str]:
        """Extrae lista de participantes de la transcripcion."""
        pattern = r"\[(\d{2}:\d{2})\]\s*(\w+):"
        matches = re.findall(pattern, transcript)
        participantes = list({m[1] for m in matches})
        return sorted(participantes)

    def extraer_action_items(self, transcript: str) -> list[dict]:
        """Extrae action items de la transcripcion."""
        action_items = []

        # Patrones de compromisos
        patterns = [
            r"(\w+):\s*(?:yo |voy a |me encargo de |hare |preparare)\s*(.+?)(?:\.|$)",
            r"(\w+):\s*(?:necesitamos|hay que|falta|pendiente)\s*(.+?)(?:\.|$)",
        ]

        for pattern in patterns:
            matches = re.finditer(pattern, transcript, re.IGNORECASE)
            for match in matches:
                persona = match.group(1)
                tarea = match.group(2).strip()

                # Detectar deadlines
                deadline = self._extraer_deadline(transcript, match.end())

                action_items.append(
                    {"person": persona, "task": tarea, "deadline": deadline, "status": "pending"}
                )

        return action_items

    def _extraer_deadline(self, transcript: str, position: int) -> str | None:
        """Extrae fecha limite cercana a una posicion."""
        context = transcript[position : position + 200]

        # Buscar referencias temporales
        patterns = [
            r"(lunes|martes|miercoles|jueves|viernes|proxima semana|mañana|este fin de semana)",
            r"(\d{1,2})\s+de\s+(enero|febrero|marzo|abril|mayo|junio|julio|agosto|septiembre|octubre|noviembre|diciembre)",
        ]

        for pattern in patterns:
            match = re.search(pattern, context, re.IGNORECASE)
            if match:
                return match.group(0)

        return None

    def extraer_decisiones(self, transcript: str) -> list[str]:
        """Extrae decisiones clave de la reunion."""
        decisiones = []

        # Patrones de decision
        patterns = [
            r"(?:queda|decidimos|se acordo|se decide|entonces|por lo tanto)\s*(.+?)(?:\.|$)",
            r"(?:el lanzamiento|la fecha|el deadline|la entrega)\s*(?:sera|es|queda en)\s*(.+?)(?:\.|$)",
        ]

        for pattern in patterns:
            matches = re.finditer(pattern, transcript, re.IGNORECASE)
            for match in matches:
                decision = match.group(0).strip()
                if len(decision) > 10:  # Filtrar muy cortos
                    decisiones.append(decision)

        return list(set(decisiones))  # Eliminar duplicados

    def generar_resumen(self, transcript: str, titulo: str = "Reunion") -> MeetingSummary:
        """Genera resumen completo de la reunion."""
        participantes = self.extraer_participantes(transcript)
        action_items = self.extraer_action_items(transcript)
        decisiones = self.extraer_decisiones(transcript)

        # Generar resumen en lenguaje natural
        puntos_clave = []
        if decisiones:
            puntos_clave.append(f"Se tomaron {len(decisiones)} decisiones clave")
        if action_items:
            puntos_clave.append(f"Se identificaron {len(action_items)} action items")

        resumen_texto = f"""Reunion: {titulo}
Participantes: {", ".join(participantes)}

Puntos clave:
{chr(10).join("- " + p for p in puntos_clave)}

Decisiones:
{chr(10).join("- " + d for d in decisiones)}

Próximos pasos:
{chr(10).join(f"- [{a['person']}] {a['task']}" + (f" (para: {a['deadline']})" if a['deadline'] else "") for a in action_items)}
"""

        meeting_id = f"MTG_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        summary = MeetingSummary(
            meeting_id=meeting_id,
            title=titulo,
            date=datetime.now().strftime("%Y-%m-%d"),
            duration_minutes=self._calcular_duracion(transcript),
            participants=participantes,
            summary=resumen_texto,
            action_items=action_items,
            key_decisions=decisiones,
            next_meeting=self._extraer_proxima_reunion(transcript),
        )

        # Guardar en historial
        self._guardar_reunion(summary)

        return summary

    def _calcular_duracion(self, transcript: str) -> int:
        """Calcula duracion estimada de la reunion."""
        times = re.findall(r"\[(\d{2}):(\d{2})\]", transcript)
        if len(times) >= 2:
            start = int(times[0][0]) * 60 + int(times[0][1])
            end = int(times[-1][0]) * 60 + int(times[-1][1])
            return max(end - start, 15)
        return 30

    def _extraer_proxima_reunion(self, transcript: str) -> str | None:
        """Extrae fecha de proxima reunion."""
        match = re.search(
            r"proxima reunion\s*(?:el|para)?\s*(.+?)(?:\.|$)", transcript, re.IGNORECASE
        )
        return match.group(1).strip() if match else None

    def _guardar_reunion(self, summary: MeetingSummary):
        """Guarda reunion en historial."""
        self.meetings.append(
            {
                "id": summary.meeting_id,
                "title": summary.title,
                "date": summary.date,
                "duration": summary.duration_minutes,
                "participants": summary.participants,
                "action_items": summary.action_items,
                "decisions": summary.key_decisions,
            }
        )

        with open(self.history_file, "w", encoding="utf-8") as f:
            json.dump(self.meetings, f, indent=2, ensure_ascii=False)

    def seguimiento_action_items(self) -> list[dict]:
        """Retorna action items pendientes de todas las reuniones."""
        pendientes = []
        for meeting in self.meetings:
            for item in meeting.get("action_items", []):
                if item.get("status") == "pending":
                    pendientes.append(
                        {
                            "meeting": meeting["title"],
                            "date": meeting["date"],
                            "person": item["person"],
                            "task": item["task"],
                            "deadline": item.get("deadline", "Sin fecha"),
                        }
                    )
        return pendientes

    def demo(self):
        """Demostracion de Meeting Intelligence."""
        print("=" * 60)
        print("MEETING INTELLIGENCE - DEMO")
        print("=" * 60)
        print()

        # Simular transcripcion
        transcript = """
        [00:00] Juan: Buenos dias a todos. Hoy vamos a revisar el proyecto Alpha.
        [00:05] Maria: Si, tenemos el diseno listo pero necesitamos mas tiempo para testing.
        [00:12] Pedro: Yo puedo ayudar con los tests este fin de semana.
        [00:18] Juan: Perfecto. Entonces el lanzamiento sera el proximo martes.
        [00:25] Maria: De acuerdo. Tambien necesitamos actualizar la documentacion.
        [00:30] Pedro: Yo me encargo de eso para el lunes.
        [00:35] Juan: Algo mas? No? Perfecto. Proxima reunion lunes que viene.
        """

        print("[1] Transcripcion de ejemplo:")
        print(transcript)
        print()

        print("[2] Generando resumen...")
        summary = self.generar_resumen(transcript, "Revision Proyecto Alpha")

        print(f"ID: {summary.meeting_id}")
        print(f"Titulo: {summary.title}")
        print(f"Duracion: {summary.duration_minutes} minutos")
        print(f"Participantes: {', '.join(summary.participants)}")
        print()

        print("[3] Action Items:")
        for item in summary.action_items:
            deadline = f" (para: {item['deadline']})" if item["deadline"] else ""
            print(f"  - [{item['person']}] {item['task']}{deadline}")
        print()

        print("[4] Decisiones Clave:")
        for dec in summary.key_decisions:
            print(f"  - {dec}")
        print()

        print("[5] Resumen Ejecutivo:")
        print(summary.summary)
        print()

        print("[6] Seguimiento de Action Items Pendientes:")
        pendientes = self.seguimiento_action_items()
        for p in pendientes:
            print(f"  - [{p['person']}] {p['task']} (de: {p['meeting']})")
        print()

        print("=" * 60)


if __name__ == "__main__":
    intel = MeetingIntelligence()
    intel.demo()
