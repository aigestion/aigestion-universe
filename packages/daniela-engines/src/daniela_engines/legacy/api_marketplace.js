/**
 * API Marketplace - aigestion.net
 * 
 * Marketplace de APIs de IA:
 * - Publicar APIs de IA
 * - Monetizar uso
 * - Gestionar acceso
 * - Analytics de uso
 * 
 * 100% gratuito con APIs open source
 */

import aiRouter from './ai_router.js';

// ==============================================================================
// CONFIGURACIÓN
// ==============================================================================

const MARKETPLACE_CONFIG = {
  name: 'aig API Marketplace',
  version: '1.0.0',
  maxApis: 100,
  defaultRateLimit: 1000, // requests por día
  pricing: {
    free: { requests: 1000, price: 0 },
    pro: { requests: 10000, price: 0 },
    enterprise: { requests: 100000, price: 0 },
  },
};

// ==============================================================================
// BASE DE DATOS DE APIS
// ==============================================================================

const apis = new Map();
const subscriptions = new Map();
const usageStats = new Map();

// ==============================================================================
// GESTIÓN DE APIS
// ==============================================================================

/**
 * Publica una nueva API en el marketplace
 */
async function publishApi(apiData) {
  const { name, description, endpoint, category, pricing } = apiData;
  
  console.log(`[Marketplace] Publicando API: ${name}`);
  
  const api = {
    id: `api_${Date.now()}`,
    name,
    description,
    endpoint,
    category,
    pricing: pricing || 'free',
    status: 'active',
    createdAt: new Date().toISOString(),
    stats: {
      totalCalls: 0,
      totalRevenue: 0,
      avgResponseTime: 0,
    },
  };
  
  apis.set(api.id, api);
  
  return {
    success: true,
    api,
    message: 'API publicada exitosamente',
  };
}

/**
 * Obtiene una API por ID
 */
function getApi(apiId) {
  const api = apis.get(apiId);
  
  if (!api) {
    throw new Error(`API no encontrada: ${apiId}`);
  }
  
  return api;
}

/**
 * Lista todas las APIs publicadas
 */
function listApis(options = {}) {
  const { category, status, limit = 50, offset = 0 } = options;
  
  let result = Array.from(apis.values());
  
  if (category) {
    result = result.filter(api => api.category === category);
  }
  
  if (status) {
    result = result.filter(api => api.status === status);
  }
  
  return {
    apis: result.slice(offset, offset + limit),
    total: result.length,
    limit,
    offset,
  };
}

/**
 * Actualiza una API
 */
function updateApi(apiId, updates) {
  const api = getApi(apiId);
  
  Object.assign(api, updates, { updatedAt: new Date().toISOString() });
  
  return {
    success: true,
    api,
    message: 'API actualizada exitosamente',
  };
}

/**
 * Elimina una API
 */
function deleteApi(apiId) {
  if (!apis.has(apiId)) {
    throw new Error(`API no encontrada: ${apiId}`);
  }
  
  apis.delete(apiId);
  
  return {
    success: true,
    message: 'API eliminada exitosamente',
  };
}

// ==============================================================================
// GESTIÓN DE SUSCRIPCIONES
// ==============================================================================

/**
 * Crea una suscripción a una API
 */
async function createSubscription(subscriptionData) {
  const { userId, apiId, plan = 'free' } = subscriptionData;
  
  console.log(`[Marketplace] Creando suscripción: ${userId} → ${apiId}`);
  
  const api = getApi(apiId);
  
  const subscription = {
    id: `sub_${Date.now()}`,
    userId,
    apiId,
    plan,
    status: 'active',
    createdAt: new Date().toISOString(),
    usage: {
      requests: 0,
      lastReset: new Date().toISOString(),
    },
    limits: MARKETPLACE_CONFIG.pricing[plan] || MARKETPLACE_CONFIG.pricing.free,
  };
  
  subscriptions.set(subscription.id, subscription);
  
  return {
    success: true,
    subscription,
    message: 'Suscripción creada exitosamente',
  };
}

/**
 * Obtiene una suscripción por ID
 */
function getSubscription(subscriptionId) {
  const subscription = subscriptions.get(subscriptionId);
  
  if (!subscription) {
    throw new Error(`Suscripción no encontrada: ${subscriptionId}`);
  }
  
  return subscription;
}

/**
 * Lista suscripciones de un usuario
 */
function listUserSubscriptions(userId) {
  return Array.from(subscriptions.values())
    .filter(sub => sub.userId === userId)
    .map(sub => ({
      ...sub,
      api: apis.get(sub.apiId),
    }));
}

/**
 * Cancela una suscripción
 */
function cancelSubscription(subscriptionId) {
  const subscription = getSubscription(subscriptionId);
  
  subscription.status = 'cancelled';
  subscription.cancelledAt = new Date().toISOString();
  
  return {
    success: true,
    subscription,
    message: 'Suscripción cancelada exitosamente',
  };
}

// ==============================================================================
// ANALYTICS Y MÉTRICAS
// ==============================================================================

/**
 * Registra uso de una API
 */
function recordUsage(apiId, userId, metadata = {}) {
  const api = getApi(apiId);
  
  // Actualizar estadísticas de la API
  api.stats.totalCalls++;
  
  // Actualizar estadísticas de uso
  const usageKey = `${apiId}_${userId}`;
  const usage = usageStats.get(usageKey) || {
    apiId,
    userId,
    totalCalls: 0,
    lastCall: null,
  };
  
  usage.totalCalls++;
  usage.lastCall = new Date().toISOString();
  
  usageStats.set(usageKey, usage);
  
  return {
    success: true,
    usage,
  };
}

/**
 * Obtiene métricas de una API
 */
function getApiMetrics(apiId) {
  const api = getApi(apiId);
  
  const apiUsage = Array.from(usageStats.values())
    .filter(u => u.apiId === apiId);
  
  return {
    apiId,
    name: api.name,
    totalCalls: api.stats.totalCalls,
    uniqueUsers: apiUsage.length,
    avgResponseTime: api.stats.avgResponseTime,
    revenue: api.stats.totalRevenue,
  };
}

/**
 * Obtiene métricas globales del marketplace
 */
function getMarketplaceMetrics() {
  const totalApis = apis.size;
  const totalSubscriptions = subscriptions.size;
  const totalCalls = Array.from(apis.values())
    .reduce((sum, api) => sum + api.stats.totalCalls, 0);
  
  return {
    totalApis,
    totalSubscriptions,
    totalCalls,
    activeApis: Array.from(apis.values()).filter(a => a.status === 'active').length,
    categories: [...new Set(Array.from(apis.values()).map(a => a.category))],
  };
}

// ==============================================================================
// BÚSQUEDA Y DESCUBRIMIENTO
// ==============================================================================

/**
 * Busca APIs por texto
 */
function searchApis(query, options = {}) {
  const { limit = 20 } = options;
  
  const lowerQuery = query.toLowerCase();
  
  const results = Array.from(apis.values())
    .filter(api => 
      api.name.toLowerCase().includes(lowerQuery) ||
      api.description.toLowerCase().includes(lowerQuery) ||
      api.category.toLowerCase().includes(lowerQuery)
    )
    .slice(0, limit);
  
  return {
    query,
    results,
    total: results.length,
  };
}

/**
 * Obtiene APIs por categoría
 */
function getApisByCategory(category) {
  return Array.from(apis.values())
    .filter(api => api.category === category)
    .map(api => ({
      ...api,
      metrics: getApiMetrics(api.id),
    }));
}

/**
 * Obtiene categorías disponibles
 */
function getCategories() {
  const categories = [...new Set(Array.from(apis.values()).map(a => a.category))];
  
  return categories.map(cat => ({
    name: cat,
    count: Array.from(apis.values()).filter(a => a.category === cat).length,
  }));
}

// ==============================================================================
// API ENDPOINTS
// ==============================================================================

/**
 * POST /api/marketplace/apis
 * Publica una nueva API
 */
export async function publishApiEndpoint(req, res) {
  try {
    const result = await publishApi(req.body);
    res.json(result);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
}

/**
 * GET /api/marketplace/apis
 * Lista todas las APIs
 */
export function listApisEndpoint(req, res) {
  const { category, status, limit, offset } = req.query;
  
  res.json(listApis({ category, status, limit, offset }));
}

/**
 * GET /api/marketplace/apis/:id
 * Obtiene una API específica
 */
export function getApiEndpoint(req, res) {
  try {
    const api = getApi(req.params.id);
    res.json(api);
  } catch (error) {
    res.status(404).json({ error: error.message });
  }
}

/**
 * PUT /api/marketplace/apis/:id
 * Actualiza una API
 */
export function updateApiEndpoint(req, res) {
  try {
    const result = updateApi(req.params.id, req.body);
    res.json(result);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
}

/**
 * DELETE /api/marketplace/apis/:id
 * Elimina una API
 */
export function deleteApiEndpoint(req, res) {
  try {
    const result = deleteApi(req.params.id);
    res.json(result);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
}

/**
 * POST /api/marketplace/subscriptions
 * Crea una suscripción
 */
export async function createSubscriptionEndpoint(req, res) {
  try {
    const result = await createSubscription(req.body);
    res.json(result);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
}

/**
 * GET /api/marketplace/metrics
 * Métricas del marketplace
 */
export function getMarketplaceMetricsEndpoint(req, res) {
  res.json(getMarketplaceMetrics());
}

/**
 * GET /api/marketplace/search
 * Busca APIs
 */
export function searchApisEndpoint(req, res) {
  const { q, limit } = req.query;
  
  if (!q) {
    return res.status(400).json({ error: 'Query required' });
  }
  
  res.json(searchApis(q, { limit }));
}

/**
 * GET /api/marketplace/categories
 * Lista categorías
 */
export function getCategoriesEndpoint(req, res) {
  res.json({
    categories: getCategories(),
  });
}

/**
 * GET /api/marketplace/status
 * Estado del marketplace
 */
export function getMarketplaceStatus(req, res) {
  res.json({
    status: 'active',
    config: MARKETPLACE_CONFIG,
    metrics: getMarketplaceMetrics(),
    timestamp: new Date().toISOString(),
  });
}

// ==============================================================================
// EXPORTACIONES
// ==============================================================================

export {
  publishApi,
  getApi,
  listApis,
  updateApi,
  deleteApi,
  createSubscription,
  getSubscription,
  listUserSubscriptions,
  cancelSubscription,
  recordUsage,
  getApiMetrics,
  getMarketplaceMetrics,
  searchApis,
  getApisByCategory,
  getCategories,
  MARKETPLACE_CONFIG,
};

export default {
  publishApiEndpoint,
  listApisEndpoint,
  getApiEndpoint,
  updateApiEndpoint,
  deleteApiEndpoint,
  createSubscriptionEndpoint,
  getMarketplaceMetricsEndpoint,
  searchApisEndpoint,
  getCategoriesEndpoint,
  getMarketplaceStatus,
  publishApi,
  getApi,
  listApis,
  updateApi,
  deleteApi,
  createSubscription,
  getSubscription,
  listUserSubscriptions,
  cancelSubscription,
  recordUsage,
  getApiMetrics,
  getMarketplaceMetrics,
  searchApis,
  getApisByCategory,
  getCategories,
};
