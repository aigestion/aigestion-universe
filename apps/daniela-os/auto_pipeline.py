import os

from gtts import gTTS
from safe_exec import run_code

BASE_DIR = os.path.expanduser("~/daniela-os")

print("⚡ [AIGESTION AUTOMATION ENGINE] Iniciando pipeline maestro...")

# 1. GENERACIÓN DE AUDIO EN LOTE (Locuciones)
locuciones = {
    "short_daniela.mp3": "Facturas clasificadas en Google Drive, borradores redactados en Gmail e informe listo, Comandante.",
    "intro_brand.mp3": "Bienvenido a AIGestion.net. Tu negocio. Tu vida. En orden absoluto.",
    "tmp_voice.mp3": "Hola Comandante. Soy Daniela. Todos los sistemas de Google y el servidor táctico están sincronizados.",
}

for name, text in locuciones.items():
    path = os.path.join(BASE_DIR, name)
    tts = gTTS(text=text, lang="es", tld="es")
    tts.save(path)
    print(f"🎙️ [AUDIO]: {name} generado correctamente.")

# 2. VINCULACIÓN AUTOMÁTICA DE IMAGEN BASE
img_src = "/storage/emulated/0/DCIM/Restored/ChatGPT Image 22 abr 2026, 22_22_52.png"
img_dst = os.path.join(BASE_DIR, "environment_base.jpg")
if os.path.exists(img_src):
    run_code(f'cp "{img_src}" "{img_dst}"')
    print("📸 [IMAGEN]: Rostro oficial de Daniela vinculado.")

# 3. GENERACIÓN DE LANDING PAGE AUTOMÁTICA
html_content = """<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AIGestion.net — Inteligencia Soberana</title>
    <style>
        body { background-color: #080c14; color: #f8fafc; font-family: system-ui, sans-serif; margin:0; padding:20px; display:flex; justify-content:center; }
        .card { max-width:600px; width:100%; background:#0f172a; border:1px solid #1e293b; border-radius:16px; padding:30px; box-shadow: 0 0 30px rgba(0,210,255,0.15); text-align:center; }
        h1 { color:#00d2ff; font-size:2rem; margin-bottom:5px; }
        p.tagline { color:#94a3b8; font-size:1.1rem; margin-bottom:25px; }
        .badge { background:rgba(34,197,94,0.1); color:#22c55e; border:1px solid #22c55e; padding:6px 14px; border-radius:20px; font-weight:bold; font-size:0.85rem; display:inline-block; }
        .services { text-align:left; margin-top:30px; }
        .service-item { background:#1e293b; padding:12px 16px; border-radius:8px; margin-bottom:10px; border-left:4px solid #00d2ff; font-size:0.95rem; }
    </style>
</head>
<body>
    <div class="card">
        <h1>AIGestion.net</h1>
        <p class="tagline">Tu negocio. Tu vida. En orden absoluto.</p>
        <span class="badge">🟢 Daniela OS v4.09 — ONLINE</span>
        <div class="services">
            <div class="service-item">📬 Gmail Sentinel & Ghostwriter Executive</div>
            <div class="service-item">📁 Google Drive Vault & Ingesta Automática</div>
            <div class="service-item">📊 Reportes Ejecutivos en Google Docs</div>
        </div>
    </div>
</body>
</html>"""

with open(os.path.join(BASE_DIR, "index.html"), "w", encoding="utf-8") as f:
    f.write(html_content)
print("🌐 [WEB]: Dashboard index.html autogenerado.")

print("\n✨ [PIPELINE COMPLETADO]: Todos los activos locales han sido automatizados.")
