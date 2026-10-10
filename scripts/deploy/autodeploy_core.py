import json
import os
import subprocess

BASE_DIR = os.path.expanduser("~/daniela-os/apps_script")
os.makedirs(BASE_DIR, exist_ok=True)

print("⚡ [DANIELA OS]: Creando y configurando WebApp automáticamente...")

# 1. Configurar appsscript.json para acceso público anónimo
manifest = {
  "timeZone": "Europe/Madrid",
  "dependencies": {},
  "exceptionLogging": "STACKDRIVER",
  "runtimeVersion": "V8",
  "webapp": {
    "access": "ANYONE_ANONYMOUS",
    "executeAs": "USER_DEPLOYING"
  }
}

with open(os.path.join(BASE_DIR, "appsscript.json"), "w", encoding="utf-8") as f:
    json.dump(manifest, f, indent=2)

# 2. Subir cambios mediante clasp
subprocess.run(["clasp", "push", "-f"], cwd=BASE_DIR)

# 3. Crear el despliegue automático de la Web App
result = subprocess.run(
    ["clasp", "deploy", "--description", "AutoDeploy_Public_v3.0"],
    cwd=BASE_DIR,
    capture_output=True,
    text=True
)

print(result.stdout)

# 4. Extraer el Deployment ID y generar la URL final
lines = result.stdout.splitlines()
deployment_id = None
for line in lines:
    if "Deployed" in line and "@" in line:
        parts = line.split()
        deployment_id = parts[1]
        break

if deployment_id:
    url = f"https://script.google.com/macros/s/{deployment_id}/exec"
    print(f"\n✅ [WEBHOOK ACTIVO]: {url}")

    # 5. Probar el endpoint automáticamente con curl
    print("\n🧪 [PRUEBA AUTOMÁTICA]: Enviando evento de prueba...")
    test_cmd = [
        "curl", "-L", "-X", "POST", url,
        "-H", "Content-Type: application/json",
        "-d", '{"origen": "Termux_AutoDeploy", "evento": "Core_Active", "detalles": "Despliegue 100% automatico"}'
    ]
    subprocess.run(test_cmd)
else:
    print("⚠️ No se pudo extraer el ID de despliegue automáticamente.")

