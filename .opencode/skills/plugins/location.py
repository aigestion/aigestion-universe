import subprocess
import json
import os
import math

BASE_DIR = os.path.expanduser("~/daniela-os")
VAULT_FILE = os.path.join(BASE_DIR, "memory_vault.json")
CONFIG_FILE = os.path.join(BASE_DIR, "geofence_config.json")

DEFAULT_CONFIG = {
    "home_lat": 28.03093,
    "home_lon": -16.5945715,
    "radius_meters": 300.0
}

def load_geofence_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r') as f:
                return json.load(f)
        except Exception:
            pass
    return DEFAULT_CONFIG

def calculate_distance(lat1, lon1, lat2, lon2):
    R = 6371000.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    delta_phi, delta_lambda = math.radians(lat2 - lat1), math.radians(lon2 - lon1)

    a = math.sin(delta_phi / 2.0)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0)**2
    return R * (2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a)))

def get_last_vault_location():
    if os.path.exists(VAULT_FILE):
        try:
            with open(VAULT_FILE, 'r') as f:
                vault = json.load(f)
                for entry in reversed(vault):
                    if entry.get("type") in ["geofence_check", "location_fix"] and "data" in entry:
                        return entry["data"]
        except Exception:
            pass
    return None

def run(context):
    context.lower()
    config = load_geofence_config()
    
    output_data = None
    prov_used = "network"

    # Secuencia de peticiones ultrarrápidas (2s de timeout máximo)
    commands = [
        ['termux-location', '-p', 'network', '-r', 'last'],
        ['termux-location', '-p', 'gps', '-r', 'last'],
        ['termux-location', '-p', 'network', '-r', 'once']
    ]

    for c in commands:
        try:
            res = subprocess.run(c, capture_output=True, text=True, timeout=2)
            if res.stdout.strip():
                output_data = json.loads(res.stdout.strip())
                prov_used = c[2] + "_" + c[4]
                break
        except Exception:
            continue

    if output_data and "latitude" in output_data:
        lat = float(output_data["latitude"])
        lon = float(output_data["longitude"])
        acc = output_data.get("accuracy", "N/A")
        source_type = f"EN VIVO ({prov_used.upper()})"
    else:
        # Fallback de emergencia a la bóveda si Android bloquea el comando
        vault_loc = get_last_vault_location()
        if vault_loc:
            lat = float(vault_loc.get("latitude", config["home_lat"]))
            lon = float(vault_loc.get("longitude", config["home_lon"]))
            acc = vault_loc.get("accuracy", "13.63")
            source_type = "BÓVEDA DE MEMORIA (ÚLTIMO REGISTRO)"
        else:
            return "📍 [GEOFENCE]: Conexión con Android suspendida. Concede permisos de 'Ubicación' a Termux:API."

    dist = calculate_distance(lat, lon, config["home_lat"], config["home_lon"])
    is_inside = dist <= config["radius_meters"]
    zone_status = "BASE_OPERATIVA" if is_inside else "ZONA_EXTERNA_GREEN_ISLAND"

    return (
        f"🌐 *[GEOFENCING - RESILIENCIA DE UBICACIÓN]*\n\n"
        f"📡 *Origen del dato:* `{source_type}`\n"
        f"📍 *Coordenadas:* `{lat}, {lon}` (Precisión: `{acc} m`)\n"
        f"📏 *Distancia a Base:* `{round(dist, 2)} m` | *Estado:* `{zone_status}`\n"
        f"🔗 *Google Maps:* https://www.google.com/maps?q={lat},{lon}"
    )
