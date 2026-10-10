import sys
from pathlib import Path

from supabase import create_client

sys.path.insert(0, str(Path(__file__).resolve().parent))
from sentence_transformers import SentenceTransformer
from supabase_env import get_supabase_creds  # noqa: E402

env_path = Path.home() / ".env"
env_vars = {}
if env_path.exists():
    with open(env_path, encoding="utf-8", errors="ignore") as f:
        for line in f:
            if "=" in line and not line.startswith("#"):
                k, v = line.strip().split("=", 1)
                env_vars[k.strip()] = v.strip().strip('"').strip("'")

url, key = get_supabase_creds()
supabase = create_client(url, key)

# Probar lectura de obsidian_embeddings
try:
    res = supabase.table('obsidian_embeddings').select('id', count='exact').execute()
    print(f"📊 Total de registros vectoriales en la nube: {res.count}")

    # Prueba de búsqueda semántica
    query = "prioridades y configuracion de daniela os"
    print(f"\n🔎 Realizando búsqueda semántica de prueba: '{query}'...")
    model = SentenceTransformer('all-MiniLM-L6-v2')
    query_vector = model.encode(query).tolist()

    rpc_res = supabase.rpc('match_obsidian_notes', {
        'query_embedding': query_vector,
        'match_threshold': 0.1,
        'match_count': 3
    }).execute()

    print("\n🟢 NOTAS RECUPERADAS CON ÉXITO:")
    for note in rpc_res.data:
        print(f"  📄 Nota: {note['file_name']} (Similitud: {round(note['similarity'] * 100, 2)}%)")

except Exception:
    print("\n⚠️ La tabla 'obsidian_embeddings' o la función 'match_obsidian_notes' no existe todavía.")
    print("👉 Pega el contenido de 'C:\\Users\\Alejandro\\aig\\init_rag.sql' en el SQL Editor de tu panel de Supabase y presiona Run.")
