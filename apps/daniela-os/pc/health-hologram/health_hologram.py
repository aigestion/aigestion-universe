"""
System 5: System Health Hologram
Real-time 3D visualization of PC health as a living hologram
"""

import time

import psutil
from flask import Flask, jsonify

app = Flask(__name__)


@app.route("/")
def index():
    return HOLOGRAM_HTML


@app.route("/api/health/realtime")
def realtime():
    cpu = psutil.cpu_percent(interval=0.1)
    mem = psutil.virtual_memory()
    disk = psutil.disk_usage("/")
    net = psutil.net_io_counters()
    temps = {}
    try:
        for temp in psutil.sensors_temperatures().values():
            if temp:
                temps[temp[0].label or "core"] = temp[0].current
    except Exception:
        pass

    procs = []
    for p in psutil.process_iter(["pid", "name", "cpu_percent", "memory_percent"]):
        try:
            info = p.info
            procs.append(
                {
                    "pid": info["pid"],
                    "name": info["name"][:20],
                    "cpu": round(info["cpu_percent"] or 0, 1),
                    "mem": round(info["memory_percent"] or 0, 1),
                }
            )
        except Exception:
            pass
    procs.sort(key=lambda x: x["cpu"], reverse=True)

    return jsonify(
        {
            "cpu": cpu,
            "memory": mem.percent,
            "disk": disk.percent,
            "net_up": net.bytes_sent,
            "net_down": net.bytes_recv,
            "temps": temps,
            "top_processes": procs[:8],
            "uptime": time.time() - psutil.boot_time(),
        }
    )


HOLOGRAM_HTML = r"""
<!DOCTYPE html>
<html><head><meta charset="UTF-8"><title>System Health Hologram</title>
<style>
* { margin:0; padding:0; box-sizing:border-box; }
html,body { width:100vw; height:100vh; overflow:hidden; background:#030814; }
canvas { position:fixed; top:0; left:0; z-index:0; }
#hud { position:fixed; top:20px; right:20px; z-index:10; font-family:'Share Tech Mono',monospace; }
.hud-card { background:rgba(3,8,20,0.85); border:1px solid rgba(0,240,255,0.2); border-radius:10px; padding:10px 14px; margin-bottom:8px; min-width:180px; }
.hud-label { font-size:9px; color:#00f0ff; letter-spacing:2px; text-transform:uppercase; }
.hud-value { font-size:22px; font-weight:700; color:#e2e8f0; font-family:'Orbitron',monospace; }
.hud-bar { width:100%; height:4px; background:rgba(0,240,255,0.1); border-radius:2px; margin-top:4px; }
.hud-bar-fill { height:100%; border-radius:2px; transition:width 0.5s; }
#processes { position:fixed; bottom:20px; left:20px; z-index:10; font-family:'Share Tech Mono',monospace; font-size:10px; color:#64748b; }
.proc-row { display:flex; gap:12px; padding:2px 0; }
.proc-name { width:100px; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
</style></head><body>
<canvas id="c"></canvas>
<div id="hud"></div>
<div id="processes"></div>
<script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
<script>
const canvas = document.getElementById('c');
const scene = new THREE.Scene();
const camera = new THREE.PerspectiveCamera(50, innerWidth/innerHeight, 0.1, 1000);
const renderer = new THREE.WebGLRenderer({canvas, antialias:true, alpha:true});
renderer.setSize(innerWidth, innerHeight);
renderer.setPixelRatio(Math.min(devicePixelRatio, 2));
camera.position.z = 6;

// Central orb (CPU = brain)
const coreGeo = new THREE.SphereGeometry(0.8, 32, 32);
const coreMat = new THREE.MeshBasicMaterial({color:0x00f0ff, transparent:true, opacity:0.4});
const core = new THREE.Mesh(coreGeo, coreMat);
scene.add(core);

// Rings for each metric
const ringMeshes = {};
['memory', 'disk', 'network'].forEach((name, i) => {
  const geo = new THREE.TorusGeometry(1.2 + i*0.3, 0.02, 8, 64);
  const mat = new THREE.MeshBasicMaterial({color: [0x8b5cf6, 0xf59e0b, 0x22c55e][i], transparent:true, opacity:0.5});
  const ring = new THREE.Mesh(geo, mat);
  ring.rotation.x = Math.PI/2 + i*0.3;
  ring.rotation.z = i*0.5;
  scene.add(ring);
  ringMeshes[name] = ring;
});

// Particles for processes
const PROC_COUNT = 50;
const procGeo = new THREE.BufferGeometry();
const procPos = new Float32Array(PROC_COUNT * 3);
for(let i=0; i<PROC_COUNT; i++) {
  const a = (i/PROC_COUNT)*Math.PI*2;
  const r = 1.5 + Math.random();
  procPos[i*3] = Math.cos(a)*r;
  procPos[i*3+1] = (Math.random()-0.5)*2;
  procPos[i*3+2] = Math.sin(a)*r;
}
procGeo.setAttribute('position', new THREE.BufferAttribute(procPos, 3));
const procMat = new THREE.PointsMaterial({color:0x00f0ff, size:0.04, transparent:true, opacity:0.6, blending:THREE.AdditiveBlending});
const procParticles = new THREE.Points(procGeo, procMat);
scene.add(procParticles);

let data = {};
async function fetchData() {
  try { data = await (await fetch('/api/health/realtime')).json(); updateHUD(); } catch(e) {}
}
setInterval(fetchData, 1000);

function updateHUD() {
  const cpuC = data.cpu > 80 ? '#ef4444' : data.cpu > 50 ? '#f59e0b' : '#00f0ff';
  const memC = data.memory > 85 ? '#ef4444' : data.memory > 70 ? '#f59e0b' : '#8b5cf6';
  const diskC = data.disk > 90 ? '#ef4444' : '#f59e0b';

  document.getElementById('hud').innerHTML =
    '<div class="hud-card"><div class="hud-label">CPU</div><div class="hud-value" style="color:'+cpuC+'">' + (data.cpu||0).toFixed(1) + '%</div>' +
    '<div class="hud-bar"><div class="hud-bar-fill" style="width:' + data.cpu + '%;background:'+cpuC+'"></div></div></div>' +
    '<div class="hud-card"><div class="hud-label">MEMORY</div><div class="hud-value" style="color:'+memC+'">' + (data.memory||0).toFixed(1) + '%</div>' +
    '<div class="hud-bar"><div class="hud-bar-fill" style="width:' + data.memory + '%;background:'+memC+'"></div></div></div>' +
    '<div class="hud-card"><div class="hud-label">DISK</div><div class="hud-value" style="color:'+diskC+'">' + (data.disk||0).toFixed(1) + '%</div>' +
    '<div class="hud-bar"><div class="hud-bar-fill" style="width:' + data.disk + '%;background:'+diskC+'"></div></div></div>';

  if(data.top_processes) {
    document.getElementById('processes').innerHTML = '<div style="color:#00f0ff;margin-bottom:4px">TOP PROCESSES</div>' +
      data.top_processes.map(p =>
        '<div class="proc-row"><span class="proc-name">' + p.name + '</span><span>' + p.cpu + '% CPU</span><span>' + p.mem + '% RAM</span></div>'
      ).join('');
  }
}

function animate() {
  requestAnimationFrame(animate);
  const t = Date.now()*0.001;

  // Core pulse
  core.material.opacity = 0.3 + Math.sin(t*2) * 0.1;
  core.scale.setScalar(1 + Math.sin(t*1.5) * 0.05);

  // CPU intensity
  const cpuNorm = (data.cpu||50)/100;
  core.material.color.setHSL(0.52 - cpuNorm*0.15, 0.8, 0.5);

  // Ring rotation based on metrics
  if(ringMeshes.memory) ringMeshes.memory.rotation.z = t * 0.3 * ((data.memory||50)/100);
  if(ringMeshes.disk) ringMeshes.disk.rotation.z = -t * 0.2 * ((data.disk||50)/100);
  if(ringMeshes.network) ringMeshes.network.rotation.z = t * 0.4;

  // Particle rotation
  procParticles.rotation.y += 0.003;

  renderer.render(scene, camera);
}
animate(); fetchData();
</script></body></html>
"""

if __name__ == "__main__":
    print("[System 5] System Health Hologram starting on port 5014...")
    app.run(host="0.0.0.0", port=5014, debug=False)
