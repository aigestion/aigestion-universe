"""
System 53: Password Vault
Encrypted password manager
"""

import json
import secrets
import time
from pathlib import Path

from flask import Flask, jsonify, request

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


def simple_encrypt(text, key):
    return "".join(chr(ord(c) ^ ord(key[i % len(key)])) for i, c in enumerate(text))


def simple_decrypt(text, key):
    return simple_encrypt(text, key)


VAULT_KEY = "daniela_os_2024"


@app.route("/")
def index():
    return VAULT_HTML


@app.route("/api/vault/list")
def list_passwords():
    vault = load_json(DATA_DIR / "vault.json", {"entries": []})
    entries = []
    for e in vault.get("entries", []):
        try:
            decrypted = simple_decrypt(e.get("password", ""), VAULT_KEY)
        except Exception:
            decrypted = "***"
        entries.append(
            {
                "id": e.get("id"),
                "name": e.get("name"),
                "username": e.get("username"),
                "password": decrypted,
                "url": e.get("url", ""),
                "category": e.get("category", "general"),
                "created": e.get("created"),
                "last_used": e.get("last_used"),
            }
        )
    return jsonify({"entries": entries})


@app.route("/api/vault/add", methods=["POST"])
def add_entry():
    data = request.json or {}
    vault = load_json(DATA_DIR / "vault.json", {"entries": []})
    entry = {
        "id": secrets.token_hex(8),
        "name": data.get("name", ""),
        "username": data.get("username", ""),
        "password": simple_encrypt(data.get("password", ""), VAULT_KEY),
        "url": data.get("url", ""),
        "category": data.get("category", "general"),
        "created": time.time(),
        "last_used": time.time(),
    }
    vault["entries"].append(entry)
    save_json(DATA_DIR / "vault.json", vault)
    return jsonify({"ok": True, "id": entry["id"]})


@app.route("/api/vault/delete", methods=["POST"])
def delete_entry():
    data = request.json or {}
    vault = load_json(DATA_DIR / "vault.json", {"entries": []})
    vault["entries"] = [e for e in vault["entries"] if e.get("id") != data.get("id")]
    save_json(DATA_DIR / "vault.json", vault)
    return jsonify({"ok": True})


@app.route("/api/vault/generate", methods=["POST"])
def generate_password():
    data = request.json or {}
    length = min(max(data.get("length", 16), 8), 64)
    use_upper = data.get("uppercase", True)
    use_numbers = data.get("numbers", True)
    use_symbols = data.get("symbols", True)
    chars = "abcdefghijklmnopqrstuvwxyz"
    if use_upper:
        chars += "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    if use_numbers:
        chars += "0123456789"
    if use_symbols:
        chars += "!@#$%^&*()_+-=[]{}|;:,.<>?"
    password = "".join(secrets.choice(chars) for _ in range(length))
    return jsonify({"password": password})


VAULT_HTML = r"""
<!DOCTYPE html>
<html><head><meta charset="UTF-8"><title>Password Vault</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{background:#0a0a1a;color:#e2e8f0;font-family:'Rajdhani',sans-serif;padding:20px}
h1{font-family:'Orbitron',monospace;color:#00f0ff;font-size:20px;letter-spacing:3px;margin-bottom:20px}
.header{display:flex;justify-content:space-between;align-items:center;margin-bottom:16px}
.btn{background:rgba(0,240,255,0.1);border:1px solid #00f0ff;color:#00f0ff;padding:8px 14px;border-radius:6px;cursor:pointer;font-size:11px;font-family:inherit}
.btn-danger{border-color:#ff0055;color:#ff0055;background:rgba(255,0,85,0.1)}
.entries{display:grid;gap:8px}
.entry{background:rgba(3,8,20,0.8);border:1px solid rgba(0,240,255,0.12);border-radius:10px;padding:12px;display:flex;justify-content:space-between;align-items:center;transition:all 0.3s}
.entry:hover{border-color:#00f0ff}
.entry-info{flex:1}
.entry-name{font-family:'Orbitron',monospace;font-size:12px;color:#00f0ff}
.entry-user{font-size:11px;color:#94a3b8;margin-top:2px}
.entry-pass{font-family:'Share Tech Mono',monospace;font-size:11px;color:#64748b;margin-top:4px}
.entry-actions{display:flex;gap:6px}
.modal{position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,0.8);z-index:100;display:none;align-items:center;justify-content:center}
.modal.show{display:flex}
.modal-content{background:#0a0a1a;border:1px solid rgba(0,240,255,0.2);border-radius:12px;padding:20px;width:360px}
.modal-title{font-family:'Orbitron',monospace;font-size:14px;color:#00f0ff;margin-bottom:16px}
.input{width:100%;background:rgba(0,240,255,0.03);border:1px solid rgba(0,240,255,0.12);color:#e2e8f0;padding:8px 12px;border-radius:6px;font-family:inherit;font-size:12px;margin-bottom:10px}
.gen-row{display:flex;gap:8px;margin-bottom:10px}
.gen-row label{font-size:11px;color:#94a3b8;display:flex;align-items:center;gap:4px}
.gen-row input[type=checkbox]{accent-color:#00f0ff}
.gen-output{font-family:'Share Tech Mono',monospace;background:rgba(0,240,255,0.05);padding:8px;border-radius:6px;font-size:12px;color:#22c55e;margin-bottom:10px;word-break:break-all}
</style></head><body>
<h1>PASSWORD VAULT</h1>
<div class="header">
  <div style="font-size:12px;color:#64748b" id="count">0 passwords stored</div>
  <button class="btn" onclick="showAdd()">Add Password</button>
</div>
<div class="entries" id="entries"></div>
<div class="modal" id="addModal">
  <div class="modal-content">
    <div class="modal-title">Add Password</div>
    <input class="input" id="name" placeholder="Name (e.g. Gmail)">
    <input class="input" id="username" placeholder="Username / Email">
    <input class="input" id="password" placeholder="Password" type="password">
    <input class="input" id="url" placeholder="URL (optional)">
    <div class="gen-row">
      <label><input type="checkbox" id="genUpper" checked> A-Z</label>
      <label><input type="checkbox" id="genNum" checked> 0-9</label>
      <label><input type="checkbox" id="genSym" checked> !@#</label>
      <input type="range" id="genLen" min="8" max="64" value="16" style="flex:1" oninput="document.getElementById('genLenVal').textContent=this.value">
      <span id="genLenVal" style="font-size:11px;color:#64748b">16</span>
      <button class="btn" onclick="generate()">Gen</button>
    </div>
    <div class="gen-output" id="genOutput" style="display:none"></div>
    <div style="display:flex;gap:8px">
      <button class="btn" onclick="saveEntry()">Save</button>
      <button class="btn btn-danger" onclick="closeAdd()">Cancel</button>
    </div>
  </div>
</div>
<script>
async function load(){
  const r=await(await fetch('/api/vault/list')).json();
  document.getElementById('count').textContent=(r.entries||[]).length+' passwords stored';
  document.getElementById('entries').innerHTML=(r.entries||[]).map(e=>
    '<div class="entry"><div class="entry-info"><div class="entry-name">'+e.name+'</div>'+
    '<div class="entry-user">'+e.username+'</div>'+
    '<div class="entry-pass" id="p-'+e.id+'">*****</div></div>'+
    '<div class="entry-actions">'+
    '<button class="btn" onclick="togglePass(\''+e.id+'\',\''+btoa(e.password)+'\')">Show</button>'+
    '<button class="btn" onclick="copyPass(\''+btoa(e.password)+'\')">Copy</button>'+
    '<button class="btn btn-danger" onclick="delEntry(\''+e.id+'\')">Del</button>'+
    '</div></div>'
  ).join('');
}
function showAdd(){document.getElementById('addModal').classList.add('show')}
function closeAdd(){document.getElementById('addModal').classList.remove('show')}
function togglePass(id,b64){const el=document.getElementById('p-'+id);el.textContent=el.textContent==='*****'?atob(b64):'*****'}
function copyPass(b64){navigator.clipboard.writeText(atob(b64))}
async function generate(){
  const r=await(await fetch('/api/vault/generate',{method:'POST',headers:{'Content-Type':'application/json'},
    body:JSON.stringify({length:parseInt(document.getElementById('genLen').value),uppercase:document.getElementById('genUpper').checked,numbers:document.getElementById('genNum').checked,symbols:document.getElementById('genSym').checked})})).json();
  document.getElementById('genOutput').textContent=r.password;document.getElementById('genOutput').style.display='block';
  document.getElementById('password').value=r.password;
}
async function saveEntry(){
  await fetch('/api/vault/add',{method:'POST',headers:{'Content-Type':'application/json'},
    body:JSON.stringify({name:document.getElementById('name').value,username:document.getElementById('username').value,password:document.getElementById('password').value,url:document.getElementById('url').value})});
  closeAdd();load();
}
async function delEntry(id){if(confirm('Delete?')){await fetch('/api/vault/delete',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({id})});load()}}
load();
</script></body></html>
"""

if __name__ == "__main__":
    print("[System 53] Password Vault starting on port 5063...")
    app.run(host="0.0.0.0", port=5063, debug=False)
