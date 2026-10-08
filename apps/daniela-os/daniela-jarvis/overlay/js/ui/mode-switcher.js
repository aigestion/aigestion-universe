/**
 * Daniela OS — Jarvis Desktop Overlay
 * Mode Switcher — Radial menu for 6 modes
 */

class ModeSwitcher {
  constructor(modeManager) {
    this.modeManager = modeManager;
    this.isOpen = false;
    this.container = null;
    this.modes = [
      { id: 'arc-reactor', icon: '⚛', label: 'CORE', color: '#00f0ff' },
      { id: 'globe', icon: '🌍', label: 'GLOBE', color: '#0ea5e9' },
      { id: 'neural-core', icon: '🧠', label: 'NEURAL', color: '#8b5cf6' },
      { id: 'planetary', icon: '🪐', label: 'SYSTEM', color: '#f59e0b' },
      { id: 'knowledge-graph', icon: '🕸', label: 'GRAPH', color: '#10b981' },
      { id: 'geolocation', icon: '📍', label: 'GPS', color: '#ef4444' },
    ];

    this.init();
  }

  init() {
    this.createContainer();
    this.bindKeys();
  }

  createContainer() {
    this.container = document.createElement('div');
    this.container.className = 'mode-switcher';
    this.container.innerHTML = `
      <button class="mode-toggle-btn" id="modeToggle">
        <span class="mode-toggle-icon">◉</span>
      </button>
      <div class="mode-radial" id="modeRadial">
        ${this.modes.map((m, i) => {
          const angle = (i / this.modes.length) * 360 - 90;
          const rad = angle * (Math.PI / 180);
          const rx = Math.cos(rad) * 90;
          const ry = Math.sin(rad) * 90;
          return `
            <button class="mode-item" data-mode="${m.id}"
              style="--rx:${rx}px; --ry:${ry}px; --color:${m.color}; --delay:${i * 30}ms">
              <span class="mode-item-icon">${m.icon}</span>
              <span class="mode-item-label">${m.label}</span>
            </button>`;
        }).join('')}
      </div>
    `;
    document.body.appendChild(this.container);

    // Toggle button
    const toggleBtn = this.container.querySelector('#modeToggle');
    toggleBtn.addEventListener('click', (e) => {
      e.stopPropagation();
      this.toggle();
    });

    // Mode items
    this.container.querySelectorAll('.mode-item').forEach(item => {
      item.addEventListener('click', (e) => {
        e.stopPropagation();
        const mode = item.dataset.mode;
        this.modeManager.switchTo(mode);
        this.updateActive(mode);
        this.close();
      });
    });

    // Close on click outside
    document.addEventListener('click', () => this.close());
    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape') this.close();
    });
  }

  bindKeys() {
    // Tab to open/close
    document.addEventListener('keydown', (e) => {
      if (e.key === 'Tab') {
        e.preventDefault();
        this.toggle();
      }
      // Number keys 1-6 to switch modes directly
      if (e.key >= '1' && e.key <= '6') {
        const idx = parseInt(e.key) - 1;
        if (this.modes[idx]) {
          this.modeManager.switchTo(this.modes[idx].id);
          this.updateActive(this.modes[idx].id);
        }
      }
    });
  }

  toggle() {
    this.isOpen ? this.close() : this.open();
  }

  open() {
    this.isOpen = true;
    this.container.classList.add('open');
  }

  close() {
    this.isOpen = false;
    this.container.classList.remove('open');
  }

  updateActive(modeId) {
    this.container.querySelectorAll('.mode-item').forEach(item => {
      item.classList.toggle('active', item.dataset.mode === modeId);
    });
  }
}

window.ModeSwitcher = ModeSwitcher;
