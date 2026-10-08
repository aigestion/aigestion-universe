/**
 * Sensores del Pixel para Daniela OS.
 * 
 * Lee y procesa:
 * - GPS (ubicación)
 * - Acelerómetro
 * - Giroscopio
 * - Sensor de luz
 * - Sensor de proximidad
 * - Temperatura
 */

// ==============================================================================
// CONFIGURACIÓN
// ==============================================================================

const SENSOR_CONFIG = {
  updateInterval: 1000, // ms
  locationAccuracy: 'high',
  enableBackground: true,
};

// ==============================================================================
// ESTADO DE SENSORES
// ==============================================================================

const sensorState = {
  location: null,
  accelerometer: null,
  gyroscope: null,
  light: null,
  proximity: null,
  temperature: null,
  lastUpdate: null,
};

// ==============================================================================
// INICIALIZACIÓN
// ==============================================================================

/**
 * Inicializa todos los sensores.
 */
export function initSensors() {
  console.log('[Sensores] Inicializando sensores del Pixel...');
  
  initLocation();
  initAccelerometer();
  initGyroscope();
  initLightSensor();
  initProximitySensor();
  
  console.log('[Sensores] Sensores inicializados');
}

// ==============================================================================
// GPS / UBICACIÓN
// ==============================================================================

/**
 * Inicializa el sensor de ubicación.
 */
function initLocation() {
  if (!('geolocation' in navigator)) {
    console.warn('[Sensores] Geolocalización no disponible');
    return;
  }
  
  navigator.geolocation.watchPosition(
    (position) => {
      sensorState.location = {
        latitude: position.coords.latitude,
        longitude: position.coords.longitude,
        altitude: position.coords.altitude,
        accuracy: position.coords.accuracy,
        heading: position.coords.heading,
        speed: position.coords.speed,
        timestamp: position.timestamp,
      };
      
      sensorState.lastUpdate = Date.now();
      notifySensorUpdate('location', sensorState.location);
    },
    (error) => {
      console.error('[Sensores] Error de ubicación:', error.message);
    },
    {
      enableHighAccuracy: SENSOR_CONFIG.locationAccuracy === 'high',
      maximumAge: 10000,
      timeout: 5000
    }
  );
}

/**
 * Obtiene la ubicación actual.
 */
export function getCurrentLocation() {
  return new Promise((resolve, reject) => {
    navigator.geolocation.getCurrentPosition(
      (position) => {
        resolve({
          latitude: position.coords.latitude,
          longitude: position.coords.longitude,
          altitude: position.coords.altitude,
          accuracy: position.coords.accuracy,
        });
      },
      (error) => {
        reject(error);
      },
      {
        enableHighAccuracy: true,
        timeout: 10000,
        maximumAge: 0
      }
    );
  });
}

// ==============================================================================
// ACELERÓMETRO
// ==============================================================================

/**
 * Inicializa el acelerómetro.
 */
function initAccelerometer() {
  if (!('DeviceMotionEvent' in window)) {
    console.warn('[Sensores] Acelerómetro no disponible');
    return;
  }
  
  window.addEventListener('devicemotion', (event) => {
    const acc = event.accelerationIncludingGravity;
    if (acc) {
      sensorState.accelerometer = {
        x: acc.x,
        y: acc.y,
        z: acc.z,
        timestamp: Date.now(),
      };
      
      notifySensorUpdate('accelerometer', sensorState.accelerometer);
    }
  });
}

// ==============================================================================
// GIROSCOPIO
// ==============================================================================

/**
 * Inicializa el giroscopio.
 */
function initGyroscope() {
  if (!('DeviceOrientationEvent' in window)) {
    console.warn('[Sensores] Giroscopio no disponible');
    return;
  }
  
  window.addEventListener('deviceorientation', (event) => {
    sensorState.gyroscope = {
      alpha: event.alpha, // Z (0-360)
      beta: event.beta,   // X (-180 to 180)
      gamma: event.gamma, // Y (-90 to 90)
      timestamp: Date.now(),
    };
    
    notifySensorUpdate('gyroscope', sensorState.gyroscope);
  });
}

// ==============================================================================
// SENSOR DE LUZ
// ==============================================================================

/**
 * Inicializa el sensor de luz.
 */
function initLightSensor() {
  if (!('AmbientLightSensor' in window)) {
    console.warn('[Sensores] Sensor de luz no disponible');
    return;
  }
  
  try {
    const sensor = new AmbientLightSensor({ frequency: 1 });
    
    sensor.addEventListener('reading', () => {
      sensorState.light = {
        illuminance: sensor.illuminance,
        timestamp: Date.now(),
      };
      
      notifySensorUpdate('light', sensorState.light);
    });
    
    sensor.addEventListener('error', (event) => {
      console.error('[Sensores] Error sensor de luz:', event.error);
    });
    
    sensor.start();
  } catch (error) {
    console.warn('[Sensores] No se pudo iniciar sensor de luz:', error);
  }
}

// ==============================================================================
// SENSOR DE PROXIMIDAD
// ==============================================================================

/**
 * Inicializa el sensor de proximidad.
 */
function initProximitySensor() {
  if (!('ProximitySensor' in window)) {
    console.warn('[Sensores] Sensor de proximidad no disponible');
    return;
  }
  
  try {
    const sensor = new ProximitySensor({ frequency: 1 });
    
    sensor.addEventListener('reading', () => {
      sensorState.proximity = {
        distance: sensor.distance,
        near: sensor.near,
        timestamp: Date.now(),
      };
      
      notifySensorUpdate('proximity', sensorState.proximity);
    });
    
    sensor.addEventListener('error', (event) => {
      console.error('[Sensores] Error sensor de proximidad:', event.error);
    });
    
    sensor.start();
  } catch (error) {
    console.warn('[Sensores] No se pudo iniciar sensor de proximidad:', error);
  }
}

// ==============================================================================
// NOTIFICACIONES DE SENSORES
// ==============================================================================

/**
 * Notifica una actualización de sensor.
 */
function notifySensorUpdate(type, data) {
  // Disparar evento personalizado
  const event = new CustomEvent('daniela:sensorUpdate', {
    detail: { type, data },
  });
  
  document.dispatchEvent(event);
  
  // Enviar a GEV si está conectado
  if (window.AndroidBridge) {
    window.AndroidBridge.sendSensorData(type, data);
  }
}

// ==============================================================================
// API PÚBLICA
// ==============================================================================

/**
 * Obtiene el estado de todos los sensores.
 */
export function getSensorState() {
  return { ...sensorState };
}

/**
 * Obtiene un sensor específico.
 */
export function getSensor(type) {
  return sensorState[type];
}

/**
 * Verifica si un sensor está disponible.
 */
export function isSensorAvailable(type) {
  const availability = {
    location: 'geolocation' in navigator,
    accelerometer: 'DeviceMotionEvent' in window,
    gyroscope: 'DeviceOrientationEvent' in window,
    light: 'AmbientLightSensor' in window,
    proximity: 'ProximitySensor' in window,
  };
  
  return availability[type] || false;
}

/**
 * Obtiene la lista de sensores disponibles.
 */
export function getAvailableSensors() {
  return Object.keys({
    location: 'geolocation' in navigator,
    accelerometer: 'DeviceMotionEvent' in window,
    gyroscope: 'DeviceOrientationEvent' in window,
    light: 'AmbientLightSensor' in window,
    proximity: 'ProximitySensor' in window,
  }).filter(type => isSensorAvailable(type));
}

// ==============================================================================
// EXPORTACIONES
// ==============================================================================

export default {
  initSensors,
  getCurrentLocation,
  getSensorState,
  getSensor,
  isSensorAvailable,
  getAvailableSensors,
  SENSOR_CONFIG,
};
