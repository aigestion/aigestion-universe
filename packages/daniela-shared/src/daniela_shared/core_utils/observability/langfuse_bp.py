"""
Blueprint for Langfuse observability (lazy imports - fail open if deps missing)
"""
from flask import Blueprint, jsonify, request

langfuse_bp = Blueprint("langfuse", __name__, url_prefix="/api/observability/langfuse")


def _lf():
    from core.observability.langfuse_integration import get_langfuse
    return get_langfuse()


def _get_lf():
    try:
        return _lf(), None
    except Exception as e:
        return None, jsonify({"error": f"langfuse unavailable: {e}"}), 503


@langfuse_bp.route("/trace", methods=["POST"])
def create_trace():
    """Create a trace for a workflow."""
    data = request.get_json() or {}
    name = data.get("name")
    if not name:
        return jsonify({"error": "name required"}), 400
    try:
        langfuse = _lf()
    except Exception as e:
        return jsonify({"error": f"langfuse unavailable: {e}"}), 503
    trace = langfuse.trace(
        name=name,
        input=data.get("input"),
        metadata=data.get("metadata"),
        tags=data.get("tags", []),
        user_id=data.get("user_id"),
        session_id=data.get("session_id"),
    )
    return jsonify({"trace_id": trace.id})


@langfuse_bp.route("/generation", methods=["POST"])
def create_generation():
    """Record an LLM generation."""
    data = request.get_json() or {}
    if not all([data.get("trace_id"), data.get("name"), data.get("model")]):
        return jsonify({"error": "trace_id, name, model required"}), 400
    try:
        langfuse = _lf()
    except Exception as e:
        return jsonify({"error": f"langfuse unavailable: {e}"}), 503
    generation = langfuse.generation(
        trace_id=data.get("trace_id"),
        name=data.get("name"),
        model=data.get("model"),
        input=data.get("input"),
        output=data.get("output"),
        usage=data.get("usage"),
        metadata=data.get("metadata"),
    )
    return jsonify({"generation_id": generation.id})


@langfuse_bp.route("/evaluate", methods=["POST"])
def evaluate():
    """Create evaluation scores for a trace."""
    data = request.get_json() or {}
    trace_id = data.get("trace_id")
    scores = data.get("scores", {})
    comments = data.get("comments", {})
    if not trace_id or not scores:
        return jsonify({"error": "trace_id and scores required"}), 400
    try:
        langfuse = _lf()
    except Exception as e:
        return jsonify({"error": f"langfuse unavailable: {e}"}), 503
    for name, value in scores.items():
        langfuse.create_evaluation(
            trace_id=trace_id, name=name, value=value,
            comment=comments.get(name),
        )
    langfuse.flush()
    return jsonify({"status": "evaluated"})


@langfuse_bp.route("/prompt/<name>", methods=["GET"])
def get_prompt(name):
    """Get a prompt from Langfuse."""
    try:
        langfuse = _lf()
    except Exception as e:
        return jsonify({"error": f"langfuse unavailable: {e}"}), 503
    prompt = langfuse.get_prompt(name)
    if prompt:
        return jsonify({
            "name": prompt.name, "version": prompt.version,
            "prompt": prompt.prompt, "labels": prompt.labels,
            "tags": prompt.tags,
        })
    return jsonify({"error": "prompt not found"}), 404


@langfuse_bp.route("/prompt", methods=["POST"])
def create_prompt():
    """Create or update a prompt."""
    data = request.get_json() or {}
    if not data.get("name") or not data.get("prompt"):
        return jsonify({"error": "name and prompt required"}), 400
    try:
        langfuse = _lf()
    except Exception as e:
        return jsonify({"error": f"langfuse unavailable: {e}"}), 503
    success = langfuse.create_prompt(
        data.get("name"), data.get("prompt"),
        data.get("labels", []), data.get("tags", []),
        data.get("is_active", True),
    )
    return jsonify({"success": success})


@langfuse_bp.route("/dataset/<name>", methods=["POST"])
def create_dataset(name):
    """Create a dataset."""
    data = request.get_json() or {}
    try:
        langfuse = _lf()
    except Exception as e:
        return jsonify({"error": f"langfuse unavailable: {e}"}), 503
    return jsonify({"success": langfuse.create_dataset(name, data.get("description"))})


@langfuse_bp.route("/dataset/<name>/item", methods=["POST"])
def add_dataset_item(name):
    """Add item to dataset."""
    data = request.get_json() or {}
    if not data.get("input"):
        return jsonify({"error": "input required"}), 400
    try:
        langfuse = _lf()
    except Exception as e:
        return jsonify({"error": f"langfuse unavailable: {e}"}), 503
    success = langfuse.add_dataset_item(
        name, data.get("input"), data.get("expected_output"), data.get("metadata"),
    )
    return jsonify({"success": success})
