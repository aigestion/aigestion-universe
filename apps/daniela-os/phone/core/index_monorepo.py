import json
import os

REPO_PATH = os.path.expanduser("~/apps/aig")
OUTPUT_INDEX = os.path.expanduser("~/apps/aig/phone/core/local_docs_rag.json")


def index_docs():
    print(f"🗂️ Indexando archivos .md y configs de {REPO_PATH}...")
    documents = []

    for root, _, files in os.walk(REPO_PATH):
        if ".git" in root or "node_modules" in root:
            continue
        for file in files:
            if file.endswith((".md", ".json", ".env.example", ".sh")):
                full_path = os.path.join(root, file)
                try:
                    with open(full_path, encoding="utf-8", errors="ignore") as f:
                        content = f.read()
                        if len(content.strip()) > 20:
                            documents.append(
                                {
                                    "file": file,
                                    "path": full_path,
                                    "content": f"Archivo [{file}]:\n" + content[:600],
                                }
                            )
                except Exception:
                    pass

    with open(OUTPUT_INDEX, "w", encoding="utf-8") as f:
        json.dump(documents, f, indent=2, ensure_ascii=False)

    print(f"✅ Indexación completada: {len(documents)} archivos indexados en {OUTPUT_INDEX}")


if __name__ == "__main__":
    index_docs()
