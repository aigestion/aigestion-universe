import json
import os


def export_digest_for_notebooklm() -> str:
    graph_path = os.path.expanduser("~/daniela-os/graph_memory.json")
    output_digest = os.path.expanduser("~/daniela-os/data/notebooklm_digest.md")
    os.makedirs(os.path.dirname(output_digest), exist_ok=True)

    if not os.path.exists(graph_path):
        return "⚠️ [NOTEBOOK_SYNC]: No existe graph_memory.json."

    with open(graph_path) as f:
        data = json.load(f)

    digest_content = "# 🧠 Daniela OS Knowledge Graph Digest\n\n"
    for rel in data.get("relations", []):
        digest_content += (
            f"- **{rel.get('source')}** --[{rel.get('relation')}]--> **{rel.get('target')}**\n"
        )

    with open(output_digest, "w") as f:
        f.write(digest_content)

    return f"📄 [NOTEBOOK_SYNC]: Digest de {len(data.get('relations', []))} relaciones exportado a data/notebooklm_digest.md"
