class HomeView {
  constructor(container) {
    this.container = container;
    this.api = new AIGApi();
  }

  async render() {
    this.container.innerHTML = `
      <h1 class="page-title fade-in">aig</h1>
      <p class="page-subtitle fade-in">Dashboard de servicios</p>
      <div id="home-stats" class="stat-grid fade-in"></div>
      <p class="section-title fade-in">Servicios</p>
      <div id="home-services" class="service-list fade-in"></div>
      <p class="section-title fade-in">Actividad reciente</p>
      <div id="home-logs" class="log-list fade-in"></div>
    `;

    await this.loadData();
  }

  async loadData() {
    try {
      const [stats, services, logs] = await Promise.allSettled([
        this.api.getSystemStats(),
        this.api.getServices(),
        this.api.getServiceLogs('all'),
      ]);

      this.renderStats(stats.status === 'fulfilled' ? stats.value : null);
      this.renderServices(services.status === 'fulfilled' ? services.value : null);
      this.renderLogs(logs.status === 'fulfilled' ? logs.value : null);
    } catch {
      this.renderError();
    }
  }

  renderStats(stats) {
    const el = document.getElementById('home-stats');
    if (!stats) {
      el.innerHTML = `
        <div class="stat-card"><div class="stat-value">--</div><div class="stat-label">Servicios</div></div>
        <div class="stat-card"><div class="stat-value">--</div><div class="stat-label">Activos</div></div>
        <div class="stat-card"><div class="stat-value">--</div><div class="stat-label">CPU</div></div>
        <div class="stat-card"><div class="stat-value">--</div><div class="stat-label">Memoria</div></div>
      `;
      return;
    }
    el.innerHTML = `
      <div class="stat-card"><div class="stat-value">${stats.services ?? 0}</div><div class="stat-label">Servicios</div></div>
      <div class="stat-card"><div class="stat-value">${stats.active ?? 0}</div><div class="stat-label">Activos</div></div>
      <div class="stat-card"><div class="stat-value">${stats.cpu ?? 0}%</div><div class="stat-label">CPU</div></div>
      <div class="stat-card"><div class="stat-value">${stats.memory ?? 0}%</div><div class="stat-label">Memoria</div></div>
    `;
  }

  renderServices(services) {
    const el = document.getElementById('home-services');
    if (!services || !services.length) {
      el.innerHTML = `<div class="empty-state"><p>No hay servicios disponibles</p></div>`;
      return;
    }
    el.innerHTML = services.slice(0, 5).map((s) => `
      <div class="service-item" onclick="app.navigate('service/${s.id}')">
        <div class="service-icon" style="background:${s.color || '#00ffff'}20;color:${s.color || '#00ffff'}">
          ${s.icon || '⚡'}
        </div>
        <div class="service-info">
          <div class="service-name">${s.name}</div>
          <div class="service-meta">${s.type || 'service'}</div>
        </div>
        <span class="status-badge status-${s.status === 'running' ? 'online' : 'offline'}">
          <span class="status-dot"></span>${s.status}
        </span>
      </div>
    `).join('');
  }

  renderLogs(logs) {
    const el = document.getElementById('home-logs');
    if (!logs || !logs.length) {
      el.innerHTML = `<div class="empty-state"><p>Sin actividad reciente</p></div>`;
      return;
    }
    el.innerHTML = logs.slice(0, 8).map((l) => `
      <div class="log-item log-${l.level || 'info'}">
        <span class="log-time">${l.time || ''}</span>${l.message}
      </div>
    `).join('');
  }

  renderError() {
    document.getElementById('home-services').innerHTML =
      `<div class="empty-state"><p>Error al cargar servicios</p></div>`;
  }
}

class DanielaView {
  constructor(container) {
    this.container = container;
    this.api = new AIGApi();
  }

  async render() {
    this.container.innerHTML = `
      <h1 class="page-title fade-in">Daniela</h1>
      <p class="page-subtitle fade-in">Asistente de IA personal</p>

      <div class="daniela-stage fade-in" id="daniela-stage">
        <div class="daniela-stage__overlay" id="daniela-overlay">
          <div class="daniela-stage__spinner" aria-hidden="true"></div>
          <p class="daniela-stage__msg" id="daniela-msg">Cargando avatar…</p>
        </div>
        <div class="daniela-stage__badge" id="daniela-badge" hidden>idle</div>
      </div>

      <div class="daniela-controls fade-in" role="group" aria-label="Estado de Daniela">
        <button class="chip" data-state="idle">Reposo</button>
        <button class="chip" data-state="listening">Escuchando</button>
        <button class="chip" data-state="thinking">Pensando</button>
        <button class="chip" data-state="talking">Hablando</button>
        <button class="chip chip--accent" id="daniela-voice">🔊 Probar voz</button>
      </div>

      <!-- Chat REAL: POST /api/ai/chat (herramientas del visor incluidas) -->
      <div class="chat fade-in" id="daniela-chat">
        <div class="chat-hilo" id="chat-hilo" aria-live="polite"></div>
        <form class="chat-form" id="chat-form" autocomplete="off">
          <input id="chat-texto" type="text" enterkeyhint="send"
                 placeholder="Escribe a Daniela…" aria-label="Mensaje para Daniela" />
          <button class="btn-chat" id="chat-enviar" type="submit">Enviar</button>
        </form>
      </div>

      <div id="daniela-profile" class="card fade-in"></div>
      <p class="section-title fade-in">Estadísticas</p>
      <div id="daniela-stats" class="stat-grid fade-in"></div>
      <p class="section-title fade-in">Conversaciones recientes</p>
      <div id="daniela-conversations" class="service-list fade-in"></div>
    `;

    this._bindControls();
    this._montarChat();
    // En paralelo: los datos de la tarjeta no deben esperar a los 3,2 MB del .glb.
    const data = this.loadData();
    await this._mountAvatar();
    await data;
  }

  /**
   * El chat de Daniela, conectado a `POST /api/ai/chat`.
   *
   * El avatar es quien "habla": cada estado del chat se le pasa al modelo 3D
   * (`onEstado`), así la conversación y el cuerpo de Daniela dicen lo mismo.
   */
  _montarChat() {
    const nodos = {
      hilo: document.getElementById('chat-hilo'),
      formulario: document.getElementById('chat-form'),
      entrada: document.getElementById('chat-texto'),
      boton: document.getElementById('chat-enviar'),
    };
    if (!nodos.hilo || !nodos.formulario) return;

    import('./daniela-chat.js').then(({ DanielaChat }) => {
      this.chat = new DanielaChat(nodos, {
        onEstado: (estado) => {
          if (this.avatar) {
            if (estado !== 'talking') this.avatar.stopSpeaking();
            this._syncChips(this.avatar.setState(estado));
          } else {
            this._syncChips(estado);
          }
        },
        onHablar: (texto) => this.avatar?.hablarTTS(texto),
      });
    }).catch((e) => {
      nodos.hilo.innerHTML =
        `<p class="chat-vacio">Chat no disponible: ${e.message}</p>`;
    });
  }

  /** Sincroniza el chip activo con el estado real del avatar. */
  _syncChips(state) {
    this.container.querySelectorAll('.chip[data-state]').forEach((c) => {
      c.classList.toggle('is-active', c.dataset.state === state);
    });
    const badge = document.getElementById('daniela-badge');
    if (badge) {
      badge.textContent = state;
      badge.hidden = false;
    }
  }

  _bindControls() {
    this.container.querySelectorAll('.chip[data-state]').forEach((btn) => {
      btn.addEventListener('click', () => {
        if (!this.avatar) return;
        if (btn.dataset.state !== 'talking') this.avatar.stopSpeaking();
        this._syncChips(this.avatar.setState(btn.dataset.state));
      });
    });

    document.getElementById('daniela-voice')?.addEventListener('click', () => {
      if (!this.avatar) return;
      this.avatar.speak(
        'Hola, soy Daniela. Tu asistente personal, funcionando sin conexión.',
      );
      this._syncChips('talking');
    });
  }

  async _mountAvatar() {
    const host = document.getElementById('daniela-stage');
    const overlay = document.getElementById('daniela-overlay');
    const msg = document.getElementById('daniela-msg');
    if (!host) return;

    // Import diferido: three.js + GLTFLoader (~890 KB) solo se descargan cuando
    // el usuario abre la pestaña de Daniela, no en el arranque de la PWA.
    const { mountDanielaAvatar } = await import('./daniela-avatar.js');

    this.avatar = await mountDanielaAvatar(host, {
      onProgress: (p) => {
        if (msg) msg.textContent = `Cargando avatar… ${Math.round(p * 100)}%`;
      },
      onReady: () => {
        overlay?.classList.add('is-hidden');
        this._syncChips(this.avatar?.state || 'idle');
      },
      onFallback: () => {
        if (!overlay) return;
        overlay.classList.add('is-fallback');
        overlay.innerHTML =
          '<img class="daniela-stage__img" src="/icons/icon-512.png" alt="Daniela">' +
          '<p class="daniela-stage__msg">Avatar 3D no disponible en este dispositivo</p>';
      },
    });
  }

  /** Libera el contexto WebGL y el chat al salir de la vista. */
  destroy() {
    this.chat?.destroy();
    this.chat = null;
    this.avatar?.dispose();
    this.avatar = null;
  }

  async loadData() {
    try {
      const [profile, stats, convos] = await Promise.allSettled([
        this.api.getDanielaProfile(),
        this.api.getDanielaStats(),
        this.api.getDanielaConversations(),
      ]);

      this.renderProfile(profile.status === 'fulfilled' ? profile.value : null);
      this.renderStats(stats.status === 'fulfilled' ? stats.value : null);
      this.renderConversations(convos.status === 'fulfilled' ? convos.value : null);
    } catch {
      document.getElementById('daniela-profile').innerHTML =
        `<div class="card-header"><span class="card-title">Error al cargar</span></div>`;
    }
  }

  renderProfile(profile) {
    const el = document.getElementById('daniela-profile');
    if (!profile) {
      el.innerHTML = `<div class="card-header"><span class="card-title">Sin datos</span></div>`;
      return;
    }
    el.innerHTML = `
      <div class="card-header">
        <span class="card-title">${profile.name || 'Daniela'}</span>
        <span class="status-badge status-online"><span class="status-dot"></span>Online</span>
      </div>
      <p class="card-subtitle">${profile.description || 'AI Assistant'}</p>
      <div class="progress-bar"><div class="progress-fill purple" style="width:${profile.health || 100}%"></div></div>
    `;
  }

  renderStats(stats) {
    const el = document.getElementById('daniela-stats');
    if (!stats) {
      el.innerHTML = `
        <div class="stat-card"><div class="stat-value">--</div><div class="stat-label">Mensajes</div></div>
        <div class="stat-card"><div class="stat-value">--</div><div class="stat-label">Sesiones</div></div>
      `;
      return;
    }
    el.innerHTML = `
      <div class="stat-card"><div class="stat-value">${stats.messages ?? 0}</div><div class="stat-label">Mensajes</div></div>
      <div class="stat-card"><div class="stat-value">${stats.sessions ?? 0}</div><div class="stat-label">Sesiones</div></div>
    `;
  }

  renderConversations(convos) {
    const el = document.getElementById('daniela-conversations');
    if (!convos || !convos.length) {
      el.innerHTML = `<div class="empty-state"><p>No hay conversaciones</p></div>`;
      return;
    }
    el.innerHTML = convos.slice(0, 5).map((c) => `
      <div class="service-item">
        <div class="service-icon" style="background:#00ffff20;color:#00ffff">💬</div>
        <div class="service-info">
          <div class="service-name">${c.title || 'Conversación'}</div>
          <div class="service-meta">${c.date || ''} · ${c.messages || 0} mensajes</div>
        </div>
      </div>
    `).join('');
  }
}

class HermesView {
  constructor(container) {
    this.container = container;
    this.api = new AIGApi();
  }

  async render() {
    this.container.innerHTML = `
      <h1 class="page-title fade-in">Hermes</h1>
      <p class="page-subtitle fade-in">Gateway y orquestador</p>
      <div id="hermes-status" class="card fade-in"></div>
      <p class="section-title fade-in">Métricas</p>
      <div id="hermes-metrics" class="stat-grid fade-in"></div>
      <p class="section-title fade-in">Logs</p>
      <div id="hermes-logs" class="log-list fade-in"></div>
    `;

    await this.loadData();
  }

  async loadData() {
    try {
      const [config, metrics, logs] = await Promise.allSettled([
        this.api.getHermesConfig(),
        this.api.getHermesMetrics(),
        this.api.getHermesLogs(),
      ]);

      this.renderStatus(config.status === 'fulfilled' ? config.value : null);
      this.renderMetrics(metrics.status === 'fulfilled' ? metrics.value : null);
      this.renderLogs(logs.status === 'fulfilled' ? logs.value : null);
    } catch {
      document.getElementById('hermes-status').innerHTML =
        `<div class="card-header"><span class="card-title">Error al cargar</span></div>`;
    }
  }

  renderStatus(config) {
    const el = document.getElementById('hermes-status');
    if (!config) {
      el.innerHTML = `<div class="card-header"><span class="card-title">Sin datos</span></div>`;
      return;
    }
    el.innerHTML = `
      <div class="card-header">
        <span class="card-title">Hermes Gateway</span>
        <span class="status-badge status-${config.status === 'running' ? 'online' : 'offline'}">
          <span class="status-dot"></span>${config.status || 'unknown'}
        </span>
      </div>
      <p class="card-subtitle">Puerto: ${config.port || '--'} · Version: ${config.version || '--'}</p>
      <div class="progress-bar"><div class="progress-fill green" style="width:${config.uptime || 0}%"></div></div>
    `;
  }

  renderMetrics(metrics) {
    const el = document.getElementById('hermes-metrics');
    if (!metrics) {
      el.innerHTML = `
        <div class="stat-card"><div class="stat-value">--</div><div class="stat-label">Requests/min</div></div>
        <div class="stat-card"><div class="stat-value">--</div><div class="stat-label">Latencia</div></div>
      `;
      return;
    }
    el.innerHTML = `
      <div class="stat-card"><div class="stat-value">${metrics.rpm ?? 0}</div><div class="stat-label">Requests/min</div></div>
      <div class="stat-card"><div class="stat-value">${metrics.latency ?? 0}ms</div><div class="stat-label">Latencia</div></div>
    `;
  }

  renderLogs(logs) {
    const el = document.getElementById('hermes-logs');
    if (!logs || !logs.length) {
      el.innerHTML = `<div class="empty-state"><p>Sin logs</p></div>`;
      return;
    }
    el.innerHTML = logs.slice(0, 10).map((l) => `
      <div class="log-item log-${l.level || 'info'}">
        <span class="log-time">${l.time || ''}</span>${l.message}
      </div>
    `).join('');
  }
}

class SettingsView {
  constructor(container) {
    this.container = container;
    this.api = new AIGApi();
    this.settings = {
      notifications: true,
      darkMode: true,
      autoRefresh: true,
      refreshInterval: 30,
    };
  }

  async render() {
    this.container.innerHTML = `
      <h1 class="page-title fade-in">Settings</h1>
      <p class="page-subtitle fade-in">Configuración de la app</p>
      <div class="settings-group fade-in">
        <div class="settings-group-title">General</div>
        <div class="settings-item">
          <span class="settings-item-label">Notificaciones push</span>
          <div class="toggle ${this.settings.notifications ? 'active' : ''}" data-setting="notifications"></div>
        </div>
        <div class="settings-item">
          <span class="settings-item-label">Modo oscuro</span>
          <div class="toggle ${this.settings.darkMode ? 'active' : ''}" data-setting="darkMode"></div>
        </div>
      </div>
      <div class="settings-group fade-in">
        <div class="settings-group-title">Datos</div>
        <div class="settings-item">
          <span class="settings-item-label">Auto refrescar</span>
          <div class="toggle ${this.settings.autoRefresh ? 'active' : ''}" data-setting="autoRefresh"></div>
        </div>
        <div class="settings-item">
          <span class="settings-item-label">Intervalo de refresco</span>
          <span class="settings-item-value">${this.settings.refreshInterval}s</span>
        </div>
      </div>
      <div class="settings-group fade-in">
        <div class="settings-group-title">App</div>
        <div class="settings-item" id="install-btn">
          <span class="settings-item-label">Instalar app</span>
          <span class="settings-item-value">PWA</span>
        </div>
        <div class="settings-item" id="clear-cache-btn">
          <span class="settings-item-label">Limpiar caché</span>
          <span class="settings-item-value">→</span>
        </div>
      </div>
      <p class="section-title fade-in">Info</p>
      <div class="card fade-in">
        <p class="card-subtitle">aig Mobile v1.0.0</p>
        <p class="card-subtitle" id="connection-status">Estado: Conectado</p>
        <p class="card-subtitle" id="sw-status">Service Worker: --</p>
      </div>
    `;

    this.bindEvents();
    this.updateInfo();
  }

  bindEvents() {
    document.querySelectorAll('.toggle').forEach((toggle) => {
      toggle.addEventListener('click', () => {
        toggle.classList.toggle('active');
        const key = toggle.dataset.setting;
        this.settings[key] = toggle.classList.contains('active');
        this.saveSettings();
      });
    });

    document.getElementById('install-btn')?.addEventListener('click', () => {
      if (window.deferredPrompt) {
        window.deferredPrompt.prompt();
      }
    });

    document.getElementById('clear-cache-btn')?.addEventListener('click', async () => {
      if ('caches' in window) {
        const keys = await caches.keys();
        await Promise.all(keys.map((k) => caches.delete(k)));
        alert('Caché limpiada');
      }
    });
  }

  async saveSettings() {
    try {
      await this.api.updateSettings(this.settings);
    } catch {
      localStorage.setItem('aig-settings', JSON.stringify(this.settings));
    }
  }

  updateInfo() {
    const connEl = document.getElementById('connection-status');
    const swEl = document.getElementById('sw-status');
    if (connEl) {
      connEl.textContent = `Estado: ${navigator.onLine ? 'Conectado' : 'Offline'}`;
    }
    if (swEl && 'serviceWorker' in navigator) {
      navigator.serviceWorker.getRegistration().then((reg) => {
        swEl.textContent = `Service Worker: ${reg ? 'Activo' : 'Inactivo'}`;
      });
    }
  }
}

class EnginesView {
  constructor(container) {
    this.container = container;
    this.api = new GatewayApi();
    this.groups = {
      Core: ['epic_pc', 'daniela', 'hermes', 'dashboard'],
      'Data & Security': ['data_engine', 'intel_engine', 'secure_engine', 'security'],
      Performance: ['optimization', 'perf', 'infra_opt', 'scale_engine'],
      Experience: ['frontend_v1', 'frontend_v2', 'ux_engine', 'ecosystem_engine'],
      Automation: ['auto_engine', 'agent_mobile', 'devtools_engine'],
    };
  }

  async render() {
    this.container.innerHTML = `
      <h1 class="page-title fade-in">Engines</h1>
      <p class="page-subtitle fade-in">19 engines via unified gateway</p>
      <div id="engines-summary" class="stat-grid fade-in"></div>
      <div id="engines-groups" class="fade-in"></div>
    `;
    await this.loadData();
  }

  async loadData() {
    try {
      const [table, cross] = await Promise.allSettled([
        this.api.statusAll(),
        this.api.crossStatus(),
      ]);
      const routeTable = table.status === 'fulfilled' ? table.value : null;
      const crossData = cross.status === 'fulfilled' ? cross.value : null;
      const health = await this.probeAll();
      this.renderSummary(routeTable, crossData, health);
      this.renderGroups(routeTable, health);
    } catch {
      document.getElementById('engines-groups').innerHTML =
        `<div class="empty-state"><p>Error loading engines</p></div>`;
    }
  }

  async probeAll() {
    const names = Object.keys(window.ENGINE_PORTS || {});
    const results = await Promise.all(
      names.map((n) => this.api.engineStatus(n).catch(() => ({ engine: n, status: 'offline', latency: -1 })))
    );
    const map = {};
    results.forEach((r) => { map[r.engine] = r; });
    return map;
  }

  renderSummary(routeTable, crossData, health) {
    const el = document.getElementById('engines-summary');
    const vals = Object.values(health);
    const online = vals.filter((h) => h.status === 'online' || h.status === 'healthy').length;
    const latencies = vals.filter((h) => h.latency >= 0).map((h) => h.latency);
    const avg = latencies.length ? Math.round(latencies.reduce((a, b) => a + b, 0) / latencies.length) : 0;
    const score = crossData && crossData.health_score != null ? crossData.health_score : '--';
    el.innerHTML = `
      <div class="stat-card"><div class="stat-value">${online}/19</div><div class="stat-label">Online</div></div>
      <div class="stat-card"><div class="stat-value">${avg}ms</div><div class="stat-label">Avg latency</div></div>
      <div class="stat-card"><div class="stat-value">${score}</div><div class="stat-label">Health score</div></div>
      <div class="stat-card"><div class="stat-value">${routeTable ? Object.keys(routeTable).length : 0}</div><div class="stat-label">Routes</div></div>
    `;
  }

  renderGroups(routeTable, health) {
    const el = document.getElementById('engines-groups');
    el.innerHTML = Object.entries(this.groups).map(([cat, names]) => `
      <p class="section-title">${cat}</p>
      <div class="service-list">
        ${names.map((n) => {
          const h = health[n] || { status: 'unknown', latency: -1 };
          const online = h.status === 'online' || h.status === 'healthy';
          const port = (window.ENGINE_PORTS || {})[n] || '--';
          return `
          <div class="service-item" onclick="app.navigate('engines')">
            <span class="status-dot ${online ? 'online' : 'offline'}" style="width:10px;height:10px;border-radius:50%;background:${online ? 'var(--success)' : 'var(--danger)'};flex-shrink:0;"></span>
            <div class="service-info">
              <div class="service-name">${n}</div>
              <div class="service-meta">:${port} · ${h.latency >= 0 ? h.latency + 'ms' : '--'}</div>
            </div>
            <span class="status-badge status-${online ? 'online' : 'offline'}">
              <span class="status-dot"></span>${h.status}
            </span>
          </div>`;
        }).join('')}
      </div>
    `).join('');
  }
}

class GatewayView {
  constructor(container) {
    this.container = container;
    this.api = new GatewayApi();
  }

  async render() {
    this.container.innerHTML = `
      <h1 class="page-title fade-in">Gateway</h1>
      <p class="page-subtitle fade-in">Unified gateway :8080 · orchestrator :9900</p>
      <div id="gateway-status" class="card fade-in"></div>
      <p class="section-title fade-in">Circuit breakers</p>
      <div id="gateway-circuits" class="service-list fade-in"></div>
      <p class="section-title fade-in">Recent cross events</p>
      <div id="gateway-events" class="log-list fade-in"></div>
    `;
    await this.loadData();
  }

  async loadData() {
    try {
      const [status, table, events] = await Promise.allSettled([
        this.api.gatewayStatus(),
        this.api.statusAll(),
        this.api.crossEvents(20),
      ]);
      this.renderStatus(status.status === 'fulfilled' ? status.value : null);
      this.renderCircuits(table.status === 'fulfilled' ? table.value : null);
      this.renderEvents(events.status === 'fulfilled' ? events.value : null);
    } catch {
      document.getElementById('gateway-status').innerHTML =
        `<div class="card-header"><span class="card-title">Gateway unreachable</span></div>`;
    }
  }

  renderStatus(status) {
    const el = document.getElementById('gateway-status');
    if (!status) {
      el.innerHTML = `<div class="card-header"><span class="card-title">Sin datos</span></div>`;
      return;
    }
    const active = status.gateway === 'active' || status.status === 'ok';
    el.innerHTML = `
      <div class="card-header">
        <span class="card-title">Gateway ${status.gateway || status.status || ''}</span>
        <span class="status-badge status-${active ? 'online' : 'offline'}">
          <span class="status-dot"></span>${active ? 'active' : 'down'}
        </span>
      </div>
      <p class="card-subtitle">Engines: ${status.engines ?? status.total ?? '--'} · Health: ${status.health_score ?? '--'}</p>
    `;
  }

  renderCircuits(table) {
    const el = document.getElementById('gateway-circuits');
    if (!table) {
      el.innerHTML = `<div class="empty-state"><p>Sin datos de circuitos</p></div>`;
      return;
    }
    const entries = Array.isArray(table) ? table : Object.entries(table).map(([name, v]) => ({ name, ...v }));
    el.innerHTML = entries.map((e) => {
      const circuit = e.circuit || e.circuit_state || 'closed';
      const open = circuit === 'open';
      return `
      <div class="service-item">
        <span class="status-dot ${open ? 'offline' : 'online'}" style="width:10px;height:10px;border-radius:50%;background:${open ? 'var(--danger)' : 'var(--success)'};flex-shrink:0;"></span>
        <div class="service-info">
          <div class="service-name">${e.name || e.engine}</div>
          <div class="service-meta">circuit: ${circuit} · rate: ${e.rate_remaining ?? '--'}</div>
        </div>
        <span class="status-badge status-${open ? 'offline' : 'online'}">
          <span class="status-dot"></span>${circuit}
        </span>
      </div>`;
    }).join('');
  }

  renderEvents(events) {
    const el = document.getElementById('gateway-events');
    const list = Array.isArray(events) ? events : (events && events.events) || [];
    if (!list.length) {
      el.innerHTML = `<div class="empty-state"><p>Sin eventos recientes</p></div>`;
      return;
    }
    el.innerHTML = list.slice(-20).reverse().map((ev) => `
      <div class="log-item log-info">
        <span class="log-time">${ev.timestamp ? new Date(ev.timestamp * 1000).toLocaleTimeString() : ''}</span>${ev.source_engine || ev.source || ''} · ${ev.event_type || ev.type || ''}
      </div>
    `).join('');
  }
}

/**
 * God's Eye DENTRO de Daniela.
 *
 * El visor no es una app aparte: es una pantalla de Daniela, servida por el
 * MISMO backend que esta PWA (`/gods-eye/`). Se embebe en un iframe a pantalla
 * completa y `js/gev.js` enlaza ese iframe con el puente de voz/sensores.
 *
 * `src` se pone desde `enlazarWebView()` (que además engancha el micrófono),
 * no en el HTML: si lo pusiera el markup, cada pintado recargaría el globo.
 */
class GevView {
  constructor(container) {
    this.container = container;
    this.api = new AIGApi();
  }

  async render() {
    this.container.innerHTML = `
      <div class="gev fade-in">
        <div class="gev-barra">
          <div class="gev-marca">
            <img class="gev-logo" src="/icons/icon-192.png" alt="" width="24" height="24" />
            <div>
              <h1 class="gev-titulo">God's Eye</h1>
              <p class="gev-estado" id="gev-estado">Conectando con Daniela…</p>
            </div>
          </div>
          <div class="gev-acciones">
            <button class="chip" id="voice-btn" title="Mando por voz"
                    aria-label="Mando por voz">🎤</button>
            <button class="chip" id="gev-recargar">Recargar</button>
            <a class="chip" href="/gods-eye/" target="_blank" rel="noopener">Abrir completo</a>
          </div>
        </div>
        <iframe id="gev-webview" class="gev-webview"
                title="God's Eye — visor de Daniela"
                allow="geolocation; microphone; fullscreen; camera"
                referrerpolicy="no-referrer-when-downgrade"></iframe>
      </div>
    `;

    // Mismo módulo que ya usa app.js: sin él el iframe no se enlaza y el
    // micrófono queda mudo.
    try {
      const { enlazarWebView } = await import('./gev.js');
      enlazarWebView(document.getElementById('gev-webview'));
    } catch (e) {
      const estado = document.getElementById('gev-estado');
      if (estado) estado.textContent = `Sin integración: ${e.message}`;
    }

    document.getElementById('gev-recargar')?.addEventListener('click', () => {
      const f = document.getElementById('gev-webview');
      if (f) f.src = f.src;   // recarga a peticion del usuario
    });

    this.loadData();
  }

  /**
   * Estado REAL del backend del visor (la misma API que usa el iframe).
   * No se comprueba el iframe: se comprueba de dónde sale.
   */
  async loadData() {
    const el = document.getElementById('gev-estado');
    if (!el) return;
    try {
      const d = await this.api.get('/globe/data');
      const nodos = Array.isArray(d.nodos) ? d.nodos.length : 0;
      el.textContent = `Conectado · ${nodos} empresas · rol ${d.rol || '?'}`;
      el.classList.remove('gev-estado--mal');
    } catch (e) {
      el.textContent = `Sin backend: ${String(e.message || e).slice(0, 60)}`;
      el.classList.add('gev-estado--mal');
    }
  }

  destroy() {
    // El iframe y sus escuchas se tiran con el nodo; `gev.js` vuelve a
    // enlazar el siguiente en cada pintado.
  }
}

window.HomeView = HomeView;
window.DanielaView = DanielaView;
window.HermesView = HermesView;
window.SettingsView = SettingsView;
window.EnginesView = EnginesView;
window.GatewayView = GatewayView;
window.GevView = GevView;
