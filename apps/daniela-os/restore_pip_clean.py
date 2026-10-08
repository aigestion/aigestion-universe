filepath = "index.html"
with open(filepath, encoding="utf-8") as f:
    html = f.read()

# Script limpio que solo carga el vídeo en el PIP manteniendo los estilos originales
clean_video_script = """
<script>
document.addEventListener('DOMContentLoaded', () => {
    const area = document.getElementById('pipDisplayArea') || document.querySelector('.pip-display');
    if (area) {
        area.style.background = '#000';
        area.innerHTML = `
            <video autoplay loop muted playsinline style="width:100%; height:100%; object-fit:cover; border-radius:4px;">
                <source src="/media/presentacion_notebooklm.mp4" type="video/mp4">
            </video>
        `;
    }
});
</script>
"""

if "presentacion_notebooklm.mp4" not in html:
    html = html.replace("</body>", clean_video_script + "\n</body>")
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(html)
    print("✅ Plantilla restaurada y vídeo vinculado sin alterar la UI.")
