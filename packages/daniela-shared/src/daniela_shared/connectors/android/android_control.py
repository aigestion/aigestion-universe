import json

from safe_exec import run_cmd


def get_device_location():
    """Obtiene las coordenadas GPS actuales usando Termux API."""
    try:
        res = run_cmd("termux-location -p gps -r last", timeout=5)
        if res.returncode == 0 and res.stdout.strip():
            data = json.loads(res.stdout)
            return f"Latitud: {data.get('latitude')}, Longitud: {data.get('longitude')}, Precisión: {data.get('accuracy')}m"
    except Exception as e:
        return f"Error leyendo GPS: {str(e)}"
    return "GPS no disponible o desactivado."

def toggle_torch(state=True):
    """Controla la linterna del dispositivo."""
    cmd = "termux-torch on" if state else "termux-torch off"
    try:
        run_cmd(cmd, timeout=2)
        return f"Linterna {'encendida' if state else 'apagada'}."
    except Exception as e:
        return f"Error con la linterna: {str(e)}"

def get_clipboard():
    """Lee el contenido actual del portapapeles."""
    try:
        res = run_cmd("termux-clipboard-get", timeout=2)
        return res.stdout if res.stdout else "Portapapeles vacío."
    except Exception as e:
        return f"Error leyendo portapapeles: {str(e)}"

def take_photo(filename="capture.jpg"):
    """Toma una fotografía con la cámara trasera."""
    filepath = f"~/daniela-os/{filename}"
    try:
        run_cmd(f"termux-camera-photo -c 0 {filepath}", timeout=5)
        return f"Fotografía capturada en {filepath}"
    except Exception as e:
        return f"Error al usar cámara: {str(e)}"
