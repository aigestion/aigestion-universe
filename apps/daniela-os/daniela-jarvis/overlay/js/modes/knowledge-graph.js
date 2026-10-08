/**
 * Daniela OS — Jarvis Desktop Overlay
 * Mode 5: Knowledge Graph
 * Force-directed 3D graph with glowing edges and active learning particles
 */

class KnowledgeGraphMode {
  constructor(scene) {
    this.scene = scene;
    this.group = new THREE.Group();
    this.nodes = [];
    this.edges = [];
    this.edgeParticles = [];
    this.nodeLabels = [];
    this.visible = false;
    this.time = 0;

    this.concepts = [
      { id: 'daniela', label: 'DANIELA', color: 0x00f0ff, size: 0.08, children: ['ai', 'systems', 'voice'] },
      { id: 'ai', label: 'IA', color: 0x8b5cf6, size: 0.06, children: ['llm', 'vision', 'nlp'] },
      { id: 'systems', label: 'SISTEMAS', color: 0x22c55e, size: 0.06, children: ['docker', 'deploy', 'monitor'] },
      { id: 'voice', label: 'VOZ', color: 0xef4444, size: 0.05, children: ['tts', 'stt'] },
      { id: 'llm', label: 'LLM', color: 0xa78bfa, size: 0.04, children: ['gpt', 'gemini', 'claude'] },
      { id: 'vision', label: 'VISION', color: 0xf59e0b, size: 0.04, children: ['camera', 'objects'] },
      { id: 'nlp', label: 'NLP', color: 0x14b8a6, size: 0.04, children: ['sentiment', 'translate'] },
      { id: 'docker', label: 'DOCKER', color: 0x0ea5e9, size: 0.04, children: ['containers'] },
      { id: 'deploy', label: 'DEPLOY', color: 0xf97316, size: 0.04, children: [] },
      { id: 'monitor', label: 'MONITOR', color: 0xec4899, size: 0.04, children: [] },
      { id: 'tts', label: 'TTS', color: 0x3b82f6, size: 0.03, children: [] },
      { id: 'stt', label: 'STT', color: 0x3b82f6, size: 0.03, children: [] },
      { id: 'gpt', label: 'GPT', color: 0x10b981, size: 0.03, children: [] },
      { id: 'gemini', label: 'GEMINI', color: 0x6366f1, size: 0.03, children: [] },
      { id: 'claude', label: 'CLAUDE', color: 0xeab308, size: 0.03, children: [] },
      { id: 'camera', label: 'CAMARA', color: 0xef4444, size: 0.03, children: [] },
      { id: 'objects', label: 'OBJETOS', color: 0xef4444, size: 0.03, children: [] },
      { id: 'sentiment', label: 'SENTIMIENTO', color: 0x14b8a6, size: 0.03, children: [] },
      { id: 'translate', label: 'TRADUCCION', color: 0x14b8a6, size: 0.03, children: [] },
      { id: 'containers', label: 'CONTAINERS', color: 0x0ea5e9, size: 0.03, children: [] },
    ];

    this.nodePositions = {};
    this._tempV = new THREE.Vector3();
    this.build();
  }

  build() {
    const ambient = new THREE.AmbientLight(0x404080, 0.4);
    this.group.add(ambient);

    // Place nodes in 3D space using simple force layout
    this.concepts.forEach((concept, idx) => {
      const phi = Math.acos(-1 + (2 * idx) / this.concepts.length);
      const theta = Math.sqrt(this.concepts.length * Math.PI) * phi;
      const r = concept.id === 'daniela' ? 0 : (1.0 + Math.random() * 0.3);

      const pos = new THREE.Vector3(
        r * Math.sin(phi) * Math.cos(theta),
        r * Math.sin(phi) * Math.sin(theta),
        r * Math.cos(phi)
      );

      this.nodePositions[concept.id] = pos;

      // Node mesh
      const geo = new THREE.SphereGeometry(concept.size, 12, 12);
      const mat = new THREE.MeshBasicMaterial({ color: concept.color, transparent: true, opacity: 0.8 });
      const mesh = new THREE.Mesh(geo, mat);
      mesh.position.copy(pos);
      this.group.add(mesh);

      // Glow
      const glowGeo = new THREE.SphereGeometry(concept.size * 2, 12, 12);
      const glowMat = new THREE.MeshBasicMaterial({ color: concept.color, transparent: true, opacity: 0.1 });
      const glow = new THREE.Mesh(glowGeo, glowMat);
      mesh.add(glow);

      // Label
      const label = document.createElement('div');
      label.className = 'graph-node-label';
      label.textContent = concept.label;
      label.style.cssText = `position:fixed;color:#e2e8f0;font-family:'Orbitron',monospace;font-size:8px;pointer-events:none;opacity:0.6;text-shadow:0 0 6px #${concept.color.toString(16).padStart(6, '0')};letter-spacing:1px;`;
      document.body.appendChild(label);

      this.nodes.push({ mesh, glow, label, concept, pos });
      this.nodeLabels.push({ el: label, pos });
    });

    // Edges
    this.concepts.forEach(concept => {
      const fromPos = this.nodePositions[concept.id];
      concept.children.forEach(childId => {
        const toPos = this.nodePositions[childId];
        if (!toPos) return;

        const lineGeo = new THREE.BufferGeometry().setFromPoints([fromPos, toPos]);
        const lineMat = new THREE.LineBasicMaterial({
          color: concept.color, transparent: true, opacity: 0.2
        });
        const line = new THREE.Line(lineGeo, lineMat);
        this.group.add(line);
        this.edges.push({ line, from: concept.id, to: childId, color: concept.color });
      });
    });

    // Edge particles (flowing along edges)
    this.edges.forEach(edge => {
      const geo = new THREE.SphereGeometry(0.01, 6, 6);
      const mat = new THREE.MeshBasicMaterial({
        color: edge.color, transparent: true, opacity: 0.8
      });
      const particle = new THREE.Mesh(geo, mat);
      this.group.add(particle);
      this.edgeParticles.push({
        mesh: particle, edge, progress: Math.random(), speed: 0.005 + Math.random() * 0.01
      });
    });

    this.scene.add(this.group);
    this.group.visible = false;
  }

  show() {
    this.visible = true;
    this.group.visible = true;
    this.nodeLabels.forEach(l => l.el.style.display = '');
  }

  hide() {
    this.visible = false;
    this.group.visible = false;
    this.nodeLabels.forEach(l => l.el.style.display = 'none');
  }

  update(time, mouse) {
    if (!this.visible) return;
    this.time = time;

    // Slow rotation
    this.group.rotation.y = time * 0.1;
    this.group.rotation.x = Math.sin(time * 0.05) * 0.05;

    // Pulse nodes
    this.nodes.forEach(n => {
      n.glow.scale.setScalar(1 + Math.sin(time * 2 + n.concept.size * 100) * 0.2);
    });

    // Animate edge particles
    this.edgeParticles.forEach(p => {
      p.progress += p.speed;
      if (p.progress >= 1) p.progress = 0;

      const fromPos = this.nodePositions[p.edge.from];
      const toPos = this.nodePositions[p.edge.to];
      if (!fromPos || !toPos) return;

      const t = p.progress;
      p.mesh.position.lerpVectors(fromPos, toPos, t);

      // Pulse opacity
      p.mesh.material.opacity = 0.3 + Math.sin(t * Math.PI) * 0.5;
    });

    // Edge opacity modulation
    this.edges.forEach((edge, i) => {
      edge.line.material.opacity = 0.15 + Math.sin(time * 1.5 + i * 0.3) * 0.05;
    });

    // Label projection
    const camera = this.scene.parent?.camera || window._jarvisCamera;
    if (camera) {
      this.nodeLabels.forEach(({ el, pos }) => {
        this._tempV.copy(pos);
        this._tempV.applyMatrix4(this.group.matrixWorld);
        this._tempV.project(camera);
        el.style.left = `${(this._tempV.x * 0.5 + 0.5) * window.innerWidth}px`;
        el.style.top = `${(-this._tempV.y * 0.5 + 0.5) * window.innerHeight}px`;
        el.style.transform = 'translate(-50%, -50%)';
        el.style.display = this._tempV.z < 1 ? '' : 'none';
      });
    }
  }
}

window.KnowledgeGraphMode = KnowledgeGraphMode;
