import logging
import os
import subprocess

PROJECTS_DIR = os.path.expanduser("~/daniela-os/projects")

def create_app_scaffold(name, tech="firebase-hosting"):
    """Crea la estructura base de una app premium."""
    try:
        os.makedirs(PROJECTS_DIR, exist_ok=True)
        app_path = os.path.join(PROJECTS_DIR, name)
        os.makedirs(app_path, exist_ok=True)

        # Crear index.html básico
        with open(os.path.join(app_path, "index.html"), "w") as f:
            f.write(f"<html><body><h1>{name} - App Premium Soberana</h1></body></html>")

        logging.info(f"App Factory: Estructura para {name} creada.")
        return f"🚀 [APP FACTORY]: App '{name}' scaffold creada en {app_path}"
    except Exception as e:
        return f"⚠️ [FACTORY ERROR]: {e}"

def deploy_app(name):
    """Despliega la app usando Firebase CLI."""
    app_path = os.path.join(PROJECTS_DIR, name)
    try:
        # Ejecutar despliegue
        result = subprocess.check_output(["firebase", "deploy", "--only", "hosting"], cwd=app_path, text=True)
        return f"✅ [DEPLOY]: App '{name}' desplegada exitosamente.\n{result}"
    except Exception as e:
        return f"❌ [DEPLOY ERROR]: Fallo en despliegue. Asegúrate de haber hecho 'firebase init' en la carpeta. {e}"
