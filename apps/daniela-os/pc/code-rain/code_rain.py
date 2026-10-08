"""
System 26: Code Rain Matrix
Falling code background with your own code
"""

import json
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


@app.route("/")
def index():
    return RAIN_HTML


@app.route("/api/rain/config")
def config():
    return jsonify(
        load_json(
            DATA_DIR / "config.json",
            {
                "speed": 1,
                "density": 30,
                "color": "#00ff41",
                "fontSize": 14,
                "chars": "abcdefghijklmnopqrstuvwxyz0123456789{}[]<>()=+-*/",
            },
        )
    )


@app.route("/api/rain/config", methods=["POST"])
def set_config():
    data = request.json or {}
    save_json(DATA_DIR / "config.json", data)
    return jsonify({"ok": True})


RAIN_HTML = r"""
<!DOCTYPE html>
<html><head><meta charset="UTF-8"><title>Code Rain Matrix</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
html,body{width:100vw;height:100vh;overflow:hidden;background:#000}
canvas{position:fixed;top:0;left:0}
#controls{position:fixed;bottom:20px;left:50%;transform:translateX(-50%);z-index:10;display:flex;gap:8px}
.btn{background:rgba(0,255,65,0.1);border:1px solid #00ff41;color:#00ff41;padding:8px 14px;border-radius:6px;cursor:pointer;font-family:'Share Tech Mono',monospace;font-size:11px}
.btn:hover{background:rgba(0,255,65,0.2)}
</style></head><body>
<canvas id="c"></canvas>
<div id="controls">
  <button class="btn" onclick="changeSpeed(-0.2)">Slower</button>
  <button class="btn" onclick="changeSpeed(0.2)">Faster</button>
  <button class="btn" onclick="changeColor()">Change Color</button>
</div>
<script>
const canvas=document.getElementById('c');const ctx=canvas.getContext('2d');
canvas.width=innerWidth;canvas.height=innerHeight;
window.onresize=()=>{canvas.width=innerWidth;canvas.height=innerHeight;initColumns()};

const chars='abcdefghijklmnopqrstuvwxyz0123456789{}[]<>()=+-*/アイウエオカキクケコサシスセソ';
let columns=[];let speed=1;let colors=['#00ff41','#00ffff','#ff00ff','#ffff00'];
let colorIdx=0;

function initColumns(){
  columns=[];
  const colW=18;
  for(let i=0;i<canvas.width/colW;i++){
    columns.push({x:i*colW,y:Math.random()*canvas.height,speed:0.5+Math.random()*1.5,chars:[]});
    for(let j=0;j<30;j++)columns[i].chars.push(chars[Math.floor(Math.random()*chars.length)]);
  }
}

function draw(){
  ctx.fillStyle='rgba(0,0,0,0.05)';ctx.fillRect(0,0,canvas.width,canvas.height);
  ctx.font='14px Share Tech Mono';
  const color=colors[colorIdx];
  columns.forEach(col=>{
    col.y+=col.speed*speed;
    for(let i=0;i<col.chars.length;i++){
      const y=col.y+i*18;
      if(y>0&&y<canvas.height){
        const alpha=1-i/col.chars.length;
        ctx.fillStyle=i===0?'#fff':color.replace(')',','+alpha+')').replace('rgb','rgba').replace('#','');
        if(i===0){ctx.fillStyle='#fff'}
        else{ctx.globalAlpha=alpha;ctx.fillStyle=color}
        ctx.fillText(col.chars[i],col.x,y);
        ctx.globalAlpha=1;
      }
    }
    if(col.y>canvas.height+200){col.y=-200;for(let j=0;j<col.chars.length;j++)col.chars[j]=chars[Math.floor(Math.random()*chars.length)]}
  });
  requestAnimationFrame(draw);
}

function changeSpeed(d){speed=Math.max(0.2,Math.min(3,speed+d))}
function changeColor(){colorIdx=(colorIdx+1)%colors.length}
initColumns();draw();
</script></body></html>
"""

if __name__ == "__main__":
    print("[System 26] Code Rain Matrix starting on port 5036...")
    app.run(host="0.0.0.0", port=5036, debug=False)
