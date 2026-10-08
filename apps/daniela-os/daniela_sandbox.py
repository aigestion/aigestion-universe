import os
import py_compile
import subprocess
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def check_syntax(file_path):
    print(f"🔍 [SANDBOX] Verificando sintaxis de '{file_path}'...")
    try:
        py_compile.compile(file_path, doraise=True)
        print("✅ [SANDBOX] Sintaxis de Python 100% válida.")
        return True
    except py_compile.PyCompileError as e:
        print(f"❌ [SANDBOX ERROR] Fallo de compilación:\n{e}")
        return False


def make_git_snapshot(msg):
    print("📸 [SANDBOX] Generando snapshot de seguridad en Git...")
    try:
        subprocess.run(["git", "add", "."], cwd=BASE_DIR, check=True)
        subprocess.run(
            ["git", "commit", "-m", f"sandbox-snapshot: {msg}"], cwd=BASE_DIR, check=True
        )
        print("✅ [SANDBOX] Snapshot creado correctamente.")
    except Exception as e:
        print(f"⚠️ [SANDBOX WARNING] No se pudo crear snapshot: {e}")


def reload_tmux_service():
    print("🔄 [SANDBOX] Programando reinicio limpio del servicio 'daniela'...")
    # Ejecuta el pkill y relanzamiento en background para no matarse a sí mismo
    sh_script = f"sleep 1 && pkill -9 -f app_daniela.py && tmux new-session -d -s daniela -c {BASE_DIR} 'python3 -u app_daniela.py'"
    subprocess.Popen(
        ["sh", "-c", sh_script],
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    print("🚀 [SANDBOX] Reinicio diferido programado. La Sandbox ha finalizado con éxito.")
    return True


def safe_deploy(draft_file, target_file="app_daniela.py"):
    draft_path = os.path.join(BASE_DIR, draft_file)
    target_path = os.path.join(BASE_DIR, target_file)

    if not os.path.exists(draft_path):
        print(f"❌ [SANDBOX ERROR] El borrador '{draft_file}' no existe.")
        return False

    if not check_syntax(draft_path):
        print("⛔ [SANDBOX ABORTADO] No se aplicaron cambios debido a errores en el borrador.")
        return False

    make_git_snapshot(f"Previo a despliegue de {draft_file}")

    print(f"📦 [SANDBOX] Reemplazando '{target_file}' con '{draft_file}'...")
    try:
        with open(draft_path) as src, open(target_path, "w") as dst:
            dst.write(src.read())
        print("✅ [SANDBOX] Archivo reemplazado con éxito.")
    except Exception as e:
        print(f"❌ [SANDBOX ERROR] Fallo al copiar archivos: {e}")
        return False

    return reload_tmux_service()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python3 daniela_sandbox.py <archivo_borrador.py>")
        sys.exit(1)

    draft = sys.argv[1]
    target = sys.argv[2] if len(sys.argv) > 2 else "app_daniela.py"

    success = safe_deploy(draft, target)
    sys.exit(0 if success else 1)
