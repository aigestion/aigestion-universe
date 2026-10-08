"""
System 42: Music Reactive Desktop
Desktop elements react to music playing on the system
"""

from flask import Flask

app = Flask(__name__)


@app.route("/")
def index():
    return MUSIC_HTML


MUSIC_HTML = r"""
<!DOCTYPE html>
<html><head><meta charset="UTF-8"><title>Music Reactive Desktop</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
html,body{width:100vw;height:100vh;overflow:hidden;background:#030814}
canvas{position:fixed;top:0;left:0}
#info{position:fixed;top:20px;right:20px;z-index:10;font-family:'Share Tech Mono',monospace;font-size:11px;color:#64748b;background:rgba(3,8,20,0.8);padding:10px;border-radius:8px;border:1px solid rgba(0,240,255,0.15)}
#startBtn{position:fixed;top:50%;left:50%;transform:translate(-50%,-50%);z-index:20;background:rgba(0,240,255,0.1);border:1px solid #00f0ff;color:#00f0ff;padding:16px 32px;border-radius:10px;cursor:pointer;font-family:'Orbitron',monospace;font-size:14px;letter-spacing:2px}
#startBtn:hover{background:rgba(0,240,255,0.2)}
</style></head><body>
<canvas id="c"></canvas>
<div id="info">Bass: <span id="bass">0</span> | Mid: <span id="mid">0</span> | Treble: <span id="treble">0</span></div>
<button id="startBtn" onclick="start()">Start Music Reactive</button>
<script>
const canvas=document.getElementById('c');const ctx=canvas.getContext('2d');
canvas.width=innerWidth;canvas.height=innerHeight;
window.onresize=()=>{canvas.width=innerWidth;canvas.height=innerHeight};

let audioCtx,analyser,dataArray;
let particles=[];let time=0;

async function start(){
  try{
    const stream=await navigator.mediaDevices.getUserMedia({audio:true});
    audioCtx=new(window.AudioContext||window.webkitAudioContext)();
    analyser=audioCtx.createAnalyser();
    audioCtx.createMediaStreamSource(stream).connect(analyser);
    analyser.fftSize=256;
    dataArray=new Uint8Array(analyser.frequencyBinCount);
    document.getElementById('startBtn').style.display='none';
    animate();
  }catch(e){alert('Microphone access needed for music reactivity')}
}

function animate(){
  requestAnimationFrame(animate);
  analyser.getByteFrequencyData(dataArray);
  ctx.fillStyle='rgba(3,8,20,0.15)';ctx.fillRect(0,0,canvas.width,canvas.height);

  const bass=dataArray.slice(0,10).reduce((a,b)=>a+b,0)/10;
  const mid=dataArray.slice(10,60).reduce((a,b)=>a+b,0)/50;
  const treble=dataArray.slice(60).reduce((a,b)=>a+b,0)/(dataArray.length-60);
  document.getElementById('bass').textContent=Math.round(bass);
  document.getElementById('mid').textContent=Math.round(mid);
  document.getElementById('treble').textContent=Math.round(treble);

  const cx=canvas.width/2,cy=canvas.height/2;

  for(let i=0;i<5;i++){
    const angle=(i/5)*Math.PI*2+time;
    const r=100+bass*2;
    const x=cx+Math.cos(angle)*r;
    const y=cy+Math.sin(angle)*r;
    ctx.beginPath();ctx.arc(x,y,10+bass/10,0,Math.PI*2);
    ctx.fillStyle=`hsla(${time*50+i*60},80%,60%,0.3)`;ctx.fill();
  }

  for(let i=0;i<dataArray.length;i+=2){
    const angle=(i/dataArray.length)*Math.PI*2;
    const r=50+dataArray[i]*1.5;
    const x=cx+Math.cos(angle)*r;
    const y=cy+Math.sin(angle)*r;
    ctx.beginPath();ctx.arc(x,y,2+dataArray[i]/80,0,Math.PI*2);
    ctx.fillStyle=`hsla(${i*4+time*20},70%,50%,0.6)`;ctx.fill();
  }

  for(let i=0;i<20;i++){
    const x=Math.random()*canvas.width;
    const y=Math.random()*canvas.height;
    const size=mid*0.2*Math.random();
    ctx.fillStyle=`rgba(0,240,255,${mid/500})`;
    ctx.fillRect(x,y,size,size);
  }

  if(bass>150){
    for(let i=0;i<3;i++){
      particles.push({x:cx,y:cy,vx:(Math.random()-0.5)*10,vy:(Math.random()-0.5)*10,life:30,hue:Math.random()*360});
    }
  }
  particles=particles.filter(p=>{p.x+=p.vx;p.y+=p.vy;p.life--;ctx.beginPath();ctx.arc(p.x,p.y,3,0,Math.PI*2);ctx.fillStyle=`hsla(${p.hue},80%,60%,${p.life/30})`;ctx.fill();return p.life>0});

  time+=0.01;
}
</script></body></html>
"""

if __name__ == "__main__":
    print("[System 42] Music Reactive Desktop starting on port 5052...")
    app.run(host="0.0.0.0", port=5052, debug=False)
