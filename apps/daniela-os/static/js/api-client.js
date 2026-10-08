/**
 * AIGestion API Client
 * Centralized API layer that unifies all backend communication.
 *
 * Replaces hardcoded endpoints:
 *   - localhost:8085
 *   - 192.168.1.133:5059
 *   - /api/chat (relative)
 *   - /api/speech (relative)
 *
 * Features:
 *   - Single configurable base URL (auto-detects from window.location or env)
 *   - REST + WebSocket with automatic fallback
 *   - Request queuing when offline
 *   - Retry logic with exponential backoff
 *   - Auth token injection (from localStorage)
 *   - SSE streaming support
 *   - Unified error handling
 *
 * Usage:
 *   import { APIClient } from '/static/js/api-client.js';
 *   const client = new APIClient({ baseUrl: 'http://localhost:8085' });
 *   const res = await client.chat('Hello Daniela');
 *
 * Or use the singleton:
 *   import { api } from '/static/js/api-client.js';
 *   const res = await api.chat('Hello Daniela');
 */

class APIClient {
  constructor(options = {}) {
    // Auto-detect base URL: env config > localStorage override > current origin
    this.baseUrl = options.baseUrl
      || window.AIGESTION_API_URL
      || localStorage.getItem('aigestion_api_url')
      || `${window.location.origin}`;

    this.wsUrl = options.wsUrl
      || window.AIGESTION_WS_URL
      || this.baseUrl.replace(/^http/, 'ws');

    // Retry configuration
    this.maxRetries = options.maxRetries || 3;
    this.retryDelay = options.retryDelay || 1000;
    this.retryBackoff = options.retryBackoff || 2;

    // Timeout
    this.timeout = options.timeout || 30000;

    // Request queue (when offline)
    this.queue = [];
    this.online = navigator.onLine;

    // WebSocket connection
    this.ws = null;
    this.wsConnected = false;
    this.wsReconnectAttempts = 0;
    this.wsMaxReconnectAttempts = 5;
    this.wsReconnectDelay = 2000;
    this.wsListeners = new Map();

    // Auth token
    this.authToken = localStorage.getItem('aigestion_auth_token') || null;

    // Listen for online/offline events
    window.addEventListener('online', () => {
      this.online = true;
      this.flushQueue();
    });
    window.addEventListener('offline', () => {
      this.online = false;
    });

    // Auto-connect WebSocket if configured
    if (options.autoConnectWs !== false) {
      this.connectWebSocket();
    }
  }

  // ============================================================
  // AUTH
  // ============================================================

  setAuthToken(token) {
    this.authToken = token;
    if (token) {
      localStorage.setItem('aigestion_auth_token', token);
    } else {
      localStorage.removeItem('aigestion_auth_token');
    }
  }

  getAuthHeaders() {
    const headers = { 'Content-Type': 'application/json' };
    if (this.authToken) {
      headers['Authorization'] = `Bearer ${this.authToken}`;
    }
    return headers;
  }

  // ============================================================
  // REST API
  // ============================================================

  async request(method, path, data = null, options = {}) {
    const url = this._buildUrl(path);

    // If offline, queue the request
    if (!this.online && !options.bypassQueue) {
      return new Promise((resolve, reject) => {
        this.queue.push({ method, path, data, options, resolve, reject });
      });
    }

    const retries = options.retries ?? this.maxRetries;
    let lastError;

    for (let attempt = 0; attempt <= retries; attempt++) {
      try {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), options.timeout || this.timeout);

        const fetchOptions = {
          method: method.toUpperCase(),
          headers: { ...this.getAuthHeaders(), ...(options.headers || {}) },
          signal: controller.signal,
        };

        if (data && ['POST', 'PUT', 'PATCH'].includes(fetchOptions.method)) {
          fetchOptions.body = JSON.stringify(data);
        }

        const response = await fetch(url, fetchOptions);
        clearTimeout(timeoutId);

        if (!response.ok) {
          throw new APIError(`HTTP ${response.status}: ${response.statusText}`, response.status, path);
        }

        // Handle different content types
        const contentType = response.headers.get('content-type') || '';
        if (contentType.includes('application/json')) {
          return await response.json();
        } else if (contentType.includes('text/')) {
          return await response.text();
        } else if (contentType.includes('blob') || contentType.includes('octet-stream')) {
          return await response.blob();
        } else {
          return await response.text();
        }
      } catch (error) {
        lastError = error;

        // Don't retry on 4xx errors (client errors)
        if (error instanceof APIError && error.status >= 400 && error.status < 500) {
          throw error;
        }

        // Don't retry on abort (timeout)
        if (error.name === 'AbortError') {
          throw new APIError('Request timeout', 408, path);
        }

        // Wait with exponential backoff before retrying
        if (attempt < retries) {
          const delay = this.retryDelay * Math.pow(this.retryBackoff, attempt);
          await this._sleep(delay);
        }
      }
    }

    throw lastError || new APIError('Request failed after all retries', 500, path);
  }

  // Convenience methods
  get(path, options) { return this.request('GET', path, null, options); }
  post(path, data, options) { return this.request('POST', path, data, options); }
  put(path, data, options) { return this.request('PUT', path, data, options); }
  patch(path, data, options) { return this.request('PATCH', path, data, options); }
  delete(path, options) { return this.request('DELETE', path, null, options); }

  // ============================================================
  // HIGH-LEVEL API METHODS
  // ============================================================

  /**
   * Send a chat message to the AI (Daniela/Gemini)
   * @param {string} message - User message
   * @param {object} context - Additional context (history, zone, etc.)
   * @returns {Promise<{response: string, audio?: string}>}
   */
  async chat(message, context = {}) {
    return this.post('/api/chat', {
      message,
      context,
      timestamp: Date.now(),
    });
  }

  /**
   * Text-to-speech synthesis
   * @param {string} text - Text to synthesize
   * @param {string} voice - Voice ID (default: ElviraNeural)
   * @returns {Promise<Blob>} Audio blob
   */
  async tts(text, voice = 'ElviraNeural') {
    const blob = await this.post('/api/tts', { text, voice }, {
      headers: { 'Accept': 'audio/mpeg' },
    });
    return blob;
  }

  /**
   * Speech-to-text transcription
   * @param {Blob} audioBlob - Audio data
   * @returns {Promise<{text: string}>}
   */
  async stt(audioBlob) {
    const formData = new FormData();
    formData.append('audio', audioBlob);

    const url = this._buildUrl('/api/stt');
    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Authorization': this.authToken ? `Bearer ${this.authToken}` : '',
      },
      body: formData,
    });

    if (!response.ok) {
      throw new APIError(`STT failed: ${response.status}`, response.status, '/api/stt');
    }
    return response.json();
  }

  /**
   * Capture a camera frame
   * @param {string} action - What to do with the frame ('snap', 'analyze', 'ocr')
   * @param {Blob} imageBlob - Image data
   * @returns {Promise<object>}
   */
  async camera(action, imageBlob) {
    const formData = new FormData();
    formData.append('action', action);
    formData.append('image', imageBlob);

    const url = this._buildUrl('/api/camera/snap');
    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Authorization': this.authToken ? `Bearer ${this.authToken}` : '',
      },
      body: formData,
    });

    if (!response.ok) {
      throw new APIError(`Camera failed: ${response.status}`, response.status, '/api/camera/snap');
    }
    return response.json();
  }

  /**
   * Get agent status (all or specific)
   * @param {string} agentName - Optional agent name filter
   * @returns {Promise<object>}
   */
  async getAgentStatus(agentName = null) {
    const path = agentName ? `/api/agents/${agentName}/status` : '/api/agents/status';
    return this.get(path);
  }

  /**
   * Get activity feed (recent agent activity)
   * @param {object} filters - { agent, limit, since }
   * @returns {Promise<Array>}
   */
  async getActivity(filters = {}) {
    const params = new URLSearchParams();
    if (filters.agent) params.set('agent', filters.agent);
    if (filters.limit) params.set('limit', filters.limit);
    if (filters.since) params.set('since', filters.since);
    return this.get(`/api/activity?${params.toString()}`);
  }

  /**
   * Get system metrics (for datacenter globe)
   * @returns {Promise<object>}
   */
  async getMetrics() {
    return this.get('/api/metrics');
  }

  // ============================================================
  // WEBSOCKET
  // ============================================================

  /**
   * Connect to the WebSocket server for real-time updates.
   */
  connectWebSocket() {
    if (this.ws && (this.ws.readyState === WebSocket.OPEN || this.ws.readyState === WebSocket.CONNECTING)) {
      return;
    }

    try {
      const wsUrl = this.authToken
        ? `${this.wsUrl}/ws?token=${encodeURIComponent(this.authToken)}`
        : `${this.wsUrl}/ws`;

      this.ws = new WebSocket(wsUrl);

      this.ws.onopen = () => {
        this.wsConnected = true;
        this.wsReconnectAttempts = 0;
        this._notifyWsListeners('connected', { url: wsUrl });
      };

      this.ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          this._notifyWsListeners('message', data);
          // Also notify type-specific listeners
          if (data.type) {
            this._notifyWsListeners(data.type, data);
          }
        } catch (e) {
          // Non-JSON message
          this._notifyWsListeners('raw', event.data);
        }
      };

      this.ws.onerror = (error) => {
        this._notifyWsListeners('error', error);
      };

      this.ws.onclose = () => {
        this.wsConnected = false;
        this._notifyWsListeners('disconnected', {});

        // Auto-reconnect
        if (this.wsReconnectAttempts < this.wsMaxReconnectAttempts) {
          this.wsReconnectAttempts++;
          const delay = this.wsReconnectDelay * this.wsReconnectAttempts;
          setTimeout(() => this.connectWebSocket(), delay);
        }
      };

    } catch (error) {
      console.warn('[AIGestion API] WebSocket connection failed:', error);
    }
  }

  /**
   * Send a message via WebSocket.
   * Falls back to REST if WebSocket is not connected.
   */
  wsSend(type, data = {}) {
    if (this.ws && this.wsConnected) {
      this.ws.send(JSON.stringify({ type, data, timestamp: Date.now() }));
      return true;
    }
    // Fallback to REST POST
    this.post('/api/ws-message', { type, data });
    return false;
  }

  /**
   * Subscribe to WebSocket events.
   * @param {string} eventType - Event type ('connected', 'disconnected', 'message', or custom type)
   * @param {function} callback - Callback function
   * @returns {function} Unsubscribe function
   */
  onWs(eventType, callback) {
    if (!this.wsListeners.has(eventType)) {
      this.wsListeners.set(eventType, new Set());
    }
    this.wsListeners.get(eventType).add(callback);
    return () => this.wsListeners.get(eventType)?.delete(callback);
  }

  _notifyWsListeners(eventType, data) {
    const listeners = this.wsListeners.get(eventType);
    if (listeners) {
      listeners.forEach(cb => {
        try { cb(data); } catch (e) { console.error('[AIGestion API] WS listener error:', e); }
      });
    }
  }

  // ============================================================
  // SSE STREAMING
  // ============================================================

  /**
   * Subscribe to a Server-Sent Events stream.
   * @param {string} path - SSE endpoint path
   * @param {function} onMessage - Callback for each message
   * @param {function} onError - Callback for errors
   * @returns {function} Cleanup function (closes the connection)
   */
  subscribeSSE(path, onMessage, onError) {
    const url = this._buildUrl(path);
    const eventSource = new EventSource(url);

    eventSource.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        onMessage(data);
      } catch (e) {
        onMessage(event.data);
      }
    };

    eventSource.onerror = (error) => {
      if (onError) onError(error);
      // EventSource auto-reconnects, but notify the caller
    };

    return () => eventSource.close();
  }

  // ============================================================
  // QUEUE MANAGEMENT
  // ============================================================

  async flushQueue() {
    const items = [...this.queue];
    this.queue = [];

    for (const item of items) {
      try {
        const result = await this.request(item.method, item.path, item.data, item.options);
        item.resolve(result);
      } catch (error) {
        item.reject(error);
      }
    }
  }

  // ============================================================
  // UTILITIES
  // ============================================================

  _buildUrl(path) {
    // If path is already a full URL, return as-is
    if (path.startsWith('http://') || path.startsWith('https://')) {
      return path;
    }
    // If path starts with /, append to base URL
    if (path.startsWith('/')) {
      return `${this.baseUrl}${path}`;
    }
    // Otherwise, treat as relative path
    return `${this.baseUrl}/${path}`;
  }

  _sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  /**
   * Health check - ping the server.
   */
  async ping() {
    try {
      const start = Date.now();
      await this.get('/api/health', { timeout: 5000, retries: 0 });
      return { ok: true, latency: Date.now() - start };
    } catch (error) {
      return { ok: false, error: error.message };
    }
  }

  /**
   * Update the base URL (e.g., when user configures a different server).
   */
  setBaseUrl(url) {
    this.baseUrl = url;
    this.wsUrl = url.replace(/^http/, 'ws');
    localStorage.setItem('aigestion_api_url', url);
    // Reconnect WebSocket
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
    this.connectWebSocket();
  }
}

// ============================================================
// ERROR CLASS
// ============================================================

class APIError extends Error {
  constructor(message, status, path) {
    super(message);
    this.name = 'APIError';
    this.status = status;
    this.path = path;
  }
}

// ============================================================
// SINGLETON EXPORT
// ============================================================

// Create default instance (auto-configures from environment)
const api = new APIClient();

// Export for ES6 module usage
if (typeof module !== 'undefined' && module.exports) {
  module.exports = { APIClient, APIError, api };
}

// Global access for non-module scripts
if (typeof window !== 'undefined') {
  window.AIGestionAPI = api;
  window.APIClient = APIClient;
  window.APIError = APIError;
}
