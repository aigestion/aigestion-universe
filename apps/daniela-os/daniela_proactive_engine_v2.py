"""
Daniela Proactive Engine v2
============================
Anticipa necesidades del usuario basandose en:
- Calendario y eventos proximos
- Tareas pendientes
- Patrones historicos
- Contexto actual (hora, dia, ubicacion)

Quick Win #1: Alto impacto, bajo esfuerzo.
"""

import asyncio
import json
import logging
import os
import time
from datetime import datetime, timedelta

# Configuracion de logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [PROACTIVE] %(message)s",
    handlers=[logging.FileHandler("proactive_engine.log"), logging.StreamHandler()],
)
logger = logging.getLogger(__name__)


class ProactiveEngine:
    """Motor proactivo de Daniela v2."""

    def __init__(self):
        self.calendar_file = "calendar_events.json"
        self.tasks_file = "tasks.json"
        self.diario_file = "diario_tactico.json"
        self.intervalo_segundos = 300  # 5 minutos
        self.alertas_enviadas = set()  # Evitar duplicados

    def cargar_calendario(self) -> list[dict]:
        """Carga eventos del calendario."""
        if not os.path.exists(self.calendar_file):
            return []
        try:
            with open(self.calendar_file, encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error cargando calendario: {e}")
            return []

    def cargar_tareas(self) -> list[dict]:
        """Carga tareas pendientes."""
        if not os.path.exists(self.tasks_file):
            return []
        try:
            with open(self.tasks_file, encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error cargando tareas: {e}")
            return []

    def cargar_diario(self) -> list[dict]:
        """Carga historial de eventos."""
        if not os.path.exists(self.diario_file):
            return []
        try:
            with open(self.diario_file, encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error cargando diario: {e}")
            return []

    def analizar_eventos_proximos(self, minutos_ventana: int = 30) -> list[dict]:
        """
        Analiza eventos que ocurren en la proxima ventana de tiempo.

        Args:
            minutos_ventana: Minutos hacia adelante para analizar

        Returns:
            Lista de eventos proximos con prioridad
        """
        eventos = self.cargar_calendario()
        ahora = datetime.now()
        ventana = ahora + timedelta(minutes=minutos_ventana)

        eventos_proximos = []
        for evento in eventos:
            try:
                # Parsear fecha/hora del evento
                fecha_evento = self._parsear_fecha(evento.get("fecha", ""), evento.get("hora", ""))
                if not fecha_evento:
                    continue

                # Si el evento esta en la ventana de tiempo
                if ahora <= fecha_evento <= ventana:
                    minutos_restantes = (fecha_evento - ahora).total_seconds() / 60

                    eventos_proximos.append(
                        {
                            "titulo": evento.get("titulo", "Evento sin titulo"),
                            "fecha": fecha_evento,
                            "minutos_restantes": int(minutos_restantes),
                            "tipo": evento.get("tipo", "general"),
                            "participantes": evento.get("participantes", []),
                            "ubicacion": evento.get("ubicacion", ""),
                            "prioridad": self._calcular_prioridad(evento, minutos_restantes),
                        }
                    )
            except Exception as e:
                logger.warning(f"Error procesando evento: {e}")
                continue

        # Ordenar por prioridad (mayor primero)
        eventos_proximos.sort(key=lambda x: x["prioridad"], reverse=True)
        return eventos_proximos

    def _parsear_fecha(self, fecha_str: str, hora_str: str) -> datetime | None:
        """Parsea string de fecha/hora a objeto datetime."""
        formatos = ["%Y-%m-%d %H:%M", "%d/%m/%Y %H:%M", "%Y-%m-%dT%H:%M", "%d-%m-%Y %H:%M"]

        for formato in formatos:
            try:
                return datetime.strptime(f"{fecha_str} {hora_str}", formato)
            except ValueError:
                continue

        # Intentar solo con fecha (asume hora actual)
        if fecha_str and not hora_str:
            try:
                fecha = datetime.strptime(fecha_str, "%Y-%m-%d").date()
                return datetime.combine(fecha, datetime.now().time())
            except ValueError:
                pass

        return None

    def _calcular_prioridad(self, evento: dict, minutos_restantes: float) -> int:
        """Calcula prioridad de un evento (0-100)."""
        prioridad = 50  # Base

        # Factor urgencia temporal
        if minutos_restantes <= 5:
            prioridad += 30
        elif minutos_restantes <= 15:
            prioridad += 20
        elif minutos_restantes <= 30:
            prioridad += 10

        # Factor tipo de evento
        tipo = evento.get("tipo", "").lower()
        if tipo in ["reunion", "llamada", "videollamada", "entrevista"]:
            prioridad += 15
        elif tipo in ["deadline", "vencimiento", "entrega"]:
            prioridad += 25
        elif tipo in ["cumpleanos", "aniversario"]:
            prioridad += 10

        # Factor participantes importantes
        participantes = evento.get("participantes", [])
        if any(p in ["jefe", "ceo", "director", "cliente"] for p in participantes):
            prioridad += 10

        return min(prioridad, 100)

    def generar_recomendacion(self, evento: dict) -> str:
        """Genera una recomendacion proactiva para un evento."""
        titulo = evento["titulo"]
        minutos = evento["minutos_restantes"]
        tipo = evento["tipo"]
        participantes = evento.get("participantes", [])
        ubicacion = evento.get("ubicacion", "")

        # Templates de recomendaciones
        if minutos <= 5:
            if tipo in ["reunion", "llamada", "videollamada"]:
                return f"URGENTE: Reunion '{titulo}' en {minutos} minutos. Preparate!"
            else:
                return f"URGENTE: '{titulo}' en {minutos} minutos."

        elif minutos <= 15:
            if ubicacion:
                return f"En {minutos} minutos: '{titulo}' en {ubicacion}. Tiempo de salir!"
            elif participantes:
                nombres = ", ".join(participantes[:2])
                return f"En {minutos} min: reunion con {nombres}. Preparar agenda?"
            else:
                return f"En {minutos} minutos: '{titulo}'. Revisa los detalles."

        elif minutos <= 30:
            if tipo in ["deadline", "vencimiento"]:
                return f"Recordatorio: '{titulo}' vence en {minutos} minutos."
            else:
                return f"Pronto: '{titulo}' en {minutos} minutos."

        else:
            return f"Recordatorio: '{titulo}' en {minutos} minutos."

    def detectar_tareas_urgentes(self) -> list[dict]:
        """Detecta tareas que necesitan atencion."""
        tareas = self.cargar_tareas()
        ahora = datetime.now()
        urgentes = []

        for tarea in tareas:
            if tarea.get("completada", False):
                continue

            # Calcular urgencia
            urgencia = 0
            fecha_limite = tarea.get("fecha_limite", "")
            if fecha_limite:
                try:
                    fecha = datetime.strptime(fecha_limite, "%Y-%m-%d")
                    dias_restantes = (fecha - ahora).days
                    if dias_restantes < 0:
                        urgencia = 100  # Vencida
                    elif dias_restantes == 0:
                        urgencia = 90  # Vence hoy
                    elif dias_restantes <= 2:
                        urgencia = 70  # Vence pronto
                except ValueError:
                    pass

            # Factor prioridad explicita
            prioridad = tarea.get("prioridad", "media").lower()
            if prioridad == "alta":
                urgencia += 20
            elif prioridad == "baja":
                urgencia -= 10

            if urgencia > 50:
                urgentes.append(
                    {
                        "titulo": tarea.get("titulo", "Tarea sin titulo"),
                        "urgencia": urgencia,
                        "fecha_limite": fecha_limite,
                        "dias_restantes": dias_restantes if "dias_restantes" in locals() else None,
                    }
                )

        urgentes.sort(key=lambda x: x["urgencia"], reverse=True)
        return urgentes[:5]  # Top 5

    def analizar_patrones(self) -> list[str]:
        """Analiza patrones del usuario para sugerencias."""
        diario = self.cargar_diario()
        sugerencias = []

        if not diario:
            return sugerencias

        # Analizar hora actual vs patrones historicos
        hora_actual = datetime.now().hour

        # Detectar si hay un patron de reuniones a esta hora
        eventos_misma_hora = [
            e for e in diario if e.get("hora", "").startswith(f"{hora_actual:02d}")
        ]

        if len(eventos_misma_hora) >= 3:
            sugerencias.append(
                f"Sueles tener actividades a las {hora_actual}:00h. Revisa tu agenda."
            )

        # Detectar tareas recurrentes no completadas
        titulos_recurrentes = {}
        for entrada in diario:
            titulo = entrada.get("detalle", "")
            if titulo:
                titulos_recurrentes[titulo] = titulos_recurrentes.get(titulo, 0) + 1

        for titulo, frecuencia in titulos_recurrentes.items():
            if frecuencia >= 5 and "pendiente" in titulo.lower():
                sugerencias.append(
                    f"Tarea recurrente pendiente: '{titulo}'. Considera priorizarla."
                )

        return sugerencias

    async def ciclo_proactivo(self):
        """Ciclo principal del motor proactivo."""
        logger.info("Daniela Proactive Engine v2 iniciado")

        while True:
            try:
                alertas = []

                # 1. Analizar eventos proximos
                eventos = self.analizar_eventos_proximos(minutos_ventana=60)
                for evento in eventos:
                    alerta_id = f"{evento['titulo']}_{evento['minutos_restantes']}"
                    if alerta_id not in self.alertas_enviadas:
                        recomendacion = self.generar_recomendacion(evento)
                        alertas.append(recomendacion)
                        self.alertas_enviadas.add(alerta_id)

                # 2. Detectar tareas urgentes
                tareas = self.detectar_tareas_urgentes()
                for tarea in tareas:
                    alertas.append(
                        f"TAREA URGENTE: '{tarea['titulo']}' (Urgencia: {tarea['urgencia']}/100)"
                    )

                # 3. Analizar patrones
                sugerencias = self.analizar_patrones()
                alertas.extend(sugerencias)

                # 4. Emitir alertas
                if alertas:
                    for alerta in alertas:
                        logger.info(f"[ALERTA] {alerta}")
                        # Aqui se conectaria con el sistema de voz/notificaciones
                        self._emitir_alerta(alerta)
                else:
                    logger.debug("Sin alertas en este ciclo")

                # Limpiar alertas antiguas (mas de 2 horas)
                self._limpiar_alertas_antiguas()

                # Esperar hasta el siguiente ciclo
                await asyncio.sleep(self.intervalo_segundos)

            except Exception as e:
                logger.error(f"Error en ciclo proactivo: {e}")
                await asyncio.sleep(self.intervalo_segundos)

    def _emitir_alerta(self, mensaje: str):
        """Emite una alerta al usuario (placeholder para integracion con voz/UI)."""
        # TODO: Integrar con sistema de voz (edge-tts)
        # TODO: Integrar con notificaciones del sistema
        # TODO: Integrar con UI/webhook

        # Guardar en log estructurado
        alerta = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "mensaje": mensaje,
            "tipo": "proactive_alert",
        }

        try:
            with open("proactive_alerts.json", "a", encoding="utf-8") as f:
                f.write(json.dumps(alerta, ensure_ascii=False) + "\n")
        except Exception as e:
            logger.error(f"Error guardando alerta: {e}")

    def _limpiar_alertas_antiguas(self):
        """Limpia alertas enviadas hace mas de 2 horas."""
        # Simplificacion: limpiar todas las alertas cada 2 horas
        # En produccion se usaria timestamp por alerta

    def demo(self):
        """Ejecuta una demostracion del motor proactivo."""
        print("=" * 60)
        print("DANIELA PROACTIVE ENGINE v2 - DEMO")
        print("=" * 60)
        print()

        # Simular datos de prueba
        print("[1] Analizando eventos proximos (proxima hora)...")
        eventos = self.analizar_eventos_proximos(minutos_ventana=60)
        if eventos:
            print(f"    Encontrados {len(eventos)} eventos:")
            for e in eventos[:3]:
                print(
                    f"    - {e['titulo']} en {e['minutos_restantes']} min (Prioridad: {e['prioridad']})"
                )
                print(f"      -> {self.generar_recomendacion(e)}")
        else:
            print("    Sin eventos proximos")
        print()

        print("[2] Detectando tareas urgentes...")
        tareas = self.detectar_tareas_urgentes()
        if tareas:
            print(f"    {len(tareas)} tareas urgentes:")
            for t in tareas[:3]:
                print(f"    - {t['titulo']} (Urgencia: {t['urgencia']})")
        else:
            print("    Sin tareas urgentes")
        print()

        print("[3] Analizando patrones...")
        sugerencias = self.analizar_patrones()
        if sugerencias:
            for s in sugerencias:
                print(f"    -> {s}")
        else:
            print("    Sin patrones detectados (se necesita mas historial)")
        print()

        print("=" * 60)
        print("Demo completada. Ejecutar 'ciclo_proactivo()' para modo continuo.")
        print("=" * 60)


# Ejemplo de calendar_events.json esperado:
CALENDAR_EXAMPLE = {
    "eventos": [
        {
            "titulo": "Reunion con Cliente A",
            "fecha": "2026-09-05",
            "hora": "16:00",
            "tipo": "reunion",
            "participantes": ["cliente_a", "jefe"],
            "ubicacion": "Sala de juntas",
        },
        {
            "titulo": "Entrega Proyecto Beta",
            "fecha": "2026-09-06",
            "hora": "09:00",
            "tipo": "deadline",
            "participantes": [],
            "ubicacion": "",
        },
    ]
}


if __name__ == "__main__":
    engine = ProactiveEngine()

    # Modo demo (una sola ejecucion)
    engine.demo()

    # Modo continuo (descomentar para produccion)
    # asyncio.run(engine.ciclo_proactivo())
