import os

filepath = "index.html"
if not os.path.exists(filepath) and os.path.exists("templates/index.html"):
    filepath = "templates/index.html"

with open(filepath, encoding="utf-8") as f:
    html = f.read()

auto_pip_script = """
<script>
document.addEventListener('DOMContentLoaded', () => {
    // Motor de Proyección y Decisiones para el PIP Master
    window.proyectarPresentacionAuto = function(titulo, diapositivas) {
        const area = document.getElementById('pipDisplayArea') || document.querySelector('.pip-display');
        if (!area) return;

        let slidesHTML = diapositivas.map(d => `
            <div style="background:#111318; border-left:3px solid #00ffcc; padding:8px; margin-bottom:8px; border-radius:3px; text-align:left;">
                <b style="color:#ffb700; font-size:0.75rem;">Diapositiva ${d.diapo}: ${d.tema}</b>
                <p style="color:#ccc; font-size:0.68rem; margin:3px 0 0 0;">${d.detalles}</p>
            </div>
        `).join('');

        area.innerHTML = `
            <div style="padding:10px; color:#00ffcc; font-family:monospace; height:100%; box-sizing:border-box; overflow-y:auto; background:#08080a;">
                <div style="color:#ff0055; font-weight:bold; font-size:0.8rem; border-bottom:1px solid #00ffcc; padding-bottom:4px; margin-bottom:8px;">📊 ${titulo}</div>
                ${slidesHTML}
                <div style="margin-top:10px; display:flex; gap:5px;">
                    <button onclick="fetch('/apply_suggestion', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({code:'// patch'})}).then(()=>alert('✅ Propuesta aprobada e inyectada.'));" style="background:#00ffcc; color:#000; border:none; padding:6px 8px; font-weight:bold; font-size:0.65rem; border-radius:3px; cursor:pointer; flex:1;">APROBAR E INYECTAR</button>
                    <button onclick="document.getElementById('pipDisplayArea').innerHTML='<div style=\"padding:20px; color:#666; font-size:0.7rem;\">Propuesta descartada.</div>';" style="background:#222; color:#fff; border:1px solid #444; padding:6px 8px; font-size:0.65rem; border-radius:3px; cursor:pointer; flex:1;">DESCARTAR</button>
                </div>
            </div>
        `;
    };

    // Auto-Carga de la Propuesta Sovereign v10.5
    setTimeout(() => {
        const slides = [
            {diapo: 1, tema: "Stealth OLED", detalles: "Píxeles en negro puro (#000000) si batería <20% o en horario nocturno."},
            {diapo: 2, tema: "Glass HUD", detalles: "Bordes neón adaptativos que responden al uso de procesador en Termux."},
            {diapo: 3, tema: "Self-Healing", detalles: "Auto-aplicación en Sandbox con backup instantáneo en Git y Rollback."}
        ];
        window.proyectarPresentacionAuto("PROPUESTA SOVEREIGN v10.5", slides);
    }, 1200);
});
</script>
"""

if "proyectarPresentacionAuto" not in html:
    html = html.replace("</body>", auto_pip_script + "\n<!-- auto_pip_script -->\n</body>")
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(html)
    print("✅ Motor de Proyección y Aprobación en PIP configurado correctamente.")
else:
    print("ℹ️ El motor ya está presente en el archivo index.html.")
