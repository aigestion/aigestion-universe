/**
 * El chat de Daniela, enchufado al backend REAL.
 *
 * `POST /api/ai/chat` (el puente de `shared/ai_bridge.py`) no es un chat de
 * mentira: le pasa el catálogo de herramientas al modelo, detecta si ha pedido
 * una (` ```tool ...``` `), la EJECUTA y le devuelve el resultado para que
 * responda con datos reales. Aquí solo se traduce eso a burbujas.
 *
 * Tres decisiones y su porqué:
 *
 * 1. `fetch` propio, no `AIGApi`: cuando el servidor falla (503 sin
 *    FREELLMAPI_KEY, 502 sin proveedor) el cuerpo trae el MOTIVO en JSON y
 *    `AIGApi` lo tira al construir el mensaje de error. Aquí se muestra tal
 *    cual: Daniela prefiere decir "no tengo clave" a fingir que no entiende.
 * 2. El hilo se guarda en `localStorage` para que el modelo tenga memoria de
 *    la conversación al volver a entrar (él no la guarda: el estado vive en
 *    el cliente).
 * 3. El avatar pasa a `thinking` mientras espera y a `talking` al responder:
 *    es la señal de que está trabajando, no un spinner decorativo.
 */

const RUTA = '/api/ai/chat';
const CLAVE_HILO = 'daniela_chat_hilo';
const MAX_MENSAJES = 24;

/** estado -> avatar: listening mientras escribes, thinking, talking, idle */
export const ESTADOS = { escribiendo: 'listening', esperando: 'thinking',
                         respondiendo: 'talking', enreposo: 'idle' };

function _leerHilo() {
  try {
    const bruto = JSON.parse(localStorage.getItem(CLAVE_HILO) || '[]');
    if (!Array.isArray(bruto)) return [];
    return bruto.filter((m) => m && (m.role === 'user' || m.role === 'assistant')
      && typeof m.content === 'string').slice(-MAX_MENSAJES);
  } catch {
    return [];
  }
}

function _guardarHilo(hilo) {
  try {
    localStorage.setItem(CLAVE_HILO, JSON.stringify(hilo.slice(-MAX_MENSAJES)));
  } catch { /* modo privado / lleno: el hilo sigue en memoria */ }
}

function _esc(t) {
  return String(t ?? '').replace(/[&<>"']/g,
    (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
}

export class DanielaChat {
  /**
   * @param {object} nodos  `{hilo, formulario, entrada, boton}` del DOM
   * @param {object} op     `{onEstado(avatarState), onHablar(texto), onTool(nombre)}`
   */
  constructor(nodos, op = {}) {
    this.hilo = nodos.hilo;
    this.formulario = nodos.formulario;
    this.entrada = nodos.entrada;
    this.boton = nodos.boton || null;
    this.onEstado = op.onEstado || (() => {});
    this.onHablar = op.onHablar || (() => {});
    this.mensajes = _leerHilo();
    this.enCurso = false;

    this._pintar();
    this.formulario?.addEventListener('submit', (ev) => {
      ev.preventDefault();
      this.enviar();
    });
    this.entrada?.addEventListener('input', () => {
      if (!this.enCurso) this.onEstado(ESTADOS.escribiendo);
    });
  }

  /** Pinta el hilo entero (barato: son como mucho 24 burbujas). */
  _pintar() {
    if (!this.hilo) return;
    if (!this.mensajes.length) {
      this.hilo.innerHTML =
        '<p class="chat-vacio">Pregúntame por el globo, las empresas o lo que ' +
        'quieras guardar en mi memoria.</p>';
      return;
    }
    this.hilo.innerHTML = this.mensajes.map((m) => `
      <div class="chat-msg chat-msg--${m.role === 'user' ? 'yo' : 'daniela'}${m.error ? ' chat-msg--error' : ''}">
        ${m.tool ? `<span class="chat-tool" title="${_esc(m.tool)}">🔧 ${_esc(m.tool)}</span>` : ''}
        <div class="chat-burbuja">${_esc(m.content).replace(/\n/g, '<br>')}</div>
      </div>`).join('');
    this.hilo.scrollTop = this.hilo.scrollHeight;
  }

  _pon(mensaje) {
    this.mensajes.push(mensaje);
    this.mensajes = this.mensajes.slice(-MAX_MENSAJES);
    _guardarHilo(this.mensajes);
    this._pintar();
  }

  /**
   * Habla con el backend. Devuelve la respuesta o lanza con el motivo.
   * `tools: false` apaga las herramientas (para el modo "solo charla").
   */
  async enviar(texto, { tools = true } = {}) {
    const contenido = String(texto ?? this.entrada?.value ?? '').trim();
    if (!contenido || this.enCurso) return null;

    if (this.entrada) this.entrada.value = '';
    this._pon({ role: 'user', content: contenido });
    this.enCurso = true;
    if (this.boton) this.boton.disabled = true;
    this.onEstado(ESTADOS.esperando);

    // Solo lo que el modelo entiende: `tool` (qué herramienta se usó) es
    // pintura de la burbuja, no mensaje; y los `error` son frases MÍAS de
    // fallo de red, no cosas que Daniela haya dicho (mandárselas de vuelta
    // le haría creer que las pronunció).
    const hilo = this.mensajes
      .filter((m) => !m.error)
      .map((m) => ({ role: m.role, content: m.content }))
      .filter((m) => m.content);
    const ctrl = new AbortController();
    const reloj = setTimeout(() => ctrl.abort(), 90000);

    try {
      const r = await fetch(RUTA, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        signal: ctrl.signal,
        body: JSON.stringify({ messages: hilo, tools, max_tokens: 600 }),
      });
      const d = await r.json().catch(() => ({}));

      if (!r.ok) {
        // El motivo del servidor se enseña TAL CUAL: "FREELLMAPI_KEY no
        // configurada" es una respuesta honesta; "no entiendo" no lo es.
        throw new Error(d.error || `HTTP ${r.status}`);
      }
      const contenido2 = String(d.content || '').trim();
      if (!contenido2) throw new Error('respuesta vacía del proveedor');

      this._pon({
        role: 'assistant',
        content: contenido2,
        tool: d.tool ? d.tool.name : null,
      });
      this.onEstado(ESTADOS.respondiendo);
      // El avatar habla la respuesta con voz neural (devuelve true si está
      // hablando: entonces él vuelve solo a idle al terminar). Si no habla,
      // el reposo llega por temporizador como antes.
      try {
        Promise.resolve(this.onHablar(contenido2)).then((habla) => {
          if (!habla) setTimeout(() => this.onEstado(ESTADOS.enreposo), 2500);
        }).catch(() => this.onEstado(ESTADOS.enreposo));
      } catch {
        setTimeout(() => this.onEstado(ESTADOS.enreposo), 2500);
      }
      return contenido2;
    } catch (e) {
      const motivo = e.name === 'AbortError'
        ? 'Se me ha hecho largo: el proveedor no contesta.'
        : (e.message || 'sin conexión con el servidor');
      this._pon({ role: 'assistant', content: `No he podido responder: ${motivo}`,
                  error: true });
      this.onEstado(ESTADOS.enreposo);
      return null;
    } finally {
      clearTimeout(reloj);
      this.enCurso = false;
      if (this.boton) this.boton.disabled = false;
    }
  }

  /** Olvida la conversación (y lo que el modelo recordaba de ella). */
  limpiar() {
    this.mensajes = [];
    _guardarHilo(this.mensajes);
    this._pintar();
  }

  /**
   * Al salir de la vista el nodo entero se tira: los escuchas del formulario
   * viajan con él y mueren con él. Solo se corta un temporizador suelto.
   */
  destroy() {
    this.enCurso = false;
    if (this.boton) this.boton.disabled = false;
  }
}

export default DanielaChat;
