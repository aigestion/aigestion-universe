import os

filepath = "index.html"
if not os.path.exists(filepath) and os.path.exists("templates/index.html"):
    filepath = "templates/index.html"

with open(filepath, encoding="utf-8") as f:
    html = f.read()

pip_stream_script = """
<script>
document.addEventListener('DOMContentLoaded', () => {
    // Proyectar vídeo/presentación sin restricciones de acceso
    setTimeout(() => {
        if (window.proyectarMediaEnPIP) {
            // Ejemplo de proyección de vídeo demo / presentación
            window.proyectarMediaEnPIP('https://www.youtube.com/embed/dQw4w9WgXcQ', 'youtube');
        }
    }, 1000);
});
</script>
"""

if "test_pip_stream" not in html:
    html = html.replace("</body>", pip_stream_script + "\n<!-- test_pip_stream -->\n</body>")
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(html)
    print("✅ Inyector de prueba multimedia listo.")
