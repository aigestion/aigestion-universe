/**
 * Notificaciones Push para Daniela OS.
 * 
 * Gestiona:
 * - Notificaciones locales
 * - Notificaciones push (FCM)
 * - Alertas de voz de Daniela
 * - Notificaciones de sistema
 */

// ==============================================================================
// CONFIGURACIÓN
// ==============================================================================

const NOTIFICATION_CONFIG = {
  channelId: 'daniela_os_channel',
  channelName: 'Daniela OS',
  channelDescription: 'Notificaciones de Daniela OS',
  priority: 'high',
  sound: true,
  vibrate: true,
};

// ==============================================================================
// ESTADO
// ==============================================================================

let notificationPermission = null;
let pushToken = null;

// ==============================================================================
// INICIALIZACIÓN
// ==============================================================================

/**
 * Inicializa el sistema de notificaciones.
 */
export function initNotifications() {
  console.log('[Notificaciones] Inicializando...');
  
  requestPermission();
  setupPushNotifications();
  
  console.log('[Notificaciones] Inicializadas');
}

/**
 * Solicita permiso de notificaciones.
 */
async function requestPermission() {
  if (!('Notification' in window)) {
    console.warn('[Notificaciones] No soportadas');
    return;
  }
  
  try {
    notificationPermission = await Notification.requestPermission();
    console.log('[Notificaciones] Permiso:', notificationPermission);
  } catch (error) {
    console.error('[Notificaciones] Error solicitando permiso:', error);
  }
}

// ==============================================================================
// NOTIFICACIONES LOCALES
// ==============================================================================

/**
 * Muestra una notificación local.
 */
export function showNotification(title, options = {}) {
  if (!('Notification' in window)) {
    console.warn('[Notificaciones] No soportadas');
    return;
  }
  
  if (notificationPermission !== 'granted') {
    console.warn('[Notificaciones] Permiso no concedido');
    return;
  }
  
  const notification = new Notification(title, {
    icon: options.icon || '/icons/icon-192.png',
    badge: options.badge || '/icons/icon-192.png',
    body: options.body || '',
    tag: options.tag || 'daniela-os',
    requireInteraction: options.requireInteraction || false,
    silent: options.silent || false,
    vibrate: options.vibrate || [200, 100, 200],
    data: options.data || {},
  });
  
  notification.onclick = () => {
    console.log('[Notificaciones] Click en notificación:', title);
    
    if (options.onClick) {
      options.onClick();
    }
    
    // Enfocar la ventana
    window.focus();
    notification.close();
  };
  
  notification.onerror = (error) => {
    console.error('[Notificaciones] Error:', error);
  };
  
  return notification;
}

/**
 * Muestra una notificación de voz de Daniela.
 */
export function showDanielaNotification(message, type = 'info') {
  const types = {
    info: {
      icon: '🔵',
      title: 'Daniela',
      vibrate: [100],
    },
    success: {
      icon: '🟢',
      title: 'Daniela - Éxito',
      vibrate: [100, 50, 100],
    },
    warning: {
      icon: '🟡',
      title: 'Daniela - Alerta',
      vibrate: [200, 100, 200],
    },
    error: {
      icon: '🔴',
      title: 'Daniela - Error',
      vibrate: [300, 100, 300, 100, 300],
    },
    urgent: {
      icon: '🚨',
      title: 'Daniela - URGENTE',
      vibrate: [500, 100, 500, 100, 500],
    },
  };
  
  const config = types[type] || types.info;
  
  showNotification(`${config.icon} ${config.title}`, {
    body: message,
    vibrate: config.vibrate,
    requireInteraction: type === 'urgent' || type === 'error',
    tag: `daniela-${type}`,
    data: { type, message, timestamp: Date.now() },
  });
}

// ==============================================================================
// NOTIFICACIONES PUSH (FCM)
// ==============================================================================

/**
 * Configura las notificaciones push con Firebase Cloud Messaging.
 */
function setupPushNotifications() {
  // Verificar soporte de service workers
  if (!('serviceWorker' in navigator)) {
    console.warn('[Notificaciones] Service Workers no disponibles');
    return;
  }
  
  // Registrar service worker
  navigator.serviceWorker.register('/sw.js')
    .then((registration) => {
      console.log('[Notificaciones] Service Worker registrado');
      
      // Solicitar token de push si está configurado FCM
      if (window.FCM && window.FCM.getToken) {
        window.FCM.getToken().then((token) => {
          pushToken = token;
          console.log('[Notificaciones] Token push obtenido');
        });
      }
    })
    .catch((error) => {
      console.error('[Notificaciones] Error registrando SW:', error);
    });
}

/**
 * Suscribe a un tema de notificaciones.
 */
export function subscribeToTopic(topic) {
  if (window.FCM && window.FCM.subscribeToTopic) {
    window.FCM.subscribeToTopic(topic)
      .then(() => {
        console.log('[Notificaciones] Suscrito a:', topic);
      })
      .catch((error) => {
        console.error('[Notificaciones] Error suscribiendo:', error);
      });
  }
}

/**
 * Cancela suscripción a un tema.
 */
export function unsubscribeFromTopic(topic) {
  if (window.FCM && window.FCM.unsubscribeFromTopic) {
    window.FCM.unsubscribeFromTopic(topic)
      .then(() => {
        console.log('[Notificaciones] Desuscrito de:', topic);
      })
      .catch((error) => {
        console.error('[Notificaciones] Error desuscrito:', error);
      });
  }
}

// ==============================================================================
// NOTIFICACIONES DE SISTEMA
// ==============================================================================

/**
 * Muestra una notificación de batería baja.
 */
export function showBatteryNotification(level) {
  if (level <= 20) {
    showDanielaNotification(
      `Batería baja: ${level}%. Conecta el cargador.`,
      level <= 10 ? 'urgent' : 'warning'
    );
  }
}

/**
 * Muestra una notificación de ubicación.
 */
export function showLocationNotification(location) {
  showDanielaNotification(
    `Ubicación actualizada: ${location.latitude.toFixed(4)}, ${location.longitude.toFixed(4)}`,
    'info'
  );
}

/**
 * Muestra una notificación de conexión.
 */
export function showConnectionNotification(connected) {
  showDanielaNotification(
    connected ? "Conexión con God's Eye View establecida" : "Conexión con God's Eye View perdida",
    connected ? 'success' : 'error'
  );
}

/**
 * Muestra una notificación de voz.
 */
export function showVoiceNotification(message) {
  showDanielaNotification(message, 'info');
}

// ==============================================================================
// UTILIDADES
// ==============================================================================

/**
 * Verifica si las notificaciones están permitidas.
 */
export function areNotificationsEnabled() {
  return notificationPermission === 'granted';
}

/**
 * Obtiene el permiso actual.
 */
export function getNotificationPermission() {
  return notificationPermission;
}

/**
 * Abre la configuración de notificaciones del sistema.
 */
export function openNotificationSettings() {
  if (window.AndroidBridge && window.AndroidBridge.openNotificationSettings) {
    window.AndroidBridge.openNotificationSettings();
  }
}

// ==============================================================================
// EXPORTACIONES
// ==============================================================================

export default {
  initNotifications,
  showNotification,
  showDanielaNotification,
  showBatteryNotification,
  showLocationNotification,
  showConnectionNotification,
  showVoiceNotification,
  subscribeToTopic,
  unsubscribeFromTopic,
  areNotificationsEnabled,
  getNotificationPermission,
  openNotificationSettings,
  NOTIFICATION_CONFIG,
};
