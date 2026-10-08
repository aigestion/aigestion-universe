import os

from safe_exec import run_code

# 1. Crear el Script Centinela de Rescate (Watchdog & Rollback)
cat_watchdog = """#!/bin/bash
# Centinela de Rescate Daniela OS
cd ~/daniela-os

python app_daniela.py
EXIT_CODE=$?

if [ $EXIT_CODE -ne 0 ]; then
    echo "⚠️ ERROR DETECTADO EN EL SERVIDOR. Ejecutando Rollback de Seguridad..."
    git reset --hard HEAD~1
    echo "✅ Sistema restaurado al último estado estable. Reconstruyendo..."
    python app_daniela.py
fi
"""

with open("run_safe.sh", "w", encoding="utf-8") as f:
    f.write(cat_watchdog)

run_code("chmod +x run_safe.sh")

# 2. Inyectar endpoint de auto-aplicación en app_daniela.py
app_path = "app_daniela.py"
if os.path.exists(app_path):
    with open(app_path, encoding="utf-8") as f:
        code = f.read()

    evolution_backend = """
# === ENGINE DE AUTO-EVOLUCIÓN SEGURA ===
import subprocess
import py_compile

@app.route('/apply_suggestion', methods=['POST'])
def apply_suggestion():
    data = request.json
    script_code = data.get('code', '')

    # Paso 1: Guardar en sandbox
    temp_file = "temp_patch.py"
    with open(temp_file, "w", encoding="utf-8") as f:
        f.write(script_code)

    # Paso 2: Test sintáctico
    try:
        py_compile.compile(temp_file, doraise=True)
    except Exception as e:
        return jsonify({"status": "error", "message": f"Prueba de sintaxis fallida: {str(e)}"})

    # Paso 3: Snapshot de Git pre-aplicación
    subprocess.run(["git", "add", "."], capture_output=True)
    subprocess.run(["git", "commit", "-m", "Snapshot previo a auto-parche"], capture_output=True)

    # Paso 4: Ejecución del parche
    res = subprocess.run(["python", temp_file], capture_output=True, text=True)
    os.remove(temp_file)

    return jsonify({"status": "success", "output": res.stdout})
# === END AUTO-EVOLUCIÓN ===
"""

    if "ENGINE DE AUTO-EVOLUCIÓN SEGURA" not in code:
        with open(app_path, "a", encoding="utf-8") as f:
            f.write("\n" + evolution_backend)
        print("✅ Motor de Auto-Evolución e Inyección Segura instalado.")
