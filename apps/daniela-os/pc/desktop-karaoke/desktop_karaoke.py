"""
System 49: Desktop Karaoke
Floating synced lyrics with music player
"""

from flask import Flask

app = Flask(__name__)


@app.route("/")
def index():
    return KARAOKE_HTML


KARAOKE_HTML = r"""
<!DOCTYPE html>
<html><head><meta charset="UTF-8"><title>Desktop Karaoke</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
html,body{width:100vw;height:100vh;overflow:hidden;background:rgba(3,8,20,0.95);font-family:'Rajdhani',sans-serif}
#lyrics{position:fixed;top:50%;left:50%;transform:translate(-50%,-50%);text-align:center;width:80%;z-index:10}
.line{font-family:'Impact',sans-serif;font-size:32px;color:rgba(255,255,255,0.2);transition:all 0.5s;margin:8px 0;letter-spacing:2px}
.line.past{color:rgba(0,240,255,0.3)}
.line.current{color:#00f0ff;font-size:40px;text-shadow:0 0 20px rgba(0,240,255,0.5)}
.line.future{color:rgba(255,255,255,0.15)}
#bg{position:fixed;top:0;left:0;width:100%;height:100%;z-index:0}
#controls{position:fixed;bottom:30px;left:50%;transform:translateX(-50%);z-index:10;display:flex;gap:10px;align-items:center}
.ctrl{background:rgba(3,8,20,0.8);border:1px solid rgba(0,240,255,0.2);border-radius:8px;padding:8px 14px;cursor:pointer;color:#00f0ff;font-size:12px}
.ctrl:hover{background:rgba(0,240,255,0.1)}
.ctrl.play{background:rgba(0,240,255,0.15);border-color:#00f0ff;font-size:16px;width:40px;height:40px;border-radius:50%;display:flex;align-items:center;justify-content:center}
#progress{width:300px;height:4px;background:rgba(0,240,255,0.1);border-radius:2px;cursor:pointer;position:relative}
#progressFill{height:100%;background:#00f0ff;border-radius:2px;width:0%;transition:width 0.1s}
#songInfo{position:fixed;top:20px;left:20px;z-index:10;font-family:'Orbitron',monospace;font-size:11px;color:#64748b}
#songTitle{color:#00f0ff;font-size:14px;margin-bottom:4px}
#mode{position:fixed;top:20px;right:20px;z-index:10;display:flex;gap:6px}
.mode-btn{background:rgba(3,8,20,0.8);border:1px solid rgba(0,240,255,0.12);border-radius:6px;padding:4px 8px;cursor:pointer;font-size:9px;color:#64748b}
.mode-btn.active{border-color:#00f0ff;color:#00f0ff}
</style></head><body>
<canvas id="bg"></canvas>
<div id="lyrics" id="lyricsBox"></div>
<div id="songInfo"><div id="songTitle">No song loaded</div><div id="songArtist">Load lyrics to start</div></div>
<div id="mode">
  <div class="mode-btn active">Float</div>
  <div class="mode-btn">Fade</div>
  <div class="mode-btn">Bounce</div>
  <div class="mode-btn">Wave</div>
</div>
<div id="controls">
  <div class="ctrl" onclick="prev()">10964</div>
  <div class="ctrl play" id="playBtn" onclick="togglePlay()">10148</div>
  <div class="ctrl" onclick="next()">10148</div>
  <div id="progress" onclick="seek(event)"><div id="progressFill"></div></div>
  <div class="ctrl" onclick="loadLyrics()">Load</div>
</div>
<script>
const canvas=document.getElementById('bg');const ctx=canvas.getContext('2d');
canvas.width=innerWidth;canvas.height=innerHeight;

const demoLyrics=[
  {t:0,text:"[Desktop Karaoke]"},
  {t:3,text:"Floating lyrics sync with your music"},
  {t:6,text:"Watch them flow across your screen"},
  {t:9,text:"Like words on a river of sound"},
  {t:12,text:"The bass drops and the lights go down"},
  {t:15,text:"Your desktop becomes the stage"},
  {t:18,text:"Every keystroke sets the pace"},
  {t:21,text:"The music flows through every pixel"},
  {t:24,text:"Your PC transforms into a concert hall"},
  {t:27,text:"Let the rhythm take control"},
  {t:30,text:"Feel the beat inside your soul"},
  {t:33,text:"The speakers shake the walls around"},
  {t:36,text:"As melodies fill up the sound"},
  {t:39,text:"The harmony of code and art"},
  {t:42,text:"Creates something from the heart"},
  {t:45,text:"Your desktop sings a new song"},
  {t:48,text:"Where technology and music belong"},
];

let lyrics=demoLyrics;let currentLine=0;let playing=false;let elapsed=0;let lastTime=0;
let particles=[];

function drawBg(){
  ctx.fillStyle='rgba(3,8,20,0.1)';ctx.fillRect(0,0,canvas.width,canvas.height);
  const time=elapsed*0.5;
  for(let i=0;i<50;i++){
    const x=(Math.sin(time+i*0.3)*0.5+0.5)*canvas.width;
    const y=(Math.cos(time+i*0.2)*0.5+0.5)*canvas.height;
    ctx.beginPath();ctx.arc(x,y,1+Math.sin(time+i)*0.5,0,Math.PI*2);
    ctx.fillStyle=`hsla(${180+i*3},80%,50%,0.1)`;ctx.fill();
  }
  requestAnimationFrame(drawBg);
}
drawBg();

function renderLyrics(){
  const box=document.getElementById('lyrics');
  box.innerHTML=lyrics.map((l,i)=>{
    let cls='line future';
    if(i<currentLine)cls='line past';
    else if(i===currentLine)cls='line current';
    return '<div class="'+cls+'">'+l.text+'</div>';
  }).join('');
}

function update(){
  if(playing){
    const now=Date.now();
    elapsed+=(now-lastTime)/1000;lastTime=now;
    while(currentLine<lyrics.length-1&&lyrics[currentLine+1].t<=elapsed)currentLine++;
    document.getElementById('progressFill').style.width=(elapsed/lyrics[lyrics.length-1].t*100)+'%';
    renderLyrics();
  }
  requestAnimationFrame(update);
}
function togglePlay(){playing=!playing;if(playing)lastTime=Date.now();document.getElementById('playBtn').innerHTML=playing?'10074':'10148'}
function prev(){elapsed=Math.max(0,elapsed-5);currentLine=0;while(currentLine<lyrics.length-1&&lyrics[currentLine+1].t<=elapsed)currentLine++;renderLyrics()}
function next(){if(currentLine<lyrics.length-1){elapsed=lyrics[currentLine+1].t;currentLine++;renderLyrics()}}
function seek(e){const r=e.target.getBoundingClientRect();const pct=(e.clientX-r.left)/r.width;elapsed=pct*lyrics[lyrics.length-1].t;currentLine=0;while(currentLine<lyrics.length-1&&lyrics[currentLine+1].t<=elapsed)currentLine++;renderLyrics()}
function loadLyrics(){document.getElementById('songTitle').textContent='Desktop Karaoke Demo';document.getElementById('songArtist').textContent='Daniela OS';renderLyrics()}
loadLyrics();update();
</script></body></html>
"""

if __name__ == "__main__":
    print("[System 49] Desktop Karaoke starting on port 5059...")
    app.run(host="0.0.0.0", port=5059, debug=False)
