/**
 * AIGestion Built-in AI Client (GT-15)
 * ====================================
 * Chrome's built-in Prompt API (stable in Chrome 148+) for zero-cost,
 * on-device AI on the landing page demo chat. No API key, no server,
 * no rate limits. Falls back to Gemini API for unsupported browsers.
 *
 * Also wraps Gemma 197M task APIs (summarizer, translator, language detector).
 *
 * Free tier: $0 forever — runs entirely in the browser.
 */

class BuiltInAI {
  constructor() {
    this.available = false;
    this.session = null;
    this.defaults = {
      temperature: 0.7,
      topK: 3,
    };
  }

  /**
   * Check if the built-in Prompt API is available.
   */
  async checkAvailability() {
    if (!('ai' in window) || !window.ai) {
      // Try the newer API surface
      if (!('LanguageModel' in window)) {
        return { available: false, reason: 'Built-in AI not supported. Use Chrome 148+.' };
      }
    }

    try {
      // Chrome 148+ API
      if ('ai' in window && window.ai.languageModel) {
        const caps = await window.ai.languageModel.capabilities();
        this.available = caps.available === 'readily' || caps.available === 'after-download';
        return {
          available: this.available,
          reason: caps.available === 'readily' ? 'Ready' :
                  caps.available === 'after-download' ? 'Model needs download (first use)' :
                  'Not available',
          api: 'window.ai.languageModel',
        };
      }
      // Newer API surface
      if ('LanguageModel' in window) {
        this.available = true;
        return { available: true, reason: 'Ready (LanguageModel API)', api: 'LanguageModel' };
      }
    } catch (e) {
      return { available: false, reason: 'Error checking: ' + e.message };
    }

    return { available: false, reason: 'No built-in AI API found' };
  }

  /**
   * Initialize a text session with the built-in model.
   */
  async init(systemPrompt) {
    const status = await this.checkAvailability();
    if (!status.available) {
      throw new Error(status.reason);
    }

    try {
      const opts = {
        temperature: this.defaults.temperature,
        topK: this.defaults.topK,
      };
      if (systemPrompt) {
        opts.systemPrompt = systemPrompt;
      }

      // Chrome 148+ API
      if ('ai' in window && window.ai.languageModel) {
        this.session = await window.ai.languageModel.create(opts);
      } else if ('LanguageModel' in window) {
        this.session = await new LanguageModel().create(opts);
      }

      return true;
    } catch (e) {
      throw new Error('Failed to init built-in AI: ' + e.message);
    }
  }

  /**
   * Generate text using the built-in on-device model.
   * Zero API cost, zero rate limits, works offline.
   */
  async generate(prompt) {
    if (!this.session) {
      await this.init();
    }

    if (!this.session) {
      throw new Error('Built-in AI session not available');
    }

    try {
      // Stream the response
      let result = '';
      const stream = this.session.promptStreaming(prompt);

      for await (const chunk of stream) {
        result += chunk;
      }

      return result;
    } catch (e) {
      // Fallback: non-streaming
      try {
        return await this.session.prompt(prompt);
      } catch (e2) {
        throw new Error('Built-in AI failed: ' + e2.message);
      }
    }
  }

  /**
   * Destroy the session to free resources.
   */
  destroy() {
    if (this.session && this.session.destroy) {
      this.session.destroy();
      this.session = null;
    }
  }
}

/**
 * Gemma 197M Task API wrapper.
 * Built-in task-specific models in Chrome 148+.
 * All run on-device, zero cost.
 */
class BuiltInTaskAPIs {
  constructor() {
    this.summarizer = null;
    this.translator = null;
    this.languageDetector = null;
  }

  /**
   * Summarize text using built-in Gemma summarizer.
   * @param {string} text - Text to summarize
   * @param {string} type - 'short' | 'medium' | 'long' | 'bullet'
   * @param {string} format - 'plain-text' | 'markdown'
   */
  async summarize(text, type = 'medium', format = 'plain-text') {
    try {
      if ('ai' in window && window.ai.summarizer) {
        if (!this.summarizer) {
          this.summarizer = await window.ai.summarizer.create({ type, format, sharedContext: '' });
        }
        return await this.summarizer.summarize(text);
      }
    } catch (e) {
      console.log('[Built-in AI] Summarizer not available:', e.message);
    }
    return null;
  }

  /**
   * Translate text using built-in translator.
   * @param {string} text - Text to translate
   * @param {string} targetLang - Target language code (e.g., 'es', 'en')
   * @param {string} sourceLang - Source language (optional, auto-detected)
   */
  async translate(text, targetLang, sourceLang = '') {
    try {
      if ('ai' in window && window.ai.translator) {
        if (!this.translator) {
          this.translator = await window.ai.translator.create({ sourceLanguage: sourceLang, targetLanguage: targetLang });
        }
        return await this.translator.translate(text);
      }
    } catch (e) {
      console.log('[Built-in AI] Translator not available:', e.message);
    }
    return null;
  }

  /**
   * Detect the language of a text.
   * @param {string} text - Text to analyze
   */
  async detectLanguage(text) {
    try {
      if ('ai' in window && window.ai.languageDetector) {
        if (!this.languageDetector) {
          this.languageDetector = await window.ai.languageDetector.create();
        }
        const results = await this.languageDetector.detect(text);
        return results[0]; // {confidence, label}
      }
    } catch (e) {
      console.log('[Built-in AI] Language detector not available:', e.message);
    }
    return null;
  }
}

/**
 * AIGestion Demo Chat Controller
 * Combines built-in AI (zero cost) with Gemini API fallback.
 *
 * Priority:
 *   1. Chrome Built-in Prompt API (free, on-device, instant)
 *   2. Gemini API via /api/chat (free tier, 15 RPM)
 *   3. Fallback response (no cost)
 */
class AIGestionDemoChat {
  constructor() {
    this.builtInAI = new BuiltInAI();
    this.taskAPIs = new BuiltInTaskAPIs();
    this.useBuiltIn = false;
    this.messageCount = 0;
    this.maxMessages = 10; // Higher limit since built-in AI is free
    this.storageKey = 'aigestion_demo_count_v2';
  }

  async init() {
    // Check built-in AI availability
    const status = await this.builtInAI.checkAvailability();

    if (status.available) {
      this.useBuiltIn = true;
      await this.builtInAI.init(
        'You are Daniela, an AI assistant for AIGestion, a platform for managing ' +
        'gestoria (fiscal/accounting) tasks. You help users understand how AIGestion ' +
        'can automate their business: emails, invoices, calendar, social media, ' +
        'content creation, and more. Respond in the same language as the user. ' +
        'Keep responses concise (2-4 sentences). Be helpful and professional.'
      );
      return { mode: 'builtin', reason: status.reason };
    }

    // Fallback to Gemini API
    return { mode: 'api', reason: 'Using Gemini API (free tier). ' + status.reason };
  }

  async sendMessage(message) {
    if (this.getMessageCount() >= this.maxMessages) {
      return {
        text: 'Has agotado tus mensajes de demo. Registrate gratis para seguir conversando.',
        limit: true,
      };
    }

    this.incrementCount();

    if (this.useBuiltIn) {
      try {
        const response = await this.builtInAI.generate(message);
        return { text: response, source: 'builtin', cost: 0 };
      } catch (e) {
        console.log('[Demo Chat] Built-in AI failed, falling back to API:', e.message);
        this.useBuiltIn = false;
      }
    }

    // Fallback to Gemini API
    try {
      const api = window.AIGestionAPI || new window.APIClient();
      const result = await api.chat(message, { source: 'landing_demo_builtin_fallback' });
      return {
        text: result.response || result.message || result.text || 'Lo siento, no pude procesar tu solicitud.',
        source: 'api',
        cost: 0, // free tier
      };
    } catch (e) {
      return {
        text: 'No pude conectar con el servidor. Si usas Chrome 148+, el chat funciona sin servidor. ' +
              'Para iniciar el backend: python aigestion_core.py',
        source: 'error',
        cost: 0,
      };
    }
  }

  getMessageCount() {
    return parseInt(localStorage.getItem(this.storageKey) || '0', 10);
  }

  incrementCount() {
    this.messageCount = this.getMessageCount() + 1;
    localStorage.setItem(this.storageKey, String(this.messageCount));
    return this.messageCount;
  }

  getRemaining() {
    return this.maxMessages - this.getMessageCount();
  }

  /**
   * Summarize content on-device (free).
   */
  async summarize(text) {
    return await this.taskAPIs.summarize(text, 'bullet', 'markdown');
  }

  /**
   * Translate content on-device (free).
   */
  async translate(text, targetLang) {
    return await this.taskAPIs.translate(text, targetLang);
  }

  /**
   * Auto-detect user language and respond accordingly.
   */
  async detectLanguage(text) {
    return await this.taskAPIs.detectLanguage(text);
  }
}

// Export as singleton
window.BuiltInAI = BuiltInAI;
window.BuiltInTaskAPIs = BuiltInTaskAPIs;
window.AIGestionDemoChat = AIGestionDemoChat;
