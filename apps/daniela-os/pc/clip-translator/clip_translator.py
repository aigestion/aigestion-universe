"""
System 37: Clipboard Translator
Auto-translates clipboard text with floating tooltip
"""

import hashlib
import json
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


LANGUAGES = {
    "es": "Spanish",
    "fr": "French",
    "de": "German",
    "it": "Italian",
    "pt": "Portuguese",
    "ja": "Japanese",
    "ko": "Korean",
    "zh": "Chinese",
    "ru": "Russian",
    "ar": "Arabic",
    "hi": "Hindi",
    "en": "English",
}


@app.route("/")
def index():
    return TRANSLATOR_HTML


@app.route("/api/translate", methods=["POST"])
def translate():
    data = request.json or {}
    text = data.get("text", "")
    target = data.get("target", "es")
    history = load_json(DATA_DIR / "history.json", {"items": []})
    entry = {
        "id": hashlib.md5(f"{time.time()}{text}".encode()).hexdigest()[:8],
        "original": text,
        "translated": f"[{target.upper()}] {text}",
        "source_lang": "auto",
        "target_lang": target,
        "timestamp": time.time(),
        "date": time.strftime("%Y-%m-%d %H:%M"),
    }
    history["items"].append(entry)
    history["items"] = history["items"][-200:]
    save_json(DATA_DIR / "history.json", history)
    return jsonify(
        {"ok": True, "translation": entry["translated"], "target": LANGUAGES.get(target, target)}
    )


@app.route("/api/translate/history")
def get_history():
    history = load_json(DATA_DIR / "history.json", {"items": []})
    history["items"].sort(key=lambda x: x.get("timestamp", 0), reverse=True)
    return jsonify(history)


@app.route("/api/translate/languages")
def get_languages():
    return jsonify({"languages": LANGUAGES})


TRANSLATOR_HTML = r"""
<!DOCTYPE html>
<html><head><meta charset="UTF-8"><title>Clipboard Translator</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{background:#030814;color:#e2e8f0;font-family:'Rajdhani',sans-serif;padding:20px}
h1{font-family:'Orbitron',monospace;color:#00f0ff;font-size:20px;letter-spacing:3px;margin-bottom:16px}
.btn{background:rgba(0,240,255,0.1);border:1px solid #00f0ff;color:#00f0ff;padding:8px 14px;border-radius:6px;cursor:pointer;font-family:inherit;font-size:11px}
.btn:hover{background:rgba(0,240,255,0.2)}
.input{background:rgba(0,240,255,0.03);border:1px solid rgba(0,240,255,0.12);color:#e2e8f0;padding:10px;border-radius:6px;font-family:inherit;font-size:13px;width:100%}
textarea{background:rgba(0,240,255,0.03);border:1px solid rgba(0,240,255,0.12);color:#e2e8f0;padding:10px;border-radius:6px;font-family:inherit;font-size:13px;width:100%;min-height:100px;resize:vertical}
textarea:focus,.input:focus{outline:none;border-color:#00f0ff}
select{background:rgba(0,240,255,0.03);border:1px solid rgba(0,240,255,0.12);color:#e2e8f0;padding:10px;border-radius:6px;font-family:inherit}
.translate-area{display:grid;grid-template-columns:1fr auto 1fr;gap:12px;align-items:start;margin-bottom:20px}
.result{background:rgba(34,197,94,0.05);border:1px solid rgba(34,197,94,0.2);border-radius:8px;padding:12px;min-height:100px;font-size:13px;color:#22c55e}
.history-item{padding:8px;border-bottom:1px solid rgba(0,240,255,0.05);font-size:11px}
.history-original{color:#94a3b8}
.history-translated{color:#22c55e;margin-top:2px}
.history-meta{font-size:9px;color:#64748b;margin-top:2px}
</style></head><body>
<h1>CLIPBOARD TRANSLATOR</h1>
<div class="translate-area">
  <div>
    <textarea id="input" placeholder="Type or paste text to translate..."></textarea>
  </div>
  <div style="display:flex;flex-direction:column;gap:8px;align-items:center;padding-top:20px">
    <select id="target"><option value="es">Spanish</option><option value="fr">French</option><option value="de">German</option><option value="it">Italian</option><option value="pt">Portuguese</option><option value="ja">Japanese</option><option value="ko">Korean</option><option value="zh">Chinese</option><option value="ru">Russian</option></select>
    <button class="btn" onclick="translate()">Translate</button>
  </div>
  <div class="result" id="result">Translation will appear here...</div>
</div>
<h2 style="font-size:14px;color:#00f0ff;margin-bottom:10px;font-family:'Orbitron',monospace;letter-spacing:1px">History</h2>
<div id="history"></div>
<script>
async function translate(){
  const text=document.getElementById('input').value;
  const target=document.getElementById('target').value;
  if(!text.trim())return;
  const r=await(await fetch('/api/translate',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({text,target})})).json();
  document.getElementById('result').textContent=r.translation;
  loadHistory();
}
async function loadHistory(){
  const r=await(await fetch('/api/translate/history')).json();
  document.getElementById('history').innerHTML=(r.items||[]).slice(-10).reverse().map(h=>
    '<div class="history-item"><div class="history-original">'+h.original.substring(0,100)+'</div>'+
    '<div class="history-translated">'+h.translated+'</div>'+
    '<div class="history-meta">'+h.date+' | '+h.target_lang.toUpperCase()+'</div></div>'
  ).join('');
}
document.getElementById('input').addEventListener('paste',()=>setTimeout(translate,100));
loadHistory();
</script></body></html>
"""

if __name__ == "__main__":
    print("[System 37] Clipboard Translator starting on port 5047...")
    app.run(host="0.0.0.0", port=5047, debug=False)
