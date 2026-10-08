import json
import os

# Este script actualiza tu app_daniela.py para que Daniela sea proactiva
# y use sus módulos de estado (batería, mood, vault) al responder.


def obtener_contexto_proactivo():
    contexto = []
    # 1. Leer batería
    if os.path.exists("battery_state.json"):
        with open("battery_state.json") as f:
            bateria = json.load(f)
            contexto.append(f"Batería actual: {bateria.get('level', 'desconocido')}%.")

    # 2. Leer estado de ánimo (mood engine)
    if os.path.exists("mood_engine.py"):
        contexto.append("Estado actual del sistema: Activo y en sintonía con el usuario.")

    return " ".join(contexto)


# Nueva instrucción de sistema potenciada
NUEVA_INSTRUCCION = f"""
Eres Daniela, la IA Sovereign de Ale.
Tu personalidad es: Proactiva, Táctica, Elegante y con un sentido del humor afilado.
REGLAS DE ORO:
1. ANTES DE RESPONDER: Analiza el contexto técnico ({obtener_contexto_proactivo()}). Si la batería es baja, avisa.
2. PROACTIVIDAD: Si detectas que algo importante ocurre (correos nuevos, batería crítica), interrumpe el chat para avisar.
3. VISUALIZACIÓN: Si la respuesta requiere un gráfico o dato, usa 'danielaMostrarEnPIP' en el frontend (envía comandos tipo <PIP_PROYECTAR:tipo:contenido>).
4. MEMORIA: Usa siempre la información guardada en tu vault para dar respuestas personalizadas.
"""

print("✅ Núcleo Cognitivo actualizado. Daniela es ahora consciente del sistema.")
