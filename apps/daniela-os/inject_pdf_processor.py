with open("server.py") as f:
    code = f.read()

pdf_endpoint_code = '''
import os
import io
from pypdf import PdfReader
from PIL import Image

@app.route('/api/upload_brand_pdf', methods=['POST'])
def upload_brand_pdf():
    user_id = request.args.get('user_id', 1)
    if 'pdf_file' not in request.files:
        return jsonify({"status": "error", "message": "No se adjuntó ningún archivo PDF"}), 400

    file = request.files['pdf_file']
    if file.filename == '':
        return jsonify({"status": "error", "message": "Archivo no seleccionado"}), 400

    try:
        reader = PdfReader(file)
        full_text = ""
        extracted_hex_colors = []

        # 1. Extracción de texto y búsqueda de códigos Hexadecimales (#RRGGBB)
        for page in reader.pages:
            text = page.extract_text() or ""
            full_text += text + "\n"
            found_hex = re.findall(r'#(?:[0-9a-fA-F]{3}){1,2}\b', text)
            for h in found_hex:
                if len(h) == 7 and h not in extracted_hex_colors:
                    extracted_hex_colors.append(h.lower())

        # 2. Análisis del Prompt Corporativo basado en el texto extraído
        summary_prompt = "Eres la entidad sintética corporativa. "
        if full_text:
            clean_text = " ".join(full_text.split()[:300]) # Primeras 300 palabras clave
            summary_prompt += f"Directrices de la marca extraídas del manual: {clean_text}"

        # 3. Asignación de Colores Primario y Secundario
        primary_color = extracted_hex_colors[0] if len(extracted_hex_colors) > 0 else "#00f0ff"
        secondary_color = extracted_hex_colors[1] if len(extracted_hex_colors) > 1 else "#e024c3"

        # 4. Actualización en la Base de Datos SQLite (universe_branding)
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO universe_branding (user_id, primary_color, secondary_color, system_prompt_override)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                primary_color=excluded.primary_color,
                secondary_color=excluded.secondary_color,
                system_prompt_override=excluded.system_prompt_override
        """, (user_id, primary_color, secondary_color, summary_prompt))
        conn.commit()
        conn.close()

        return jsonify({
            "status": "success",
            "message": "Manual de marca procesado con éxito",
            "extracted_data": {
                "primary_color": primary_color,
                "secondary_color": secondary_color,
                "detected_colors": extracted_hex_colors,
                "system_prompt_override": summary_prompt
            }
        })

    except Exception as e:
        return jsonify({"status": "error", "message": f"Error al procesar PDF: {str(e)}"}), 500
'''

if "/api/upload_brand_pdf" not in code:
    code = code.replace(
        "if __name__ == '__main__':", pdf_endpoint_code + "\nif __name__ == '__main__':"
    )
    with open("server.py", "w") as f:
        f.write(code)
    print("Endpoint /api/upload_brand_pdf inyectado con éxito.")
else:
    print("El endpoint /api/upload_brand_pdf ya existía en server.py.")
