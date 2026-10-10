import os
import subprocess
import sys

DIR_SANDBOX = os.path.expanduser("~/daniela-os/sandbox")

def inicializar_sandbox():
    os.makedirs(DIR_SANDBOX, exist_ok=True)

def probar_codigo(nombre_archivo, codigo):
    inicializar_sandbox()
    ruta_script = os.path.join(DIR_SANDBOX, f"{nombre_archivo}.py")

    # 1. Escribir el código en el Sandbox
    with open(ruta_script, 'w', encoding='utf-8') as f:
        f.write(codigo)

    print(f"🛠️ [ARQUITECTO] Código escrito en Sandbox: sandbox/{nombre_archivo}.py")

    # 2. Test de sintaxis con Python
    resultado = subprocess.run(["python", "-m", "py_compile", ruta_script], capture_output=True, text=True)

    if resultado.returncode == 0:
        print("✅ [ARQUITECTO] Sintaxis verificada correctamente. Script listo para producción.")
        return True
    else:
        print("❌ [ARQUITECTO] Error de sintaxis detectado en el Sandbox:")
        print(resultado.stderr)
        return False

def desplegar_a_produccion(nombre_archivo):
    ruta_sandbox = os.path.join(DIR_SANDBOX, f"{nombre_archivo}.py")
    ruta_prod = os.path.expanduser(f"~/daniela-os/{nombre_archivo}.py")

    if os.path.exists(ruta_sandbox):
        os.rename(ruta_sandbox, ruta_prod)
        print(f"🚀 [ARQUITECTO] Script desplegado con éxito en el núcleo: ~/{nombre_archivo}.py")
    else:
        print("⚠️ No existe el archivo en el sandbox.")

if __name__ == "__main__":
    if len(sys.argv) >= 3 and sys.argv[1] == "crear":
        nombre = sys.argv[2]
        # El resto de argumentos conforman el código
        codigo = " ".join(sys.argv[3:])
        if probar_codigo(nombre, codigo):
            desplegar_a_produccion(nombre)
    else:
        print("Uso: python arquitecto.py crear <nombre_script> <codigo_python>")
