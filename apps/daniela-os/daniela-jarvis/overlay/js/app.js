/**
 * Daniela OS — Jarvis Desktop Overlay
 * Main Application Orchestrator
 * Integrates all 6 modes via ModeManager
 */

class JarvisApp {
  constructor() {
    this.renderer = null;
    this.modeManager = null;
    this.modeSwitcher = null;
    this.systemInfo = null;
    this.voice = null;
    this.commandPanel = null;
    this.isVisible = false;
    this.bootComplete = false;
  }

  async init() {
    console.log('[Jarvis] Initializing...');

    await this.runBootSequence();

    // Initialize shared renderer
    this.renderer = new JarvisRenderer('arcCanvas');
    window._jarvisCamera = this.renderer.getCamera();

    // Initialize mode manager (creates all 6 modes)
    this.modeManager = new ModeManager(this.renderer);

    // Initialize mode switcher UI
    this.modeSwitcher = new ModeSwitcher(this.modeManager);

    // Update mode switcher active state on mode change
    this.modeManager.onModeChange = (name) => {
      this.modeSwitcher.updateActive(name);
    };

    // Initialize widgets
    this.systemInfo = new SystemInfo();
    this.voice = new VoiceVisualizer();
    this.commandPanel = new CommandPanel();

    this.voice.onResult = (text) => {
      this.commandPanel.showChat();
      this.commandPanel.addChatMessage('user', text);
    };

    // Show overlay
    document.getElementById('bootScreen').style.display = 'none';
    document.getElementById('overlay').style.display = 'block';
    this.isVisible = true;
    this.bootComplete = true;

    console.log('[Jarvis] Ready — 6 modes available');
    console.log('[Jarvis] Press Tab for mode switcher | 1-6 direct mode select');

    this.connectToBackend();
  }

  async runBootSequence() {
    const lines = document.querySelectorAll('.boot-line');
    for (const line of lines) {
      const delay = parseInt(line.dataset.delay) || 0;
      await this.sleep(delay > 0 ? 200 : 0);
      line.style.animationDelay = `${delay}ms`;
      line.style.animation = `fadeInUp 0.3s ${delay}ms forwards`;
    }
    await this.sleep(1500);
  }

  async connectToBackend() {
    try {
      const resp = await fetch('http://localhost:5000/api/system/info', { signal: AbortSignal.timeout(3000) });
      if (resp.ok) {
        this.commandPanel.showToast('Connected to Daniela OS');
      }
    } catch (e) {
      console.warn('[Jarvis] Backend not available');
    }
  }

  sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
  }
}

document.addEventListener('DOMContentLoaded', () => {
  const app = new JarvisApp();
  app.init();
});
