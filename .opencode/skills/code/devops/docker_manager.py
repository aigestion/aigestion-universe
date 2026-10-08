import subprocess


def list_containers():
    """Lista contenedores Docker activos."""
    try:
        output = subprocess.check_output(["docker", "ps", "--format", "{{.Names}} ({{.Status}})"], text=True)
        return f"🐳 [DOCKER]: Contenedores activos:\n{output.strip()}"
    except Exception:
        return "⚠️ [DOCKER]: Docker no instalado o no corriendo."

def create_venv(path):
    """Crea un entorno virtual de Python."""
    try:
        subprocess.run(["python3", "-m", "venv", path], check=True)
        return f"🐍 [VENV]: Entorno creado en {path}"
    except Exception as e:
        return f"⚠️ [VENV ERROR]: {e}"
