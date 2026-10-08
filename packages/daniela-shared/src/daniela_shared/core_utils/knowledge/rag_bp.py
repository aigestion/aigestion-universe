"""
Blueprint for LlamaIndex RAG integration (lazy imports - fail open if deps missing).

Multi-notebook: each NotebookLM notebook lives in its own Qdrant collection
(`nb_<slug>`). Pass {"collection": "..."} or use /api/rag/context which fans
a question out across notebooks and returns one assembled context block -
that is the endpoint Daniela calls to "get context from the notebooks".
"""
from flask import Blueprint, jsonify, request

rag_bp = Blueprint("rag", __name__, url_prefix="/api/rag")


def _load():
    from core.knowledge.llamaindex_rag import (
        DEFAULT_COLLECTION,
        NOTEBOOK_PREFIX,
        add_knowledge,
        assemble_context,
        get_rag,
        ingest_memory_nodes,
        list_collections,
        notebook_collection,
        query_knowledge,
        search_knowledge,
    )
    return (query_knowledge, search_knowledge, add_knowledge,
            ingest_memory_nodes, get_rag, list_collections,
            notebook_collection, assemble_context, NOTEBOOK_PREFIX,
            DEFAULT_COLLECTION)


@rag_bp.route("/query", methods=["POST"])
def query():
    """Query the RAG system (optional: {"collection": "..."})."""
    data = request.get_json() or {}
    question = data.get("question", "")
    if not question:
        return jsonify({"error": "question required"}), 400
    try:
        query_knowledge, *_ = _load()
    except Exception as e:
        return jsonify({"error": f"RAG unavailable: {e}"}), 503
    return jsonify(query_knowledge(question, collection=data.get("collection")))


@rag_bp.route("/search", methods=["POST"])
def search():
    """Search knowledge without synthesis (optional collection)."""
    data = request.get_json() or {}
    question = data.get("question", "")
    top_k = data.get("top_k", 10)
    if not question:
        return jsonify({"error": "question required"}), 400
    try:
        _, search_knowledge, *_ = _load()
    except Exception as e:
        return jsonify({"error": f"RAG unavailable: {e}"}), 503
    return jsonify({"results": search_knowledge(question, top_k, collection=data.get("collection"))})


@rag_bp.route("/add", methods=["POST"])
def add():
    """Add knowledge to the vault (optional collection)."""
    data = request.get_json() or {}
    text = data.get("text", "")
    metadata = data.get("metadata", {})
    if not text:
        return jsonify({"error": "text required"}), 400
    try:
        _, _, add_knowledge, *_ = _load()
    except Exception as e:
        return jsonify({"error": f"RAG unavailable: {e}"}), 503
    return jsonify({
        "doc_id": add_knowledge(text, metadata, collection=data.get("collection")),
        "status": "added",
    })


@rag_bp.route("/ingest-memory", methods=["POST"])
def ingest_memory():
    """Ingest memory nodes."""
    data = request.get_json() or {}
    nodes = data.get("nodes", [])
    namespace = data.get("namespace", "memory")
    if not nodes:
        return jsonify({"error": "nodes required"}), 400
    try:
        _, _, _, ingest_memory_nodes, *_ = _load()
    except Exception as e:
        return jsonify({"error": f"RAG unavailable: {e}"}), 503
    return jsonify({"ingested": ingest_memory_nodes(nodes, namespace)})


@rag_bp.route("/stats", methods=["GET"])
def stats():
    """Get RAG stats (optional ?collection=...)."""
    try:
        from core.knowledge.llamaindex_rag import get_rag
        return jsonify(get_rag(request.args.get("collection")).get_stats())
    except Exception as e:
        return jsonify({"error": f"RAG unavailable: {e}"}), 503


@rag_bp.route("/collections", methods=["GET"])
def collections():
    """List Qdrant collections (= notebooks + default vault)."""
    try:
        _, _, _, _, _, list_collections, *_ = _load()
    except Exception as e:
        return jsonify({"error": f"RAG unavailable: {e}"}), 503
    return jsonify({"collections": list_collections()})


@rag_bp.route("/context", methods=["POST"])
def context():
    """Assemble context from one, several, or ALL notebooks.

    Body: {"question": "...", "notebooks": ["Mi cuaderno", ...], "top_k": 5}
    - notebooks omitted/empty -> every nb_* collection + default vault.
    - Returns {"context": "<cited blocks>", "sources": [...]} ready to
      paste into an LLM prompt. This is Daniela's "get context" endpoint.
    """
    data = request.get_json() or {}
    question = data.get("question", "")
    if not question:
        return jsonify({"error": "question required"}), 400
    top_k = int(data.get("top_k", 5))
    try:
        (_, _, _, _, _, list_collections,
         notebook_collection, assemble_context, NOTEBOOK_PREFIX,
         DEFAULT_COLLECTION) = _load()
    except Exception as e:
        return jsonify({"error": f"RAG unavailable: {e}"}), 503

    notebooks = data.get("notebooks") or []
    if notebooks:
        collections = [notebook_collection(n) for n in notebooks]
    else:
        try:
            all_cols = list_collections()
        except Exception:
            all_cols = []
        collections = [c for c in all_cols if c.startswith(NOTEBOOK_PREFIX)]
        if DEFAULT_COLLECTION not in collections:
            collections.append(DEFAULT_COLLECTION)

    try:
        result = assemble_context(question, collections, top_k)
    except Exception as e:
        return jsonify({"error": f"context failed: {e}"}), 500
    return jsonify(result)
