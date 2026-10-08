"""
Flow Builder - Visual Workflow Constructor
Drag-and-drop automation workflows
"""

import json
import time
import uuid
from pathlib import Path

from flask import Flask, jsonify, request, send_from_directory

app = Flask(__name__)
DATA_DIR = Path(__file__).parent / "data"
DATA_DIR.mkdir(exist_ok=True)


def load_json(path, default=None):
    if path.exists():
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    return default or {}


def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


NODE_TYPES = [
    {
        "type": "trigger_time",
        "name": "Time Trigger",
        "category": "triggers",
        "icon": "128336",
        "color": "#22c55e",
        "inputs": [],
        "outputs": ["out"],
        "config": {"cron": "0 9 * * *", "label": "Every day 9am"},
    },
    {
        "type": "trigger_file",
        "name": "File Watcher",
        "category": "triggers",
        "icon": "128193",
        "color": "#22c55e",
        "inputs": [],
        "outputs": ["out"],
        "config": {"path": "", "event": "modified"},
    },
    {
        "type": "trigger_manual",
        "name": "Manual Start",
        "category": "triggers",
        "icon": "128154",
        "color": "#22c55e",
        "inputs": [],
        "outputs": ["out"],
        "config": {"label": "Click to run"},
    },
    {
        "type": "trigger_webhook",
        "name": "Webhook",
        "category": "triggers",
        "icon": "127760",
        "color": "#22c55e",
        "inputs": [],
        "outputs": ["out"],
        "config": {"path": "/hook/abc123"},
    },
    {
        "type": "action_script",
        "name": "Run Script",
        "category": "actions",
        "icon": "128187",
        "color": "#00f0ff",
        "inputs": ["in"],
        "outputs": ["out"],
        "config": {"script": "", "lang": "python"},
    },
    {
        "type": "action_notify",
        "name": "Send Notification",
        "category": "actions",
        "icon": "128276",
        "color": "#00f0ff",
        "inputs": ["in"],
        "outputs": ["out"],
        "config": {"title": "", "message": "", "type": "info"},
    },
    {
        "type": "action_file",
        "name": "File Operation",
        "category": "actions",
        "icon": "128194",
        "color": "#00f0ff",
        "inputs": ["in"],
        "outputs": ["out"],
        "config": {"operation": "copy", "source": "", "dest": ""},
    },
    {
        "type": "action_http",
        "name": "HTTP Request",
        "category": "actions",
        "icon": "127760",
        "color": "#00f0ff",
        "inputs": ["in"],
        "outputs": ["out"],
        "config": {"method": "GET", "url": "", "headers": {}},
    },
    {
        "type": "action_email",
        "name": "Send Email",
        "category": "actions",
        "icon": "128231",
        "color": "#00f0ff",
        "inputs": ["in"],
        "outputs": ["out"],
        "config": {"to": "", "subject": "", "body": ""},
    },
    {
        "type": "action_shell",
        "name": "Shell Command",
        "category": "actions",
        "icon": "128424",
        "color": "#00f0ff",
        "inputs": ["in"],
        "outputs": ["out"],
        "config": {"command": ""},
    },
    {
        "type": "condition",
        "name": "If / Else",
        "category": "logic",
        "icon": "128256",
        "color": "#f59e0b",
        "inputs": ["in"],
        "outputs": ["true", "false"],
        "config": {"variable": "", "operator": "equals", "value": ""},
    },
    {
        "type": "condition_compare",
        "name": "Compare",
        "category": "logic",
        "icon": "128200",
        "color": "#f59e0b",
        "inputs": ["in"],
        "outputs": ["true", "false"],
        "config": {"left": "", "op": "==", "right": ""},
    },
    {
        "type": "delay",
        "name": "Delay",
        "category": "logic",
        "icon": "9203",
        "color": "#f59e0b",
        "inputs": ["in"],
        "outputs": ["out"],
        "config": {"seconds": 5},
    },
    {
        "type": "loop",
        "name": "Loop",
        "category": "logic",
        "icon": "128257",
        "color": "#f59e0b",
        "inputs": ["in"],
        "outputs": ["out", "done"],
        "config": {"count": 10},
    },
    {
        "type": "transform",
        "name": "Transform Data",
        "category": "data",
        "icon": "128260",
        "color": "#8b5cf6",
        "inputs": ["in"],
        "outputs": ["out"],
        "config": {"expression": ""},
    },
    {
        "type": "filter",
        "name": "Filter",
        "category": "data",
        "icon": "128267",
        "color": "#8b5cf6",
        "inputs": ["in"],
        "outputs": ["out", "filtered"],
        "config": {"condition": ""},
    },
    {
        "type": "aggregate",
        "name": "Aggregate",
        "category": "data",
        "icon": "128202",
        "color": "#8b5cf6",
        "inputs": ["in"],
        "outputs": ["out"],
        "config": {"method": "count"},
    },
    {
        "type": "output",
        "name": "Output / End",
        "category": "output",
        "icon": "128259",
        "color": "#ff0055",
        "inputs": ["in"],
        "outputs": [],
        "config": {"label": "Done"},
    },
]


@app.route("/")
def index():
    return send_from_directory(str(Path(__file__).parent), "index.html")


@app.route("/api/nodes/types")
def node_types():
    return jsonify({"types": NODE_TYPES})


@app.route("/api/workflows/list")
def list_workflows():
    wf_dir = DATA_DIR / "workflows"
    wf_dir.mkdir(exist_ok=True)
    workflows = []
    for f in wf_dir.glob("*.json"):
        data = load_json(f)
        workflows.append(
            {
                "id": f.stem,
                "name": data.get("name", f.stem),
                "nodes": len(data.get("nodes", [])),
                "created": data.get("created"),
                "updated": data.get("updated"),
            }
        )
    return jsonify({"workflows": workflows})


@app.route("/api/workflows/get/<wf_id>")
def get_workflow(wf_id):
    wf_path = DATA_DIR / "workflows" / f"{wf_id}.json"
    if wf_path.exists():
        return jsonify(load_json(wf_path))
    return jsonify({"error": "Not found"}), 404


@app.route("/api/workflows/save", methods=["POST"])
def save_workflow():
    data = request.json or {}
    wf_id = data.get("id", str(uuid.uuid4())[:8])
    data["id"] = wf_id
    data["updated"] = time.time()
    if "created" not in data:
        data["created"] = time.time()
    wf_dir = DATA_DIR / "workflows"
    wf_dir.mkdir(exist_ok=True)
    save_json(wf_dir / f"{wf_id}.json", data)
    return jsonify({"ok": True, "id": wf_id})


@app.route("/api/workflows/delete", methods=["POST"])
def delete_workflow():
    data = request.json or {}
    wf_path = DATA_DIR / "workflows" / f"{data.get('id', '')}.json"
    if wf_path.exists():
        wf_path.unlink()
    return jsonify({"ok": True})


@app.route("/api/workflows/execute", methods=["POST"])
def execute_workflow():
    data = request.json or {}
    nodes = data.get("nodes", [])
    connections = data.get("connections", [])
    logs = []
    node_map = {n["id"]: n for n in nodes}
    execution_order = topological_sort(nodes, connections)
    for node_id in execution_order:
        node = node_map.get(node_id, {})
        ntype = node.get("type", "")
        logs.append({"node": node_id, "type": ntype, "status": "executed", "time": time.time()})
    return jsonify({"ok": True, "logs": logs, "executed": len(execution_order)})


def topological_sort(nodes, connections):
    adj = {n["id"]: [] for n in nodes}
    indeg = {n["id"]: 0 for n in nodes}
    for c in connections:
        if c.get("from") in adj:
            adj[c["from"]].append(c.get("to"))
            indeg[c.get("to", "")] = indeg.get(c.get("to", ""), 0) + 1
    queue = [nid for nid, d in indeg.items() if d == 0]
    result = []
    while queue:
        nid = queue.pop(0)
        result.append(nid)
        for neighbor in adj.get(nid, []):
            indeg[neighbor] -= 1
            if indeg[neighbor] == 0:
                queue.append(neighbor)
    return result


if __name__ == "__main__":
    print("[Flow Builder] Starting on port 9090...")
    app.run(host="0.0.0.0", port=9090, debug=False)
