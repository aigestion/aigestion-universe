import os
import subprocess
import sys


def ejecutar_y_depurar(script_path):
    script = os.path.expanduser(script_path)
    if not os.path.exists(script):
        print(f"❌ Script no encontrado: {script_path}")
        return

    print(f"🔍 [DEPURADOR] Ejecutando y supervisando: {os.path.basename(script)}...")

    # Ejecutar el script capturando salida y errores
    proceso = subprocess.run(["python", script], capture_output=True, text=True)

    if proceso.returncode == 0:
        print("✅ [DEPURADOR] Ejecución limpia. Salida:")
        print(proceso.stdout)
    else:
        print("🚨 [DEPURADOR] Error detectado durante la ejecución:")
        error_log = proceso.stderr
        print(error_log)

        # Analizador de excepciones comunes
        print("\n🧠 [DIAGNÓSTICO AUTÓNOMO DE DANIELA]:")
        if "ImportError" in error_log or "ModuleNotFoundError" in error_log:
            print("👉 Causa: Falta un módulo o hay una discrepancia en los nombres de importación.")
        elif "NameError" in error_log:
            print("👉 Causa: Variable o función no definida (falta de import os/sys o tipografía).")
        elif "FileNotFoundError" in error_log:
            print("👉 Causa: La ruta de archivo especificada no existe en Termux.")
        else:
            print("👉 Causa: Error lógico o de sintaxis en tiempo de ejecución.")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        ejecutar_y_depurar(sys.argv[1])
    else:
        print("Uso: python autocorrect.py <ruta_script.py>")
