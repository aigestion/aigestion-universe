"""Blueprint /api/iot/* — superficie IoT de Daniela OS (fase `iot`).

Registrado en gev/daniela-os/server.py. Todas las rutas devuelven JSON y
degradan a ``ok: false`` con mensaje (sin 500 por backends caidos).
"""

from __future__ import annotations

from flask import Blueprint, jsonify, request
from iot_hub import discovery, service
from iot_hub.backends import esphome, mqtt

iot_bp = Blueprint("iot", __name__, url_prefix="/api/iot")


@iot_bp.get("/status")
def iot_status():
    svc = service.get_service()
    payload = svc.get_state()
    payload["backends"] = {
        "homeassistant": svc.ha_status(),
        "mqtt": mqtt.status(),
        "esphome": esphome.status(),
    }
    return jsonify(payload)


@iot_bp.get("/devices")
def iot_devices():
    domain = request.args.get("domain", "")
    return jsonify({"devices": service.get_service().get_devices(domain)})


@iot_bp.post("/sync")
def iot_sync():
    return jsonify(service.get_service().sync_devices())


@iot_bp.post("/control")
def iot_control():
    data = request.json or {}
    entity_id = data.get("entity_id", "")
    action = data.get("action", "")
    params = data.get("params", {})
    if not entity_id or not action:
        return jsonify({"ok": False, "error": "entity_id y action son obligatorios"}), 400
    return jsonify(service.get_service().control_device(entity_id, action, params))


@iot_bp.post("/scene")
def iot_scene():
    scene_id = (request.json or {}).get("scene_id", "")
    return jsonify(service.get_service().activate_scene(scene_id))


@iot_bp.post("/voice")
def iot_voice():
    text = (request.json or {}).get("text", "")
    return jsonify(service.get_service().parse_voice_command(text))


@iot_bp.get("/aliases")
def iot_aliases():
    return jsonify(service.get_service().get_device_map())


@iot_bp.post("/alias")
def iot_add_alias():
    data = request.json or {}
    return jsonify(
        service.get_service().add_alias(data.get("alias", ""), data.get("entity_id", ""))
    )


@iot_bp.post("/discovery")
def iot_discovery():
    data = request.json or {}
    try:
        inv = discovery.scan(subnet=data.get("subnet") or None)
    except ValueError as e:
        return jsonify({"ok": False, "error": str(e)}), 400
    return jsonify({"ok": True, "inventory": inv})


@iot_bp.get("/inventory")
def iot_inventory():
    return jsonify(discovery.load_inventory())


@iot_bp.post("/mqtt/publish")
def iot_mqtt_publish():
    data = request.json or {}
    topic = data.get("topic", "")
    if not topic:
        return jsonify({"ok": False, "error": "topic obligatorio"}), 400
    return jsonify(mqtt.publish(topic, data.get("payload", ""), qos=int(data.get("qos", 0))))
