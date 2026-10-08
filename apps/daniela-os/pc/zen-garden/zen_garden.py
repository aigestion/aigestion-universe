"""
System 22: Desktop Zen Garden
Floating ideas as stones/plants that grow into knowledge trees
"""

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


@app.route("/")
def index():
    return ZEN_HTML


@app.route("/api/zen/items")
def get_items():
    return jsonify(load_json(DATA_DIR / "garden.json", {"items": []}))


@app.route("/api/zen/add", methods=["POST"])
def add_item():
    data = request.json or {}
    items = load_json(DATA_DIR / "garden.json", {"items": []})
    item = {
        "id": int(time.time()),
        "text": data.get("text", ""),
        "type": data.get("type", "stone"),
        "x": data.get("x", 400 + (len(items) % 10) * 80),
        "y": data.get("y", 300 + (len(items) % 6) * 60),
        "growth": 0,
        "created": time.time(),
        "watered": 0,
    }
    items["items"].append(item)
    save_json(DATA_DIR / "garden.json", items)
    return jsonify({"ok": True})


@app.route("/api/zen/water", methods=["POST"])
def water_item():
    data = request.json or {}
    items = load_json(DATA_DIR / "garden.json", {"items": []})
    for item in items["items"]:
        if item["id"] == data.get("id"):
            item["watered"] = item.get("watered", 0) + 1
            item["growth"] = min(100, item.get("growth", 0) + 10)
            break
    save_json(DATA_DIR / "garden.json", items)
    return jsonify({"ok": True})


@app.route("/api/zen/delete", methods=["POST"])
def delete_item():
    data = request.json or {}
    items = load_json(DATA_DIR / "garden.json", {"items": []})
    items["items"] = [i for i in items["items"] if i["id"] != data.get("id")]
    save_json(DATA_DIR / "garden.json", items)
    return jsonify({"ok": True})


ZEN_HTML = r"""
<!DOCTYPE html>
<html><head><meta charset="UTF-8"><title>Desktop Zen Garden</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
html,body{width:100vw;height:100vh;overflow:hidden;background:#0a0a1a;font-family:'Rajdhani',sans-serif}
canvas{position:fixed;top:0;left:0;z-index:0}
#controls{position:fixed;bottom:20px;left:50%;transform:translateX(-50%);z-index:10;display:flex;gap:8px}
#controls input{background:rgba(3,8,20,0.8);border:1px solid rgba(0,240,255,0.2);color:#e2e8f0;padding:10px 16px;border-radius:8px;font-family:inherit;width:300px}
#controls input:focus{outline:none;border-color:#00f0ff}
.btn{background:rgba(0,240,255,0.1);border:1px solid #00f0ff;color:#00f0ff;padding:10px 16px;border-radius:8px;cursor:pointer;font-family:inherit}
.btn:hover{background:rgba(0,240,255,0.2)}
#tooltip{position:fixed;z-index:20;background:rgba(3,8,20,0.95);border:1px solid rgba(0,240,255,0.3);border-radius:8px;padding:10px 14px;color:#e2e8f0;font-size:12px;pointer-events:none;display:none;max-width:200px}
</style></head><body>
<canvas id="c"></canvas>
<div id="controls">
  <input id="ideaInput" placeholder="Add an idea to the garden...">
  <button class="btn" onclick="addIdea()">Plant</button>
</div>
<div id="tooltip"></div>
<script>
const canvas=document.getElementById('c');const ctx=canvas.getContext('2d');
canvas.width=innerWidth;canvas.height=innerHeight;
window.onresize=()=>{canvas.width=innerWidth;canvas.height=innerHeight;draw()};

let items=[];let time=0;let selected=null;

async function loadItems(){const r=await(await fetch('/api/zen/items')).json();items=r.items||[];draw()}
async function addIdea(){
  const text=document.getElementById('ideaInput').value;if(!text)return;
  await fetch('/api/zen/add',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({text,type:'stone',x:200+Math.random()*(canvas.width-400),y:200+Math.random()*(canvas.height-400)})});
  document.getElementById('ideaInput').value='';loadItems();
}

function draw(){
  ctx.clearRect(0,0,canvas.width,canvas.height);
  const grad=ctx.createRadialGradient(canvas.width/2,canvas.height/2,0,canvas.width/2,canvas.height/2,canvas.width/2);
  grad.addColorStop(0,'#0a1a0a');grad.addColorStop(1,'#0a0a1a');
  ctx.fillStyle=grad;ctx.fillRect(0,0,canvas.width,canvas.height);

  ctx.strokeStyle='rgba(0,240,255,0.03)';
  for(let x=0;x<canvas.width;x+=40){ctx.beginPath();ctx.moveTo(x,0);ctx.lineTo(x,canvas.height);ctx.stroke()}
  for(let y=0;y<canvas.height;y+=40){ctx.beginPath();ctx.moveTo(0,y);ctx.lineTo(canvas.width,y);ctx.stroke()}

  items.forEach(item=>{
    const growth=item.growth||0;const size=10+growth*0.4;
    const yOff=Math.sin(time*0.5+item.id)*3;

    if(growth<30){
      ctx.fillStyle=`rgba(120,120,140,${0.6+growth*0.01})`;
      ctx.beginPath();ctx.ellipse(item.x,item.y+yOff,size,size*0.6,0,0,Math.PI*2);ctx.fill();
    }else{
      const h=growth;ctx.strokeStyle=`hsl(${120+h},60%,40%)`;ctx.lineWidth=2+growth*0.02;
      ctx.beginPath();ctx.moveTo(item.x,item.y+size);ctx.lineTo(item.x,item.y+size-h*0.8);ctx.stroke();
      for(let b=0;b<Math.min(5,growth/20);b++){
        const by=item.y+size-h*0.8*(b+1)/(Math.min(5,growth/20)+1);
        const bl=(growth-b*10)*0.3;
        ctx.fillStyle=`hsl(${120+h},50%,${40+b*5}%)`;
        ctx.beginPath();ctx.ellipse(item.x-bl,by,bl,bl*0.4,-0.3,0,Math.PI*2);ctx.fill();
        ctx.beginPath();ctx.ellipse(item.x+bl,by,bl,bl*0.4,0.3,0,Math.PI*2);ctx.fill();
      }
    }
    ctx.fillStyle='#e2e8f0';ctx.font='10px Share Tech Mono';ctx.textAlign='center';
    ctx.fillText(item.text.substring(0,15),item.x,item.y+size+16);
  });
  time+=0.02;requestAnimationFrame(draw);
}

canvas.addEventListener('click',e=>{
  const rect=canvas.getBoundingClientRect();
  const mx=e.clientX-rect.left,my=e.clientY-rect.top;
  for(const item of items){
    if(Math.hypot(mx-item.x,my-item.y)<20){
      fetch('/api/zen/water',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({id:item.id})}).then(()=>loadItems());
      break;
    }
  }
});

canvas.addEventListener('mousemove',e=>{
  const rect=canvas.getBoundingClientRect();
  const mx=e.clientX-rect.left,my=e.clientY-rect.top;
  let found=false;
  for(const item of items){
    if(Math.hypot(mx-item.x,my-item.y)<20){
      const tip=document.getElementById('tooltip');
      tip.style.display='block';tip.style.left=(e.clientX+10)+'px';tip.style.top=(e.clientY-30)+'px';
      tip.innerHTML='<b>'+item.text+'</b><br>Growth: '+(item.growth||0)+'%<br>Watered: '+(item.watered||0)+'x';
      found=true;break;
    }
  }
  if(!found)document.getElementById('tooltip').style.display='none';
});

loadItems();
</script></body></html>
"""

if __name__ == "__main__":
    print("[System 22] Desktop Zen Garden starting on port 5032...")
    app.run(host="0.0.0.0", port=5032, debug=False)
