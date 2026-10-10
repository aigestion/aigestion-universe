/**
 * aig Cloud - Plataforma Cloud Empresarial
 * 
 * Infraestructura cloud para soluciones IA:
 * - Multi-tenant SaaS
 * - API Gateway
 * - Storage escalable
 * - Monitoreo y alertas
 * 
 * 100% gratuito con APIs open source
 */

import aiRouter from './ai_router.js';

// ==============================================================================
// CONFIGURACIÓN CLOUD
// ==============================================================================

const CLOUD_CONFIG = {
  name: 'aig Cloud',
  version: '1.0.0',
  region: 'local',
  multiTenant: true,
  maxTenants: 100,
  storageLimit: '10GB', // por tenant
  apiRateLimit: 1000, // requests por minuto
};

// ==============================================================================
// GESTIÓN DE TENANTS
// ==============================================================================

const tenants = new Map();

/**
 * Crea un nuevo tenant (empresa cliente)
 */
async function createTenant(tenantData) {
  const { name, email, plan = 'starter' } = tenantData;
  
  console.log(`[Cloud] Creando tenant: ${name}`);
  
  const tenant = {
    id: `tenant_${Date.now()}`,
    name,
    email,
    plan,
    status: 'active',
    createdAt: new Date().toISOString(),
    usage: {
      apiCalls: 0,
      storage: 0,
      aiRequests: 0,
    },
    config: {
      maxUsers: plan === 'enterprise' ? 100 : plan === 'pro' ? 20 : 5,
      features: getPlanFeatures(plan),
    },
  };
  
  tenants.set(tenant.id, tenant);
  
  return {
    success: true,
    tenant,
    message: 'Tenant creado exitosamente',
  };
}

/**
 * Obtiene información de un tenant
 */
function getTenant(tenantId) {
  const tenant = tenants.get(tenantId);
  
  if (!tenant) {
    throw new Error(`Tenant no encontrado: ${tenantId}`);
  }
  
  return tenant;
}

/**
 * Actualiza uso de un tenant
 */
function updateTenantUsage(tenantId, usage) {
  const tenant = getTenant(tenantId);
  
  tenant.usage.apiCalls += usage.apiCalls || 0;
  tenant.usage.storage += usage.storage || 0;
  tenant.usage.aiRequests += usage.aiRequests || 0;
  
  return tenant;
}

/**
 * Lista todos los tenants
 */
function listTenants() {
  return Array.from(tenants.values()).map(t => ({
    id: t.id,
    name: t.name,
    plan: t.plan,
    status: t.status,
    usage: t.usage,
  }));
}

// ==============================================================================
// API GATEWAY
// ==============================================================================

/**
 * Procesa una request a través del API Gateway
 */
async function processApiRequest(request) {
  const { tenantId, endpoint, method, data } = request;
  
  console.log(`[Cloud] Procesando request: ${method} ${endpoint} para tenant ${tenantId}`);
  
  // Verificar tenant
  const tenant = getTenant(tenantId);
  
  // Verificar rate limit
  if (tenant.usage.apiCalls >= CLOUD_CONFIG.apiRateLimit) {
    throw new Error('Rate limit excedido');
  }
  
  // Procesar con IA si es necesario
  let response;
  if (endpoint.includes('/ai/')) {
    response = await processAIRequest(data, tenant);
  } else {
    response = { message: 'Request procesada', data };
  }
  
  // Actualizar uso
  updateTenantUsage(tenantId, { apiCalls: 1, aiRequests: endpoint.includes('/ai/') ? 1 : 0 });
  
  return {
    success: true,
    response,
    tenant: tenant.id,
    timestamp: new Date().toISOString(),
  };
}

/**
 * Procesa una request de IA
 */
async function processAIRequest(data, tenant) {
  const prompt = data.prompt || data.message;
  
  const result = await aiRouter.callAI(prompt, {
    systemPrompt: `Eres un asistente de ${tenant.name}. Responde de forma profesional y útil.`,
    maxTokens: data.maxTokens || 200,
    temperature: data.temperature || 0.7,
  });
  
  return {
    response: result.response,
    provider: result.provider,
    tokens: result.usage?.total_tokens || 0,
  };
}

// ==============================================================================
// STORAGE
// ==============================================================================

/**
 * Almacena datos para un tenant
 */
async function storeData(tenantId, key, data) {
  const tenant = getTenant(tenantId);
  
  // Verificar límite de storage
  const dataSize = JSON.stringify(data).length;
  if (tenant.usage.storage + dataSize > parseStorageLimit(CLOUD_CONFIG.storageLimit)) {
    throw new Error('Storage limit excedido');
  }
  
  // Almacenar (en producción, usar S3/MinIO)
  const storageKey = `${tenantId}/${key}`;
  
  updateTenantUsage(tenantId, { storage: dataSize });
  
  return {
    success: true,
    key: storageKey,
    size: dataSize,
  };
}

/**
 * Obtiene datos de un tenant
 */
async function getData(tenantId, key) {
  const tenant = getTenant(tenantId);
  
  // En producción, obtener de S3/MinIO
  return {
    success: true,
    data: null, // Implementar según backend
  };
}

// ==============================================================================
// MONITOREO Y ALERTAS
// ==============================================================================

/**
 * Obtiene métricas del sistema
 */
function getSystemMetrics() {
  const totalTenants = tenants.size;
  const totalApiCalls = Array.from(tenants.values()).reduce((sum, t) => sum + t.usage.apiCalls, 0);
  const totalAiRequests = Array.from(tenants.values()).reduce((sum, t) => sum + t.usage.aiRequests, 0);
  
  return {
    tenants: {
      total: totalTenants,
      active: Array.from(tenants.values()).filter(t => t.status === 'active').length,
    },
    usage: {
      apiCalls: totalApiCalls,
      aiRequests: totalAiRequests,
    },
    limits: {
      maxTenants: CLOUD_CONFIG.maxTenants,
      apiRateLimit: CLOUD_CONFIG.apiRateLimit,
      storageLimit: CLOUD_CONFIG.storageLimit,
    },
    timestamp: new Date().toISOString(),
  };
}

/**
 * Genera alertas del sistema
 */
function generateAlerts() {
  const alerts = [];
  const metrics = getSystemMetrics();
  
  // Alerta de tenants cerca del límite
  if (metrics.tenants.total > CLOUD_CONFIG.maxTenants * 0.8) {
    alerts.push({
      type: 'warning',
      category: 'tenants',
      message: `Tenants cerca del límite: ${metrics.tenants.total}/${CLOUD_CONFIG.maxTenants}`,
      severity: 'medium',
    });
  }
  
  // Alerta de uso de API
  if (metrics.usage.apiCalls > CLOUD_CONFIG.apiRateLimit * 0.9) {
    alerts.push({
      type: 'warning',
      category: 'api',
      message: 'Uso de API cerca del límite',
      severity: 'high',
    });
  }
  
  return {
    success: true,
    alerts,
    total: alerts.length,
  };
}

// ==============================================================================
// FUNCIONES AUXILIARES
// ==============================================================================

function getPlanFeatures(plan) {
  const features = {
    starter: ['basic_ai', 'email_support', '5_users'],
    pro: ['advanced_ai', 'priority_support', '20_users', 'analytics'],
    enterprise: ['all_features', 'dedicated_support', 'unlimited_users', 'custom_integrations'],
  };
  
  return features[plan] || features.starter;
}

function parseStorageLimit(limit) {
  const match = limit.match(/(\d+)(GB|MB)/);
  if (!match) return 10 * 1024 * 1024 * 1024; // 10GB default
  
  const value = parseInt(match[1]);
  const unit = match[2];
  
  return unit === 'GB' ? value * 1024 * 1024 * 1024 : value * 1024 * 1024;
}

// ==============================================================================
// API ENDPOINTS
// ==============================================================================

/**
 * POST /api/cloud/tenants
 * Crea un nuevo tenant
 */
export async function createTenantEndpoint(req, res) {
  try {
    const result = await createTenant(req.body);
    res.json(result);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
}

/**
 * GET /api/cloud/tenants
 * Lista todos los tenants
 */
export function listTenantsEndpoint(req, res) {
  res.json({
    tenants: listTenants(),
    total: tenants.size,
  });
}

/**
 * POST /api/cloud/request
 * Procesa una request del API Gateway
 */
export async function processApiRequestEndpoint(req, res) {
  try {
    const result = await processApiRequest(req.body);
    res.json(result);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
}

/**
 * GET /api/cloud/metrics
 * Obtiene métricas del sistema
 */
export function getSystemMetricsEndpoint(req, res) {
  res.json(getSystemMetrics());
}

/**
 * GET /api/cloud/alerts
 * Genera alertas del sistema
 */
export function generateAlertsEndpoint(req, res) {
  res.json(generateAlerts());
}

/**
 * GET /api/cloud/status
 * Estado del sistema cloud
 */
export function getCloudStatus(req, res) {
  res.json({
    status: 'active',
    config: CLOUD_CONFIG,
    metrics: getSystemMetrics(),
    timestamp: new Date().toISOString(),
  });
}

// ==============================================================================
// EXPORTACIONES
// ==============================================================================

export {
  createTenant,
  getTenant,
  listTenants,
  processApiRequest,
  storeData,
  getData,
  getSystemMetrics,
  generateAlerts,
  CLOUD_CONFIG,
};

export default {
  createTenantEndpoint,
  listTenantsEndpoint,
  processApiRequestEndpoint,
  getSystemMetricsEndpoint,
  generateAlertsEndpoint,
  getCloudStatus,
  createTenant,
  getTenant,
  listTenants,
  processApiRequest,
  getSystemMetrics,
  generateAlerts,
};
