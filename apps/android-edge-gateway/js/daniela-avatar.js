/**
 * Avatar 3D de Daniela — motor de animación procedural + morph targets.
 *
 * ─────────────────────────────────────────────────────────────────────────────
 * EL MODELO
 * ─────────────────────────────────────────────────────────────────────────────
 * `assets/daniela3d_rigged.glb` (generado por scripts/avatar/rig_daniela.py
 * desde la plantilla `assets/daniela3d.glb`) añade tres morph targets:
 *
 *     blink    → párpados cierran (parpadeo natural aleatorio)
 *     jawOpen  → mandíbula abre (sincronizado con el envelope de voz)
 *     browUp   → cejas suben (estado "thinking")
 *
 * Si el GLB rigged no está disponible, se carga `assets/daniela3d.glb`
 * (estático, sin morphs) y el avatar sigue vivo solo con animación
 * procedural de transform. La API no cambia.
 * ─────────────────────────────────────────────────────────────────────────────
 *
 * Estados disponibles: idle | listening | thinking | talking
 */

import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { RoomEnvironment } from 'three/addons/environments/RoomEnvironment.js';
import { MeshoptDecoder } from 'three/addons/libs/meshopt_decoder.module.js';

export const AVATAR_STATES = ['idle', 'listening', 'thinking', 'talking'];

/**
 * Perfil por estado. `breathe` escala la amplitud de la respiración, `bob`
 * la micro-cabeceada al hablar, `sway` el balanceo lento y `tilt` la
 * inclinación de postura (rad, signo = hacia delante).
 */
const PROFILE = {
  idle: { breathe: 1.0, bob: 0.0, sway: 1.0, tilt: 0.0, glow: 0.02, speed: 1.0 },
  listening: { breathe: 1.3, bob: 0.0, sway: 0.5, tilt: -0.04, glow: 0.07, speed: 1.15 },
  thinking: { breathe: 0.8, bob: 0.0, sway: 0.3, tilt: 0.07, glow: 0.04, speed: 0.7 },
  talking: { breathe: 1.5, bob: 1.0, sway: 0.7, tilt: 0.0, glow: 0.16, speed: 1.4 },
};

const MODEL_URL = '/assets/daniela3d_rigged.glb';
const MODEL_URL_FALLBACK = '/assets/daniela3d.glb';

export class DanielaAvatar {
  /**
   * @param {HTMLElement} container Nodo donde montar el <canvas>.
   * @param {object} [opts]
   * @param {(p:number)=>void} [opts.onProgress] 0..1 durante la carga.
   * @param {(err:Error)=>void} [opts.onError] Si WebGL o la carga fallan.
   * @param {()=>void} [opts.onReady] Una vez dibujado el primer frame.
   */
  constructor(container, opts = {}) {
    this.container = container;
    this.opts = opts;
    this.state = 'idle';
    this.disposed = false;
    this.ready = false;

    // Envoltura de "volumen de voz": 0 (boca cerrada) .. 1 (boca abierta).
    // La alimenta `speakAudio()` desde un AnalyserNode, o `setEnvelope()`.
    this.envelope = 0;

    this._t = 0;
    this._pointer = new THREE.Vector2(0, 0);
    this._look = new THREE.Vector2(0, 0);
    this._saccade = { yaw: 0, pitch: 0, next: 0 };
    this._raf = 0;
    this._audioCtx = null;
    this._analyser = null;
    this._activeSource = null;
    this._utterance = null;

    // Morph targets del GLB rigged (null si se carga el fallback estático).
    this._morphMesh = null;
    this._morphDict = null;
    this._blinkValue = 0;
    this._browValue = 0;
    this._blink = { phase: 'open', t: 0, next: 2.5 };
  }

  /** Crea renderer, escena, luces y carga el .glb. Resuelve cuando hay primer frame. */
  mount() {
    return new Promise((resolve, reject) => {
      if (this.disposed) return reject(new Error('avatar disposed'));

      try {
        this.renderer = new THREE.WebGLRenderer({
          antialias: true,
          alpha: true,
          powerPreference: 'high-performance',
        });
      } catch (err) {
        this.opts.onError?.(err);
        return reject(err);
      }

      const dpr = Math.min(window.devicePixelRatio || 1, 2);
      this.renderer.setPixelRatio(dpr);
      this.renderer.toneMapping = THREE.ACESFilmicToneMapping;
      this.renderer.toneMappingExposure = 1.15;
      this.renderer.setClearColor(0x000000, 0);
      this.container.appendChild(this.renderer.domElement);
      this.renderer.domElement.classList.add('daniela-canvas');

      this.scene = new THREE.Scene();
      this.camera = new THREE.PerspectiveCamera(30, 1, 0.05, 50);

      // Entorno PBR: sin IBL los materiales con metallic map quedan negros.
      const pmrem = new THREE.PMREMGenerator(this.renderer);
      this._envRT = pmrem.fromScene(new RoomEnvironment(), 0.04);
      this.scene.environment = this._envRT.texture;
      pmrem.dispose();

      this._addLights();

      this.pivot = new THREE.Group();
      this.scene.add(this.pivot);

      const loader = new GLTFLoader();
      loader.setMeshoptDecoder(MeshoptDecoder);

      const alCargar = (gltf) => {
        if (this.disposed) return;
        this._setupModel(gltf.scene);
        this._resize();
        this._startLoop();
        this.ready = true;
        this.opts.onReady?.();
        resolve();
      };
      const alProgreso = (evt) => {
        if (evt.lengthComputable && evt.total) {
          this.opts.onProgress?.(Math.min(1, evt.loaded / evt.total));
        }
      };
      const alFallar = (err) => {
        if (MODEL_URL !== MODEL_URL_FALLBACK) {
          console.warn('[DanielaAvatar] rigged no disponible, probando original');
          loader.load(MODEL_URL_FALLBACK, alCargar, alProgreso, (err2) => {
            this.opts.onError?.(err2 instanceof Error ? err2 : new Error(String(err2)));
            reject(err2);
          });
        } else {
          this.opts.onError?.(err instanceof Error ? err : new Error(String(err)));
          reject(err);
        }
      };

      loader.load(MODEL_URL, alCargar, alProgreso, alFallar);

      this._observeResize();
      this._observeVisibility();
      this._bindPointer();
    });
  }

  _addLights() {
    // Clave + relleno + contra: el modelo es busto, necesitamos leer el relieve.
    const key = new THREE.DirectionalLight(0xffffff, 2.1);
    key.position.set(1.6, 2.2, 2.0);
    const fill = new THREE.DirectionalLight(0x9ec5ff, 0.7);
    fill.position.set(-2.2, 0.6, 1.4);
    const rim = new THREE.DirectionalLight(0xff9ecb, 0.9);
    rim.position.set(-0.6, 1.4, -2.2);
    const hemi = new THREE.HemisphereLight(0xbdd4ff, 0x1b1030, 0.45);
    this.scene.add(key, fill, rim, hemi);
    this._glowLights = [key, rim];
  }

  _setupModel(root) {
    const box = new THREE.Box3().setFromObject(root);
    const size = box.getSize(new THREE.Vector3());
    const center = box.getCenter(new THREE.Vector3());

    // Recentrar en el origen para que todas las rotaciones giren sobre ella.
    root.position.sub(center);
    this.pivot.add(root);
    this.model = root;

    this._size = size;
    this._frameCamera();

    this._baseMaterials = [];
    root.traverse((o) => {
      if (!o.isMesh) return;
      o.castShadow = false;
      o.frustumCulled = true;
      const mats = Array.isArray(o.material) ? o.material : [o.material];
      for (const m of mats) {
        if (!m) continue;
        m.envMapIntensity = 1.15;
        if (m.emissive) m.userData.baseEmissive = m.emissive.clone();
        this._baseMaterials.push(m);
      }
      if (o.morphTargetInfluences && o.morphTargetInfluences.length) {
        this._morphMesh = o;
        this._morphDict = o.morphTargetDictionary;
      }
    });
  }

  _frameCamera() {
    const { width, height } = this._viewport();
    if (!width || !height) return;

    this.camera.aspect = width / height;

    const vFov = (this.camera.fov * Math.PI) / 180;
    const hFov = 2 * Math.atan(Math.tan(vFov / 2) * this.camera.aspect);

    // Encuadre que respeta el eje restrictivo (altura en retrato, anchura en
    // landscape) y deja un 18% de aire alrededor del busto.
    const distV = this._size.y / 2 / Math.tan(vFov / 2);
    const distH = this._size.x / 2 / Math.tan(hFov / 2);
    const dist = (Math.max(distV, distH) * 1.18) / 0.9;

    this.camera.position.set(0, this._size.y * 0.03, dist);
    this.camera.lookAt(0, 0, 0);
    // `shift` (0..0.5, + = modelo a la derecha): para lienzos a pantalla
    // completa donde el chat ocupa la izquierda (web_ui.html).
    if (this.opts.shift) {
      this.camera.setViewOffset(width, height, -this.opts.shift * width, 0, width, height);
    } else {
      this.camera.clearViewOffset();
    }
    this.camera.updateProjectionMatrix();
  }

  _viewport() {
    const r = this.container.getBoundingClientRect();
    return { width: Math.max(1, r.width), height: Math.max(1, r.height) };
  }

  _resize() {
    if (!this.renderer || !this.camera) return;
    const { width, height } = this._viewport();
    this.renderer.setSize(width, height, false);
    this.canvasW = width;
    this.canvasH = height;
    if (this._size) this._frameCamera();
  }

  _observeResize() {
    if (typeof ResizeObserver === 'undefined') {
      window.addEventListener('resize', () => this._resize());
      return;
    }
    this._ro = new ResizeObserver(() => this._resize());
    this._ro.observe(this.container);
  }

  _observeVisibility() {
    // No renderizar con la pestaña oculta: en móvil ahorra batería y térmica.
    this._onVis = () => {
      if (document.hidden) this._stopLoop();
      else if (!this.disposed && this.ready) this._startLoop();
    };
    document.addEventListener('visibilitychange', this._onVis);
  }

  _bindPointer() {
    const el = this.renderer.domElement;
    this._onPointer = (ev) => {
      const r = el.getBoundingClientRect();
      const pt = ev.touches ? ev.touches[0] : ev;
      if (!pt) return;
      this._pointer.set(
        ((pt.clientX - r.left) / r.width) * 2 - 1,
        ((pt.clientY - r.top) / r.height) * 2 - 1,
      );
    };
    el.addEventListener('pointermove', this._onPointer, { passive: true });
    el.addEventListener('pointerdown', this._onPointer, { passive: true });
    el.addEventListener('pointerleave', () => this._pointer.set(0, 0), { passive: true });
  }

  _startLoop() {
    if (this._raf || this.disposed) return;
    this._last = performance.now();
    this.renderer.setAnimationLoop((now) => this._tick(now));
  }

  _stopLoop() {
    if (!this.renderer) return;
    this.renderer.setAnimationLoop(null);
    this._raf = 0;
  }

  _tick(now) {
    const dt = Math.min(0.05, (now - (this._last || now)) / 1000);
    this._last = now;
    this._t += dt;

    this._decayEnvelope(dt);
    this._updateBlink(dt);
    this._applyMorphs(dt);
    this.applyPose(dt);
    this.renderer.render(this.scene, this.camera);
  }

  /**
   * Parpadeo natural: ciclos open → closing → closed → opening con tiempos
   * aleatorios. Más lento cuando Daniela está "pensando".
   */
  _updateBlink(dt) {
    const b = this._blink;
    b.t += dt;
    const slow = this.state === 'thinking' ? 1.8 : 1.0;
    if (b.phase === 'open') {
      this._blinkValue = 0;
      if (b.t > b.next) {
        b.phase = 'closing';
        b.t = 0;
      }
    } else if (b.phase === 'closing') {
      const k = Math.min(1, b.t / 0.12);
      this._blinkValue = k;
      if (k >= 1) {
        b.phase = 'closed';
        b.t = 0;
      }
    } else if (b.phase === 'closed') {
      this._blinkValue = 1;
      if (b.t > 0.06) {
        b.phase = 'opening';
        b.t = 0;
      }
    } else {
      const k = Math.min(1, b.t / 0.16);
      this._blinkValue = 1 - k;
      if (k >= 1) {
        b.phase = 'open';
        b.t = 0;
        b.next = (2.2 + Math.random() * 3.2) * slow;
      }
    }
  }

  /**
   * Escribe las influencias de los morph targets del GLB rigged:
   * jawOpen sigue el envelope de voz, blink el parpadeo, browUp el estado.
   * Sin GLB rigged (fallback estático) no hace nada.
   */
  _applyMorphs(dt) {
    if (!this._morphMesh || !this._morphDict) return;
    const d = this._morphDict;
    const inf = this._morphMesh.morphTargetInfluences;
    if (d.jawOpen !== undefined) {
      inf[d.jawOpen] = Math.min(1, this.envelope * 1.15);
    }
    if (d.blink !== undefined) {
      inf[d.blink] = this._blinkValue;
    }
    if (d.browUp !== undefined) {
      const target = this.state === 'thinking' ? 0.7 : 0;
      this._browValue += (target - this._browValue) * Math.min(1, dt * 6);
      inf[d.browUp] = this._browValue;
    }
  }

  /**
   * Aplica la pose procedural del frame actual. Es el único punto que toca el
   * transform; si el modelo llega a tener rig, se reemplaza por AnimationMixer.
   */
  applyPose(dt) {
    const p = PROFILE[this.state] || PROFILE.idle;
    const t = this._t * p.speed;

    // Respiración: escala mínima en Y + traslación vertical.
    const breath = Math.sin(t * 1.7) * p.breathe;
    this.pivot.scale.set(1 + breath * 0.006, 1 + breath * 0.011, 1 + breath * 0.006);
    this.pivot.position.y = breath * 0.008;

    // Balanceo lento de postura.
    const sway = Math.sin(t * 0.62) * p.sway;
    const tilt = p.tilt + Math.sin(t * 0.9 + 1.3) * 0.022 * p.sway;

    // Sacádicas: cada pocos segundos Daniela mira un punto distinto. Da la
    // sensación de atención sin animación facial.
    if (t > this._saccade.next) {
      this._saccade.yaw = (Math.random() - 0.5) * 0.34;
      this._saccade.pitch = (Math.random() - 0.5) * 0.14;
      this._saccade.next = t + 2.2 + Math.random() * 3.4;
    }

    // La mirada sigue al puntero con amortiguación, y se superpone a la sacádica.
    const wantYaw = THREE.MathUtils.clamp(this._pointer.x * 0.55 + this._saccade.yaw, -0.7, 0.7);
    const wantPitch = THREE.MathUtils.clamp(-this._pointer.y * 0.3 + this._saccade.pitch, -0.35, 0.35);
    const k = 1 - Math.exp(-dt * 4.5);
    this._look.x += (wantYaw - this._look.x) * k;
    this._look.y += (wantPitch - this._look.y) * k;

    // Micro-cabeceada ligada al volumen de voz.
    const env = this.envelope;
    const bob = Math.sin(t * 11.3) * 0.016 * p.bob * env;
    const roll = Math.sin(t * 7.1 + 0.9) * 0.05 * p.bob * env;

    this.pivot.rotation.set(
      this._look.y + tilt + bob,
      this._look.x * 0.75 + sway * 0.12 + roll,
      this._look.x * 0.08 + Math.sin(t * 0.5) * 0.012,
    );

    this._applyGlow(p.glow + env * 0.35);
  }

  _applyGlow(amount) {
    if (!this._baseMaterials) return;
    for (const m of this._baseMaterials) {
      if (!m.emissive) continue;
      const base = m.userData.baseEmissive;
      if (base) m.emissive.copy(base);
      // Tinte frío de "presencia digital", coherente con la paleta de la app.
      m.emissive.r += amount * 0.22;
      m.emissive.g += amount * 0.5;
      m.emissive.b += amount * 1.0;
      m.emissiveIntensity = 1;
    }
  }

  _decayEnvelope(dt) {
    if (this._analyser) {
      const buf = new Uint8Array(this._analyser.frequencyBinCount);
      this._analyser.getByteTimeDomainData(buf);
      let sum = 0;
      for (let i = 0; i < buf.length; i++) {
        const v = (buf[i] - 128) / 128;
        sum += v * v;
      }
      const rms = Math.sqrt(sum / buf.length);
      // Raíz + suavizado: la voz tiene silencios entre palabras.
      const target = Math.min(1, Math.sqrt(rms) * 3.2);
      this.envelope += (target - this.envelope) * (target > this.envelope ? 0.55 : 0.12);
      return;
    }
    // Sin analyser (p. ej. speechSynthesis no expone audio): envoltura sintética
    // que marca sílabas con frecuencias incommensurables para que no oscile rítmico.
    if (this.state !== 'talking') {
      this.envelope += (0 - this.envelope) * Math.min(1, dt * 6);
      return;
    }
    const t = this._t;
    const env =
      0.5 +
      0.28 * Math.sin(t * 12.7) +
      0.16 * Math.sin(t * 21.3 + 1.1) +
      0.06 * Math.sin(t * 5.9 + 2.4);
    this.envelope = Math.max(0, Math.min(1, env));
  }

  /** Cambia el estado de animación. Devuelve el estado aplicado. */
  setState(name) {
    this.state = AVATAR_STATES.includes(name) ? name : 'idle';
    return this.state;
  }

  /**
   * Fuerza el volumen de voz (0..1) desde fuera. Útil si el TTS llega como
   * stream sin AnalyserNode. Se decae solo si durante 300ms no llega nada.
   */
  setEnvelope(v) {
    this.envelope = Math.max(0, Math.min(1, Number(v) || 0));
    this._lastExternalEnvelope = performance.now();
  }

  /**
   * Habla con la voz del dispositivo (Web Speech API, funciona offline).
   * Mantiene el estado `talking` mientras dura la locución.
   */
  speak(text, { lang = 'es-ES', rate = 1.0, pitch = 1.05 } = {}) {
    if (!('speechSynthesis' in window) || !text) return false;
    window.speechSynthesis.cancel();

    const u = new SpeechSynthesisUtterance(text);
    u.lang = lang;
    u.rate = rate;
    u.pitch = pitch;
    u.onend = () => this.setState('idle');
    u.onerror = () => this.setState('idle');
    this._utterance = u;

    this.setState('talking');
    window.speechSynthesis.speak(u);
    return true;
  }

  /**
   * Habla una locución ya sintetizada por el servidor (mp3/wav) y, si el
   * navegador lo permite, engancha un AnalyserNode para sincronizar el
   * movimiento con la amplitud real de la voz.
   */
  async speakAudio(url) {
    if (!url) return false;
    this.stopSpeaking();

    const AC = window.AudioContext || window.webkitAudioContext;
    if (!AC) return false;

    try {
      this._audioCtx = this._audioCtx || new AC();
      await this._audioCtx.resume();

      const res = await fetch(url);
      const buf = await res.arrayBuffer();
      const audio = await this._audioCtx.decodeAudioData(buf);

      const src = this._audioCtx.createBufferSource();
      src.buffer = audio;
      const analyser = this._audioCtx.createAnalyser();
      analyser.fftSize = 512;
      analyser.smoothingTimeConstant = 0.6;
      src.connect(analyser);
      analyser.connect(this._audioCtx.destination);

      src.onended = () => {
        if (this._activeSource === src) {
          this._activeSource = null;
          this._analyser = null;
          this.setState('idle');
        }
      };

      this._activeSource = src;
      this._analyser = analyser;
      this.setState('talking');
      src.start(0);
      return true;
    } catch {
      this.setState('idle');
      return false;
    }
  }

  /**
   * Habla un texto con la voz neural del servidor (edge-tts) y sincroniza
   * la boca con el audio real. Si el TTS falla (sin red, sin edge-tts),
   * cae a `speak()` (voz del dispositivo). Devuelve true si está hablando;
   * el estado vuelve a idle solo al terminar.
   */
  async hablarTTS(texto) {
    const t = String(texto || '').trim().slice(0, 1000);
    if (!t) return false;
    try {
      const r = await fetch('/api/voice/tts', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text: t }),
      });
      if (!r.ok) throw new Error(`TTS HTTP ${r.status}`);
      const blob = await r.blob();
      const url = URL.createObjectURL(blob);
      const ok = await this.speakAudio(url);
      URL.revokeObjectURL(url);
      if (ok) return true;
    } catch {
      /* sin red o sin edge-tts: cae al fallback */
    }
    return this.speak(t);
  }

  stopSpeaking() {
    try {
      window.speechSynthesis?.cancel();
    } catch { /* noop */ }
    if (this._activeSource) {
      try { this._activeSource.stop(); } catch { /* ya detenido */ }
      this._activeSource = null;
    }
    this._analyser = null;
    this.envelope = 0;
    if (this.state === 'talking') this.setState('idle');
  }

  /** Libera GPU, observers y audio. Llamar al salir de la vista. */
  dispose() {
    this.disposed = true;
    this.stopSpeaking();
    this._stopLoop();

    window.removeEventListener('resize', this._onResize || (() => {}));
    this._ro?.disconnect();
    document.removeEventListener('visibilitychange', this._onVis);

    if (this.renderer) {
      const el = this.renderer.domElement;
      if (this._onPointer) el.removeEventListener('pointermove', this._onPointer);
      this.scene?.traverse((o) => {
        if (!o.isMesh) return;
        o.geometry?.dispose();
        const mats = Array.isArray(o.material) ? o.material : [o.material];
        mats.forEach((m) => m?.dispose());
      });
      this._envRT?.dispose();
      this.renderer.dispose();
      el.remove();
    }

    this.model = null;
    this.scene = null;
    this.camera = null;
    this.renderer = null;
  }
}

/**
 * Helper de montaje con fallback: si no hay WebGL o el .glb no carga, ejecuta
 * `onFallback` en vez de dejar un hueco negro.
 *
 * @returns {Promise<DanielaAvatar|null>}
 */
export async function mountDanielaAvatar(container, opts = {}) {
  const avatar = new DanielaAvatar(container, opts);
  try {
    await avatar.mount();
    return avatar;
  } catch (err) {
    console.warn('[DanielaAvatar] no disponible:', err);
    avatar.dispose();
    opts.onFallback?.(err);
    return null;
  }
}
