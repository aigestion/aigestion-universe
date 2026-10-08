import argparse
import subprocess


def purge_google_drive(remote_name: str):
    print(f"🗑️ Eliminando archivos en Google Drive ('{remote_name}:')...")

    # 1. Eliminar archivos y carpetas en Google Drive
    cmd_purge = ["rclone", "purge", f"{remote_name}:"]
    res = subprocess.run(cmd_purge, capture_output=True, text=True)

    # 2. Vaciar papelera de reciclaje
    print("🧹 Vaciando papelera de Google Drive...")
    cmd_cleanup = ["rclone", "cleanup", f"{remote_name}:"]
    subprocess.run(cmd_cleanup, capture_output=True, text=True)

    if res.returncode == 0:
        print(
            f"✅ Se ha liberado todo el espacio en '{remote_name}:' y vaciado la papelera de reciclaje."
        )
    else:
        print(f"⚠️ Error durante la limpieza: {res.stderr.strip()}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Limpiador de Google Drive")
    parser.add_argument("--remote", default="gdrive", help="Nombre del remoto en rclone")
    args = parser.parse_args()
    purge_google_drive(args.remote)
