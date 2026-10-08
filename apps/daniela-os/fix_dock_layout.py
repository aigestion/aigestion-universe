import os

path = os.path.expanduser("~/daniela-os/index.html")
with open(path) as f:
    content = f.read()

# 1. Asegurar que body use dvh (Dynamic Viewport Height) para navegadores móviles
content = content.replace("height: 100vh;", "height: 100dvh; height: 100vh;")

# 2. Forzar que el viewport principal deje espacio libre abajo para la barra
content = content.replace("bottom: 0;", "bottom: 70px;")
content = content.replace("padding-bottom: 20px;", "padding-bottom: 80px;")

# 3. Anclar la barra inferior con máxima prioridad visual
dock_css_old = ".bottom-hud {"
dock_css_new = """.bottom-hud {
            position: fixed !important;
            bottom: 0 !important;
            left: 0 !important;
            right: 0 !important;
            height: 65px !important;
            z-index: 9999 !important;
            background: rgba(15, 23, 42, 0.98) !important;
            box-shadow: 0 -4px 20px rgba(0,0,0,0.8);"""

if dock_css_old in content:
    content = content.replace(dock_css_old, dock_css_new)

with open(path, "w") as f:
    f.write(content)

print("✅ Parche CSS para la barra inferior fijado correctamente.")
