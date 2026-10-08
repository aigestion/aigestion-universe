"""
System 4: Smart Notification Brain
AI-powered notification hub that summarizes, prioritizes, and learns
"""

import json
import time
from collections import defaultdict
from pathlib import Path

from flask import Flask, jsonify, request

app = Flask(__name__)

NOTIFICATIONS_FILE = Path(__file__).parent / "notifications.json"
LEARNING_FILE = Path(__file__).parent / "learning.json"


def load_notifications():
    if NOTIFICATIONS_FILE.exists():
        with open(NOTIFICATIONS_FILE) as f:
            return json.load(f)
    return []


def save_notifications(data):
    with open(NOTIFICATIONS_FILE, "w") as f:
        json.dump(data, f, indent=2)


def load_learning():
    if LEARNING_FILE.exists():
        with open(LEARNING_FILE) as f:
            return json.load(f)
    return {"ignored": {}, "prioritized": {}, "patterns": {}}


def save_learning(data):
    with open(LEARNING_FILE, "w") as f:
        json.dump(data, f, indent=2)


def classify_urgency(notif):
    """Simple rule-based urgency classifier"""
    text = (notif.get("title", "") + " " + notif.get("body", "")).lower()
    source = notif.get("source", "").lower()

    score = 50  # default

    # High urgency keywords
    if any(w in text for w in ["urgent", "error", "critical", "failed", "crash", "hack", "breach"]):
        score += 30
    if any(w in text for w in ["meeting", "call", "deadline", "asap", "now"]):
        score += 25
    if source in ["slack", "teams", "whatsapp"]:
        score += 10

    # Low urgency
    if any(w in text for w in ["newsletter", "digest", "summary", "weekly"]):
        score -= 20
    if source in ["github", "gitlab"]:
        score -= 5

    learning = load_learning()
    if text in learning.get("ignored", {}):
        score -= 30
    if text in learning.get("prioritized", {}):
        score += 20

    return max(0, min(100, score))


def summarize_batch(notifications):
    """Simple summarization - group by source and count"""
    groups = defaultdict(list)
    for n in notifications:
        groups[n.get("source", "unknown")].append(n)

    summary = []
    for source, items in groups.items():
        if len(items) > 3:
            summary.append(f"{source}: {len(items)} notifications")
        else:
            for item in items:
                summary.append(f"{source}: {item.get('title', 'No title')[:60]}")

    return summary[:10]


@app.route("/")
def index():
    return NOTIFICATION_HTML


@app.route("/api/notifications", methods=["GET"])
def get_notifications():
    notifs = load_notifications()
    # Sort by urgency
    for n in notifs:
        n["urgency"] = classify_urgency(n)
    notifs.sort(key=lambda x: x.get("urgency", 0), reverse=True)
    return jsonify({"notifications": notifs[:50], "total": len(notifs)})


@app.route("/api/notifications", methods=["POST"])
def add_notification():
    data = request.json or {}
    data["timestamp"] = time.time()
    data["read"] = False
    notifs = load_notifications()
    notifs.append(data)
    # Keep last 500
    if len(notifs) > 500:
        notifs = notifs[-500:]
    save_notifications(notifs)
    return jsonify({"ok": True, "urgency": classify_urgency(data)})


@app.route("/api/notifications/summary")
def get_summary():
    notifs = load_notifications()
    unread = [n for n in notifs if not n.get("read")]
    summary = summarize_batch(unread)
    return jsonify({"summary": summary, "unread_count": len(unread)})


@app.route("/api/notifications/<int:id>/action", methods=["POST"])
def notification_action(id):
    data = request.json or {}
    action = data.get("action", "read")
    notifs = load_notifications()
    if id < len(notifs):
        if action == "ignore":
            learning = load_learning()
            key = notifs[id].get("title", "")[:50]
            learning["ignored"][key] = learning["ignored"].get(key, 0) + 1
            save_learning(learning)
        elif action == "prioritize":
            learning = load_learning()
            key = notifs[id].get("title", "")[:50]
            learning["prioritized"][key] = learning["prioritized"].get(key, 0) + 1
            save_learning(learning)
        notifs[id]["read"] = True
        save_notifications(notifs)
    return jsonify({"ok": True})


NOTIFICATION_HTML = r"""
<!DOCTYPE html>
<html><head><meta charset="UTF-8"><title>Notification Brain</title>
<style>
* { margin:0; padding:0; box-sizing:border-box; }
body { background:#030814; color:#e2e8f0; font-family:'Rajdhani',sans-serif; padding:20px; }
h1 { font-family:'Orbitron',monospace; color:#00f0ff; font-size:20px; letter-spacing:3px; margin-bottom:20px; }
.summary { background:rgba(0,240,255,0.05); border:1px solid rgba(0,240,255,0.2); border-radius:12px; padding:16px; margin-bottom:20px; }
.summary h2 { font-size:14px; color:#00f0ff; margin-bottom:8px; }
.summary-item { font-size:12px; color:#94a3b8; padding:4px 0; }
.notif { background:rgba(3,8,20,0.8); border:1px solid rgba(0,240,255,0.1); border-radius:10px; padding:12px; margin-bottom:8px; transition:all 0.2s; }
.notif:hover { border-color:#00f0ff; box-shadow:0 0 15px rgba(0,240,255,0.1); }
.notif-header { display:flex; justify-content:space-between; align-items:center; margin-bottom:4px; }
.notif-source { font-family:'Share Tech Mono',monospace; font-size:10px; color:#00f0ff; text-transform:uppercase; }
.notif-time { font-size:10px; color:#64748b; }
.notif-title { font-size:13px; font-weight:600; }
.notif-body { font-size:11px; color:#94a3b8; margin-top:4px; }
.notif-actions { display:flex; gap:6px; margin-top:8px; }
.notif-btn { background:none; border:1px solid; border-radius:4px; padding:3px 8px; font-size:9px; cursor:pointer; font-family:inherit; }
.notif-btn.ignore { border-color:#f59e0b; color:#f59e0b; }
.notif-btn.prioritize { border-color:#22c55e; color:#22c55e; }
.urgency { display:inline-block; width:8px; height:8px; border-radius:50%; margin-right:6px; }
.urgency.high { background:#ef4444; }
.urgency.medium { background:#f59e0b; }
.urgency.low { background:#22c55e; }
.stats { position:fixed; bottom:20px; right:20px; font-family:'Share Tech Mono',monospace; font-size:10px; color:#64748b; }
</style></head><body>
<h1>🧠 NOTIFICATION BRAIN</h1>
<div class="summary" id="summary"><h2>Loading...</h2></div>
<div id="list"></div>
<div class="stats" id="stats"></div>
<script>
async function load() {
  const s = await (await fetch('/api/notifications/summary')).json();
  document.getElementById('summary').innerHTML = '<h2>Summary</h2>' +
    s.summary.map(x => '<div class="summary-item">' + x + '</div>').join('');

  const r = await (await fetch('/api/notifications')).json();
  document.getElementById('list').innerHTML = r.notifications.map((n,i) => {
    const urg = n.urgency > 70 ? 'high' : n.urgency > 40 ? 'medium' : 'low';
    const time = new Date(n.timestamp*1000).toLocaleTimeString();
    return '<div class="notif"><div class="notif-header">' +
      '<span><span class="urgency ' + urg + '"></span><span class="notif-source">' + (n.source||'system') + '</span></span>' +
      '<span class="notif-time">' + time + '</span></div>' +
      '<div class="notif-title">' + (n.title||'No title') + '</div>' +
      '<div class="notif-body">' + (n.body||'') + '</div>' +
      '<div class="notif-actions">' +
      '<button class="notif-btn ignore" onclick="act(' + i + ',\'ignore\')">Ignore</button>' +
      '<button class="notif-btn prioritize" onclick="act(' + i + ',\'prioritize\')">Prioritize</button>' +
      '</div></div>';
  }).join('');
  document.getElementById('stats').textContent = r.total + ' total | ' + r.notifications.length + ' shown';
}
async function act(id, action) {
  await fetch('/api/notifications/' + id + '/action', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({action})});
  load();
}
load(); setInterval(load, 10000);
</script></body></html>
"""

if __name__ == "__main__":
    print("[System 4] Notification Brain starting on port 5013...")
    app.run(host="0.0.0.0", port=5013, debug=False)
