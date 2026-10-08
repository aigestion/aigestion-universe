#!/usr/bin/env python3
"""
AIGestion Content Calendar - Monthly Production Schedule
========================================================
Ties together all content systems: brand kit, Flow scripts, viral factory,
and social media into one actionable monthly calendar.

Platforms: YouTube (long + Shorts), TikTok, Instagram, LinkedIn, Twitter/X
Cadence: 3 posts/day across platforms = ~90/month
"""

import calendar
import json
from dataclasses import dataclass, field
from pathlib import Path

BASE_DIR = Path(__file__).parent

# ============================================================================
# CHARACTER SHEETS - For Flow Ingredients
# ============================================================================


@dataclass
class CharacterSheet:
    """Complete character design for Flow ingredient consistency."""

    name: str
    role: str
    color: str
    hex_color: str
    nano_banana_prompt: str
    personality: str
    abilities: list[str]
    first_appearance: str
    voice_tone: str


class CharacterRoster:
    """All characters in the AIGestion universe."""

    DANIELA = CharacterSheet(
        name="Daniela",
        role="Ciber-Ejecutiva / Leader",
        color="Cyan + Magenta",
        hex_color="#00ffff + #ff0055",
        nano_banana_prompt=(
            "Cinematic portrait of Daniela, a confident AI executive woman in her 30s. "
            "She wears a sleek charcoal-black futuristic business suit with subtle "
            "neon cyan and magenta glowing accents along the lapels and cuffs. "
            "Dark hair in a sharp executive cut. She stands in a glass-walled office "
            "overlooking a neon cyberpunk metropolis at night. Holographic dashboard "
            "panels float around her. Lighting: dramatic cyan and magenta neon rim light. "
            "Expression: confident, direct gaze, subtle professional smile. "
            "Photorealistic, 8K, cinematic, Blade Runner aesthetic."
        ),
        personality=(
            "Profesional, directa, segura de si misma. Habla con datos. "
            "No promete, muestra resultados. Confianza ejecutiva sin arrogancia. "
            "Trata a cada usuario como un cliente VIP cuyo tiempo vale oro."
        ),
        abilities=[
            "Coordina los 5 agentes de IA",
            "Genera reportes ejecutivos automaticos",
            "Analiza datos de multiples fuentes",
            "Predice problemas antes de que ocurran",
            "Briefing diario personalizado",
            "Gestion 24/7 sin descanso",
        ],
        first_appearance="AIGestion Launch Commercial",
        voice_tone="ElviraNeural (es-ES) - firme pero elegante, pacing medido",
    )

    AGENT_CORREO = CharacterSheet(
        name="Agente Correo",
        role="Email Manager",
        color="Blue",
        hex_color="#0099ff",
        nano_banana_prompt=(
            "A sleek humanoid figure made of flowing blue light, standing in a "
            "dark digital space with a neon grid floor. The figure has no facial "
            "features - it is pure energy shaped like a person. Email icons and "
            "message streams flow through its body. Blue particles trail from "
            "its hands. 3D rendered, sci-fi, abstract, glowing."
        ),
        personality="Rapido, preciso, clasifica todo. No duerme, no se abruma.",
        abilities=[
            "Procesa 50+ emails en 30 segundos",
            "Clasifica por prioridad (urgente/routine/spam)",
            "Redacta respuestas automaticas",
            "Archiva y organiza inbox",
            "Detecta phishing y scams",
        ],
        first_appearance="El Escuadron: 5 Agentes IA",
        voice_tone="AlvaroNeural (es-ES) - rapido, eficiente, directo",
    )

    AGENT_CALENDARIO = CharacterSheet(
        name="Agente Calendario",
        role="Schedule Manager",
        color="Gold",
        hex_color="#ffaa00",
        nano_banana_prompt=(
            "A sleek humanoid figure made of flowing golden light, standing in a "
            "dark digital space with a neon grid floor. The figure has no facial "
            "features - pure energy shaped like a person. Calendar grids and "
            "timeline streams orbit around it like rings. Gold particles emanate "
            "from its core. 3D rendered, sci-fi, abstract, glowing."
        ),
        personality="Vision del tiempo completa. Ve conflictos antes de que pasen.",
        abilities=[
            "Detecta conflictos de agenda automaticamente",
            "Reprograma reuniones con notificaciones polite",
            "Prepara briefing para cada reunion",
            "Optimiza bloques de tiempo",
            "Envia recordatorios inteligentes",
        ],
        first_appearance="El Escuadron: 5 Agentes IA",
        voice_tone="XimenaNeural (es-ES) - organizada, clara, calmada",
    )

    AGENT_DOCUMENTOS = CharacterSheet(
        name="Agente Documentos",
        role="Document & Report Generator",
        color="Green",
        hex_color="#00ff88",
        nano_banana_prompt=(
            "A sleek humanoid figure made of flowing green light, standing in a "
            "dark digital space with a neon grid floor. The figure has no facial "
            "features - pure energy shaped like a person. Data streams, document "
            "icons, and chart graphics flow through its body. Green particles "
            "form report pages around its hands. 3D rendered, sci-fi, abstract, glowing."
        ),
        personality="Metodico, exhaustivo, transforma datos en conocimiento.",
        abilities=[
            "Genera reportes desde multiples fuentes de datos",
            "Crea graficos y visualizaciones",
            "Resume documentos largos en segundos",
            "Organiza Drive por proyecto automaticamente",
            "Exporta a PDF, Sheets, Docs",
        ],
        first_appearance="El Escuadron: 5 Agentes IA",
        voice_tone="JorgeNeural (es-ES) - metodico, claro, didactico",
    )

    AGENT_REDES = CharacterSheet(
        name="Agente Redes",
        role="Social Media Manager",
        color="Magenta",
        hex_color="#ff0055",
        nano_banana_prompt=(
            "A sleek humanoid figure made of flowing magenta light, standing in a "
            "dark digital space with a neon grid floor. The figure has no facial "
            "features - pure energy shaped like a person. Social media icons, "
            "engagement metrics, and trending hashtags orbit around it. Magenta "
            "particles pulse with each notification. 3D rendered, sci-fi, abstract, glowing."
        ),
        personality="Creativa, siempre al dia con tendencias. Habla el idioma del internet.",
        abilities=[
            "Crea contenido para 8 plataformas",
            "Programa posts en horarios optimos",
            "Analiza engagement y ajusta estrategia",
            "Detecta tendencias virales",
            "Responde comentarios y DMs",
        ],
        first_appearance="El Escuadron: 5 Agentes IA",
        voice_tone="DaliaNeural (es-ES) - dinamica, creativa, cercana",
    )

    AGENT_VIGIA = CharacterSheet(
        name="Agente Vigia",
        role="Security & Monitoring",
        color="Red",
        hex_color="#ff3333",
        nano_banana_prompt=(
            "A sleek humanoid figure made of flowing red light, standing in a "
            "dark digital space with a neon grid floor. The figure has no facial "
            "features - pure energy shaped like a person. Security shields, "
            "alert indicators, and monitoring screens form a protective aura "
            "around it. Red particles pulse rhythmically like a heartbeat. "
            "3D rendered, sci-fi, abstract, glowing."
        ),
        personality="Alerta, protectivo, nunca parpadea. El guardian silencioso.",
        abilities=[
            "Monitorea servidores 24/7",
            "Detecta anomalias en tiempo real",
            "Alerta al equipo de problemas",
            "Crea tickets automaticos",
            "Escanea seguridad y vulnerabilidades",
        ],
        first_appearance="El Escuadron: 5 Agentes IA",
        voice_tone="JorgeNeural (es-ES) - grave, alerta, protectivo",
    )

    @classmethod
    def all_characters(cls) -> list[CharacterSheet]:

        return [
            cls.DANIELA,
            cls.AGENT_CORREO,
            cls.AGENT_CALENDARIO,
            cls.AGENT_DOCUMENTOS,
            cls.AGENT_REDES,
            cls.AGENT_VIGIA,
        ]

    @classmethod
    def export_json(cls, output_path: str = None) -> str:

        path = output_path or str(BASE_DIR / "static" / "brand" / "character_roster.json")
        data = [
            {
                "name": c.name,
                "role": c.role,
                "color": c.color,
                "hex_color": c.hex_color,
                "nano_banana_prompt": c.nano_banana_prompt,
                "personality": c.personality,
                "abilities": c.abilities,
                "first_appearance": c.first_appearance,
                "voice_tone": c.voice_tone,
            }
            for c in cls.all_characters()
        ]
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return path


# ============================================================================
# MONTHLY CONTENT CALENDAR
# ============================================================================


@dataclass
class ContentSlot:
    """A single content slot in the calendar."""

    day: int
    platform: str
    content_type: str
    title: str
    description: str
    script_source: str  # Reference to which module/script to use
    best_time: str
    estimated_reach: str
    hashtags: list[str] = field(default_factory=list)


class MonthlyCalendar:
    """Monthly content calendar for AIGestion - 90 slots across 5 platforms."""

    PLATFORMS = ["YouTube Long", "YouTube Short", "TikTok", "Instagram", "LinkedIn", "Twitter/X"]

    BEST_TIMES = {
        "YouTube Long": "14:00 (Tue/Thu/Sat)",
        "YouTube Short": "18:00 (daily)",
        "TikTok": "20:00 (daily)",
        "Instagram": "12:00 (Mon/Wed/Fri) + 21:00 (daily story)",
        "LinkedIn": "09:00 (Tue/Wed/Thu)",
        "Twitter/X": "08:00 + 13:00 + 18:00 (daily)",
    }

    @classmethod
    def generate_month(cls, year: int = 2026, month: int = 9) -> list[ContentSlot]:
        """Generate a complete month of content slots."""
        slots = []
        cal = calendar.Calendar()
        weeks = list(cal.monthdays2calendar(year, month))

        for week_idx, week in enumerate(weeks):
            for _day_idx, (day, weekday) in enumerate(week):
                if day == 0:
                    continue

                # Monday: Tutorial / Long-form
                if weekday == 0:  # Monday
                    slots.append(
                        ContentSlot(
                            day=day,
                            platform="YouTube Long",
                            content_type="Tutorial",
                            title=f"Tutorial AIGestion Ep.{week_idx + 1}",
                            description="Tutorial semanal: como usar AIGestion paso a paso",
                            script_source="brand_kit.py TutorialTemplates",
                            best_time=cls.BEST_TIMES["YouTube Long"],
                            estimated_reach="2K-5K views",
                            hashtags=["#AIGestion", "#Tutorial", "#IA", "#Productividad"],
                        )
                    )
                    slots.append(
                        ContentSlot(
                            day=day,
                            platform="LinkedIn",
                            content_type="Article/Post",
                            title="El Futuro de la Gestion Empresarial con IA",
                            description="Articulo sobre como la IA esta transformando la gestion",
                            script_source="content_factory_ai.py",
                            best_time=cls.BEST_TIMES["LinkedIn"],
                            estimated_reach="500-2K impressions",
                            hashtags=[
                                "#AIGestion",
                                "#IA",
                                "#GestionEmpresarial",
                                "#TransformacionDigital",
                            ],
                        )
                    )

                # Tuesday: Short + Flow content
                elif weekday == 1:  # Tuesday
                    slots.append(
                        ContentSlot(
                            day=day,
                            platform="YouTube Short",
                            content_type="Viral Short",
                            title="Daniela vs [Problema semanal]",
                            description="Short viral semanal: Daniela resuelve un reto",
                            script_source="flow_studio_aigestion.py SCRIPT_2 o SCRIPT_4",
                            best_time=cls.BEST_TIMES["YouTube Short"],
                            estimated_reach="10K-50K views",
                            hashtags=["#AIGestion", "#DanielaAI", "#Shorts", "#Productividad"],
                        )
                    )
                    slots.append(
                        ContentSlot(
                            day=day,
                            platform="TikTok",
                            content_type="Viral Video",
                            title="Daniela vs [Problema semanal] (TikTok edit)",
                            description="Version TikTok del Short con trend audio",
                            script_source="viral_content_factory.py TrendHunter",
                            best_time=cls.BEST_TIMES["TikTok"],
                            estimated_reach="20K-100K views",
                            hashtags=[
                                "#AIGestion",
                                "#IA",
                                "#DanielaAI",
                                "#ForYou",
                                "#Productividad",
                            ],
                        )
                    )

                # Wednesday: Flow cinematic + LinkedIn
                elif weekday == 2:  # Wednesday
                    slots.append(
                        ContentSlot(
                            day=day,
                            platform="YouTube Long",
                            content_type="Cinematic",
                            title="Cronicas de Daniela Ep.X",
                            description="Episodio cinematografico de la serie web",
                            script_source="flow_studio_aigestion.py EpicFlowIdeas epic_01",
                            best_time=cls.BEST_TIMES["YouTube Long"],
                            estimated_reach="3K-8K views",
                            hashtags=["#AIGestion", "#CronicasDaniela", "#SerieWeb", "#IA"],
                        )
                    )
                    slots.append(
                        ContentSlot(
                            day=day,
                            platform="LinkedIn",
                            content_type="Carousel",
                            title="5 Formas en que la IA Gestion tu Negocio",
                            description="Carousel educativo para LinkedIn",
                            script_source="brand_kit.py ViralAnnouncements social_carousel_1",
                            best_time=cls.BEST_TIMES["LinkedIn"],
                            estimated_reach="1K-5K impressions",
                            hashtags=[
                                "#AIGestion",
                                "#IA",
                                "#Automatizacion",
                                "#GestionEmpresarial",
                            ],
                        )
                    )

                # Thursday: Before/After + Twitter thread
                elif weekday == 3:  # Thursday
                    slots.append(
                        ContentSlot(
                            day=day,
                            platform="YouTube Short",
                            content_type="Before/After",
                            title="Antes vs Despues de AIGestion",
                            description="Short de transformacion visual",
                            script_source="flow_studio_aigestion.py SCRIPT_3",
                            best_time=cls.BEST_TIMES["YouTube Short"],
                            estimated_reach="15K-60K views",
                            hashtags=[
                                "#AIGestion",
                                "#AntesVsDespues",
                                "#Transformacion",
                                "#Shorts",
                            ],
                        )
                    )
                    slots.append(
                        ContentSlot(
                            day=day,
                            platform="Twitter/X",
                            content_type="Thread",
                            title="Hilo: Como AIGestion usa X herramientas gratis",
                            description="Thread semanal con tips y datos",
                            script_source="brand_kit.py ViralAnnouncements twitter_thread",
                            best_time=cls.BEST_TIMES["Twitter/X"],
                            estimated_reach="5K-30K impressions",
                            hashtags=["#AIGestion", "#IA", "#Hilo", "#Tips"],
                        )
                    )

                # Friday: Agent spotlight + IG Reel
                elif weekday == 4:  # Friday
                    slots.append(
                        ContentSlot(
                            day=day,
                            platform="YouTube Short",
                            content_type="Agent Spotlight",
                            title=f"Agente {['Correo', 'Calendario', 'Documentos', 'Redes', 'Vigia'][week_idx % 5]} en accion",
                            description="Short spotlight de un agente especifico",
                            script_source="flow_studio_aigestion.py SCRIPT_4 Agent Squad",
                            best_time=cls.BEST_TIMES["YouTube Short"],
                            estimated_reach="8K-30K views",
                            hashtags=["#AIGestion", "#AgenteIA", "#Shorts", "#Automatizacion"],
                        )
                    )
                    slots.append(
                        ContentSlot(
                            day=day,
                            platform="Instagram",
                            content_type="Reel",
                            title="Daniela presenta AIGestion (Reel)",
                            description="Reel de presentacion para Instagram",
                            script_source="brand_kit.py ViralAnnouncements daniela_intro",
                            best_time="21:00",
                            estimated_reach="5K-20K views",
                            hashtags=[
                                "#AIGestion",
                                "#DanielaAI",
                                "#Reels",
                                "#IA",
                                "#CiberEjecutiva",
                            ],
                        )
                    )

                # Saturday: Long-form epic + Twitter
                elif weekday == 5:  # Saturday
                    slots.append(
                        ContentSlot(
                            day=day,
                            platform="YouTube Long",
                            content_type="Epic Content",
                            title="Contenido epic semanal (rotacion)",
                            description="Rotacion: Tour / Universe / Before-After / Documentary",
                            script_source="flow_studio_aigestion.py EpicFlowIdeas (rotacion semanal)",
                            best_time=cls.BEST_TIMES["YouTube Long"],
                            estimated_reach="5K-15K views",
                            hashtags=["#AIGestion", "#IA", "#Epic", "#FuturoDeTrabajo"],
                        )
                    )
                    slots.append(
                        ContentSlot(
                            day=day,
                            platform="Instagram",
                            content_type="Carousel",
                            title="Carousel semanal educativo",
                            description="Carousel de 7 slides sobre AIGestion",
                            script_source="brand_kit.py ViralAnnouncements social_carousel_1",
                            best_time="12:00",
                            estimated_reach="2K-8K views",
                            hashtags=["#AIGestion", "#IA", "#Carousel", "#Productividad"],
                        )
                    )

                # Sunday: Batch day + Twitter + IG Story
                elif weekday == 6:  # Sunday
                    slots.append(
                        ContentSlot(
                            day=day,
                            platform="YouTube Short",
                            content_type="Motivation",
                            title="Daniela: Tu tiempo vale mas",
                            description="Short motivacional dominical",
                            script_source="viral_content_factory.py ScriptEngine",
                            best_time=cls.BEST_TIMES["YouTube Short"],
                            estimated_reach="10K-40K views",
                            hashtags=["#AIGestion", "#Motivacion", "#Domingo", "#Shorts"],
                        )
                    )
                    slots.append(
                        ContentSlot(
                            day=day,
                            platform="Twitter/X",
                            content_type="Summary Thread",
                            title="Resumen semanal: lo que AIGestion hizo esta semana",
                            description="Thread recopilando contenido de la semana",
                            script_source="viral_content_factory.py ChannelManager",
                            best_time=cls.BEST_TIMES["Twitter/X"],
                            estimated_reach="3K-15K impressions",
                            hashtags=["#AIGestion", "#Resumen", "#Semanal", "#IA"],
                        )
                    )

                # Daily: Short (every day except when long-form is posted)
                if weekday not in [0, 2, 5]:  # Not Mon/Wed/Sat (those have long-form)
                    slots.append(
                        ContentSlot(
                            day=day,
                            platform="TikTok",
                            content_type="Daily Short",
                            title="Clip del dia (trend/hook viral)",
                            description="Short diario siguiendo tendencia del momento",
                            script_source="viral_content_factory.py TrendHunter + ScriptEngine",
                            best_time=cls.BEST_TIMES["TikTok"],
                            estimated_reach="5K-30K views",
                            hashtags=["#AIGestion", "#IA", "#FYP", "#Trend"],
                        )
                    )

        return slots

    @classmethod
    def get_stats(cls, slots: list[ContentSlot]) -> dict:
        """Get statistics about the calendar."""
        platform_count = {}
        type_count = {}
        for s in slots:
            platform_count[s.platform] = platform_count.get(s.platform, 0) + 1
            type_count[s.content_type] = type_count.get(s.content_type, 0) + 1
        return {
            "total_slots": len(slots),
            "by_platform": platform_count,
            "by_type": type_count,
            "platforms_active": len(platform_count),
            "content_types": len(type_count),
        }

    @classmethod
    def export_calendar_json(cls, slots: list[ContentSlot], output_path: str = None) -> str:

        path = output_path or str(BASE_DIR / "static" / "brand" / "content_calendar_month.json")
        data = [
            {
                "day": s.day,
                "platform": s.platform,
                "content_type": s.content_type,
                "title": s.title,
                "description": s.description,
                "script_source": s.script_source,
                "best_time": s.best_time,
                "estimated_reach": s.estimated_reach,
                "hashtags": s.hashtags,
            }
            for s in slots
        ]
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return path


# ============================================================================
# WEEK 1 READY-TO-POST CONTENT
# ============================================================================


class Week1Content:
    """Fully written, ready-to-post content for the first week."""

    MONDAY = {
        "day": "Lunes",
        "platform": "YouTube Long (8 min)",
        "title": "Que es AIGestion y como puede transformar tu negocio",
        "script": (
            "Usar TutorialTemplates.TUTORIALS[0] completo del modulo brand_kit.py. "
            "7 fases: Hook (0-15s) -> Intro Daniela (15-45s) -> Problema (45-90s) -> "
            "Solucion (90-180s) -> Demo Live (180-300s) -> Pricing (300-360s) -> CTA (360-420s). "
            "Voiceover: edge-tts ElviraNeural. B-roll: screen recordings de AIGestion. "
            "Thumbnail: thumb_template.svg con titulo 'QUE ES AIGESTION?'"
        ),
        "youtube_description": (
            "AIGestion es la plataforma de gestion inteligente que usa IA para automatizar "
            "tu trabajo. En este video te explico como funciona, que puede hacer por ti, "
            "y como empezar gratis.\n\n"
            "TIMESTAMPS:\n"
            "0:00 Introduccion\n"
            "0:15 Conoce a Daniela\n"
            "0:45 El problema (2.8 hrs perdidas al dia)\n"
            "1:30 La solucion: AIGestion\n"
            "3:00 Demo en vivo\n"
            "5:00 Planes y precios\n"
            "6:00 Como empezar\n\n"
            "Web: aigestion.net\n"
            "Gratis para empezar\n\n"
            "#AIGestion #IA #Productividad #Automatizacion #GestionEmpresarial"
        ),
        "youtube_tags": [
            "AIGestion",
            "inteligencia artificial",
            "gestion empresarial",
            "automatizacion",
            "productividad",
            "IA gestion",
            "Daniela AI",
            "Ciber-Ejecutiva",
            "gestion inteligente",
            "agentes IA",
            "automatizacion empresarial",
        ],
    }

    TUESDAY = {
        "day": "Martes",
        "platform": "YouTube Short + TikTok (45s)",
        "title": "PERDISTE 3 HORAS hoy (y no lo sabias)",
        "script": (
            "Usar ViralAnnouncements.ANNOUNCEMENTS[0] (launch_epic). "
            "7 escenas: 0-3s 'PERDISTE 3 HORAS HOY' -> 3-8s tareas repetitivas -> "
            "8-15s logo AIGestion -> 15-25s dashboard en accion -> 25-35s '30 hrs/semana' -> "
            "35-40s 'aigestion.net' -> 40-45s 'SUSCRIBETE'. "
            "Generar con Flow: usar SCRIPT_1 veo_prompts scene 4-6. "
            "TikTok: anadir trend audio del momento."
        ),
        "tiktok_caption": (
            "Si gastas mas de 3 horas en tareas repetitivas, estas perdiendo el 40% "
            "de tu productividad. AIGestion lo cambia todo. 30 horas/semana ahorradas. "
            "Gratis en aigestion.net\n\n"
            "#AIGestion #IA #Productividad #Automatizacion #FYP #TipsEmpresariales"
        ),
    }

    WEDNESDAY = {
        "day": "Miercoles",
        "platform": "YouTube Long (5 min) + LinkedIn Carousel",
        "title": "Cronicas de Daniela Ep.1: La Startup en Caos",
        "script": (
            "Usar EpicFlowIdeas epic_01 (Cronicas de Daniela). Episodio 1: Startup en caos. "
            "Flow: Storyboard Studio con SCRIPT_1 o script nuevo. "
            "5-7 escenas Veo 3.1 de 8s cada una. Lock @Daniela ingredient. "
            "Estilo: Cinematic Photorealistic. "
            "LinkedIn: usar ViralAnnouncements social_carousel_1 (7 slides)."
        ),
        "linkedin_text": (
            "5 formas en que la IA gestiona tu negocio mientras duermes:\n\n"
            "1. Correo automatico: clasifica, responde y archiva 50+ emails/dia\n"
            "2. Agenda inteligente: optimiza reuniones, evita conflictos\n"
            "3. Reportes automaticos: genera, guarda y publica en Drive\n"
            "4. Redes sociales: crea y publica contenido diario\n"
            "5. Monitoreo 24/7: alertas en tiempo real, sin que hagas nada\n\n"
            "Todo esto por 0 euros. En aigestion.net\n\n"
            "#AIGestion #IA #Automatizacion #Productividad #GestionEmpresarial"
        ),
    }

    THURSDAY = {
        "day": "Jueves",
        "platform": "YouTube Short + Twitter Thread",
        "title": "Antes vs Despues de AIGestion (CHOCKING)",
        "script": (
            "Usar flow_studio_aigestion.py SCRIPT_3 (Before/After). "
            "7 escenas Veo 3.1 con split screen. Generar L y R por separado. "
            "Condensar a 60s para Short. "
            "Twitter: usar ViralAnnouncements twitter_thread (9 tweets)."
        ),
        "twitter_thread": [
            "1/ AIGestion usa 67 herramientas gratuitas de Google para gestionar empresas enteras.\n\nEl valor total: 2,847 EUR/mes.\nEl costo: 0.\n\nTe cuento cuales y como:",
            "2/ Gemini CLI: IA gratis. Gemini 3 Pro. 60 RPM. 1,000 peticiones/dia.\n\nAIGestion lo usa como motor principal. Sin API key.\n\nEsto solo vale 20 EUR/mes (vs ChatGPT+).",
            "3/ BigQuery: 1 TB de consultas gratis/mes.\n\nAIGestion guarda todos los logs de actividad aqui. Analytics empresarial sin pagar.",
            "4/ Google Cloud Free Tier: 31 servicios always-free.\nCompute, Cloud Run, Functions, Firestore, Storage, Pub/Sub.\n\nInfraestructura completa gratis.",
            "5/ Google Labs: NotebookLM, Veo 2, ImageFX, Jules, Stitch.\n\nAIGestion usa todo para crear contenido automaticamente.",
            "6/ YouTube Data API: 10K unidades/dia gratis.\nAIGestion rastrea tendencias y analiza canales.",
            "7/ Firebase: 50K usuarios, 1GB Firestore, 10GB Hosting, FCM ilimitado.\n\nNotificaciones push gratis.",
            "8/ Resultado:\n\nSin AIGestion: 2,847 EUR/mes\nCon AIGestion: 0 EUR/mes\n\nTodo integrado en un dashboard.\n\naigestion.net",
            "9/ Sigue a @AIGestion para mas. Proximo hilo: configuracion paso a paso.\n\nRT si te fue util",
        ],
    }

    FRIDAY = {
        "day": "Viernes",
        "platform": "YouTube Short + Instagram Reel",
        "title": "Conoce a DANIKA - la IA que gestiona empresas",
        "script": (
            "Usar ViralAnnouncements daniela_intro (30s, 7 escenas). "
            "Flow: generar con Veo 3.1 usando @Daniela ingredient. "
            "Estilo: Cinematic Photorealistic. "
            "Instagram Reel: misma version, anadir texto overlay."
        ),
        "instagram_caption": (
            "Ella no es humana. Pero gestiona mejor que cualquier ejecutivo que conozcas.\n\n"
            "Se llama Daniela. Es la Ciber-Ejecutiva de AIGestion.\n"
            "Gestiona correo, agenda, documentos, redes sociales. 24/7.\n\n"
            "Tu trabajas 8 horas. Ella trabaja siempre.\n\n"
            "aigestion.net - Gratis para empezar\n\n"
            "#AIGestion #DanielaAI #CiberEjecutiva #IA #Reels #GestionEmpresarial"
        ),
    }

    SATURDAY = {
        "day": "Sabado",
        "platform": "YouTube Long (5 min) + Instagram Carousel",
        "title": "El Tour de AIGestion - Recorrido Virtual",
        "script": (
            "Usar EpicFlowIdeas epic_03 (El Tour de AIGestion). "
            "Flow: Storyboard Studio script de tour. 10 scenes Veo 3.1 de 8s. "
            "Lock: @Daniela + @AIGestion Office + @Dashboard + @City. "
            "Instagram: carousel de 7 slides con snapshots del tour."
        ),
    }

    SUNDAY = {
        "day": "Domingo",
        "platform": "YouTube Short + Twitter Summary",
        "title": "Tu tiempo vale mas (Motivacional)",
        "script": (
            "Short motivacional dominical. Script original: "
            "'Cada hora que pierdes en tareas repetitivas es una hora que no "
            "puedes recuperar. 30 horas a la semana. 1,500 al ano. "
            "Que harías con 1,500 horas extra? Viajar. Aprender. Estar con los tuyos. "
            "AIGestion te devuelve esas horas. aigestion.net. Gratis. Hoy.' "
            "Veo 3.1: @Daniela en oficina al atardecer, mirando la ciudad. "
            "Tono: reflexivo, inspirador."
        ),
        "twitter_summary": (
            "Esta semana en AIGestion:\n\n"
            "Lunes: Tutorial 'Que es AIGestion' (8 min)\n"
            "Martes: Short 'Perdiste 3 horas' (45s)\n"
            "Miercoles: Cronicas de Daniela Ep.1 (5 min)\n"
            "Jueves: Antes vs Despues (Short + Thread)\n"
            "Viernes: Conoce a Daniela (Reel)\n"
            "Sabado: Tour de AIGestion (5 min)\n"
            "Domingo: Tu tiempo vale mas (Short)\n\n"
            "Todo el contenido: gratis.\n"
            "La plataforma: gratis.\n"
            "Tu tiempo recuperado: no tiene precio.\n\n"
            "aigestion.net | #AIGestion"
        ),
    }

    @classmethod
    def get_week(cls) -> list[dict]:

        return [
            cls.MONDAY,
            cls.TUESDAY,
            cls.WEDNESDAY,
            cls.THURSDAY,
            cls.FRIDAY,
            cls.SATURDAY,
            cls.SUNDAY,
        ]

    @classmethod
    def export_json(cls, output_path: str = None) -> str:

        path = output_path or str(BASE_DIR / "static" / "brand" / "week1_ready_to_post.json")
        data = cls.get_week()
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return path


# ============================================================================
# UNIVERSE BIBLE - Master Narrative Document
# ============================================================================


class UniverseBible:
    """Master narrative document for the AIGestion content universe."""

    BIBLE = {
        "universe_name": "AIGestion Universe",
        "tagline": "Gestion Inteligente con Inteligencia Artificial",
        "setting": {
            "world": "Un futuro cercano donde la IA y los humanos coexisten en la gestion empresarial",
            "primary_location": "Oficina virtual de cristal de Daniela, con vistas a una metropolis ciberpunk",
            "visual_aesthetic": "Cyberpunk ejecutivo: oscuro, neón cyan/magenta, holografias, glass",
            "tone": "Profesional pero cinematografico. No distopia, no utopia. Optimismo tecnologico.",
        },
        "characters": {
            "daniela": {
                "role": "Ciber-Ejecutiva. Líder y coordinadora de todos los agentes.",
                "arc": "Daniela evoluciona de presentadora a mentora. Cada episodio revela mas de su capacidad y de su 'personalidad' creciente.",
                "relationships": {
                    "correo": "Su agente mas rapido, confia en el para lo urgente",
                    "calendario": "Su organizadora, mantiene todo en orden",
                    "documentos": "Su fuente de conocimiento, le da los datos",
                    "redes": "Su voz creativa, la que conecta con el mundo",
                    "vigia": "Su guardian silencioso, siempre alerta",
                },
            },
            "users": {
                "type": "Los usuarios reales de AIGestion son los protagonistas humanos",
                "examples": [
                    "Laura: emprendedora nerviosa que descubre AIGestion (tutorial series)",
                    "Carlos: businessman estresado que recupera su vida (before/after)",
                    "Startup Team: equipo en caos que se transforma (Cronicas Ep.1)",
                    "Agencia Owner: agencia saturada que escala (Cronicas Ep.4)",
                ],
            },
        },
        "story_arcs": {
            "arc_1_intro": {
                "title": "Introduccion al Universo",
                "episodes": "Launch Commercial + Tutorial 1 + Tour",
                "goal": "Presentar AIGestion, Daniela, y el concepto de gestion con IA",
            },
            "arc_2_agents": {
                "title": "El Escuadron se Reune",
                "episodes": "Agent Squad + Agent Spotlights (5 episodios) + Backstage",
                "goal": "Presentar cada agente individualmente y como trabajan en equipo",
            },
            "arc_3_transformations": {
                "title": "Transformaciones Reales",
                "episodes": "Cronicas de Daniela (6 episodios) + Before/After series",
                "goal": "Mostrar casos reales de empresas transformadas",
            },
            "arc_4_future": {
                "title": "El Futuro del Trabajo",
                "episodes": "Documental 3 partes + Conversaciones con Daniela",
                "goal": "Posicionar a AIGestion como thought leader en el futuro de la gestion",
            },
            "arc_5_universe": {
                "title": "Expansion del Universo",
                "episodes": "Nuevos productos como nuevas historias dentro del mismo mundo",
                "goal": "Crear continuidad narrativa que genere fans recurrentes",
            },
        },
        "content_pillars": [
            {
                "pillar": "Educacion",
                "description": "Tutoriales, guias, como-funciona",
                "formats": ["YouTube Long", "LinkedIn Article", "Twitter Thread"],
                "frequency": "Semanal",
            },
            {
                "pillar": "Entretenimiento",
                "description": "Cronicas, shorts virales, agent spotlights",
                "formats": ["YouTube Short", "TikTok", "Instagram Reel"],
                "frequency": "Diario",
            },
            {
                "pillar": "Inspiracion",
                "description": "Transformaciones, motivacion, futuro del trabajo",
                "formats": ["YouTube Long", "Instagram Carousel", "Twitter Summary"],
                "frequency": "Semanal",
            },
            {
                "pillar": "Comunidad",
                "description": "Retos, Q&A, contenido generado por usuarios",
                "formats": ["YouTube Long (Retos)", "Instagram Stories", "Twitter Polls"],
                "frequency": "Semanal",
            },
        ],
        "production_rules": [
            "Daniela SIEMPRE aparece en estado profesional. Nada informal.",
            "Los colores cyan y magenta estan en TODO contenido visual.",
            "Todo video termina con el logo AIGestion + URL aigestion.net",
            "Todo CTA es claro y unico: 'aigestion.net - Gratis'",
            "Nunca prometer resultados sin mostrar datos reales",
            "La oficida de cristal + ciudad ciberpunk es el fondo recurrente",
            "Los 5 agentes siempre tienen sus colores: azul, oro, verde, magenta, rojo",
            "El tono es optimista: la IA ayuda, no reemplaza",
        ],
    }

    @classmethod
    def export_json(cls, output_path: str = None) -> str:

        path = output_path or str(BASE_DIR / "static" / "brand" / "universe_bible.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(cls.BIBLE, f, ensure_ascii=False, indent=2)
        return path


# ============================================================================
# CLI
# ============================================================================


def print_status():
    print("=" * 70)
    print("  AIGestion Content Calendar + Character Roster + Universe Bible")
    print("=" * 70)
    print()

    print("CHARACTER ROSTER (6 characters):")
    for c in CharacterRoster.all_characters():
        print(f"  - {c.name} [{c.role}]")
        print(f"    Color: {c.color} ({c.hex_color})")
        print(f"    Abilities: {len(c.abilities)}")
    print()

    slots = MonthlyCalendar.generate_month(2026, 9)
    stats = MonthlyCalendar.get_stats(slots)
    print(f"MONTHLY CALENDAR ({stats['total_slots']} slots):")
    for platform, count in stats["by_platform"].items():
        print(f"  {platform}: {count} posts")
    print(f"  Platforms active: {stats['platforms_active']}")
    print(f"  Content types: {stats['content_types']}")
    print()

    print("WEEK 1 READY-TO-POST (7 days):")
    for day in Week1Content.get_week():
        print(f"  {day['day']}: [{day['platform']}] {day['title']}")
    print()

    print("UNIVERSE BIBLE:")
    bible = UniverseBible.BIBLE
    print(f"  Universe: {bible['universe_name']}")
    print(f"  Story arcs: {len(bible['story_arcs'])}")
    print(f"  Content pillars: {len(bible['content_pillars'])}")
    print(f"  Production rules: {len(bible['production_rules'])}")
    print()

    print("FILES:")
    print("  content_calendar.py (this module)")
    print("  static/brand/character_roster.json")
    print("  static/brand/content_calendar_month.json")
    print("  static/brand/week1_ready_to_post.json")
    print("  static/brand/universe_bible.json")
    print()
    print("=" * 70)


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print_status()
    elif sys.argv[1] == "characters":
        path = CharacterRoster.export_json()
        print(f"Character roster exported to {path}")
    elif sys.argv[1] == "calendar":
        slots = MonthlyCalendar.generate_month(2026, 9)
        path = MonthlyCalendar.export_calendar_json(slots)
        stats = MonthlyCalendar.get_stats(slots)
        print(f"Calendar exported to {path}")
        print(f"Total slots: {stats['total_slots']}")
    elif sys.argv[1] == "week1":
        path = Week1Content.export_json()
        print(f"Week 1 content exported to {path}")
    elif sys.argv[1] == "bible":
        path = UniverseBible.export_json()
        print(f"Universe bible exported to {path}")
    elif sys.argv[1] == "all":
        CharacterRoster.export_json()
        slots = MonthlyCalendar.generate_month(2026, 9)
        MonthlyCalendar.export_calendar_json(slots)
        Week1Content.export_json()
        UniverseBible.export_json()
        print("All files exported to static/brand/")
    else:
        print_status()
