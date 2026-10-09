/**
 * menu.js — Vision Menu de Daniela.
 *
 * Cada pestaña habla con el backend Python (el mismo que sirve /gods-eye) a
 * traves de `cfg.menu.backend`. Nada de este fichero inventa datos: cada panel
 * muestra lo que la API devuelve, y cuando no hay backend muestra COMO
 * levantarlo en vez de fingir un grafo vacio.
 *
 * Pestanas:
 *   gev      - Globo / God's Eye View + capas OSINT
 *   memoria  - Vault de memoria como grafo interconectado
 *   agentes  - Los engines trabajando en tiempo real (SSE)
 *   estudio  - Estudio audiovisual (todo lo que Daniela puede crear)
 *   vital    - Vitals del sistema y de la maquina
 *   ajustes  - Config del avatar
 */

const $ = (s, r = document) => r.querySelector(s);
const $$ = (s, r = document) => [...r.querySelectorAll(s)];

// ── Estado ─────────────────────────────────────────────────────────

const app = {
  backend: 'http://127.0.0.1:9200',
  cfg: null,
  pestana: 'gev',
  viva: false,
  sse: null,
  ultimaPulsacion: new Map(),
};

const TABS = [
  { id: 'gev', ico: '🌍', txt: 'God’s Eye' },
  { id: 'memoria', ico: '🧠', txt: 'Memoria' },
  { id: 'agentes', ico: '🤖', txt: 'Agentes' },
  { id: 'estudio', ico: '🎬', txt: 'Estudio' },
  { id: 'vital', ico: '📊', txt: 'Vitals' },
  { id: 'captura', ico: '📸', txt: 'Captura' },
  { id: 'ajustes', ico: '⚙️', txt: 'Ajustes' },
];

/** Descarga de un asset de marca desde la web (fuera de la app). */
const BRAND = 'http://127.0.0.1:9200/gods-eye/brand';

// ── Utilidades ─────────────────────────────────────────────────────

const esc = (s) =>
  String(s ?? '').replace(/[&<>"']/g, (c) =>
    ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c])
  );

/**
 * Formatea para mostrar, o convierte a numero con valor por defecto.
 * `num(1234)` -> "1.234"   |   `num("abc", 7)` -> 7
 */
const num = (v, defecto) => {
  if (defecto === undefined) return typeof v === 'number' ? v.toLocaleString('es-ES') : (v ?? '—');
  const n = Number(v);
  return Number.isFinite(n) ? n : defecto;
};

async function pedir(ruta, opts = {}) {
  const ctl = new AbortController();
  const { timeout, headers, ...init } = opts;
  const t = setTimeout(() => ctl.abort(), timeout ?? 9000);
  try {
    const r = await fetch(app.backend + ruta, {
      signal: ctl.signal,
      headers: { Accept: 'application/json', ...(headers || {}) },
      ...init,
    });
    const txt = await r.text();
    try {
      return JSON.parse(txt);
    } catch {
      throw new Error(`respuesta no-JSON (HTTP ${r.status})`);
    }
  } finally {
    clearTimeout(t);
  }
}

function sinBackend(que) {
  return `<div class="vacio">
    <strong>Sin conexión con el backend de Daniela.</strong><br><br>
    Para ver ${que} hay que levantar Daniela OS:<br>
    <code>python start_daniela_os.ps1</code><br><br>
    Esperando en <code>${esc(app.backend)}</code>…
  </div>`;
}

// ── Barra y navegacion ─────────────────────────────────────────────

function pintarPestanas() {
  $('#pestanas').innerHTML = TABS.map(
    (t) => `<button class="pestana${t.id === app.pestana ? ' activa' : ''}" data-tab="${t.id}">
      <span class="ico">${t.ico}</span>${esc(t.txt)}</button>`
  ).join('');
}

function irA(id) {
  app.pestana = id;
  $$('.pestana').forEach((b) => b.classList.toggle('activa', b.dataset.tab === id));
  $$('.vista').forEach((v) => v.classList.toggle('activa', v.id === `v-${id}`));
  invocarTauri('set_menu_tab', { tab: id }).catch(() => {});
  pintar();
}

async function pintar() {
  const vista = $(`#v-${app.pestana}`);
  if (!vista) return;
  vista.innerHTML = `<div class="vacio">cargando…</div>`;
  try {
    await VISTAS[app.pestana](vista);
  } catch (e) {
    vista.innerHTML = `<div class="vacio">Error: ${esc(e.message)}</div>`;
  }
}

// ── Tauri (opcional) ───────────────────────────────────────────────

function hayTauri() {
  return typeof window !== 'undefined' && !!window.__TAURI_INTERNALS__;
}
async function invocarTauri(cmd, args) {
  if (!hayTauri()) return null;
  // Sin bundler: la API global la inyecta Tauri (`withGlobalTauri: true`).
  return window.__TAURI__.core.invoke(cmd, args);
}
async function alEventoTauri(nombre, cb) {
  if (!hayTauri()) return;
  try {
    await window.__TAURI__.event.listen(nombre, (e) => cb(e.payload));
  } catch { /* sin Tauri */ }
}

// ── 1. God's Eye View ──────────────────────────────────────────────

const VISTAS = {};

VISTAS.gev = async (raiz) => {
  // El visor completo va en iframe: es una app Vite aparte (ver gev_proxy.py).
  // Solo se monta si responde, si no se ofrece el enlace directo.
  let embebible = false;
  try {
    const ctl = new AbortController();
    setTimeout(() => ctl.abort(), 2500);
    const r = await fetch(app.backend + '/gods-eye/', { signal: ctl.signal });
    embebible = r.ok;
  } catch { embebible = false; }

  raiz.innerHTML = `
    <h2 class="seccion">Visor 3D · God's Eye</h2>
    ${embebible
      ? `<iframe class="visor" src="${esc(app.backend)}/gods-eye/" title="God's Eye"></iframe>`
      : sinBackend('el globo y sus capas')}

    <h2 class="seccion" style="margin-top:22px">Capas OSINT</h2>
    <div id="capasOsint" class="capas"><div class="vacio">consultando catálogo…</div></div>

    <h2 class="seccion" style="margin-top:22px">Nodos del globo</h2>
    <div id="nodosGlobo"></div>`;

  if (!embebible) { $('#capasOsint').outerHTML = ''; $('#nodosGlobo').outerHTML = ''; return; }

  await Promise.all([cargarCapas(raiz), cargarNodos(raiz)]);
  conectarSSE();
};

async function cargarCapas(raiz) {
  const caja = $('#capasOsint', raiz);
  let d;
  try {
    d = await pedir('/api/globe/osint');
  } catch (e) {
    caja.innerHTML = `<div class="vacio">Sin catálogo de capas: ${esc(e.message)}</div>`;
    return;
  }
  if (!d?.ok || !d.capas?.length) {
    caja.innerHTML = `<div class="vacio">El backend no devolvió capas.</div>`;
    return;
  }
  const activas = await capasGuardadas();

  caja.innerHTML = d.capas.map((c) => {
    const chip = c.estado === 'ok' ? 'ok' : c.estado === 'sin_gev' ? 'aviso' : 'tenue';
    return `<div class="capa${activas.has(c.capa) ? ' activa' : ''}" data-capa="${esc(c.capa)}">
      <span class="puntoCapa" style="background:${esc(c.color)}"></span>
      <div>
        <div>${esc(c.capa)}</div>
        <div class="motivo">${esc(c.motivo || '')}</div>
      </div>
      <span class="chip ${chip}" style="margin-left:auto">${esc(c.estado)}</span>
    </div>`;
  }).join('');

  $$('.capa', caja).forEach((el) => {
    el.onclick = async () => {
      const capa = el.dataset.capa;
      const d2 = await pedir(`/api/globe/osint/${capa}?limite=400`, { timeout: 25000 });
      const activo = el.classList.toggle('activa');
      if (activo) {
        if (activas.has(capa)) activas.delete(capa); else activas.add(capa);
        guardarCapas(activas);
      }
      const puntos = d2?.puntos?.length ?? 0;
      burbuja(`${capa}: ${puntos} punto${puntos === 1 ? '' : 's'}` +
        (d2?.ok ? '' : ` · ${d2?.error ?? 'sin datos'}`));
    };
  });
}

async function cargarNodos(raiz) {
  const caja = $('#nodosGlobo', raiz);
  try {
    const d = await pedir('/api/globe/data');
    if (!d?.ok) throw new Error(d?.error ?? 'sin datos');
    const nodos = d.nodos ?? [];
    const sede = d.sede;
    caja.innerHTML = `<div class="tarjeta">
      <h3>${esc(sede ? sede.nombre : 'Sin sede')}${sede ? '' : ' (solo cliente)'}</h3>
      <p>${nodos.length} empresa${nodos.length === 1 ? '' : 's'} · rol <code>${esc(d.rol ?? '?')}</code></p>
      ${nodos.length === 0 ? '' : `<table class="tabla" style="margin-top:10px">
        <thead><tr><th>Empresa</th><th>Estado</th><th>Ciudad</th><th class="num">MRR</th></tr></thead>
        <tbody>${nodos.map((n) => `<tr>
          <td>${esc(n.nombre)}</td>
          <td><span class="chip ${n.estado === 'activo' ? 'ok' : n.estado === 'incidencia' ? 'error' : 'tenue'}">${esc(n.estado_etiqueta || n.estado)}</span></td>
          <td>${esc([n.ciudad, n.pais].filter(Boolean).join(', ') || '—')}</td>
          <td class="num">${n.mrr ? num(n.mrr) : '—'}</td>
        </tr>`).join('')}</tbody></table>`}
    </div>`;
  } catch (e) {
    caja.innerHTML = sinBackend(`los nodos (${e.message})`);
  }
}

async function capasGuardadas() {
  try {
    const d = await pedir('/api/globe/capas');
    return new Set(d?.capas_activas ?? []);
  } catch { return new Set(); }
}
async function guardarCapas(set) {
  try {
    await pedir('/api/globe/capas', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ capas_activas: [...set] }),
    });
  } catch { /* sin backend: la preferencia no persiste */ }
}

// ── 2. Memoria (vault como grafo) ──────────────────────────────────

VISTAS.memoria = async (raiz) => {
  raiz.innerHTML = `
    <h2 class="seccion">Vault de memoria</h2>
    <div class="rejilla dos" style="margin-bottom:16px">
      <input class="campo" id="memBusca" placeholder="Buscar recuerdo… (busca y resalta el subgrafo)">
      <button class="btn" id="memGuardar">Guardar recuerdo</button>
    </div>
    <div id="memGrafo"></div>
    <h2 class="seccion" style="margin-top:20px">Recientes</h2>
    <div id="memLista"></div>`;

  $('#memBusca', raiz).addEventListener('input', debounce(async (e) => {
    await cargarMemoria(raiz, e.target.value.trim());
  }, 400));
  $('#memGuardar', raiz).onclick = async () => {
    const txt = prompt('¿Qué quieres que recuerde?');
    if (!txt?.trim()) return;
    try {
      await pedir('/api/globe/memoria', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ content: txt.trim(), source: 'menu' }),
      });
      burbuja('Guardado. Ya lo tengo.');
      await cargarMemoria(raiz);
    } catch (e) {
      burbuja(`No pude guardar: ${e.message}`);
    }
  };

  await cargarMemoria(raiz);
};

async function cargarMemoria(raiz, q = '') {
  const g = $('#memGrafo', raiz);
  const l = $('#memLista', raiz);
  g.innerHTML = '<div class="vacio">cargando…</div>';
  let d;
  try {
    d = await pedir(`/api/globe/memoria?top=50${q ? `&q=${encodeURIComponent(q)}` : ''}`);
  } catch (e) {
    g.innerHTML = sinBackend(`la memoria (${e.message})`);
    l.innerHTML = '';
    return;
  }
  if (!d?.ok) {
    g.innerHTML = `<div class="vacio">${esc(d?.error ?? 'sin permiso o sin datos')}</div>`;
    l.innerHTML = '';
    return;
  }
  const recs = d.recuerdos ?? [];
  const st = d.stats ?? {};

  g.innerHTML = `<div class="grafo" id="svgMem"></div>
    <div class="rejilla auto" style="margin-top:12px">
      <div class="tarjeta"><h3>${num(st.docs ?? 0)}</h3><p>recuerdos</p></div>
      <div class="tarjeta"><h3>${num(st.links ?? st.aristas ?? 0)}</h3><p>enlaces</p></div>
      <div class="tarjeta"><h3>${num(st.tokens ?? 0)}</h3><p>tokens</p></div>
    </div>`;

  dibujarGrafo($('#svgMem', g), recs, (r) => burbuja(`#${r.id} · ${r.content?.slice(0, 180) ?? ''}`));

  l.innerHTML = recs.length === 0
    ? '<div class="vacio">Sin recuerdos todavía.</div>'
    : `<table class="tabla"><tbody>${recs.map((r) => `
      <tr><td class="num">#${r.id}</td>
        <td>${esc(r.content ?? '')}</td>
        <td class="num">${esc(r.source ?? '')}</td>
      </tr>`).join('')}</tbody></table>`;
}

// ── 3. Agentes (grafo neural en vivo) ──────────────────────────────

VISTAS.agentes = async (raiz) => {
  raiz.innerHTML = `
    <h2 class="seccion">Engines trabajando (tiempo real)</h2>
    <div id="agGrafo"></div>
    <h2 class="seccion" style="margin-top:20px">Actividad</h2>
    <div id="agEventos" class="tarjeta"><div class="vacio">conectando al stream…</div></div>`;

  await cargarEstadoAgentes(raiz);
  conectarSSE(raiz);
};

async function cargarEstadoAgentes(raiz) {
  const caja = $('#agGrafo', raiz);
  let d;
  try {
    d = await pedir('/api/status');
  } catch (e) {
    caja.innerHTML = sinBackend(`el estado de los engines (${e.message})`);
    return;
  }

  // El backend devuelve forma variable; se normaliza a nodos con nombre+estado.
  const nodos = normalizarEstado(d);
  if (!nodos.length) {
    caja.innerHTML = `<div class="vacio">El backend respondió pero sin estado de engines.<br><code>${esc(JSON.stringify(d).slice(0, 200))}</code></div>`;
    return;
  }
  caja.innerHTML = `<div class="grafo" id="svgAg"></div>`;
  dibujarGrafo($('#svgAg', caja), nodos, (n) =>
    burbuja(`${n.nombre}: ${n.estado}${n.detalle ? ` · ${n.detalle}` : ''}`)
  );
}

function normalizarEstado(d) {
  if (!d || typeof d !== 'object') return [];
  const out = [];
  const meter = (nombre, estado, detalle) => {
    if (!nombre) return;
    out.push({ id: nombre, nombre, estado: String(estado ?? '—'), detalle: detalle ?? '' });
  };
  for (const [k, v] of Object.entries(d)) {
    if (typeof v !== 'object' || v === null) continue;
    meter(k, v.estado ?? v.status ?? v.state ?? 'ok',
      v.detail ?? v.motivo ?? v.version ?? '');
  }
  if (!out.length) {
    // Formato plano: {servicios: [...]} o lista.
    const lista = d.servicios ?? d.services ?? d.engines ?? (Array.isArray(d) ? d : null);
    if (Array.isArray(lista)) {
      for (const x of lista) {
        meter(x.name ?? x.nombre ?? x.id, x.estado ?? x.status ?? 'ok', x.detail ?? '');
      }
    }
  }
  return out;
}

// ── SSE: eventos en vivo ───────────────────────────────────────────

function conectarSSE(raiz = document) {
  app.sse?.close();
  try {
    const es = new EventSource(app.backend + '/api/globe/stream');
    app.sse = es;

    es.onmessage = (ev) => {
      let d;
      try { d = JSON.parse(ev.data); } catch { return; }
      if (d?.error) return;

      const cajaEventos = $('#agEventos', raiz);
      if (cajaEventos) {
        const prev = $('.vacio', cajaEventos);
        if (prev) cajaEventos.innerHTML = '';
        const linea = document.createElement('div');
        linea.className = 'num';
        linea.style.cssText = 'font-size:11.5px;padding:4px 0;border-bottom:1px solid rgba(148,163,184,.07)';
        linea.textContent = `${new Date((d.ts ?? Date.now() / 1000) * 1000)
          .toLocaleTimeString('es-ES')} · ${d.cliente_id ?? '—'} · ${esc(d.tipo ?? d.evento ?? '')} ${esc(d.mensaje ?? '')}`;
        cajaEventos.prepend(linea);
        while (cajaEventos.children.length > 40) cajaEventos.lastChild.remove();
      }
      // Pulso en el grafo de agentes: el nodo del cliente implicado crece.
      const svg = $('#svgAg', raiz);
      if (svg && d.cliente_id != null) {
        app.ultimaPulsacion.set(String(d.cliente_id), Date.now());
        const idx = [...svg.querySelectorAll('g[data-idx]')].findIndex(
          (g) => g.querySelector('title')?.textContent.startsWith(String(d.cliente_id))
        );
        const c = idx >= 0 ? svg.querySelectorAll('.nodo')[idx] : null;
        if (c) {
          c.setAttribute('r', '11');
          setTimeout(() => c.setAttribute('r', '7'), 450);
        }
      }
    };

    es.onerror = () => {
      // EventSource reintenta solo; no hay que hacer nada (y no se debe
      // cerrar, porque entonces dejaria de reintentar).
    };
  } catch { /* SSE no soportado */ }
}

// ── 4. Estudio audiovisual ─────────────────────────────────────────

const ESTUDIO = [
  { ico: '🎥', txt: 'Video generativo', d: 'Veo 3, Kling, Seedance', tab: 'video' },
  { ico: '🎙️', txt: 'Voz y TTS', d: 'edge-tts, CSM-1B', tab: 'audio' },
  { ico: '🎵', txt: 'Música y SFX', d: 'Udio, SFX, sonido de video', tab: 'audio' },
  { ico: '🖼️', txt: 'Imagen', d: 'Nano Banana, flux', tab: 'imagen' },
  { ico: '🧊', txt: '3D y avatar', d: 'Blender, morph targets', tab: '3d' },
  { ico: '✂️', txt: 'Edición', d: 'Remotion, ffmpeg', tab: 'video' },
  { ico: '📐', txt: 'Style pack', d: 'LUT 3D, ritmo de corte', tab: 'imagen' },
  { ico: '📱', txt: 'Publicar', d: 'SocialClaw, 13 plataformas', tab: 'social' },
];

VISTAS.estudio = async (raiz) => {
  raiz.innerHTML = `
    <h2 class="seccion">Estudio audiovisual · todo lo que Daniela puede crear</h2>
    <div class="rejilla auto">${ESTUDIO.map((e) => `
      <div class="tarjeta" data-estudio="${esc(e.tab)}" style="cursor:pointer">
        <h3>${e.ico} ${esc(e.txt)}</h3>
        <p>${esc(e.d)}</p>
        <p style="margin-top:8px"><span class="chip info">abrir pipeline</span></p>
      </div>`).join('')}
    </div>

    <h2 class="seccion" style="margin-top:24px">Generadores configurados</h2>
    <div id="estGeneradores"></div>

    <h2 class="seccion" style="margin-top:24px">Brief rápido</h2>
    <div class="tarjeta">
      <textarea class="campo" id="estBrief" rows="5"
        placeholder="Describe el vídeo: duración, tono, formato, para qué canal…"></textarea>
      <div style="display:flex;gap:8px;margin-top:10px">
        <button class="btn" id="estEnviar">Pedirlo a Daniela</button>
        <button class="btn peligro" id="estLimpiar">Limpiar</button>
      </div>
      <p style="margin-top:8px">
        El brief se guarda en tu memoria y llega al motor de producción
        (<code>daniela_epic_engine.py</code>) por el mismo canal que el chat.
      </p>
    </div>`;

  $$('[data-estudio]', raiz).forEach((el) => {
    el.onclick = () => {
      const t = el.dataset.estudio;
      burbuja(`Pipeline «${t}»: lo ejecuto desde el chat o lo lanzo ahora.`);
      const ta = $('#estBrief', raiz);
      if (ta) ta.focus();
    };
  });

  $('#estEnviar', raiz).onclick = async () => {
    const brief = $('#estBrief', raiz).value.trim();
    if (!brief) return;
    try {
      await pedir('/api/globe/memoria', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ content: `Brief audiovisual: ${brief}`, source: 'estudio' }),
      });
      burbuja('Brief guardado. Lo recojo cuando me digas.');
    } catch (e) {
      burbuja(`No pude guardarlo: ${e.message}`);
    }
  };
  $('#estLimpiar', raiz).onclick = () => { $('#estBrief', raiz).value = ''; };

  await cargarGeneradores(raiz);
};

async function cargarGeneradores(raiz) {
  const caja = $('#estGeneradores', raiz);
  // No hay endpoint dedicado de "proveedores": se deduce de lo que el
  // backend declara. Si no responde, se dice en vez de inventar la lista.
  try {
    const d = await pedir('/api/status', { timeout: 6000 });
    const fuentes = Object.keys(d || {}).filter((k) =>
      /video|audio|imagen|image|3d|tts|render|fal|blender|remotion/i.test(k)
    );
    caja.innerHTML = fuentes.length
      ? `<div class="capas">${fuentes.map((f) => `<div class="capa"><span class="puntoCapa" style="background:var(--ok)"></span>${esc(f)}</div>`).join('')}</div>`
      : `<div class="vacio">El backend no declara proveedores.<br>Se consultarán al ejecutar el pipeline.</div>`;
  } catch {
    caja.innerHTML = `<div class="vacio">${esc(sinBackend('los generadores'))}</div>`;
  }
}

// ── 5. Vitals ──────────────────────────────────────────────────────

VISTAS.vital = async (raiz) => {
  const info = await invocarTauri('system_info').catch(() => null);
  raiz.innerHTML = `
    <h2 class="seccion">Esta máquina</h2>
    ${info ? `<div class="rejilla auto">
      <div class="tarjeta"><h3>${esc(info.host)}</h3><p>${esc(info.os)}</p></div>
      <div class="tarjeta"><h3>${info.ramPct.toFixed(1)}%</h3><p>RAM en uso</p>
        <div class="carga" style="margin-top:8px"><i style="width:${info.ramPct.toFixed(1)}%"></i></div>
        <p style="margin-top:6px">${info.ramUsedGb.toFixed(1)} / ${info.ramTotalGb.toFixed(1)} GB</p></div>
      <div class="tarjeta"><h3>WebView2</h3><p>Motor del render del avatar</p>
        <p style="margin-top:8px"><span class="chip ok">activo</span></p></div>
    </div>` : `<div class="vacio">Los vitals de la máquina solo existen dentro de la app de escritorio.</div>`}

    <h2 class="seccion" style="margin-top:24px">Servicios vigilados</h2>
    <div id="vitalServicios">${info ? '' : sinBackend('los servicios')}</div>`;

  if (info) await cargarServicios(raiz);
};

async function cargarServicios(raiz) {
  const caja = $('#vitalServicios', raiz);
  try {
    const d = await pedir('/api/status');
    const nodos = normalizarEstado(d);
    caja.innerHTML = nodos.length
      ? `<table class="tabla"><thead><tr><th>Servicio</th><th>Estado</th><th>Detalle</th></tr></thead>
         <tbody>${nodos.map((n) => `<tr><td>${esc(n.nombre)}</td>
           <td><span class="chip ${/ok|vivo|activo|up/i.test(n.estado) ? 'ok' : /error|down|caido/i.test(n.estado) ? 'error' : 'tenue'}">${esc(n.estado)}</span></td>
           <td class="num">${esc(n.detalle)}</td></tr>`).join('')}</tbody></table>`
      : `<div class="vacio">El backend no expone servicios en <code>/api/status</code>.</div>`;
  } catch (e) {
    caja.innerHTML = sinBackend(`los servicios (${e.message})`);
  }
}

// ── 6. Captura ─────────────────────────────────────────────────────

VISTAS.captura = async (raiz) => {
  raiz.innerHTML = `
    <h2 class="seccion">Captura de pantalla</h2>
    <div class="rejilla dos">
      <div class="tarjeta">
        <h3>Objetivo</h3>
        <div class="capas" id="capObjetivos" style="margin-top:10px"></div>
        <div style="display:flex;gap:8px;margin-top:14px">
          <button class="btn" id="capIniciar">Iniciar</button>
          <button class="btn peligro" id="capParar">Parar</button>
        </div>
      </div>
      <div class="tarjeta">
        <h3>Vista previa</h3>
        <p style="margin-bottom:10px">Frame actual, escalado para no arrastrar MB.</p>
        <img id="capImg" alt="captura" style="width:100%;border-radius:8px;border:1px solid var(--borde);display:none">
      </div>
    </div>
    <h2 class="seccion" style="margin-top:22px">Ventanas abiertas</h2>
    <div id="capVentanas"></div>`;

  const st = await invocarTauri('capture_status').catch(() => null);
  const activos = [];

  const pintarObj = async () => {
    const caja = $('#capObjetivos', raiz);
    caja.innerHTML = `<div class="capa activa" data-obj="monitor"><span class="puntoCapa" style="background:var(--acento)"></span>Pantalla completa</div>`;
    const wins = await invocarTauri('list_windows').catch(() => null);
    if (Array.isArray(wins)) {
      caja.insertAdjacentHTML('beforeend', wins.slice(0, 14).map((w) =>
        `<div class="capa" data-obj="window:${esc(w.titulo)}" title="${esc(w.proceso)} · ${w.ancho}x${w.alto}">
           <span class="puntoCapa" style="background:var(--violeta)"></span>${esc(w.titulo.slice(0, 42))}</div>`
      ).join(''));
      $$('[data-obj]', caja).forEach((el) => {
        el.onclick = () => {
          $$('[data-obj]', caja).forEach((x) => x.classList.remove('activa'));
          el.classList.add('activa');
        };
      });
    }
  };
  await pintarObj();

  $('#capIniciar', raiz).onclick = async () => {
    const obj = $('#capObjetivos .activa', raiz)?.dataset.obj ?? 'monitor';
    try {
      const d = await invocarTauri('start_capture', { objetivo: obj });
      activos.push(d);
      burbuja(`Capturando: ${d}`);
      refrescarPreview(raiz);
    } catch (e) {
      burbuja(`No pude capturar: ${e}`);
    }
  };
  $('#capParar', raiz).onclick = async () => {
    await invocarTauri('stop_capture');
    burbuja('Captura detenida.');
    $('#capImg', raiz).style.display = 'none';
  };

  const wins = await invocarTauri('list_windows').catch(() => null);
  $('#capVentanas', raiz).innerHTML = Array.isArray(wins)
    ? `<table class="tabla"><thead><tr><th>Título</th><th>Proceso</th><th class="num">Tamaño</th></tr></thead>
       <tbody>${wins.slice(0, 25).map((w) => `<tr><td>${esc(w.titulo)}</td><td class="num">${esc(w.proceso)}</td>
       <td class="num">${w.ancho}x${w.alto}</td></tr>`).join('')}</tbody></table>`
    : `<div class="vacio">Solo dentro de la app de escritorio.</div>`;

  if (st?.activa) refrescarPreview(raiz);
};

function refrescarPreview(raiz) {
  const img = $('#capImg', raiz);
  if (!img) return;
  const t = setInterval(async () => {
    const d = await invocarTauri('get_capture_frame', { maxAncho: 1280 }).catch(() => null);
    if (!d) return;
    img.src = d;
    img.style.display = 'block';
  }, 1200);
  // El preview es best-effort: si la ventana se cierra, el intervalo muere con ella.
  addEventListener('beforeunload', () => clearInterval(t), { once: true });
}

// ── 7. Ajustes ─────────────────────────────────────────────────────

VISTAS.ajustes = async (raiz) => {
  let cfg = await invocarTauri('get_config').catch(() => null);
  if (!cfg) {
    raiz.innerHTML = `<div class="vacio">Los ajustes viven en la app de escritorio.<br>
      Abre <strong>Ajustes</strong> desde el menú contextual del avatar.</div>`;
    return;
  }

  const perfiles = ['companion', 'focus', 'mentor', 'playful', 'guardian'];
  raiz.innerHTML = `
    <h2 class="seccion">Personalidad</h2>
    <div class="capas">${perfiles.map((p) => `
      <div class="capa${cfg.avatar.personalidad === p ? ' activa' : ''}" data-perfil="${p}">
        <span class="puntoCapa" style="background:var(--acento)"></span>${p}</div>`).join('')}</div>

    <h2 class="seccion" style="margin-top:22px">Comportamiento</h2>
    <div class="tarjeta" style="display:grid;gap:12px">
      ${campo('autoSleepMin', 'Minutos sin actividad para dormir', cfg.avatar.autoSleepMin, 'number')}
      ${campo('timeoutDescanso', 'Segundos encendida antes de aburrirse', cfg.avatar.timeoutDescanso, 'number')}
      ${interruptor('microAcciones', 'Micro-acciones de aburrimiento (bostezos, tarareos)', cfg.comportamiento.microAcciones)}
      ${interruptor('celebrarLogros', 'Celebrar logros (commits, tests, deploys)', cfg.comportamiento.celebrarLogros)}
      ${interruptor('seguirCursor', 'Mirar al cursor', cfg.comportamiento.seguirCursor)}
      ${interruptor('hablarAlDespertar', 'Hablar al despertar', cfg.comportamiento.hablarAlDespertar)}
    </div>

    <h2 class="seccion" style="margin-top:22px">Voz</h2>
    <div class="tarjeta" style="display:grid;gap:12px">
      ${interruptor('voiceHabilitada', 'Voz activada', cfg.voice.habilitada)}
      <label class="campo" style="display:flex;justify-content:space-between;align-items:center">
        <span>Idioma</span>
        <select id="cfgIdioma" style="background:transparent;border:0;color:inherit;font:inherit">
          ${['es-ES', 'en-US', 'pt-BR', 'fr-FR', 'de-DE'].map((i) =>
            `<option ${cfg.voice.idioma === i ? 'selected' : ''}>${i}</option>`).join('')}
        </select>
      </label>
      ${campo('velocidad', 'Velocidad', cfg.voice.velocidad, 'number', 0.5, 2, 0.05)}
      ${campo('tono', 'Tono', cfg.voice.tono, 'number', 0.5, 2, 0.05)}
    </div>

    <div style="margin-top:18px;display:flex;gap:8px">
      <button class="btn" id="cfgGuardar">Guardar cambios</button>
      <button class="btn" id="cfgProbar">Probar voz</button>
    </div>`;

  $$('[data-perfil]', raiz).forEach((el) => {
    el.onclick = () => {
      $$('[data-perfil]', raiz).forEach((x) => x.classList.remove('activa'));
      el.classList.add('activa');
    };
  });

  $('#cfgProbar', raiz).onclick = () => {
    const p = $('[data-perfil].activa', raiz)?.dataset.perfil ?? 'companion';
    const textos = {
      companion: 'Hola, aqui estoy. Dime que necesitas.',
      focus: 'En modo foco. Solo aparezco si me llamas.',
      mentor: 'Ensename algo y lo practicamos juntos.',
      playful: 'Otra vez mis bostezos, eh.',
      guardian: 'Todo tranquilo por aqui. Nada se escapa sin que lo veas.',
    };
    if (hayTauri()) {
      window.__TAURI__.event.emit('avatar-say', textos[p] ?? textos.companion).catch(() => {});
    } else {
      burbuja(textos[p] ?? textos.companion);
    }
  };

  $('#cfgGuardar', raiz).onclick = async () => {
    const nuevo = {
      ...cfg,
      avatar: {
        ...cfg.avatar,
        personalidad: $('[data-perfil].activa', raiz)?.dataset.perfil ?? cfg.avatar.personalidad,
        autoSleepMin: num($('#autoSleepMin', raiz).value, cfg.avatar.autoSleepMin),
        timeoutDescanso: num($('#timeoutDescanso', raiz).value, cfg.avatar.timeoutDescanso),
      },
      voice: {
        ...cfg.voice,
        habilitada: $('#voiceHabilitada', raiz).checked,
        idioma: $('#cfgIdioma', raiz).value,
        velocidad: num($('#velocidad', raiz).value, cfg.voice.velocidad),
        tono: num($('#tono', raiz).value, cfg.voice.tono),
      },
      comportamiento: {
        ...cfg.comportamiento,
        microAcciones: $('#microAcciones', raiz).checked,
        celebrarLogros: $('#celebrarLogros', raiz).checked,
        seguirCursor: $('#seguirCursor', raiz).checked,
        hablarAlDespertar: $('#hablarAlDespertar', raiz).checked,
      },
    };
    try {
      await invocarTauri('set_config', { config: nuevo });
      cfg = nuevo;
      burbuja('Ajustes guardados.');
    } catch (e) {
      burbuja(`No pude guardar: ${e}`);
    }
  };
};

function campo(id, etiqueta, valor, tipo = 'number', min, max, step) {
  return `<label class="campo" style="display:flex;justify-content:space-between;align-items:center;gap:12px">
    <span>${esc(etiqueta)}</span>
    <input id="${id}" type="${tipo}" value="${valor}"
      ${min !== undefined ? `min="${min}"` : ''} ${max !== undefined ? `max="${max}"` : ''}
      ${step !== undefined ? `step="${step}"` : ''}
      style="width:96px;background:transparent;border:0;color:var(--acento);font:inherit;text-align:right">
  </label>`;
}

function interruptor(id, etiqueta, valor) {
  return `<label class="campo" style="display:flex;justify-content:space-between;align-items:center;gap:12px;cursor:pointer">
    <span>${esc(etiqueta)}</span>
    <input id="${id}" type="checkbox" ${valor ? 'checked' : ''} style="width:17px;height:17px;accent-color:var(--acento)">
  </label>`;
}

// ── Grafo SVG (fuerza dirigida, sin dependencias) ───────────────────

/**
 * Dibuja un grafo de fuerza en SVG puro.
 *
 * Sin Cytoscape/D3 a proposito: son ~400 KB por una pestana que aqui son
 * 60 nodos, y el menu tiene que abrir sin red. La simulacion es la de
 * Fruchterman-Reingold-simple: repulsion entre todos los pares + atraccion
 * por arista + centrado. Con este tamano converge en unos cientos de
 * iteraciones, instantaneo.
 *
 * @param {SVGElement} svg
 * @param {{id:string,nombre:string,estado:string,detalle?:string}[]} nodos
 * @param {(n:object)=>void} [alClic]
 */
function dibujarGrafo(svg, nodos, alClic) {
  const W = svg.clientWidth || 800;
  const H = svg.clientHeight || 420;
  svg.setAttribute('viewBox', `0 0 ${W} ${H}`);

  if (!nodos.length) {
    svg.innerHTML = `<text x="${W / 2}" y="${H / 2}" fill="var(--apagado)"
      text-anchor="middle" font-size="13">sin datos</text>`;
    return;
  }

  // Estado determinista inicial: circulo, no aleatorio, para que dos recargas
  // den el mismo dibujo (facilita leer y depurar).
  const n = nodos.length;
  const puntos = nodos.map((d, i) => {
    const a = (i / n) * Math.PI * 2;
    return {
      ...d,
      x: W / 2 + Math.cos(a) * (Math.min(W, H) * 0.32),
      y: H / 2 + Math.sin(a) * (Math.min(W, H) * 0.32),
      vx: 0, vy: 0,
    };
  });

  // Aristas: cuando el backend no las da, se conectan vecinos en el orden
  // recibido (los eventos suele venir agrupados por cliente).
  const aristas = [];
  for (let i = 1; i < n; i++) aristas.push([i - 1, i]);
  if (n > 6) for (let i = 0; i < n; i += 3) aristas.push([i, (i + 2) % n]);

  const k = Math.sqrt((W * H) / n) * 0.62;
  let temp = W / 8;
  const ITER = 260;

  for (let it = 0; it < ITER; it++) {
    // Repulsion entre todos los pares.
    for (let i = 0; i < n; i++) {
      for (let j = i + 1; j < n; j++) {
        let dx = puntos[i].x - puntos[j].x;
        let dy = puntos[i].y - puntos[j].y;
        let d2 = dx * dx + dy * dy;
        if (d2 < 1) { d2 = 1; dx = (i - j) * 0.1 + 0.1; dy = 0.1; }
        const d = Math.sqrt(d2);
        const f = (k * k) / d;
        const ux = dx / d, uy = dy / d;
        puntos[i].vx += ux * f; puntos[i].vy += uy * f;
        puntos[j].vx -= ux * f; puntos[j].vy -= uy * f;
      }
    }
    // Atraccion por arista.
    for (const [a, b] of aristas) {
      const dx = puntos[a].x - puntos[b].x;
      const dy = puntos[a].y - puntos[b].y;
      const d = Math.max(1, Math.hypot(dx, dy));
      const f = (d * d) / k;
      const ux = dx / d, uy = dy / d;
      puntos[a].vx -= ux * f; puntos[a].vy -= uy * f;
      puntos[b].vx += ux * f; puntos[b].vy += uy * f;
    }
    // Centrado + enfriamiento.
    for (const p of puntos) {
      p.vx += (W / 2 - p.x) * 0.012;
      p.vy += (H / 2 - p.y) * 0.012;
      const v = Math.hypot(p.vx, p.vy) || 1;
      p.x += (p.vx / v) * Math.min(v, temp);
      p.y += (p.vy / v) * Math.min(v, temp);
      p.x = Math.max(30, Math.min(W - 30, p.x));
      p.y = Math.max(22, Math.min(H - 22, p.y));
      p.vx *= 0.55; p.vy *= 0.55;
    }
    temp *= 0.97;
  }

  const color = (e) =>
    /error|down|caido|fall/i.test(e) ? 'var(--error)'
      : /warn|aviso|degrad/i.test(e) ? 'var(--aviso)'
        : /ok|vivo|activo|up|online/i.test(e) ? 'var(--ok)'
          : 'var(--acento)';

  svg.innerHTML =
    aristas.map(([a, b]) =>
      `<line class="arista" x1="${puntos[a].x.toFixed(1)}" y1="${puntos[a].y.toFixed(1)}"
             x2="${puntos[b].x.toFixed(1)}" y2="${puntos[b].y.toFixed(1)}"/>`).join('') +
    puntos.map((p) => `
      <g data-idx="${puntos.indexOf(p)}">
        <circle class="nodo" cx="${p.x.toFixed(1)}" cy="${p.y.toFixed(1)}"
          r="7" fill="${color(p.estado)}" fill-opacity=".85" stroke="var(--bg)" stroke-width="1.5">
          <title>${esc(`${p.nombre}: ${p.estado}${p.detalle ? ` · ${p.detalle}` : ''}`)}</title>
        </circle>
        <text class="etiqueta" x="${p.x.toFixed(1)}" y="${(p.y - 13).toFixed(1)}" text-anchor="middle">
          ${esc(String(p.nombre).slice(0, 18))}</text>
      </g>`).join('');

  if (alClic) {
    // Un <g> por nodo: el circulo y su etiqueta se resaltan juntos sin tener
    // que casarlos por coordenadas (que se rompen al redimensionar).
    $$('g[data-idx]', svg).forEach((g) => {
      g.style.cursor = 'pointer';
      g.onclick = () => {
        $$('.etiqueta', svg).forEach((t) => t.classList.remove('activa'));
        $('.etiqueta', g)?.classList.add('activa');
        alClic(puntos[Number(g.dataset.idx)]);
      };
    });
  }
}

// ── Utilidades de UI ───────────────────────────────────────────────

let _burbujaT;
function burbuja(txt, ms = 3600) {
  let el = $('#burbujaMenu');
  if (!el) {
    el = document.createElement('div');
    el.id = 'burbujaMenu';
    el.style.cssText =
      'position:fixed;bottom:44px;left:50%;transform:translateX(-50%);background:rgba(13,20,36,.97);' +
      'border:1px solid rgba(56,189,248,.3);border-radius:10px;padding:9px 16px;font-size:12.5px;' +
      'z-index:999;box-shadow:0 10px 36px rgba(0,0,0,.5);transition:opacity .25s;max-width:70vw';
    document.body.appendChild(el);
  }
  el.textContent = txt;
  el.style.opacity = '1';
  clearTimeout(_burbujaT);
  _burbujaT = setTimeout(() => { el.style.opacity = '0'; }, ms);
}

function debounce(fn, ms) {
  let t;
  return (...a) => {
    clearTimeout(t);
    t = setTimeout(() => fn(...a), ms);
  };
}

void BRAND;

// ── Arranque ───────────────────────────────────────────────────────

async function arrancar() {
  app.cfg = await invocarTauri('get_config').catch(() => null);
  app.backend = app.cfg?.menu?.backend ?? 'http://127.0.0.1:9200';
  const inicial = app.cfg?.menu?.pestanaInicial ?? 'gev';
  app.pestana = TABS.some((t) => t.id === inicial) ? inicial : 'gev';

  // Contenedores de todas las vistas (se crean de una vez).
  $('#cuerpo').innerHTML = TABS.map((t) =>
    `<section class="vista${t.id === app.pestana ? ' activa' : ''}" id="v-${t.id}"></section>`).join('');

  pintarPestanas();

  $('#pestanas').onclick = (e) => {
    const b = e.target.closest('.pestana');
    if (b) irA(b.dataset.tab);
  };
  $('#btnRefrescar').onclick = () => pintar();
  $('#btnCerrar').onclick = () => invocarTauri('hide_menu').catch(() => window.close());

  // Reloj del pie.
  setInterval(() => {
    $('#reloj').textContent = new Date().toLocaleTimeString('es-ES');
  }, 1000);

  await comprobarBackend();
  setInterval(comprobarBackend, 15000);

  await alEventoTauri('menu-tab', (tab) => {
    if (TABS.some((t) => t.id === tab) && tab !== app.pestana) irA(tab);
  });
  await alEventoTauri('capture-state', (a) => {
    $('#estadoCaptura').textContent = a ? 'capturando' : 'captura inactiva';
  });

  irA(app.pestana);
}

async function comprobarBackend() {
  const p = $('#puntoBackend');
  const s = $('#subBackend');
  const e = $('#estadoBackend');
  try {
    const r = await fetch(app.backend + '/api/globe/data', {
      signal: AbortSignal.timeout(3500),
    });
    const ok = r.ok;
    p.className = 'punto ' + (ok ? 'ok' : 'error');
    s.textContent = ok ? 'backend conectado' : `HTTP ${r.status}`;
    e.textContent = app.backend;
  } catch (err) {
    p.className = 'punto error';
    s.textContent = 'backend caído';
    e.textContent = `${app.backend} · ${err.name}`;
  }
}

arrancar().catch((e) => {
  document.getElementById('cuerpo').innerHTML =
    `<div class="vacio">No pude abrir el menú: ${esc(e.message)}</div>`;
});