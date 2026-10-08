"""
System 3: 3D File Galaxy
File manager as a 3D galaxy - folders are stars, files are orbiting planets
"""

from pathlib import Path

from flask import Flask, jsonify, request

app = Flask(__name__)


@app.route("/api/galaxy/scan", methods=["POST"])
def scan_directory():
    data = request.json or {}
    root = data.get("path", str(Path.home()))
    max_depth = data.get("depth", 2)

    nodes = []
    edges = []

    def scan(path, depth=0, parent_id=None):
        if depth > max_depth:
            return
        try:
            items = list(Path(path).iterdir())
        except PermissionError:
            return

        node_id = str(Path(path).name or path)
        nodes.append(
            {
                "id": node_id,
                "name": str(Path(path).name),
                "path": str(path),
                "type": "folder" if Path(path).is_dir() else "file",
                "size": sum(f.stat().st_size for f in Path(path).rglob("*") if f.is_file())
                if Path(path).is_dir()
                else (Path(path).stat().st_size if Path(path).is_file() else 0),
                "children": len(items) if Path(path).is_dir() else 0,
            }
        )

        if parent_id:
            edges.append({"from": parent_id, "to": node_id})

        if Path(path).is_dir():
            for item in items[:20]:  # Limit to 20 items per folder
                if not item.name.startswith("."):
                    scan(item, depth + 1, node_id)

    scan(root)
    return jsonify({"nodes": nodes, "edges": edges, "root": root})


GALAXY_HTML = r"""
<!DOCTYPE html>
<html><head><meta charset="UTF-8"><title>3D File Galaxy</title>
<style>
* { margin:0; padding:0; box-sizing:border-box; }
html,body { width:100vw; height:100vh; overflow:hidden; background:#030814; font-family:'Share Tech Mono',monospace; }
canvas { position:fixed; top:0; left:0; z-index:0; }
#ui { position:fixed; top:20px; left:20px; z-index:10; }
#path-input { background:rgba(0,240,255,0.05); border:1px solid rgba(0,240,255,0.3); color:#00f0ff; padding:8px 12px; width:400px; font-family:inherit; font-size:12px; border-radius:6px; }
#path-input:focus { outline:none; border-color:#00f0ff; box-shadow:0 0 15px rgba(0,240,255,0.2); }
#scan-btn { background:rgba(0,240,255,0.1); border:1px solid #00f0ff; color:#00f0ff; padding:8px 16px; margin-left:8px; border-radius:6px; cursor:pointer; font-family:inherit; }
#scan-btn:hover { background:rgba(0,240,255,0.2); }
#info { position:fixed; bottom:20px; left:20px; z-index:10; font-size:11px; color:rgba(0,240,255,0.5); }
#tooltip { position:fixed; display:none; background:rgba(3,8,20,0.9); border:1px solid #00f0ff; padding:8px 12px; border-radius:8px; font-size:11px; color:#e2e8f0; pointer-events:none; z-index:100; max-width:300px; }
</style></head><body>
<div id="ui">
  <input id="path-input" value="C:\Users\Alejandro" placeholder="Enter path...">
  <button id="scan-btn" onclick="scan()">Scan</button>
</div>
<div id="info">3D File Galaxy | Click nodes to navigate | Scroll to zoom</div>
<div id="tooltip"></div>
<canvas id="c"></canvas>
<script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
<script>
const canvas = document.getElementById('c');
const scene = new THREE.Scene();
const camera = new THREE.PerspectiveCamera(50, window.innerWidth/window.innerHeight, 0.1, 2000);
const renderer = new THREE.WebGLRenderer({canvas, antialias:true, alpha:true});
renderer.setSize(window.innerWidth, window.innerHeight);
renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
camera.position.z = 50;

let galaxyGroup = new THREE.Group();
scene.add(galaxyGroup);
const nodeMeshes = [];
const nodeData = [];

async function scan() {
  const path = document.getElementById('path-input').value;
  const resp = await fetch('/api/galaxy/scan', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({path, depth:2})});
  const data = await resp.json();
  buildGalaxy(data);
}

function buildGalaxy(data) {
  // Clear old
  while(galaxyGroup.children.length) galaxyGroup.remove(galaxyGroup.children[0]);
  nodeMeshes.length = 0; nodeData.length = 0;

  const nodes = data.nodes;
  const maxChildren = Math.max(...nodes.map(n=>n.children||1));

  nodes.forEach((node, i) => {
    const size = Math.max(0.3, Math.min(3, (node.size||1000) / 1000000));
    const isFolder = node.type === 'folder';

    // Position in spiral
    const angle = i * 0.5;
    const radius = Math.sqrt(i) * 3;
    const x = Math.cos(angle) * radius;
    const y = (Math.random()-0.5) * radius * 0.3;
    const z = Math.sin(angle) * radius;

    const geo = isFolder ?
      new THREE.OctahedronGeometry(size) :
      new THREE.SphereGeometry(size * 0.5, 8, 8);

    const hue = isFolder ? 190 : (30 + (node.size%360));
    const mat = new THREE.MeshBasicMaterial({
      color: new THREE.Color(`hsl(${hue}, 70%, ${isFolder?60:40}%)`),
      transparent: true, opacity: isFolder ? 0.8 : 0.6
    });

    const mesh = new THREE.Mesh(geo, mat);
    mesh.position.set(x, y, z);
    mesh.userData = { node, index: i };

    // Glow for folders
    if (isFolder) {
      const glowGeo = new THREE.SphereGeometry(size * 2, 8, 8);
      const glowMat = new THREE.MeshBasicMaterial({color: 0x00f0ff, transparent:true, opacity:0.08});
      mesh.add(new THREE.Mesh(glowGeo, glowMat));
    }

    galaxyGroup.add(mesh);
    nodeMeshes.push(mesh);
    nodeData.push(node);
  });

  // Center core
  const coreGeo = new THREE.SphereGeometry(1, 16, 16);
  const coreMat = new THREE.MeshBasicMaterial({color:0x00f0ff, transparent:true, opacity:0.3});
  const core = new THREE.Mesh(coreGeo, coreMat);
  galaxyGroup.add(core);
}

// Mouse interaction
let mouse = new THREE.Vector2();
let raycaster = new THREE.Raycaster();
canvas.addEventListener('mousemove', e => {
  mouse.x = (e.clientX/window.innerWidth)*2-1;
  mouse.y = -(e.clientY/window.innerHeight)*2+1;
});

canvas.addEventListener('click', e => {
  raycaster.setFromCamera(mouse, camera);
  const hits = raycaster.intersectObjects(nodeMeshes);
  if (hits.length > 0) {
    const node = hits[0].object.userData.node;
    if (node.type === 'folder') {
      document.getElementById('path-input').value = node.path;
      scan();
    }
  }
});

let camAngle = 0, camRadius = 50;
canvas.addEventListener('wheel', e => {
  camRadius = Math.max(10, Math.min(200, camRadius + e.deltaY * 0.05));
});

function animate() {
  requestAnimationFrame(animate);
  camAngle += 0.002;
  camera.position.x = Math.cos(camAngle) * camRadius;
  camera.position.z = Math.sin(camAngle) * camRadius;
  camera.position.y = camRadius * 0.3;
  camera.lookAt(0, 0, 0);

  galaxyGroup.rotation.y += 0.001;

  // Hover tooltip
  raycaster.setFromCamera(mouse, camera);
  const hits = raycaster.intersectObjects(nodeMeshes);
  const tooltip = document.getElementById('tooltip');
  if (hits.length > 0) {
    const node = hits[0].object.userData.node;
    tooltip.style.display = 'block';
    tooltip.style.left = (event?.clientX||0) + 15 + 'px';
    tooltip.style.top = (event?.clientY||0) + 15 + 'px';
    const sizeMB = ((node.size||0)/1048576).toFixed(1);
    tooltip.innerHTML = `<b>${node.name}</b><br>${node.type} | ${sizeMB} MB | ${node.children||0} items`;
  } else {
    tooltip.style.display = 'none';
  }

  renderer.render(scene, camera);
}
animate();
scan();
</script></body></html>
"""


@app.route("/")
def index():
    return GALAXY_HTML


if __name__ == "__main__":
    print("[System 3] 3D File Galaxy starting on port 5012...")
    app.run(host="0.0.0.0", port=5012, debug=False)
