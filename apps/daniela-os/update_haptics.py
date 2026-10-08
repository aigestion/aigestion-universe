with open("templates/index.html") as f:
    html = f.read()

haptic_script = """
<script>
function tocarHaptico(patron) {
    if ("vibrate" in navigator) {
        navigator.vibrate(patron || [50, 30, 50]);
    }
}
document.addEventListener("click", () => tocarHaptico([30]));
</script>
"""

if "tocarHaptico" not in html:
    html = html.replace("</body>", f"{haptic_script}\n</body>")
    with open("templates/index.html", "w") as f:
        f.write(html)
    print("🟢 [HUD]: Respuesta háptica inyectada en la interfaz web.")
