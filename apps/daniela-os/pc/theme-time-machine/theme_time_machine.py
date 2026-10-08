"""
System 24: Theme Time Machine
Change the entire PC look by decade: Windows 95, Aero, Metro, Neumorphism, Glassmorphism
"""

import json
from pathlib import Path

from flask import Flask, jsonify, request

app = Flask(__name__)
DATA_DIR = Path(__file__).parent / "data"
DATA_DIR.mkdir(exist_ok=True)

THEMES = {
    "win95": {
        "name": "Windows 95",
        "year": 1995,
        "bg": "#008080",
        "accent": "#c0c0c0",
        "text": "#000000",
        "font": "MS Sans Serif",
        "style": "retro",
    },
    "xp": {
        "name": "Windows XP",
        "year": 2001,
        "bg": "#3a6ea5",
        "accent": "#316ac5",
        "text": "#ffffff",
        "font": "Tahoma",
        "style": "classic",
    },
    "aero": {
        "name": "Windows Aero",
        "year": 2007,
        "bg": "#1a2a3a",
        "accent": "#4580c4",
        "text": "#ffffff",
        "font": "Segoe UI",
        "style": "glass",
    },
    "metro": {
        "name": "Metro/Modern",
        "year": 2012,
        "bg": "#2d2d2d",
        "accent": "#0078d4",
        "text": "#ffffff",
        "font": "Segoe UI Light",
        "style": "flat",
    },
    "neumorphism": {
        "name": "Neumorphism",
        "year": 2020,
        "bg": "#e0e5ec",
        "accent": "#6c5ce7",
        "text": "#2d3436",
        "font": "Inter",
        "style": "neumorphic",
    },
    "glassmorphism": {
        "name": "Glassmorphism",
        "year": 2022,
        "bg": "#0a0a2e",
        "accent": "#00f0ff",
        "text": "#ffffff",
        "font": "Rajdhani",
        "style": "glass2",
    },
    "cyberpunk": {
        "name": "Cyberpunk",
        "year": 2077,
        "bg": "#0a0a0a",
        "accent": "#ff0055",
        "text": "#00ff41",
        "font": "Orbitron",
        "style": "cyber",
    },
}


def load_json(path, default=None):
    if path.exists():
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    return default or {}


def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


@app.route("/")
def index():
    return THEME_HTML


@app.route("/api/themes/list")
def list_themes():
    return jsonify({"themes": THEMES})


@app.route("/api/themes/current")
def current_theme():
    state = load_json(DATA_DIR / "state.json", {"current": "glassmorphism"})
    return jsonify(
        {
            "current": state["current"],
            "theme": THEMES.get(state["current"], THEMES["glassmorphism"]),
        }
    )


@app.route("/api/themes/set", methods=["POST"])
def set_theme():
    data = request.json or {}
    theme = data.get("theme", "glassmorphism")
    if theme in THEMES:
        save_json(DATA_DIR / "state.json", {"current": theme})
        return jsonify({"ok": True, "theme": THEMES[theme]})
    return jsonify({"error": "Unknown theme"}), 400


THEME_HTML = r"""
<!DOCTYPE html>
<html><head><meta charset="UTF-8"><title>Theme Time Machine</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{background:#030814;color:#e2e8f0;font-family:'Rajdhani',sans-serif;padding:20px}
h1{font-family:'Orbitron',monospace;color:#00f0ff;font-size:20px;letter-spacing:3px;margin-bottom:20px}
.themes{display:grid;grid-template-columns:repeat(auto-fill,minmax(200px,1fr));gap:12px}
.theme-card{border-radius:12px;padding:20px;cursor:pointer;transition:all 0.3s;border:2px solid transparent;position:relative;overflow:hidden}
.theme-card:hover{transform:translateY(-4px);box-shadow:0 8px 30px rgba(0,0,0,0.3)}
.theme-card.active{border-color:#00f0ff;box-shadow:0 0 20px rgba(0,240,255,0.3)}
.theme-name{font-family:'Orbitron',monospace;font-size:14px;letter-spacing:1px}
.theme-year{font-size:10px;margin-top:4px;opacity:0.7}
.theme-preview{margin-top:12px;padding:8px;border-radius:6px;font-size:10px}
.preview-bar{height:6px;border-radius:3px;margin:3px 0}
</style></head><body>
<h1>THEME TIME MACHINE</h1>
<div class="themes" id="themes"></div>
<script>
const themeStyles={
  win95:{bg:'#008080',card:'#c0c0c0',text:'#000',bar1:'#808080',bar2:'#c0c0c0'},
  xp:{bg:'#3a6ea5',card:'#316ac5',text:'#fff',bar1:'#ff6600',bar2:'#316ac5'},
  aero:{bg:'#1a2a3a',card:'rgba(69,128,196,0.3)',text:'#fff',bar1:'rgba(255,255,255,0.2)',bar2:'#4580c4'},
  metro:{bg:'#2d2d2d',card:'#0078d4',text:'#fff',bar1:'#0078d4',bar2:'#107c10'},
  neumorphism:{bg:'#e0e5ec',card:'#e0e5ec',text:'#2d3436',bar1:'#a3b1c6',bar2:'#6c5ce7'},
  glassmorphism:{bg:'#0a0a2e',card:'rgba(0,240,255,0.1)',text:'#fff',bar1:'rgba(0,240,255,0.3)',bar2:'#00f0ff'},
  cyberpunk:{bg:'#0a0a0a',card:'rgba(255,0,85,0.15)',text:'#00ff41',bar1:'#ff0055',bar2:'#00ff41'}
};

async function load(){
  const r=await(await fetch('/api/themes/list')).json();
  const cur=await(await fetch('/api/themes/current')).json();
  document.getElementById('themes').innerHTML=Object.entries(r.themes).map(([k,t])=>{
    const s=themeStyles[k]||themeStyles.glassmorphism;
    return '<div class="theme-card'+(cur.current===k?' active':'')+'" style="background:'+s.card+';color:'+s.text+'" onclick="setTheme(\''+k+'\')">'+
    '<div class="theme-name">'+t.name+'</div><div class="theme-year">'+t.year+'</div>'+
    '<div class="theme-preview"><div class="preview-bar" style="background:'+s.bar1+'"></div><div class="preview-bar" style="background:'+s.bar2+'"></div><div class="preview-bar" style="background:'+s.bar1+';width:60%"></div></div></div>';
  }).join('');
}
async function setTheme(k){
  await fetch('/api/themes/set',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({theme:k})});
  load();
}
load();
</script></body></html>
"""

if __name__ == "__main__":
    print("[System 24] Theme Time Machine starting on port 5034...")
    app.run(host="0.0.0.0", port=5034, debug=False)
