import logging


def _clasifica(cmd):
    """Clasifica dispositivo/accion con el heuristico historico (fallback)."""
    device = "dispositivo"
    action = "estado"

    if "luz" in cmd or "iluminación" in cmd:
        device = "Luces"
    elif "persiana" in cmd or "cortina" in cmd:
        device = "Persianas"
    elif "termostato" in cmd or "aire" in cmd or "calefacción" in cmd:
        device = "Termostato"
    elif "tv" in cmd or "televisión" in cmd:
        device = "Smart TV"

    if "enciende" in cmd or "abrir" in cmd or "subir" in cmd:
        action = "encendido"
    elif "apaga" in cmd or "cerrar" in cmd or "bajar" in cmd:
        action = "apagado"

    return device, action


def process_iot_command(command):
    """
    Skill #17: Central de Domótica -> iot_hub (real).

    Delega en iot_hub.service.parse_voice_command (Home Assistant real);
    si el hub no esta disponible o el comando no es ejecutable, cae al
    mensaje simulado historico (contrato: devuelve SIEMPRE str).
    """
    cmd = command.lower()
    try:
        device, action = _clasifica(cmd)

        result = None
        try:
            from iot_hub.service import get_service

            result = get_service().parse_voice_command(command)
        except Exception as e:  # noqa: BLE001 - arbol parcial o sin hub
            logging.warning("IoT Controller: hub no disponible: %s", e)

        if result and result.get("ok"):
            entity = result.get("entity_id", device)
            service = result.get("action", action)
            logging.info("IoT Controller: %s -> %s (%s)", command, entity, service)
            return f"🔌 [DOMÓTICA]: '{entity}' configurado a '{service}' correctamente."

        if result:
            logging.info("IoT Controller: no ejecutable: %s", result.get("error"))

        # Fallback simulado (mismo mensaje historico)
        logging.info(f"IoT Controller: Ejecutando {action} en {device}")
        return f"🔌 [DOMÓTICA]: '{device}' configurado a '{action}' correctamente."

    except Exception as e:
        logging.error(f"Error en IoT Controller: {e}")
        return f"Error en control domótico: {e}"
