"""
Sentiment-Aware Dashboard
==========================
Analiza el tono de comunicaciones y prioriza tareas
segun el estado emocional detectado.

Quick Win #6: Alto impacto, bajo esfuerzo.
Integra con mood_engine.py existente.
"""

import json
import logging
import os
import re
from dataclasses import dataclass
from enum import Enum

logging.basicConfig(level=logging.INFO, format="%(asctime)s [SENTIMENT] %(message)s")
logger = logging.getLogger(__name__)


class SentimentType(Enum):
    """Tipos de sentimiento detectados."""

    VERY_NEGATIVE = "muy_negativo"  # Urgente, enojado, frustrado
    NEGATIVE = "negativo"  # Preocupado, critico
    NEUTRAL = "neutral"  # Informativo
    POSITIVE = "positivo"  # Feliz, satisfecho
    VERY_POSITIVE = "muy_positivo"  # Entusiasta, emocionado


@dataclass
class SentimentScore:
    """Puntuacion de sentimiento."""

    sentiment: SentimentType
    score: float  # -1.0 a 1.0
    urgency: int  # 0-100
    keywords: list[str]
    recommendation: str


class SentimentAnalyzer:
    """Analizador de sentimiento basado en reglas + keywords."""

    # Diccionarios de sentimiento en espanol
    VERY_NEGATIVE_WORDS = [
        "urgente",
        "critico",
        "grave",
        "enojado",
        "furioso",
        "indignado",
        "desastroso",
        "terrible",
        "horrible",
        "inaceptable",
        "denuncia",
        "demanda",
        "ultimatum",
        "inmediato",
        "ahora mismo",
        "emergencia",
        "catastrofe",
        "fracaso",
        "ruina",
        "desastre",
        "insufrible",
        "impresentable",
        "incompetente",
        "estafa",
        "timado",
    ]

    NEGATIVE_WORDS = [
        "problema",
        "error",
        "fallo",
        "defecto",
        "retraso",
        "atraso",
        "preocupado",
        "inquieto",
        "molesto",
        "disconforme",
        "insatisfecho",
        "decepcionado",
        "frustrado",
        "cansado",
        "agotado",
        "estresado",
        "dificil",
        "complicado",
        "confuso",
        "dudoso",
        "sospechoso",
        "lamentable",
        "deplorable",
        "deficiente",
        "inadecuado",
    ]

    POSITIVE_WORDS = [
        "bien",
        "excelente",
        "perfecto",
        "genial",
        "fantastico",
        "satisfecho",
        "contento",
        "feliz",
        "encantado",
        "agradecido",
        "exitoso",
        "logrado",
        "conseguido",
        "avance",
        "progreso",
        "oportunidad",
        "mejora",
        "optimizacion",
        "eficiente",
        "rapido",
    ]

    VERY_POSITIVE_WORDS = [
        "increible",
        "extraordinario",
        "maravilloso",
        "espectacular",
        "brillante",
        "excepcional",
        "sobresaliente",
        "inigualable",
        "entusiasmado",
        "emocionado",
        "eufórico",
        "triunfo",
        "exito",
        "celebrar",
        "felicidades",
        "innovador",
        "revolucionario",
    ]

    URGENCY_INDICATORS = [
        "urgente",
        "inmediato",
        "ahora",
        "hoy",
        "antes posible",
        "lo antes posible",
        "deadline",
        "vence",
        "limite",
        "plazo",
        "critical",
        "grave",
        "emergencia",
        "asap",
        "prioridad",
        "importante",
        "crucial",
        "vital",
        "esencial",
        "imprescindible",
    ]

    def __init__(self):
        self.patterns = self._compile_patterns()

    def _compile_patterns(self) -> dict:
        """Compila patrones de deteccion."""
        return {
            "exclamation": re.compile(r"!{2,}"),  # Multiples exclamaciones
            "caps": re.compile(r"[A-Z\u00c1\u00c9\u00cd\u00d3\u00da\u00d1]{3,}"),  # MAYUSCULAS
            "question": re.compile(r"\?{2,}"),  # Multiples interrogaciones
            "ellipsis": re.compile(r"\.{3,}"),  # Puntos suspensivos
        }

    def analyze(self, text: str, context: str | None = None) -> SentimentScore:
        """
        Analiza el sentimiento de un texto.

        Args:
            text: Texto a analizar
            context: Contexto adicional (email, chat, etc.)

        Returns:
            SentimentScore con puntuacion y recomendacion
        """
        if not text:
            return SentimentScore(
                sentiment=SentimentType.NEUTRAL,
                score=0.0,
                urgency=0,
                keywords=[],
                recommendation="Sin texto para analizar",
            )

        text_lower = text.lower()
        text_lower.split()

        # Contar palabras por categoria
        very_neg_count = sum(1 for w in self.VERY_NEGATIVE_WORDS if w in text_lower)
        neg_count = sum(1 for w in self.NEGATIVE_WORDS if w in text_lower)
        pos_count = sum(1 for w in self.POSITIVE_WORDS if w in text_lower)
        very_pos_count = sum(1 for w in self.VERY_POSITIVE_WORDS if w in text_lower)
        urgency_count = sum(1 for w in self.URGENCY_INDICATORS if w in text_lower)

        # Detectar patrones especiales
        has_exclamations = bool(self.patterns["exclamation"].search(text))
        has_caps = bool(self.patterns["caps"].search(text))
        bool(self.patterns["question"].search(text))
        bool(self.patterns["ellipsis"].search(text))

        # Calcular score base (-1.0 a 1.0)
        total_sentiment_words = very_neg_count + neg_count + pos_count + very_pos_count
        if total_sentiment_words == 0:
            score = 0.0
        else:
            score = (
                (-2 * very_neg_count) + (-1 * neg_count) + (1 * pos_count) + (2 * very_pos_count)
            ) / (2 * total_sentiment_words)

        # Ajustar por patrones especiales
        if has_caps:
            score -= 0.2  # MAYUSCULAS indican enfado/urgencia
        if has_exclamations:
            score -= 0.1  # !!! indica emocion fuerte (usualmente negativa en business)

        # Calcular urgencia (0-100)
        urgency = min(urgency_count * 15, 60)  # Base por keywords
        if has_caps:
            urgency += 20
        if has_exclamations:
            urgency += 10
        if very_neg_count > 0:
            urgency += 20
        urgency = min(urgency, 100)

        # Determinar tipo de sentimiento
        if score <= -0.7:
            sentiment = SentimentType.VERY_NEGATIVE
        elif score <= -0.3:
            sentiment = SentimentType.NEGATIVE
        elif score >= 0.7:
            sentiment = SentimentType.VERY_POSITIVE
        elif score >= 0.3:
            sentiment = SentimentType.POSITIVE
        else:
            sentiment = SentimentType.NEUTRAL

        # Extraer keywords encontradas
        keywords = []
        for word_list, prefix in [
            (self.VERY_NEGATIVE_WORDS, " muy-neg"),
            (self.NEGATIVE_WORDS, " neg"),
            (self.POSITIVE_WORDS, " pos"),
            (self.VERY_POSITIVE_WORDS, " muy-pos"),
            (self.URGENCY_INDICATORS, " urg"),
        ]:
            for w in word_list:
                if w in text_lower:
                    keywords.append(w + prefix)

        # Generar recomendacion
        recommendation = self._generate_recommendation(sentiment, urgency, has_caps, context)

        return SentimentScore(
            sentiment=sentiment,
            score=round(score, 2),
            urgency=urgency,
            keywords=list(set(keywords))[:10],  # Max 10 keywords
            recommendation=recommendation,
        )

    def _generate_recommendation(
        self, sentiment: SentimentType, urgency: int, has_caps: bool, context: str | None
    ) -> str:
        """Genera recomendacion basada en el analisis."""

        if sentiment == SentimentType.VERY_NEGATIVE:
            if urgency >= 70:
                return (
                    "ALTA PRIORIDAD: Comunicacion muy negativa y urgente. "
                    "Responder con calma y empatia. No usar tono defensivo. "
                    "Ofrecer soluciones concretas y plazos."
                )
            else:
                return (
                    "Comunicacion muy negativa. Revisar fondo del problema. "
                    "Considerar llamada telefonica en lugar de email."
                )

        elif sentiment == SentimentType.NEGATIVE:
            if urgency >= 50:
                return (
                    "Prioridad media-alta: Comunicacion negativa con urgencia. "
                    "Responder pronto con propuesta de solucion."
                )
            else:
                return (
                    "Comunicacion negativa. Responder con datos/objetividad. Evitar confrontacion."
                )

        elif sentiment == SentimentType.POSITIVE:
            return (
                "Comunicacion positiva. Buen momento para proponer ideas nuevas o pedir feedback."
            )

        elif sentiment == SentimentType.VERY_POSITIVE:
            return (
                "Comunicacion muy positiva! Aprovechar para fortalecer "
                "relacion: agradecer, compartir buenas noticias, proponer "
                "colaboracion adicional."
            )

        else:  # NEUTRAL
            if urgency >= 50:
                return (
                    "Comunicacion neutra pero URGENTE. Responder rapido "
                    "con la informacion solicitada."
                )
            else:
                return "Comunicacion informativa/neutra. Responder cuando sea conveniente."


class SentimentDashboard:
    """Dashboard de sentimiento para gestion de comunicaciones."""

    def __init__(self):
        self.analyzer = SentimentAnalyzer()
        self.history_file = "sentiment_history.json"

    def analyze_email(self, subject: str, body: str, sender: str) -> SentimentScore:
        """Analiza un email completo."""
        full_text = f"{subject} {body}"
        score = self.analyzer.analyze(full_text, context="email")

        # Guardar en historial
        self._save_analysis(
            {
                "timestamp": self._now(),
                "type": "email",
                "sender": sender,
                "subject": subject,
                "sentiment": score.sentiment.value,
                "score": score.score,
                "urgency": score.urgency,
                "recommendation": score.recommendation,
            }
        )

        return score

    def analyze_chat_message(self, text: str, sender: str) -> SentimentScore:
        """Analiza un mensaje de chat."""
        score = self.analyzer.analyze(text, context="chat")

        self._save_analysis(
            {
                "timestamp": self._now(),
                "type": "chat",
                "sender": sender,
                "sentiment": score.sentiment.value,
                "score": score.score,
                "urgency": score.urgency,
                "recommendation": score.recommendation,
            }
        )

        return score

    def analyze_task(self, title: str, description: str) -> SentimentScore:
        """Analiza una tarea para priorizacion."""
        full_text = f"{title} {description}"
        score = self.analyzer.analyze(full_text, context="task")

        self._save_analysis(
            {
                "timestamp": self._now(),
                "type": "task",
                "sentiment": score.sentiment.value,
                "score": score.score,
                "urgency": score.urgency,
                "recommendation": score.recommendation,
            }
        )

        return score

    def get_priority_queue(self, items: list[dict]) -> list[dict]:
        """
        Ordena items por prioridad considerando sentimiento + urgencia.

        Args:
            items: Lista de dicts con 'title', 'text', 'deadline'

        Returns:
            Items ordenados por prioridad (mayor primero)
        """
        scored_items = []

        for item in items:
            text = f"{item.get('title', '')} {item.get('text', '')}"
            sentiment = self.analyzer.analyze(text)

            # Calcular prioridad compuesta
            priority = sentiment.urgency
            if sentiment.sentiment in [SentimentType.VERY_NEGATIVE, SentimentType.NEGATIVE]:
                priority += 15
            if item.get("deadline") == "hoy":
                priority += 20
            elif item.get("deadline") == "manana":
                priority += 10

            scored_items.append(
                {
                    **item,
                    "priority": min(priority, 100),
                    "sentiment": sentiment.sentiment.value,
                    "sentiment_score": sentiment.score,
                    "recommendation": sentiment.recommendation,
                }
            )

        # Ordenar por prioridad descendente
        scored_items.sort(key=lambda x: x["priority"], reverse=True)
        return scored_items

    def generate_daily_report(self) -> dict:
        """Genera reporte diario de sentimiento."""
        history = self._load_history()
        today = self._now()[:10]  # YYYY-MM-DD

        today_items = [h for h in history if h["timestamp"].startswith(today)]

        if not today_items:
            return {
                "date": today,
                "total_analyzed": 0,
                "summary": "Sin comunicaciones analizadas hoy",
            }

        # Estadisticas
        sentiments = {}
        total_urgency = 0
        urgent_count = 0

        for item in today_items:
            s = item["sentiment"]
            sentiments[s] = sentiments.get(s, 0) + 1
            total_urgency += item["urgency"]
            if item["urgency"] >= 50:
                urgent_count += 1

        avg_urgency = total_urgency / len(today_items)

        return {
            "date": today,
            "total_analyzed": len(today_items),
            "sentiment_breakdown": sentiments,
            "average_urgency": round(avg_urgency, 1),
            "urgent_items": urgent_count,
            "summary": self._generate_daily_summary(sentiments, avg_urgency),
        }

    def _generate_daily_summary(self, sentiments: dict, avg_urgency: float) -> str:
        """Genera resumen en lenguaje natural."""
        total = sum(sentiments.values())
        negative = sentiments.get("muy_negativo", 0) + sentiments.get("negativo", 0)
        positive = sentiments.get("muy_positivo", 0) + sentiments.get("positivo", 0)

        if negative > total * 0.3:
            return (
                f"Dia con comunicaciones dificiles ({negative} negativas). "
                f"Urgencia media: {avg_urgency:.0f}/100. Recomendacion: "
                f"tomar descansos y responder con calma."
            )
        elif positive > total * 0.5:
            return (
                f"Dia positivo ({positive} comunicaciones favorables). "
                f"Buen momento para proponer ideas nuevas."
            )
        else:
            return (
                f"Dia equilibrado. {total} comunicaciones analizadas. "
                f"Urgencia media: {avg_urgency:.0f}/100."
            )

    def _save_analysis(self, data: dict):
        """Guarda analisis en historial."""
        history = self._load_history()
        history.append(data)

        # Mantener solo ultimos 1000
        history = history[-1000:]

        try:
            with open(self.history_file, "w", encoding="utf-8") as f:
                json.dump(history, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Error guardando historial: {e}")

    def _load_history(self) -> list[dict]:
        """Carga historial de analisis."""
        if not os.path.exists(self.history_file):
            return []
        try:
            with open(self.history_file, encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []

    def _now(self) -> str:
        """Retorna timestamp actual."""
        from datetime import datetime

        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def demo(self):
        """Demostracion del dashboard de sentimiento."""
        print("=" * 70)
        print("SENTIMENT-AWARE DASHBOARD - DEMO")
        print("=" * 70)
        print()

        # Ejemplos de emails
        test_emails = [
            {
                "subject": "URGENTE: Problema critico en produccion",
                "body": "Tenemos un BUG GRAVE que esta afectando a todos los clientes. "
                "Necesitamos solucion INMEDIATA. Esto es inaceptable.",
                "sender": "cliente@empresa.com",
            },
            {
                "subject": "Reunion de seguimiento semanal",
                "body": "Hola, quedamos en revisar los avances del proyecto. "
                "Nos vemos el martes a las 10.",
                "sender": "colega@empresa.com",
            },
            {
                "subject": "Excelente trabajo en la presentacion!",
                "body": "Felicidades, la presentacion fue extraordinaria. "
                "El cliente quedo encantado. Gran trabajo del equipo.",
                "sender": "jefe@empresa.com",
            },
            {
                "subject": "Factura vencida #12345",
                "body": "Le recordamos que su factura vence hoy. "
                "Por favor realice el pago lo antes posible.",
                "sender": "facturacion@proveedor.com",
            },
        ]

        print("[1] Analisis de emails de ejemplo:")
        print()

        for email in test_emails:
            score = self.analyze_email(email["subject"], email["body"], email["sender"])

            print(f"  De: {email['sender']}")
            print(f"  Asunto: {email['subject']}")
            print(f"  -> Sentimiento: {score.sentiment.value.upper()}")
            print(f"  -> Score: {score.score}")
            print(f"  -> Urgencia: {score.urgency}/100")
            print(f"  -> Keywords: {', '.join(score.keywords[:5])}")
            print(f"  -> Recomendacion: {score.recommendation}")
            print()

        print("[2] Cola de prioridad con sentimiento:")
        print()

        tasks = [
            {
                "title": "Responder email del cliente enojado",
                "text": "urgente critico problema",
                "deadline": "hoy",
            },
            {
                "title": "Preparar presentacion",
                "text": "reunion semanal avance",
                "deadline": "manana",
            },
            {
                "title": "Actualizar documentacion",
                "text": "mejoras actualizaciones",
                "deadline": "proxima_semana",
            },
            {
                "title": "BUG: Login no funciona",
                "text": "error grave usuarios no pueden entrar",
                "deadline": "hoy",
            },
        ]

        prioritized = self.get_priority_queue(tasks)
        for i, task in enumerate(prioritized, 1):
            print(f"  {i}. [{task['priority']}/100] {task['title']}")
            print(f"     Sentimiento: {task['sentiment']} | {task['recommendation'][:60]}...")
            print()

        print("[3] Reporte diario:")
        report = self.generate_daily_report()
        print(f"  Fecha: {report['date']}")
        print(f"  Analizados: {report['total_analyzed']}")
        print(f"  Urgencia media: {report.get('average_urgency', 'N/A')}")
        print(f"  Items urgentes: {report.get('urgent_items', 0)}")
        print(f"  Resumen: {report['summary']}")
        print()

        print("=" * 70)
        print("Demo completada.")
        print("=" * 70)


if __name__ == "__main__":
    dashboard = SentimentDashboard()
    dashboard.demo()
