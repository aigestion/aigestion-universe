html_path = "index.html"
with open(html_path, encoding="utf-8") as f:
    html = f.read()

telegram_radar = """
<script>
// Radar de Notificaciones de Familia
setInterval(async () => {
    const res = await fetch('/check_alerts');
    const data = await res.json();

    if (data.remitente) {
        // Daniela proyecta la notificación en el PIP
        window.danielaMostrarEnPIP('html',
            `<div style="padding:15px; border-left:4px solid #ff0055;">
                <b style="color:#ffb700;">🔔 MENSAJE DE FAMILIA</b><br>
                <i style="color:#fff;">${data.remitente}:</i> "${data.texto}"
            </div>`,
            'Notificación Prioritaria'
        );
        // Voz de Daniela anunciando
        speechSynthesis.speak(new SpeechSynthesisUtterance("Tienes un mensaje de " + data.remitente));
    }
}, 5000);
</script>
"""

if "Radar de Notificaciones" not in html:
    html = html.replace("</body>", telegram_radar + "\n</body>")
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html)
    print("✅ Radar de notificaciones familiar activado.")
