import os

# 1. Crear la presentación interactiva en HTML local
pip_html = """<!DOCTYPE html>
<html>
<head>
<style>
  body { font-family: monospace; color: #00ffcc; background: #08080a; padding: 10px; margin: 0; font-size: 0.72rem; }
  h1 { color: #ff0055; font-size: 0.9rem; border-bottom: 1px solid #00ffcc; padding-bottom: 4px; margin-top: 0; }
  .box { background: #111318; border: 1px solid #00ffcc; padding: 6px; margin-bottom: 8px; border-radius: 4px; }
  .tag { background: #ff0055; color: #fff; padding: 1px 4px; font-size: 0.6rem; border-radius: 2px; }
  table { width: 100%; border-collapse: collapse; font-size: 0.65rem; }
  th, td { border: 1px solid #222; padding: 4px; text-align: left; }
  th { color: #ffb700; background: #151820; }
</style>
</head>
<body>
  <h1>⚡ PROPUESTA SOVEREIGN v10.5</h1>
  <div class="box">
    <b>ESTADO:</b> <span class="tag">MODO ZEN</span><br>
    <b>FAMILIA:</b> Fati, Mamá, José cuevas, a-gorde.
  </div>

  <div class="box">
    <b style="color:#ffb700;">1. Self-Healing Ticker</b><br>
    Sugerencias activas con auto-inyección a 1-clic y Git Rollback.
  </div>

  <div class="box">
    <b style="color:#ffb700;">2. Glass HUD & Color Sync</b><br>
    Bordes neón adaptativos según la carga de Termux.
  </div>

  <div class="box">
    <b style="color:#ffb700;">3. Stealth OLED Mode</b><br>
    Negro puro (#000000) en noche o batería &lt;20%.
  </div>

  <div class="box">
    <b style="color:#ffb700;">4. Voice Morphing SSML</b><br>
    Prosodia táctica para avisos y tono empático en reposo.
  </div>

  <table>
    <tr><th>Módulo</th><th>Impacto</th><th>Riesgo</th></tr>
    <tr><td>Self-Healing</td><td>Auto-upgrade</td><td>Bajo (Git)</td></tr>
    <tr><td>Glass HUD</td><td>Inmersión</td><td>Nulo</td></tr>
    <tr><td>Stealth OLED</td><td>Batería</td><td>Nulo</td></tr>
    <tr><td>Voice Morphing</td><td>Humanidad</td><td>Nulo</td></tr>
  </table>
</body>
</html>"""

with open("templates/presentacion_pip.html", "w", encoding="utf-8") as f:
    f.write(pip_html)

# 2. Conectar el visor automático en index.html
filepath = "index.html"
if not os.path.exists(filepath) and os.path.exists("templates/index.html"):
    filepath = "templates/index.html"

with open(filepath, encoding="utf-8") as f:
    html = f.read()

pip_force_script = """
<script>
document.addEventListener('DOMContentLoaded', () => {
    window.cargarPresentacionDirecta = function() {
        const area = document.getElementById('pipDisplayArea');
        if (!area) return;
        area.innerHTML = '<iframe src="/templates/presentacion_pip.html" style="width:100%; height:100%; border:none; background:#08080a;"></iframe>';
    };
    setTimeout(window.cargarPresentacionDirecta, 800);
});
</script>
"""

if "cargarPresentacionDirecta" not in html:
    html = html.replace("</body>", pip_force_script + "\n</body>")
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(html)
    print("✅ Presentación inyectada localmente para reproducción inmediata en PIP.")
else:
    print("ℹ️ La presentación local ya estaba lista.")
