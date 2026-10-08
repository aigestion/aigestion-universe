import hashlib
import os
import shutil

STORAGE_BASE = os.path.expanduser("~/storage/shared")
DOWNLOADS_DIR = os.path.join(STORAGE_BASE, "Download")
SCREENSHOTS_DIR = os.path.join(STORAGE_BASE, "Pictures", "Screenshots")
DANIELA_TARGET = os.path.expanduser("~/apps/AIGESTION-MONOREPO")


def get_file_hash(filepath, block_size=65536):
    hasher = hashlib.sha256()
    try:
        with open(filepath, "rb") as f:
            for block in iter(lambda: f.read(block_size), b""):
                hasher.update(block)
        return hasher.hexdigest()
    except Exception:
        return None


def clean_duplicates(directory_path):
    if not os.path.exists(directory_path):
        return 0, 0

    hashes = {}
    duplicates_removed = 0
    space_freed = 0

    for root, _, files in os.walk(directory_path):
        for filename in files:
            filepath = os.path.join(root, filename)
            if os.path.islink(filepath):
                continue

            file_hash = get_file_hash(filepath)
            if file_hash:
                if file_hash in hashes:
                    file_size = os.path.getsize(filepath)
                    os.remove(filepath)
                    duplicates_removed += 1
                    space_freed += file_size
                else:
                    hashes[file_hash] = filepath

    return duplicates_removed, space_freed / (1024 * 1024)


def audit_daniela_folders():
    print("==================================================")
    print("   AUDITORÍA PROFUNDA Y ELIMINACIÓN DUPLICADOS    ")
    print("==================================================")

    # 1. Limpieza de Duplicados
    print("🔍 Buscando y eliminando duplicados en Download...")
    dl_dup, dl_space = clean_duplicates(DOWNLOADS_DIR)
    print(f"✅ Download: {dl_dup} duplicados eliminados ({dl_space:.2f} MB liberados).")

    print("🔍 Buscando y eliminando duplicados en Screenshots...")
    sc_dup, sc_space = clean_duplicates(SCREENSHOTS_DIR)
    print(f"✅ Screenshots: {sc_dup} duplicados eliminados ({sc_space:.2f} MB liberados).")

    print("--------------------------------------------------")
    print("⚙️ Auditando carpetas externas de Daniela OS...")

    # 2. Localizar carpetas de Daniela OS en Storage Interno
    found_daniela_files = []
    for item in os.listdir(STORAGE_BASE):
        item_path = os.path.join(STORAGE_BASE, item)
        if "daniela" in item.lower() or "aigestion" in item.lower():
            found_daniela_files.append((item, item_path))

    if found_daniela_files:
        print(
            f"📁 Se encontraron {len(found_daniela_files)} elementos de Daniela OS en almacenamiento interno:"
        )
        for name, path in found_daniela_files:
            print(f"   - {name} ({'Carpeta' if os.path.isdir(path) else 'Archivo'})")
            # Mover o sincronizar con el monorepo si no existe
            dest_path = os.path.join(DANIELA_TARGET, "external-assets", name)
            os.makedirs(os.path.dirname(dest_path), exist_ok=True)
            if not os.path.exists(dest_path):
                if os.path.isdir(path):
                    shutil.copytree(path, dest_path)
                else:
                    shutil.copy2(path, dest_path)
                print(f"     ➔ Acoplado correctamente a: {dest_path}")
    else:
        print("✅ No se detectaron carpetas huérfanas fuera del monorepo.")

    print("--------------------------------------------------")
    print("✨ Limpieza e integración completadas con éxito.")


if __name__ == "__main__":
    audit_daniela_folders()
