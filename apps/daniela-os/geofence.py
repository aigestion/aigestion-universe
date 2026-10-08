import json
import math
import os
import subprocess

CONFIG_PATH = os.path.expanduser("~/daniela-os/geo_config.json")

# Coordenadas por defecto (Cámbialas por las tuyas si no usas el archivo json)
CASA_LAT = 40.416775  # Cambiar por tu latitud real
CASA_LON = -3.703790  # Cambiar por tu longitud real
RADIO_CASA_METROS = 100.0


def guardar_base_operativa():
    """Captura la posición GPS actual y la guarda como Casa."""
    print("🛰️ Obteniendo posición GPS actual para fijar Base Operativa...")
    try:
        raw = subprocess.check_output(
            ["termux-location", "-p", "network", "-r", "once"], stderr=subprocess.DEVNULL
        ).decode("utf-8")
        data = json.loads(raw)
        lat = data.get("latitude")
        lon = data.get("longitude")
        if lat and lon:
            config = {"casa_lat": lat, "casa_lon": lon, "radio_m": RADIO_CASA_METROS}
            with open(CONFIG_PATH, "w") as f:
                json.dump(config, f, indent=2)
            print(f"✅ Base Operativa guardada: Lat {lat:.6f}, Lon {lon:.6f}")
            return True
    except Exception as e:
        print(f"❌ Error al capturar GPS: {e}")
    return False


def haversine(lat1, lon1, lat2, lon2):
    """Calcula la distancia en metros entre dos puntos geográficos."""
    R = 6371000.0  # Radio de la Tierra en metros
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)

    a = math.sin(dphi / 2.0) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2.0) ** 2
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return R * c


def obtener_estado_ubicacion():
    """Devuelve 'CASA' o 'CALLE' según la posición del teléfono."""
    if not os.path.exists(CONFIG_PATH):
        return "CASA", 0.0

    with open(CONFIG_PATH) as f:
        config = json.load(f)

    casa_lat = config.get("casa_lat", CASA_LAT)
    casa_lon = config.get("casa_lon", CASA_LON)
    radio = config.get("radio_m", RADIO_CASA_METROS)

    try:
        raw = subprocess.check_output(
            ["termux-location", "-p", "network", "-r", "last"], stderr=subprocess.DEVNULL
        ).decode("utf-8")
        data = json.loads(raw)
        cur_lat = data.get("latitude")
        cur_lon = data.get("longitude")
        if cur_lat and cur_lon:
            distancia = haversine(casa_lat, casa_lon, cur_lat, cur_lon)
            if distancia <= radio:
                return "CASA", distancia
            else:
                return "CALLE", distancia
    except Exception:
        pass

    return "CASA", 0.0


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "--set-base":
        guardar_base_operativa()
    else:
        estado, dist = obtener_estado_ubicacion()
        print(f"📍 Estado actual: {estado} (Distancia a la base: {dist:.1f} metros)")
