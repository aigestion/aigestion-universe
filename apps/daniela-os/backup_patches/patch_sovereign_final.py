import os

# 1. ACTUALIZACIÓN DEL BACKEND PARA PROACTIVIDAD TEMPORAL
filepath = "app_daniela.py"
if os.path.exists(filepath):
    with open(filepath, encoding="utf-8") as f:
        code = f.read()

    contexto_temporal = """
# --- CONTEXTO TEMPORAL SOVEREIGN ---
import datetime
def get_tiempo_sovereign():
    now = datetime.datetime.now()
    return f"Hoy es {now.strftime('%A, %d de %B de %Y')}, hora {now.strftime('%H:%M')}. Ubicación: España."
# -----------------------------------
"""
    if "CONTEXTO TEMPORAL SOVEREIGN" not in code:
        code = code.replace("import os", "import os\n" + contexto_temporal)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(code)

# 2. ACTUALIZACIÓN DEL FRONTEND PARA COLOR-SYNC Y ATMÓSFERA
html_path = "index.html"
with open(html_path, encoding="utf-8") as f:
    html = f.read()

ui_sovereign = """
<script>
// Motor de Estado Emocional (Color Sync)
window.cambiarHumor = (tipo) => {
    const root = document.documentElement;
    const pip = document.getElementById('pipTacticoContainer');
    const colors = {
        'normal': '#00ffcc',
        'analizando': '#ffb700',
        'urgente': '#ff0055'
    };
    if (pip) pip.style.borderColor = colors[tipo] || '#00ffcc';
    console.log("Daniela modo:", tipo);
};

// Motor de "Pensamiento" (Pulso visual de vida)
const pip = document.getElementById('pipTacticoContainer');
if (pip) {
    pip.style.transition = "box-shadow 1.5s ease-in-out";
    setInterval(() => {
        pip.style.boxShadow = "0 0 15px rgba(0, 255, 204, 0.4)";
        setTimeout(() => pip.style.boxShadow = "none", 750);
    }, 2000);
}
</script>
"""

if "window.cambiarHumor" not in html:
    html = html.replace("</body>", ui_sovereign + "\n</body>")
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html)

print("✅ Protocolo Sovereign aplicado: Daniela es ahora una entidad consciente.")
