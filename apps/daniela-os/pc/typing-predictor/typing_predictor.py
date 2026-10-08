"""
System 16: Typing Predictor
Learns your writing style and autocompletes full sentences
"""

import json
import re
from pathlib import Path

from flask import Flask, jsonify, request

app = Flask(__name__)

DATA_DIR = Path(__file__).parent / "data"
DATA_DIR.mkdir(exist_ok=True)
CORPUS_FILE = DATA_DIR / "corpus.json"


def load_json(path, default=None):
    if path.exists():
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    return default or {}


def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


class TypingModel:
    def __init__(self):
        self.data = load_json(
            CORPUS_FILE, {"bigrams": {}, "trigrams": {}, "phrases": {}, "total_chars": 0}
        )
        self.bigrams = self.data.get("bigrams", {})
        self.trigrams = self.data.get("trigrams", {})
        self.phrases = self.data.get("phrases", {})

    def learn(self, text):
        words = text.lower().split()
        for i in range(len(words)):
            if i < len(words) - 1:
                key = words[i]
                next_w = words[i + 1]
                if key not in self.bigrams:
                    self.bigrams[key] = {}
                self.bigrams[key][next_w] = self.bigrams[key].get(next_w, 0) + 1
            if i < len(words) - 2:
                key = f"{words[i]} {words[i + 1]}"
                next_w = words[i + 2]
                if key not in self.trigrams:
                    self.trigrams[key] = {}
                self.trigrams[key][next_w] = self.trigrams[key].get(next_w, 0) + 1
        sentences = re.split(r"[.!?]+", text)
        for s in sentences:
            s = s.strip()
            if len(s) > 10:
                words = s.lower().split()
                if len(words) >= 2:
                    key = " ".join(words[:2])
                    self.phrases[key] = self.phrases.get(key, 0) + 1
        self.data = {
            "bigrams": self.bigrams,
            "trigrams": self.trigrams,
            "phrases": self.phrases,
            "total_chars": self.data.get("total_chars", 0) + len(text),
        }
        save_json(CORPUS_FILE, self.data)

    def predict(self, text, count=5):
        words = text.lower().split()
        predictions = []
        if words:
            last = words[-1]
            if last in self.bigrams:
                sorted_next = sorted(self.bigrams[last].items(), key=lambda x: x[1], reverse=True)
                for word, freq in sorted_next[:count]:
                    predictions.append({"text": word, "confidence": min(100, freq * 5)})
            if len(words) >= 2:
                key = f"{words[-2]} {words[-1]}"
                if key in self.trigrams:
                    sorted_next = sorted(
                        self.trigrams[key].items(), key=lambda x: x[1], reverse=True
                    )
                    for word, freq in sorted_next[:count]:
                        predictions.append({"text": word, "confidence": min(100, freq * 8)})
        return predictions[:count]


model = TypingModel()


@app.route("/")
def index():
    return TYPING_HTML


@app.route("/api/typing/learn", methods=["POST"])
def learn():
    data = request.json or {}
    text = data.get("text", "")
    model.learn(text)
    return jsonify({"ok": True, "chars": model.data.get("total_chars", 0)})


@app.route("/api/typing/predict")
def predict():
    text = request.args.get("text", "")
    count = int(request.args.get("count", 5))
    return jsonify({"predictions": model.predict(text, count)})


@app.route("/api/typing/stats")
def stats():
    return jsonify(
        {
            "bigrams": len(model.bigrams),
            "trigrams": len(model.trigrams),
            "phrases": len(model.phrases),
            "total_chars": model.data.get("total_chars", 0),
        }
    )


TYPING_HTML = r"""
<!DOCTYPE html>
<html><head><meta charset="UTF-8"><title>Typing Predictor</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{background:#030814;color:#e2e8f0;font-family:'Rajdhani',sans-serif;padding:20px}
h1{font-family:'Orbitron',monospace;color:#00f0ff;font-size:20px;letter-spacing:3px;margin-bottom:20px}
.editor{width:100%;min-height:300px;background:rgba(0,240,255,0.03);border:1px solid rgba(0,240,255,0.15);color:#e2e8f0;padding:16px;border-radius:10px;font-family:'Share Tech Mono',monospace;font-size:14px;line-height:1.6;resize:vertical}
.editor:focus{outline:none;border-color:#00f0ff}
.predictions{display:flex;gap:8px;margin:12px 0;flex-wrap:wrap}
.pred-chip{background:rgba(0,240,255,0.08);border:1px solid rgba(0,240,255,0.2);color:#00f0ff;padding:6px 14px;border-radius:20px;cursor:pointer;font-family:'Share Tech Mono',monospace;font-size:12px;transition:all 0.2s}
.pred-chip:hover{background:rgba(0,240,255,0.15);border-color:#00f0ff}
.pred-chip .conf{font-size:9px;color:#64748b;margin-left:4px}
.stats{position:fixed;bottom:20px;right:20px;font-size:10px;color:#64748b;font-family:'Share Tech Mono',monospace}
.controls{display:flex;gap:8px;margin:12px 0}
.btn{background:rgba(0,240,255,0.1);border:1px solid #00f0ff;color:#00f0ff;padding:8px 16px;border-radius:6px;cursor:pointer;font-family:inherit;font-size:12px}
.btn:hover{background:rgba(0,240,255,0.2)}
</style></head><body>
<h1>TYPING PREDICTOR</h1>
<div class="controls">
  <button class="btn" onclick="learnText()">Learn from text</button>
  <button class="btn" onclick="clearEditor()">Clear</button>
</div>
<div class="predictions" id="preds"></div>
<textarea class="editor" id="editor" placeholder="Start typing... The AI will learn your style and predict words/sentences as you type."></textarea>
<div class="stats" id="stats"></div>
<script>
const editor=document.getElementById('editor');
let learnBuffer='';
editor.addEventListener('input',async()=>{
  const text=editor.value;
  const lastSentence=text.split(/[.!?]\s+/).pop()||'';
  if(lastSentence.length>2){
    const r=await(await fetch('/api/typing/predict?text='+encodeURIComponent(lastSentence))).json();
    document.getElementById('preds').innerHTML=r.predictions.map(p=>
      '<div class="pred-chip" onclick="insertPrediction(\''+p.text.replace(/'/g,"\\'")+'\')">'+p.text+'<span class="conf">'+p.confidence+'%</span></div>'
    ).join('');
  }
  learnBuffer+=' '+text.split(/\s+/).pop();
  if(learnBuffer.length>200){fetch('/api/typing/learn',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({text:learnBuffer})});learnBuffer=''}
});
function insertPrediction(word){editor.value+=' '+word;editor.focus()}
function learnText(){const text=prompt('Paste text to learn from:');if(text)fetch('/api/typing/learn',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({text})}).then(()=>alert('Learned!'))}
function clearEditor(){editor.value=''}
async function loadStats(){const s=await(await fetch('/api/typing/stats')).json();document.getElementById('stats').textContent=s.bigrams+' bigrams | '+s.trigrams+' trigrams | '+s.total_chars+' chars learned'}
loadStats();
</script></body></html>
"""

if __name__ == "__main__":
    print("[System 16] Typing Predictor starting on port 5026...")
    app.run(host="0.0.0.0", port=5026, debug=False)
