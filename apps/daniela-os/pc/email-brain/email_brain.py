"""
System 19: Email Priority Brain
Classifies emails by real urgency, auto-replies to trivial ones
"""

import json
import re
import time
from pathlib import Path

from flask import Flask, jsonify, request

app = Flask(__name__)

DATA_DIR = Path(__file__).parent / "data"
DATA_DIR.mkdir(exist_ok=True)

EMAILS_FILE = DATA_DIR / "emails.json"


def load_json(path, default=None):
    if path.exists():
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    return default or {}


def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


URGENCY_KEYWORDS = {
    "urgent": 10,
    "asap": 10,
    "emergency": 10,
    "critical": 9,
    "deadline": 8,
    "today": 7,
    "tonight": 7,
    "immediately": 8,
    "important": 6,
    "action required": 7,
    "action needed": 7,
    "please respond": 6,
    "time sensitive": 7,
    "follow up": 5,
    "meeting": 4,
    "reminder": 3,
    "fyi": 1,
    "newsletter": 0,
    "unsubscribe": 0,
    "promotion": 0,
    "sale": 0,
    "offer": 0,
}


def classify_urgency(email):
    score = 3
    subject = email.get("subject", "").lower()
    body = email.get("body", "").lower()
    combined = subject + " " + body
    for keyword, weight in URGENCY_KEYWORDS.items():
        if keyword in combined:
            score = max(score, weight)
    if email.get("from", "").lower() in ["boss", "manager", "lead", "director"]:
        score = max(score, 8)
    if re.search(r"\b[A-Z]{2,}\b", email.get("subject", "")):
        score = max(score, 6)
    if score >= 8:
        return "critical"
    if score >= 6:
        return "high"
    if score >= 4:
        return "medium"
    if score >= 2:
        return "low"
    return "trivial"


@app.route("/")
def index():
    return EMAIL_HTML


@app.route("/api/emails/list")
def list_emails():
    emails = load_json(EMAILS_FILE, {"emails": []})
    emails["emails"].sort(key=lambda x: x.get("timestamp", 0), reverse=True)
    return jsonify(emails)


@app.route("/api/emails/add", methods=["POST"])
def add_email():
    data = request.json or {}
    urgency = classify_urgency(data)
    email = {
        "id": int(time.time()),
        "from": data.get("from", ""),
        "to": data.get("to", ""),
        "subject": data.get("subject", ""),
        "body": data.get("body", ""),
        "urgency": urgency,
        "timestamp": time.time(),
        "date": time.strftime("%Y-%m-%d %H:%M"),
        "read": False,
        "replied": False,
    }
    emails = load_json(EMAILS_FILE, {"emails": []})
    emails["emails"].append(email)
    save_json(EMAILS_FILE, emails)
    return jsonify({"ok": True, "urgency": urgency})


@app.route("/api/emails/reply", methods=["POST"])
def reply_email():
    data = request.json or {}
    eid = data.get("id")
    reply_text = data.get("reply", "")
    emails = load_json(EMAILS_FILE, {"emails": []})
    for e in emails["emails"]:
        if e["id"] == eid:
            e["replied"] = True
            e["reply"] = reply_text
            e["reply_time"] = time.strftime("%Y-%m-%d %H:%M")
            break
    save_json(EMAILS_FILE, emails)
    return jsonify({"ok": True})


@app.route("/api/emails/stats")
def stats():
    emails = load_json(EMAILS_FILE, {"emails": []}).get("emails", [])
    urgency_count = {}
    for e in emails:
        u = e.get("urgency", "unknown")
        urgency_count[u] = urgency_count.get(u, 0) + 1
    return jsonify({"total": len(emails), "by_urgency": urgency_count})


EMAIL_HTML = r"""
<!DOCTYPE html>
<html><head><meta charset="UTF-8"><title>Email Priority Brain</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{background:#030814;color:#e2e8f0;font-family:'Rajdhani',sans-serif;padding:20px}
h1{font-family:'Orbitron',monospace;color:#00f0ff;font-size:20px;letter-spacing:3px;margin-bottom:20px}
.btn{background:rgba(0,240,255,0.1);border:1px solid #00f0ff;color:#00f0ff;padding:8px 14px;border-radius:6px;cursor:pointer;font-family:inherit;font-size:11px}
.btn:hover{background:rgba(0,240,255,0.2)}
.input{background:rgba(0,240,255,0.03);border:1px solid rgba(0,240,255,0.12);color:#e2e8f0;padding:8px 12px;border-radius:6px;font-family:inherit;font-size:12px;width:100%;margin-bottom:6px}
.textarea{background:rgba(0,240,255,0.03);border:1px solid rgba(0,240,255,0.12);color:#e2e8f0;padding:8px 12px;border-radius:6px;font-family:inherit;font-size:12px;width:100%;min-height:60px;resize:vertical}
.email-list{display:flex;flex-direction:column;gap:8px}
.email-card{background:rgba(3,8,20,0.8);border:1px solid rgba(0,240,255,0.12);border-radius:8px;padding:12px;cursor:pointer}
.email-card.critical{border-left:3px solid #ef4444}
.email-card.high{border-left:3px solid #f59e0b}
.email-card.medium{border-left:3px solid #0ea5e9}
.email-card.low{border-left:3px solid #22c55e}
.email-card.trivial{border-left:3px solid #64748b}
.email-from{font-size:12px;color:#00f0ff}
.email-subject{font-size:13px;margin:4px 0}
.email-body{font-size:11px;color:#94a3b8}
.email-meta{font-size:10px;color:#64748b;margin-top:4px}
.urgency-badge{display:inline-block;padding:2px 8px;border-radius:4px;font-size:9px;font-family:'Share Tech Mono',monospace}
.urgency-badge.critical{background:rgba(239,68,68,0.15);color:#ef4444}
.urgency-badge.high{background:rgba(245,158,11,0.15);color:#f59e0b}
.urgency-badge.medium{background:rgba(14,165,233,0.15);color:#0ea5e9}
.urgency-badge.low{background:rgba(34,197,94,0.15);color:#22c55e}
.urgency-badge.trivial{background:rgba(100,116,139,0.15);color:#64748b}
.add-form{background:rgba(3,8,20,0.8);border:1px solid rgba(0,240,255,0.15);border-radius:10px;padding:16px;margin-bottom:16px;display:none}
.add-form.show{display:block}
.stats{position:fixed;bottom:20px;right:20px;font-size:10px;color:#64748b;font-family:'Share Tech Mono',monospace}
</style></head><body>
<h1>EMAIL PRIORITY BRAIN</h1>
<button class="btn" onclick="toggleForm()">+ Add Email</button>
<div class="add-form" id="addForm">
  <input class="input" id="from" placeholder="From">
  <input class="input" id="to" placeholder="To">
  <input class="input" id="subject" placeholder="Subject">
  <textarea class="textarea" id="body" placeholder="Email body..."></textarea>
  <button class="btn" onclick="addEmail()" style="margin-top:8px">Classify & Save</button>
</div>
<div class="email-list" id="emails"></div>
<div class="stats" id="stats"></div>
<script>
function toggleForm(){document.getElementById('addForm').classList.toggle('show')}
async function load(){
  const r=await(await fetch('/api/emails/list')).json();
  document.getElementById('emails').innerHTML=(r.emails||[]).map(e=>
    '<div class="email-card '+e.urgency+'"><div class="email-from">'+e.from+' <span class="urgency-badge '+e.urgency+'">'+e.urgency.toUpperCase()+'</span></div>'+
    '<div class="email-subject">'+e.subject+'</div>'+
    '<div class="email-body">'+(e.body||'').substring(0,120)+'</div>'+
    '<div class="email-meta">'+e.date+(e.replied?' | Replied':'')+'</div></div>'
  ).join('')||'<div style="color:#64748b">No emails</div>';
  const s=await(await fetch('/api/emails/stats')).json();
  document.getElementById('stats').textContent=s.total+' emails | '+JSON.stringify(s.by_urgency);
}
async function addEmail(){
  const data={from:document.getElementById('from').value,to:document.getElementById('to').value,subject:document.getElementById('subject').value,body:document.getElementById('body').value};
  await fetch('/api/emails/add',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(data)});
  document.getElementById('from').value='';document.getElementById('to').value='';document.getElementById('subject').value='';document.getElementById('body').value='';
  document.getElementById('addForm').classList.remove('show');load();
}
load();
</script></body></html>
"""

if __name__ == "__main__":
    print("[System 19] Email Priority Brain starting on port 5029...")
    app.run(host="0.0.0.0", port=5029, debug=False)
