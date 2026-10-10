#!/usr/bin/env python3
"""
aig Content Factory AI - Quick Win #10
Generador de contenido multi-formato para marketing digital,
blogs, newsletters, redes sociales y campañas publicitarias.

Autor: aig Team
Versión: 1.0.0
"""

import json
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


def _slug_archivo(platform: str, topic: str) -> str:
    """Nombre de fichero seguro para el indice (Fase 3: sin backslash
    en f-string, que rompia el modulo entero en Python <3.12)."""
    limpio = re.sub(r"[^\w\s-]", "", topic).strip().replace(" ", "-")[:30].lower()
    return f"{platform}/{limpio}.txt"


class ContentFactoryAI:
    """
    Fábrica de contenido inteligente que genera múltiples formatos
    de contenido a partir de un tema o brief inicial.
    """

    TONES = {
        "profesional": "Formal, directo, orientado a resultados de negocio.",
        "casual": "Relajado, conversacional, cercano al lector.",
        "persuasivo": "Enfocado en beneficios, llamadas a la acción claras.",
        "educativo": "Instructivo, explicativo, con ejemplos prácticos.",
        "inspirador": "Motivacional, storytelling, emocional.",
        "técnico": "Preciso, detallado, con terminología especializada.",
    }

    PLATFORMS = {
        "blog": {"max_chars": 5000, "hashtags": False, "cta": True},
        "twitter": {"max_chars": 280, "hashtags": True, "cta": True},
        "linkedin": {"max_chars": 3000, "hashtags": True, "cta": True},
        "instagram": {"max_chars": 2200, "hashtags": True, "cta": True},
        "facebook": {"max_chars": 5000, "hashtags": False, "cta": True},
        "newsletter": {"max_chars": 10000, "hashtags": False, "cta": True},
        "email": {"max_chars": 5000, "hashtags": False, "cta": True},
        "ad_copy": {"max_chars": 300, "hashtags": False, "cta": True},
    }

    def __init__(self, output_dir: str = "./content_output"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.history: list[dict[str, Any]] = []
        self._load_templates()

    # ── Templates ───────────────────────────────────────────────

    def _load_templates(self) -> None:
        """Carga plantillas de contenido por defecto."""
        self.templates = {
            "blog": self._template_blog,
            "twitter": self._template_twitter,
            "linkedin": self._template_linkedin,
            "instagram": self._template_instagram,
            "facebook": self._template_facebook,
            "newsletter": self._template_newsletter,
            "email": self._template_email,
            "ad_copy": self._template_ad_copy,
        }

    def _template_blog(self, topic: str, tone: str, keywords: list[str]) -> str:
        kw_str = ", ".join(keywords[:5]) if keywords else topic
        return f"""# {topic}: Guía Completa 2026

## Introducción

En el panorama actual, **{topic}** se ha convertido en un pilar fundamental para el éxito empresarial. Este artículo explora cada aspecto clave que necesitas dominar.

## ¿Qué es {topic}?

{topic} representa una evolución en cómo las organizaciones abordan sus desafíos diarios. Al integrar esta disciplina en tu estrategia, obtendrás ventajas competitivas medibles.

## Beneficios Principales

1. **Eficiencia Operativa**: Reducción de tiempos y optimización de recursos.
2. **Escalabilidad**: Crecimiento sostenible sin comprometer la calidad.
3. **Innovación Continua**: Adaptación ágil a cambios del mercado.

## Implementación Práctica

### Paso 1: Evaluación Inicial
Analiza tu situación actual y define objetivos SMART.

### Paso 2: Selección de Herramientas
Elige soluciones alineadas con tus necesidades específicas.

### Paso 3: Despliegue Gradual
Implementa por fases para minimizar riesgos.

## Caso de Éxito

Empresa del sector tecnológico logró un **40% de mejora** en sus métricas tras adoptar {topic} en su flujo de trabajo.

## Conclusión

{topic} no es una moda pasajera; es una inversión estratégica. Comienza hoy mismo y posiciona a tu organización para el futuro.

---
*Keywords: {kw_str}*
*Publicado: {datetime.now().strftime("%Y-%m-%d")}*
"""

    def _template_twitter(self, topic: str, tone: str, keywords: list[str]) -> str:
        hashtags = " ".join([f"#{k.replace(' ', '')}" for k in keywords[:3]]) if keywords else f"#{topic.replace(' ', '')}"
        hooks = [
            f"🧵 Hilo sobre {topic}:\n\nAquí van 5 insights que cambiarán tu perspectiva:",
            f"¿Sabías que {topic} puede transformar tu negocio? 🚀\n\nTe explico cómo en 60 segundos:",
            f"El error más común con {topic} (y cómo evitarlo) 👇",
            f"🔥 {topic} en 2026:\n\nLo que funciona vs. lo que no:",
        ]
        hook = hooks[hash(topic) % len(hooks)]
        return f"""{hook}

1️⃣ Define objetivos claros antes de comenzar.

2️⃣ Mide resultados desde el día uno.

3️⃣ Itera basándote en datos, no intuición.

4️⃣ Involucra a todo el equipo.

5️⃣ Nunca dejes de aprender.

{hashtags}
"""

    def _template_linkedin(self, topic: str, tone: str, keywords: list[str]) -> str:
        return f"""💼 {topic}: Reflexiones desde la trinchera empresarial

Llevo años trabajando con equipos que implementan {topic}, y hay un patrón que se repite constantemente:

Las organizaciones que tienen éxito no son las que invierten más dinero, sino las que invierten mejor tiempo en planificación.

📌 Tres principios que aplico en cada proyecto:

→ Claridad estratégica antes de ejecutar
→ Métricas de éxito definidas desde el inicio
→ Cultura de aprendizaje continuo

¿Cuál ha sido tu mayor aprendizaje con {topic}? Comparte en comentarios.

---

#Innovación #Liderazgo #{topic.replace(' ', '')} #TransformaciónDigital
"""

    def _template_instagram(self, topic: str, tone: str, keywords: list[str]) -> str:
        emojis = ["✨", "🚀", "💡", "🔥", "🎯", "📈", "💪", "🌟"]
        emoji = emojis[hash(topic) % len(emojis)]
        hashtags = " ".join([f"#{k.replace(' ', '')}" for k in keywords[:8]]) if keywords else "#contenido #marketing"
        return f"""{emoji} {topic.upper()} {emoji}

Swipe para descubrir los 3 secretos que nadie te cuenta 👉

1️⃣ SECRETO #1: La consistencia vence al talento natural.

2️⃣ SECRETO #2: Los datos son tu brújula, no tu ancla.

3️⃣ SECRETO #3: La comunidad lo es todo.

¿Cuál resonó más contigo? 💬

---

{hashtags} #aig #Crecimiento #Emprendimiento #Tips
"""

    def _template_facebook(self, topic: str, tone: str, keywords: list[str]) -> str:
        return f"""📢 ¡Nuevo contenido sobre {topic}!

Sabemos que mantenerse actualizado no es fácil. Por eso hemos preparado este resumen con lo más importante que necesitas saber.

✅ Qué es {topic}
✅ Por qué importa AHORA
✅ Cómo empezar sin complicaciones
✅ Errores comunes a evitar

👇 Déjanos tus preguntas en comentarios. Las responderemos todas.

#aig #Conocimiento
"""

    def _template_newsletter(self, topic: str, tone: str, keywords: list[str]) -> str:
        return f"""━━━━━━━━━━━━━━━━━━━━━━
aig WEEKLY
━━━━━━━━━━━━━━━━━━━━━━

Hola [Nombre],

Este domingo traemos un tema que está revolucionando la industria: **{topic}**.

📊 EN ESTA EDICIÓN:

▸ Deep Dive: {topic} explicado paso a paso
▸ Herramienta del Mes: La solución que usamos internamente
▸ Case Study: Cómo [Empresa] logró resultados en 30 días
▸ Próximos Eventos: Webinars y workshops gratuitos

┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄
🧠 DEEP DIVE: {topic.upper()}
┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄

{topic} no es solo una tendencia; es una respuesta a la complejidad creciente de los entornos empresariales modernos.

Las organizaciones que adoptan {topic} reportan:
• 35% reducción en tiempos de entrega
• 50% mejora en satisfacción del equipo
• 2.5x retorno de inversión en 12 meses

┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄
🛠️ HERRAMIENTA DEL MES
┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄

Nuestra recomendación: aig Platform

Gestión inteligente de proyectos con IA integrada. Prueba gratuita de 14 días.

┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄
📅 PRÓXIMOS EVENTOS
┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄

• Workshop: "{topic} para No-Técnicos" - 15 Sept
• Webinar: "Tendencias 2026" - 22 Sept
• Networking: Madrid AI Meetup - 28 Sept

━━━━━━━━━━━━━━━━━━━━━━

¿Te ha gustado este contenido? Reenvía a un colega.

Hasta la próxima semana,
El Equipo aig

━━━━━━━━━━━━━━━━━━━━━━
¿Quieres personalizar tu newsletter? Responde a este email.
"""

    def _template_email(self, topic: str, tone: str, keywords: list[str]) -> str:
        return f"""Asunto: Tu guía sobre {topic} está lista 🎯

Hola [Nombre],

Gracias por tu interés en {topic}. Como prometimos, aquí tienes los recursos exclusivos:

━━━━━━━━━━━━━━━━━━━━━━
📥 TU PAQUETE DE RECURSOS
━━━━━━━━━━━━━━━━━━━━━━

1. Guía Rápida de {topic} (PDF)
2. Checklist de Implementación
3. Plantilla de Plan de Acción (Editable)
4. Acceso a nuestra comunidad privada

━━━━━━━━━━━━━━━━━━━━━━
🚀 PRÓXIMO PASO RECOMENDADO
━━━━━━━━━━━━━━━━━━━━━━

Reserva una llamada estratégica gratuita de 20 minutos donde analizaremos tu caso específico.

[RESERVAR MI LLAMADA]

¿Preguntas? Responde a este email directamente.

Saludos cordiales,
[aig Team]

---
P.D. Si no quieres recibir más emails, puedes darte de baja aquí.
"""

    def _template_ad_copy(self, topic: str, tone: str, keywords: list[str]) -> str:
        variations = [
            f"""🔥 {topic} sin complicaciones

¿Cansado de procesos lentos?
Descubre cómo {topic} transforma tu día a día.

✅ Resultados en 7 días
✅ Sin contratos de permanencia
✅ Soporte humano 24/7

👉 [PRUÉBALO GRATIS]

Promoción válida hasta {datetime.now().strftime('%d/%m/%Y')}.""",
            f"""⚡ La forma más inteligente de gestionar {topic}

Miles de empresas ya lo están usando.
Únete a la revolución.

🎯 Ahorra 10+ horas semanales
🎯 Automatiza lo repetitivo
🎯 Enfócate en lo estratégico

[EMPEZAR AHORA] →""",
            f"""💡 ¿Y si {topic} fuera 10x más fácil?

Así es como lo hacemos en aig:

1. Analizamos tu caso
2. Diseñamos tu solución
3. Implementamos en 48h

Resultados garantizados o te devolvemos tu dinero.

[SOLICITAR DEMO]""",
        ]
        return variations[hash(topic) % len(variations)]

    # ── Core API ────────────────────────────────────────────────

    def generate(
        self,
        topic: str,
        platform: str = "blog",
        tone: str = "profesional",
        keywords: list[str] | None = None,
        custom_prompt: str | None = None,
        save: bool = True,
    ) -> dict[str, Any]:
        """
        Genera contenido para una plataforma específica.

        Args:
            topic: Tema principal del contenido
            platform: Una de blog|twitter|linkedin|instagram|facebook|newsletter|email|ad_copy
            tone: Tono de voz (ver self.TONES)
            keywords: Palabras clave para SEO y hashtags
            custom_prompt: Prompt personalizado (opcional, anula templates)
            save: Si True, guarda el archivo en output_dir

        Returns:
            Dict con content, metadata, y file_path
        """
        if platform not in self.PLATFORMS:
            raise ValueError(f"Plataforma '{platform}' no soportada. Usa: {list(self.PLATFORMS.keys())}")
        if tone not in self.TONES:
            raise ValueError(f"Tono '{tone}' no soportado. Usa: {list(self.TONES.keys())}")

        keywords = keywords or [topic.lower()]
        config = self.PLATFORMS[platform]

        # Generar contenido
        if custom_prompt:
            content = self._generate_from_prompt(custom_prompt, platform, tone, config)
        else:
            content = self.templates[platform](topic, tone, keywords)

        # Truncar si excede límites (con inteligencia)
        content = self._smart_truncate(content, config["max_chars"])

        # Construir metadata
        timestamp = datetime.now().isoformat()
        slug = re.sub(r"[^\w\s-]", "", topic).strip().replace(" ", "-")[:30].lower()
        filename = f"{platform}_{slug}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        file_path = self.output_dir / filename

        result = {
            "content": content,
            "metadata": {
                "topic": topic,
                "platform": platform,
                "tone": tone,
                "keywords": keywords,
                "char_count": len(content),
                "word_count": len(content.split()),
                "created_at": timestamp,
                "max_chars": config["max_chars"],
                "tone_description": self.TONES[tone],
            },
            "file_path": str(file_path) if save else None,
        }

        if save:
            file_path.write_text(content, encoding="utf-8")

        self.history.append(result)
        return result

    def generate_campaign(
        self,
        topic: str,
        platforms: list[str] | None = None,
        tone: str = "profesional",
        keywords: list[str] | None = None,
    ) -> list[dict[str, Any]]:
        """
        Genera una campaña completa multi-plataforma.

        Returns:
            Lista de resultados por plataforma
        """
        platforms = platforms or ["blog", "twitter", "linkedin", "newsletter"]
        results = []

        for platform in platforms:
            try:
                result = self.generate(
                    topic=topic,
                    platform=platform,
                    tone=tone,
                    keywords=keywords,
                    save=True,
                )
                results.append(result)
            except Exception as e:
                results.append({
                    "platform": platform,
                    "error": str(e),
                })

        return results

    def generate_email_sequence(
        self,
        topic: str,
        sequence_type: str = "onboarding",
        emails_count: int = 5,
        tone: str = "profesional",
    ) -> list[dict[str, Any]]:
        """
        Genera una secuencia de emails automatizada.

        Args:
            sequence_type: onboarding|nurture|sales|re-engagement
            emails_count: Número de emails en la secuencia
        """
        sequences = {
            "onboarding": [
                "Bienvenido a bordo: Tu primer paso con {topic}",
                "Configuración rápida: Empezar a ver resultados",
                "Tip avanzado: Sacar el máximo provecho",
                "Inspiración: Cómo otros lo están usando",
                "Próximos pasos: Tu roadmap personalizado",
            ],
            "nurture": [
                "El problema que nadie está viendo sobre {topic}",
                "La solución que cambió todo para nuestros clientes",
                "Caso real: De 0 a resultados en 30 días",
                "Comparativa: Opciones del mercado analizadas",
                "Oferta exclusiva: Solo para quienes siguen el camino",
            ],
            "sales": [
                "¿Todavía usando el método antiguo para {topic}?",
                "La alternativa que ahorra 10 horas semanales",
                "Demo gratuita: Ve los resultados por ti mismo",
                "Última oportunidad: Precio especial termina pronto",
                "P.S. Tu competencia ya está usando esto",
            ],
            "re-engagement": [
                "Te echamos de menos en aig",
                "Lo que te has perdido esta semana",
                "Un regalo exclusivo para volver",
                "Último intento: ¿Nos dejas saber?",
                "Adiós (y gracias por todo)",
            ],
        }

        subjects = sequences.get(sequence_type, sequences["onboarding"])
        results = []

        for i in range(min(emails_count, len(subjects))):
            subject = subjects[i].format(topic=topic)
            custom_prompt = f"""Email #{i+1} de secuencia '{sequence_type}'.
Asunto: {subject}
Tono: {tone}
Tema general: {topic}

Este email debe ser personal, directo, y tener una CTA clara."""

            result = self.generate(
                topic=subject,
                platform="email",
                tone=tone,
                custom_prompt=custom_prompt,
                save=True,
            )
            result["metadata"]["sequence"] = {
                "type": sequence_type,
                "position": i + 1,
                "total": emails_count,
                "subject": subject,
            }
            results.append(result)

        return results

    # ── Helpers ─────────────────────────────────────────────────

    def _generate_from_prompt(
        self,
        prompt: str,
        platform: str,
        tone: str,
        config: dict,
    ) -> str:
        """Genera contenido a partir de un prompt personalizado."""
        # En una implementación real, aquí iría una llamada a LLM
        # Por ahora, enriquecemos el contenido basado en el prompt
        return f"""[GENERADO CON PROMPT PERSONALIZADO]

{prompt}

---

[Tono aplicado: {tone}]
[Plataforma: {platform}]
[Límite de caracteres: {config['max_chars']}]
"""

    def _smart_truncate(self, text: str, max_chars: int) -> str:
        """Trunca texto respetando párrafos y oraciones."""
        if len(text) <= max_chars:
            return text

        # Intentar cortar al final de oración
        truncated = text[:max_chars]
        last_period = truncated.rfind(".")
        last_newline = truncated.rfind("\n")

        cut_point = max(last_period, last_newline)
        if cut_point > max_chars * 0.8:
            return truncated[: cut_point + 1].strip()

        # Fallback: cortar en espacio
        last_space = truncated.rfind(" ")
        if last_space > max_chars * 0.8:
            return truncated[:last_space].strip() + "..."

        return truncated.strip() + "..."

    def get_history(self) -> list[dict[str, Any]]:
        """Devuelve el historial de contenidos generados."""
        return self.history

    def export_campaign_package(
        self,
        campaign_name: str,
        results: list[dict[str, Any]],
    ) -> str:
        """
        Exporta una campaña completa como un paquete organizado.

        Returns:
            Ruta al directorio de la campaña
        """
        campaign_dir = self.output_dir / f"campaign_{campaign_name}_{datetime.now().strftime('%Y%m%d')}"
        campaign_dir.mkdir(parents=True, exist_ok=True)

        # Estructura organizada
        for result in results:
            if "error" in result:
                continue
            platform = result["metadata"]["platform"]
            platform_dir = campaign_dir / platform
            platform_dir.mkdir(exist_ok=True)

            slug = re.sub(r"[^\w\s-]", "", result["metadata"]["topic"]).strip().replace(" ", "-")[:30].lower()
            filename = f"{slug}.txt"
            (platform_dir / filename).write_text(result["content"], encoding="utf-8")

        # Crear índice
        index = {
            "campaign_name": campaign_name,
            "created_at": datetime.now().isoformat(),
            "contents": [
                {
                    "platform": r["metadata"]["platform"],
                    "topic": r["metadata"]["topic"],
                    "tone": r["metadata"]["tone"],
                    "word_count": r["metadata"]["word_count"],
                    "file": _slug_archivo(r["metadata"]["platform"], r["metadata"]["topic"]),
                }
                for r in results
                if "error" not in r
            ],
        }

        (campaign_dir / "index.json").write_text(
            json.dumps(index, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

        return str(campaign_dir)

    def content_calendar(self, topics: list[str], platforms: list[str], start_date: str | None = None) -> dict[str, Any]:
        """
        Genera un calendario de contenidos para múltiples semanas.

        Args:
            topics: Lista de temas a cubrir
            platforms: Plataformas destino
            start_date: Fecha inicio (ISO), default hoy

        Returns:
            Dict con calendario estructurado por días
        """
        from datetime import timedelta

        start = datetime.fromisoformat(start_date) if start_date else datetime.now()
        calendar = {}

        day_map = {
            0: ("linkedin", "profesional"),      # Lunes
            1: ("blog", "educativo"),            # Martes
            2: ("twitter", "casual"),            # Miércoles
            3: ("instagram", "inspirador"),      # Jueves
            4: ("newsletter", "profesional"),    # Viernes
            5: ("twitter", "casual"),            # Sábado
            6: None,                              # Domingo - descanso
        }

        for i, topic in enumerate(topics):
            day_offset = i % 7
            current_date = start + timedelta(days=day_offset)
            date_str = current_date.strftime("%Y-%m-%d")

            if day_map[day_offset] is None:
                calendar[date_str] = {"rest_day": True}
                continue

            platform, tone = day_map[day_offset]
            if platform in platforms:
                calendar[date_str] = {
                    "topic": topic,
                    "platform": platform,
                    "tone": tone,
                    "status": "planned",
                }

        return calendar


# ═══════════════════════════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════════════════════════

def main() -> int:

    import argparse

    parser = argparse.ArgumentParser(description="aig Content Factory AI")
    parser.add_argument("topic", help="Tema del contenido a generar")
    parser.add_argument("-p", "--platform", default="blog", choices=list(ContentFactoryAI.PLATFORMS.keys()))
    parser.add_argument("-t", "--tone", default="profesional", choices=list(ContentFactoryAI.TONES.keys()))
    parser.add_argument("-k", "--keywords", nargs="+", help="Palabras clave")
    parser.add_argument("-o", "--output", default="./content_output", help="Directorio de salida")
    parser.add_argument("--campaign", action="store_true", help="Generar campaña completa")
    parser.add_argument("--email-sequence", choices=["onboarding", "nurture", "sales", "re-engagement"])
    parser.add_argument("--sequence-count", type=int, default=5)
    parser.add_argument("--calendar", nargs="+", help="Generar calendario con múltiples temas")

    args = parser.parse_args()
    factory = ContentFactoryAI(output_dir=args.output)

    if args.calendar:
        calendar = factory.content_calendar(
            topics=args.calendar,
            platforms=["blog", "twitter", "linkedin", "instagram", "newsletter"],
        )
        print("📅 CALENDARIO DE CONTENIDOS")
        print(json.dumps(calendar, indent=2, ensure_ascii=False))
        return 0

    if args.email_sequence:
        results = factory.generate_email_sequence(
            topic=args.topic,
            sequence_type=args.email_sequence,
            emails_count=args.sequence_count,
            tone=args.tone,
        )
        print(f"📧 SECUENCIA DE EMAILS: {args.email_sequence.upper()}")
        for r in results:
            meta = r.get("metadata", {}).get("sequence", {})
            print(f"\n--- Email {meta.get('position', '?')}/{meta.get('total', '?')} ---")
            print(f"Asunto: {meta.get('subject', 'N/A')}")
            print(f"Archivo: {r.get('file_path', 'N/A')}")
        return 0

    if args.campaign:
        results = factory.generate_campaign(
            topic=args.topic,
            tone=args.tone,
            keywords=args.keywords,
        )
        campaign_dir = factory.export_campaign_package(
            campaign_name=args.topic.replace(" ", "-").lower()[:20],
            results=results,
        )
        print("🚀 CAMPAÑA COMPLETA GENERADA")
        print(f"📁 Directorio: {campaign_dir}")
        print("\nContenidos:")
        for r in results:
            if "error" not in r:
                print(f"  ✅ {r['metadata']['platform']}: {r['metadata']['word_count']} palabras")
            else:
                print(f"  ❌ {r['platform']}: {r['error']}")
        return 0

    result = factory.generate(
        topic=args.topic,
        platform=args.platform,
        tone=args.tone,
        keywords=args.keywords,
    )

    print(f"✅ CONTENIDO GENERADO: {args.platform.upper()}")
    print(f"📄 Archivo: {result['file_path']}")
    print(f"📝 Palabras: {result['metadata']['word_count']}")
    print(f"🔤 Caracteres: {result['metadata']['char_count']}")
    print("\n--- CONTENIDO ---\n")
    print(result["content"])

    return 0


if __name__ == "__main__":
    sys.exit(main())
