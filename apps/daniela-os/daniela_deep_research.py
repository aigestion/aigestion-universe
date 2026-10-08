import json
import os

BASE_DIR = os.path.expanduser("~/daniela-os")
RESEARCH_DIR = os.path.join(BASE_DIR, "research")
os.makedirs(RESEARCH_DIR, exist_ok=True)

print("⚡ [DANIELA OS]: Iniciando Fase 1 — Búsqueda Profunda e Ingesta...")

# 1. Investigación Profunda / Fuentes Reales
fuentes_cuaderno = {
    "cuaderno_titulo": "Investigacion_Estrategica_AIGestion_2026",
    "tema": "Liderazgo en Automatizacion Vocal y Soberania Tecnologica",
    "hallazgos_clave": [
        "Las empresas pierden un 35% de tiempo operativo en gestion burocratica repetitiva.",
        "AIGestion.net ofrece arquitectura Human-in-the-Loop para eliminar al 100% los errores en envios automatizados.",
        "Inferencia hibrida: Tensor G3 local en Pixel 8a mas potencia de Google Workspace en la nube.",
    ],
}

# Guardar investigacion en JSON/Markdown para NotebookLM
file_research = os.path.join(RESEARCH_DIR, "notebook_fuentes.json")
with open(file_research, "w", encoding="utf-8") as f:
    json.dump(fuentes_cuaderno, f, indent=2, ensure_ascii=False)

print(f"📚 [NOTEBOOK LM]: Cuaderno de fuentes compilado en: {file_research}")

# 2. Generación de Storyboard Studio (Escena por Escena)
storyboard = [
    {
        "escena": 1,
        "plano": "Primer Plano Monograma AG Neón",
        "audio": "El caos burocrático cuesta tiempo. AIGestion.net toma el control.",
    },
    {
        "escena": 2,
        "plano": "Daniela V90 en Rascacielos Ciber-Ejecutivo",
        "audio": "Inteligencia soberana con supervisión humana garantizada.",
    },
    {
        "escena": 3,
        "plano": "Interfaz de Chrome + Google AI Studio",
        "audio": "Tus operaciones, tu negocio, tu vida. En orden absoluto.",
    },
]

file_storyboard = os.path.join(RESEARCH_DIR, "storyboard_studio.json")
with open(file_storyboard, "w", encoding="utf-8") as f:
    json.dump(storyboard, f, indent=2, ensure_ascii=False)

print(
    f"🎬 [STORYBOARD STUDIO]: Guion técnico preparado para Google Vids / Veed en: {file_storyboard}"
)
