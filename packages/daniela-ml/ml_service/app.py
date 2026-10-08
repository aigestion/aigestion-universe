"""
aig ML sidecar - Heavy ML dependencies isolated from base services.
Hosts: LlamaIndex RAG, mem0 memory, LangGraph orchestration, Langfuse tracing.
Port: 9810
"""
import os
import sys

sys.path.insert(0, "/app")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + "/..")

from flask import Flask, jsonify

app = Flask(__name__)

failed: list[dict[str, str]] = []


def _safe_register(name, fn):
    try:
        fn()
    except Exception as e:
        failed.append({"phase": name, "error": str(e)[:200]})
        print(f"[ML] Phase '{name}' FAILED: {e}")


def register_all():
    from core.knowledge.rag_bp import rag_bp
    from core.memory.mem0_bp import memory_bp as mem0_bp
    from core.observability.langfuse_bp import langfuse_bp
    from core.orchestration.langgraph_bp import langgraph_bp

    for name, bp in [
        ("rag", rag_bp),
        ("mem0", mem0_bp),
        ("langgraph", langgraph_bp),
        ("langfuse", langfuse_bp),
    ]:
        _safe_register(name, lambda b=bp: app.register_blueprint(b))


register_all()


@app.route("/health")
def health():
    return jsonify({"status": "ok", "service": "aig-ml", "failed": failed})


@app.route("/api/status")
def status():
    return jsonify({
        "name": "aig ML Sidecar",
        "version": "1.0.0",
        "failed_phases": failed,
        "routes": len([r for r in app.url_map.iter_rules() if r.endpoint != "static"]),
        "status": "alive",
    })


if __name__ == "__main__":
    port = int(os.getenv("PORT", "9810"))
    print(f"[ML] Starting aig ML sidecar on port {port}...")
    app.run(host="0.0.0.0", port=port, debug=False)
