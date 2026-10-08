import logging
import os

import PIL.Image
import PIL.ImageDraw
import PIL.ImageFont


def generate_infographic(topic, insights):
    try:
        width, height = 800, 1000
        img = PIL.Image.new('RGB', (width, height), color='#05070a')
        draw = PIL.ImageDraw.Draw(img)

        # Estilo Cyberpunk / Sovereign
        draw.rectangle([10, 10, width-10, height-10], outline='#00ffcc', width=2)
        draw.rectangle([20, 20, width-20, 100], fill='#0a0f19', outline='#ff0055', width=1)

        # Título
        draw.text((30, 40), f"DANIELA OS - DEEP RESEARCH: {topic.upper()[:25]}", fill='#00ffcc')

        # Contenido / Infografía
        y = 140
        for i, insight in enumerate(insights, 1):
            draw.rectangle([30, y, width-30, y+100], fill='#0a0f19', outline='#00ffcc', width=1)
            draw.text((45, y+20), f"0{i}. INSIGHT CLAVE", fill='#ffb700')
            draw.text((45, y+50), insight[:60], fill='#ffffff')
            y += 120

        os.makedirs("static", exist_ok=True)
        file_path = f"static/infographic_{os.urandom(4).hex()}.png"
        img.save(file_path)
        logging.info(f"Infografía generada: {file_path}")
        return f"/{file_path}"
    except Exception as e:
        logging.error(f"Error en Designer: {str(e)}")
        return None
