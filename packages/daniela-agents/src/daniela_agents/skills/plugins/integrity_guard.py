import hashlib, json, os

BASE_DIR = os.path.expanduser("~/daniela-os")
HASH_FILE = os.path.join(BASE_DIR, "integrity_hashes.json")

def get_hash(filepath):
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def calculate_all_hashes():
    hashes = {}
    for root, _, files in os.walk(BASE_DIR):
        for file in files:
            if file.endswith(".py") and file != "integrity_guard.py":
                path = os.path.join(root, file)
                hashes[path] = get_hash(path)
    return hashes

def init_integrity():
    hashes = calculate_all_hashes()
    with open(HASH_FILE, 'w') as f:
        json.dump(hashes, f, indent=4)
    return f"🛡️ [INTEGRITY]: Firma del sistema establecida en {len(hashes)} archivos."

def verify_integrity():
    if not os.path.exists(HASH_FILE):
        return "⚠️ [INTEGRITY]: Base de firmas no encontrada. Ejecuta 'init'."
    
    with open(HASH_FILE, 'r') as f:
        stored = json.load(f)
    
    current = calculate_all_hashes()
    anomalies = []
    
    for path, h in current.items():
        if path not in stored:
            anomalies.append(f"Nuevo archivo detectado: {os.path.basename(path)}")
        elif stored[path] != h:
            anomalies.append(f"Archivo corrompido/modificado: {os.path.basename(path)}")
            
    if anomalies:
        return "🚨 [ALERTA DE SEGURIDAD]: " + " | ".join(anomalies)
    return None

def run(context):
    cmd = context.lower()
    if "init" in cmd: return init_integrity()
    if "check" in cmd:
        res = verify_integrity()
        return res if res else "✅ [INTEGRITY]: Sistema íntegro."
    return "❌ [INTEGRITY]: Usa 'init' para establecer firmas o 'check' para auditar."
