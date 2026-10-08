/**
 * Daniela OS — Jarvis Desktop Overlay
 * Mode Manager — Switches between 6 visualization modes
 */

class ModeManager {
  constructor(renderer) {
    this.renderer = renderer;
    this.modes = {};
    this.currentMode = null;
    this.transitioning = false;
    this.onModeChange = null;

    this.registerDefaults();
  }

  registerDefaults() {
    const scene = this.renderer.getScene();

    this.register('arc-reactor', new ArcReactorMode(scene));
    this.register('globe', new GlobeMode(scene));
    this.register('neural-core', new NeuralCoreMode(scene));
    this.register('planetary', new PlanetaryMode(scene));
    this.register('knowledge-graph', new KnowledgeGraphMode(scene));
    this.register('geolocation', new GeolocationMode(scene));

    // Start with arc reactor
    this.switchTo('arc-reactor');
  }

  register(name, modeInstance) {
    this.modes[name] = modeInstance;
    this.renderer.registerMode(name, modeInstance);
  }

  switchTo(name) {
    if (this.transitioning || name === this.currentMode) return;
    if (!this.modes[name]) return;

    this.transitioning = true;

    // Fade out
    this.renderer.canvas.style.transition = 'opacity 0.3s';
    this.renderer.canvas.style.opacity = '0';

    setTimeout(() => {
      // Switch
      this.renderer.switchMode(name);
      this.currentMode = name;

      // Fade in
      this.renderer.canvas.style.opacity = '1';

      setTimeout(() => {
        this.transitioning = false;
        this.renderer.canvas.style.transition = '';
      }, 300);

      if (this.onModeChange) this.onModeChange(name);
    }, 300);
  }

  nextMode() {
    const names = Object.keys(this.modes);
    const idx = names.indexOf(this.currentMode);
    const next = names[(idx + 1) % names.length];
    this.switchTo(next);
  }

  getModeNames() {
    return Object.keys(this.modes);
  }

  getCurrentMode() {
    return this.currentMode;
  }
}

window.ModeManager = ModeManager;
