"""
Flask API server for aig Auto Engine.
Port 9860.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask, jsonify, request

from auto_engine.actions import ActionLibrary
from auto_engine.integrations import IntegrationManager
from auto_engine.scheduler import TaskScheduler
from auto_engine.triggers import TriggerManager
from auto_engine.workflow_engine import WorkflowEngine

app = Flask(__name__)

engine = WorkflowEngine(db_path="auto_workflow_state.db")
scheduler = TaskScheduler()
triggers = TriggerManager()
actions = ActionLibrary()
integrations = IntegrationManager()

for action_type in actions.handlers:
    engine.register_action(action_type, actions.handlers[action_type])
    scheduler.register_action(action_type, actions.handlers[action_type])
for action_type in actions.handlers:
    triggers.register_action(action_type, actions.handlers[action_type])


@app.route("/api/auto/status", methods=["GET"])
def status():
    return jsonify({
        "status": "ok",
        "service": "auto_engine",
        "version": "1.0.0",
        "workflows": len(engine.workflows),
        "scheduled_jobs": len(scheduler.jobs),
        "triggers": len(triggers.triggers),
        "actions": len(actions.list_actions()),
        "integrations": len(integrations.configs),
    })


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "service": "auto_engine"})


@app.route("/api/auto/workflows", methods=["GET", "POST"])
def workflows_endpoint():
    if request.method == "GET":
        return jsonify(engine.list_workflows())
    data = request.get_json(force=True)
    name = data.get("name", "Untitled Workflow")
    tasks = data.get("tasks", [])
    version = data.get("version", "1.0.0")
    template = data.get("template")
    try:
        if template:
            wf = engine.create_from_template(template, name=name)
        else:
            wf = engine.create_workflow(name, tasks, version)
        return jsonify(wf.to_dict()), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@app.route("/api/auto/workflows/<workflow_id>", methods=["GET", "DELETE"])
def workflow_detail(workflow_id):
    if request.method == "GET":
        wf = engine.get_workflow(workflow_id)
        if wf:
            return jsonify(wf.to_dict())
        return jsonify({"error": "Not found"}), 404
    engine.delete_workflow(workflow_id)
    return jsonify({"deleted": workflow_id})


@app.route("/api/auto/workflows/<workflow_id>/execute", methods=["POST"])
def execute_workflow(workflow_id):
    try:
        result = engine.execute_workflow(workflow_id)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@app.route("/api/auto/scheduler", methods=["GET", "POST"])
def scheduler_endpoint():
    if request.method == "GET":
        return jsonify(scheduler.list_jobs())
    data = request.get_json(force=True)
    job = scheduler.add_job(
        name=data.get("name", "Untitled Job"),
        action_type=data.get("action_type", "shell_command"),
        params=data.get("params"),
        recurrence=data.get("recurrence", "once"),
        cron_expr=data.get("cron_expr"),
        interval_seconds=data.get("interval_seconds"),
        priority=data.get("priority", 0),
        depends_on=data.get("depends_on"),
        rate_limit=data.get("rate_limit"),
        calendar_aware=data.get("calendar_aware", False),
        tags=data.get("tags"),
    )
    return jsonify(job.to_dict()), 201


@app.route("/api/auto/scheduler/<job_id>", methods=["DELETE", "PUT"])
def scheduler_job_detail(job_id):
    if request.method == "DELETE":
        removed = scheduler.remove_job(job_id)
        if removed:
            return jsonify({"deleted": job_id})
        return jsonify({"error": "Not found"}), 404
    data = request.get_json(force=True)
    action = data.get("action")
    if action == "pause":
        scheduler.pause_job(job_id)
    elif action == "resume":
        scheduler.resume_job(job_id)
    elif action == "execute":
        result = scheduler.execute_job(job_id)
        return jsonify(result)
    return jsonify({"status": "ok"})


@app.route("/api/auto/scheduler/execute-ready", methods=["POST"])
def execute_ready_jobs():
    results = scheduler.execute_ready_jobs()
    return jsonify(results)


@app.route("/api/auto/triggers", methods=["GET", "POST"])
def triggers_endpoint():
    if request.method == "GET":
        return jsonify(triggers.list_triggers())
    data = request.get_json(force=True)
    trigger = triggers.add_trigger(
        name=data.get("name", "Untitled Trigger"),
        trigger_type=data.get("trigger_type", "manual"),
        config=data.get("config"),
        action_type=data.get("action_type"),
        action_params=data.get("action_params"),
        debounce_ms=data.get("debounce_ms", 0),
        throttle_ms=data.get("throttle_ms", 0),
    )
    return jsonify(trigger.to_dict()), 201


@app.route("/api/auto/triggers/<trigger_id>", methods=["DELETE", "PUT"])
def trigger_detail(trigger_id):
    if request.method == "DELETE":
        removed = triggers.remove_trigger(trigger_id)
        if removed:
            return jsonify({"deleted": trigger_id})
        return jsonify({"error": "Not found"}), 404
    data = request.get_json(force=True)
    action = data.get("action")
    if action == "pause":
        triggers.pause_trigger(trigger_id)
    elif action == "resume":
        triggers.resume_trigger(trigger_id)
    elif action == "fire":
        result = triggers.fire_trigger(trigger_id, data.get("payload"))
        return jsonify(result)
    return jsonify({"status": "ok"})


@app.route("/api/auto/actions", methods=["GET"])
def list_actions():
    return jsonify(actions.list_actions())


@app.route("/api/auto/actions/execute", methods=["POST"])
def execute_action():
    data = request.get_json(force=True)
    action_type = data.get("action_type", "")
    params = data.get("params", {})
    result = actions.execute(action_type, params)
    return jsonify(result)


@app.route("/api/auto/integrations", methods=["GET", "POST"])
def integrations_endpoint():
    if request.method == "GET":
        return jsonify(integrations.list_integrations())
    data = request.get_json(force=True)
    config = integrations.configure(
        name=data.get("name", ""),
        integration_type=data.get("integration_type", ""),
        **{k: v for k, v in data.items() if k not in ("name", "integration_type")},
    )
    return jsonify(config.to_dict()), 201


@app.route("/api/auto/integrations/<name>", methods=["DELETE"])
def integration_detail(name):
    integrations.remove(name)
    return jsonify({"deleted": name})


@app.route("/api/auto/history", methods=["GET"])
def history():
    wf_id = request.args.get("workflow_id")
    limit = request.args.get("limit", 100, type=int)
    executions = engine.persistence.get_executions(wf_id)
    trigger_log = triggers.get_fire_log(limit=limit)
    action_log = actions.get_log(limit=limit)
    scheduler_history = scheduler.get_history(limit=limit)
    return jsonify({
        "workflows": executions[-limit:],
        "triggers": trigger_log,
        "actions": action_log,
        "scheduler": scheduler_history,
    })


if __name__ == "__main__":
    import os
    app.run(host="0.0.0.0", port=int(os.getenv("SERVICE_PORT", "9860")), debug=False)
