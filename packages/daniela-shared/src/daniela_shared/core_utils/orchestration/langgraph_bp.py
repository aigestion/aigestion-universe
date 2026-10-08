"""
Blueprint for LangGraph orchestration (lazy imports - fail open if deps missing)
"""
from flask import Blueprint, jsonify, request

langgraph_bp = Blueprint("langgraph", __name__, url_prefix="/api/orchestrator")

# Global orchestrator instance
_orchestrator = None


def _load():
    from core.orchestration.langgraph_orchestrator import (
        LangGraphOrchestrator,
        Task,
        build_android_workflow,
        build_code_review_workflow,
        build_deploy_workflow,
        create_aig_agents,
    )
    return (
        LangGraphOrchestrator, create_aig_agents,
        build_code_review_workflow, build_deploy_workflow,
        build_android_workflow, Task,
    )


def get_orchestrator():
    global _orchestrator
    if _orchestrator is None:
        LangGraphOrchestrator, create_aig_agents, *_ = _load()
        agents = create_aig_agents()
        _orchestrator = LangGraphOrchestrator(agents)
    return _orchestrator

@langgraph_bp.route("/workflow/code-review", methods=["POST"])
def code_review():
    """Run code review workflow."""
    data = request.get_json() or {}
    pr_number = data.get("pr_number")
    repo = data.get("repo", "aig")

    if not pr_number:
        return jsonify({"error": "pr_number required"}), 400

    try:
        _, _, build_code_review_workflow, _, _, _ = _load()
        tasks = build_code_review_workflow(pr_number, repo)
        orchestrator = get_orchestrator()
        result = orchestrator.run(tasks, thread_id=f"code-review-{pr_number}")
        return jsonify({"status": "completed", "result": result})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@langgraph_bp.route("/workflow/deploy", methods=["POST"])
def deploy():
    """Run deployment workflow."""
    data = request.get_json() or {}
    environment = data.get("environment", "staging")
    version = data.get("version", "latest")
    services = data.get("services", ["daniela", "hermes", "agent"])

    try:
        _, _, _, build_deploy_workflow, _, _ = _load()
        tasks = build_deploy_workflow(environment, version, services)
        orchestrator = get_orchestrator()
        result = orchestrator.run(tasks, thread_id=f"deploy-{environment}-{version}")
        return jsonify({"status": "completed", "result": result})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@langgraph_bp.route("/workflow/android", methods=["POST"])
def android():
    """Run Android feature workflow."""
    data = request.get_json() or {}
    feature = data.get("feature")

    if not feature:
        return jsonify({"error": "feature required"}), 400

    try:
        _, _, _, _, build_android_workflow, _ = _load()
        tasks = build_android_workflow(feature)
        orchestrator = get_orchestrator()
        result = orchestrator.run(tasks, thread_id=f"android-{feature}")
        return jsonify({"status": "completed", "result": result})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@langgraph_bp.route("/workflow/custom", methods=["POST"])
def custom_workflow():
    """Run custom workflow from task definitions."""
    data = request.get_json() or {}
    tasks_data = data.get("tasks", [])
    initial_context = data.get("context", {})

    if not tasks_data:
        return jsonify({"error": "tasks required"}), 400

    try:
        _, _, _, _, _, Task = _load()
        tasks = [Task(**t) for t in tasks_data]
        orchestrator = get_orchestrator()
        result = orchestrator.run(tasks, initial_context=initial_context)
        return jsonify({"status": "completed", "result": result})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@langgraph_bp.route("/workflow/stream", methods=["POST"])
def stream_workflow():
    """Stream workflow execution."""
    data = request.get_json() or {}
    tasks_data = data.get("tasks", [])
    initial_context = data.get("context", {})

    if not tasks_data:
        return jsonify({"error": "tasks required"}), 400

    try:
        _, _, _, _, _, Task = _load()
        tasks = [Task(**t) for t in tasks_data]
        orchestrator = get_orchestrator()
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    def generate():
        import json
        for chunk in orchestrator.stream(tasks, initial_context=initial_context):
            yield f"data: {json.dumps(chunk)}\n\n"

    from flask import Response
    return Response(generate(), mimetype="text/event-stream")

@langgraph_bp.route("/status/<workflow_id>", methods=["GET"])
def workflow_status(workflow_id):
    """Get workflow status."""
    try:
        orchestrator = get_orchestrator()
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    try:
        state = orchestrator.get_state(thread_id=workflow_id)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    if state:
        values = getattr(state, "values", state)
        if callable(values):
            values = values()
        try:
            import json
            json.dumps(values)
            safe_values = values
        except Exception:
            safe_values = str(values)
        return jsonify({"status": "found", "state": safe_values})
    return jsonify({"status": "not_found"}), 404
