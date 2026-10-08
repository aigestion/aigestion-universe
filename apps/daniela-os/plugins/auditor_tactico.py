import os
import json

RESEARCH_DIR = os.path.expanduser("~/daniela-os/research")
file_tareas = os.path.join(RESEARCH_DIR, "tareas_pendientes.json")

def registrar_tarea_tactica(titulo, prioridad="ALTA", canal="Google Docs"):
    tarea = {
        "titulo": titulo,
        "prioridad": prioridad,
        "canal": canal,
        "estado": "Pendiente de aprobación (Human-in-the-Loop)"
    }
    
    tareas = []
    if os.path.exists(file_tareas):
        with open(file_tareas, "r", encoding="utf-8") as f:
            try:
                tareas = json.load(f)
            except Exception:
                tareas = []
                
    tareas.append(tarea)
    with open(file_tareas, "w", encoding="utf-8") as f:
        json.dump(tareas, f, indent=2, ensure_ascii=False)
        
    print(f"🎯 [AUDITOR TÁCTICO]: Tarea registrada exitosamente: {titulo}")

if __name__ == "__main__":
    registrar_tarea_tactica("Revisión de integración Google Vids y Gema Prime")
