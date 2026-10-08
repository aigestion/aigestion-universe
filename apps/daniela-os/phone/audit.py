import os
import subprocess

HOME = os.path.expanduser("~")

EXPECTED_STRUCTURE = {
    "core": ["daniela_brain.py", "danielas_guardians.py", "run_daemon.sh"],
    "apps/AIGESTION-MONOREPO": [],
    "logs": ["guardians.log"],
    ".shortcuts": ["Daniela.sh"],
    "whisper.cpp/build/bin": ["whisper-cli"],
    "whisper.cpp/models": ["ggml-base.bin", "ggml-small.bin"],
}


def audit():
    print("==================================================")
    print("🔍 AUDITORÍA DE ESTRUCTURA Y ACOPLAMIENTO DANIELA OS")
    print("==================================================")

    issues = []
    successes = []

    # 1. Verificar carpetas y archivos clave
    for folder, files in EXPECTED_STRUCTURE.items():
        folder_path = os.path.join(HOME, folder)
        if os.path.exists(folder_path):
            successes.append(f"Carpeta presente: ~/{folder}")
            for f in files:
                file_path = os.path.join(folder_path, f)
                if os.path.exists(file_path):
                    # Verificar permisos si es executable
                    if f.endswith(".sh") or f == "whisper-cli":
                        is_exec = os.access(file_path, os.X_OK)
                        if is_exec:
                            successes.append(f"  └─ File + Exec OK: {f}")
                        else:
                            issues.append(f"  └─ Permiso de ejecución faltante: {file_path}")
                    else:
                        successes.append(f"  └─ Archivo OK: {f}")
                else:
                    issues.append(f"  └─ Archivo faltante: {file_path}")
        else:
            issues.append(f"Carpeta faltante: ~/{folder}")

    # 2. Revisar almacenamiento temporal RAM
    ram_dir = "/data/data/com.termux/files/usr/tmp/daniela_ram"
    if os.path.exists(ram_dir):
        files_in_ram = os.listdir(ram_dir)
        successes.append(
            f"Directorio RAM temporal activo: {ram_dir} ({len(files_in_ram)} archivos)"
        )
    else:
        issues.append("Directorio RAM temporal no encontrado.")

    # 3. Comprobar Demonio Activo
    ps_res = subprocess.run(["ps", "aux"], capture_output=True, text=True)
    if "run_daemon.sh" in ps_res.stdout or "danielas_guardians" in ps_res.stdout:
        successes.append("Daemon de Guardianes: ACTIVO EN SEGUNDO PLANO 🛡️")
    else:
        issues.append("Daemon de Guardianes: INACTIVO (Reiniciar con ~/core/run_daemon.sh)")

    # 4. Comprobar Conexión con Remotos Rclone (MEGA y GDrive)
    rclone_res = subprocess.run(["rclone", "listremotes"], capture_output=True, text=True)
    remotes = rclone_res.stdout.splitlines()
    if "gdrive:" in remotes and "mega:" in remotes:
        successes.append("Conexiones Rclone: 'gdrive:' y 'mega:' VÁLIDAS Y VINCULADAS ☁️")
    else:
        issues.append(f"Revisar remotos de Rclone. Detectados: {remotes}")

    print("\n--- 🟢 COMPONENTES ACOPLADOS ---")
    for s in successes:
        print(f"  ✅ {s}")

    if issues:
        print("\n--- 🔴 INCONSISTENCIAS DETECTADAS ---")
        for i in issues:
            print(f"  ❌ {i}")
    else:
        print("\n✨ SISTEMA 100% ACOPLADO, COMPACTO Y OPTIMIZADO.")


if __name__ == "__main__":
    audit()
