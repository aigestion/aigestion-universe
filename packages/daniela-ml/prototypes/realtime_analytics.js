/**
 * Real-time Analytics - aigestion.net
 * 
 * Sistema de analítica en tiempo real:
 * - Métricas en vivo
 * - Eventos en tiempo real
 * - Alertas automáticas
 * - Dashboards en tiempo real
 * - Análisis predictivo
 * 
 * 100% gratuito con APIs open source
 */

import aiRouter from './ai_router.js';

// ==============================================================================
// CONFIGURACIÓN
// ==============================================================================

const REALTIME_CONFIG = {
  name: 'aig Real-time Analytics',
  version: '1.0.0',
  maxEventsPerSecond: 1000,
  retentionPeriod: 86400000, // 24 horas
  aggregationInterval: 60000, // 1 minuto
  alertThresholds: {
    errorRate: 0.05,
    responseTime: 2000,
    cpuUsage: 0.8,
    memoryUsage: 0.9,
  },
};

// ==============================================================================
// ALMACENAMIENTO DE MÉTRICAS
// ==============================================================================

const metricsStore = new Map();
const eventsStore = [];
const alertsStore = new Map();

/**
 * Registra una métrica
 */
function recordMetric(name, value, tags = {}) {
  const timestamp = Date.now();
  const key = `${name}_${JSON.stringify(tags)}`;
  
  if (!metricsStore.has(key)) {
    metricsStore.set(key, {
      name,
      tags,
      values: [],
      count: 0,
      sum: 0,
      min: Infinity,
      max: -Infinity,
    });
  }
  
  const metric = metricsStore.get(key);
  metric.values.push({ value, timestamp });
  metric.count++;
  metric.sum += value;
  metric.min = Math.min(metric.min, value);
  metric.max = Math.max(metric.max, value);
  
  // Mantener solo últimas 24 horas
  const cutoff = timestamp - REALTIME_CONFIG.retentionPeriod;
  metric.values = metric.values.filter(v => v.timestamp > cutoff);
  
  // Verificar alertas
  checkMetricAlerts(name, value, tags);
  
  return metric;
}

/**
 * Registra un evento
 */
function recordEvent(type, data, options = {}) {
  const { severity = 'info', source = 'system' } = options;
  
  const event = {
    id: `evt_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
    type,
    data,
    severity,
    source,
    timestamp: new Date().toISOString(),
  };
  
  eventsStore.push(event);
  
  // Mantener solo últimos 10000 eventos
  if (eventsStore.length > 10000) {
    eventsStore.shift();
  }
  
  return event;
}

/**
 * Verifica alertas de métricas
 */
function checkMetricAlerts(name, value, tags) {
  const thresholds = REALTIME_CONFIG.alertThresholds;
  
  if (name === 'error_rate' && value > thresholds.errorRate) {
    createAlert('error_rate_high', `Error rate alto: ${(value * 100).toFixed(1)}%`, 'high', tags);
  }
  
  if (name === 'response_time' && value > thresholds.responseTime) {
    createAlert('response_time_high', `Tiempo de respuesta alto: ${value}ms`, 'medium', tags);
  }
  
  if (name === 'cpu_usage' && value > thresholds.cpuUsage) {
    createAlert('cpu_usage_high', `Uso de CPU alto: ${(value * 100).toFixed(1)}%`, 'medium', tags);
  }
  
  if (name === 'memory_usage' && value > thresholds.memoryUsage) {
    createAlert('memory_usage_high', `Uso de memoria alto: ${(value * 100).toFixed(1)}%`, 'high', tags);
  }
}

/**
 * Crea una alerta
 */
function createAlert(type, message, severity, tags = {}) {
  const alert = {
    id: `alert_${Date.now()}`,
    type,
    message,
    severity,
    tags,
    status: 'active',
    createdAt: new Date().toISOString(),
    acknowledgedAt: null,
  };
  
  alertsStore.set(alert.id, alert);
  
  console.log(`[Alert] ${severity.toUpperCase()}: ${message}`);
  
  return alert;
}

// ==============================================================================
// AGREGACIÓN DE MÉTRICAS
// ==============================================================================

/**
 * Agrega métricas por período
 */
function aggregateMetrics(name, period = '1m', tags = {}) {
  const key = `${name}_${JSON.stringify(tags)}`;
  const metric = metricsStore.get(key);
  
  if (!metric) {
    return null;
  }
  
  const now = Date.now();
  const periods = {
    '1m': 60000,
    '5m': 300000,
    '1h': 3600000,
    '1d': 86400000,
  };
  
  const periodMs = periods[period] || periods['1m'];
  const cutoff = now - periodMs;
  
  const values = metric.values
    .filter(v => v.timestamp > cutoff)
    .map(v => v.value);
  
  if (values.length === 0) {
    return null;
  }
  
  const sum = values.reduce((a, b) => a + b, 0);
  const avg = sum / values.length;
  const min = Math.min(...values);
  const max = Math.max(...values);
  
  return {
    name,
    period,
    count: values.length,
    sum,
    avg,
    min,
    max,
    timestamp: new Date().toISOString(),
  };
}

/**
 * Obtiene estadísticas de métricas
 */
function getMetricStats(name, tags = {}) {
  const key = `${name}_${JSON.stringify(tags)}`;
  const metric = metricsStore.get(key);
  
  if (!metric) {
    return null;
  }
  
  const values = metric.values.map(v => v.value);
  
  if (values.length === 0) {
    return null;
  }
  
  const sorted = [...values].sort((a, b) => a - b);
  const sum = values.reduce((a, b) => a + b, 0);
  
  return {
    name,
    count: values.count,
    sum,
    avg: sum / values.length,
    min: sorted[0],
    max: sorted[sorted.length - 1],
    median: sorted[Math.floor(sorted.length / 2)],
    p95: sorted[Math.floor(sorted.length * 0.95)],
    p99: sorted[Math.floor(sorted.length * 0.99)],
  };
}

// ==============================================================================
// ANÁLISIS EN TIEMPO REAL
// ==============================================================================

/**
 * Analiza tendencias en tiempo real
 */
async function analyzeTrends(metricName, options = {}) {
  const { period = '1h', tags = {} } = options;
  
  console.log(`[Analytics] Analizando tendencias: ${metricName}`);
  
  const stats = getMetricStats(metricName, tags);
  
  if (!stats) {
    return {
      success: false,
      error: 'No hay datos suficientes',
    };
  }
  
  // Análisis con IA
  const prompt = `Analiza las siguientes métricas y proporciona insights:

Métrica: ${metricName}
Período: ${period}
Estadísticas: ${JSON.stringify(stats)}

Proporciona:
1. Tendencia actual
2. Anomalías detectadas
3. Predicción próxima hora
4. Recomendaciones`;
  
  const result = await aiRouter.callAI(prompt, {
    systemPrompt: 'Eres un analista de datos en tiempo real. Proporciona insights accionables.',
    maxTokens: 400,
    temperature: 0.4,
  });
  
  return {
    success: true,
    metric: metricName,
    period,
    stats,
    analysis: result.response,
    provider: result.provider,
    timestamp: new Date().toISOString(),
  };
}

/**
 * Genera reporte en tiempo real
 */
async function generateRealtimeReport(options = {}) {
  const { metrics = [], period = '1h' } = options;
  
  console.log(`[Analytics] Generando reporte en tiempo real`);
  
  const report = {
    period,
    generatedAt: new Date().toISOString(),
    metrics: {},
    alerts: Array.from(alertsStore.values()).filter(a => a.status === 'active'),
    summary: {},
  };
  
  // Agregar métricas solicitadas
  for (const metricName of metrics) {
    const stats = getMetricStats(metricName);
    if (stats) {
      report.metrics[metricName] = stats;
    }
  }
  
  // Generar resumen con IA
  const prompt = `Genera un resumen ejecutivo basado en las siguientes métricas:
${JSON.stringify(report.metrics)}

Alertas activas: ${report.alerts.length}

Proporciona:
1. Resumen ejecutivo
2. Puntos clave
3. Acciones recomendadas`;
  
  const result = await aiRouter.callAI(prompt, {
    systemPrompt: 'Eres un analista ejecutivo. Proporciona resúmenes claros y accionables.',
    maxTokens: 300,
    temperature: 0.5,
  });
  
  report.summary = result.response;
  
  return {
    success: true,
    report,
    timestamp: new Date().toISOString(),
  };
}

// ==============================================================================
// DASHBOARD
// ==============================================================================

/**
 * Obtiene datos para el dashboard
 */
function getDashboardData(options = {}) {
  const { period = '1h' } = options;
  
  const metricNames = Array.from(metricsStore.keys())
    .map(key => metricsStore.get(key).name);
  
  const uniqueMetrics = [...new Set(metricNames)];
  
  const dashboard = {
    period,
    generatedAt: new Date().toISOString(),
    metrics: {},
    alerts: {
      active: Array.from(alertsStore.values()).filter(a => a.status === 'active').length,
      total: alertsStore.size,
    },
    events: {
      total: eventsStore.length,
      recent: eventsStore.slice(-10),
    },
  };
  
  // Agregar métricas al dashboard
  for (const metricName of uniqueMetrics) {
    const stats = getMetricStats(metricName);
    if (stats) {
      dashboard.metrics[metricName] = stats;
    }
  }
  
  return dashboard;
}

// ==============================================================================
// LIMPIEZA
// ==============================================================================

/**
 * Limpia datos antiguos
 */
function cleanup() {
  const now = Date.now();
  const cutoff = now - REALTIME_CONFIG.retentionPeriod;
  
  let removedMetrics = 0;
  let removedEvents = 0;
  
  // Limpiar métricas antiguas
  for (const [key, metric] of metricsStore.entries()) {
    const originalLength = metric.values.length;
    metric.values = metric.values.filter(v => v.timestamp > cutoff);
    removedMetrics += originalLength - metric.values.length;
  }
  
  // Limpiar eventos antiguos
  const originalEventsLength = eventsStore.length;
  while (eventsStore.length > 0 && new Date(eventsStore[0].timestamp).getTime() < cutoff) {
    eventsStore.shift();
    removedEvents++;
  }
  
  return {
    removedMetrics,
    removedEvents,
    timestamp: new Date().toISOString(),
  };
}

// ==============================================================================
// API ENDPOINTS
// ==============================================================================

/**
 * POST /api/analytics/metrics
 * Registra una métrica
 */
export function recordMetricEndpoint(req, res) {
  const { name, value, tags } = req.body;
  
  if (!name || value === undefined) {
    return res.status(400).json({ error: 'Name and value required' });
  }
  
  const metric = recordMetric(name, value, tags);
  
  res.json({
    success: true,
    metric: {
      name: metric.name,
      count: metric.count,
      avg: metric.sum / metric.count,
    },
  });
}

/**
 * POST /api/analytics/events
 * Registra un evento
 */
export function recordEventEndpoint(req, res) {
  const { type, data, severity, source } = req.body;
  
  if (!type) {
    return res.status(400).json({ error: 'Type required' });
  }
  
  const event = recordEvent(type, data, { severity, source });
  
  res.json({
    success: true,
    event,
  });
}

/**
 * GET /api/analytics/metrics/:name
 * Obtiene estadísticas de una métrica
 */
export function getMetricStatsEndpoint(req, res) {
  const stats = getMetricStats(req.params.name, req.query.tags ? JSON.parse(req.query.tags) : {});
  
  if (!stats) {
    return res.status(404).json({ error: 'Metric not found' });
  }
  
  res.json(stats);
}

/**
 * GET /api/analytics/aggregate/:name
 * Agrega métricas por período
 */
export function aggregateMetricsEndpoint(req, res) {
  const { period, tags } = req.query;
  
  const aggregated = aggregateMetrics(req.params.name, period, tags ? JSON.parse(tags) : {});
  
  if (!aggregated) {
    return res.status(404).json({ error: 'No data found' });
  }
  
  res.json(aggregated);
}

/**
 * POST /api/analytics/trends
 * Analiza tendencias
 */
export async function analyzeTrendsEndpoint(req, res) {
  const { metricName, period, tags } = req.body;
  
  if (!metricName) {
    return res.status(400).json({ error: 'Metric name required' });
  }
  
  try {
    const result = await analyzeTrends(metricName, { period, tags });
    res.json(result);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
}

/**
 * POST /api/analytics/report
 * Genera reporte en tiempo real
 */
export async function generateRealtimeReportEndpoint(req, res) {
  const { metrics, period } = req.body;
  
  try {
    const result = await generateRealtimeReport({ metrics, period });
    res.json(result);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
}

/**
 * GET /api/analytics/dashboard
 * Datos para el dashboard
 */
export function getDashboardDataEndpoint(req, res) {
  const { period } = req.query;
  
  res.json(getDashboardData({ period }));
}

/**
 * GET /api/analytics/alerts
 * Lista alertas activas
 */
export function getActiveAlertsEndpoint(req, res) {
  const alerts = Array.from(alertsStore.values())
    .filter(a => a.status === 'active');
  
  res.json({
    alerts,
    total: alerts.length,
  });
}

/**
 * POST /api/analytics/alerts/:id/acknowledge
 * Reconoce una alerta
 */
export function acknowledgeAlertEndpoint(req, res) {
  const alert = alertsStore.get(req.params.id);
  
  if (!alert) {
    return res.status(404).json({ error: 'Alert not found' });
  }
  
  alert.status = 'acknowledged';
  alert.acknowledgedAt = new Date().toISOString();
  
  res.json({
    success: true,
    alert,
  });
}

/**
 * GET /api/analytics/status
 * Estado del sistema de analítica
 */
export function getAnalyticsStatus(req, res) {
  res.json({
    status: 'active',
    config: REALTIME_CONFIG,
    metrics: {
      total: metricsStore.size,
      events: eventsStore.length,
      alerts: alertsStore.size,
    },
    timestamp: new Date().toISOString(),
  });
}

// ==============================================================================
// EXPORTACIONES
// ==============================================================================

export {
  recordMetric,
  recordEvent,
  aggregateMetrics,
  getMetricStats,
  analyzeTrends,
  generateRealtimeReport,
  getDashboardData,
  cleanup,
  REALTIME_CONFIG,
};

export default {
  recordMetricEndpoint,
  recordEventEndpoint,
  getMetricStatsEndpoint,
  aggregateMetricsEndpoint,
  analyzeTrendsEndpoint,
  generateRealtimeReportEndpoint,
  getDashboardDataEndpoint,
  getActiveAlertsEndpoint,
  acknowledgeAlertEndpoint,
  getAnalyticsStatus,
  recordMetric,
  recordEvent,
  aggregateMetrics,
  getMetricStats,
  analyzeTrends,
  generateRealtimeReport,
  getDashboardData,
  cleanup,
};
