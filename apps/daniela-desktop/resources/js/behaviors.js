/**
 * behaviors.js - las conductas de Daniela en el escritorio.
 *
 * Este modulo NO dibuja nada: decide *que estado* debe tener el avatar, *que
 * morphs* pedir y *que decir*. `app.js` lo consulta en cada frame.
 *
 * Tres capas, de menos a mas invasiva:
 *
 *   1. AMBIENTE   - siempre activa. Respiracion, sacadidas, circadiano,
 *                   fatiga. No interrumpe nunca.
 *   2. DESCANSO   - cuando lleva encendida sin atencion. Fases de
 *                   aburrimiento con micro-acciones que dependen de la
 *                   semilla.
 *   3. PROACTIVA  -ahead de tiempo. Solo si el perfil lo permite.
 *
 * El PRNG es el del avatar (misma semilla): la secuencia de bostezos es
 * distinta en cada instalacion pero estable entre reinicios.
 */

// ── Perfiles de personalidad ────────────────────────────────────────
// Multiplicadores sobre los parametros globales. Un perfil solo cambia COMO se
// mide el exceso, nunca el motor: asi los cinco comparten el mismo codigo.

export const PERFILES = {
  companion: {
    etiqueta: 'Companera',
    conversacion: 1.0,
    proactividad: 0.7,
    aburrimiento: 1.0,
  },
  focus: {
    etiqueta: 'Deep Work',
    conversacion: 0.25,
    proactividad: 0.1,
    aburrimiento: 0.4,
  },
  mentor: {
    etiqueta: 'Mentor',
    conversacion: 1.3,
    proactividad: 0.8,
    aburrimiento: 0.9,
  },
  playful: {
    etiqueta: 'Juguetona',
    conversacion: 1.1,
    proactividad: 0.6,
    aburrimiento: 1.6,
  },
  guardian: {
    etiqueta: 'Guardiana',
    conversacion: 0.6,
    proactividad: 0.5,
    aburrimiento: 0.5,
  },
};

// ── Micro-acciones del aburrimiento ─────────────────────────────────
// Cada una es una pequena coreografia. `dur` en ms. La semilla elige CUAL de
// las posibles, no el contenido: con la misma semilla bosteza siempre igual.

const MICRO = {
  bostezar:      { dur: 1600, etiqueta: 'bosteza' },
  tararear:      { dur: 1400, etiqueta: 'tararea' },
  mirar_reloj:   { dur: 1800, etiqueta: 'mira el reloj' },
  balanceo:      { dur: 2200, etiqueta: 'se balancea' },
  rascar:        { dur: 1500, etiqueta: 'se rasca' },
  contar:        { dur: 2000, etiqueta: 'cuenta' },
  suspiro:       { dur: 1200, etiqueta: 'suspira' },
  estira_cuello: { dur: 1600, etiqueta: 'estira el cuello' },
};

const CLAVES = Object.keys(MICRO);

export class Conductas {
  /**
   * @param {object} o
   * @param {() => number} o.azar              PRNG del avatar (misma semilla).
   * @param {() => string} o.estadoActual
   * @param {(e:string, d?:object) => void} o.decir  burbuja + voz.
   * @param {(s:string) => void} [o.alCambiarEstado]
   */
  constructor(o) {
    this.azar = o.azar;
    this.estadoActual = o.estadoActual;
    this.decir = o.decir || (() => {});
    this.alCambiarEstado = o.alCambiarEstado || (() => {});

    this.cfg = {
      perfil: 'companion',
      // Minutos sin actividad del usuario antes de dormir.
      autoSleepMin: 30,
      // Segundos encendida antes de empezar a aburrirse.
      timeoutAburlo: 45,
      hablarAlDespertar: true,
      celebrarLogros: true,
      microAcciones: true,
      notarVentanaActiva: true,
      seguirCursor: true,
    };

    this._t = 0;
    this._ultimaInteraccion = 0;
    this._micro = null;
    this._proximaMicro = 0;
    this._ultimaVentana = null;
    this._ventanaDistinta = 0;
    this._ultimoEvento = 0;

    this._cara = { smile: 0, furrow: 0, sigh: 0 };
    this._objetivoCara = { smile: 0, furrow: 0, sigh: 0 };
    this._curva = 'estandar';
    this._curvaT = 0;
    this._curvaDur = 0;

    this._obj = { circ: 1, fatiga: 0 };
  }

  configurar(cfg) {
    Object.assign(this.cfg, cfg || {});
  }

  get perfil() {
    return PERFILES[this.cfg.perfil] || PERFILES.companion;
  }

  /** Probabilidad de doble parpadeo segun perfil: juguetona mas viva, focus casi nada. */
  get tasaDobleParpadeo() {
    switch (this.cfg.perfil) {
      case 'playful': return 0.22;
      case 'companion': return 0.14;
      case 'mentor': return 0.10;
      case 'guardian': return 0.08;
      case 'focus': return 0.05;
      default: return 0.12;
    }
  }

  /** Interaccion del usuario: reinicia aburrimiento y el reloj de inactividad. */
  toque() {
    this._ultimaInteraccion = this._t;
    const e = this.estadoActual();
    // Despertar de aburrida/dormida es un EVENTO (curva), no un estado nuevo.
    if (e === 'resting' || e === 'sleeping') {
      this._curva = 'despertar';
      this._curvaT = 0;
      this._curvaDur = 800;
    }
  }

  /** Curva cinematica puntual (logro, error, saludo). */
  chispa(tipo, dur = 1400) {
    this._curva = tipo;
    this._curvaT = 0;
    this._curvaDur = dur;
  }

  /**
   * Avanza la simulacion. Devuelve la cara a aplicar este frame.
   * @param {number} dt segundos
   */
  tick(dt) {
    this._t += dt;
    const p = this.perfil;
    const e = this.estadoActual();

    this._curvaT += dt * 1000;
    this._avanzarCurva();
    this._ambiente(dt);
    this._aburrimiento(dt, e, p);
    this._curiosidad();
    this._mezclarCara(dt);

    return this._cara;
  }

  // ── 1. Ambiente ──────────────────────────────────────────────

  /**
   * Fatiga y circadiano. No cambia de estado (eso lo decide `autoSleepMin`);
   * solo modula como se mueve, para que 40 minutos seguidos no se vean como
   * 40 minutos identicos.
   */
  _ambiente(dt) {
    const inactivoMin = (this._t - this._ultimaInteraccion) / 60;

    // Circadiano: manana fria y energetica, noche lenta.
    const hora = new Date().getHours();
    let circ = 1;
    if (hora >= 6 && hora < 12) circ = 1.15;
    else if (hora >= 12 && hora < 18) circ = 1.0;
    else if (hora >= 18 && hora < 23) circ = 0.9;
    else circ = 0.7;

    // Fatiga: a partir de 90 min sin tocar nada, la postura se encorva.
    this._obj.fatiga = Math.min(1, Math.max(0, (inactivoMin - 90) / 60));
    this._obj.circ = circ;

    if (this._ventanaDistinta > 0) this._ventanaDistinta = Math.max(0, this._ventanaDistinta - dt * 2);
  }

  /** El WebView avisa de la ventana activa de Windows. */
  notarVentana(titulo) {
    if (titulo === this._ultimaVentana) return false;
    this._ultimaVentana = titulo;
    this._ventanaDistinta = 1;
    return true;
  }

  /**
   * Curiosidad: al notar una ventana nueva, cejas un poco arriba y amago de
   * sonrisa. Se suma ENCIMA de la curva en curso y decae sola con
   * `_ventanaDistinta` (ver `_ambiente`). Si el perfil lo apaga, no hace nada.
   */
  _curiosidad() {
    if (this.cfg.notarVentanaActiva === false) return;
    const c = this._ventanaDistinta || 0;
    if (c <= 0.01) return;
    this._objetivoCara.furrow = Math.max(this._objetivoCara.furrow, 0.30 * c);
    this._objetivoCara.smile = Math.max(this._objetivoCara.smile, 0.18 * c);
  }

  // ── 2. Aburrimiento / descanso ───────────────────────────────

  _aburrimiento(dt, estado, perfil) {
    const inactivo = this._t - this._ultimaInteraccion;

    // Dormir: mucho rato sin actividad. Es el estado mas barato y el que hace
    // que el avatar "no moleste" cuando no se le usa.
    if (this.cfg.autoSleepMin > 0 && inactivo > this.cfg.autoSleepMin * 60) {
      if (estado !== 'sleeping') this._cambiar('sleeping');
      this._micro = null;
      return;
    }

    // Dormida solo se despierta por interaccion real, no por el paso del tiempo.
    if (estado === 'sleeping') return;

    // Encendida sin atencion: empieza el aburrimiento.
    const umbral = this.cfg.timeoutAburlo * perfil.aburrimiento;
    if (estado === 'idle' && inactivo > umbral) {
      this._curva = 'descanso';
      this._curvaT = 0;
      this._curvaDur = 1000;
      this._cambiar('resting');
      this._proximaMicro = 0;
      return;
    }

    if (estado !== 'resting') return;

    if (this._micro) {
      this._micro.t += dt * 1000;
      if (this._micro.t >= MICRO[this._micro.nombre].dur) {
        this._micro = null;
        this._proximaMicro = this._t + this._gapAburrimiento(inactivo - umbral);
      }
      return;
    }

    if (this.cfg.microAcciones && this._t >= this._proximaMicro) {
      this._micro = { nombre: CLAVES[(this.azar() * CLAVES.length) | 0], t: 0 };
    }
  }

  /**
   * Cada vez mas espaciado: al principio bosteza cada ~12 s, a los cinco
   * minutos casi nunca. Los ultimos minutos tienen que estar callados.
   */
  _gapAburrimiento(lleva) {
    const base = 12 * this.perfil.aburrimiento;
    const rampa = 1 + Math.min(6, lleva / 45);
    return this._t + base * rampa * (0.6 + this.azar() * 0.8);
  }

  // ── 3. Proactiva ─────────────────────────────────────────────

  /**
   * Daniela habla sin que le pregunten. Rate-limited, para que sea compania y
   * no un bot de notificaciones.
   *
   * @param {string} texto
   * @param {{importante?:boolean}} [opts]
   */
  proponer(texto, opts = {}) {
    const ahora = this._t;
    const minimo = opts.importante ? 20 : 45 / Math.max(0.05, this.perfil.proactividad);
    if (ahora - this._ultimoEvento < minimo) return false;
    this._ultimoEvento = ahora;
    this.decir(texto);
    return true;
  }

  /** Celebracion: solo si el perfil la tiene activa. */
  celebrar(texto) {
    if (!this.cfg.celebrarLogros) return false;
    this._ultimoEvento = this._t;
    this.chispa('logro', 1800);
    this.decir(texto);
    return true;
  }

  // ── Curvas de expresion ──────────────────────────────────────

  _avanzarCurva() {
    const u = this._curvaDur > 0 ? Math.min(1, this._curvaT / this._curvaDur) : 1;

    switch (this._curva) {
      case 'despertar':
        // Sorpresa (0..0.35) -> orientacion (0.35..0.6) -> sonrisa.
        this._objetivoCara.smile = u < 0.35 ? 0 : Math.min(1, (u - 0.35) / 0.65);
        this._objetivoCara.furrow = u < 0.2 ? 1 - u / 0.2 : 0;
        this._objetivoCara.sigh = 0;
        break;

      case 'logro':
        // Sonrisa que sube y baja, como si contuviera el aliento.
        this._objetivoCara.smile = Math.sin(u * Math.PI);
        this._objetivoCara.furrow = 0;
        this._objetivoCara.sigh = 0;
        break;

      case 'sospeso':
        this._objetivoCara.smile = 0;
        this._objetivoCara.furrow = u < 0.5 ? u * 2 : (1 - u) * 2;
        this._objetivoCara.sigh = 0;
        break;

      case 'descanso':
        // Entra al descanso: suspiro y cejas de fastidio.
        this._objetivoCara.sigh = u < 0.4 ? u / 0.4 : Math.max(0, 1 - (u - 0.4) / 0.6);
        this._objetivoCara.furrow = u < 0.3 ? (u / 0.3) * 0.4 : 0.4 * Math.max(0, 1 - (u - 0.3) / 0.7);
        this._objetivoCara.smile = 0;
        break;

      default: {
        // Estandar + micro-accion en curso.
        const m = this._micro;
        this._objetivoCara.smile = 0;
        this._objetivoCara.furrow = m ? 0.25 : 0;
        this._objetivoCara.sigh =
          m?.nombre === 'suspiro' || m?.nombre === 'estira_cuello' ? 1 : 0;

        // El bostezo se apoya en la mandibula (jawOpen), no en la cara.
        if (m?.nombre === 'bostezar') this._objetivoMandibula = 0.85;
      }
    }

    if (this._curvaDur > 0 && u >= 1 && this._curva !== 'estandar') {
      this._curva = 'estandar';
      this._curvaT = 0;
      this._curvaDur = 0;
    }
  }

  /** Mandibula extra para bostezos: 0..1, se amortigua sola. */
  get mandibulaExtra() {
    if (this._micro?.nombre !== 'bostezar') return 0;
    const u = Math.min(1, this._micro.t / MICRO.bostezar.dur);
    return Math.sin(u * Math.PI);
  }

  /** Amortigua la cara hacia el objetivo: los cambios son suaves, no a saltos. */
  _mezclarCara(dt) {
    const k = 1 - Math.exp(-6 * dt);
    for (const n of Object.keys(this._cara)) {
      this._cara[n] += (this._objetivoCara[n] - this._cara[n]) * k;
    }
  }

  _cambiar(estado) {
    this.alCambiarEstado(estado);
  }

  // ── Consulta para la UI ──────────────────────────────────────

  /** Snapshot para el HUD de debug o para tests. */
  snapshot() {
    const inactivo = this._t - this._ultimaInteraccion;
    return {
      t: this._t,
      inactivo,
      micro: this._micro
        ? { ...this._micro, etiqueta: MICRO[this._micro.nombre].etiqueta }
        : null,
      cara: { ...this._cara },
      objetivo: { ...this._objetivoCara },
      curva: this._curva,
      ventana: this._ultimaVentana,
      perfil: this.cfg.perfil,
      ambiente: { ...this._obj },
    };
  }
}

export { MICRO };