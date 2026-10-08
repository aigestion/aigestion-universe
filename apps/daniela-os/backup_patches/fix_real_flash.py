import os

app_path = "app_daniela.py"
if os.path.exists(app_path):
    with open(app_path, encoding="utf-8") as f:
        code = f.read()

    # Reemplazar o inyectar la lógica de activación por hardware
    flash_logic = """
    if "flash" in user_message.lower():
        if "enciende" in user_message.lower() or "activa" in user_message.lower():
            os.system("termux-torch on &")
            return jsonify({"response": "⚡ Flash de la cámara activado físicamente por hardware."})
        elif "apaga" in user_message.lower() or "desactiva" in user_message.lower():
            os.system("termux-torch off &")
            return jsonify({"response": "💡 Flash de la cámara apagado."})
"""
    if "termux-torch" not in code:
        # Inyectar justo antes de la respuesta por defecto en el endpoint de chat
        code = code.replace(
            "return jsonify({'response':", flash_logic + "\n    return jsonify({'response':"
        )
        with open(app_path, "w", encoding="utf-8") as f:
            f.write(code)
        print("✅ Control físico del flash inyectado en el servidor.")
