/**
 * app.js - orquestador de la ventana del avatar.
 *
 * Une las tres piezas:
 *   - `Avatar3D`  : dibuja y aplica pose/morphs.
 *   - `Conductas` : decide estado, cara y Cuando hablar.
 *   - Tauri IPC   : estado real compartido, config, capturas.
 *
 * Maquina de clicks (lo pedido):
 *
 *   Dormida --1 clic--> Encendida (idle/listening) --2 clics rapidos--> Vision Menu
 *   Encendida --1 clic--> Descanso (resting: sigh, fastidio, micro-acciones)
 *   Descanso --1 clic--> Encendida (curva 'despertar')
 */

import { Avatar3D, ESTADOS } from './avatar3d.js';
import { Conductas } from './behaviors.js';

const MS_DOBLE_CLIC = 380; // ventana para dos clics

// ── Puente con Tauri ───────────────────────────────────────────────
// Cuando se abre en un navegador (desarrollo, `python -m http.server`), las
// invocaciones no existen. `hayTauri()` decide: en navegador todo cae a no-op
// y el avatar sigue siendo usable (es lo que permite iterar el diseno rapido).

const _cacheInvoke = new Map();

function hayTauri() {
  return typeof window !== 'undefined' && !!window.__TAURI_INTERNALS__;
}

async function invocar(cmd, args) {
  if (!hayTauri()) {
    const stub = _cacheInvoke.get(cmd);
    if (stub) return stub;
    return null;
  }
  // Sin bundler: la API global la inyecta Tauri (`withGlobalTauri: true`).
  return window.__TAURI__.core.invoke(cmd, args);
}

/** Eventos emitidos por Rust (`app.emit(...)`). */
async function alEvento(nombre, cb) {
  if (!hayTauri()) return () => {};
  try {
    const unlisten = await window.__TAURI__.event.listen(nombre, (e) => cb(e.payload));
    return unlisten;
  } catch {
    return () => {};
  }
}

// ── Referencias del DOM ────────────────────────────────────────────

const $ = (id) => document.getElementById(id);

const ui = {
  cont: $('contenedor'),
  indicador: $('indicador'),
  burbuja: $('burbuja'),
  captura: $('indicadorCaptura'),
  menuCtx: $('menuCtx'),
  pista: $('pistaArrastre'),
  entrada: $('entrada'),
  carga: $('carga'),
};

// ── Estado de la app ───────────────────────────────────────────────

const app = {
  avatar: null,
  conductas: null,
  estado: 'sleeping',
  cfg: null,
  ultimoClick: 0,
  arrastrando: false,
  clicSoltado: false,
  izquierda: 0,
  arriba: 0,
  burbujaTemporizador: 0,
  ultimoFrame: 0,
  reduccionMovimiento: false,
};

// ── Burbuja de texto ───────────────────────────────────────────────

function burbuja(texto, ms = 4200) {
  if (!texto) return;
  ui.burbuja.textContent = texto;
  ui.burbuja.classList.add('visible');
  clearTimeout(app.burbujaTemporizador);
  app.burbujaTemporizador = setTimeout(() => {
    ui.burbuja.classList.remove('visible');
  }, ms);
}

/** Hablar = burbuja + voz. La voz se respeta como config, la burbuja no. */
function decir(texto, { voz = true } = {}) {
  burbuja(texto);
  const c = app.cfg?.voice;
  if (!voz || !c?.habilitada || !app.avatar) return;
  // Se deja al backend la voz neuronal si esta configurado; si no, la del
  // dispositivo (funciona sin red).
  app.avatar.hablar(texto, {
    idioma: c.idioma || 'es-ES',
    velocidad: c.velocidad ?? 1,
    tono: c.tono ?? 1.05,
  });
}

// ── Backend: latido ligero cada 15 s, sin molestar ──────────────────
// Pinta el punto de estado con el backend real (`MenuConfig.backend`).
// Si no hay backend, el avatar sigue vivo igual: solo cambia el `title`.
let _backendOk = null;
async function comprobarBackend() {
  const base = (app.cfg?.menu?.backend || 'http://127.0.0.1:9200').replace(/\/$/, '');
  // El core real expone /api/globe/data (200 con datos); /api/health no
  // existe en el stack (503). Se prueba el endpoint real primero.
  const rutas = [`${base}/api/globe/data`, `${base}/`];
  _backendOk = false;
  for (const u of rutas) {
    try {
      const ctrl = new AbortController();
      const t = setTimeout(() => ctrl.abort(), 3000);
      const res = await fetch(u, { signal: ctrl.signal });
      clearTimeout(t);
      if (res.ok) { _backendOk = true; break; }
    } catch { /* siguiente ruta */ }
  }
  ui.indicador.title = `${app.estado}${_backendOk === null ? '' : _backendOk ? ' · backend ok' : ' · sin backend'}`;
  ui.indicador.dataset.backend = _backendOk ? 'ok' : 'off';
}

// ── Cambio de estado ───────────────────────────────────────────────

async function cambiarEstado(nuevo, { propagar = true } = {}) {
  if (!ESTADOS.includes(nuevo)) return;
  app.estado = nuevo;
  app.avatar?.setEstado(nuevo);
  ui.indicador.className = `estado ${nuevo}`;
  ui.indicador.title = nuevo;
  if (propagar) invocar('set_avatar_state', { nuevo }).catch(() => {});
}

// ── Clicks: la maquina de estados del raton ────────────────────────

function alClicIzquierdo(ev) {
  // Click simple vs doble: el doble necesita DOS eventos `click` separados,
  // asi que se cuenta el tiempo desde el anterior.
  const ahora = performance.now();
  const doble = ahora - app.ultimoClick < MS_DOBLE_CLIC;
  app.ultimoClick = ahora;

  app.conductas?.toque();

  const encendida = app.estado !== 'sleeping';

  if (doble) {
    // 2 clics -> vision menu
    abrirMenuVision();
    return;
  }

  if (!encendida) {
    // Dormida -> despierta y escucha.
    cambiarEstado('listening');
    const c = app.cfg?.comportamiento;
    if (c?.hablarAlDespertar !== false) {
      decir('¿Me necesitas?');
    }
    return;
  }

  if (app.estado === 'resting') {
    // Descanso -> despierta.
    cambiarEstado('idle');
    return;
  }

  // Encendida y activa -> se va a descansar (lo pedido: aburrimiento).
  app.conductas.chispa('descanso', 1000);
  cambiarEstado('resting');
}

// ── Menu de vision ─────────────────────────────────────────────────

function abrirMenuVision(pestana = null) {
  invocar('show_menu', { pestana }).catch(() => {});
}

// ── Menu contextual (click derecho) ────────────────────────────────

function alMenuContextual(ev) {
  ev.preventDefault();
  const r = ui.cont.getBoundingClientRect();
  ui.menuCtx.style.left = `${Math.min(ev.clientX - r.left, r.width - 180)}px`;
  ui.menuCtx.style.top = `${Math.min(ev.clientY - r.top, r.height - 160)}px`;
  ui.menuCtx.classList.add('visible');
}

function cerrarMenuCtx() {
  ui.menuCtx.classList.remove('visible');
}

async function accionCtx(accion) {
  cerrarMenuCtx();
  switch (accion) {
    case 'menu': abrirMenuVision(); break;
    case 'descanso':
      app.conductas.chispa('descanso', 1000);
      cambiarEstado('resting');
      break;
    case 'ocultar': invocar('toggle_avatar').catch(() => {}); break;
    case 'captura':
      invocar('start_capture').then((d) => {
        ui.captura.classList.add('activo');
        decir(`Capturando ${d}. Dime qué necesitas.`);
      }).catch((e) => burbuja(`No pude capturar: ${e}`));
      break;
    case 'parar': {
      const st = await invocar('capture_status');
      if (st?.activa) {
        await invocar('stop_capture');
        ui.captura.classList.remove('activo');
        burbuja('Captura detenida.');
      }
      break;
    }
    case 'ajustes': abrirMenuVision('ajustes'); break;
    default: break;
  }
}

// ── Arrastre ───────────────────────────────────────────────────────

async function alBoton(ev) {
  app.arrastrando = true;
  app.clicSoltado = false;
  ui.cont.classList.add('arrastrando');
  app.izquierda = ev.screenX - ui.cont.getBoundingClientRect().left;
  app.arriba = ev.screenY - ui.cont.getBoundingClientRect().top;
}

async function alSoltar() {
  app.arrastrando = false;
  ui.cont.classList.remove('arrastrando');
  // La posicion final se guarda para la proxima sesion.
  // Rust devuelve la tupla (x, y) serializada como array [x, y].
  try {
    const pos = await invocar('get_avatar_position');
    const x = Array.isArray(pos) ? pos[0] : pos?.x;
    const y = Array.isArray(pos) ? pos[1] : pos?.y;
    if (Number.isInteger(x) && Number.isInteger(y)) {
      invocar('set_avatar_position', { x, y }).catch(() => {});
    }
  } catch { /* no pasa nada */ }
}

async function alMover(ev) {
  if (!app.arrastrando) return;
  app.clicSoltado = true;
  // El arrastre nativo de la ventana lo hace Tauri; aqui solo Evangelizamos el
  // desplazamiento para que la ventana "siga" al cursor sin saltos.
  try {
    await window.__TAURI__.window.getCurrentWindow().startDragging();
  } catch {
    // En navegador no hay arrastre de ventana: no hace nada.
  }
  void ev;
}

// ── Bucle de conductas + cara ──────────────────────────────────────

function bucle() {
  const ahora = performance.now();
  const dt = Math.min(0.05, (ahora - (app.ultimoFrame || ahora)) / 1000);
  app.ultimoFrame = ahora;

  if (app.avatar?.listo && app.conductas) {
    const cara = app.conductas.tick(dt);
    const extraMandibula = app.conductas.mandibulaExtra;
    app.avatar.aplicarPose(dt, cara);

    // El bostezo necesita jawOpen, que el avatar escribe desde la envoltura de
    // voz; se le suma aparte para que no se lose al hablar.
    if (extraMandibula > 0.01) {
      app.avatar.envoltura = Math.max(app.avatar.envoltura, extraMandibula);
    }
  }
  requestAnimationFrame(bucle);
}

// ── Arranque ───────────────────────────────────────────────────────

async function arrancar() {
  ui.carga.hidden = false;

  // Config. En navegador se usan los valores por defecto de Rust.
  app.cfg = (await invocar('get_config')) || {
    avatar: { escala: 1, opacidad: 1, autoSleepMin: 30, personalidad: 'companion', timeoutDescanso: 45 },
    voice: { habilitada: true, velocidad: 1, tono: 1.05, volumen: 0.8, idioma: 'es-ES', ttsServidor: true },
    capture: { habilitada: false, confirmarSiempre: true, objetivo: 'monitor', anchoMax: 1600, fps: 10 },
    menu: { pestanaInicial: 'gev', backend: 'http://127.0.0.1:9200' },
    comportamiento: {
      hablarAlDespertar: true, notarVentanaActiva: true, seguirCursor: true,
      celebrarLogros: true, microAcciones: true, semilla: null,
    },
  };

  const sem = app.cfg.comportamiento?.semilla ?? null;
  app.reduccionMovimiento =
    window.matchMedia?.('(prefers-reduced-motion: reduce)').matches === true;

  // ── Avatar ──
  app.avatar = new Avatar3D(ui.cont, {
    semilla: sem ?? undefined,
    reducido: app.reduccionMovimiento,
    seguirCursor: app.cfg.comportamiento?.seguirCursor !== false,
    onProgress: (p) => {
      ui.carga.textContent = `Cargando modelo… ${Math.round(p * 100)}%`;
    },
    onError: (e) => {
      ui.carga.textContent = `Sin 3D: ${e.message}. La ventana sigue viva.`;
    },
  });

  try {
    await app.avatar.montar();
    ui.carga.hidden = true;
  } catch (e) {
    console.warn('[daniela] avatar 3D no disponible:', e);
    ui.carga.hidden = true;
  }

  // ── Conductas ──
  app.conductas = new Conductas({
    azar: () => app.avatar?._azar?.() ?? Math.random(),
    estadoActual: () => app.estado,
    decir,
    alCambiarEstado: (e) => cambiarEstado(e),
  });
  app.conductas.configurar({
    perfil: app.cfg.avatar.personalidad,
    autoSleepMin: app.cfg.avatar.autoSleepMin,
    timeoutAburlo: app.cfg.avatar.timeoutDescanso,
    hablarAlDespertar: app.cfg.comportamiento.hablarAlDespertar,
    celebrarLogros: app.cfg.comportamiento.celebrarLogros,
    microAcciones: app.cfg.comportamiento.microAcciones,
    notarVentanaActiva: app.cfg.comportamiento.notarVentanaActiva,
    seguirCursor: app.cfg.comportamiento.seguirCursor,
  });
  // Vivo: el avatar hereda ritmo de parpadeo y mirada del perfil, y los
  // logros hacen destello calido ademas de la curva de sonrisa.
  if (app.avatar) {
    app.avatar.seguirCursor = app.cfg.comportamiento?.seguirCursor !== false;
    app.avatar.tasaDobleParpadeo = app.conductas.tasaDobleParpadeo ?? 0.12;
    const chispaOrig = app.conductas.chispa.bind(app.conductas);
    app.conductas.chispa = (tipo, dur) => {
      chispaOrig(tipo, dur);
      if (tipo === 'logro') app.avatar?.chispaVisual('logro', dur);
    };
  }

  // ── Eventos del raton ──
  ui.cont.addEventListener('click', alClicIzquierdo);
  ui.cont.addEventListener('contextmenu', alMenuContextual);
  ui.cont.addEventListener('mousedown', alBoton);
  window.addEventListener('mouseup', alSoltar);
  window.addEventListener('mousemove', alMover);
  window.addEventListener('blur', cerrarMenuCtx);
  ui.menuCtx.addEventListener('click', (e) => {
    const it = e.target.closest('.itemMenu');
    if (it) accionCtx(it.dataset.accion);
  });

  // Boton derecho del menu de tareas de Windows -> vision menu.
  window.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') { cerrarMenuCtx(); if (app.estado === 'resting') cambiarEstado('idle'); }
  });

  // ── Eventos de Tauri ──
  alEvento('avatar-state', (e) => {
    // Rust manda (tray, auto-sleep): refleja el estado real.
    if (ESTADOS.includes(e) && e !== app.estado) cambiarEstado(e, { propagar: false });
  });
  alEvento('capture-state', (activo) => ui.captura.classList.toggle('activo', !!activo));
  alEvento('avatar-say', (texto) => decir(texto));
  alEvento('config-changed', async () => {
    app.cfg = (await invocar('get_config')) || app.cfg;
    app.conductas.configurar({
      perfil: app.cfg.avatar.personalidad,
      timeoutAburlo: app.cfg.avatar.timeoutDescanso,
      autoSleepMin: app.cfg.avatar.autoSleepMin,
      hablarAlDespertar: app.cfg.comportamiento?.hablarAlDespertar,
      celebrarLogros: app.cfg.comportamiento?.celebrarLogros,
      microAcciones: app.cfg.comportamiento?.microAcciones,
      notarVentanaActiva: app.cfg.comportamiento?.notarVentanaActiva,
      seguirCursor: app.cfg.comportamiento?.seguirCursor,
    });
    if (app.avatar) {
      app.avatar.seguirCursor = app.cfg.comportamiento?.seguirCursor !== false;
      app.avatar.tasaDobleParpadeo = app.conductas.tasaDobleParpadeo ?? 0.12;
    }
  });

  // Entrada de texto (si se muestra): enviar = hablar.
  ui.entrada?.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && ui.entrada.value.trim()) {
      decir(ui.entrada.value.trim());
      ui.entrada.value = '';
    }
  });

  await cambiarEstado('idle', { propagar: false });
  comprobarBackend();
  setInterval(comprobarBackend, 15000);
  bucle();
}

arrancar().catch((e) => {
  console.error('[daniela] fallo al arrancar:', e);
  ui.carga.textContent = `Error: ${e.message}`;
});