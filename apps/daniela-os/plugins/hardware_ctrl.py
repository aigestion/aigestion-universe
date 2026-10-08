import subprocess, json

def run(context):
    cmd = context.lower()
    
    # 1. Control de Linterna
    if "linterna on" in cmd or "enciende linterna" in cmd or "encender linterna" in cmd:
        subprocess.run(['termux-torch', 'on'])
        return "🔦 [HARDWARE]: Linterna encendida."
    elif "linterna off" in cmd or "apaga linterna" in cmd or "apagar linterna" in cmd:
        subprocess.run(['termux-torch', 'off'])
        return "🔦 [HARDWARE]: Linterna apagada."
        
    # 2. Control Háptico (Vibración)
    elif "vibra" in cmd or "vibrar" in cmd:
        subprocess.run(['termux-vibrate', '-d', '500'])
        return "📳 [HARDWARE]: Pulso háptico ejecutado (500ms)."
        
    # 3. Geo-Ubicación GPS
    elif "donde estoy" in cmd or "gps" in cmd or "ubicacion" in cmd:
        try:
            res = subprocess.run(['termux-location', '-p', 'gps', '-r', 'once'], capture_output=True, text=True, timeout=10)
            data = json.loads(res.stdout)
            lat = data.get("latitude")
            lon = data.get("longitude")
            alt = data.get("altitude")
            return f"📍 [GPS]: Latitud {lat}, Longitud {lon} (Altitud: {alt}m)."
        except Exception as e:
            return f"⚠️ [GPS]: No se pudo obtener la ubicación rápida: {str(e)}"
            
    # 4. Información de Batería Nivel Hardware
    elif "bateria" in cmd or "battery" in cmd:
        try:
            res = subprocess.run(['termux-battery-status'], capture_output=True, text=True, timeout=5)
            data = json.loads(res.stdout)
            perc = data.get("percentage")
            health = data.get("health")
            temp = data.get("temperature")
            return f"🔋 [HARDWARE]: Batería al {perc}% | Salud: {health} | Temp: {temp}°C."
        except Exception as e:
            return f"❌ [HARDWARE]: Error al consultar batería: {str(e)}"

    return "❌ [HARDWARE]: Comando no reconocido. Prueba con 'linterna on', 'linterna off', 'vibra', 'gps' o 'bateria'."
