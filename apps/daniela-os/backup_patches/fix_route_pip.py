import os

filepath = "app_daniela.py"
if os.path.exists(filepath):
    with open(filepath, encoding="utf-8") as f:
        code = f.read()

    route_code = """
@app.route('/presentacion_pip')
def presentacion_pip():
    return '''<!DOCTYPE html>
<html>
<head>
<style>
  body { font-family: monospace; color: #00ffcc; background: #08080a; padding: 12px; margin: 0; font-size: 0.75rem; }
  h1 { color: #ff0055; font-size: 0.95rem; border-bottom: 1px solid #00ffcc; padding-bottom: 4px; margin-top: 0; }
  .box { background: #111318; border: 1px solid #00ffcc; padding: 8px; margin-bottom: 8px; border-radius: 4px; }
  .tag { background: #ff0055; color: #fff; padding: 1px 4px; font-size: 0.6rem; border-radius: 2px; }
  table { width: 100%; border-collapse: collapse; font-size: 0.68rem; margin-top: 6px; }
  th, td { border: 1px solid #222; padding: 5px; text-align: left; }
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
</html>'''
"""

    if "/presentacion_pip" not in code:
        with open(filepath, "a", encoding="utf-8") as f:
            f.write("\n" + route_code)
        print("✅ Ruta /presentacion_pip registrada en Flask.")

# Actualizar el frontend para apuntar a la ruta limpia
index_path = "index.html"
if os.path.exists(index_path):
    with open(index_path, encoding="utf-8") as f:
        html = f.read()

    html = html.replace("/templates/presentacion_pip.html", "/presentacion_pip")
    with open(index_path, "w", encoding="utf-8") as f:
        f.write(html)
    print("✅ Frontend actualizado a la ruta oficial.")
