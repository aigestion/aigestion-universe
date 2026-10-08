class AIGApi {
  constructor(baseUrl = '') {
    this.baseUrl = baseUrl;
    this.timeout = 15000;
    this.maxRetries = 3;
    this.retryDelay = 1000;
  }

  async request(endpoint, options = {}) {
    const url = `${this.baseUrl}/api${endpoint}`;
    const config = {
      headers: { 'Content-Type': 'application/json' },
      ...options,
    };

    for (let attempt = 1; attempt <= this.maxRetries; attempt++) {
      try {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), this.timeout);

        const response = await fetch(url, {
          ...config,
          signal: controller.signal,
        });
        clearTimeout(timeoutId);

        if (!response.ok) {
          throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }

        return await response.json();
      } catch (err) {
        if (attempt === this.maxRetries || err.name === 'AbortError') {
          throw err;
        }
        await this.delay(this.retryDelay * attempt);
      }
    }
  }

  delay(ms) {
    return new Promise((r) => setTimeout(r, ms));
  }

  get(endpoint) {
    return this.request(endpoint);
  }

  post(endpoint, data) {
    return this.request(endpoint, {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  put(endpoint, data) {
    return this.request(endpoint, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  }

  delete(endpoint) {
    return this.request(endpoint, { method: 'DELETE' });
  }

  async getServices() {
    return this.get('/services');
  }

  async getService(id) {
    return this.get(`/services/${id}`);
  }

  async getServiceStatus(id) {
    return this.get(`/services/${id}/status`);
  }

  async getServiceLogs(id) {
    return this.get(`/services/${id}/logs`);
  }

  async restartService(id) {
    return this.post(`/services/${id}/restart`);
  }

  async stopService(id) {
    return this.post(`/services/${id}/stop`);
  }

  async startService(id) {
    return this.post(`/services/${id}/start`);
  }

  async getSystemStats() {
    return this.get('/system/stats');
  }

  async getSystemHealth() {
    return this.get('/system/health');
  }

  async getDockerContainers() {
    return this.get('/docker/containers');
  }

  async getDockerContainer(id) {
    return this.get(`/docker/containers/${id}`);
  }

  async restartDockerContainer(id) {
    return this.post(`/docker/containers/${id}/restart`);
  }

  async getHermesConfig() {
    return this.get('/hermes/config');
  }

  async updateHermesConfig(config) {
    return this.put('/hermes/config', config);
  }

  async getHermesLogs() {
    return this.get('/hermes/logs');
  }

  async getHermesMetrics() {
    return this.get('/hermes/metrics');
  }

  async getDanielaProfile() {
    return this.get('/daniela/profile');
  }

  async getDanielaConversations() {
    return this.get('/daniela/conversations');
  }

  async getDanielaStats() {
    return this.get('/daniela/stats');
  }

  async sendDanielaMessage(message) {
    return this.post('/daniela/message', { message });
  }

  async getBackups() {
    return this.get('/backups');
  }

  async createBackup() {
    return this.post('/backups');
  }

  async getSettings() {
    return this.get('/settings');
  }

  async updateSettings(settings) {
    return this.put('/settings', settings);
  }
}

window.AIGApi = AIGApi;

// ── Mobile v2: unified gateway (http://localhost:8095/api/<engine>/*) ──
// :8080 is occupied by another gateway; ours runs on :8095.
// Mirrors cross_engine/protocols.py ENGINE_PORTS / ENGINE_PATHS.
// Old AIGApi direct-port methods above are kept as fallback.
const GATEWAY_BASE = 'http://localhost:8095';
const ORCHESTRATOR_BASE = 'http://localhost:9900';

const ENGINE_PORTS = {
  epic_pc: 5020,
  daniela: 9200,
  hermes: 9300,
  optimization: 9400,
  frontend_v1: 9500,
  frontend_v2: 9600,
  infra_opt: 9700,
  agent_mobile: 9800,
  security: 9999,
  perf: 9998,
  dashboard: 9997,
  intel_engine: 9850,
  auto_engine: 9860,
  data_engine: 9870,
  secure_engine: 9880,
  devtools_engine: 9890,
  ecosystem_engine: 9840,
  ux_engine: 9830,
  scale_engine: 9820,
};

const ENGINE_PATHS = {
  epic_pc: '/api/epic-pc',
  daniela: '/api/daniela',
  hermes: '/api/hermes',
  optimization: '/api/optimization',
  frontend: '/api/frontend',
  infra_opt: '/api/infra',
  agent_mobile: '/api/agent',
  security: '/api/security',
  perf: '/api/perf',
  dashboard: '/api/dashboard',
  intel_engine: '/api/intel',
  auto_engine: '/api/auto',
  data_engine: '/api/data',
  secure_engine: '/api/secure-engine',
  devtools_engine: '/api/devtools',
  ecosystem_engine: '/api/ecosystem',
  ux_engine: '/api/ux',
  scale_engine: '/api/scale',
};

class GatewayApi {
  constructor(gatewayBase = GATEWAY_BASE, orchestratorBase = ORCHESTRATOR_BASE) {
    this.gatewayBase = gatewayBase;
    this.orchestratorBase = orchestratorBase;
    this.timeout = 4000;
    this.maxRetries = 2;
  }

  delay(ms) {
    return new Promise((r) => setTimeout(r, ms));
  }

  async fetchJson(url, options = {}) {
    for (let attempt = 1; attempt <= this.maxRetries; attempt++) {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), this.timeout);
      try {
        const response = await fetch(url, {
          headers: { 'Content-Type': 'application/json' },
          ...options,
          signal: controller.signal,
        });
        clearTimeout(timeoutId);
        if (!response.ok) {
          throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        return await response.json();
      } catch (err) {
        clearTimeout(timeoutId);
        if (attempt === this.maxRetries) throw err;
        await this.delay(250 * attempt);
      }
    }
  }

  gatewayUrl(path) {
    return `${this.gatewayBase}${path}`;
  }

  enginePath(name) {
    return ENGINE_PATHS[name] || `/api/${name}`;
  }

  directUrl(name, subPath = '/status') {
    const port = ENGINE_PORTS[name];
    if (!port) throw new Error(`Unknown engine: ${name}`);
    return `http://localhost:${port}${subPath}`;
  }

  // GET /api/gateway/engines — full route table + circuit/rate state
  async statusAll() {
    return this.fetchJson(this.gatewayUrl('/api/gateway/engines'));
  }

  async gatewayStatus() {
    return this.fetchJson(this.gatewayUrl('/api/gateway/status'));
  }

  async gatewayEvents(limit = 20) {
    return this.fetchJson(this.gatewayUrl(`/api/gateway/events?limit=${limit}`));
  }

  // Per-engine status via gateway (/api/<engine>/*), direct-port fallback
  async engineStatus(name) {
    const t0 = performance.now();
    try {
      const data = await this.fetchJson(
        this.gatewayUrl(`${this.enginePath(name)}/status`)
      );
      return { engine: name, status: 'online', latency: Math.round(performance.now() - t0), ...data };
    } catch {
      try {
        const data = await this.fetchJson(this.directUrl(name, '/status'));
        return { engine: name, status: 'online', latency: Math.round(performance.now() - t0), ...data, via: 'direct' };
      } catch (err) {
        return { engine: name, status: 'offline', latency: Math.round(performance.now() - t0), error: String(err) };
      }
    }
  }

  // GET /api/cross/status via orchestrator :9900, gateway fallback
  async crossStatus() {
    try {
      return await this.fetchJson(`${this.orchestratorBase}/api/cross/status`);
    } catch {
      return await this.fetchJson(this.gatewayUrl('/api/gateway/status'));
    }
  }

  async crossEvents(limit = 20) {
    try {
      return await this.fetchJson(`${this.orchestratorBase}/api/cross/events?limit=${limit}`);
    } catch {
      return await this.gatewayEvents(limit);
    }
  }

  // Heartbeat via gateway, direct-port fallback
  async sendHeartbeat(name) {
    const body = JSON.stringify({ engine: name, timestamp: Date.now() });
    try {
      return await this.fetchJson(
        this.gatewayUrl(`${this.enginePath(name)}/heartbeat`),
        { method: 'POST', body }
      );
    } catch {
      return await this.fetchJson(this.directUrl(name, '/heartbeat'), {
        method: 'POST',
        body,
      });
    }
  }
}

window.GatewayApi = GatewayApi;
window.GATEWAY_BASE = GATEWAY_BASE;
window.ORCHESTRATOR_BASE = ORCHESTRATOR_BASE;
window.ENGINE_PORTS = ENGINE_PORTS;
window.ENGINE_PATHS = ENGINE_PATHS;
