"""
Blueprint for mem0 memory integration (lazy imports - fail open if deps missing)
"""
from flask import Blueprint, jsonify, request

memory_bp = Blueprint("mem0", __name__, url_prefix="/api/mem0")


def _load():
    from core.memory.mem0_integration import (
        add_memory,
        get_memory_manager,
        get_shared_context,
        search_memory,
    )
    return add_memory, search_memory, get_shared_context, get_memory_manager


@memory_bp.route("/add", methods=["POST"])
def add():
    """Add interaction to agent memory."""
    data = request.get_json() or {}
    messages = data.get("messages", [])
    if not messages:
        return jsonify({"error": "messages required"}), 400
    try:
        add_memory, *_ = _load()
    except Exception as e:
        return jsonify({"error": f"mem0 unavailable: {e}"}), 503
    return jsonify(add_memory(
        data.get("agent_id", "default"),
        data.get("user_id", "default"),
        messages, data.get("metadata", {}),
    ))


@memory_bp.route("/search", methods=["POST"])
def search():
    """Search agent memory."""
    data = request.get_json() or {}
    query = data.get("query", "")
    if not query:
        return jsonify({"error": "query required"}), 400
    try:
        _, search_memory, *_ = _load()
    except Exception as e:
        return jsonify({"error": f"mem0 unavailable: {e}"}), 503
    return jsonify({"results": search_memory(
        data.get("agent_id", "default"),
        data.get("user_id", "default"),
        query, data.get("limit", 10),
    )})


@memory_bp.route("/shared-context", methods=["POST"])
def shared_context():
    """Get shared context across agents."""
    data = request.get_json() or {}
    query = data.get("query", "")
    agent_ids = data.get("agent_ids", [])
    if not query or not agent_ids:
        return jsonify({"error": "query and agent_ids required"}), 400
    try:
        _, _, get_shared_context, _ = _load()
    except Exception as e:
        return jsonify({"error": f"mem0 unavailable: {e}"}), 503
    return jsonify(get_shared_context(query, agent_ids, data.get("limit", 5)))


@memory_bp.route("/manager/stats", methods=["GET"])
def manager_stats():
    """Get memory manager stats."""
    try:
        *_, get_memory_manager = _load()
    except Exception as e:
        return jsonify({"error": f"mem0 unavailable: {e}"}), 503
    manager = get_memory_manager()
    return jsonify({"status": "active", "agents": list(manager.agent_memories.keys())})
