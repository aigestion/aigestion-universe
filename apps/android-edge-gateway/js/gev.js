/**
 * Integración de God's Eye View con la app de Daniela (móvil y PC).
 *
 * Permite:
 * - Mostrar God's Eye dentro de la app (iframe `#gev-webview`)
 * - Controles de voz integrados
 * - Sincronización de estado con el visor
 * - Notificaciones push
 *
 * El visor NO es otro sitio: es una PANTALLA de Daniela, servida por el MISMO
 * servidor que la PWA (`/gods-eye/`). Por eso la URL es relativa: con
 * `localhost:4173` solo funcionaba en el portátil de desarrollo y en el móvil
 * apuntaba al propio teléfono (nada).
 */

// ==============================================================================
// CONFIGURACIÓN
// ==============================================================================

const GEV_CONFIG = {
  // Relativa a propósito: misma origen que la PWA, el proxy de Daniela y el
  // despliegue. Se puede sobreescribir con `localStorage.gev_url` para apuntar
  // a otro servidor sin recompilar nada.
  url: localStorage.getItem('gev_url') || '/gods-eye/',
  voiceEnabled: true,
  locationEnabled: true,
  notificationsEnabled: true,
};

/** Origen del visor, resuelto tanto si `url` es relativa como absoluta. */
function origenDelVisor() {
  try {
    return new URL(GEV_CONFIG.url, window.location.href).origin;
  } catch {
    return '';
  }
}

// ==============================================================================
// ESTADO
// ==============================================================================

let webView = null;
let isConnected = false;
let voiceRecognition = null;

// ==============================================================================
// INICIALIZACIÓN
// ==============================================================================

/**
 * Inicializa la integración de God's Eye con la app.
 *
 * El iframe NO tiene por que existir aun: la vista del visor se pinta cuando
 * el usuario la abre. Por eso esto solo coloca los escuchas globales y deja
 * `enlazarWebView()` para cuando el `<iframe>` aparezca.
 */
export function initGEVIntegration() {
  console.log('[GEV] Inicializando integración...');

  // Un solo escucha de mensajes para toda la vida de la pestaña.
  if (!window.__gevMessageEscuchado) {
    window.addEventListener('message', onGEVMessage);
    window.__gevMessageEscuchado = true;
  }

  // Si el iframe ya está en el DOM (carga directa de la vista), se enlaza ya.
  enlazarWebView(document.getElementById('gev-webview'));

  setupVoiceControl();
  setupSensors();
  setupNotifications();

  console.log('[GEV] Integración lista · visor en', GEV_CONFIG.url);
}

/** Enlaza el iframe y (re)conecta el micrófono de la vista. */
function _enlazado() {
  setupVoiceControl();
}

/**
 * Enlaza (o vuelva a enlazar) el iframe del visor.
 *
 * La vista se vuelve a pintar en cada visita y el `<iframe>` es entonces un
 * elemento NUEVO: sin volver a enlazar, el visor se quedaba mudo porque el
 * escucha viejo apuntaba a un nodo ya retirado del DOM.
 *
 * AVISO (historia): este módulo se escribió pensando en un WebView nativo de
 * Android (ajustes JavaScript del WebView, cliente de carga nativo, inyección
 * de código desde Java). Esa API no existe en una PWA: el fichero contenía
 * código Kotlin dentro de un .js y no llegaba a parsearse, lo que tumaba
 * `app.js` entero (importa este módulo). Se tradujo al equivalente DOM real:
 * <iframe> + load/error + postMessage. Al servir el visor en el MISMO origen
 * que la PWA, la comunicación es postMessage estructurado y el origen de
 * entrada ya no puede ser el de un tercero.
 *
 * Devuelve `true` si hay iframe enlazado.
 */
export function enlazarWebView(iframe) {
  if (!iframe || typeof iframe.contentWindow === 'undefined') {
    console.warn('[GEV] iframe #gev-webview no disponible en el DOM');
    return false;
  }

  if (webView !== iframe) {
    webView = iframe;
    isConnected = false;
    iframe.addEventListener('load', () => {
      isConnected = true;
      console.log('[GEV] visor cargado en el iframe');
      announceBridge();
    });
    iframe.addEventListener('error', (ev) => {
      console.error('[GEV] Error al cargar el visor:',
                    ev.message || GEV_CONFIG.url);
      isConnected = false;
    });
    // `src` solo la primera vez: reasignarlo recargaría el globo entero
    // en cada visita a la vista.
    if (!iframe.getAttribute('src')) {
      iframe.setAttribute('src', GEV_CONFIG.url);
    }
  }
  _enlazado();
  return true;
}

/** Mensajes salientes hacia el iframe de GEV. */
function postToGEV(payload) {
  if (!webView || !isConnected || !webView.contentWindow) {
    return false;
  }
  webView.contentWindow.postMessage(payload, '*');
  return true;
}

/** Avisa a GEV de que el lado de Daniela está listo para enlazar. */
function announceBridge() {
  postToGEV({ type: 'daniela:ready', source: 'aig-pwa' });
}

/** Entrada desde GEV. Se valida el origen antes de procesar nada. */
function onGEVMessage(ev) {
  // Mismo origen que la app: cualquier otra página embebida queda fuera.
  if (ev.origin !== origenDelVisor()) return;

  const data = ev.data;
  if (!data || typeof data !== 'object') return;

  switch (data.type) {
    case 'gev:ready':
      isConnected = true;
      break;
    case 'gev:deepLink':
      handleDeepLink(String(data.url || ''));
      break;
    case 'gev:notify':
      showNotification('Daniela OS', String(data.message || ''));
      break;
    default:
      break;
  }
}

// ==============================================================================
// CONTROL DE VOZ
// ==============================================================================

/**
 * Configura los controles de voz.
 */
function setupVoiceControl() {
  const voiceBtn = document.getElementById('voice-btn');

  // Sin boton no hay voz, pero tampoco es un error: el visor se puede usar
  // a mano. Se avisa solo si el config exige voz (ahorro de ruido en consola).
  if (!voiceBtn) return;
  if (voiceBtn.__gevEscuchado) return;   // ya enlazado en esta vista
  voiceBtn.__gevEscuchado = true;

  voiceBtn.addEventListener('click', () => {
    if (!GEV_CONFIG.voiceEnabled) {
      showToast('Voz desactivada');
      return;
    }

    toggleVoiceRecognition();
  });
}

/**
 * Alterna el reconocimiento de voz.
 */
function toggleVoiceRecognition() {
  if (voiceRecognition) {
    stopVoiceRecognition();
  } else {
    startVoiceRecognition();
  }
}

/**
 * Inicia el reconocimiento de voz.
 */
function startVoiceRecognition() {
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  
  if (!SpeechRecognition) {
    showToast('Reconocimiento de voz no disponible');
    return;
  }
  
  voiceRecognition = new SpeechRecognition();
  voiceRecognition.continuous = true;
  voiceRecognition.interimResults = true;
  voiceRecognition.lang = 'es-ES';
  
  voiceRecognition.onresult = (event) => {
    let transcript = '';
    for (let i = event.resultIndex; i < event.results.length; i++) {
      transcript += event.results[i][0].transcript;
    }
    
    if (transcript.trim()) {
      sendCommandToGEV(transcript);
    }
  };
  
  voiceRecognition.onerror = (event) => {
    console.error('[GEV-Android] Error de voz:', event.error);
    showToast('Error de voz: ' + event.error);
  };
  
  voiceRecognition.start();
  showToast('Escuchando...');
  
  // Actualizar UI
  const voiceBtn = document.getElementById('voice-btn');
  if (voiceBtn) {
    voiceBtn.classList.add('active');
    voiceBtn.innerHTML = '🔴';
  }
}

/**
 * Detiene el reconocimiento de voz.
 */
function stopVoiceRecognition() {
  if (voiceRecognition) {
    voiceRecognition.stop();
    voiceRecognition = null;
  }
  
  showToast('Voz detenida');
  
  // Actualizar UI
  const voiceBtn = document.getElementById('voice-btn');
  if (voiceBtn) {
    voiceBtn.classList.remove('active');
    voiceBtn.innerHTML = '🎤';
  }
}

// ==============================================================================
// SENSORES
// ==============================================================================

/**
 * Configura los sensores del dispositivo.
 */
function setupSensors() {
  if (!GEV_CONFIG.locationEnabled) {
    return;
  }
  
  // Ubicación
  navigator.geolocation.watchPosition(
    (position) => {
      const { latitude, longitude, altitude, accuracy } = position.coords;
      updateGEVLocation(latitude, longitude, altitude, accuracy);
    },
    (error) => {
      console.error('[GEV-Android] Error de ubicación:', error);
    },
    {
      enableHighAccuracy: true,
      maximumAge: 10000,
      timeout: 5000
    }
  );
}

/**
 * Actualiza la ubicación en GEV.
 */
function updateGEVLocation(lat, lng, alt, accuracy) {
  postToGEV({ type: 'gev:location', lat, lng, alt, accuracy });
}

// ==============================================================================
// NOTIFICACIONES
// ==============================================================================

/**
 * Configura las notificaciones push.
 */
function setupNotifications() {
  if (!GEV_CONFIG.notificationsEnabled) {
    return;
  }
  
  // Solicitar permiso de notificaciones
  if ('Notification' in window) {
    Notification.requestPermission().then(permission => {
      if (permission === 'granted') {
        console.log('[GEV-Android] Notificaciones permitidas');
      }
    });
  }
}

/**
 * Muestra una notificación local.
 */
export function showNotification(title, message) {
  if (!('Notification' in window)) {
    return;
  }
  
  if (Notification.permission === 'granted') {
    new Notification(title, {
      body: message,
      icon: '/icons/icon-192.png',
      badge: '/icons/icon-192.png'
    });
  }
}

// ==============================================================================
// COMANDOS Y LINKS
// ==============================================================================

/**
 * Envía un comando a GEV.
 */
function sendCommandToGEV(command) {
  // Antes se interpolaba `command` dentro de un string que se evaluaba en el
  // iframe: un comando con una comilla rompía la sintaxis (y era un vector de
  // inyección). Con postMessage viaja como dato, nunca como código.
  if (!postToGEV({ type: 'gev:command', command: String(command) })) {
    showToast('GEV no conectado');
  }
}

/**
 * Maneja links personalizados (daniela://).
 */
function handleDeepLink(url) {
  const parts = url.replace('daniela://', '').split('/');
  const action = parts[0];
  const params = parts.slice(1);
  
  switch (action) {
    case 'command':
      sendCommandToGEV(params.join(' '));
      break;
    case 'navigate':
      navigateTo(params[0]);
      break;
    case 'voice':
      toggleVoiceRecognition();
      break;
    case 'notify':
      showNotification('Daniela OS', params.join(' '));
      break;
    default:
      console.warn('[GEV-Android] Acción no reconocida:', action);
  }
}

/**
 * Navega a una ubicación en GEV.
 */
function navigateTo(location) {
  postToGEV({ type: 'gev:navigate', location: String(location) });
}

// ==============================================================================
// UTILIDADES
// ==============================================================================

/**
 * Muestra un toast en la app.
 */
function showToast(message) {
  let toast = document.getElementById('android-toast');
  
  if (!toast) {
    toast = document.createElement('div');
    toast.id = 'android-toast';
    toast.style.cssText = `
      position: fixed;
      bottom: 80px;
      left: 50%;
      transform: translateX(-50%);
      padding: 12px 24px;
      background: rgba(0, 0, 0, 0.9);
      border-radius: 24px;
      color: #fff;
      font-size: 14px;
      z-index: 1000;
      opacity: 0;
      transition: opacity 0.3s;
    `;
    document.body.appendChild(toast);
  }
  
  toast.textContent = message;
  toast.style.opacity = '1';
  
  setTimeout(() => {
    toast.style.opacity = '0';
  }, 2000);
}

// ==============================================================================
// EXPORTACIONES
// ==============================================================================

export default {
  initGEVIntegration,
  enlazarWebView,
  showNotification,
  sendCommandToGEV,
  toggleVoiceRecognition,
  GEV_CONFIG,
};
