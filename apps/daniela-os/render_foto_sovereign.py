import os

filepath = "index.html"
if not os.path.exists(filepath) and os.path.exists("templates/index.html"):
    filepath = "templates/index.html"

if os.path.exists(filepath):
    with open(filepath, encoding="utf-8") as f:
        html = f.read()

    # JS para forzar la carga de la foto guardada en el lienzo/avatar original
    js_render = """
    <script>
    document.addEventListener('DOMContentLoaded', () => {
        const fotoUrl = '/static/daniela_foto.jpg?v=' + new Date().getTime();

        // 1. Buscar imágenes o contenedores de foto en la plantilla
        const imgs = document.querySelectorAll('img');
        let fotoCambiada = false;

        imgs.forEach(img => {
            if (img.src.includes('daniela') || img.alt.toLowerCase().includes('daniela') || img.closest('.canvas, .studio, .avatar')) {
                img.src = fotoUrl;
                fotoCambiada = true;
            }
        });

        // 2. Si no es un <img> sino un fondo CSS (background-image)
        const canvas = document.querySelector('.canvas, #studio, .avatar-box');
        if (canvas) {
            canvas.style.backgroundImage = `url('${fotoUrl}')`;
            canvas.style.backgroundSize = 'cover';
            canvas.style.backgroundPosition = 'center';
        }
    });
    </script>
    """

    if "fotoUrl" not in html:
        html = (
            html.replace("</body>", js_render + "\n</body>")
            if "</body>" in html
            else html + js_render
        )
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(html)
        print("✅ Renderizador de foto inyectado correctamente.")
    else:
        print("ℹ️ El renderizador ya estaba instalado.")
