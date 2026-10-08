"""
System 44: Desktop DJ
Mix audio from different sources with visual equalizer
"""

from flask import Flask

app = Flask(__name__)


@app.route("/")
def index():
    return DJ_HTML


DJ_HTML = r"""
<!DOCTYPE html>
<html><head><meta charset="UTF-8"><title>Desktop DJ</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
html,body{width:100vw;height:100vh;overflow:hidden;background:#0a0a1a;font-family:'Rajdhani',sans-serif}
canvas{position:fixed;top:0;left:0;z-index:0}
#ui{position:fixed;bottom:30px;left:50%;transform:translateX(-50%);z-index:10;display:flex;gap:12px;align-items:flex-end}
.deck{background:rgba(3,8,20,0.9);border:1px solid rgba(0,240,255,0.2);border-radius:12px;padding:14px;width:200px}
.deck-label{font-family:'Orbitron',monospace;font-size:10px;color:#00f0ff;letter-spacing:1px;margin-bottom:8px}
.deck input[type=range]{width:100%;-webkit-appearance:none;height:4px;background:#1a1a3e;border-radius:2px}
.deck input[type=range]::-webkit-slider-thumb{-webkit-appearance:none;width:14px;height:14px;background:#00f0ff;border-radius:50%;cursor:pointer}
.deck-value{font-family:'Share Tech Mono',monospace;font-size:11px;color:#64748b;text-align:center;margin-top:4px}
.mix-panel{background:rgba(3,8,20,0.9);border:1px solid rgba(255,0,85,0.3);border-radius:12px;padding:14px;width:120px}
.mix-knob{width:60px;height:60px;border-radius:50%;border:3px solid #ff0055;margin:0 auto 8px;position:relative;cursor:pointer}
.mix-knob::after{content:'';position:absolute;top:5px;left:50%;width:2px;height:20px;background:#ff0055;transform-origin:bottom}
.btn{background:rgba(0,240,255,0.1);border:1px solid #00f0ff;color:#00f0ff;padding:6px 12px;border-radius:6px;cursor:pointer;font-family:inherit;font-size:10px}
.btn:hover{background:rgba(0,240,255,0.2)}
#startBtn{position:fixed;top:50%;left:50%;transform:translate(-50%,-50%);z-index:20;background:rgba(255,0,85,0.1);border:1px solid #ff0055;color:#ff0055;padding:16px 32px;border-radius:10px;cursor:pointer;font-family:'Orbitron',monospace;font-size:14px}
</style></head><body>
<canvas id="c"></canvas>
<button id="startBtn" onclick="start()">Start DJ</button>
<div id="ui" style="display:none">
  <div class="deck">
    <div class="deck-label">DECK A</div>
    <input type="range" id="volA" min="0" max="100" value="70" oninput="update()">
    <div class="deck-value" id="valA">70%</div>
  </div>
  <div class="mix-panel">
    <div class="deck-label" style="text-align:center">MASTER</div>
    <input type="range" id="master" min="0" max="100" value="80" style="width:100%" oninput="update()">
    <div class="deck-value" id="valM">80%</div>
  </div>
  <div class="deck">
    <div class="deck-label">DECK B</div>
    <input type="range" id="volB" min="0" max="100" value="70" oninput="update()">
    <div class="deck-value" id="valB">70%</div>
  </div>
</div>
<script>
const canvas=document.getElementById('c');const ctx=canvas.getContext('2d');
canvas.width=innerWidth;canvas.height=innerHeight;
let audioCtx,analyser,dataArray,time=0;

async function start(){
  try{
    const stream=await navigator.mediaDevices.getUserMedia({audio:true});
    audioCtx=new(window.AudioContext||window.webkitAudioContext)();
    analyser=audioCtx.createAnalyser();
    audioCtx.createMediaStreamSource(stream).connect(analyser);
    analyser.fftSize=256;
    dataArray=new Uint8Array(analyser.frequencyBinCount);
    document.getElementById('startBtn').style.display='none';
    document.getElementById('ui').style.display='flex';
    animate();
  }catch(e){alert('Microphone needed')}
}

function update(){
  document.getElementById('valA').textContent=document.getElementById('volA').value+'%';
  document.getElementById('valB').textContent=document.getElementById('volB').value+'%';
  document.getElementById('valM').textContent=document.getElementById('master').value+'%';
}

function animate(){
  requestAnimationFrame(animate);
  if(!analyser)return;
  analyser.getByteFrequencyData(dataArray);
  ctx.fillStyle='rgba(10,10,26,0.15)';ctx.fillRect(0,0,canvas.width,canvas.height);
  const barW=canvas.width/dataArray.length;
  for(let i=0;i<dataArray.length;i++){
    const h=dataArray[i]/255*canvas.height*0.6;
    const hue=(i/dataArray.length)*60+320;
    ctx.fillStyle=`hsl(${hue},80%,50%)`;
    ctx.fillRect(i*barW,canvas.height-h,barW-1,h);
    ctx.fillStyle=`hsl(${hue},80%,70%)`;
    ctx.fillRect(i*barW,canvas.height-h-4,barW-1,3);
  }
  time+=0.02;
}
</script></body></html>
"""

if __name__ == "__main__":
    print("[System 44] Desktop DJ starting on port 5054...")
    app.run(host="0.0.0.0", port=5054, debug=False)
