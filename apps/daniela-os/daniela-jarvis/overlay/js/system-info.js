/**
 * Daniela OS — Jarvis Desktop Overlay
 * System Info Widgets (CPU, RAM, Network, Disk)
 * Fetches data from Daniela OS backend (port 5000)
 */

class SystemInfo {
  constructor() {
    this.baseUrl = 'http://localhost:5000';
    this.cache = {};
    this.updateInterval = null;
    this.elements = {};
    this.previousNetUp = 0;
    this.previousNetDown = 0;
    this.init();
  }

  init() {
    // Cache DOM elements
    this.elements = {
      cpuGauge: document.getElementById('cpuGauge'),
      cpuValue: document.getElementById('cpuValue'),
      cpuDetail: document.getElementById('cpuDetail'),
      ramGauge: document.getElementById('ramGauge'),
      ramValue: document.getElementById('ramValue'),
      ramDetail: document.getElementById('ramDetail'),
      netUp: document.getElementById('netUp'),
      netDown: document.getElementById('netDown'),
      netUpVal: document.getElementById('netUpVal'),
      netDownVal: document.getElementById('netDownVal'),
      diskFill: document.getElementById('diskFill'),
      diskDetail: document.getElementById('diskDetail'),
      statusCpu: document.getElementById('statusCpu'),
      statusMem: document.getElementById('statusMem'),
      bottomRight: document.getElementById('bottomRight'),
      statusTime: document.getElementById('statusTime'),
    };

    this.updateClock();
    this.startUpdates();
  }

  startUpdates() {
    this.fetchSystemInfo();
    this.updateInterval = setInterval(() => this.fetchSystemInfo(), 2000);
  }

  async fetchSystemInfo() {
    try {
      // Try fetching from Daniela OS backend
      const resp = await fetch(`${this.baseUrl}/api/system/info`, { signal: AbortSignal.timeout(3000) });
      if (resp.ok) {
        const data = await resp.json();
        this.updateFromBackend(data);
        return;
      }
    } catch (e) {
      // Backend not available, use Electron's getSystemInfo
    }

    // Fallback: use Electron's IPC
    if (window.jarvis) {
      try {
        const info = await window.jarvis.getSystemInfo();
        this.updateFromElectron(info);
      } catch (e) {
        console.warn('[SystemInfo] Cannot fetch system info:', e);
      }
    }
  }

  updateFromBackend(data) {
    const cpu = data.cpu_percent ?? data.cpu ?? 0;
    const mem = data.memory ?? {};
    const memPercent = mem.percent ?? data.memory_percent ?? 0;
    const memUsed = mem.used ?? 0;
    const memTotal = mem.total ?? 1;
    const disk = data.disk ?? {};
    const diskPercent = disk.percent ?? 0;
    const diskUsed = disk.used ?? 0;
    const diskTotal = disk.total ?? 1;
    const uptime = data.uptime ?? 0;

    this.updateGauge('cpu', cpu);
    this.updateGauge('ram', memPercent);
    this.updateDisk(diskPercent, diskUsed, diskTotal);
    this.updateUptime(uptime);

    // Network
    const net = data.network ?? {};
    const netUp = net.bytes_sent ?? 0;
    const netDown = net.bytes_recv ?? 0;
    this.updateNetwork(netUp, netDown);
  }

  updateFromElectron(info) {
    const memUsed = info.totalMemory - info.freeMemory;
    const memPercent = (memUsed / info.totalMemory) * 100;

    this.updateGauge('ram', memPercent);
    this.elements.ramDetail.textContent = `${(memUsed / 1073741824).toFixed(1)} GB / ${(info.totalMemory / 1073741824).toFixed(1)} GB`;
    this.updateUptime(info.uptime);
  }

  updateGauge(type, percent) {
    const gauge = this.elements[`${type}Gauge`];
    const value = this.elements[`${type}Value`];
    if (!gauge || !value) return;

    const circumference = 251.2;
    const offset = circumference - (percent / 100) * circumference;
    gauge.style.strokeDashoffset = offset;

    // Color coding
    gauge.classList.remove('warning', 'critical');
    if (percent > 90) gauge.classList.add('critical');
    else if (percent > 70) gauge.classList.add('warning');

    value.textContent = `${Math.round(percent)}%`;

    if (type === 'cpu') {
      this.elements.cpuDetail.textContent = `${navigator.hardwareConcurrency || '--'} cores`;
      this.elements.statusCpu.textContent = `CPU: ${Math.round(percent)}%`;
    } else if (type === 'ram') {
      this.elements.statusMem.textContent = `RAM: ${Math.round(percent)}%`;
    }
  }

  updateNetwork(totalUp, totalDown) {
    const upSpeed = Math.max(0, totalUp - this.previousNetUp);
    const downSpeed = Math.max(0, totalDown - this.previousNetDown);
    this.previousNetUp = totalUp;
    this.previousNetDown = totalDown;

    const upStr = this.formatBytes(upSpeed) + '/s';
    const downStr = this.formatBytes(downSpeed) + '/s';

    this.elements.netUpVal.textContent = upStr;
    this.elements.netDownVal.textContent = downStr;

    // Scale bars (max ~10MB/s = 100%)
    const maxSpeed = 10 * 1024 * 1024;
    const upPct = Math.min(100, (upSpeed / maxSpeed) * 100);
    const downPct = Math.min(100, (downSpeed / maxSpeed) * 100);

    const upBar = this.elements.netUp;
    const downBar = this.elements.netDown;
    if (upBar) upBar.style.setProperty('--bar-width', `${upPct}%`);
    if (downBar) downBar.style.setProperty('--bar-width', `${downPct}%`);

    // Update bar fill via pseudo-element (use inline style)
    document.documentElement.style.setProperty('--net-up-width', `${upPct}%`);
    document.documentElement.style.setProperty('--net-down-width', `${downPct}%`);
  }

  updateDisk(percent, used, total) {
    if (this.elements.diskFill) {
      this.elements.diskFill.style.width = `${percent}%`;
    }
    if (this.elements.diskDetail) {
      this.elements.diskDetail.textContent = `${this.formatBytes(used)} / ${this.formatBytes(total)}`;
    }
  }

  updateUptime(seconds) {
    if (!this.elements.bottomRight) return;
    const h = Math.floor(seconds / 3600);
    const m = Math.floor((seconds % 3600) / 60);
    this.elements.bottomRight.textContent = `Uptime: ${h}h ${m}m`;
  }

  updateClock() {
    const update = () => {
      const now = new Date();
      const timeStr = now.toLocaleTimeString('en-US', { hour12: false });
      if (this.elements.statusTime) {
        this.elements.statusTime.textContent = timeStr;
      }
    };
    update();
    setInterval(update, 1000);
  }

  formatBytes(bytes) {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
  }

  destroy() {
    if (this.updateInterval) clearInterval(this.updateInterval);
  }
}

window.SystemInfo = SystemInfo;
