import json
import os
import shutil

import psutil

BASE_DIR = r"C:\Users\Alejandro\aig"
SCRIPTS_DIR = os.path.join(BASE_DIR, "scripts")
CONFIG_DIR = os.path.join(BASE_DIR, "config")
ASSETS_DIR = os.path.join(BASE_DIR, "assets")
OUTPUT_DIR = os.path.join(BASE_DIR, "output-assets")

print("⚙️ INICIANDO CONFIGURACIÓN INTEGRAL DE DANIELA OS")
print("=" * 50)

# 1. Directorios
print("\n📁 [1/4] Creando árbol de directorios...")
dirs = [BASE_DIR, SCRIPTS_DIR, CONFIG_DIR, ASSETS_DIR, OUTPUT_DIR,
        os.path.join(ASSETS_DIR, "broll"), os.path.join(ASSETS_DIR, "audio")]
for d in dirs:
    os.makedirs(d, exist_ok=True)
    print(f"  ✅ Directorio verificado: {d}")

# 2. Detener procesos colgados de Windsurf/Antigravity
print("\n🧹 [2/4] Limpiando procesos y cachés de Windsurf/Antigravity...")
for proc in psutil.process_iter(['name']):
    try:
        pname = proc.info['name'].lower()
        if any(x in pname for x in ['windsurf', 'antigravity', 'code']):
            proc.kill()
    except Exception:
        pass

user_profile = os.environ.get('USERPROFILE', r'C:\Users\Alejandro')
cache_paths = [
    os.path.join(user_profile, r'AppData\Roaming\Windsurf\User\workspaceStorage'),
    os.path.join(user_profile, r'AppData\Roaming\Windsurf\CachedData'),
    os.path.join(user_profile, '.codeium'),
    os.path.join(user_profile, '.antigravity')
]

for cp in cache_paths:
    if os.path.exists(cp):
        try:
            shutil.rmtree(cp)
            print(f"  🗑️ Caché eliminada: {cp}")
        except Exception as e:
            print(f"  ⚠️ No se pudo eliminar {cp}: {e}")

# 3. Exclusiones en settings.json
print("\n⚙️ [3/4] Ajustando exclusiones de archivos pesados en Windsurf...")
settings_dir = os.path.join(user_profile, r'AppData\Roaming\Windsurf\User')
os.makedirs(settings_dir, exist_ok=True)
settings_file = os.path.join(settings_dir, 'settings.json')

settings_data = {
    "files.watcherExclude": {
        "**/.git/objects/**": True,
        "**/output-assets/**": True,
        "**/assets/broll/**": True
    },
    "search.exclude": {
        "**/output_assets": True,
        "**/assets/broll": True
    }
}

# Cargar settings existentes si hay para no sobrescribir preferencias del usuario
if os.path.exists(settings_file):
    try:
        with open(settings_file, encoding='utf-8') as f:
            existing = json.load(f)
            existing.update(settings_data)
            settings_data = existing
    except Exception:
        pass

with open(settings_file, 'w', encoding='utf-8') as f:
    json.dump(settings_data, f, indent=2)

print(f"  ✅ Configuración guardada en: {settings_file}")

# 4. Comprobación de Módulos
print("\n🔍 [4/4] Verificando presencia de módulos de Python...")
modulos = [
    "notebook2json.py",
    "daniela_ultra_engine.py",
    "daniela_vision_auditor.py",
    "daniela_telemetry_monitor.py",
    "daniela_gmail_auditor.py",
    "daniela_hardware_bridge.py"
]

for mod in modulos:
    mod_path = os.path.join(SCRIPTS_DIR, mod)
    if os.path.exists(mod_path):
        print(f"  ✅ Módulo activo: {mod}")
    else:
        print(f"  ⚠️ Falta módulo: {mod}")

print("\n==================================================")
print("🚀 ¡CONFIGURACIÓN COMPLETA! ENTORNO LISTO.")
print("==================================================")
