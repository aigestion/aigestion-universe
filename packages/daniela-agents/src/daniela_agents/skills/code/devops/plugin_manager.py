import importlib
import logging
import os

DYNAMIC_SKILLS = {}

def load_plugin(plugin_name):
    """
    Skill #31: Dynamic Plugin Manager (Hot-Reloading).
    Carga o recarga dinámicamente un módulo dentro de la carpeta skills.
    """
    try:
        module_path = f"skills.{plugin_name}"
        if module_path in importlib.sys.modules:
            mod = importlib.reload(importlib.sys.modules[module_path])
            status = "reinstalado/recargado"
        else:
            mod = importlib.import_module(module_path)
            status = "cargado exitosamente"

        DYNAMIC_SKILLS[plugin_name] = mod
        logging.info(f"Plugin Manager: Módulo '{plugin_name}' {status}.")
        return f"🔌 [PLUGIN MANAGER]: Módulo '{plugin_name}' {status} en caliente."
    except Exception as e:
        logging.error(f"Error cargando plugin '{plugin_name}': {e}")
        return f"⚠️ [PLUGIN ERROR]: No se pudo cargar '{plugin_name}': {e}"

def list_plugins():
    """Lista las skills dinámicas cargadas en memoria."""
    skills_dir = os.path.expanduser("~/daniela-os/skills/")
    available = [f[:-3] for f in os.listdir(skills_dir) if f.endswith(".py") and not f.startswith("__")]
    loaded = list(DYNAMIC_SKILLS.keys())
    return f"📋 [PLUGINS DISPONIBLES]: {len(available)} en disco | {len(loaded)} dinámicos activos en memoria."
