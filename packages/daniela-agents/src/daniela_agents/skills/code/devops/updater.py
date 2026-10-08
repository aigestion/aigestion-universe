import logging
import subprocess


def update_system():
    """
    Skill #24: Auto-Updater.
    Sincroniza el repositorio local con el remoto (GitHub) y aplica cambios.
    """
    try:
        logging.info("Auto-Updater: Iniciando sincronización...")
        # Aseguramos fetch y pull para evitar conflictos
        subprocess.run(["git", "fetch", "origin"], check=True)
        result = subprocess.check_output(["git", "pull", "origin", "main"], text=True)
        return f"🔄 [UPDATER]: Sistema sincronizado correctamente:\n{result}"
    except Exception as e:
        return f"⚠️ [UPDATER ERROR]: Fallo en la actualización. Verifica permisos o conflictos: {e}"
