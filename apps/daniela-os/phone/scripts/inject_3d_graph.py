import os

nexus_path = os.path.expanduser("~/aig-monorepo/apps/nexus-command-center/nexus_dashboard.py")

with open(nexus_path, encoding="utf-8") as f:
    code = f.read()

# 1. Inyectar endpoint /api/graph-data en do_GET si no existe
if "/api/graph-data" not in code:
    old_target = 'elif parsed_path == "/api/finops-status":'
    new_target = """elif parsed_path == "/api/graph-data":
            try:
                nodes_data = [{"id": n, "name": data.get("label", n), "val": data.get("access_count", 1)} for n, data in self.cache._nodes.items()]
                links_data = []
                for n, data in self.cache._nodes.items():
                    for target in data.get("connections", []):
                        if target in self.cache._nodes:
                            links_data.append({"source": n, "target": target})
                respond_json({"nodes": nodes_data, "links": links_data})
            except Exception as e:
                respond_json({"nodes": [], "links": []})
        elif parsed_path == "/api/finops-status":"""
    code = code.replace(old_target, new_target)

# 2. Inyectar HTML y JS para 3D Force Graph si HTML_TEMPLATE está presente
graph_3d_script = """
<!-- 3D Graph Container -->
<div id="3d-graph" style="width: 100%; height: 400px; background: #0d1117; border-radius: 8px; margin-top: 15px;"></div>
<script src="https://unpkg.com/3d-force-graph"></script>
<script>
  fetch('/api/graph-data')
    .then(res => res.json())
    .then(data => {
      if (data.nodes && data.nodes.length > 0) {
        const Graph = ForceGraph3D()
          (document.getElementById('3d-graph'))
            .graphData(data)
            .nodeLabel('name')
            .nodeColor(node => node.val > 2 ? '#00ffcc' : '#58a6ff')
            .nodeRelSize(4)
            .linkWidth(1)
            .linkOpacity(0.4)
            .backgroundColor('#0d1117');
      }
    });
</script>
"""

if "</body>" in code and "3d-force-graph" not in code:
    code = code.replace("</body>", graph_3d_script + "\n</body>")

with open(nexus_path, "w", encoding="utf-8") as f:
    f.write(code)

print("✨ [Nexus 3D Engine] Endpoint /api/graph-data y visor WebGL inyectados con éxito.")
