import json


def filtrar_notificacion(remitente, tipo):
    with open("family_whitelist.json") as f:
        whitelist = json.load(f)

    # Si es familia o prioridad alta, Daniela avisa con voz y luz
    if remitente in whitelist["familia"] or remitente in whitelist["prioridad_alta"]:
        return "ACTIVA_ALERTA_VOZ"

    # Si no, solo pulso visual silencioso en PIP
    return "ACTIVA_PULSO_VISUAL_SILENCIOSO"


print("✅ Filtro Zen Sovereign instalado. Daniela ahora es tu portero personal.")
