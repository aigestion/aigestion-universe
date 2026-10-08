"""
System 47: VR Desktop
3D virtual desktop environment
"""

from flask import Flask

app = Flask(__name__)


@app.route("/")
def index():
    return VR_HTML


VR_HTML = r"""
<!DOCTYPE html>
<html><head><meta charset="UTF-8"><title>VR Desktop</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
html,body{width:100vw;height:100vh;overflow:hidden;background:#030814;font-family:'Rajdhani',sans-serif}
canvas{position:fixed;top:0;left:0}
#controls{position:fixed;bottom:20px;left:50%;transform:translateX(-50%);z-index:10;display:flex;gap:8px}
.ctrl{background:rgba(3,8,20,0.8);border:1px solid rgba(0,240,255,0.2);border-radius:8px;padding:8px 14px;cursor:pointer;font-size:11px;color:#00f0ff;font-family:'Orbitron',monospace;letter-spacing:1px}
.ctrl:hover{background:rgba(0,240,255,0.1)}
.ctrl.active{border-color:#ff0055;color:#ff0055}
#info{position:fixed;top:20px;left:20px;z-index:10;font-family:'Share Tech Mono',monospace;font-size:10px;color:#64748b;background:rgba(3,8,20,0.8);padding:8px;border-radius:6px;border:1px solid rgba(0,240,255,0.12)}
#minimap{position:fixed;top:20px;right:20px;z-index:10;width:120px;height:120px;background:rgba(3,8,20,0.8);border:1px solid rgba(0,240,255,0.2);border-radius:8px;overflow:hidden}
</style></head><body>
<canvas id="c"></canvas>
<div id="controls">
  <div class="ctrl active" onclick="setView('orbit')">ORBIT</div>
  <div class="ctrl" onclick="setView('first')">FIRST PERSON</div>
  <div class="ctrl" onclick="setView('top')">TOP DOWN</div>
  <div class="ctrl" onclick="toggleWire()">WIREFRAME</div>
  <div class="ctrl" onclick="toggleGrid()">GRID</div>
</div>
<div id="info">FPS: <span id="fps">60</span> | Objects: <span id="objCount">0</span> | Mode: <span id="mode">Orbit</span></div>
<canvas id="minimap"></canvas>
<script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
<script>
const canvas=document.getElementById('c');
const scene=new THREE.Scene();
const camera=new THREE.PerspectiveCamera(60,innerWidth/innerHeight,0.1,1000);
const renderer=new THREE.WebGLRenderer({canvas,antialias:true});
renderer.setSize(innerWidth,innerHeight);renderer.setPixelRatio(Math.min(devicePixelRatio,2));
scene.background=new THREE.Color(0x030814);scene.fog=new THREE.FogExp2(0x030814,0.02);
const ambient=new THREE.AmbientLight(0x1a1a3e,0.4);scene.add(ambient);
const dirLight=new THREE.DirectionalLight(0x00f0ff,0.6);dirLight.position.set(5,10,5);scene.add(dirLight);
const pointLight=new THREE.PointLight(0xff0055,0.5,20);pointLight.position.set(-3,3,-3);scene.add(pointLight);

const objects=[];
const grid=new THREE.GridHelper(30,30,0x00f0ff,0x0a0a2e);scene.add(grid);

const roomGeo=new THREE.BoxGeometry(10,6,10);
const roomMat=new THREE.MeshPhongMaterial({color:0x0a0a2e,transparent:true,opacity:0.2,side:THREE.DoubleSide});
const room=new THREE.Mesh(roomGeo,roomMat);room.position.y=3;scene.add(room);

function createScreen(x,y,z,w,h,color,label){
  const geo=new THREE.BoxGeometry(w,h,0.05);
  const mat=new THREE.MeshPhongMaterial({color,emissive:color,emissiveIntensity:0.2});
  const mesh=new THREE.Mesh(geo,mat);mesh.position.set(x,y,z);scene.add(mesh);
  const edge=new THREE.EdgesGeometry(geo);
  const line=new THREE.LineSegments(edge,new THREE.LineBasicMaterial({color:0x00f0ff,transparent:true,opacity:0.4}));
  line.position.copy(mesh.position);scene.add(line);
  objects.push(mesh);
}

createScreen(0,3.5,-4.9,8,4,0x0a1a3e,'Main Monitor');
createScreen(-4.9,3,-2,0.05,3,3,0x0a1a3e,'Left Panel');
createScreen(4.9,3,-2,0.05,3,3,0x0a1a3e,'Right Panel');
createScreen(0,1,-4.9,4,0.3,0x0a1a3e,'Desk');
createScreen(-1,0.5,-3,0.3,0.3,0x0a1a3e,'PC Tower');
createScreen(1,0.5,-3,0.3,0.3,0x0a1a3e,'PC Tower 2');

const particleGeo=new THREE.BufferGeometry();
const positions=new Float32Array(300);
for(let i=0;i<300;i++){positions[i]=(Math.random()-0.5)*20}
particleGeo.setAttribute('position',new THREE.BufferAttribute(positions,3));
const particleMat=new THREE.PointsMaterial({color:0x00f0ff,size:0.05,transparent:true,opacity:0.5});
const particles=new THREE.Points(particleGeo,particleMat);scene.add(particles);

let viewMode='orbit';let wireframe=false;let showGrid=true;
let mouseX=0,mouseY=0;let cameraAngle=0;let cameraRadius=12;

function setView(v){
  viewMode=v;document.querySelectorAll('.ctrl').forEach(c=>c.classList.remove('active'));
  event.target.classList.add('active');
  document.getElementById('mode').textContent=v.charAt(0).toUpperCase()+v.slice(1);
}
function toggleWire(){wireframe=!wireframe;scene.traverse(c=>{if(c.material){c.material.wireframe=wireframe}})}
function toggleGrid(){showGrid=!showGrid;grid.visible=showGrid}
document.onmousemove=e=>{mouseX=(e.clientX/innerWidth)*2-1;mouseY=(e.clientY/innerHeight)*2-1};
document.onwheel=e=>{cameraRadius=Math.max(5,Math.min(20,cameraRadius+e.deltaY*0.01))};

let time=0;let frameCount=0;let lastFps=0;let fpsTimer=0;
function animate(){
  requestAnimationFrame(animate);time+=0.01;frameCount++;
  if(time-fpsTimer>1){document.getElementById('fps').textContent=frameCount;frameCount=0;fpsTimer=time}

  if(viewMode==='orbit'){
    cameraAngle+=0.003;
    camera.position.x=Math.sin(cameraAngle)*cameraRadius;
    camera.position.z=Math.cos(cameraAngle)*cameraRadius;
    camera.position.y=6+mouseY*2;
  }else if(viewMode==='first'){
    camera.position.set(mouseX*4,3,-2);camera.lookAt(0,3,-5);
  }else{
    camera.position.set(0,15,0);camera.lookAt(0,0,0);
  }

  pointLight.position.x=Math.sin(time*0.5)*5;pointLight.position.z=Math.cos(time*0.5)*5;
  particles.rotation.y=time*0.1;
  document.getElementById('objCount').textContent=objects.length;
  renderer.render(scene,camera);
}
animate();
</script></body></html>
"""

if __name__ == "__main__":
    print("[System 47] VR Desktop starting on port 5057...")
    app.run(host="0.0.0.0", port=5057, debug=False)
