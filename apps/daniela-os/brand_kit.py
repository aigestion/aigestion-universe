#!/usr/bin/env python3
"""
AIGestion Brand Kit - Complete Brand Identity & Asset Management
================================================================
Central module for all AIGestion brand assets, templates, and content generation.

Brand Identity:
  - Name: AIGestion
  - Mascot: Daniela (Ciber-Ejecutiva)
  - Colors: Neon Cyan #00ffff / Magenta #ff0055 / Dark #0b0f19
  - Aesthetic: Cyberpunk Executive / Glass Office / Holographic Dashboards
  - Voice: Professional, Futuristic, Confident, Tech-Forward
"""

import json
from dataclasses import dataclass, field
from pathlib import Path

# ============================================================================
# BRAND CONSTANTS
# ============================================================================

BASE_DIR = Path(__file__).parent
BRAND_DIR = BASE_DIR / "static" / "brand"
INTRO_DIR = BRAND_DIR / "intro"
OUTRO_DIR = BRAND_DIR / "outro"
THUMB_DIR = BRAND_DIR / "thumbnails"
SOCIAL_DIR = BRAND_DIR / "social"


class Colors:
    """AIGestion brand color palette."""

    CYAN = "#00ffff"  # Primary - Neon Cyan
    CYAN_DARK = "#0099ff"  # Primary gradient end
    MAGENTA = "#ff0055"  # Secondary - Hot Magenta
    MAGENTA_LIGHT = "#ff00aa"  # Secondary gradient end
    DARK = "#0b0f19"  # Background - Deep Space
    DARK_BLUE = "#0f1428"  # Background variant
    PANEL = "#1a1f35"  # Card/Panel background
    GRAY = "#3a4a6a"  # Muted text
    WHITE = "#ffffff"  # Headlines on dark
    SUCCESS = "#00ff88"  # Accent green (success states)
    WARNING = "#ffaa00"  # Accent amber (warning states)


class Typography:
    """AIGestion typography system."""

    HEADING = "'Segoe UI', 'Arial Black', sans-serif"
    BODY = "'Segoe UI', sans-serif"
    MONO = "'Consolas', 'Courier New', monospace"
    SIZES = {
        "display": 96,  # Hero text
        "h1": 72,  # Main titles
        "h2": 52,  # Section headers
        "h3": 36,  # Subsection
        "body_lg": 28,  # Large body
        "body": 20,  # Standard body
        "caption": 16,  # Small text
        "micro": 12,  # Fine print
    }


class BrandAssets:
    """Paths to all brand assets."""

    LOGO_MAIN = BRAND_DIR / "logo_aigestion.svg"
    LOGO_ICON = BRAND_DIR / "logo_icon.svg"
    LOGO_HORIZONTAL = BRAND_DIR / "logo_horizontal.svg"
    INTRO_TEMPLATE = INTRO_DIR / "intro_template.svg"
    OUTRO_TEMPLATE = OUTRO_DIR / "outro_template.svg"
    THUMB_YOUTUBE = THUMB_DIR / "thumb_template.svg"
    THUMB_SHORTS = THUMB_DIR / "thumb_shorts.svg"
    DANIELA_IMAGES = [
        BASE_DIR / "static" / "daniela_official.png",
        BASE_DIR / "static" / "daniela.png",
        BASE_DIR / "static" / "daniela.jpg",
        BASE_DIR / "static" / "official_daniela.png",
        BASE_DIR / "static" / "daniela_avatar.jpg",
        BASE_DIR / "static" / "daniela_foto.jpg",
    ]


class DanielaPersona:
    """Daniela - AIGestion's Ciber-Ejecutiva mascot identity."""

    NAME = "Daniela"
    ROLE = "Ciber-Ejecutiva"
    DESCRIPTION = (
        "Daniela es la Ciber-Ejecutiva de AIGestion. Una mujer profesional "
        "con traje de alta costura futurista, que opera desde una oficina "
        "virtual de cristal con vistas nocturnas a una metropolis ciberpunk. "
        "Su presencia combina elegancia ejecutiva con tecnologia de punta."
    )
    VISUAL_TRAITS = {
        "attire": "Traje de alta costura futurista oscuro con detalles neón",
        "colors": "Cian neón y magenta como acentos",
        "setting": "Oficina virtual de cristal, metropolis ciberpunk nocturna",
        "lighting": "Neón cian y magenta, hologramas ambientales",
        "expression": "Confianza ejecutiva, mirada directa, sonrisa sutil",
    }
    PERSONALITY = {
        "tone": "Profesional, directa, segura de sí misma",
        "expertise": "Gestion empresarial, IA, automatizacion, estrategia",
        "voice": "ElviraNeural (es-ES) - firme pero elegante",
        "pacing": "Medido, claro, sin prisas pero sin pausas innecesarias",
    }
    IMAGE_PROMPT = (
        "Cinematic high-end commercial photo of Daniela, an elegant AI executive "
        "woman wearing a sleek futuristic dark suit with neon cyan and magenta "
        "accents. She stands in a glass-walled virtual office overlooking a "
        "cyberpunk metropolis at night. Holographic dashboards float around her. "
        "Professional lighting with cyan and magenta neon glow. Confident, "
        "executive presence, direct gaze, subtle smile. 8K, photorealistic."
    )


class BrandVoice:
    """AIGestion brand voice guidelines."""

    PILLARS = [
        "Inteligente: hablamos de IA y gestion con dominio del tema",
        "Futurista: vision de lo que viene, no de lo que ya existe",
        "Confiado: sin dudar, sin pedir perdon por saber",
        "Accesible: complejo si, incomprensible no",
        "Directo: valor en cada frase, sin paja",
    ]
    DO = [
        "Usar datos y numeros concretos",
        "Mostrar resultados, no promesas",
        "Referenciar tecnologia actual (Gemini, GPT, Claude, etc.)",
        "Hablar de automatizacion y eficiencia",
        "Incluir CTAs claros en todo contenido",
    ]
    DONT = [
        "Usar jerga sin explicacion",
        "Prometer cosas que no podemos cumplir",
        "Ser excesivamente informal o usar memes",
        "Hablar de la competencia negativamente",
        "Usar lenguaje tecnico sin contexto",
    ]
    HASHTAGS = [
        "#AIGestion",
        "#IA",
        "#InteligenciaArtificial",
        "#Automatizacion",
        "#GestionEmpresarial",
        "#FuturoDeTrabajo",
        "#DanielaAI",
        "#CiberEjecutiva",
        "#TransformacionDigital",
    ]


# ============================================================================
# VIDEO TEMPLATES
# ============================================================================


@dataclass
class VideoTemplate:
    """Video template specification."""

    name: str
    format: str  # "16:9" or "9:16"
    resolution: tuple[int, int]
    duration_sec: int
    blocks: list[dict] = field(default_factory=list)


class VideoTemplates:
    """Pre-built video templates for AIGestion content."""

    INTRO_VERTICAL = VideoTemplate(
        name="intro_vertical_9x16",
        format="9:16",
        resolution=(1080, 1920),
        duration_sec=8,
        blocks=[
            {
                "phase": "logo_reveal",
                "duration": 3,
                "description": "Logo AIGestion aparece con efecto neón desde el centro",
                "svg_template": "intro/intro_template.svg",
                "animation": "scale(0) -> scale(1) + opacity(0) -> opacity(1)",
                "ffmpeg_filter": "fade=in:0:30,scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2",
            },
            {
                "phase": "title_text",
                "duration": 3,
                "description": "Texto AIGestion + tagline aparece con glow",
                "animation": "fade in + blur to sharp",
                "ffmpeg_filter": "fade=t=in:st=3:d=1,fade=t=out:st=7:d=1",
            },
            {
                "phase": "transition_out",
                "duration": 2,
                "description": "Flash cyan -> transicion al contenido",
                "animation": "quick zoom + flash",
                "ffmpeg_filter": "fade=t=out:st=6:d=1",
            },
        ],
    )

    OUTRO_VERTICAL = VideoTemplate(
        name="outro_vertical_9x16",
        format="9:16",
        resolution=(1080, 1920),
        duration_sec=10,
        blocks=[
            {
                "phase": "gracias_text",
                "duration": 3,
                "description": "GRACIAS aparece grande con efecto neón",
                "svg_template": "outro/outro_template.svg",
                "animation": "fade in + scale",
                "ffmpeg_filter": "fade=in:0:30",
            },
            {
                "phase": "cta_buttons",
                "duration": 4,
                "description": "Botones de Suscribete / Like / Comenta aparecen secuencialmente",
                "animation": "slide in from bottom",
                "ffmpeg_filter": "fade=t=in:st=3:d=1",
            },
            {
                "phase": "logo_social",
                "duration": 3,
                "description": "Logo + handles sociales + fade out",
                "animation": "fade out",
                "ffmpeg_filter": "fade=t=out:st=7:d=3",
            },
        ],
    )

    COMMERCIAL_4BLOCK = VideoTemplate(
        name="commercial_4block_16s",
        format="9:16",
        resolution=(1080, 1920),
        duration_sec=64,
        blocks=[
            {
                "phase": "caos_inicial",
                "duration": 16,
                "description": "Caos inicial: tareas manuales, estres, desorganizacion",
                "visual": "Pantalla dividida con multiples apps, notificaciones, reloj acelerado",
                "audio": "Sonido de teclado rapido, notificaciones, tono estresante",
                "color_tone": "Tono grisaceo, sobresaturado",
            },
            {
                "phase": "daniela_appearance",
                "duration": 16,
                "description": "Daniela aparece: transicion neón, presenta AIGestion",
                "visual": "Daniela en su oficina de cristal, hologramas, dashboard",
                "audio": "Musica electronica crescendo, voz ElviraNeural presenta",
                "color_tone": "Neón cian y magenta, fondo oscuro",
            },
            {
                "phase": "metrics_demo",
                "duration": 16,
                "description": "Demo de capacidades: metrics, Google Drive sync, automatizacion",
                "visual": "Dashboard con datos animados, graficos subiendo, Drive sync",
                "audio": "Sonidos de notificacion positivos, voz describe features",
                "color_tone": "Cian dominante con acentos magenta",
            },
            {
                "phase": "cta_cierre",
                "duration": 16,
                "description": "CTA + logo + URL + next steps",
                "visual": "Logo AIGestion grande, URL aigestion.net, QR code",
                "audio": "Musica epica final, voz llama a accion",
                "color_tone": "Glow neón completo, fondo estrellado",
            },
        ],
    )

    @classmethod
    def get_intro_ffmpeg_command(cls, output_path: str, bg_image: str = None) -> str:
        """Generate ffmpeg command to render intro from SVG template."""
        svg_path = str(BrandAssets.INTRO_TEMPLATE)
        bg = bg_image or f"-i {svg_path}"
        return (
            f"ffmpeg -y -loop 1 {bg} -t 8 "
            f'-vf "fade=t=in:st=0:d=1,fade=t=out:st=6:d=2,'
            f"scale=1080:1920:force_original_aspect_ratio=decrease,"
            f'pad=1080:1920:(ow-iw)/2:(oh-ih)/2" '
            f'-c:v libx264 -pix_fmt yuv420p -r 30 "{output_path}"'
        )

    @classmethod
    def get_outro_ffmpeg_command(cls, output_path: str, bg_image: str = None) -> str:
        """Generate ffmpeg command to render outro from SVG template."""
        svg_path = str(BrandAssets.OUTRO_TEMPLATE)
        bg = bg_image or f"-i {svg_path}"
        return (
            f"ffmpeg -y -loop 1 {bg} -t 10 "
            f'-vf "fade=t=in:st=0:d=1,fade=t=out:st=7:d=3,'
            f"scale=1080:1920:force_original_aspect_ratio=decrease,"
            f'pad=1080:1920:(ow-iw)/2:(oh-ih)/2" '
            f'-c:v libx264 -pix_fmt yuv420p -r 30 "{output_path}"'
        )

    @classmethod
    def get_commercial_ffmpeg_pipeline(cls, output_path: str, blocks: list[str]) -> str:
        """Generate ffmpeg pipeline for 4-block commercial."""
        if len(blocks) != 4:
            raise ValueError("Commercial requires exactly 4 block inputs")
        concat_file = "/tmp/aigestion_concat.txt"
        parts = []
        for i, block in enumerate(blocks):
            part_path = f"/tmp/aigestion_block_{i}.mp4"
            filter_str = (
                "fade=t=in:st=0:d=0.5,fade=t=out:st=15.5:d=0.5,"
                "scale=1080:1920:force_original_aspect_ratio=decrease,"
                "pad=1080:1920:(ow-iw)/2:(oh-ih)/2"
            )
            cmd = (
                f'ffmpeg -y -i "{block}" -t 16 -vf "{filter_str}" '
                f'-c:v libx264 -pix_fmt yuv420p -r 30 "{part_path}"'
            )
            parts.append(cmd)
        concat_cmd = (
            f"printf \"file '/tmp/aigestion_block_0.mp4'\n"
            f"file '/tmp/aigestion_block_1.mp4'\n"
            f"file '/tmp/aigestion_block_2.mp4'\n"
            f"file '/tmp/aigestion_block_3.mp4'\n\" > {concat_file} && "
            f'ffmpeg -y -f concat -safe 0 -i {concat_file} -c copy "{output_path}"'
        )
        return " && ".join(parts + [concat_cmd])


# ============================================================================
# TUTORIAL SCRIPT TEMPLATES
# ============================================================================


@dataclass
class TutorialScript:
    """Tutorial script template."""

    title: str
    duration_min: int
    format: str  # "16:9" or "9:16"
    sections: list[dict] = field(default_factory=list)


class TutorialTemplates:
    """Pre-built tutorial script templates for AIGestion."""

    TUTORIALS: list[TutorialScript] = [
        TutorialScript(
            title="Que es AIGestion y como puede transformar tu negocio",
            duration_min=8,
            format="16:9",
            sections=[
                {
                    "phase": "HOOK (0-15s)",
                    "visual": "Pantalla con caos de tareas manuales, reloj corriendo",
                    "narration": "Si gastas mas de 3 horas al dia en tareas repetitivas, "
                    "estas perdiendo el 40% de tu productividad. "
                    "Pero hay una solucion. Se llama AIGestion.",
                    "on_screen_text": "¿Gastas 3+ horas en tareas repetitivas?",
                    "b_roll": "Screenshots de Excel, Gmail, calendar, Notion desordenados",
                },
                {
                    "phase": "INTRO (15-45s)",
                    "visual": "Logo AIGestion aparece, Daniela en su oficina",
                    "narration": "Hola, soy Daniela, la Ciber-Ejecutiva de AIGestion. "
                    "AIGestion es una plataforma de gestion inteligente "
                    "que usa IA para automatizar tu trabajo. "
                    "En este video te muestro como funciona.",
                    "on_screen_text": "Daniela - Ciber-Ejecutiva | AIGestion",
                    "b_roll": "Daniela holograma, dashboard AIGestion",
                },
                {
                    "phase": "PROBLEMA (45-90s)",
                    "visual": "Grafico: tiempo perdido en tareas manuales",
                    "narration": "El trabajador promedio pierde 2.8 horas diarias "
                    "en tareas que una IA podria hacer automaticamente. "
                    "Eso son 14 horas a la semana. 60 al mes. "
                    "Casi un mes entero de trabajo perdido.",
                    "on_screen_text": "2.8 hrs/dia = 60 hrs/mes PERDIDAS",
                    "b_roll": "Infografia animada con numeros creciendo",
                },
                {
                    "phase": "SOLUCION (90-180s)",
                    "visual": "Demo de AIGestion: dashboard, agentes, automatizacion",
                    "narration": "AIGestion automatiza eso. Tienes agentes de IA que "
                    "gestionan tu correo, agenda, documentos, analiticas "
                    "y redes sociales. Todo desde un dashboard. "
                    "Conecta con Google Drive, Notion, GitHub, y mas.",
                    "on_screen_text": "Agentes IA | Dashboard Unificado | Google + Notion + GitHub",
                    "b_roll": "Screen recording de AIGestion en accion",
                },
                {
                    "phase": "DEMO LIVE (180-300s)",
                    "visual": "Screen recording real de AIGestion funcionando",
                    "narration": "Mira esto: le pido a Daniela que genere un reporte "
                    "de ventas, lo guarde en Drive, y lo publique en "
                    "mi dashboard. Todo en menos de 30 segundos. "
                    "Y esto es solo el principio.",
                    "on_screen_text": "Demo en vivo - 30 segundos",
                    "b_roll": "Screen recording con cursor moviendose",
                },
                {
                    "phase": "PRICING (300-360s)",
                    "visual": "Tabla de planes con precios",
                    "narration": "AIGestion tiene un plan gratuito que incluye "
                    "los agentes basicos. Y planes de pago desde "
                    "muy poco al mes con todo desbloqueado. "
                    "Te dejo el enlace en la descripcion.",
                    "on_screen_text": "Plan Gratuito | Pro | Enterprise",
                    "b_roll": "Tabla de precios con animacion neón",
                },
                {
                    "phase": "CTA (360-420s)",
                    "visual": "Logo grande + URL + QR code",
                    "narration": "Si quieres dejar de perder tiempo en tareas "
                    "repetitivas, ve a aigestion.net y prueba gratis. "
                    "Suscribete para mas tutoriales de IA y gestion. "
                    "Soy Daniela, y esto era AIGestion.",
                    "on_screen_text": "aigestion.net | SUSCRIBETE",
                    "b_roll": "Logo + URL + QR + social handles",
                },
            ],
        ),
        TutorialScript(
            title="Como configurar tus primeros 3 agentes de IA en AIGestion",
            duration_min=10,
            format="16:9",
            sections=[
                {
                    "phase": "HOOK (0-15s)",
                    "visual": "3 agentes trabajando simultaneamente",
                    "narration": "Estos 3 agentes de IA acaban de hacer en 10 segundos "
                    "lo que a ti te tomaria 2 horas. Te enseño a configurarlos.",
                    "on_screen_text": "3 Agentes IA = 2 horas de trabajo en 10 segundos",
                },
                {
                    "phase": "SETUP (15-60s)",
                    "visual": "Pantalla de configuracion de AIGestion",
                    "narration": "Lo primero: entra a AIGestion y ve a la pestania Agentes. "
                    "Ahi veras una lista de agentes disponibles. "
                    "Vamos a configurar tres: uno de correo, "
                    "uno de calendario, y uno de documentos.",
                    "on_screen_text": "Pestania Agentes | 3 agentes a configurar",
                },
                {
                    "phase": "AGENTE 1: CORREO (60-180s)",
                    "visual": "Config del agente de correo",
                    "narration": "Agente 1: Correo. Conecta tu Gmail. "
                    "El agente leera correos, clasificara por prioridad, "
                    "redactara respuestas, y te avisara solo lo urgente. "
                    "Configura: que correos lee, cada cuanto revisa, "
                    "y que nivel de autonomia tiene.",
                    "on_screen_text": "Agente Correo | Gmail | Clasifica + Responde",
                },
                {
                    "phase": "AGENTE 2: CALENDARIO (180-300s)",
                    "visual": "Config del agente de calendario",
                    "narration": "Agente 2: Calendario. Conecta Google Calendar. "
                    "Este agente agenda reuniones, envia recordatorios, "
                    "reorganiza tu dia si hay conflictos, y te prepara "
                    "un briefing cada manana con tu agenda del dia.",
                    "on_screen_text": "Agente Calendario | Google Calendar | Agenda + Briefing",
                },
                {
                    "phase": "AGENTE 3: DOCUMENTOS (300-420s)",
                    "visual": "Config del agente de documentos",
                    "narration": "Agente 3: Documentos. Conecta Google Drive. "
                    "Este agente genera reportes, resume documentos, "
                    "organiza archivos por proyecto, y mantiene "
                    "todo tu Drive estructurado automaticamente.",
                    "on_screen_text": "Agente Documentos | Google Drive | Reportes + Organizacion",
                },
                {
                    "phase": "RESULTADOS (420-540s)",
                    "visual": "Dashboard mostrando tiempo ahorrado",
                    "narration": "Ahora mira el dashboard. Estos 3 agentes te estan "
                    "ahorrando 4 horas al dia. Y lo mejor: "
                    "aprenden de tus correcciones y mejoran con el tiempo. "
                    "Manana seran mas eficientes que hoy.",
                    "on_screen_text": "4 hrs/dia ahorradas | Aprenden y mejoran",
                },
                {
                    "phase": "CTA (540-600s)",
                    "visual": "Logo + URL + siguiente tutorial",
                    "narration": "Ya tienes 3 agentes trabajando. En el proximo "
                    "video te enseño a crear automatizaciones entre ellos. "
                    "Suscribete para no perdertelo. aigestion.net",
                    "on_screen_text": "Proximo: Automatizaciones | aigestion.net",
                },
            ],
        ),
        TutorialScript(
            title="Automatiza tu negocios completo con AIGestion (caso real)",
            duration_min=12,
            format="16:9",
            sections=[
                {
                    "phase": "HOOK (0-15s)",
                    "visual": "Comparativa: antes vs despues de AIGestion",
                    "narration": "Esta empresa ahorro 30 horas semanales y 2000 euros "
                    "al mes con AIGestion. Te muestro exactamente como.",
                    "on_screen_text": "-30 hrs/semana | -2000 EUR/mes",
                },
                {
                    "phase": "EL NEGOCIO (15-60s)",
                    "visual": "Descripcion del negocio caso de estudio",
                    "narration": "Es una agencia de marketing con 8 empleados. "
                    "Gastaban 30 horas semanales en reportes, "
                    "gestion de clientes, y tareas administrativas. "
                    "Veamos como AIGestion cambio eso.",
                    "on_screen_text": "Agencia Marketing | 8 empleados | 30 hrs perdidas",
                },
                {
                    "phase": "IMPLEMENTACION (60-300s)",
                    "visual": "Paso a paso de implementacion",
                    "narration": "Paso 1: Agentes de correo y calendario para todo el equipo. "
                    "Paso 2: Agente de reportes automaticos para clientes. "
                    "Paso 3: Dashboard unificado con metrics de todos. "
                    "Paso 4: Automatizacion de redes sociales. "
                    "Paso 5: Integracion con Google Drive y Notion.",
                    "on_screen_text": "5 Pasos | De caos a control total",
                },
                {
                    "phase": "RESULTADOS (300-420s)",
                    "visual": "Graficos de antes y despues",
                    "narration": "Resultados en 30 dias: 30 horas/semana recuperadas. "
                    "Tiempo de respuesta a clientes: de 4 horas a 15 minutos. "
                    "Reportes de clientes: de manual semanal a automatico diario. "
                    "Costo: 2000 euros menos al mes en tareas administrativas.",
                    "on_screen_text": "30 hrs/semana | 4h->15min | Manual->Automatico | -2000 EUR",
                },
                {
                    "phase": "TESTIMONIO (420-540s)",
                    "visual": "Testimonio del cliente (texto o voz)",
                    "narration": "El CEO dice: 'AIGestion no es una herramienta, "
                    "es un empleado mas. Y el mejor empleado que tenemos.' "
                    "Ahora la agencia ofrece servicio de gestion "
                    "con IA a sus propios clientes.",
                    "on_screen_text": "'Es el mejor empleado que tenemos' - CEO",
                },
                {
                    "phase": "CTA (540-660s)",
                    "visual": "Logo + URL + info contacto",
                    "narration": "Si quieres resultados como estos para tu negocio, "
                    "ve a aigestion.net. Tenemos plan gratuito para empezar. "
                    "Y si necesitas implementacion personalizada, "
                    "contactanos directamente. Suscribete para mas casos reales.",
                    "on_screen_text": "aigestion.net | Plan Gratis | Implementacion a medida",
                },
            ],
        ),
    ]

    @classmethod
    def get_all_scripts(cls) -> list[dict]:
        """Get all tutorial scripts as dictionaries."""
        return [
            {
                "title": t.title,
                "duration_min": t.duration_min,
                "format": t.format,
                "sections": t.sections,
            }
            for t in cls.TUTORIALS
        ]

    @classmethod
    def export_scripts_json(cls, output_path: str = None) -> str:
        """Export all tutorial scripts as JSON."""
        scripts = cls.get_all_scripts()
        path = output_path or str(BRAND_DIR / "tutorial_scripts.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(scripts, f, ensure_ascii=False, indent=2)
        return path


# ============================================================================
# VIRAL ANNOUNCEMENT SCRIPTS
# ============================================================================


class ViralAnnouncements:
    """Viral announcement scripts for social media and YouTube."""

    ANNOUNCEMENTS = [
        {
            "id": "launch_epic",
            "platform": "YouTube (Short)",
            "format": "9:16",
            "duration_sec": 45,
            "title": "Esto va a cambiar COMO TRABAJAS para siempre",
            "hook": "Acabas de perder 3 horas hoy en tareas que una IA podria hacer en 30 segundos.",
            "script": [
                {
                    "time": "0-3s",
                    "visual": "Texto grande en pantalla",
                    "text": "PERDISTE 3 HORAS HOY",
                    "voice": "Acabas de perder 3 horas hoy.",
                },
                {
                    "time": "3-8s",
                    "visual": "Animacion de tareas repetitivas",
                    "text": "Tareas que una IA haria en 30 segundos",
                    "voice": "En tareas que una IA podria hacer en 30 segundos.",
                },
                {
                    "time": "8-15s",
                    "visual": "Logo AIGestion aparece con neón",
                    "text": "AIGestion",
                    "voice": "Pero existe AIGestion. Gestion inteligente con IA.",
                },
                {
                    "time": "15-25s",
                    "visual": "Dashboard en accion, agentes trabajando",
                    "text": "Agentes que trabajan por ti",
                    "voice": "Agentes que gestionan tu correo, agenda, documentos, y redes sociales. Automaticamente.",
                },
                {
                    "time": "25-35s",
                    "visual": "Numeros: horas ahorradas, dinero ahorrado",
                    "text": "30 hrs/semana ahorradas",
                    "voice": "30 horas a la semana. Para ti. Para lo que importa.",
                },
                {
                    "time": "35-40s",
                    "visual": "Logo + URL grande",
                    "text": "aigestion.net",
                    "voice": "aigestion.net. Gratis para empezar.",
                },
                {
                    "time": "40-45s",
                    "visual": "CTA suscribete",
                    "text": "SUSCRIBETE",
                    "voice": "Suscribete. Tu tiempo vale mas.",
                },
            ],
            "hashtags": [
                "#AIGestion",
                "#IA",
                "#Productividad",
                "#Automatizacion",
                "#FuturoDeTrabajo",
            ],
            "thumbnail_spec": {
                "background": "dark_neon",
                "main_text": "PERDISTE 3 HORAS",
                "sub_text": "IA lo hace en 30 seg",
                "logo": True,
                "colors": ["cyan", "magenta"],
            },
        },
        {
            "id": "daniela_intro",
            "platform": "YouTube (Short) + Instagram Reel",
            "format": "9:16",
            "duration_sec": 30,
            "title": "Conoce a DANIKA - la IA que gestiona empresas",
            "hook": "Ella no es humana. Pero gestiona mejor que cualquier ejecutivo que conozcas.",
            "script": [
                {
                    "time": "0-3s",
                    "visual": "Daniela aparece en pantalla",
                    "text": "NO ES HUMANA",
                    "voice": "Ella no es humana.",
                },
                {
                    "time": "3-8s",
                    "visual": "Daniela en oficina holografica",
                    "text": "Pero gestiona mejor que tu",
                    "voice": "Pero gestiona mejor que cualquier ejecutivo que conozcas.",
                },
                {
                    "time": "8-12s",
                    "visual": "Nombre aparece: DANIKA - Ciber-Ejecutiva",
                    "text": "DANIKA | Ciber-Ejecutiva",
                    "voice": "Se llama Daniela. Es la Ciber-Ejecutiva de AIGestion.",
                },
                {
                    "time": "12-20s",
                    "visual": "Demo de capacidades rapidas",
                    "text": "Correo | Agenda | Documentos | Redes",
                    "voice": "Gestiona correo, agenda, documentos, redes sociales. Sin parar. 24/7.",
                },
                {
                    "time": "20-25s",
                    "visual": "Comparativa: humano vs Daniela",
                    "text": "Humano: 8h | Daniela: 24/7",
                    "voice": "Tu trabajas 8 horas. Ella trabaja siempre.",
                },
                {
                    "time": "25-30s",
                    "visual": "Logo + URL",
                    "text": "aigestion.net | GRATIS",
                    "voice": "aigestion.net. Ella te espera.",
                },
            ],
            "hashtags": [
                "#DanielaAI",
                "#CiberEjecutiva",
                "#AIGestion",
                "#IA",
                "#GestionEmpresarial",
            ],
            "thumbnail_spec": {
                "background": "daniela_portrait",
                "main_text": "NO ES HUMANA",
                "sub_text": "Pero gestiona mejor",
                "logo": True,
                "colors": ["cyan", "magenta"],
            },
        },
        {
            "id": "comparison_viral",
            "platform": "YouTube (Long-form 5min)",
            "format": "16:9",
            "duration_sec": 300,
            "title": "Antes vs Despues de AIGestion (CHOCKING)",
            "hook": "Mira lo que pasaba ANTES de AIGestion y lo que pasa DESPUES. La diferencia es brutal.",
            "script": [
                {
                    "time": "0-10s",
                    "phase": "HOOK",
                    "visual": "Split screen: antes vs despues",
                    "text": "ANTES vs DESPUES",
                    "voice": "Mira esto. Antes de AIGestion. Y despues de AIGestion.",
                },
                {
                    "time": "10-60s",
                    "phase": "ANTES",
                    "visual": "Caos: 20 pestañas, correos sin leer, reloj",
                    "text": "ANTES: Caos total",
                    "voice": "Antes: 50 correos sin leer. Calendario saturado. 3 horas perdidas cada dia en tareas que no aportan nada.",
                },
                {
                    "time": "60-120s",
                    "phase": "DESPUES",
                    "visual": "Dashboard limpio, agentes trabajando, notificaciones utiles",
                    "text": "DESPUES: Control total",
                    "voice": "Despues: Dashboard unico. Agentes de IA gestionan todo. Correo clasificado y respondido. Calendario optimizado. Reportes automaticos.",
                },
                {
                    "time": "120-180s",
                    "phase": "NUMEROS",
                    "visual": "Graficos comparativos animados",
                    "text": "30 hrs/semana ahorradas | 2000 EUR/mes",
                    "voice": "Los numeros: 30 horas ahorradas a la semana. 2000 euros menos al mes. Tiempo de respuesta a clientes: de 4 horas a 15 minutos.",
                },
                {
                    "time": "180-240s",
                    "phase": "TESTIMONIO",
                    "visual": "Testimonio de usuario real",
                    "text": "'Mi mejor empleado'",
                    "voice": "Los usuarios dicen: 'Es el mejor empleado que he tenido. Y no cobra salario.'",
                },
                {
                    "time": "240-300s",
                    "phase": "CTA",
                    "visual": "Logo + URL + QR",
                    "text": "aigestion.net | GRATIS",
                    "voice": "Si quieres pasar del caos al control, ve a aigestion.net. Plan gratuito disponible. Suscribete para mas.",
                },
            ],
            "hashtags": ["#AIGestion", "#AntesVsDespues", "#Productividad", "#Automatizacion"],
            "thumbnail_spec": {
                "background": "split_screen",
                "main_text": "ANTES vs DESPUES",
                "sub_text": "La diferencia es BRUTAL",
                "logo": True,
                "colors": ["cyan", "magenta"],
            },
        },
        {
            "id": "free_tools_reveal",
            "platform": "YouTube (Short) + TikTok",
            "format": "9:16",
            "duration_sec": 40,
            "title": "AIGestion usa 67 herramientas GRATIS de Google (te muestro cuales)",
            "hook": "AIGestion usa 67 herramientas de Google gratis. Juntas valen 2800 euros al mes. Cuesta 0.",
            "script": [
                {
                    "time": "0-3s",
                    "visual": "Numero grande: 67",
                    "text": "67 HERRAMIENTAS GRATIS",
                    "voice": "67 herramientas de Google. Gratis.",
                },
                {
                    "time": "3-8s",
                    "visual": "Lista rapida de logos: Gemini, Drive, BigQuery, YouTube API",
                    "text": "Valor: 2800 EUR/mes",
                    "voice": "Juntas valen 2800 euros al mes. AIGestion las usa todas. Por 0.",
                },
                {
                    "time": "8-15s",
                    "visual": "Gemini CLI en accion",
                    "text": "Gemini CLI: IA gratis",
                    "voice": "Gemini CLI: acceso a Gemini 3 Pro gratis. Sin API key.",
                },
                {
                    "time": "15-22s",
                    "visual": "BigQuery + Firestore + Cloud Run",
                    "text": "GCP Free Tier: 31 servicios",
                    "voice": "Google Cloud Free Tier: 31 servicios always-free. Compute, BigQuery, Firestore, Cloud Run.",
                },
                {
                    "time": "22-30s",
                    "visual": "NotebookLM + Veo 2 + ImageFX",
                    "text": "Labs: NotebookLM + Veo 2 + ImageFX",
                    "voice": "Google Labs: NotebookLM para knowledge base. Veo 2 para videos. ImageFX para imagenes.",
                },
                {
                    "time": "30-35s",
                    "visual": "Logo AIGestion + mensaje",
                    "text": "AIGestion = todo esto integrado",
                    "voice": "AIGestion integra todo esto en una sola plataforma de gestion.",
                },
                {
                    "time": "35-40s",
                    "visual": "URL + CTA",
                    "text": "aigestion.net | GRATIS",
                    "voice": "aigestion.net. Gratis para empezar.",
                },
            ],
            "hashtags": ["#AIGestion", "#GoogleFreeTier", "#HerramientasGratis", "#IA", "#GCP"],
            "thumbnail_spec": {
                "background": "google_logos_grid",
                "main_text": "67 HERRAMIENTAS GRATIS",
                "sub_text": "Valor: 2800 EUR/mes | Costo: 0",
                "logo": True,
                "colors": ["cyan", "magenta"],
            },
        },
        {
            "id": "social_carousel_1",
            "platform": "Instagram + LinkedIn Carousel",
            "format": "1:1 (1080x1080)",
            "duration_sec": 0,  # Static carousel
            "title": "5 formas en que IA gestiona tu negocio (mientras duermes)",
            "slides": [
                {
                    "slide": 1,
                    "title": "5 formas en que la IA gestiona tu negocio",
                    "subtitle": "Mientras tu duermes",
                    "visual": "Logo AIGestion + numero 5 grande",
                },
                {
                    "slide": 2,
                    "title": "1. Correo automatico",
                    "subtitle": "Clasifica, responde y archiva 50+ correos/dia",
                    "visual": "Icono de correo con check verde neón",
                },
                {
                    "slide": 3,
                    "title": "2. Agenda inteligente",
                    "subtitle": "Optimiza reuniones y evita conflictos",
                    "visual": "Calendario con slots optimizados",
                },
                {
                    "slide": 4,
                    "title": "3. Reportes automaticos",
                    "subtitle": "Genera, guarda y publica en Drive",
                    "visual": "Grafico de barras subiendo",
                },
                {
                    "slide": 5,
                    "title": "4. Redes sociales",
                    "subtitle": "Crea y publica contenido diario",
                    "visual": "Iconos de redes sociales",
                },
                {
                    "slide": 6,
                    "title": "5. Monitoreo 24/7",
                    "subtitle": "Alertas en tiempo real, sin que tu hagas nada",
                    "visual": "Dashboard con alertas",
                },
                {
                    "slide": 7,
                    "title": "Todo esto por 0 euros",
                    "subtitle": "aigestion.net | Plan gratuito",
                    "visual": "Logo + URL + CTA",
                },
            ],
            "hashtags": [
                "#AIGestion",
                "#IA",
                "#Automatizacion",
                "#Productividad",
                "#GestionEmpresarial",
            ],
        },
        {
            "id": "twitter_thread",
            "platform": "Twitter/X Thread",
            "format": "text",
            "duration_sec": 0,
            "title": "Hilo: Como AIGestion automatiza empresas con 67 herramientas gratis de Google",
            "tweets": [
                "1/ AIGestion usa 67 herramientas gratuitas de Google para gestionar empresas enteras.\n\nEl valor total: 2,847 EUR/mes.\nEl costo: 0.\n\nTe cuento cuales y como: 🧵",
                "2/ 🧠 Gemini CLI\nIA gratis. Gemini 3 Pro. 60 RPM. 1,000 peticiones/dia.\n\nAIGestion lo usa como motor de IA principal. Sin API key. Sin costo.\n\nEsto solo ya vale 20 EUR/mes (vs ChatGPT+).",
                "3/ 📊 BigQuery\n1 TB de consultas gratis al mes.\n\nAIGestion guarda todos los logs de actividad de agentes aqui. Analytics empresarial sin pagar.",
                "4/ ☁️ Google Cloud Free Tier\n31 servicios always-free:\n- Compute e2-micro\n- Cloud Run (2M req)\n- Cloud Functions (2M invoc)\n- Firestore (50K lecturas)\n- Storage (5GB)\n- Pub/Sub (10GB)\n\nInfraestructura completa gratis.",
                "5/ 🎥 Google Labs\n- NotebookLM: knowledge base ilimitado\n- Veo 2: 30 videos/mes\n- ImageFX: imagenes con IA\n- Jules: 15 PRs automaticos/dia\n- Stitch: 450 UIs generadas/mes\n\nAIGestion usa todo para crear contenido.",
                "6/ 📺 YouTube Data API\n10,000 unidades/dia gratis.\n\nAIGestion rastrea tendencias, analiza canales, y programa contenido basado en datos reales.",
                "7/ 🌐 Firebase Spark Plan\n50K usuarios activos. 1GB Firestore. 10GB Hosting. FCM ilimitado.\n\nNotificaciones push gratis para toda la app de AIGestion.",
                "8/ El resultado:\n\n❌ Sin AIGestion: 2,847 EUR/mes en herramientas\n✅ Con AIGestion: 0 EUR/mes\n\nY lo mejor: todo integrado en un dashboard.\n\nPruebalo gratis: aigestion.net",
                "9/ ¿Quieres saber como configurar cada uno de estos?\n\nSigue a @AIGestion para el siguiente hilo donde explico la configuracion paso a paso.\n\nRT si te fue util 🔄",
            ],
            "hashtags": ["#AIGestion", "#GoogleFreeTier", "#IA", "#Hilo"],
        },
    ]

    @classmethod
    def get_announcement(cls, ann_id: str) -> dict | None:
        """Get a specific announcement by ID."""
        for ann in cls.ANNOUNCEMENTS:
            if ann["id"] == ann_id:
                return ann
        return None

    @classmethod
    def export_all_json(cls, output_path: str = None) -> str:
        """Export all announcements as JSON."""
        path = output_path or str(BRAND_DIR / "viral_announcements.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(cls.ANNOUNCEMENTS, f, ensure_ascii=False, indent=2)
        return path

    @classmethod
    def get_platform_summary(cls) -> dict[str, int]:
        """Get count of announcements per platform."""
        summary = {}
        for ann in cls.ANNOUNCEMENTS:
            platform = ann.get("platform", "unknown")
            summary[platform] = summary.get(platform, 0) + 1
        return summary


# ============================================================================
# BRAND KIT UTILITIES
# ============================================================================


class BrandKitUtils:
    """Utility functions for brand kit operations."""

    @staticmethod
    def get_brand_summary() -> dict:
        """Get complete brand summary as dictionary."""
        return {
            "brand_name": "AIGestion",
            "tagline": "Gestion Inteligente con Inteligencia Artificial",
            "url": "aigestion.net",
            "colors": {
                "primary_cyan": Colors.CYAN,
                "primary_cyan_dark": Colors.CYAN_DARK,
                "secondary_magenta": Colors.MAGENTA,
                "secondary_magenta_light": Colors.MAGENTA_LIGHT,
                "background_dark": Colors.DARK,
                "background_dark_blue": Colors.DARK_BLUE,
                "panel": Colors.PANEL,
            },
            "typography": {
                "heading": Typography.HEADING,
                "body": Typography.BODY,
                "mono": Typography.MONO,
            },
            "mascot": {
                "name": DanielaPersona.NAME,
                "role": DanielaPersona.ROLE,
                "description": DanielaPersona.DESCRIPTION,
                "visual_traits": DanielaPersona.VISUAL_TRAITS,
                "personality": DanielaPersona.PERSONALITY,
                "image_prompt": DanielaPersona.IMAGE_PROMPT,
            },
            "voice": {
                "pillars": BrandVoice.PILLARS,
                "do": BrandVoice.DO,
                "dont": BrandVoice.DONT,
                "hashtags": BrandVoice.HASHTAGS,
            },
            "assets": {
                "logo_main": str(BrandAssets.LOGO_MAIN),
                "logo_icon": str(BrandAssets.LOGO_ICON),
                "logo_horizontal": str(BrandAssets.LOGO_HORIZONTAL),
                "intro_template": str(BrandAssets.INTRO_TEMPLATE),
                "outro_template": str(BrandAssets.OUTRO_TEMPLATE),
                "thumb_youtube": str(BrandAssets.THUMB_YOUTUBE),
                "thumb_shorts": str(BrandAssets.THUMB_SHORTS),
                "daniela_images": [str(p) for p in BrandAssets.DANIELA_IMAGES if p.exists()],
            },
            "templates": {
                "intro_vertical": VideoTemplates.INTRO_VERTICAL.__dict__,
                "outro_vertical": VideoTemplates.OUTRO_VERTICAL.__dict__,
                "commercial_4block": VideoTemplates.COMMERCIAL_4BLOCK.__dict__,
            },
            "tutorials": TutorialTemplates.get_all_scripts(),
            "announcements": ViralAnnouncements.ANNOUNCEMENTS,
        }

    @staticmethod
    def export_brand_kit_json(output_path: str = None) -> str:
        """Export complete brand kit as JSON."""
        path = output_path or str(BRAND_DIR / "brand_kit.json")
        summary = BrandKitUtils.get_brand_summary()
        # Fix dataclass serialization
        for key in summary.get("templates", {}):
            tpl = summary["templates"][key]
            if hasattr(tpl, "__dict__"):
                summary["templates"][key] = dict(tpl.__dict__.items())
        with open(path, "w", encoding="utf-8") as f:
            json.dump(summary, f, ensure_ascii=False, indent=2, default=str)
        return path

    @staticmethod
    def check_assets_exist() -> dict:
        """Check which brand assets exist on disk."""
        assets = {
            "logo_main": BrandAssets.LOGO_MAIN.exists(),
            "logo_icon": BrandAssets.LOGO_ICON.exists(),
            "logo_horizontal": BrandAssets.LOGO_HORIZONTAL.exists(),
            "intro_template": BrandAssets.INTRO_TEMPLATE.exists(),
            "outro_template": BrandAssets.OUTRO_TEMPLATE.exists(),
            "thumb_youtube": BrandAssets.THUMB_YOUTUBE.exists(),
            "thumb_shorts": BrandAssets.THUMB_SHORTS.exists(),
        }
        assets["daniela_images"] = {p.name: p.exists() for p in BrandAssets.DANIELA_IMAGES}
        return assets

    @staticmethod
    def get_ffmpeg_intro_cmd(output: str) -> str:
        """Get the ffmpeg command to render the intro."""
        return VideoTemplates.get_intro_ffmpeg_command(output)

    @staticmethod
    def get_ffmpeg_outro_cmd(output: str) -> str:
        """Get the ffmpeg command to render the outro."""
        return VideoTemplates.get_outro_ffmpeg_command(output)

    @staticmethod
    def print_status():
        """Print brand kit status to console."""
        print("=" * 60)
        print("  AIGestion Brand Kit - Status Report")
        print("=" * 60)
        print()

        # Assets
        print("ASSETS:")
        assets = BrandKitUtils.check_assets_exist()
        for name, exists in assets.items():
            if isinstance(exists, dict):
                for img_name, img_exists in exists.items():
                    status = "OK" if img_exists else "MISSING"
                    print(f"  daniela/{img_name}: {status}")
            else:
                status = "OK" if exists else "MISSING"
                print(f"  {name}: {status}")

        print()
        print("COLORS:")
        print(f"  Primary:   {Colors.CYAN} (Neon Cyan)")
        print(f"  Secondary: {Colors.MAGENTA} (Hot Magenta)")
        print(f"  Dark:      {Colors.DARK} (Deep Space)")

        print()
        print("MASCOT:")
        print(f"  Name: {DanielaPersona.NAME}")
        print(f"  Role: {DanielaPersona.ROLE}")

        print()
        print("TEMPLATES:")
        print(f"  Intro:   {VideoTemplates.INTRO_VERTICAL.duration_sec}s (9:16)")
        print(f"  Outro:   {VideoTemplates.OUTRO_VERTICAL.duration_sec}s (9:16)")
        print(f"  Commercial: {VideoTemplates.COMMERCIAL_4BLOCK.duration_sec}s (4 blocks x 16s)")

        print()
        print("TUTORIALS:")
        for t in TutorialTemplates.TUTORIALS:
            print(f"  - {t.title} ({t.duration_min} min)")

        print()
        print("VIRAL ANNOUNCEMENTS:")
        for a in ViralAnnouncements.ANNOUNCEMENTS:
            dur = f"{a.get('duration_sec', 0)}s" if a.get("duration_sec") else "static"
            print(f"  - [{a['platform']}] {a['title']} ({dur})")

        print()
        print("FFMPEG READY:")
        print(f"  Intro cmd: {VideoTemplates.get_intro_ffmpeg_command('intro.mp4')[:80]}...")
        print(f"  Outro cmd: {VideoTemplates.get_outro_ffmpeg_command('outro.mp4')[:80]}...")

        print()
        print("=" * 60)


# ============================================================================
# CLI
# ============================================================================

if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        BrandKitUtils.print_status()
        print()
        print("Commands:")
        print("  status       - Print brand kit status")
        print("  summary      - Export brand summary JSON")
        print("  tutorials    - Export tutorial scripts JSON")
        print("  announcements - Export viral announcements JSON")
        print("  intro-cmd    - Print ffmpeg intro command")
        print("  outro-cmd    - Print ffmpeg outro command")
        sys.exit(0)

    cmd = sys.argv[1].lower()

    if cmd == "status":
        BrandKitUtils.print_status()
    elif cmd == "summary":
        path = BrandKitUtils.export_brand_kit_json()
        print(f"Brand kit exported to: {path}")
    elif cmd == "tutorials":
        path = TutorialTemplates.export_scripts_json()
        print(f"Tutorial scripts exported to: {path}")
    elif cmd == "announcements":
        path = ViralAnnouncements.export_all_json()
        print(f"Viral announcements exported to: {path}")
    elif cmd == "intro-cmd":
        out = sys.argv[2] if len(sys.argv) > 2 else "intro.mp4"
        print(VideoTemplates.get_intro_ffmpeg_command(out))
    elif cmd == "outro-cmd":
        out = sys.argv[2] if len(sys.argv) > 2 else "outro.mp4"
        print(VideoTemplates.get_outro_ffmpeg_command(out))
    else:
        print(f"Unknown command: {cmd}")
        print("Available: status, summary, tutorials, announcements, intro-cmd, outro-cmd")
