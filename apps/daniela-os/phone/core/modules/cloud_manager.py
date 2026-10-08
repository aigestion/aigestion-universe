import subprocess
import sys

PROJECT_ID = "gen-lang-client-0804172662"


def run_cmd(cmd):
    res = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    return res.stdout.strip() if res.returncode == 0 else f"⚠️ Error: {res.stderr.strip()}"


def get_status():
    print(f"📊 **ESTADO GLOBAL DEL PROYECTO GCP: [{PROJECT_ID}]**\n")
    print("--- 1. SERVICIOS Y APIS ACTIVAS ---")
    services = run_cmd("gcloud services list --enabled --format='value(config.name)'")
    print(services[:300] + ("..." if len(services) > 300 else ""))

    print("\n--- 2. ALMACENAMIENTO (CLOUD STORAGE) ---")
    buckets = run_cmd("gcloud storage buckets list --format='value(name)'")
    print(buckets if buckets else "No hay buckets creados.")

    print("\n--- 3. INSTANCIAS (COMPUTE ENGINE) ---")
    vms = run_cmd("gcloud compute instances list --format='table(name,zone,status)'")
    print(vms if vms else "No hay instancias activas.")


def create_bucket(bucket_name):
    print(f"📦 Creando bucket gs://{bucket_name} en [{PROJECT_ID}]...")
    res = run_cmd(f"gcloud storage buckets create gs://{bucket_name} --location=us-central1")
    print(res)


def execute_action(action_type, target):
    if action_type == "status":
        get_status()
    elif action_type == "bucket":
        create_bucket(target)
    else:
        print(f"Comando '{action_type}' no reconocido.")


if __name__ == "__main__":
    cmd_type = sys.argv[1] if len(sys.argv) > 1 else "status"
    target_param = sys.argv[2] if len(sys.argv) > 2 else "aig-unified-storage"
    execute_action(cmd_type, target_param)
