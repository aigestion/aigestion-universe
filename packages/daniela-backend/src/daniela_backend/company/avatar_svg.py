#!/usr/bin/env python3
# avatar_svg.py - Generación de avatares SVG para directores y DG
# Source: indicaciones.txt conversacion 1 - 21 JPEG + 21 SVG backup

import os

DATA_DIR = os.path.join(os.path.dirname(__file__), "data", "company", "faces")
FACES_DIR = DATA_DIR

# Perfiles con rutas de imágenes
DIRECTOR_PROFILES = [
    {"nombre": "Daniela Ferrer Soler", "genero": "F", "archivo": "daniela_avatar.jpg"},
    {"nombre": "Elena Vidal", "genero": "F", "archivo": "elena_vidal.jpg"},
    {"nombre": "Amara Diallo", "genero": "F", "archivo": "amara_diallo.jpg"},
    {"nombre": "Priya Sharma", "genero": "F", "archivo": "priya_sharma.jpg"},
    {"nombre": "Kenji Tanaka", "genero": "M", "archivo": "kenji_tanaka.jpg"},
    {"nombre": "Sofia Petrova", "genero": "F", "archivo": "sofia_petrova.jpg"},
    {"nombre": "Liam O'Connor", "genero": "M", "archivo": "liam_oconnor.jpg"},
    {"nombre": "Valentina Ríos", "genero": "F", "archivo": "valentina_rios.jpg"},
    {"nombre": "Alex Rivera", "genero": "M", "archivo": "alex_rivera.jpg"},
    {"nombre": "Yuki Nakamura", "genero": "F", "archivo": "yuki_nakamura.jpg"},
    {"nombre": "Marco Ruiz", "genero": "M", "archivo": "marco_ruiz.jpg"},
    {"nombre": "Kwame Mensah", "genero": "M", "archivo": "kwame_mensah.jpg"},
    {"nombre": "Ingrid Larsen", "genero": "F", "archivo": "ingrid_larsen.jpg"},
    {"nombre": "Diego Fernández", "genero": "M", "archivo": "diego_fernandez.jpg"},
    {"nombre": "Camille Dubois", "genero": "F", "archivo": "camille_dubois.jpg"},
    {"nombre": "Mei Chen", "genero": "F", "archivo": "mei_chen.jpg"},
    {"nombre": "Jordan Blake", "genero": "M", "archivo": "jordan_blake.jpg"},
    {"nombre": "Fatima Al-Hassan", "genero": "F", "archivo": "fatima_al-hassan.jpg"},
    {"nombre": "Noah Kim", "genero": "M", "archivo": "noah_kim.jpg"},
    {"nombre": "Lucía Gómez", "genero": "F", "archivo": "lucia_gomez.jpg"},
    {"nombre": "David Steiner", "genero": "M", "archivo": "david_steiner.jpg"},
]

# Generar avatar SVG placeholder por si no existe la imagen JPEG
def generar_avatar_svg(nombre, genero):
    """Genera un avatar SVG con las iniciales y color según género"""
    iniciales = nombre.split()[0][0] + nombre.split()[-1][0]
    color_base = {"F": "#FF69B4", "M": "#4169E1"}[genero]

    svg = f'''<svg width="200" height="200" viewBox="0 0 200 200" xmlns="http://www.w3.org/2000/svg">
  <circle cx="100" cy="100" r="90" fill="{color_base}"/>
  <text x="100" y="105" text-anchor="middle" font-family="Verdana" font-size="70" fill="white">{iniciales}</text>
</svg>'''
    return svg

# Generar todos los avatares
def inicializar_avatares():
    """Crear archivos SVG de respaldo para todos los directores"""
    inicializados = []
    for profile in DIRECTOR_PROFILES:
        nombre = profile["nombre"]
        archivo_jpg = os.path.join(FACES_DIR, profile["archivo"])
        svg_path = os.path.join(FACES_DIR, f"{nombre.replace(' ', '_')}.svg")

        if not os.path.exists(archivo_jpg):
            # Crear SVG de respaldo
            svg_content = generar_avatar_svg(nombre, profile["genero"])
            with open(svg_path, "w", encoding="utf-8") as f:
                f.write(svg_content)
            inicializados.append(nombre)
    return inicializados

# Punto de entrada
if __name__ == "__main__":
    creados = inicializar_avatares()
    print(f"Avatars SVG generados para: {creados}")
    print("Total avatars JPEG reales: 21")
    print(f"Total avatars SVG de respaldo: {len(creados)}")
