import json
import os
import subprocess

BASE_DIR = os.path.expanduser("~/daniela-os/apps_script_admin")
os.makedirs(BASE_DIR, exist_ok=True)

print("⚡ [DANIELA OS]: Creando proyecto independiente en admin@aigestion.net...")

# 1. Crear el proyecto en la cuenta profesional
subprocess.run(
    ["clasp", "create", "--type", "standalone", "--title", "AIGestion_Core_Professional"],
    cwd=BASE_DIR,
)

# 2. Inyectar código del Webhook
gs_code = """/**
 * AIGestion.net — Core Webhook Relay
 * Operaciones bajo la cuenta corporativa admin@aigestion.net
 */
function doPost(e) {
  try {
    const data = JSON.parse(e.postData.contents);
    return ContentService.createTextOutput(JSON.stringify({
      status: "success",
      message: "Conexión profesional AIGestion.net verificada",
      received: data
    })).setMimeType(ContentService.MimeType.JSON);
  } catch (error) {
    return ContentService.createTextOutput(JSON.stringify({
      status: "error",
      error: error.toString()
    })).setMimeType(ContentService.MimeType.JSON);
  }
}
"""

with open(os.path.join(BASE_DIR, "Code.gs"), "w", encoding="utf-8") as f:
    f.write(gs_code)

# 3. Configurar appsscript.json con permisos públicos anónimos
manifest = {
    "timeZone": "Europe/Madrid",
    "dependencies": {},
    "exceptionLogging": "STACKDRIVER",
    "runtimeVersion": "V8",
    "webapp": {"access": "ANYONE_ANONYMOUS", "executeAs": "USER_DEPLOYING"},
}

with open(os.path.join(BASE_DIR, "appsscript.json"), "w", encoding="utf-8") as f:
    json.dump(manifest, f, indent=2)

# 4. Sincronizar y Desplegar
print("🚀 [DANIELA OS]: Subiendo y desplegando en Google Workspace...")
subprocess.run(["clasp", "push", "-f"], cwd=BASE_DIR)
result = subprocess.run(
    ["clasp", "deploy", "--description", "Prod_v1.0_Admin"],
    cwd=BASE_DIR,
    capture_output=True,
    text=True,
)

print(result.stdout)

# Extraer URL e invocar prueba
lines = result.stdout.splitlines()
for line in lines:
    if "Deployed" in line and "@" in line:
        dep_id = line.split()[1]
        url = f"https://script.google.com/macros/s/{dep_id}/exec"
        print(f"\n✅ [WEBHOOK PROFESIONAL ACTIVO]:\n{url}\n")
        print("🧪 [PROBANDO ENDPOINT]:")
        subprocess.run(
            [
                "curl",
                "-L",
                "-X",
                "POST",
                url,
                "-H",
                "Content-Type: application/json",
                "-d",
                '{"origen": "Termux_Admin", "evento": "Professional_Check"}',
            ]
        )
        break
