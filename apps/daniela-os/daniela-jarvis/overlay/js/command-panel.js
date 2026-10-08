/**
 * Daniela OS — Jarvis Desktop Overlay
 * Command Panel — Quick Actions & Chat
 */

class CommandPanel {
  constructor() {
    this.baseUrl = 'http://localhost:5000';
    this.chatWidget = document.getElementById('chatWidget');
    this.chatMessages = document.getElementById('chatMessages');
    this.chatInput = document.getElementById('chatInput');
    this.chatSend = document.getElementById('chatSend');
    this.chatClose = document.getElementById('chatClose');

    this.init();
  }

  init() {
    // Action buttons
    document.querySelectorAll('.action-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        const action = btn.dataset.action;
        this.executeAction(action);
      });
    });

    // Chat
    if (this.chatSend) {
      this.chatSend.addEventListener('click', () => this.sendChat());
    }
    if (this.chatInput) {
      this.chatInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') this.sendChat();
      });
    }
    if (this.chatClose) {
      this.chatClose.addEventListener('click', () => this.hideChat());
    }
  }

  async executeAction(action) {
    switch (action) {
      case 'briefing':
        await this.fetchBriefing();
        break;
      case 'deploy':
        this.showToast('Opening Docker Marketplace...');
        window.open('http://localhost:5000/docker-marketplace', '_blank');
        break;
      case 'chat':
        this.showChat();
        break;
      case 'health':
        await this.runHealthCheck();
        break;
      case 'search':
        this.showChat();
        this.chatInput.placeholder = 'Search...';
        this.chatInput.focus();
        break;
      case 'settings':
        this.showToast('Settings panel coming soon');
        break;
    }
  }

  async fetchBriefing() {
    this.showToast('Fetching morning briefing...');
    try {
      const resp = await fetch(`${this.baseUrl}/api/predictive/briefing`, { signal: AbortSignal.timeout(5000) });
      if (resp.ok) {
        const data = await resp.json();
        this.showChat();
        this.addChatMessage('daniela', 'Morning Briefing:');
        if (data.briefing) {
          this.addChatMessage('daniela', data.briefing);
        } else if (data.summary) {
          this.addChatMessage('daniela', data.summary);
        } else {
          this.addChatMessage('daniela', JSON.stringify(data).substring(0, 500));
        }
      } else {
        this.showToast('Briefing unavailable', 'warning');
      }
    } catch (e) {
      this.showToast('Cannot connect to Daniela OS', 'error');
    }
  }

  async runHealthCheck() {
    this.showToast('Running health check...');
    try {
      const resp = await fetch(`${this.baseUrl}/api/healing/status`, { signal: AbortSignal.timeout(5000) });
      if (resp.ok) {
        const data = await resp.json();
        this.showChat();
        this.addChatMessage('daniela', 'System Health:');
        if (data.checks) {
          Object.entries(data.checks).forEach(([name, check]) => {
            const status = check.status === 'ok' || check.status === 'healthy' ? 'OK' : 'WARNING';
            this.addChatMessage('daniela', `  ${name}: ${status}`);
          });
        } else {
          this.addChatMessage('daniela', JSON.stringify(data).substring(0, 500));
        }
      } else {
        this.showToast('Health check unavailable', 'warning');
      }
    } catch (e) {
      this.showToast('Cannot connect to Daniela OS', 'error');
    }
  }

  showChat() {
    if (this.chatWidget) {
      this.chatWidget.style.display = 'flex';
      this.chatInput?.focus();
    }
  }

  hideChat() {
    if (this.chatWidget) {
      this.chatWidget.style.display = 'none';
    }
  }

  addChatMessage(role, text) {
    if (!this.chatMessages) return;
    const div = document.createElement('div');
    div.className = `chat-msg ${role}`;
    div.textContent = text;
    this.chatMessages.appendChild(div);
    this.chatMessages.scrollTop = this.chatMessages.scrollHeight;
  }

  async sendChat() {
    const text = this.chatInput?.value?.trim();
    if (!text) return;

    this.addChatMessage('user', text);
    this.chatInput.value = '';

    try {
      const resp = await fetch(`${this.baseUrl}/api/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: text }),
        signal: AbortSignal.timeout(10000)
      });

      if (resp.ok) {
        const data = await resp.json();
        this.addChatMessage('daniela', data.response || data.message || 'OK');
      } else {
        this.addChatMessage('daniela', '(Backend unavailable)');
      }
    } catch (e) {
      this.addChatMessage('daniela', '(Cannot connect to Daniela OS)');
    }
  }

  showToast(message, type = 'info') {
    let container = document.querySelector('.toast-container');
    if (!container) {
      container = document.createElement('div');
      container.className = 'toast-container';
      document.body.appendChild(container);
    }

    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.textContent = message;
    container.appendChild(toast);

    setTimeout(() => toast.remove(), 3500);
  }
}

window.CommandPanel = CommandPanel;
