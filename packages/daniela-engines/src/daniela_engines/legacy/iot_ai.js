/**
 * IoT + IA - aigestion.net
 * 
 * Sistema de Internet de las Cosas con inteligencia artificial:
 * - Gestión de dispositivos IoT
 * - Análisis de datos de sensores
 * - Mantenimiento predictivo
 * - Automatización inteligente
 * - Edge computing con IA
 * 
 * 100% gratuito con APIs open source
 */

import aiRouter from './ai_router.js';

// ==============================================================================
// CONFIGURACIÓN
// ==============================================================================

const IOT_CONFIG = {
  name: 'aig IoT',
  version: '1.0.0',
  maxDevices: 1000,
  sensorTypes: ['temperature', 'humidity', 'pressure', 'motion', 'light', 'sound'],
  dataRetention: 30 * 24 * 60 * 60 * 1000, // 30 días
  alertThresholds: {
    temperature: { min: 15, max: 35 },
    humidity: { min: 30, max: 70 },
    pressure: { min: 950, max: 1050 },
    motion: { threshold: 0.5 },
  },
};

// ==============================================================================
// BASE DE DATOS IoT
// ==============================================================================

const devices = new Map();
const sensors = new Map();
const readings = [];
const alerts = new Map();

// ==============================================================================
// GESTIÓN DE DISPOSITIVOS
// ==============================================================================

/**
 * Registra un nuevo dispositivo IoT
 */
async function registerDevice(deviceData) {
  const { name, type, location, sensors: sensorTypes = [] } = deviceData;
  
  console.log(`[IoT] Registrando dispositivo: ${name} (${type})`);
  
  const device = {
    id: `device_${Date.now()}`,
    name,
    type,
    location,
    status: 'online',
    registeredAt: new Date().toISOString(),
    lastSeen: new Date().toISOString(),
    sensors: sensorTypes,
    metadata: {},
  };
  
  devices.set(device.id, device);
  
  // Análisis inicial del dispositivo con IA
  const aiAnalysis = await analyzeDeviceHealth(device);
  device.metadata.aiAnalysis = aiAnalysis;
  
  return {
    success: true,
    device,
    aiAnalysis,
    message: 'Dispositivo registrado exitosamente',
  };
}

/**
 * Obtiene un dispositivo por ID
 */
function getDevice(deviceId) {
  const device = devices.get(deviceId);
  
  if (!device) {
    throw new Error(`Dispositivo no encontrado: ${deviceId}`);
  }
  
  return device;
}

/**
 * Lista todos los dispositivos
 */
function listDevices(options = {}) {
  const { status, type, limit = 50, offset = 0 } = options;
  
  let result = Array.from(devices.values());
  
  if (status) {
    result = result.filter(d => d.status === status);
  }
  
  if (type) {
    result = result.filter(d => d.type === type);
  }
  
  return {
    devices: result.slice(offset, offset + limit),
    total: result.length,
    limit,
    offset,
  };
}

/**
 * Actualiza estado de un dispositivo
 */
function updateDeviceStatus(deviceId, status) {
  const device = getDevice(deviceId);
  
  device.status = status;
  device.lastSeen = new Date().toISOString();
  
  return {
    success: true,
    device,
  };
}

// ==============================================================================
// DATOS DE SENSORES
// ==============================================================================

/**
 * Registra lectura de sensor
 */
async function recordSensorReading(readingData) {
  const { deviceId, sensorType, value, unit = '', metadata = {} } = readingData;
  
  console.log(`[IoT] Lectura de sensor: ${sensorType} = ${value}${unit}`);
  
  const reading = {
    id: `reading_${Date.now()}`,
    deviceId,
    sensorType,
    value,
    unit,
    metadata,
    timestamp: new Date().toISOString(),
  };
  
  readings.push(reading);
  
  // Mantener solo últimos 30 días
  const cutoff = Date.now() - IOT_CONFIG.dataRetention;
  while (readings.length > 0 && new Date(readings[0].timestamp).getTime() < cutoff) {
    readings.shift();
  }
  
  // Verificar alertas
  await checkSensorAlerts(reading);
  
  // Análisis con IA
  const aiInsight = await analyzeReading(reading);
  
  return {
    success: true,
    reading,
    aiInsight,
  };
}

/**
 * Obtiene lecturas de un dispositivo
 */
function getDeviceReadings(deviceId, options = {}) {
  const { sensorType, limit = 100, startTime, endTime } = options;
  
  let result = readings.filter(r => r.deviceId === deviceId);
  
  if (sensorType) {
    result = result.filter(r => r.sensorType === sensorType);
  }
  
  if (startTime) {
    result = result.filter(r => new Date(r.timestamp) >= new Date(startTime));
  }
  
  if (endTime) {
    result = result.filter(r => new Date(r.timestamp) <= new Date(endTime));
  }
  
  return {
    readings: result.slice(-limit),
    total: result.length,
  };
}

/**
 * Obtiene estadísticas de sensores
 */
async function getSensorStatistics(deviceId, sensorType, options = {}) {
  const { period = '24h' } = options;
  
  const deviceReadings = readings.filter(
    r => r.deviceId === deviceId && r.sensorType === sensorType
  );
  
  if (deviceReadings.length === 0) {
    return null;
  }
  
  const values = deviceReadings.map(r => r.value);
  const sorted = [...values].sort((a, b) => a - b);
  const sum = values.reduce((a, b) => a + b, 0);
  
  const stats = {
    count: values.length,
    sum,
    avg: sum / values.length,
    min: sorted[0],
    max: sorted[sorted.length - 1],
    median: sorted[Math.floor(sorted.length / 2)],
    lastValue: values[values.length - 1],
  };
  
  // Análisis predictivo con IA
  const prediction = await predictSensorValue(deviceId, sensorType);
  
  return {
    ...stats,
    prediction,
    period,
  };
}

// ==============================================================================
// ALERTAS Y MONITOREO
// ==============================================================================

/**
 * Verifica alertas de sensores
 */
async function checkSensorAlerts(reading) {
  const thresholds = IOT_CONFIG.alertThresholds[reading.sensorType];
  
  if (!thresholds) {
    return;
  }
  
  let alert = null;
  
  if (thresholds.min !== undefined && reading.value < thresholds.min) {
    alert = {
      type: 'low',
      message: `${reading.sensorType} por debajo del mínimo: ${reading.value}`,
      severity: 'warning',
    };
  }
  
  if (thresholds.max !== undefined && reading.value > thresholds.max) {
    alert = {
      type: 'high',
      message: `${reading.sensorType} por encima del máximo: ${reading.value}`,
      severity: 'critical',
    };
  }
  
  if (alert) {
    alert.id = `alert_${Date.now()}`;
    alert.deviceId = reading.deviceId;
    alert.sensorType = reading.sensorType;
    alert.value = reading.value;
    alert.timestamp = new Date().toISOString();
    alert.status = 'active';
    
    alerts.set(alert.id, alert);
    
    console.log(`[IoT Alert] ${alert.severity.toUpperCase()}: ${alert.message}`);
  }
}

/**
 * Obtiene alertas activas
 */
function getActiveAlerts(options = {}) {
  const { severity, deviceId, limit = 50 } = options;
  
  let result = Array.from(alerts.values()).filter(a => a.status === 'active');
  
  if (severity) {
    result = result.filter(a => a.severity === severity);
  }
  
  if (deviceId) {
    result = result.filter(a => a.deviceId === deviceId);
  }
  
  return {
    alerts: result.slice(0, limit),
    total: result.length,
  };
}

/**
 * Reconoce una alerta
 */
function acknowledgeAlert(alertId) {
  const alert = alerts.get(alertId);
  
  if (!alert) {
    throw new Error(`Alerta no encontrada: ${alertId}`);
  }
  
  alert.status = 'acknowledged';
  alert.acknowledgedAt = new Date().toISOString();
  
  return {
    success: true,
    alert,
  };
}

// ==============================================================================
// MANTENIMIENTO PREDICTIVO
// ==============================================================================

/**
 * Predice fallos de dispositivos con IA
 */
async function predictDeviceFailures(deviceId) {
  const device = getDevice(deviceId);
  const deviceReadings = readings.filter(r => r.deviceId === deviceId);
  
  console.log(`[IoT] Prediciendo fallos para dispositivo: ${device.name}`);
  
  const prompt = `Basado en los siguientes datos del dispositivo ${device.name}:

Estado actual: ${device.status}
Lecturas recientes: ${JSON.stringify(deviceReadings.slice(-10))}
Metadatos: ${JSON.stringify(device.metadata)}

Predice:
1. Probabilidad de fallo en los próximos 7 días
2. Causas potenciales
3. Acciones preventivas recomendadas
4. Componentes que podrían fallar`;
  
  const result = await aiRouter.callAI(prompt, {
    systemPrompt: 'Eres un experto en mantenimiento predictivo IoT. Proporciones predicciones basadas en datos.',
    maxTokens: 400,
    temperature: 0.4,
  });
  
  return {
    success: true,
    deviceId,
    deviceName: device.name,
    prediction: result.response,
    provider: result.provider,
    timestamp: new Date().toISOString(),
  };
}

/**
 * Genera mantenimiento preventivo
 */
async function generatePreventiveMaintenance(deviceId) {
  console.log(`[IoT] Generando mantenimiento preventivo para: ${deviceId}`);
  
  const failurePrediction = await predictDeviceFailures(deviceId);
  
  // Generar plan de mantenimiento
  const prompt = `Basado en la predicción de fallos:

${failurePrediction.prediction}

Genera un plan de mantenimiento preventivo con:
1. Tareas específicas
2. Frecuencia recomendada
3. Piezas de repuesto necesarias
4. Tiempo estimado por tarea
5. Prioridad de cada tarea`;
  
  const result = await aiRouter.callAI(prompt, {
    systemPrompt: 'Eres un planificador de mantenimiento experto. Genera planes accionables.',
    maxTokens: 500,
    temperature: 0.5,
  });
  
  return {
    success: true,
    deviceId,
    failurePrediction,
    maintenancePlan: result.response,
    timestamp: new Date().toISOString(),
  };
}

// ==============================================================================
// AUTOMATIZACIÓN INTELIGENTE
// ==============================================================================

/**
 * Crea regla de automatización con IA
 */
async function createAutomationRule(ruleData) {
  const { name, trigger, condition, action } = ruleData;
  
  console.log(`[IoT] Creando regla de automatización: ${name}`);
  
  // Analizar regla con IA
  const prompt = `Analiza la siguiente regla de automatización IoT:

Nombre: ${name}
Trigger: ${trigger}
Condición: ${condition}
Acción: ${action}

Proporciona:
1. Viabilidad técnica
2. Riesgos potenciales
3. Optimizaciones sugeridas
4. Impacto en rendimiento`;
  
  const result = await aiRouter.callAI(prompt, {
    systemPrompt: 'Eres un experto en automatización IoT. Analiza y optimiza reglas.',
    maxTokens: 300,
    temperature: 0.4,
  });
  
  const automationRule = {
    id: `rule_${Date.now()}`,
    name,
    trigger,
    condition,
    action,
    status: 'active',
    createdAt: new Date().toISOString(),
    aiAnalysis: result.response,
    executions: 0,
    lastExecuted: null,
  };
  
  return {
    success: true,
    automationRule,
    message: 'Regla de automatización creada exitosamente',
  };
}

/**
 * Ejecuta automatización inteligente
 */
async function executeAutomation(ruleId, context) {
  console.log(`[IoT] Ejecutando automatización: ${ruleId}`);
  
  // En producción, ejecutar la acción real
  return {
    success: true,
    ruleId,
    executedAt: new Date().toISOString(),
    result: 'Automatización ejecutada exitosamente',
  };
}

// ==============================================================================
// ANÁLISIS CON IA
// ==============================================================================

/**
 * Analiza dispositivo con IA
 */
async function analyzeDeviceHealth(device) {
  const deviceReadings = readings.filter(r => r.deviceId === device.id);
  
  const prompt = `Analiza la salud del siguiente dispositivo IoT:

Dispositivo: ${device.name}
Tipo: ${device.type}
Ubicación: ${device.location}
Estado: ${device.status}
Lecturas recientes: ${JSON.stringify(deviceReadings.slice(-5))}

Proporciona:
1. Estado general del dispositivo
2. Problemas potenciales
3. Recomendaciones de mantenimiento
4. Vida útil estimada restante`;
  
  const result = await aiRouter.callAI(prompt, {
    systemPrompt: 'Eres un experto en IoT. Analiza la salud de dispositivos.',
    maxTokens: 300,
    temperature: 0.3,
  });
  
  return {
    analysis: result.response,
    provider: result.provider,
  };
}

/**
 * Analiza lectura con IA
 */
async function analyzeReading(reading) {
  const prompt = `Analiza la siguiente lectura de sensor IoT:

Sensor: ${reading.sensorType}
Valor: ${reading.value}
Unidad: ${reading.unit}
Dispositivo: ${reading.deviceId}

Proporciona una breve interpretación y cualquier alerta necesaria.`;
  
  const result = await aiRouter.callAI(prompt, {
    systemPrompt: 'Eres un analista de datos IoT. Proporciona interpretaciones breves.',
    maxTokens: 100,
    temperature: 0.3,
  });
  
  return {
    interpretation: result.response,
    provider: result.provider,
  };
}

/**
 * Predice valor futuro de sensor
 */
async function predictSensorValue(deviceId, sensorType) {
  const deviceReadings = readings.filter(
    r => r.deviceId === deviceId && r.sensorType === sensorType
  );
  
  if (deviceReadings.length < 5) {
    return {
      success: false,
      error: 'Datos insuficientes para predicción',
    };
  }
  
  const prompt = `Predice el próximo valor para el sensor ${sensorType} basado en:

Últimas lecturas: ${JSON.stringify(deviceReadings.slice(-10).map(r => r.value))}

Proporciona solo el valor predicho y la confianza (0-100%).`;
  
  const result = await aiRouter.callAI(prompt, {
    systemPrompt: 'Eres un sistema de predicción de series temporales. Proporciona predicciones precisas.',
    maxTokens: 100,
    temperature: 0.2,
  });
  
  // Extraer valor predicho
  const valueMatch = result.response.match(/(\d+\.?\d*)/);
  const confidenceMatch = result.response.match(/(\d+)%/);
  
  return {
    success: true,
    predictedValue: valueMatch ? parseFloat(valueMatch[1]) : null,
    confidence: confidenceMatch ? parseInt(confidenceMatch[1]) / 100 : 0.7,
    rawResponse: result.response,
  };
}

// ==============================================================================
// MÉTRICAS
// ==============================================================================

/**
 * Obtiene métricas del sistema IoT
 */
function getIoTMetrics() {
  const onlineDevices = Array.from(devices.values()).filter(d => d.status === 'online').length;
  const activeAlerts = Array.from(alerts.values()).filter(a => a.status === 'active').length;
  
  return {
    devices: {
      total: devices.size,
      online: offlineDevices,
      offline: devices.size - onlineDevices,
    },
    sensors: {
      total: readings.length,
      last24h: readings.filter(r => Date.now() - new Date(r.timestamp).getTime() < 86400000).length,
    },
    alerts: {
      total: alerts.size,
      active: activeAlerts,
      critical: Array.from(alerts.values()).filter(a => a.severity === 'critical').length,
    },
    timestamp: new Date().toISOString(),
  };
}

// ==============================================================================
// API ENDPOINTS
// ==============================================================================

/**
 * POST /api/iot/devices
 * Registra un dispositivo
 */
export async function registerDeviceEndpoint(req, res) {
  try {
    const result = await registerDevice(req.body);
    res.json(result);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
}

/**
 * GET /api/iot/devices
 * Lista dispositivos
 */
export function listDevicesEndpoint(req, res) {
  const { status, type, limit, offset } = req.query;
  
  res.json(listDevices({ status, type, limit, offset }));
}

/**
 * POST /api/iot/readings
 * Registra lectura de sensor
 */
export async function recordReadingEndpoint(req, res) {
  try {
    const result = await recordSensorReading(req.body);
    res.json(result);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
}

/**
 * GET /api/iot/devices/:id/readings
 * Obtiene lecturas de un dispositivo
 */
export function getDeviceReadingsEndpoint(req, res) {
  const { sensorType, limit, startTime, endTime } = req.query;
  
  const result = getDeviceReadings(req.params.id, { sensorType, limit, startTime, endTime });
  
  res.json(result);
}

/**
 * GET /api/iot/devices/:id/statistics
 * Obtiene estadísticas de sensores
 */
export async function getSensorStatisticsEndpoint(req, res) {
  try {
    const stats = await getSensorStatistics(req.params.id, req.query.sensorType, req.query);
    res.json(stats);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
}

/**
 * GET /api/iot/alerts
 * Lista alertas activas
 */
export function getActiveAlertsEndpoint(req, res) {
  const { severity, deviceId, limit } = req.query;
  
  res.json(getActiveAlerts({ severity, deviceId, limit }));
}

/**
 * POST /api/iot/alerts/:id/acknowledge
 * Reconoce una alerta
 */
export function acknowledgeAlertEndpoint(req, res) {
  try {
    const result = acknowledgeAlert(req.params.id);
    res.json(result);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
}

/**
 * POST /api/iot/devices/:id/predict
 * Predice fallos de dispositivo
 */
export async function predictDeviceFailuresEndpoint(req, res) {
  try {
    const result = await predictDeviceFailures(req.params.id);
    res.json(result);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
}

/**
 * POST /api/iot/maintenance
 * Genera mantenimiento preventivo
 */
export async function generatePreventiveMaintenanceEndpoint(req, res) {
  try {
    const result = await generatePreventiveMaintenance(req.body.deviceId);
    res.json(result);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
}

/**
 * POST /api/iot/automation
 * Crea regla de automatización
 */
export async function createAutomationRuleEndpoint(req, res) {
  try {
    const result = await createAutomationRule(req.body);
    res.json(result);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
}

/**
 * GET /api/iot/metrics
 * Métricas del sistema IoT
 */
export function getIoTMetricsEndpoint(req, res) {
  res.json(getIoTMetrics());
}

/**
 * GET /api/iot/status
 * Estado del sistema IoT
 */
export function getIoTStatus(req, res) {
  res.json({
    status: 'active',
    config: IOT_CONFIG,
    metrics: getIoTMetrics(),
    timestamp: new Date().toISOString(),
  });
}

// ==============================================================================
// EXPORTACIONES
// ==============================================================================

export {
  registerDevice,
  listDevices,
  recordSensorReading,
  getDeviceReadings,
  getSensorStatistics,
  getActiveAlerts,
  predictDeviceFailures,
  generatePreventiveMaintenance,
  createAutomationRule,
  getIoTMetrics,
  IOT_CONFIG,
};

export default {
  registerDeviceEndpoint,
  listDevicesEndpoint,
  recordReadingEndpoint,
  getDeviceReadingsEndpoint,
  getSensorStatisticsEndpoint,
  getActiveAlertsEndpoint,
  acknowledgeAlertEndpoint,
  predictDeviceFailuresEndpoint,
  generatePreventiveMaintenanceEndpoint,
  createAutomationRuleEndpoint,
  getIoTMetricsEndpoint,
  getIoTStatus,
  registerDevice,
  listDevices,
  recordSensorReading,
  getDeviceReadings,
  getSensorStatistics,
  getActiveAlerts,
  predictDeviceFailures,
  generatePreventiveMaintenance,
  createAutomationRule,
  getIoTMetrics,
};
