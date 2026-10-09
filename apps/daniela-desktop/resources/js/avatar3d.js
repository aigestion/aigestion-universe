/**
 * avatar3d.js — motor 3D de Daniela para escritorio.
 *
 * Derivado de `frontend/apps/android-app/mobile-app/js/daniela-avatar.js` (el
 * que ya funciona en el movil) y extendido con:
 *
 *   - Estado `resting` (aburrimiento/descanzo) con micro-acciones.
 *   - Estados `sleeping` (dormida) y `listening`.
 *   - Curvas de transicion por estado, en vez de un perfil plano.
 *
 * ─────────────────────────────────────────────────────────────────────────────
 * MORPHS: REALES vs APROXIMADOS
 * ─────────────────────────────────────────────────────────────────────────────
 * `assets/daniela3d_rigged.glb` (generado por `scripts/avatar/rig_daniela.py`)
 * solo trae TRES morph targets:
 *
 *     blink  -> parpados
 *     jawOpen -> mandibula
 *     browUp  -> cejas
 *
 * `browFurrow`, `smile`, `sigh` y `browDown` NO existen en el modelo. Se
 * aproximan de forma procedural (rotacion de cabeza, cierre parcial de
 * parpados, tinte del material) y estan marcados como tales en `_applyFace`.
 * Cuando se re-riggee el GLB con esos morphs bastamapearlos en
 * `_MORPHS_REALES` y el resto del codigo no cambia.
 */

import * as THREE from 'three';
import { GLTFLoader } from '../lib/GLTFLoader.js';
import { RoomEnvironment } from '../lib/RoomEnvironment.js';
import { MeshoptDecoder } from '../lib/MeshoptDecoder.js';

export const ESTADOS = [
  'sleeping',
  'idle',
  'listening',
  'thinking',
  'talking',
  'resting',
];

/** Morphs que el GLB rigged expone de verdad. */
const _MORPHS_REALES = new Set(['blink', 'jawOpen', 'browUp']);

/**
 * Perfil por estado. Todo lo que multiplica la amplitud es relativo a 1.
 * `tilt` en radianes (signo = hacia delante), `glow` 0..1.
 */
const PERFIL = {
  sleeping: { respira: 0.35, balanceo: 0.15, tilt: 0.10, glow: 0.00, vel: 0.35, parpadeo: 3.4 },
  idle:     { respira: 1.00, balanceo: 1.00, tilt: 0.00, glow: 0.02, vel: 1.00, parpadeo: 1.0 },
  listening: { respira: 1.30, balanceo: 0.50, tilt: -0.05, glow: 0.08, vel: 1.15, parpadeo: 1.2 },
  thinking: { respira: 0.80, balanceo: 0.30, tilt: 0.07, glow: 0.05, vel: 0.70, parpadeo: 1.8 },
  talking:  { respira: 1.50, balanceo: 0.70, tilt: 0.00, glow: 0.16, vel: 1.40, parpadeo: 1.0 },
  resting:  { respira: 0.55, balanceo: 0.18, tilt: -0.13, glow: 0.01, vel: 0.60, parpadeo: 2.6 },
};

/** Transicion hacia cada estado: amortiguacion del morph y duracion del cambio. */
const CURVA = {
  sleeping: { k: 1.2 },
  idle: { k: 5.0 },
  listening: { k: 8.0 },
  thinking: { k: 7.0 },
  talking: { k: 14.0 },
  resting: { k: 1.6 },
};

const MODELO = 'assets/daniela3d_rigged.glb';
const MODELO_FALLBACK = 'assets/daniela3d.glb';

export class Avatar3D {
  /**
   * @param {HTMLElement} contenedor
   * @param {object} [opts]
   * @param {(p:number)=>void} [opts.onProgress]
   * @param {(err:Error)=>void} [opts.onError]
   * @param {()=>void} [opts.onReady]
   * @param {boolean} [opts.reducido] Respeta prefers-reduced-motion.
   */
  constructor(contenedor, opts = {}) {
    this.cont = contenedor;
    this.opts = opts;
    this.estado = 'sleeping';
    this.listo = false;
    this.tirado = false;

    /** Envolvente de voz 0..1: mueve la mandibula. */
    this.envoltura = 0;

    /** Semilla: fija el azar para que la "personalidad" sea estable. */
    this.semilla = opts.semilla ?? ((Math.random() * 1e9) | 0);
    this._rng = mulberry32(this.semilla);

    this._t = 0;
    this._ultimo = 0;
    this._puntero = new THREE.Vector2(0, 0);
    this._mirada = new THREE.Vector2(0, 0);
    this._sacada = { yaw: 0, pitch: 0, proximo: 0 };
    this._audioCtx = null;
    this._analizador = null;
    this._fuente = null;
    this._locucion = null;

    // Morphs
    this._mallaMorph = null;
    this._dicMorph = null;
    this._valores = { blink: 0, jawOpen: 0, browUp: 0 };
    this._objetivo = { blink: 0, jawOpen: 0, browUp: 0 };
    this._parpadeo = { fase: 'abierto', t: 0, proximo: 2.5 };
    // Vivo: seguir cursor (lo apaga el perfil focus), doble parpadeo
    // ocasional y destellos visuales puntuales (logros).
    this.seguirCursor = opts.seguirCursor ?? true;
    this.tasaDobleParpadeo = opts.tasaDobleParpadeo ?? 0.12;
    this._chispa = null;
    this._sombra = null;
  }

  /** Semilla -> PRNG determinista. Misma semilla, mismos tics de aburrimiento. */
  _azar() {
    return this._rng();
  }

  // ── Montaje ───────────────────────────────────────────────────

  async montar() {
    if (this.tirado) throw new Error('avatar descartado');

    try {
      this.renderer = new THREE.WebGLRenderer({
        antialias: true,
        alpha: true,
        powerPreference: 'high-performance',
      });
    } catch (err) {
      this.opts.onError?.(err);
      throw err;
    }

    const dpr = Math.min(window.devicePixelRatio || 1, 2);
    this.renderer.setPixelRatio(dpr);
    this.renderer.toneMapping = THREE.ACESFilmicToneMapping;
    this.renderer.toneMappingExposure = 1.15;
    this.renderer.setClearColor(0x000000, 0);
    this.cont.appendChild(this.renderer.domElement);

    this.escena = new THREE.Scene();
    this.camara = new THREE.PerspectiveCamera(30, 1, 0.05, 50);

    // Sin IBL los materiales con metallic map salen negros: RoomEnvironment
    // aporta el reflejo difuso que hace legible el busto.
    const pmrem = new THREE.PMREMGenerator(this.renderer);
    this._rt = pmrem.fromScene(new RoomEnvironment(), 0.04);
    this.escena.environment = this._rt.texture;
    pmrem.dispose();

    this._luces();

    this.pivote = new THREE.Group();
    this.escena.add(this.pivote);

    const carga = await this._cargarModelo();
    this._redimensionar();

    this._ro = new ResizeObserver(() => this._redimensionar());
    this._ro.observe(this.cont);

    this._visibilidad();
    this._punteroRaton();

    this._bucle();
    this.listo = true;
    this.opts.onReady?.();
    return this;
  }

  _cargarModelo() {
    return new Promise((resolve, reject) => {
      const loader = new GLTFLoader();
      loader.setMeshoptDecoder(MeshoptDecoder);

      const ok = (gltf) => {
        this._prepararModelo(gltf.scene);
        resolve();
      };
      const progreso = (ev) => {
        if (ev.lengthComputable && ev.total) {
          this.opts.onProgress?.(Math.min(1, ev.loaded / ev.total));
        }
      };
      const fallo = (e) => {
        console.warn('[daniela] no cargo el modelo principal, pruebo fallback:', e?.message || e);
        if (MODELO !== MODELO_FALLBACK) {
          loader.load(MODELO_FALLBACK, ok, progreso, (e2) =>
            reject(e2 instanceof Error ? e2 : new Error(String(e2)))
          );
        } else {
          reject(e instanceof Error ? e : new Error(String(e)));
        }
      };

      loader.load(MODELO, ok, progreso, fallo);
    });
  }

  _luces() {
    const clave = new THREE.DirectionalLight(0xffffff, 2.1);
    clave.position.set(1.6, 2.2, 2.0);
    const relleno = new THREE.DirectionalLight(0x9ec5ff, 0.7);
    relleno.position.set(-2.2, 0.6, 1.4);
    const contra = new THREE.DirectionalLight(0xff9ecb, 0.9);
    contra.position.set(-0.6, 1.4, -2.2);
    const hemi = new THREE.HemisphereLight(0xbdd4ff, 0x1b1030, 0.45);
    this.escena.add(clave, relleno, contra, hemi);
    this._luzGlow = [clave, contra];
  }

  _prepararModelo(raiz) {
    const caja = new THREE.Box3().setFromObject(raiz);
    const tam = caja.getSize(new THREE.Vector3());
    const centro = caja.getCenter(new THREE.Vector3());

    raiz.position.sub(centro); // todo gira sobre ella
    this.pivote.add(raiz);
    this.modelo = raiz;
    this._tam = tam;

    this._materiales = [];
    raiz.traverse((o) => {
      if (!o.isMesh) return;
      o.castShadow = false;
      const mats = Array.isArray(o.material) ? o.material : [o.material];
      for (const m of mats) {
        if (!m) continue;
        m.envMapIntensity = 1.15;
        if (m.emissive) m.userData.emissiveBase = m.emissive.clone();
        this._materiales.push(m);
      }
      if (o.morphTargetInfluences?.length) {
        this._mallaMorph = o;
        this._dicMorph = o.morphTargetDictionary;
      }
    });

    this._encuadrar();
    this._sombraContacto();
  }

  /** Encuadre que respeta el eje restrictivo y deja 18% de aire. */
  _encuadrar() {
    const { ancho, alto } = this._vp();
    if (!ancho || !alto) return;
    this.camara.aspect = ancho / alto;

    const fovV = (this.camara.fov * Math.PI) / 180;
    const fovH = 2 * Math.atan(Math.tan(fovV / 2) * this.camara.aspect);
    const dV = this._tam.y / 2 / Math.tan(fovV / 2);
    const dH = this._tam.x / 2 / Math.tan(fovH / 2);
    const dist = (Math.max(dV, dH) * 1.18) / 0.9;

    this.camara.position.set(0, this._tam.y * 0.03, dist);
    this.camara.lookAt(0, 0, 0);
    this.camara.updateProjectionMatrix();
  }

  /** Sombra de contacto procedural: asienta el busto, sin assets ni sombras reales. */
  _sombraContacto() {
    if (!this._tam || this._sombra) return;
    try {
      const c = document.createElement('canvas');
      c.width = 128; c.height = 128;
      const g = c.getContext('2d');
      const grad = g.createRadialGradient(64, 64, 6, 64, 64, 62);
      grad.addColorStop(0, 'rgba(0,0,0,0.55)');
      grad.addColorStop(0.55, 'rgba(0,0,0,0.28)');
      grad.addColorStop(1, 'rgba(0,0,0,0)');
      g.fillStyle = grad;
      g.fillRect(0, 0, 128, 128);
      const tex = new THREE.CanvasTexture(c);
      const mat = new THREE.MeshBasicMaterial({ map: tex, transparent: true, depthWrite: false, opacity: 0.34 });
      const plano = new THREE.Mesh(new THREE.PlaneGeometry(this._tam.x * 1.15, this._tam.x * 1.15), mat);
      plano.rotation.x = -Math.PI / 2;
      plano.position.y = -this._tam.y / 2 - 0.012;
      plano.renderOrder = -1;
      this.escena.add(plano);
      this._sombra = plano;
    } catch { /* sin sombra no pasa nada */ }
  }

  _vp() {
    const r = this.cont.getBoundingClientRect();
    return { ancho: Math.max(1, r.width), alto: Math.max(1, r.height) };
  }

  _redimensionar() {
    if (!this.renderer || !this.camara) return;
    const { ancho, alto } = this._vp();
    this.renderer.setSize(ancho, alto, false);
    if (this._tam) this._encuadrar();
  }

  _visibilidad() {
    this._vis = () => {
      if (document.hidden) this.renderer?.setAnimationLoop(null);
      else if (!this.tirado) this.renderer?.setAnimationLoop((t) => this._tick(t));
    };
    document.addEventListener('visibilitychange', this._vis);
  }

  _punteroRaton() {
    const el = this.renderer.domElement;
    this._onMover = (ev) => {
      const r = el.getBoundingClientRect();
      if (!r.width || !r.height) return;
      this._puntero.set(
        ((ev.clientX - r.left) / r.width) * 2 - 1,
        ((ev.clientY - r.top) / r.height) * 2 - 1
      );
    };
    el.addEventListener('pointermove', this._onMover, { passive: true });
    // Fuera del canvas (ventana 280x280 casi toda es canvas, pero por si
    // acaso): la mirada sigue al cursor de la ventana.
    this._onMoverWin = (ev) => {
      if (!window.innerWidth || !window.innerHeight) return;
      this._puntero.set(
        (ev.clientX / window.innerWidth) * 2 - 1,
        (ev.clientY / window.innerHeight) * 2 - 1
      );
    };
    window.addEventListener('pointermove', this._onMoverWin, { passive: true });
    this._el = el;
  }

  // ── Bucle ────────────────────────────────────────────────────

  _bucle() {
    this._ultimo = performance.now();
    this.renderer.setAnimationLoop((now) => this._tick(now));
  }

  _tick(now) {
    const dt = Math.min(0.05, (now - (this._ultimo || now)) / 1000);
    this._ultimo = now;
    this._t += dt;

    this._decaerEnvoltura(dt);
    this._tickParpadeo(dt);
    this._aplicarMorphs(dt);
    this.aplicarPose(dt);
    this.renderer.render(this.escena, this.camara);
  }

  /**
   * Parpadeo con fases open -> closing -> closed -> opening y tiempos
   * aleatorios. Mas lento cuando esta dormida o aburrida.
   */
  _tickParpadeo(dt) {
    const b = this._parpadeo;
    b.t += dt;
    const p = PERFIL[this.estado] || PERFIL.idle;
    const lento = p.parpadeo;

    if (b.fase === 'abierto') {
      if (b.t > b.proximo) {
        b.fase = 'cerrando';
        b.t = 0;
      }
    } else if (b.fase === 'cerrando') {
      const k = Math.max(0, Math.min(1, b.t / 0.12));
      this._objetivo.blink = k;
      if (k >= 1) {
        b.fase = 'cerrado';
        b.t = 0;
      }
    } else if (b.fase === 'cerrado') {
      this._objetivo.blink = 1;
      if (b.t > 0.06) {
        b.fase = 'abriendo';
        b.t = 0;
      }
    } else {
      const k = Math.min(1, b.t / 0.16);
      this._objetivo.blink = 1 - k;
      if (k >= 1) {
        // Doble parpadeo ocasional: parece vivo, no robotico.
        if (this._azar() < (this.tasaDobleParpadeo || 0)) {
          b.fase = 'cerrando';
          b.t = -0.12; // micro-pausa antes del segundo parpadeo
        } else {
          b.fase = 'abierto';
          b.t = 0;
          b.proximo = (2.2 + this._azar() * 3.2) * lento;
        }
      }
    }
  }

  /**
   * Escribe los morphs reales. Los aproximados se resuelven aqui tambien para
   * que el estado de la cara viva en un solo sitio.
   */
  _aplicarMorphs(dt) {
    const k = (CURVA[this.estado] || CURVA.idle).k;
    const m = 1 - Math.exp(-k * dt);

    for (const nombre of Object.keys(this._valores)) {
      this._valores[nombre] += (this._objetivo[nombre] - this._valores[nombre]) * m;
    }

    // La mandibula sigue la voz con ataque rapido y caida suave: la voz tiene
    // silencios entre palabras y una caida rapida se ve como mueca.
    this._valores.jawOpen += (this.envoltura * 1.15 - this._valores.jawOpen) *
      (this.envoltura > this._valores.jawOpen ? 0.55 : 0.12);

    if (!this._mallaMorph || !this._dicMorph) return;
    const inf = this._mallaMorph.morphTargetInfluences;
    const d = this._dicMorph;
    if (d.blink !== undefined) inf[d.blink] = this._valores.blink;
    if (d.jawOpen !== undefined) inf[d.jawOpen] = Math.min(1, this._valores.jawOpen);
    if (d.browUp !== undefined) inf[d.browUp] = this._valores.browUp;
  }

  /**
   * Pose procedural. Es el UNICO punto que toca el transform del pivote; si el
   * modelo llegara a tener un esqueleto, aqui se sustituiria por AnimationMixer.
   *
   * @param {number} dt
   * @param {object} [cara] Aproximaciones de expression: `{smile, furrow, sigh}`.
   */
  aplicarPose(dt, cara = {}) {
    const p = PERFIL[this.estado] || PERFIL.idle;
    const t = this._t * p.vel;
    const suave = this.opts.reducido === true;

    // --- respiracion ---
    const resp = Math.sin(t * 1.7) * p.respira;
    this.pivote.scale.set(1 + resp * 0.006, 1 + resp * 0.011, 1 + resp * 0.006);
    this.pivote.position.y = resp * 0.008;
    if (this._sombra) {
      const s = 1 + resp * 0.012;
      this._sombra.scale.set(s, 1, s);
      this._sombra.material.opacity = 0.34 - resp * 0.010;
    }

    // --- balanceo de postura ---
    const balanceo = suave ? 0 : Math.sin(t * 0.62) * p.balanceo;
    const tilt = p.tilt + (suave ? 0 : Math.sin(t * 0.9 + 1.3) * 0.022 * p.balanceo);

    // --- aproximaciones de expresion (el GLB no las tiene) ---
    // "sigh": suspiro = cabeza atras + mandibula un poco abierta.
    const sigh = cara.sigh || 0;
    // "smile": sonrisa = cabeza ladeada suave + calidez en el material.
    const smile = cara.smile || 0;
    // "furrow": concentracion = entrecerrar los ojos al 35%.
    const furrow = cara.furrow || 0;
    this._objetivo.blink = Math.max(this._objetivo.blink, furrow * 0.35);

    // --- sacadidas ---
    if (t > this._sacada.proximo) {
      const amplitud = this.estado === 'resting' ? 0.5 : 1;
      this._sacada.yaw = (this._azar() - 0.5) * 0.34 * amplitud;
      this._sacada.pitch = (this._azar() - 0.5) * 0.14 * amplitud;
      this._sacada.proximo = t + 2.2 + this._azar() * 3.4;
    }

    const sigo = this.seguirCursor !== false ? 1 : 0;
    const quieroYaw = THREE.MathUtils.clamp(
      this._puntero.x * 0.55 * sigo + this._sacada.yaw, -0.7, 0.7
    );
    const quieroPitch = THREE.MathUtils.clamp(
      -this._puntero.y * 0.3 * sigo + this._sacada.pitch, -0.35, 0.35
    );
    const k = 1 - Math.exp(-dt * 4.5);
    this._mirada.x += (quieroYaw - this._mirada.x) * k;
    this._mirada.y += (quieroPitch - this._mirada.y) * k;

    // --- micro-cabeceada ligada al volumen ---
    const env = this.envoltura;
    const bob = Math.sin(t * 11.3) * 0.016 * (suave ? 0 : 1) * env;
    const roll = Math.sin(t * 7.1 + 0.9) * 0.05 * (suave ? 0 : 1) * env;

    // --- destello puntual (logro/saludo): calidez + sonrisa breve ---
    let chispaCalidez = 0;
    if (this._chispa) {
      this._chispa.t += dt * 1000;
      const u = Math.min(1, this._chispa.t / Math.max(1, this._chispa.dur));
      chispaCalidez = this._chispa.tipo === 'logro' ? Math.sin(u * Math.PI) : 0;
      if (u >= 1) this._chispa = null;
    }
    const sonrisaTotal = Math.min(1, smile + chispaCalidez);

    this.pivote.rotation.set(
      this._mirada.y + tilt + bob - sigh * 0.16 + sonrisaTotal * 0.03,
      this._mirada.x * 0.75 + balanceo * 0.12 + roll + sonrisaTotal * 0.10,
      this._mirada.x * 0.08 + (suave ? 0 : Math.sin(t * 0.5) * 0.012)
    );

    this._glow(p.glow + env * 0.35 + chispaCalidez * 0.25, sonrisaTotal);
  }

  _glow(cantidad, calidez = 0) {
    if (!this._materiales) return;
    for (const m of this._materiales) {
      if (!m.emissive) continue;
      const base = m.userData.emissiveBase;
      if (base) m.emissive.copy(base);
      // Tinte frio de presencia digital; `calidez` lo desplaza a naranja para
      // los momentos cálidos (logros, saludos).
      m.emissive.r += cantidad * 0.22 + calidez * 0.35;
      m.emissive.g += cantidad * 0.50 + calidez * 0.14;
      m.emissive.b += cantidad * 1.00 - calidez * 0.20;
      m.emissiveIntensity = 1;
    }
  }

  _decaerEnvoltura(dt) {
    if (this._analizador) {
      const buf = new Uint8Array(this._analizador.frequencyBinCount);
      this._analizador.getByteTimeDomainData(buf);
      let suma = 0;
      for (let i = 0; i < buf.length; i++) {
        const v = (buf[i] - 128) / 128;
        suma += v * v;
      }
      const rms = Math.sqrt(suma / buf.length);
      const objetivo = Math.min(1, Math.sqrt(rms) * 3.2);
      this.envoltura += (objetivo - this.envoltura) *
        (objetivo > this.envoltura ? 0.55 : 0.12);
      return;
    }
    if (this.estado !== 'talking') {
      this.envoltura += (0 - this.envoltura) * Math.min(1, dt * 6);
      return;
    }
    // speechSynthesis no expone audio: se sintetiza una envolvente con
    // frecuencias incommensurables para que no suene ritmica.
    const t = this._t;
    const env =
      0.5 + 0.28 * Math.sin(t * 12.7) + 0.16 * Math.sin(t * 21.3 + 1.1) +
      0.06 * Math.sin(t * 5.9 + 2.4);
    this.envoltura = Math.max(0, Math.min(1, env));
  }

  // ── API publica ──────────────────────────────────────────────

  /** Cambia de estado. Devuelve el estado realmente aplicado. */
  setEstado(nombre) {
    this.estado = ESTADOS.includes(nombre) ? nombre : 'idle';
    if (this.estado === 'thinking') this._objetivo.browUp = 0.7;
    return this.estado;
  }

  /** Destello visual puntual (logro, saludo): calidez + sonrisa breve. */
  chispaVisual(tipo = 'logro', dur = 1800) {
    this._chispa = { tipo, t: 0, dur };
  }

  /** Fuerza el volumen de voz desde fuera (0..1). */
  setEnvoltura(v) {
    this.envoltura = Math.max(0, Math.min(1, Number(v) || 0));
  }

  /**
   * Habla con la voz del dispositivo. Funciona sin red, que para una
   * asistente local es la garantia importante.
   */
  hablar(texto, { idioma = 'es-ES', velocidad = 1.0, tono = 1.05 } = {}) {
    if (!('speechSynthesis' in window) || !texto) return false;
    window.speechSynthesis.cancel();
    const u = new SpeechSynthesisUtterance(texto);
    u.lang = idioma;
    u.rate = velocidad;
    u.pitch = tono;
    const antes = this.estado;
    u.onend = () => { if (this.estado === 'talking') this.setEstado(antes === 'sleeping' ? 'sleeping' : 'idle'); };
    u.onerror = u.onend;
    this._locucion = u;
    this.setEstado('talking');
    window.speechSynthesis.speak(u);
    return true;
  }

  /**
   * Habla audio ya sintetizado (edge-tts del servidor) y engancha un
   * AnalyserNode para que la boca siga la amplitud real.
   */
  async hablarAudio(url) {
    if (!url) return false;
    this.pararHablar();
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
      const an = this._audioCtx.createAnalyser();
      an.fftSize = 512;
      an.smoothingTimeConstant = 0.6;
      src.connect(an);
      an.connect(this._audioCtx.destination);
      src.onended = () => {
        if (this._fuente === src) {
          this._fuente = null;
          this._analizador = null;
          this.setEstado('idle');
        }
      };
      this._fuente = src;
      this._analizador = an;
      this.setEstado('talking');
      src.start(0);
      return true;
    } catch {
      this.setEstado('idle');
      return false;
    }
  }

  pararHablar() {
    try { window.speechSynthesis?.cancel(); } catch { /* nada */ }
    if (this._fuente) {
      try { this._fuente.stop(); } catch { /* ya parado */ }
      this._fuente = null;
    }
    this._analizador = null;
    this.envoltura = 0;
    if (this.estado === 'talking') this.setEstado('idle');
  }

  /** Libera GPU, observers y audio. */
  dispose() {
    this.tirado = true;
    this.pararHablar();
    this.renderer?.setAnimationLoop(null);
    this._ro?.disconnect();
    document.removeEventListener('visibilitychange', this._vis);
    if (this._el && this._onMover) this._el.removeEventListener('pointermove', this._onMover);
    if (this._onMoverWin) window.removeEventListener('pointermove', this._onMoverWin);

    if (this.renderer) {
      this.escena?.traverse((o) => {
        if (!o.isMesh) return;
        o.geometry?.dispose();
        const mats = Array.isArray(o.material) ? o.material : [o.material];
        mats.forEach((m) => m?.dispose());
      });
      this._rt?.dispose();
      this.renderer.dispose();
      this.renderer.domElement.remove();
    }
    this.modelo = null;
    this.escena = null;
    this.camara = null;
    this.renderer = null;
  }
}

/** PRNG mulberry32: rapido, sin estado global, y reproducible con semilla. */
function mulberry32(semilla) {
  let a = semilla >>> 0;
  return function () {
    a = (a + 0x6d2b79f5) >>> 0;
    let t = a;
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

export { _MORPHS_REALES };