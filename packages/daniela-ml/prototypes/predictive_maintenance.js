/**
 * Predictive Maintenance - aigestion.net
 * 
 * Sistema de mantenimiento predictivo con IA:
 * - Predicción de fallos de equipos
 * - Análisis de vibraciones y temperatura
 * - Alertas tempranas
 * - Programación óptima de mantenimiento
 * - Análisis de vida útil
 * 
 * 100% gratuito con APIs open source
 */

import aiRouter from './ai_router.js';

// ==============================================================================
// CONFIGURACIÓN
// ==============================================================================

const MAINTENANCE_CONFIG = {
  name: 'aig Predictive Maintenance',
  version: '1.0.0',
  equipmentTypes: ['hvac', 'motor', 'pump', 'compressor', 'generator', 'conveyor'],
  sensorTypes: ['vibration', 'temperature', 'pressure', 'current', 'voltage', 'oil'],
  alertLevels: ['info', 'warning', 'critical', 'emergency'],
  predictionHorizon: 7, // días
  maintenanceInterval: 30, // días
};

// ==============================================================================
// BASE DE DATOS
// ==============================================================================

const equipment = new Map();
const maintenanceHistory = new Map();
const predictions = new Map();
const alerts = new Map();

// ==============================================================================
// GESTIÓN DE EQUIPOS
// ==============================================================================

/**
 * Registra un equipo para monitoreo
 */
async function registerEquipment(equipmentData) {
  const { name, type, location, manufacturer, model, installDate } = equipmentData;
  
  console.log(`[Maintenance] Registrando equipo: ${name} (${type})`);
  
  const equip = {
    id: `equip_${Date.now()}`,
    name,
    type,
    location,
    manufacturer,
    model,
    installDate,
    status: 'operational',
    healthScore: 100,
    lastMaintenance: null,
    nextMaintenance: null,
    sensors: [],
    createdAt: new Date().toISOString(),
  };
  
  // Análisis inicial del equipo con IA
  const aiAssessment = await assessEquipmentHealth(equip);
  equip.aiAssessment = aiAssessment;
  
  equipment.set(equip.id, equip);
  
  return {
    success: true,
    equipment: equip,
    aiAssessment,
    message: 'Equipo registrado exitosamente',
  };
}

/**
 * Obtiene un equipo por ID
 */
function getEquipment(equipmentId) {
  const equip = equipment.get(equipmentId);
  
  if (!equip) {
    throw new Error(`Equipo no encontrado: ${equipmentId}`);
  }
  
  return equip;
}

/**
 * Lista todos los equipos
 */
function listEquipment(options = {}) {
  const { type, status, limit = 50, offset = 0 } = options;
  
  let result = Array.from(equipment.values());
  
  if (type) {
    result = result.filter(e => e.type === type);
  }
  
  if (status) {
    result = result.filter(e => e.status === status);
  }
  
  return {
    equipment: result.slice(offset, offset + limit),
    total: result.length,
    limit,
    offset,
  };
}

/**
 * Actualiza estado de un equipo
 */
function updateEquipmentStatus(equipmentId, status, metadata = {}) {
  const equip = getEquipment(equipmentId);
  
  equip.status = status;
  equip.lastUpdated = new Date().toISOString();
  equip.metadata = { ...equip.metadata, ...metadata };
  
  return {
    success: true,
    equipment: equip,
  };
}

// ==============================================================================
// ANÁLISIS DE SALUD
// ==============================================================================

/**
 * Evalúa la salud del equipo con IA
 */
async function assessEquipmentHealth(equip) {
  const prompt = `Evalúa la salud del siguiente equipo industrial:

Nombre: ${equip.name}
Tipo: ${equip.type}
Ubicación: ${equip.location}
Fabricante: ${equip.manufacturer}
Modelo: ${equip.model}
Fecha instalación: ${equip.installDate}
Estado actual: ${equip.status}

Proporciona:
1. Puntuación de salud (0-100)
2. Riesgos identificados
3. Recomendaciones de mantenimiento
4. Vida útil estimada restante
5. Próximas acciones requeridas`;
  
  const result = await aiRouter.callAI(prompt, {
    systemPrompt: 'Eres un ingeniero de mantenimiento predictivo experto.',
    maxTokens: 400,
    temperature: 0.4,
  });
  
  return {
    assessment: result.response,
    healthScore: extractHealthScore(result.response),
    risks: extractRisks(result.response),
    recommendations: extractRecommendations(result.response),
    provider: result.provider,
  };
}

/**
 * Extrae puntuación de salud
 */
function extractHealthScore(text) {
  const match = text.match(/(\d+)\s*\/\s*100|puntuación.*?(\d+)/i);
  return match ? parseInt(match[1] || match[2]) : 75;
}

/**
 * Extrae riesgos identificados
 */
function extractRisks(text) {
  const risks = [];
  const lines = text.split('\n');
  
  lines.forEach(line => {
    if (line.toLowerCase().includes('riesgo') || line.toLowerCase().includes('risk')) {
      risks.push(line.trim());
    }
  });
  
  return risks;
}

/**
 * Extrae recomendaciones
 */
function extractRecommendations(text) {
  const recommendations = [];
  const lines = text.split('\n');
  
  lines.forEach(line => {
    if (line.toLowerCase().includes('recomend') || line.toLowerCase().includes('suger')) {
      recommendations.push(line.trim());
    }
  });
  
  return recommendations;
}

// ==============================================================================
// PREDICCIÓN DE FALLOS
// ==============================================================================

/**
 * Predice fallos futuros del equipo
 */
async function predictFailures(equipmentId, options = {}) {
  const { horizon = 7, includeRecommendations = true } = options;
  
  console.log(`[Maintenance] Prediciendo fallos para ${equipmentId} (${horizon} días)`);
  
  const equip = getEquipment(equipmentId);
  const history = maintenanceHistory.get(equipmentId) || [];
  
  const prompt = `Basado en los siguientes datos del equipo, predice posibles fallos:

Equipo: ${equip.name}
Tipo: ${equip.type}
Estado actual: ${equip.status}
Puntuación salud: ${equip.healthScore}
Historial mantenimiento: ${JSON.stringify(history.slice(-5))}

Predice:
1. Probabilidad de fallo en ${horizon} días
2. Componentes en riesgo
3. Causas probables
4. ${includeRecommendations ? 'Acciones preventivas recomendadas' : ''}
5. Costo estimado de reparación vs mantenimiento preventivo`;
  
  const result = await aiRouter.callAI(prompt, {
    systemPrompt: 'Eres un experto en mantenimiento predictivo industrial.',
    maxTokens: 500,
    temperature: 0.4,
  });
  
  const prediction = {
    id: `pred_${Date.now()}`,
    equipmentId,
    horizon,
    prediction: result.response,
    failureProbability: extractFailureProbability(result.response),
    riskComponents: extractRiskComponents(result.response),
    recommendations: includeRecommendations ? extractRecommendations(result.response) : [],
    provider: result.provider,
    timestamp: new Date().toISOString(),
  };
  
  predictions.set(prediction.id, prediction);
  
  return {
    success: true,
    prediction,
  };
}

/**
 * Extrae probabilidad de fallo
 */
function extractFailureProbability(text) {
  const match = text.match(/(\d+)%|probabilidad.*?(\d+)/i);
  return match ? parseInt(match[1] || match[2]) / 100 : 0.3;
}

/**
 * Extrae componentes en riesgo
 */
function extractRiskComponents(text) {
  const components = [];
  const lines = text.split('\n');
  
  lines.forEach(line => {
    if (line.toLowerCase().includes('componente') || line.toLowerCase().includes('part')) {
      components.push(line.trim());
    }
  });
  
  return components;
}

/**
 * Obtiene todas las predicciones
 */
function getPredictions(options = {}) {
  const { equipmentId, limit = 50, offset = 0 } = options;
  
  let result = Array.from(predictions.values());
  
  if (equipmentId) {
    result = result.filter(p => p.equipmentId === equipmentId);
  }
  
  return {
    predictions: result.slice(offset, offset + limit),
    total: result.length,
    limit,
    offset,
  };
}

// ==============================================================================
// MANTENIMIENTO
// ==============================================================================

/**
 * Programa mantenimiento
 */
async function scheduleMaintenance(equipmentId, options = {}) {
  const { type = 'preventive', priority = 'medium', notes = '' } = options;
  
  console.log(`[Maintenance] Programando ${type} para ${equipmentId}`);
  
  const equip = getEquipment(equipmentId);
  
  const prompt = `Programa un mantenimiento ${type} para el siguiente equipo:

Equipo: ${equip.name}
Tipo: ${equip.type}
Ubicación: ${equip.location}
Estado: ${equip.status}
Salud: ${equip.healthScore}
Notas: ${notes}

Proporciona:
1. Tareas específicas a realizar
2. Repuestos necesarios
3. Tiempo estimado
4. Personal requerido
5. Instrucciones de seguridad`;
  
  const result = await aiRouter.callAI(prompt, {
    systemPrompt: 'Eres un planificador de mantenimiento industrial.',
    maxTokens: 500,
    temperature: 0.5,
  });
  
  const maintenance = {
    id: `maint_${Date.now()}`,
    equipmentId,
    type,
    priority,
    notes,
    plan: result.response,
    status: 'scheduled',
    scheduledAt: new Date().toISOString(),
    provider: result.provider,
  };
  
  // Guardar en historial
  if (!maintenanceHistory.has(equipmentId)) {
    maintenanceHistory.set(equipmentId, []);
  }
  maintenanceHistory.get(equipmentId).push(maintenance);
  
  // Actualizar equipo
  equip.lastMaintenance = maintenance.scheduledAt;
  equip.nextMaintenance = new Date(Date.now() + MAINTENANCE_CONFIG.maintenanceInterval * 86400000).toISOString();
  
  return {
    success: true,
    maintenance,
  };
}

/**
 * Completa mantenimiento
 */
function completeMaintenance(equipmentId, maintenanceId, options = {}) {
  const { notes = '', partsReplaced = [], nextMaintenanceDate } = options;
  
  console.log(`[Maintenance] Completando mantenimiento ${maintenanceId}`);
  
  const equip = getEquipment(equipmentId);
  const history = maintenanceHistory.get(equipmentId) || [];
  
  const maintenance = history.find(m => m.id === maintenanceId);
  
  if (!maintenance) {
    throw new Error(`Mantenimiento no encontrado: ${maintenanceId}`);
  }
  
  maintenance.status = 'completed';
  maintenance.completedAt = new Date().toISOString();
  maintenance.completionNotes = notes;
  maintenance.partsReplaced = partsReplaced;
  
  // Actualizar salud del equipo
  equip.healthScore = Math.min(100, equip.healthScore + 20);
  equip.lastMaintenance = maintenance.completedAt;
  equip.nextMaintenance = nextMaintenanceDate || new Date(Date.now() + MAINTENANCE_CONFIG.maintenanceInterval * 86400000).toISOString();
  
  return {
    success: true,
    maintenance,
    equipment: equip,
  };
}

/**
 * Obtiene historial de mantenimiento
 */
function getMaintenanceHistory(equipmentId, options = {}) {
  const { limit = 50, offset = 0 } = options;
  
  const history = maintenanceHistory.get(equipmentId) || [];
  
  return {
    history: history.slice(offset, offset + limit),
    total: history.length,
    limit,
    offset,
  };
}

// ==============================================================================
// ALERTAS
// ==============================================================================

/**
 * Crea una alerta de mantenimiento
 */
function createAlert(equipmentId, alertData) {
  const { type, message, severity = 'warning' } = alertData;
  
  console.log(`[Maintenance] Alerta ${severity}: ${message}`);
  
  const alert = {
    id: `alert_${Date.now()}`,
    equipmentId,
    type,
    message,
    severity,
    status: 'active',
    createdAt: new Date().toISOString(),
    acknowledgedAt: null,
  };
  
  alerts.set(alert.id, alert);
  
  return {
    success: true,
    alert,
  };
}

/**
 * Obtiene alertas activas
 */
function getActiveAlerts(options = {}) {
  const { severity, equipmentId, limit = 50 } = options;
  
  let result = Array.from(alerts.values()).filter(a => a.status === 'active');
  
  if (severity) {
    result = result.filter(a => a.severity === severity);
  }
  
  if (equipmentId) {
    result = result.filter(a => a.equipmentId === equipmentId);
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
// MÉTRICAS
// ==============================================================================

/**
 * Obtiene métricas del sistema de mantenimiento
 */
function getMaintenanceMetrics() {
  const totalEquipment = equipment.size;
  const operationalEquipment = Array.from(equipment.values()).filter(e => e.status === 'operational').length;
  const totalPredictions = predictions.size;
  const totalAlerts = alerts.size;
  const activeAlerts = Array.from(alerts.values()).filter(a => a.status === 'active').length;
  
  const avgHealthScore = totalEquipment > 0
    ? Array.from(equipment.values()).reduce((sum, e) => sum + e.healthScore, 0) / totalEquipment
    : 0;
  
  return {
    equipment: {
      total: totalEquipment,
      operational: operationalEquipment,
      maintenance: totalEquipment - operationalEquipment,
      avgHealthScore: avgHealthScore.toFixed(1),
    },
    predictions: {
      total: totalPredictions,
    },
    alerts: {
      total: totalAlerts,
      active: activeAlerts,
      critical: Array.from(alerts.values()).filter(a => a.severity === 'critical').length,
    },
    config: MAINTENANCE_CONFIG,
    timestamp: new Date().toISOString(),
  };
}

// ==============================================================================
// API ENDPOINTS
// ==============================================================================

/**
 * POST /api/maintenance/equipment
 * Registra un equipo
 */
export async function registerEquipmentEndpoint(req, res) {
  try {
    const result = await registerEquipment(req.body);
    res.json(result);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
}

/**
 * GET /api/maintenance/equipment
 * Lista equipos
 */
export function listEquipmentEndpoint(req, res) {
  const { type, status, limit, offset } = req.query;
  
  res.json(listEquipment({ type, status, limit, offset }));
}

/**
 * GET /api/maintenance/equipment/:id
 * Obtiene un equipo
 */
export function getEquipmentEndpoint(req, res) {
  try {
    const equip = getEquipment(req.params.id);
    res.json(equip);
  } catch (error) {
    res.status(404).json({ error: error.message });
  }
}

/**
 * POST /api/maintenance/equipment/:id/predict
 * Predice fallos
 */
export async function predictFailuresEndpoint(req, res) {
  try {
    const result = await predictFailures(req.params.id, req.body.options);
    res.json(result);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
}

/**
 * POST /api/maintenance/equipment/:id/schedule
 * Programa mantenimiento
 */
export async function scheduleMaintenanceEndpoint(req, res) {
  try {
    const result = await scheduleMaintenance(req.params.id, req.body.options);
    res.json(result);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
}

/**
 * GET /api/maintenance/equipment/:id/history
 * Historial de mantenimiento
 */
export function getMaintenanceHistoryEndpoint(req, res) {
  const { limit, offset } = req.query;
  
  const result = getMaintenanceHistory(req.params.id, { limit, offset });
  
  res.json(result);
}

/**
 * GET /api/maintenance/alerts
 * Lista alertas activas
 */
export function getActiveAlertsEndpoint(req, res) {
  const { severity, equipmentId, limit } = req.query;
  
  res.json(getActiveAlerts({ severity, equipmentId, limit }));
}

/**
 * POST /api/maintenance/alerts/:id/acknowledge
 * Reconoce alerta
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
 * GET /api/maintenance/metrics
 * Métricas del sistema
 */
export function getMaintenanceMetricsEndpoint(req, res) {
  res.json(getMaintenanceMetrics());
}

/**
 * GET /api/maintenance/status
 * Estado del sistema
 */
export function getMaintenanceStatus(req, res) {
  res.json({
    status: 'active',
    config: MAINTENANCE_CONFIG,
    metrics: getMaintenanceMetrics(),
    timestamp: new Date().toISOString(),
  });
}

// ==============================================================================
// EXPORTACIONES
// ==============================================================================

export {
  registerEquipment,
  getEquipment,
  listEquipment,
  updateEquipmentStatus,
  assessEquipmentHealth,
  predictFailures,
  scheduleMaintenance,
  completeMaintenance,
  getMaintenanceHistory,
  createAlert,
  getActiveAlerts,
  acknowledgeAlert,
  getMaintenanceMetrics,
  MAINTENANCE_CONFIG,
};

export default {
  registerEquipmentEndpoint,
  listEquipmentEndpoint,
  getEquipmentEndpoint,
  predictFailuresEndpoint,
  scheduleMaintenanceEndpoint,
  getMaintenanceHistoryEndpoint,
  getActiveAlertsEndpoint,
  acknowledgeAlertEndpoint,
  getMaintenanceMetricsEndpoint,
  getMaintenanceStatus,
  registerEquipment,
  getEquipment,
  listEquipment,
  updateEquipmentStatus,
  assessEquipmentHealth,
  predictFailures,
  scheduleMaintenance,
  completeMaintenance,
  getMaintenanceHistory,
  createAlert,
  getActiveAlerts,
  acknowledgeAlert,
  getMaintenanceMetrics,
};
