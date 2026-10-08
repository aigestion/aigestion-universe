/**
 * Multi-tenant SaaS - aigestion.net
 * 
 * Plataforma SaaS multi-tenant:
 * - Gestión de múltiples clientes
 * - Aislamiento de datos por tenant
 * - Personalización por tenant
 * - Facturación y suscripciones
 * - Admin de tenants
 * 
 * 100% gratuito con APIs open source
 */

import aiRouter from './ai_router.js';

// ==============================================================================
// CONFIGURACIÓN
// ==============================================================================

const SAAS_CONFIG = {
  name: 'aig SaaS',
  version: '1.0.0',
  maxTenants: 100,
  defaultPlan: 'starter',
  plans: {
    starter: {
      name: 'Starter',
      price: 0,
      features: ['5 users', '1000 API calls/mes', 'Email support'],
      limits: { users: 5, apiCalls: 1000, storage: '1GB' },
    },
    pro: {
      name: 'Pro',
      price: 0,
      features: ['20 users', '10000 API calls/mes', 'Priority support'],
      limits: { users: 20, apiCalls: 10000, storage: '10GB' },
    },
    enterprise: {
      name: 'Enterprise',
      price: 0,
      features: ['Unlimited users', 'Unlimited API calls', 'Dedicated support'],
      limits: { users: -1, apiCalls: -1, storage: 'Unlimited' },
    },
  },
};

// ==============================================================================
// BASE DE DATOS
// ==============================================================================

const tenants = new Map();
const users = new Map();
const subscriptions = new Map();
const usageRecords = new Map();

// ==============================================================================
// GESTIÓN DE TENANTS
// ==============================================================================

/**
 * Crea un nuevo tenant (empresa cliente)
 */
async function createTenant(tenantData) {
  const { name, email, plan = 'starter', industry = 'general' } = tenantData;
  
  console.log(`[SaaS] Creando tenant: ${name}`);
  
  const tenant = {
    id: `tenant_${Date.now()}`,
    name,
    email,
    plan,
    industry,
    status: 'active',
    createdAt: new Date().toISOString(),
    settings: {
      branding: { logo: null, colors: {} },
      features: SAAS_CONFIG.plans[plan].features,
      limits: SAAS_CONFIG.plans[plan].limits,
    },
    usage: {
      apiCalls: 0,
      storage: 0,
      users: 0,
    },
    billing: {
      balance: 0,
      lastPayment: null,
      nextPayment: null,
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
 * Obtiene un tenant por ID
 */
function getTenant(tenantId) {
  const tenant = tenants.get(tenantId);
  
  if (!tenant) {
    throw new Error(`Tenant no encontrado: ${tenantId}`);
  }
  
  return tenant;
}

/**
 * Actualiza un tenant
 */
function updateTenant(tenantId, updates) {
  const tenant = getTenant(tenantId);
  
  Object.assign(tenant, updates, { updatedAt: new Date().toISOString() });
  
  return {
    success: true,
    tenant,
    message: 'Tenant actualizado exitosamente',
  };
}

/**
 * Elimina un tenant
 */
function deleteTenant(tenantId) {
  if (!tenants.has(tenantId)) {
    throw new Error(`Tenant no encontrado: ${tenantId}`);
  }
  
  tenants.delete(tenantId);
  
  return {
    success: true,
    message: 'Tenant eliminado exitosamente',
  };
}

/**
 * Lista todos los tenants
 */
function listTenants(options = {}) {
  const { status, plan, limit = 50, offset = 0 } = options;
  
  let result = Array.from(tenants.values());
  
  if (status) {
    result = result.filter(t => t.status === status);
  }
  
  if (plan) {
    result = result.filter(t => t.plan === plan);
  }
  
  return {
    tenants: result.slice(offset, offset + limit),
    total: result.length,
    limit,
    offset,
  };
}

// ==============================================================================
// GESTIÓN DE USUARIOS
// ==============================================================================

/**
 * Crea un usuario en un tenant
 */
async function createUser(userData) {
  const { tenantId, name, email, role = 'user' } = userData;
  
  console.log(`[SaaS] Creando usuario: ${name} en tenant ${tenantId}`);
  
  const tenant = getTenant(tenantId);
  
  // Verificar límite de usuarios
  if (tenant.usage.users >= tenant.settings.limits.users) {
    throw new Error('Límite de usuarios excedido');
  }
  
  const user = {
    id: `user_${Date.now()}`,
    tenantId,
    name,
    email,
    role,
    status: 'active',
    createdAt: new Date().toISOString(),
    lastLogin: null,
  };
  
  users.set(user.id, user);
  
  // Actualizar contador de usuarios
  tenant.usage.users++;
  
  return {
    success: true,
    user,
    message: 'Usuario creado exitosamente',
  };
}

/**
 * Obtiene un usuario por ID
 */
function getUser(userId) {
  const user = users.get(userId);
  
  if (!user) {
    throw new Error(`Usuario no encontrado: ${userId}`);
  }
  
  return user;
}

/**
 * Actualiza un usuario
 */
function updateUser(userId, updates) {
  const user = getUser(userId);
  
  Object.assign(user, updates, { updatedAt: new Date().toISOString() });
  
  return {
    success: true,
    user,
    message: 'Usuario actualizado exitosamente',
  };
}

/**
 * Elimina un usuario
 */
function deleteUser(userId) {
  const user = getUser(userId);
  const tenant = getTenant(user.tenantId);
  
  users.delete(userId);
  tenant.usage.users--;
  
  return {
    success: true,
    message: 'Usuario eliminado exitosamente',
  };
}

/**
 * Lista usuarios de un tenant
 */
function listTenantUsers(tenantId) {
  getTenant(tenantId); // Verificar que existe
  
  return Array.from(users.values())
    .filter(u => u.tenantId === tenantId);
}

// ==============================================================================
// GESTIÓN DE SUSCRIPCIONES
// ==============================================================================

/**
 * Crea una suscripción para un tenant
 */
async function createSubscription(subscriptionData) {
  const { tenantId, plan = 'starter', duration = 'monthly' } = subscriptionData;
  
  console.log(`[SaaS] Creando suscripción: ${tenantId} → ${plan}`);
  
  const tenant = getTenant(tenantId);
  
  const subscription = {
    id: `sub_${Date.now()}`,
    tenantId,
    plan,
    duration,
    status: 'active',
    startDate: new Date().toISOString(),
    endDate: calculateEndDate(duration),
    autoRenew: true,
  };
  
  subscriptions.set(subscription.id, subscription);
  
  // Actualizar plan del tenant
  tenant.plan = plan;
  tenant.settings.features = SAAS_CONFIG.plans[plan].features;
  tenant.settings.limits = SAAS_CONFIG.plans[plan].limits;
  
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
 * Cancela una suscripción
 */
function cancelSubscription(subscriptionId) {
  const subscription = getSubscription(subscriptionId);
  
  subscription.status = 'cancelled';
  subscription.cancelledAt = new Date().toISOString();
  subscription.autoRenew = false;
  
  return {
    success: true,
    subscription,
    message: 'Suscripción cancelada exitosamente',
  };
}

/**
 * Renueva una suscripción
 */
function renewSubscription(subscriptionId) {
  const subscription = getSubscription(subscriptionId);
  
  subscription.endDate = calculateEndDate(subscription.duration);
  subscription.status = 'active';
  
  return {
    success: true,
    subscription,
    message: 'Suscripción renovada exitosamente',
  };
}

// ==============================================================================
// ANALYTICS Y MÉTRICAS
// ==============================================================================

/**
 * Registra uso de API
 */
function recordApiUsage(tenantId, endpoint, metadata = {}) {
  const tenant = getTenant(tenantId);
  
  // Verificar límite
  if (tenant.usage.apiCalls >= tenant.settings.limits.apiCalls) {
    throw new Error('Límite de API calls excedido');
  }
  
  // Registrar uso
  tenant.usage.apiCalls++;
  
  const usageKey = `${tenantId}_${new Date().toISOString().split('T')[0]}`;
  const usage = usageRecords.get(usageKey) || {
    tenantId,
    date: new Date().toISOString().split('T')[0],
    apiCalls: 0,
    endpoints: {},
  };
  
  usage.apiCalls++;
  usage.endpoints[endpoint] = (usage.endpoints[endpoint] || 0) + 1;
  
  usageRecords.set(usageKey, usage);
  
  return {
    success: true,
    usage,
  };
}

/**
 * Obtiene métricas de un tenant
 */
function getTenantMetrics(tenantId) {
  const tenant = getTenant(tenantId);
  
  const tenantUsage = Array.from(usageRecords.values())
    .filter(u => u.tenantId === tenantId);
  
  return {
    tenantId,
    name: tenant.name,
    plan: tenant.plan,
    usage: tenant.usage,
    limits: tenant.settings.limits,
    usageHistory: tenantUsage,
  };
}

/**
 * Obtiene métricas globales de la plataforma
 */
function getPlatformMetrics() {
  const totalTenants = tenants.size;
  const totalUsers = users.size;
  const totalApiCalls = Array.from(tenants.values())
    .reduce((sum, t) => sum + t.usage.apiCalls, 0);
  
  const planDistribution = {};
  Array.from(tenants.values()).forEach(t => {
    planDistribution[t.plan] = (planDistribution[t.plan] || 0) + 1;
  });
  
  return {
    totalTenants,
    totalUsers,
    totalApiCalls,
    planDistribution,
    activeTenants: Array.from(tenants.values()).filter(t => t.status === 'active').length,
    timestamp: new Date().toISOString(),
  };
}

// ==============================================================================
// PERSONALIZACIÓN
// ==============================================================================

/**
 * Personaliza la experiencia de un tenant
 */
function customizeTenant(tenantId, customizations) {
  const tenant = getTenant(tenantId);
  
  tenant.settings.branding = {
    ...tenant.settings.branding,
    ...customizations,
  };
  
  return {
    success: true,
    tenant,
    message: 'Personalización aplicada exitosamente',
  };
}

/**
 * Obtiene la configuración de un tenant
 */
function getTenantConfig(tenantId) {
  const tenant = getTenant(tenantId);
  
  return {
    tenantId,
    name: tenant.name,
    plan: tenant.plan,
    settings: tenant.settings,
    usage: tenant.usage,
  };
}

// ==============================================================================
// FUNCIONES AUXILIARES
// ==============================================================================

function calculateEndDate(duration) {
  const date = new Date();
  
  switch (duration) {
    case 'monthly':
      date.setMonth(date.getMonth() + 1);
      break;
    case 'yearly':
      date.setFullYear(date.getFullYear() + 1);
      break;
    default:
      date.setMonth(date.getMonth() + 1);
  }
  
  return date.toISOString();
}

// ==============================================================================
// API ENDPOINTS
// ==============================================================================

/**
 * POST /api/saas/tenants
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
 * GET /api/saas/tenants
 * Lista todos los tenants
 */
export function listTenantsEndpoint(req, res) {
  const { status, plan, limit, offset } = req.query;
  
  res.json(listTenants({ status, plan, limit, offset }));
}

/**
 * GET /api/saas/tenants/:id
 * Obtiene un tenant específico
 */
export function getTenantEndpoint(req, res) {
  try {
    const tenant = getTenant(req.params.id);
    res.json(tenant);
  } catch (error) {
    res.status(404).json({ error: error.message });
  }
}

/**
 * PUT /api/saas/tenants/:id
 * Actualiza un tenant
 */
export function updateTenantEndpoint(req, res) {
  try {
    const result = updateTenant(req.params.id, req.body);
    res.json(result);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
}

/**
 * DELETE /api/saas/tenants/:id
 * Elimina un tenant
 */
export function deleteTenantEndpoint(req, res) {
  try {
    const result = deleteTenant(req.params.id);
    res.json(result);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
}

/**
 * POST /api/saas/users
 * Crea un usuario
 */
export async function createUserEndpoint(req, res) {
  try {
    const result = await createUser(req.body);
    res.json(result);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
}

/**
 * GET /api/saas/tenants/:id/users
 * Lista usuarios de un tenant
 */
export function listTenantUsersEndpoint(req, res) {
  try {
    const users = listTenantUsers(req.params.id);
    res.json({ users, total: users.length });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
}

/**
 * POST /api/saas/subscriptions
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
 * GET /api/saas/metrics
 * Métricas de la plataforma
 */
export function getPlatformMetricsEndpoint(req, res) {
  res.json(getPlatformMetrics());
}

/**
 * GET /api/saas/tenants/:id/metrics
 * Métricas de un tenant
 */
export function getTenantMetricsEndpoint(req, res) {
  try {
    const metrics = getTenantMetrics(req.params.id);
    res.json(metrics);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
}

/**
 * GET /api/saas/status
 * Estado de la plataforma SaaS
 */
export function getSaasStatus(req, res) {
  res.json({
    status: 'active',
    config: SAAS_CONFIG,
    metrics: getPlatformMetrics(),
    timestamp: new Date().toISOString(),
  });
}

// ==============================================================================
// EXPORTACIONES
// ==============================================================================

export {
  createTenant,
  getTenant,
  updateTenant,
  deleteTenant,
  listTenants,
  createUser,
  getUser,
  updateUser,
  deleteUser,
  listTenantUsers,
  createSubscription,
  getSubscription,
  cancelSubscription,
  renewSubscription,
  recordApiUsage,
  getTenantMetrics,
  getPlatformMetrics,
  customizeTenant,
  getTenantConfig,
  SAAS_CONFIG,
};

export default {
  createTenantEndpoint,
  listTenantsEndpoint,
  getTenantEndpoint,
  updateTenantEndpoint,
  deleteTenantEndpoint,
  createUserEndpoint,
  listTenantUsersEndpoint,
  createSubscriptionEndpoint,
  getPlatformMetricsEndpoint,
  getTenantMetricsEndpoint,
  getSaasStatus,
  createTenant,
  getTenant,
  updateTenant,
  deleteTenant,
  listTenants,
  createUser,
  getUser,
  updateUser,
  deleteUser,
  listTenantUsers,
  createSubscription,
  getSubscription,
  cancelSubscription,
  renewSubscription,
  recordApiUsage,
  getTenantMetrics,
  getPlatformMetrics,
  customizeTenant,
  getTenantConfig,
};
