import os

filepath = "index.html"
if not os.path.exists(filepath) and os.path.exists("templates/index.html"):
    filepath = "templates/index.html"

if os.path.exists(filepath):
    with open(filepath, encoding="utf-8") as f:
        html = f.read()

    # Ocultar el div #pinOverlay directamente en el CSS
    html = html.replace("#pinOverlay {", "#pinOverlay { display: none !important; ")

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(html)
    print("✅ Bloqueo #pinOverlay desactivado permanentemente.")
else:
    print("❌ No se encontró index.html")
