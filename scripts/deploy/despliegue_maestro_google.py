import os
import subprocess

BASE_DIR = os.path.expanduser("~/daniela-os")
MEDIA_DIR = os.path.join(BASE_DIR, "media")
RESEARCH_DIR = os.path.join(BASE_DIR, "research")
CONFIG_DIR = os.path.join(BASE_DIR, "config")

for folder in [MEDIA_DIR, RESEARCH_DIR, CONFIG_DIR]:
    os.makedirs(folder, exist_ok=True)

print("⚡ [DANIELA OS]: Desplegando Optimización Total del Entorno Google...")

# 1. Crear System Prompt para AI Studio (Gema Maestra)
system_prompt = """[SYSTEM PROMPT — DANIELA PRIME MASTER GEM]
Eres Daniela Prime, la Inteligencia Artificial Ejecutiva de aigestion.net.
Misión: Optimización de flujos burocráticos, gobernanza de datos y producción táctica.

REGLAS DE OPERACIÓN:
1. Arquitectura Human-in-the-Loop: Ningún envío o gasto se ejecuta sin la aprobación explícita del Comandante.
2. Respuesta Estructurada: Salidas en JSON o Storyboard técnico (Planos, Audio, Tiempos).
3. Eficiencia Energética y Costes: Respetar techo de gasto local.
4. Lema: "aigestion.net. Tu negocio. Tu vida. En orden absoluto."
"""
with open(os.path.join(CONFIG_DIR, "ai_studio_system_prompt.txt"), "w", encoding="utf-8") as f:
    f.write(system_prompt)

# 2. Guardar Bookmarklet para Chrome Auto-Ingest
bookmarklet_code = """javascript:(function(){let text=window.getSelection().toString()||document.title;fetch('http://localhost:8080/ingest',{method:'POST',body:JSON.stringify({url:window.location.href,content:text})});alert('📌 Capturado para Daniela OS');})();"""
with open(os.path.join(CONFIG_DIR, "chrome_bookmarklet.js"), "w", encoding="utf-8") as f:
    f.write(bookmarklet_code)

# 3. Mantenimiento de la Bóveda de Medios
print("🧹 Liberando espacio y manteniendo archivos críticos...")
archivos_permitidos = ["storyboard_android.mp4", "index.html", "spot_master_premium.mp3"]
for item in os.listdir(MEDIA_DIR):
    if item not in archivos_permitidos:
        try:
            os.remove(os.path.join(MEDIA_DIR, item))
        except Exception:
            pass

# 4. Activar Servidor Web Táctico en Segundo Plano
print("🌐 Reiniciando servidor web persistente en puerto 8080...")
subprocess.run(["pkill", "-f", "http.server"], check=False)
subprocess.Popen(["python3", "-m", "http.server", "8080", "--directory", MEDIA_DIR], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

print("\n✨ [DESPLIEGUE COMPLETO]: Todo el entorno Google está configurado y optimizado.")
