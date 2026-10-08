"""
System 46: Stream Overlay
Stream overlay with alerts, chat, and widgets
"""

from flask import Flask

app = Flask(__name__)


@app.route("/")
def index():
    return STREAM_HTML


STREAM_HTML = r"""
<!DOCTYPE html>
<html><head><meta charset="UTF-8"><title>Stream Overlay</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
html,body{width:100vw;height:100vh;overflow:hidden;background:transparent;font-family:'Rajdhani',sans-serif}
#alert{position:fixed;top:40px;left:50%;transform:translateX(-50%);z-index:100;background:rgba(3,8,20,0.9);border:2px solid #ff0055;border-radius:14px;padding:16px 32px;display:none;text-align:center;animation:fadeIn 0.5s,glow 2s infinite}
@keyframes fadeIn{from{opacity:0;transform:translateX(-50%) translateY(-20px)}to{opacity:1;transform:translateX(-50%) translateY(0)}}
@keyframes glow{0%,100%{box-shadow:0 0 20px rgba(255,0,85,0.3)}50%{box-shadow:0 0 40px rgba(255,0,85,0.6)}}
.alert-icon{font-size:28px}
.alert-title{font-family:'Orbitron',monospace;color:#ff0055;font-size:16px;letter-spacing:2px;margin-top:4px}
.alert-msg{color:#e2e8f0;font-size:13px;margin-top:4px}
#chat{position:fixed;bottom:20px;left:20px;width:300px;z-index:10;background:rgba(3,8,20,0.8);border:1px solid rgba(0,240,255,0.2);border-radius:10px;padding:10px;max-height:200px;overflow-y:auto}
.chat-msg{font-size:11px;padding:3px 0;border-bottom:1px solid rgba(0,240,255,0.05)}
.chat-user{color:#00f0ff;font-weight:bold}
.chat-text{color:#e2e8f0}
#widgets{position:fixed;top:20px;right:20px;z-index:10;display:flex;flex-direction:column;gap:8px}
.widget{background:rgba(3,8,20,0.8);border:1px solid rgba(0,240,255,0.2);border-radius:8px;padding:8px 12px}
.widget-label{font-family:'Orbitron',monospace;font-size:8px;color:#00f0ff;letter-spacing:1px}
.widget-value{font-family:'Share Tech Mono',monospace;font-size:16px;color:#e2e8f0}
#scene{position:fixed;bottom:20px;right:20px;z-index:10;background:rgba(3,8,20,0.8);border:1px solid rgba(0,240,255,0.2);border-radius:8px;padding:8px;display:flex;gap:6px}
.scene-btn{width:24px;height:24px;border-radius:4px;border:1px solid rgba(0,240,255,0.2);background:rgba(0,240,255,0.05);cursor:pointer;color:#00f0ff;font-size:9px;display:flex;align-items:center;justify-content:center}
.scene-btn.active{background:rgba(0,240,255,0.2);border-color:#00f0ff}
</style></head><body>
<div id="alert"><div class="alert-icon" id="alertIcon"></div><div class="alert-title" id="alertTitle"></div><div class="alert-msg" id="alertMsg"></div></div>
<div id="chat" id="chatBox"></div>
<div id="widgets">
  <div class="widget"><div class="widget-label">VIEWERS</div><div class="widget-value" id="viewers">0</div></div>
  <div class="widget"><div class="widget-label">DURATION</div><div class="widget-value" id="duration">00:00:00</div></div>
  <div class="widget"><div class="widget-label">FPS</div><div class="widget-value" id="fps">60</div></div>
</div>
<div id="scene">
  <div class="scene-btn active">1</div><div class="scene-btn">2</div><div class="scene-btn">3</div>
</div>
<script>
let startTime=Date.now();
const alerts=[
  {icon:'128142',title:'NEW FOLLOWER',msg:'user123 just followed!'},
  {icon:'128176',title:'NEW SUBSCRIBER',msg:'pro_user subscribed for 3 months!'},
  {icon:'11088',title:'DONATION',msg:'supporter donated $10.00!'},
  {icon:'127873',title:'RAID',msg:'streamer500 raided with 150 viewers!'},
  {icon:'128640',title:'NEW CHEER',msg:'user456 cheered 500 bits!'},
];
let alertIndex=0;
function showAlert(){
  const a=alerts[alertIndex%alerts.length];
  document.getElementById('alertIcon').textContent=String.fromCodePoint(parseInt(a.icon));
  document.getElementById('alertTitle').textContent=a.title;
  document.getElementById('alertMsg').textContent=a.msg;
  document.getElementById('alert').style.display='block';
  setTimeout(()=>{document.getElementById('alert').style.display='none'},5000);
  alertIndex++;
}
setInterval(showAlert,12000);
setTimeout(showAlert,2000);
const chatUsers=['xGamer42','pro_streamer','night_owl','code_wizard','pixel_queen','music_lover','tech_fan','art_maker'];
const chatMsgs=['Love the stream!','That was amazing','GG!','So cool','Hype!','Can you play my song?','First time here, love it'];
function addChat(){
  const box=document.getElementById('chat');
  const user=chatUsers[Math.floor(Math.random()*chatUsers.length)];
  const msg=chatMsgs[Math.floor(Math.random()*chatMsgs.length)];
  const div=document.createElement('div');div.className='chat-msg';
  div.innerHTML='<span class="chat-user">'+user+':</span> <span class="chat-text">'+msg+'</span>';
  box.appendChild(div);box.scrollTop=box.scrollHeight;
  if(box.children.length>30)box.removeChild(box.firstChild);
}
setInterval(addChat,3000+Math.random()*4000);
function updateStats(){
  const elapsed=Math.floor((Date.now()-startTime)/1000);
  const h=String(Math.floor(elapsed/3600)).padStart(2,'0');
  const m=String(Math.floor((elapsed%3600)/60)).padStart(2,'0');
  const s=String(elapsed%60).padStart(2,'0');
  document.getElementById('duration').textContent=h+':'+m+':'+s;
  document.getElementById('viewers').textContent=Math.floor(50+Math.random()*30);
  document.getElementById('fps').textContent=Math.floor(58+Math.random()*4);
}
setInterval(updateStats,1000);
document.querySelectorAll('.scene-btn').forEach(b=>b.onclick=function(){document.querySelectorAll('.scene-btn').forEach(x=>x.classList.remove('active'));this.classList.add('active')});
</script></body></html>
"""

if __name__ == "__main__":
    print("[System 46] Stream Overlay starting on port 5056...")
    app.run(host="0.0.0.0", port=5056, debug=False)
