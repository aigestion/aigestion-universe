with open("app_daniela.py", encoding="utf-8") as f:
    code = f.read()

# Lógica estricta de ejecución de comandos por consola
flash_handler = """
    # Exec hardware flash
    if "flash" in user_message.lower():
        if any(w in user_message.lower() for w in ["enciende", "activa", "prendo"]):
            import subprocess
            subprocess.run(["termux-torch", "on"], check=False)
            return jsonify({"response": "⚡ Flash físico activado por hardware."})
        elif any(w in user_message.lower() for w in ["apaga", "desactiva"]):
            import subprocess
            subprocess.run(["termux-torch", "off"], check=False)
            return jsonify({"response": "💡 Flash físico apagado."})
"""

if "termux-torch" not in code:
    code = code.replace("def api_chat():", "def api_chat():\n" + flash_handler)
    with open("app_daniela.py", "w", encoding="utf-8") as f:
        f.write(code)
    print("✅ Parche de hardware inyectado con éxito.")
else:
    print("ℹ️ El controlador de hardware ya estaba registrado.")
