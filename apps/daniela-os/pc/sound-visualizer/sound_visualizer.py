"""
System 29: Sound Visualizer Pro
Real-time audio visualization with Web Audio API
"""

from flask import Flask

app = Flask(__name__)


@app.route("/")
def index():
    return SOUND_HTML


SOUND_HTML = r"""
<!DOCTYPE html>
<html><head><meta charset="UTF-8"><title>Sound Visualizer Pro</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
html,body{width:100vw;height:100vh;overflow:hidden;background:#000}
canvas{position:fixed;top:0;left:0}
#controls{position:fixed;bottom:20px;left:50%;transform:translateX(-50%);z-index:10;display:flex;gap:8px}
.btn{background:rgba(0,240,255,0.1);border:1px solid #00f0ff;color:#00f0ff;padding:10px 18px;border-radius:8px;cursor:pointer;font-family:'Share Tech Mono',monospace;font-size:12px}
.btn:hover{background:rgba(0,240,255,0.2)}
.btn.active{background:rgba(0,240,255,0.3);border-color:#fff}
#info{position:fixed;top:20px;right:20px;z-index:10;font-family:'Share Tech Mono',monospace;font-size:11px;color:#64748b}
</style></head><body>
<canvas id="c"></canvas>
<div id="controls">
  <button class="btn" id="startBtn" onclick="startMic()">Start Microphone</button>
  <button class="btn" onclick="toggleMode()">Change Mode</button>
</div>
<div id="info">Mode: Bars | Click "Start Microphone" to begin</div>
<script>
const canvas=document.getElementById('c');const ctx=canvas.getContext('2d');
canvas.width=innerWidth;canvas.height=innerHeight;
window.onresize=()=>{canvas.width=innerWidth;canvas.height=innerHeight};

let audioCtx,analyser,dataArray,source;
let mode=0;const modes=['bars','wave','circle','particles'];
let particles=[];

async function startMic(){
  try{
    const stream=await navigator.mediaDevices.getUserMedia({audio:true});
    audioCtx=new(window.AudioContext||window.webkitAudioContext)();
    analyser=audioCtx.createAnalyser();
    source=audioCtx.createMediaStreamSource(stream);
    source.connect(analyser);
    analyser.fftSize=256;
    dataArray=new Uint8Array(analyser.frequencyBinCount);
    document.getElementById('startBtn').textContent='Listening...';
    document.getElementById('startBtn').classList.add('active');
    animate();
  }catch(e){alert('Microphone access denied')}
}

function toggleMode(){mode=(mode+1)%modes.length;document.getElementById('info').textContent='Mode: '+modes[mode].charAt(0).toUpperCase()+modes[mode].slice(1)}

function animate(){
  requestAnimationFrame(animate);
  if(!analyser)return;
  analyser.getByteFrequencyData(dataArray);
  ctx.fillStyle='rgba(0,0,0,0.15)';ctx.fillRect(0,0,canvas.width,canvas.height);
  const avg=dataArray.reduce((a,b)=>a+b,0)/dataArray.length;
  if(mode===0){
    const barW=canvas.width/dataArray.length*2;
    for(let i=0;i<dataArray.length;i++){
      const h=dataArray[i]/255*canvas.height*0.8;
      const hue=(i/dataArray.length)*360;
      ctx.fillStyle=`hsl(${hue},80%,50%)`;
      ctx.fillRect(i*barW,canvas.height-h,barW-2,h);
    }
  }else if(mode===1){
    ctx.beginPath();ctx.strokeStyle=`hsl(${avg*2},80%,60%)`;ctx.lineWidth=2;
    for(let i=0;i<dataArray.length;i++){
      const x=(i/dataArray.length)*canvas.width;
      const y=canvas.height/2+((dataArray[i]-128)/128)*canvas.height*0.4;
      i===0?ctx.moveTo(x,y):ctx.lineTo(x,y);
    }
    ctx.stroke();
  }else if(mode===2){
    const cx=canvas.width/2,cy=canvas.height/2;
    for(let i=0;i<dataArray.length;i++){
      const angle=(i/dataArray.length)*Math.PI*2;
      const r=100+dataArray[i]*0.8;
      const x=cx+Math.cos(angle)*r;
      const y=cy+Math.sin(angle)*r;
      ctx.beginPath();ctx.arc(x,y,3+dataArray[i]/50,0,Math.PI*2);
      ctx.fillStyle=`hsl(${i*3},80%,60%)`;ctx.fill();
    }
  }else{
    for(let i=0;i<dataArray.length;i+=2){
      if(dataArray[i]>150){
        particles.push({x:Math.random()*canvas.width,y:canvas.height,vx:(Math.random()-0.5)*5,vy:-Math.random()*5-2,size:Math.random()*4+1,hue:Math.random()*360,life:60});
      }
    }
    particles=particles.filter(p=>{p.x+=p.vx;p.y+=p.vy;p.vy+=0.1;p.life--;ctx.beginPath();ctx.arc(p.x,p.y,p.size,0,Math.PI*2);ctx.fillStyle=`hsla(${p.hue},80%,60%,${p.life/60})`;ctx.fill();return p.life>0});
  }
}
</script></body></html>
"""

if __name__ == "__main__":
    print("[System 29] Sound Visualizer Pro starting on port 5039...")
    app.run(host="0.0.0.0", port=5039, debug=False)
