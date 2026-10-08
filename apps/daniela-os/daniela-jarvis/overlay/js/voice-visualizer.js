/**
 * Daniela OS — Jarvis Desktop Overlay
 * Voice Visualizer & Speech Recognition
 * Microphone button with waveform visualization
 */

class VoiceVisualizer {
  constructor() {
    this.audioContext = null;
    this.analyser = null;
    this.microphone = null;
    this.isListening = false;
    this.recognition = null;
    this.onResult = null;
    this.onStatusChange = null;

    this.btn = document.getElementById('voiceBtn');
    this.statusEl = document.getElementById('voiceStatus');
    this.waveCanvas = document.getElementById('voiceWave');
    this.waveCtx = this.waveCanvas ? this.waveCanvas.getContext('2d') : null;

    this.init();
  }

  init() {
    if (this.btn) {
      this.btn.addEventListener('click', () => this.toggle());
    }

    // Initialize Web Speech API if available
    if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
      const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
      this.recognition = new SpeechRecognition();
      this.recognition.continuous = false;
      this.recognition.interimResults = true;
      this.recognition.lang = 'es-ES';

      this.recognition.onresult = (event) => {
        const last = event.results[event.results.length - 1];
        const transcript = last[0].transcript;
        if (last.isFinal) {
          this.handleFinalResult(transcript);
        } else {
          this.updateStatus(`Listening: "${transcript}"`);
        }
      };

      this.recognition.onend = () => {
        if (this.isListening) {
          this.stop();
        }
      };

      this.recognition.onerror = (event) => {
        console.warn('[Voice] Error:', event.error);
        this.updateStatus(`Error: ${event.error}`);
        this.stop();
      };
    } else {
      console.warn('[Voice] Speech Recognition not available');
      this.updateStatus('Speech API unavailable');
    }
  }

  async toggle() {
    if (this.isListening) {
      this.stop();
    } else {
      await this.start();
    }
  }

  async start() {
    try {
      // Get microphone access
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      this.audioContext = new (window.AudioContext || window.webkitAudioContext)();
      this.analyser = this.audioContext.createAnalyser();
      this.analyser.fftSize = 256;
      this.microphone = this.audioContext.createMediaStreamSource(stream);
      this.microphone.connect(this.analyser);

      this.stream = stream;
      this.isListening = true;

      // Start speech recognition
      if (this.recognition) {
        this.recognition.start();
      }

      this.btn.classList.add('listening');
      this.updateStatus('Listening...');
      this.drawWaveform();

    } catch (err) {
      console.error('[Voice] Microphone access denied:', err);
      this.updateStatus('Mic access denied');
    }
  }

  stop() {
    this.isListening = false;

    if (this.recognition) {
      try { this.recognition.stop(); } catch (e) {}
    }

    if (this.stream) {
      this.stream.getTracks().forEach(t => t.stop());
    }

    if (this.audioContext) {
      this.audioContext.close();
    }

    this.btn.classList.remove('listening');
    this.updateStatus('Click to speak');
    this.clearWaveform();
  }

  handleFinalResult(transcript) {
    this.updateStatus(`You said: "${transcript}"`);
    if (this.onResult) {
      this.onResult(transcript);
    }

    // Send to Daniela OS chat
    this.sendToDaniela(transcript);
    this.stop();
  }

  async sendToDaniela(text) {
    try {
      const resp = await fetch('http://localhost:5000/api/voice/command', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text, source: 'jarvis_overlay' })
      });
      if (resp.ok) {
        const data = await resp.json();
        if (data.response) {
          this.speak(data.response);
        }
      }
    } catch (e) {
      // Backend not available, try chat endpoint
      try {
        const resp = await fetch('http://localhost:5000/api/chat', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ message: text })
        });
        if (resp.ok) {
          const data = await resp.json();
          if (data.response) {
            this.speak(data.response);
          }
        }
      } catch (e2) {
        console.warn('[Voice] Cannot reach Daniela:', e2);
      }
    }
  }

  speak(text) {
    if ('speechSynthesis' in window) {
      const utter = new SpeechSynthesisUtterance(text);
      utter.lang = 'es-ES';
      utter.rate = 1.0;
      utter.pitch = 0.9;
      speechSynthesis.speak(utter);
      this.updateStatus('Speaking...');
      utter.onend = () => this.updateStatus('Click to speak');
    }
  }

  updateStatus(text) {
    if (this.statusEl) {
      this.statusEl.textContent = text;
    }
    if (this.onStatusChange) {
      this.onStatusChange(text);
    }
  }

  drawWaveform() {
    if (!this.analyser || !this.waveCtx) return;

    const canvas = this.waveCanvas;
    const ctx = this.waveCtx;
    const bufferLength = this.analyser.frequencyBinCount;
    const dataArray = new Uint8Array(bufferLength);

    const draw = () => {
      if (!this.isListening) return;
      requestAnimationFrame(draw);

      this.analyser.getByteFrequencyData(dataArray);

      ctx.clearRect(0, 0, canvas.width, canvas.height);

      const barWidth = (canvas.width / bufferLength) * 2.5;
      let x = 0;

      for (let i = 0; i < bufferLength; i++) {
        const barHeight = (dataArray[i] / 255) * canvas.height;
        const hue = (i / bufferLength) * 60 + 170; // Cyan to magenta

        ctx.fillStyle = `hsla(${hue}, 100%, 60%, 0.8)`;
        ctx.fillRect(x, canvas.height - barHeight, barWidth, barHeight);

        // Glow effect
        ctx.shadowBlur = 10;
        ctx.shadowColor = `hsla(${hue}, 100%, 60%, 0.5)`;

        x += barWidth + 1;
      }
    };

    draw();
  }

  clearWaveform() {
    if (this.waveCtx) {
      this.waveCtx.clearRect(0, 0, this.waveCanvas.width, this.waveCanvas.height);
    }
  }
}

window.VoiceVisualizer = VoiceVisualizer;
