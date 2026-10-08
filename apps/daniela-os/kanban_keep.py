import json
import os

RESEARCH_DIR = os.path.expanduser("~/daniela-os/research")
file_kanban = os.path.join(RESEARCH_DIR, "kanban_keep_local.json")

kanban_data = {
    "tablero": "Daniela OS - Kanban Táctico AIGestion",
    "estado_sincronizacion": "Google Keep Sync Activo",
    "tareas": [
        {
            "prioridad": "ALTA",
            "descripcion": "Revisión de integración Google Vids y Gema Prime",
            "completada": False,
        },
        {
            "prioridad": "MEDIA",
            "descripcion": "Configuración de AI Studio Live API Vocal en Pixel",
            "completada": False,
        },
        {
            "prioridad": "MEDIA",
            "descripcion": "Renderizado de Assets Visuales con Imagen 3 API",
            "completada": False,
        },
    ],
}

with open(file_kanban, "w", encoding="utf-8") as f:
    json.dump(kanban_data, f, indent=2, ensure_ascii=False)

print(
    "✨ [KANBAN INTEGRADO]: Espejo local actualizado en ~/daniela-os/research/kanban_keep_local.json"
)
