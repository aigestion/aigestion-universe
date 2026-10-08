import json
import os

RULES_FILE = os.path.expanduser("~/daniela-os/event_rules.json")

def load_rules():
    if not os.path.exists(RULES_FILE):
        default_rules = [
            {"event": "battery_low", "condition": "level < 20", "action": "resource_optimizer", "msg": "Modo ahorro activado"},
            {"event": "net_change", "condition": "status == disconnected", "action": "local_llm", "msg": "Conmutando a inferencia offline"}
        ]
        with open(RULES_FILE, "w") as f:
            json.dump(default_rules, f, indent=2)
        return default_rules
    with open(RULES_FILE) as f:
        return json.load(f)

def trigger_event(event_type, payload=None):
    """
    Skill #32B: Event-Driven Automation Pipeline.
    Evalúa reglas en tiempo de ejecución ante un evento entrante.
    """
    rules = load_rules()
    triggered = []

    for rule in rules:
        if rule.get("event") == event_type:
            action = rule.get("action")
            msg = rule.get("msg", "Regla ejecutada")
            triggered.append(f"⚡ [EVENT TRIGGERED]: Evento '{event_type}' -> Ejecutando Skill '{action}' ({msg})")

    if triggered:
        return "\n".join(triggered)
    return f"ℹ️ [EVENT PIPELINE]: Evento '{event_type}' procesado. Ninguna regla requerida."

def list_rules():
    rules = load_rules()
    return f"📋 [EVENT PIPELINE]: {len(rules)} reglas activas registradas en event_rules.json."
