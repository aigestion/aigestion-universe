import os

from PIL import Image, ImageDraw

MEDIA_DIR = os.path.expanduser("~/daniela-os/media")
os.makedirs(MEDIA_DIR, exist_ok=True)

print("🎨 [DANIELA OS]: Renderizando fotograma base para el anuncio de AIGestion.net...")

# 1. Crear lienzo gráfico 1080x1920 (Formato Vertical 9:16)
img = Image.new("RGB", (1080, 1920), color="#05070d")
draw = ImageDraw.Draw(img)

# Dibujar elementos ciberpunk neon (Marcos y Neón Cian/Magenta)
draw.rectangle([40, 40, 1040, 1880], outline="#00ffff", width=6)
draw.rectangle([80, 80, 1000, 1840], outline="#ff00ff", width=3)

# Dibujar líneas de cuadrícula y holograma
for y in range(200, 1800, 100):
    draw.line([(80, y), (1000, y)], fill="#00ffff1a", width=1)

# Títulos del Anuncio
draw.text((120, 250), "AIGESTION.NET", fill="#00ffff")
draw.text((120, 320), "DANIELA OS // CIBER-EJECUTIVA", fill="#ff00ff")
draw.text((120, 1600), "SISTEMA BUROCRÁTICO EN ORDEN ABSOLUTO", fill="#ffffff")

# Guardar asset de imagen
asset_path = os.path.join(MEDIA_DIR, "daniela_office_frame.png")
img.save(asset_path)
print(f"🖼️ Asset gráfico generado en: {asset_path}")

# 2. Sincronizar actualización con Google Drive Docs
try:
    import importlib

    gdr = importlib.import_module("plugins.gdrive_reporter")
    resultado = gdr.run("exportar")
    print(f"📄 [GDRIVE VAULT]: {resultado}")
except Exception as e:
    print(f"⚠️ [GDRIVE VAULT]: {e}")

print("\n✨ [OPERACIÓN COMPLETADA]: Asset listo y expediente actualizado.")
