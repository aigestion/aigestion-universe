import os
import shutil
import time

STORAGE_BASE = os.path.expanduser("~/storage/shared")
DOWNLOADS_DIR = os.path.join(STORAGE_BASE, "Download")
SCREENSHOTS_DIR = os.path.join(STORAGE_BASE, "Pictures", "Screenshots")

# Clasificación para descargas
CATEGORIES = {
    "Instaladores_APK": [".apk", ".xapk", ".idsig"],
    "Documentos": [".pdf", ".docx", ".xlsx", ".txt", ".pptx", ".csv", ".json"],
    "Media": [".png", ".jpg", ".jpeg", ".mp4", ".mp3", ".webp", ".gif"],
    "Compressed": [".zip", ".tar", ".gz", ".7z", ".rar"],
}


def get_dir_size_mb(path):
    total = 0
    if not os.path.exists(path):
        return 0
    for root, _dirs, files in os.walk(path):
        for f in files:
            fp = os.path.join(root, f)
            if not os.path.islink(fp):
                total += os.path.getsize(fp)
    return total / (1024 * 1024)


def audit_and_optimize():
    print("==================================================")
    print("   AUDITORÍA Y OPTIMIZACIÓN DE ALMACENAMIENTO    ")
    print("==================================================")

    dl_size = get_dir_size_mb(DOWNLOADS_DIR)
    sc_size = get_dir_size_mb(SCREENSHOTS_DIR)

    print(f"📊 Espacio ocupado en Download: {dl_size:.2f} MB")
    print(f"📊 Espacio ocupado en Screenshots: {sc_size:.2f} MB")
    print("--------------------------------------------------")

    # 1. Optimizar Descargas
    if os.path.exists(DOWNLOADS_DIR):
        print("🧹 Clasificando carpeta Downloads...")
        files = [
            f for f in os.listdir(DOWNLOADS_DIR) if os.path.isfile(os.path.join(DOWNLOADS_DIR, f))
        ]
        moved_count = 0

        for file in files:
            ext = os.path.splitext(file)[1].lower()
            file_path = os.path.join(DOWNLOADS_DIR, file)

            for category, exts in CATEGORIES.items():
                if ext in exts:
                    target_dir = os.path.join(DOWNLOADS_DIR, category)
                    os.makedirs(target_dir, exist_ok=True)
                    shutil.move(file_path, os.path.join(target_dir, file))
                    moved_count += 1
                    break
        print(f"✅ Descargas: {moved_count} archivos organizados en subcarpetas.")

    # 2. Archivo de Screenshots antiguas
    if os.path.exists(SCREENSHOTS_DIR):
        print("🖼️ Auditando Screenshots...")
        archive_dir = os.path.join(SCREENSHOTS_DIR, "Archive_Screenshots")
        now = time.time()
        days_30 = 30 * 86400
        sc_files = [
            f
            for f in os.listdir(SCREENSHOTS_DIR)
            if os.path.isfile(os.path.join(SCREENSHOTS_DIR, f))
        ]
        archived_count = 0

        for sc in sc_files:
            sc_path = os.path.join(SCREENSHOTS_DIR, sc)
            if (now - os.path.getmtime(sc_path)) > days_30:
                os.makedirs(archive_dir, exist_ok=True)
                shutil.move(sc_path, os.path.join(archive_dir, sc))
                archived_count += 1

        print(f"✅ Capturas: {archived_count} capturas antiguas movidas a 'Archive_Screenshots'.")

    print("--------------------------------------------------")
    print("✨ Auditoría completada con éxito.")


if __name__ == "__main__":
    audit_and_optimize()
