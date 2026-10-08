html_path = "index.html"
with open(html_path, encoding="utf-8") as f:
    html = f.read()

zen_button = """
<script>
// Comando para alternar el Modo Zen desde el PIP
window.toggleModoZen = (activo) => {
    if(activo) {
        document.body.style.filter = "none";
        alert("Modo Zen ACTIVADO: Solo familia y urgencias.");
    } else {
        alert("Modo Zen DESACTIVADO: Notificaciones restablecidas.");
    }
};
</script>
"""

if "window.toggleModoZen" not in html:
    html = html.replace("</body>", zen_button + "\n</body>")
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html)
    print("✅ Botón de gestión de Modo Zen listo.")
