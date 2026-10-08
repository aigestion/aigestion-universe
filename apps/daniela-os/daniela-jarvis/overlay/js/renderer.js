/**
 * Daniela OS — Jarvis Desktop Overlay
 * Shared Three.js Renderer + Camera
 * Single renderer shared by all 6 modes
 */

class JarvisRenderer {
  constructor(canvasId) {
    this.canvas = document.getElementById(canvasId);
    if (!this.canvas) return;

    this.scene = new THREE.Scene();
    this.camera = new THREE.PerspectiveCamera(50, window.innerWidth / window.innerHeight, 0.1, 2000);
    this.renderer = new THREE.WebGLRenderer({
      canvas: this.canvas,
      alpha: true,
      antialias: true,
      powerPreference: 'high-performance'
    });

    this.modes = {};
    this.activeMode = null;
    this.activeModeName = null;
    this.time = 0;
    this.mouse = { x: 0, y: 0 };
    this.targetCamZ = 5;

    this.init();
  }

  init() {
    this.renderer.setSize(window.innerWidth, window.innerHeight);
    this.renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    this.renderer.setClearColor(0x000000, 0);

    this.camera.position.z = this.targetCamZ;

    window.addEventListener('resize', () => this.onResize());
    window.addEventListener('mousemove', (e) => {
      this.mouse.x = (e.clientX / window.innerWidth) * 2 - 1;
      this.mouse.y = -(e.clientY / window.innerHeight) * 2 + 1;
    });

    this.animate();
  }

  onResize() {
    this.camera.aspect = window.innerWidth / window.innerHeight;
    this.camera.updateProjectionMatrix();
    this.renderer.setSize(window.innerWidth, window.innerHeight);
  }

  registerMode(name, modeInstance) {
    this.modes[name] = modeInstance;
  }

  switchMode(name) {
    // Hide current mode
    if (this.activeMode && this.modes[this.activeModeName]) {
      this.modes[this.activeModeName].hide();
    }

    // Show new mode
    this.activeModeName = name;
    this.activeMode = this.modes[name];
    if (this.activeMode) {
      this.activeMode.show();
    }
  }

  animate() {
    requestAnimationFrame(() => this.animate());
    this.time += 0.016;

    if (this.activeMode) {
      this.activeMode.update(this.time, this.mouse);
    }

    // Smooth camera zoom
    this.camera.position.z += (this.targetCamZ - this.camera.position.z) * 0.05;

    this.renderer.render(this.scene, this.camera);
  }

  setCameraZoom(z) {
    this.targetCamZ = z;
  }

  getScene() { return this.scene; }
  getCamera() { return this.camera; }
  getTime() { return this.time; }
  getMouse() { return this.mouse; }
}

window.JarvisRenderer = JarvisRenderer;
