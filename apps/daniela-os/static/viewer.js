/* God's Eye Dashboard — Daniela OS
   Globo 3D con la Sede (solo admin) y las empresas del negocio. */

const API = {
  data:    '/api/globe/data',
  cliente: (id) => `/api/globe/cliente/${encodeURIComponent(id)}`,
  estado:  (id) => `/api/globe/cliente/${encodeURIComponent(id)}/estado`,
  stream:  '/api/globe/stream',
  alta:    '/api/globe/cliente',
  osint:   '/api/globe/osint',
  capa:    (c) => `/api/globe/osint/${encodeURIComponent(c)}`,
  memoria: '/api/globe/memoria',
  i18n:    (l) => `/api/i18n/${encodeURIComponent(l)}`,
  capas:   '/api/globe/capas',
  busqueda:(q) => `/api/globe/busqueda?q=${encodeURIComponent(q)}`,
  cc: {
    astra:      '/api/cc/astra',
    voice:      '/api/cc/voz',
    inbox:      '/api/cc/inbox',
    telemetria: '/api/cc/telemetria',
    consola:    '/api/cc/consola',
  },
};

// ── Capas personalizadas por usuario ────────────────────────
let CAPAS_PERSONAL = { capas: [], aoi: null, estilo: 'normal', mapa: 'satellite' };

async function cargarCapasPersonalizadas() {
  try {
    const r = await fetch(API.capas);
    const d = await r.json();
    if (d.ok) {
      CAPAS_PERSONAL = d;
      for (const c of d.capas || []) {
        if (c.activa && c.estado === 'ok') {
          CAPAS_ACTIVAS.add(c.capa);
          COLORES_CAPA[c.capa] = c.color;
          await cargarCapa(c.capa);
        }
      }
      if (d.aoi?.lat != null && d.aoi?.lon != null) {
        volarA(d.aoi.lat, d.aoi.lon, d.aoi.radio_km || 150);
      }
      aplicarEstilo(d.estilo, d.mapa);
    }
  } catch { /* silencioso: el visor sigue sin capas personalizadas */ }
}

function aplicarEstilo(estilo, mapa) {
  if (!viewer || !viewer.scene) return;
  const s = viewer.scene;
  if (mapa === 'dark' || mapa === 'terrain') {
    s.globe.baseColor = Cesium.Color.fromCssColorString('#050810');
  } else {
    s.globe.baseColor = Cesium.Color.fromCssColorString('#0b1220');
  }
  if (estilo === 'nvg') s.backgroundColor = Cesium.Color.fromCssColorString('#001a00');
  else if (estilo === 'flir') s.backgroundColor = Cesium.Color.fromCssColorString('#0a0a1a');
  else if (estilo === 'snow') s.backgroundColor = Cesium.Color.fromCssColorString('#e8edf2');
  else s.backgroundColor = Cesium.Color.fromCssColorString('#0b0f19');
}

async function guardarCapasPersonal() {
  try {
    await fetch(API.capas, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        capas_activas: [...CAPAS_ACTIVAS],
        aoi: CAPAS_PERSONAL.aoi || { lat: null, lon: null, radio_km: 150 },
        estilo: CAPAS_PERSONAL.estilo,
        mapa: CAPAS_PERSONAL.mapa,
      }),
    });
  } catch { /* silencioso */ }
}

// ── Búsqueda dirigida por Daniela ────────────────────────────

async function buscarDaniela(q) {
  try {
    const r = await fetch(API.busqueda(q));
    const d = await r.json();
    if (!d.ok) {
      aviso('Búsqueda: ' + (d.error || 'no reconocida'));
      return null;
    }
    CAPAS_ACTIVAS.add(d.capa);
    COLORES_CAPA[d.capa] = d.capa_color;
    await cargarCapa(d.capa);
    if (d.destino?.lat != null && d.destino?.lon != null) {
      volarA(d.destino.lat, d.destino.lon, d.destino.radio_km || 150);
    }
    await guardarCapasPersonal();
    aviso(`Capa "${d.capa}" activa — ${d.contexto || q}`);
    return d;
  } catch (e) {
    aviso('Búsqueda falló: ' + e.message);
    return null;
  }
}

// Exposto para el chat de Daniela (postMessage desde la PWA)
window.buscarDaniela = buscarDaniela;
window.cargarCapasPersonalizadas = cargarCapasPersonalizadas;

let viewer = null;
let estadoGlobal = { sede: null, nodos: [], rol: 'admin' };
const entidades = new Map();   // id -> entidad Cesium

// Idioma: espanol por defecto, ingles opcional (se recuerda en localStorage).
let IDIOMA = localStorage.getItem('daniela_lang') || 'es';
let CADENAS = {};
const T = (clave, alt) => CADENAS[clave] || alt || clave;

// Capas OSINT activas
const CAPAS_ACTIVAS = new Set();
const COLORES_CAPA = {};

// ── Arranque ────────────────────────────────────────────────

function iniciarGlobo() {
  Cesium.Ion.defaultAccessToken = undefined;   // sin token: capas sin clave

  viewer = new Cesium.Viewer('globe', {
    imageryProvider: new Cesium.UrlTemplateImageryProvider({
      url: 'https://server.arcgisonline.com/ArcGIS/rest/services/' +
           'World_Imagery/MapServer/tile/{z}/{y}/{x}',
      credit: 'Esri World Imagery',
    }),
    baseLayerPicker: false, geocoder: false, homeButton: false,
    sceneModePicker: false, navigationHelpButton: false,
    animation: false, timeline: false, fullscreenButton: false,
    selectionIndicator: false, infoBox: false,
    terrainProvider: new Cesium.EllipsoidTerrainProvider(),
  });

  const escena = viewer.scene;
  escena.globe.enableLighting = true;
  escena.skyAtmosphere.show = true;
  escena.backgroundColor = Cesium.Color.fromCssColorString('#0b0f19');
  escena.globe.baseColor = Cesium.Color.fromCssColorString('#0b1220');

  viewer.camera.setView({
    destination: Cesium.Cartesian3.fromDegrees(0, 25, 22000000),
  });

  // Click en el globo
  new Cesium.ScreenSpaceEventHandler(escena.canvas).setInputAction((mov) => {
    const elegido = escena.pick(mov.position);
    if (Cesium.defined(elegido) && elegido.id) {
      const tipo = elegido.id.properties?.tipo?.getValue?.();
      if (tipo === 'sede') abrirSede();
      else if (tipo === 'empresa') abrirEmpresa(elegido.id.properties.id.getValue());
    }
  }, Cesium.ScreenSpaceEventType.LEFT_CLICK);
}

// ── Carga de datos ──────────────────────────────────────────

async function cargarDatos() {
  try {
    const r = await fetch(API.data);
    const d = await r.json();
    if (!d.ok) throw new Error(d.error || 'respuesta invalida');
    estadoGlobal = d;
    pintar();
    pintarHud(d);
    pintarPanel(d);
    await cargarCapasPersonalizadas();
  } catch (e) {
    aviso('No se pudo cargar el globo: ' + e.message);
  }
}

function pintar() {
  for (const e of entidades.values()) viewer.entities.remove(e);
  entidades.clear();

  if (estadoGlobal.sede) pintarSede(estadoGlobal.sede);
  for (const n of estadoGlobal.nodos) pintarEmpresa(n);
}

// ── Marcadores ──────────────────────────────────────────────

function pintarSede(s) {
  const pos = Cesium.Cartesian3.fromDegrees(s.lon, s.lat, 0);

  // Haz vertical visible desde orbita
  const haz = viewer.entities.add({
    id: 'sede-haz',
    polyline: {
      positions: [pos, Cesium.Cartesian3.fromDegrees(s.lon, s.lat, 900000)],
      width: 3,
      material: new Cesium.PolylineGlowMaterialProperty({
        glowPower: 0.35, color: Cesium.Color.fromCssColorString('#00ffff'),
      }),
    },
  });
  entidades.set('sede-haz', haz);

  // Nucleo holografico
  const nucleo = viewer.entities.add({
    id: 'sede-aig',
    name: s.nombre,
    position: pos,
    properties: {
      tipo: 'sede', id: 'sede-aig',
      nombre: s.nombre, descripcion: s.descripcion,
    },
    point: {
      pixelSize: 18,
      color: Cesium.Color.fromCssColorString('#00ffff'),
      outlineColor: Cesium.Color.WHITE, outlineWidth: 2,
      heightReference: Cesium.HeightReference.CLAMP_TO_GROUND,
    },
    ellipse: {
      semiMinorAxis: 42000, semiMajorAxis: 42000,
      material: Cesium.Color.fromCssColorString('#00ffff').withAlpha(0.22),
      outline: true,
      outlineColor: Cesium.Color.fromCssColorString('#00ffff'),
      heightReference: Cesium.HeightReference.CLAMP_TO_GROUND,
    },
    label: {
      text: s.nombre, font: '600 13px Segoe UI',
      fillColor: Cesium.Color.WHITE,
      style: Cesium.LabelStyle.FILL_AND_OUTLINE,
      outlineColor: Cesium.Color.fromCssColorString('#0b1220'),
      outlineWidth: 3,
      pixelOffset: new Cesium.Cartesian2(0, -30),
      heightReference: Cesium.HeightReference.CLAMP_TO_GROUND,
      disableDepthTestDistance: Number.POSITIVE_INFINITY,
    },
  });
  entidades.set('sede-aig', nucleo);

  // Pulso luminico (anillo que crece y se desvanece)
  let radio = 42000;
  viewer.clock.onTick.addEventListener(() => {
    radio += 2600;
    if (radio > 190000) radio = 42000;
    const alfa = 0.42 * (1 - (radio - 42000) / 148000);
    nucleo.ellipse.semiMinorAxis = radio;
    nucleo.ellipse.semiMajorAxis = radio;
    nucleo.ellipse.material = Cesium.Color.fromCssColorString('#00ffff')
      .withAlpha(Math.max(alfa, 0));
  });
}

function pintarEmpresa(n) {
  const color = Cesium.Color.fromCssColorString(n.color || '#6b7280');
  const pos = Cesium.Cartesian3.fromDegrees(n.lon, n.lat, 0);
  const ent = viewer.entities.add({
    id: `emp-${n.id}`,
    name: n.nombre,
    position: pos,
    properties: {
      tipo: 'empresa', id: n.id, nombre: n.nombre,
      estado: n.estado, tier: n.tier,
    },
    point: {
      pixelSize: 12, color,
      outlineColor: Cesium.Color.WHITE, outlineWidth: 1.5,
      heightReference: Cesium.HeightReference.CLAMP_TO_GROUND,
    },
    // Columna vertical: altura segun tier (volumen de negocio)
    polyline: {
      positions: [
        pos,
        Cesium.Cartesian3.fromDegrees(n.lon, n.lat,
          n.tier === 'enterprise' ? 260000 : n.tier === 'pro' ? 160000 : 90000),
      ],
      width: 2,
      material: new Cesium.PolylineGlowMaterialProperty({
        glowPower: 0.22, color,
      }),
    },
    label: {
      text: n.nombre, font: '12px Segoe UI',
      fillColor: color,
      style: Cesium.LabelStyle.FILL_AND_OUTLINE,
      outlineColor: Cesium.Color.fromCssColorString('#0b1220'),
      outlineWidth: 3,
      pixelOffset: new Cesium.Cartesian2(0, -22),
      heightReference: Cesium.HeightReference.CLAMP_TO_GROUND,
      disableDepthTestDistance: Number.POSITIVE_INFINITY,
    },
  });
  entidades.set(`emp-${n.id}`, ent);
}

// ── HUD y panel ─────────────────────────────────────────────

function pintarHud(d) {
  document.getElementById('hud-rol').textContent =
    d.rol === 'admin' ? T('hud.admin', 'Administrador — acceso total')
                      : T('hud.cliente', 'Cliente — acceso restringido');
  const r = d.resumen || {};
  const partes = [];
  if (r.total !== null && r.total !== undefined) {
    partes.push(`<div><b>${r.total}</b>${T('hud.empresas', 'empresas')}</div>`);
    partes.push(`<div><b>${r.ubicados ?? 0}</b>${T('hud.en_globo', 'en el globo')}</div>`);
    partes.push(`<div><b>${r.mrr_total ?? 0} €</b>${T('hud.mrr', 'MRR')}</div>`);
  } else {
    partes.push(`<div><b>${T('hud.restringido', 'restringido')}</b>${T('hud.agregados', 'agregados')}</div>`);
  }
  document.getElementById('hud-metricas').innerHTML = partes.join('');
}

function pintarPanel(d) {
  const cont = document.getElementById('panel-lista');
  const filas = [];
  if (d.sede) {
    filas.push(fila({
      id: 'sede-aig', nombre: d.sede.nombre, color: '#00ffff',
      meta: `${T('panel.sede_marca', 'Sede')} · ${d.sede.descripcion || ''}`,
      esSede: true,
    }));
  }
  for (const n of d.nodos || []) {
    filas.push(fila({
      id: n.id, nombre: n.nombre, color: n.color,
      meta: `${n.tier} · ${n.estado_etiqueta || n.estado}`,
    }));
  }
  cont.innerHTML = filas.join('') ||
    `<p class="nodo-meta">${T('panel.vacio', 'Sin nodos visibles.')}</p>`;
  cont.querySelectorAll('.nodo-fila').forEach((el) => {
    el.addEventListener('click', () => {
      if (el.dataset.sede === '1') abrirSede();
      else abrirEmpresa(el.dataset.id);
    });
  });
}

function fila({ id, nombre, color, meta, esSede }) {
  return `<div class="nodo-fila" data-id="${esc(id)}" data-sede="${esSede ? 1 : 0}">
    <span class="nodo-punto" style="background:${color}"></span>
    <span class="nodo-info">
      <span class="nodo-nombre">${esc(nombre)}</span>
      <span class="nodo-meta">${esc(meta || '')}</span>
    </span></div>`;
}

// ── Modales ─────────────────────────────────────────────────

function abrirSede() {
  const s = estadoGlobal.sede;
  if (!s) { aviso(T('panel.sede_no_disp', 'La Sede no esta disponible para tu rol.'), true); return; }
  document.getElementById('sede-sub').textContent =
    `${s.nombre} · ${s.descripcion || ''}`;
  abrir('modal-sede');
  // Cada apertura empieza limpio: si se abrio la memoria la vez anterior,
  // no se queda una caja de busqueda suelta sobre otra herramienta.
  const memoria = document.getElementById('memoria-caja');
  if (memoria) memoria.classList.add('oculto');
  volarA(s.lat, s.lon, 420000);
}

async function abrirEmpresa(id) {
  try {
    const r = await fetch(API.cliente(id));
    const d = await r.json();
    if (!r.ok || !d.ok) {
      aviso(d.motivo || d.error || T('panel.sin_acceso', 'Sin acceso a esa empresa.'), true);
      return;
    }
    const e = d.empresa;
    document.getElementById('emp-nombre').textContent = e.nombre;
    document.getElementById('emp-sub').textContent =
      [e.sector, e.ciudad, e.pais].filter(Boolean).join(' · ') ||
      e.direccion || T('panel.sin_ubicacion', 'Sin ubicacion registrada');
    document.getElementById('emp-tier').textContent = e.tier;
    document.getElementById('emp-estado').innerHTML =
      `<span style="color:${e.color}">${e.estado_etiqueta || e.estado}</span>`;
    document.getElementById('emp-mrr').textContent = `${e.mrr} €`;
    document.getElementById('emp-eventos').textContent = d.metricas.eventos_24h;

    document.getElementById('emp-modulos').innerHTML = d.modulos.map((m) => `
      <div class="modulo" style="border-left-color:${m.color}">
        <span class="m-nombre">${esc(m.nombre)}</span>
        <span class="barra"><i style="width:${Math.min(m.altura, 100)}%;
          background:${m.color}"></i></span>
        <span class="m-estado">${esc(m.estado)}</span>
      </div>`).join('');

    document.getElementById('emp-log').innerHTML = (d.eventos || []).length
      ? d.eventos.map((ev) => `<div class="log-fila">
          <b>${esc(ev.tipo)}</b> ${esc(ev.mensaje || '')}
          <span style="float:right">${hora(ev.ts)}</span></div>`).join('')
      : `<div class="log-fila">${T('panel.sin_telemetria', 'Sin telemetria reciente.')}</div>`;

    abrir('modal-empresa');
    if (e.lat && e.lon) volarA(e.lat, e.lon, 60000);
  } catch (err) {
    aviso('Error al abrir la empresa: ' + err.message);
  }
}

function volarA(lat, lon, altura) {
  viewer.camera.flyTo({
    destination: Cesium.Cartesian3.fromDegrees(lon, lat, altura),
    orientation: { heading: 0, pitch: Cesium.Math.toRadians(-55), roll: 0 },
    duration: 1.8,
  });
}

function abrir(id) { document.getElementById(id).classList.remove('oculto'); }
function cerrar(id) { document.getElementById(id).classList.add('oculto'); }

// ── Herramientas del Command Center ─────────────────────────
// Cada boton llama a su endpoint real de Daniela (/api/cc/*). No hay texto
// pre-cocinado: si el backend dice que algo no esta conectado, se muestra asi.

const HERRAMIENTAS = {
  astra:      () => API.cc.astra,
  voice:      () => API.cc.voice,
  inbox:      () => API.cc.inbox,
  telemetria: () => API.cc.telemetria,
  consola:    () => API.cc.consola,
  memoria:    (q) => (q ? `${API.memoria}?q=${encodeURIComponent(q)}` : API.memoria),
};

function _lineas(cabecera, pares) {
  const cuerpo = pares
    .filter(([, v]) => v !== undefined && v !== null && v !== '')
    .map(([k, v]) => `  ${k}: ${v}`)
    .join('\n');
  return cabecera + (cuerpo ? '\n' + cuerpo : '');
}

function formatearAstra(d) {
  if (!d.conectado) return `Astra Document Sniper — ${T('cc.no_conectado')}\n  ${d.motivo || ''}`;
  return _lineas('Astra Document Sniper', [
    ['documentos indexados', d.docs],
    ['enlaces', d.enlaces],
    ['fuentes', Object.keys(d.fuentes || {}).join(', ') || '(ninguna)'],
    ['base de datos', d.db],
    ['nota', d.nota],
  ]);
}

function formatearVoz(d) {
  const cab = d.tts_disponible
    ? 'Voice Briefing Agent — TTS disponible'
    : 'Voice Briefing Agent — solo texto (Piper no instalado)';
  return _lineas(cab, [
    ['voces', (d.voces || []).join(', ') || '(ninguna)'],
    ['', ''],
    ['BRIEFING', ''],
    ['', d.briefing],
  ]);
}

function formatearInbox(d) {
  if (!d.conectado) return `Inbox Zero Drafter — ${T('cc.no_conectado')}\n  ${d.motivo || ''}`;
  return _lineas('Inbox Zero Drafter', [
    ['clasificador', d.clasificador],
    ['buzon conectado', d.buzon_conectado ? 'si' : 'no'],
    ['nota', d.nota],
  ]);
}

function formatearTelemetria(d) {
  if (!d.conectado) return `Life Telemetry HUD — ${T('cc.no_conectado')}`;
  const disco = d.disco || {};
  const mem = d.memoria || {};
  const cpu = d.cpu || {};
  const host = d.host || {};
  return _lineas('Life Telemetry HUD', [
    ['disco', disco.porcentaje != null ? `${disco.porcentaje}% (${disco.libre_gb} GB libres)` : disco.motivo || disco.error],
    ['memoria', mem.porcentaje != null ? `${mem.porcentaje}%` : mem.motivo || 'n/d'],
    ['cpu', cpu.porcentaje != null ? `${cpu.porcentaje}% (${cpu.nucleos} nucleos)` : cpu.motivo || 'n/d'],
    ['sistema', `${host.sistema || '?'} ${host.release || ''} · Python ${host.python || '?'}`],
    ['uptime', `${host.uptime_s || 0} s`],
  ]);
}

function formatearConsola(d) {
  const grupos = Object.entries(d.grupos || {}).slice(0, 10)
    .map(([k, v]) => `  ${k} → ${v}`).join('\n');
  const fallidas = (d.fases_fallidas || []).length;
  return _lineas('Command & Control Console', [
    ['rutas registradas', d.rutas_total],
    ['agentes', d.agentes ? `${d.agentes.total}` : 'n/d'],
    ['fases fallidas', fallidas],
  ]) + (grupos ? `\n\nRUTAS POR PREFIJO\n${grupos}` : '');
}

const FORMATEADORES = {
  astra: formatearAstra, voice: formatearVoz, inbox: formatearInbox,
  telemetria: formatearTelemetria, consola: formatearConsola,
  memoria: formatearMemoria,
};

function formatearMemoria(d) {
  const st = d.stats || {};
  const fuentes = Object.entries(st.fuentes || {})
    .map(([k, v]) => `${k}:${v}`).join(', ');
  const filas = (d.recuerdos || []).map((r) => {
    const puntuacion = r.score == null ? '—' : Number(r.score).toFixed(2);
    const texto = String(r.content || '').replace(/\s+/g, ' ').slice(0, 110);
    return `  #${r.id} [${puntuacion} ${(r.via || 'reciente')}] ` +
           `${r.source}: ${texto}`;
  });
  return _lineas('Memoria de Daniela — agents/memory_vault.py', [
    ['documentos', st.docs],
    ['enlaces', st.links],
    ['fuentes', fuentes],
    ['consulta', d.q || '(últimos recuerdos)'],
    ['recuerdos', d.n],
    ['base', st.db ? st.db.split('/').slice(-2).join('/') : ''],
  ]) + (filas.length
    ? `\n\nRECUERDOS\n${filas.join('\n')}`
    : `\n\n${T('cc.memoria.vacia', 'Memoria vacía: guarda el primer recuerdo.')}`);
}

async function ejecutarHerramienta(k, arg) {
  const salida = document.getElementById('consola-salida');
  const url = (HERRAMIENTAS[k] || (() => null))(arg);
  if (!url) { salida.textContent = 'Herramienta no reconocida: ' + k; return; }

  salida.textContent = T('cc.cargando', 'Consultando a Daniela...');
  try {
    const r = await fetch(url);
    const d = await r.json();
    if (!r.ok) {
      // 403 -> la memoria (y cualquier ruta protegida) explica el PORQUE,
      // no un JSON a medias que el formateador no sabe leer.
      salida.textContent = d.error === 'acceso_denegado'
        ? (d.motivo || T('cc.memoria.restringida', 'Acceso denegado'))
        : `${T('aviso.error', 'Error')} ${r.status}\n  ${d.motivo || d.error || ''}`;
      return;
    }
    salida.textContent = (FORMATEADORES[k] || (() => JSON.stringify(d, null, 2)))(d);
  } catch (e) {
    salida.textContent = `${T('aviso.error', 'Error')}: ${e.message}`;
  }
}

function iniciarHerramientas() {
  document.querySelectorAll('.herramienta').forEach((b) => {
    b.addEventListener('click', () => {
      // La memoria tiene caja propia: buscar y guardar en la misma base
      // que usa el chat de Daniela (`agents/memory_vault.py`).
      const esMemoria = b.dataset.accion === 'memoria';
      document.getElementById('memoria-caja').classList.toggle('oculto', !esMemoria);
      ejecutarHerramienta(b.dataset.accion);
    });
  });

  const caja = document.getElementById('memoria-caja');
  const texto = document.getElementById('memoria-texto');
  if (!caja || !texto) return;

  document.getElementById('memoria-buscar').addEventListener('click', () => {
    const q = texto.value.trim();
    ejecutarHerramienta('memoria', q || undefined);
  });
  texto.addEventListener('keydown', (ev) => {
    if (ev.key === 'Enter') document.getElementById('memoria-buscar').click();
  });

  document.getElementById('memoria-guardar').addEventListener('click', async () => {
    const salida = document.getElementById('consola-salida');
    const contenido = texto.value.trim();
    if (!contenido) {
      salida.textContent = T('cc.memoria.vacia',
        'Memoria vacía: guarda el primer recuerdo.');
      return;
    }
    salida.textContent = T('cc.cargando', 'Consultando a Daniela...');
    try {
      const r = await fetch(API.memoria, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ content: contenido, source: 'visor' }),
      });
      const d = await r.json();
      if (!r.ok) {
        salida.textContent = d.error === 'acceso_denegado'
          ? (d.motivo || T('cc.memoria.restringida', 'Acceso denegado'))
          : `${T('aviso.error', 'Error')} ${r.status}\n  ${d.motivo || d.error || ''}`;
        return;
      }
      texto.value = '';
      await ejecutarHerramienta('memoria');   // se ve recien guardado
      aviso(`Recuerdo #${d.id} guardado en la memoria de Daniela.`, false);
    } catch (e) {
      salida.textContent = `${T('aviso.error', 'Error')}: ${e.message}`;
    }
  });
}

// ── Telemetria en tiempo real ───────────────────────────────

function conectarStream() {
  if (!window.EventSource) return;
  try {
    const es = new EventSource(API.stream);
    es.onmessage = (m) => {
      try {
        const ev = JSON.parse(m.data);
        if (ev.error) return;
        // Un evento -> un destello en el nodo afectado
        const ent = entidades.get(`emp-${ev.cliente_id}`);
        if (ent && ent.point) destellar(ent, ev.severidad);
      } catch (_) { /* mensaje no-JSON: ignorar */ }
    };
    es.onerror = () => { /* reconexion automatica del navegador */ };
  } catch (_) { /* SSE no disponible */ }
}

function destellar(ent, severidad) {
  const col = severidad === 'error' ? '#ff6b6b'
            : severidad === 'aviso' ? '#fdcb6e' : '#00d2a0';
  const base = ent.point.pixelSize.getValue();
  ent.point.pixelSize = 26;
  ent.point.color = Cesium.Color.fromCssColorString(col);
  setTimeout(() => {
    ent.point.pixelSize = base;
    ent.point.color = Cesium.Color.fromCssColorString(
      ent.properties?.tier?.getValue() === 'free' ? '#6b7280' : '#00d2a0');
  }, 700);
}

// ── Utilidades ──────────────────────────────────────────────

function esc(t) {
  return String(t ?? '').replace(/[&<>"']/g,
    (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
}
function hora(ts) {
  return new Date((ts || 0) * 1000).toLocaleTimeString('es-ES',
    { hour: '2-digit', minute: '2-digit' });
}
function aviso(msg, esError) {
  const el = document.getElementById('aviso');
  el.textContent = msg;
  el.classList.remove('oculto');
  el.classList.toggle('ok', !esError);
  clearTimeout(el._t);
  el._t = setTimeout(() => el.classList.add('oculto'), 5200);
}

// ── Eventos de UI ───────────────────────────────────────────

/** Vuelve a la vista de todo el globo (botón "Ver todo" y comandos de la app). */
function verTodo() {
  viewer.camera.flyTo({
    destination: Cesium.Cartesian3.fromDegrees(0, 25, 22000000),
    duration: 1.6,
  });
}

function iniciarUI() {
  document.querySelectorAll('[data-cerrar]').forEach((b) =>
    b.addEventListener('click', () => cerrar(b.dataset.cerrar)));
  document.querySelectorAll('.modal').forEach((m) =>
    m.addEventListener('click', (e) => { if (e.target === m) m.classList.add('oculto'); }));
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape')
      document.querySelectorAll('.modal').forEach((m) => m.classList.add('oculto'));
  });

  document.getElementById('btn-sede').addEventListener('click', abrirSede);
  document.getElementById('btn-refrescar').addEventListener('click', cargarDatos);
  document.getElementById('btn-idioma').addEventListener('click', alternarIdioma);
  document.getElementById('btn-globo').addEventListener('click', verTodo);
  window.addEventListener('message', atenderApp);
}

// ── Idioma (espanol por defecto, ingles opcional) ───────────

async function cargarIdioma(lang) {
  try {
    const r = await fetch(API.i18n(lang));
    const d = await r.json();
    if (!d.ok) return;
    IDIOMA = d.idioma;
    CADENAS = d.cadenas || {};
    localStorage.setItem('daniela_lang', IDIOMA);
    document.documentElement.lang = IDIOMA;
    aplicarIdioma();
  } catch (_) { /* si falla, se queda el texto del HTML (espanol) */ }
}

function aplicarIdioma() {
  document.querySelectorAll('[data-i18n]').forEach((el) => {
    const txt = T(el.dataset.i18n);
    if (txt) el.textContent = txt;
  });
  // Los placeholders tambien se traducen: un input con `data-i18n-ph` se
  // quedaba en espanol aunque el visor estuviera en ingles.
  document.querySelectorAll('[data-i18n-ph]').forEach((el) => {
    const txt = T(el.dataset.i18nPh);
    if (txt) el.placeholder = txt;
  });
  const b = document.getElementById('btn-idioma');
  if (b) b.textContent = IDIOMA === 'es' ? 'ES' : 'EN';
  pintarPanel(estadoGlobal);
}

function alternarIdioma() {
  cargarIdioma(IDIOMA === 'es' ? 'en' : 'es');
}

// ── Capas OSINT (GEV como sensorio de Daniela) ─────────────

async function iniciarOsint() {
  const cont = document.getElementById('osint-lista');
  try {
    const r = await fetch(API.osint);
    const d = await r.json();
    if (!d.ok) throw new Error(d.error || 'sin catalogo');
    cont.innerHTML = '';
    for (const c of d.capas) {
      Object.assign(COLORES_CAPA, { [c.capa]: c.color });
      const id = 'osint-' + c.capa;
      const fila = document.createElement('label');
      fila.className = 'osint-fila';
      fila.innerHTML =
        `<input type="checkbox" id="${id}" data-capa="${c.capa}"` +
        `${c.estado !== 'ok' ? ' disabled' : ''} />` +
        `<span class="osint-punto" style="background:${c.color}"></span>` +
        `<span class="osint-nombre">${esc(T('osint.' + c.capa, c.capa))}</span>` +
        `<span class="osint-nota">${esc(c.estado === 'ok' ? '' : c.motivo)}</span>`;
      cont.appendChild(fila);
      fila.querySelector('input').addEventListener('change', (e) =>
        alternarCapa(c.capa, e.target.checked));
    }
    document.getElementById('osint-estado').textContent =
      d.gev_vivo ? '' : T('osint.sin_gev', 'GEV no responde');
  } catch (e) {
    cont.textContent = T('aviso.error', 'Error') + ': ' + e.message;
  }
}

async function alternarCapa(capa, activa) {
  const estado = document.getElementById('osint-estado');
  if (!activa) {
    CAPAS_ACTIVAS.delete(capa);
    quitarCapa(capa);
    estado.textContent = '';
    return;
  }
  estado.textContent = T('osint.cargando', 'Cargando capa...');
  try {
    const r = await fetch(API.capa(capa));
    const d = await r.json();
    if (!d.ok || !d.conectado) {
      estado.textContent = d.motivo || T('osint.vacia');
      document.getElementById('osint-' + capa).checked = false;
      return;
    }
    CAPAS_ACTIVAS.add(capa);
    pintarCapa(capa, d.puntos || []);
    estado.textContent = `${capa}: ${d.total} · ${d.fuente || ''}`;
  } catch (e) {
    estado.textContent = T('aviso.error', 'Error') + ': ' + e.message;
    document.getElementById('osint-' + capa).checked = false;
  }
}

function quitarCapa(capa) {
  for (const [k, e] of [...entidades.entries()]) {
    if (k.startsWith('osint-' + capa + '-')) {
      viewer.entities.remove(e);
      entidades.delete(k);
    }
  }
}

function pintarCapa(capa, puntos) {
  quitarCapa(capa);
  const color = Cesium.Color.fromCssColorString(COLORES_CAPA[capa] || '#93a0bd');
  puntos.forEach((p, i) => {
    const ent = viewer.entities.add({
      id: `osint-${capa}-${i}`,
      name: p.etiqueta,
      position: Cesium.Cartesian3.fromDegrees(p.lon, p.lat, 0),
      point: {
        pixelSize: capa === 'sismos' ? 9 : 6,
        color,
        outlineColor: Cesium.Color.fromCssColorString('#0b0f19'),
        outlineWidth: 1,
        heightReference: Cesium.HeightReference.CLAMP_TO_GROUND,
      },
      label: {
        text: p.etiqueta, font: '11px Segoe UI',
        fillColor: color,
        style: Cesium.LabelStyle.FILL_AND_OUTLINE,
        outlineColor: Cesium.Color.fromCssColorString('#0b0f19'),
        outlineWidth: 2,
        pixelOffset: new Cesium.Cartesian2(0, -14),
        heightReference: Cesium.HeightReference.CLAMP_TO_GROUND,
        disableDepthTestDistance: Number.POSITIVE_INFINITY,
        scaleByDistance: new Cesium.NearFarScalar(1e5, 1.0, 4e6, 0.0),
      },
    });
    entidades.set(`osint-${capa}-${i}`, ent);
  });
}

// ── Alta de empresa (solo admin) ────────────────────────────

function iniciarAlta() {
  document.getElementById('btn-nueva-empresa')
    .addEventListener('click', () => {
      document.getElementById('alta-sub').textContent = '';
      abrir('modal-alta');
    });

  document.getElementById('alta-crear').addEventListener('click', async () => {
    const sub = document.getElementById('alta-sub');
    const nombre = document.getElementById('alta-nombre').value.trim();
    if (!nombre) { sub.textContent = T('cli.falta_nombre', 'Falta el nombre.'); return; }

    sub.textContent = T('cc.cargando', 'Consultando a Daniela...');
    try {
      const r = await fetch(API.alta, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          nombre,
          direccion: document.getElementById('alta-direccion').value.trim(),
          sector: document.getElementById('alta-sector').value.trim(),
          tier: document.getElementById('alta-tier').value,
        }),
      });
      const d = await r.json();
      if (!r.ok || !d.ok) {
        sub.textContent = (d.motivo || d.error || 'error') + '';
        return;
      }
      sub.textContent = T('cli.creada', 'Empresa creada.') +
        ' ' + (d.empresa.ubicado
          ? `(${d.empresa.ciudad || d.empresa.lat})`
          : '(sin coordenadas: revisa la direccion)');
      ['alta-nombre', 'alta-direccion', 'alta-sector'].forEach((id) =>
        document.getElementById(id).value = '');
      await cargarDatos();
    } catch (e) {
      sub.textContent = T('aviso.error', 'Error') + ': ' + e.message;
    }
  });
}

// ── Puente con la app que embebe el visor (postMessage) ─────
//
// God's Eye se muestra DENTRO de Daniela (la PWA del móvil y la de PC). La
// app manda comandos —voz, deep links `daniela://`— y el visor los ejecuta
// aquí; en la otra dirección devuelve el resultado para que la app lo enseñe.
//
// Solo se aceptan mensajes del MISMO origen: una página ajena no da ordenes
// al globo. Si la PWA se sirviera en otro origen los comandos se ignoran
// (mejor callado que abierto a cualquiera).

function _paraApp(payload) {
  try {
    if (window.parent && window.parent !== window) {
      window.parent.postMessage(payload, '*');
    }
  } catch (_) { /* sin padre, o cross-origin bloqueado */ }
}

/** Minúsculas sin acentos: "Sede" == "sede", "Ubicación" == "ubicacion". */
function _norm(t) {
  return String(t || '').toLowerCase()
    .normalize('NFD').replace(/[\u0300-\u036f]/g, '').trim();
}

/**
 * Ejecuta un comando hablado/escrito en la app. Devuelve `true` si lo ha
 * reconocido. No hay interpretación libre: se mira contra lo que el visor
 * SABE hacer (la Sede, el globo completo y las empresas cargadas).
 */
function ejecutarComandoApp(texto) {
  const q = _norm(texto);
  const res = (ok, detalle, extra) =>
    _paraApp({ type: 'gev:resultado', ok, comando: String(texto || ''),
               detalle, ...(extra || {}) });
  if (!q) return res(false, 'comando vacío');

  try {
    if (/\b(sede|cuartel|headquarters|hq)\b/.test(q)) {
      if (!estadoGlobal.sede) return res(false, 'la Sede no está disponible para tu rol');
      abrirSede();
      return res(true, `yendo a la ${estadoGlobal.sede.nombre}`);
    }
    if (/(^|\W)(todo|todos|globo|global|mundo|world|all)(\W|$)/.test(q)) {
      verTodo();
      return res(true, 'mostrando el globo completo');
    }

    const nodos = estadoGlobal.nodos || [];
    const nodo = nodos.find((n) => {
      const campos = [_norm(n.nombre), _norm(n.ciudad), _norm(n.pais),
                      _norm(n.tenant_slug)];
      return q.length >= 3 && campos.some((c) => c && c.includes(q));
    });
    if (nodo) {
      volarA(nodo.lat, nodo.lon, 320000);
      abrirEmpresa(nodo.id);          // detalle + estructura 3D del sitio
      return res(true, `yendo a ${nodo.nombre}`, { id: nodo.id });
    }
    return res(false, `no veo nada llamado «${texto}» entre los ${nodos.length} nodos`);
  } catch (e) {
    return res(false, String(e && e.message || e).slice(0, 160));
  }
}

function atenderApp(ev) {
  if (ev.origin !== window.location.origin) return;
  const d = ev.data;
  if (!d || typeof d !== 'object') return;

  switch (d.type) {
    case 'daniela:ready':
      // La app avisa de que está viva: el visor se presenta.
      _paraApp({ type: 'gev:ready', titulo: TITULO,
                 nodos: (estadoGlobal.nodos || []).length });
      break;
    case 'gev:command':
      ejecutarComandoApp(d.command);
      break;
    case 'gev:navigate':
      ejecutarComandoApp(d.location);
      break;
    case 'gev:buscar':
      buscarDaniela(d.query).then((res) => {
        _paraApp({ type: 'gev:resultado', ok: !!res,
                   comando: d.query, detalle: res?.contexto || 'falló' });
      });
      break;
    case 'gev:capas':
      _paraApp({ type: 'gev:capas', ...CAPAS_PERSONAL });
      break;
    case 'gev:location':
      // La posición del móvil no mueve la cámara sola: si no, el globo
      // perseguiría al usuario en mitad de una consulta. Se ignora hoy.
      break;
    default:
      break;
  }
}

// ── Main ────────────────────────────────────────────────────

window.addEventListener('load', async () => {
  try {
    iniciarGlobo();
    iniciarUI();
    iniciarHerramientas();
    iniciarAlta();
    await cargarIdioma(IDIOMA);   // espanol por defecto
    await cargarDatos();
    await iniciarOsint();
    conectarStream();
    setInterval(cargarDatos, 60000);   // refresco de respaldo
  } catch (e) {
    aviso('Fallo al iniciar el visor: ' + e.message);
  }
});
