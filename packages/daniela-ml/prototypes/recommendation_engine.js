/**
 * Recommendation Engine - aigestion.net
 * 
 * Motor de recomendaciones con IA:
 * - Recomendaciones personalizadas
 * - Filtrado colaborativo
 * - Recomendaciones basadas en contenido
 * - Sugerencias en tiempo real
 * 
 * 100% gratuito con APIs open source
 */

import aiRouter from './ai_router.js';

// ==============================================================================
// CONFIGURACIÓN
// ==============================================================================

const RECOMMENDATION_CONFIG = {
  name: 'aig Recommendation Engine',
  version: '1.0.0',
  maxRecommendations: 20,
  minConfidence: 0.6,
  categories: ['product', 'service', 'content', 'action'],
  algorithms: ['collaborative', 'content-based', 'hybrid', 'trending'],
};

// ==============================================================================
// BASE DE DATOS
// ==============================================================================

const users = new Map();
const items = new Map();
const interactions = new Map();
const recommendations = new Map();

// ==============================================================================
// USUARIOS
// ==============================================================================

/**
 * Crea un perfil de usuario
 */
async function createUserProfile(userData) {
  const { userId, name, preferences = {} } = userData;
  
  console.log(`[Recommendation] Creando perfil: ${name}`);
  
  const profile = {
    id: `user_${Date.now()}`,
    userId,
    name,
    preferences,
    segments: [],
    behavior: {
      totalInteractions: 0,
      favoriteCategories: [],
      averageRating: 0,
    },
    createdAt: new Date().toISOString(),
  };
  
  // Análisis inicial del usuario con IA
  const aiProfile = await analyzeUserProfile(profile);
  profile.aiProfile = aiProfile;
  
  users.set(userId, profile);
  
  return {
    success: true,
    profile,
    aiProfile,
  };
}

/**
 * Obtiene perfil de usuario
 */
function getUserProfile(userId) {
  const profile = users.get(userId);
  
  if (!profile) {
    throw new Error(`Usuario no encontrado: ${userId}`);
  }
  
  return profile;
}

/**
 * Actualiza perfil de usuario
 */
function updateUserProfile(userId, updates) {
  const profile = getUserProfile(userId);
  
  Object.assign(profile, updates, { updatedAt: new Date().toISOString() });
  
  return {
    success: true,
    profile,
  };
}

/**
 * Lista todos los usuarios
 */
function listUsers(options = {}) {
  const { limit = 50, offset = 0 } = options;
  
  const allUsers = Array.from(users.values());
  
  return {
    users: allUsers.slice(offset, offset + limit),
    total: allUsers.length,
    limit,
    offset,
  };
}

/**
 * Lista perfiles de usuario
 */
function listUserProfiles(options = {}) {
  const { limit = 50, offset = 0 } = options;
  
  const allProfiles = Array.from(users.values());
  
  return {
    profiles: allProfiles.slice(offset, offset + limit),
    total: allProfiles.length,
    limit,
    offset,
  };
}

// ==============================================================================
// ÍTEMS
// ==============================================================================

/**
 * Registra un ítem para recomendar
 */
async function registerItem(itemData) {
  const { name, category, description, tags = [], metadata = {} } = itemData;
  
  console.log(`[Recommendation] Registrando ítem: ${name}`);
  
  const item = {
    id: `item_${Date.now()}`,
    name,
    category,
    description,
    tags,
    metadata,
    stats: {
      totalViews: 0,
      totalClicks: 0,
      totalConversions: 0,
      averageRating: 0,
    },
    createdAt: new Date().toISOString(),
  };
  
  // Análisis del ítem con IA
  const aiAnalysis = await analyzeItem(item);
  item.aiAnalysis = aiAnalysis;
  
  items.set(item.id, item);
  
  return {
    success: true,
    item,
    aiAnalysis,
  };
}

/**
 * Obtiene un ítem por ID
 */
function getItem(itemId) {
  const item = items.get(itemId);
  
  if (!item) {
    throw new Error(`Ítem no encontrado: ${itemId}`);
  }
  
  return item;
}

/**
 * Lista ítems
 */
function listItems(options = {}) {
  const { category, limit = 50, offset = 0 } = options;
  
  let result = Array.from(items.values());
  
  if (category) {
    result = result.filter(i => i.category === category);
  }
  
  return {
    items: result.slice(offset, offset + limit),
    total: result.length,
    limit,
    offset,
  };
}

// ==============================================================================
// INTERACCIONES
// ==============================================================================

/**
 * Registra interacción usuario-ítem
 */
async function recordInteraction(userId, itemId, interactionData) {
  const { type, value = 1, metadata = {} } = interactionData;
  
  console.log(`[Recommendation] Registrando interacción: ${userId} → ${itemId} (${type})`);
  
  const interaction = {
    id: `int_${Date.now()}`,
    userId,
    itemId,
    type,
    value,
    metadata,
    timestamp: new Date().toISOString(),
  };
  
  // Guardar interacción
  if (!interactions.has(userId)) {
    interactions.set(userId, []);
  }
  interactions.get(userId).push(interaction);
  
  // Actualizar estadísticas
  const profile = users.get(userId);
  if (profile) {
    profile.behavior.totalInteractions++;
  }
  
  const item = items.get(itemId);
  if (item) {
    if (type === 'view') item.stats.totalViews++;
    if (type === 'click') item.stats.totalClicks++;
    if (type === 'convert') item.stats.totalConversions++;
  }
  
  // Actualizar recomendaciones
  await updateRecommendations(userId);
  
  return {
    success: true,
    interaction,
  };
}

/**
 * Obtiene interacciones de un usuario
 */
function getUserInteractions(userId, options = {}) {
  const { limit = 100, offset = 0 } = options;
  
  const userInteractions = interactions.get(userId) || [];
  
  return {
    interactions: userInteractions.slice(offset, offset + limit),
    total: userInteractions.length,
    limit,
    offset,
  };
}

/**
 * Obtiene interacciones de un ítem
 */
function getItemInteractions(itemId, options = {}) {
  const { limit = 100, offset = 0 } = options;
  
  const allInteractions = Array.from(interactions.values())
    .flat()
    .filter(i => i.itemId === itemId);
  
  return {
    interactions: allInteractions.slice(offset, offset + limit),
    total: allInteractions.length,
    limit,
    offset,
  };
}

// ==============================================================================
// RECOMENDACIONES
// ==============================================================================

/**
 * Genera recomendaciones personalizadas
 */
async function generateRecommendations(userId, options = {}) {
  const { limit = 10, category = 'all', algorithm = 'hybrid' } = options;
  
  console.log(`[Recommendation] Generando recomendaciones para ${userId} (${algorithm})`);
  
  const profile = getUserProfile(userId);
  const userInteractions = interactions.get(userId) || [];
  
  // Obtener ítems candidatos
  let candidates = Array.from(items.values());
  
  if (category !== 'all') {
    candidates = candidates.filter(i => i.category === category);
  }
  
  // Calcular puntuaciones según algoritmo
  const scoredItems = [];
  
  for (const item of candidates) {
    let score = 0;
    
    switch (algorithm) {
      case 'collaborative':
        score = calculateCollaborativeScore(userId, item.id);
        break;
      case 'content-based':
        score = calculateContentBasedScore(profile, item);
        break;
      case 'hybrid':
        score = (calculateCollaborativeScore(userId, item.id) + 
                 calculateContentBasedScore(profile, item)) / 2;
        break;
      case 'trending':
        score = calculateTrendingScore(item);
        break;
    }
    
    scoredItems.push({ item, score });
  }
  
  // Ordenar y filtrar
  scoredItems.sort((a, b) => b.score - a.score);
  
  const topRecommendations = scoredItems
    .filter(s => s.score >= RECOMMENDATION_CONFIG.minConfidence)
    .slice(0, limit);
  
  // Enriquecer con IA
  const prompt = `Basado en las siguientes recomendaciones, proporciona una explicación personalizada:

Usuario: ${profile.name}
Preferencias: ${JSON.stringify(profile.preferences)}
Recomendaciones: ${JSON.stringify(topRecommendations.map(r => ({
  nombre: r.item.name,
  categoria: r.item.category,
  puntuacion: r.score.toFixed(2),
})))}

Explica por qué se recomiendan estos ítems.`;
  
  const result = await aiRouter.callAI(prompt, {
    systemPrompt: 'Eres un experto en recomendaciones personalizadas.',
    maxTokens: 200,
    temperature: 0.6,
  });
  
  const recommendation = {
    id: `rec_${Date.now()}`,
    userId,
    items: topRecommendations.map(r => ({
      id: r.item.id,
      name: r.item.name,
      category: r.item.category,
      score: r.score,
    })),
    explanation: result.response,
    algorithm,
    confidence: topRecommendations.length > 0 ? topRecommendations[0].score : 0,
    provider: result.provider,
    timestamp: new Date().toISOString(),
  };
  
  recommendations.set(recommendation.id, recommendation);
  
  return {
    success: true,
    recommendation,
  };
}

/**
 * Calcula puntuación de filtrado colaborativo
 */
function calculateCollaborativeScore(userId, itemId) {
  // Implementación simplificada
  const userInteractions = interactions.get(userId) || [];
  const itemInteractions = Array.from(interactions.values())
    .flat()
    .filter(i => i.itemId === itemId);
  
  if (itemInteractions.length === 0) return 0;
  
  const avgValue = itemInteractions.reduce((sum, i) => sum + i.value, 0) / itemInteractions.length;
  return Math.min(avgValue / 5, 1);
}

/**
 * Calcula puntuación basada en contenido
 */
function calculateContentBasedScore(profile, item) {
  const userPrefs = profile.preferences || {};
  const itemTags = item.tags || [];
  
  let score = 0;
  let matches = 0;
  
  for (const [prefKey, prefValue] of Object.entries(userPrefs)) {
    if (item.category === prefValue) {
      score += 0.5;
      matches++;
    }
    
    if (itemTags.includes(prefValue)) {
      score += 0.3;
      matches++;
    }
  }
  
  return matches > 0 ? Math.min(score, 1) : 0;
}

/**
 * Calcula puntuación de tendencia
 */
function calculateTrendingScore(item) {
  const views = item.stats?.totalViews || 0;
  const clicks = item.stats?.totalClicks || 0;
  const conversions = item.stats?.totalConversions || 0;
  
  const clickRate = views > 0 ? clicks / views : 0;
  const conversionRate = clicks > 0 ? conversions / clicks : 0;
  
  return (clickRate * 0.4 + conversionRate * 0.6);
}

/**
 * Actualiza recomendaciones de un usuario
 */
async function updateRecommendations(userId) {
  return await generateRecommendations(userId);
}

/**
 * Obtiene recomendaciones de un usuario
 */
function getUserRecommendations(userId, options = {}) {
  const { limit = 10 } = options;
  
  const userRecs = Array.from(recommendations.values())
    .filter(r => r.userId === userId);
  
  return {
    recommendations: userRecs.slice(0, limit),
    total: userRecs.length,
  };
}

/**
 * Lista todas las recomendaciones
 */
function listAllRecommendations(options = {}) {
  const { limit = 50, offset = 0 } = options;
  
  const allRecs = Array.from(recommendations.values());
  
  return {
    recommendations: allRecs.slice(offset, offset + limit),
    total: allRecs.length,
    limit,
    offset,
  };
}

// ==============================================================================
// ANÁLISIS CON IA
// ==============================================================================

/**
 * Analiza perfil de usuario con IA
 */
async function analyzeUserProfile(profile) {
  const prompt = `Analiza el siguiente perfil de usuario:

Nombre: ${profile.name}
Preferencias: ${JSON.stringify(profile.preferences)}
Comportamiento: ${JSON.stringify(profile.behavior)}

Proporciona:
1. Segmento de usuario
2. Intereses principales
3. Patrones de comportamiento
4. Recomendaciones de personalización`;
  
  const result = await aiRouter.callAI(prompt, {
    systemPrompt: 'Eres un analista de usuario experto en personalización.',
    maxTokens: 300,
    temperature: 0.5,
  });
  
  return {
    analysis: result.response,
    provider: result.provider,
  };
}

/**
 * Analiza ítem con IA
 */
async function analyzeItem(item) {
  const prompt = `Analiza el siguiente ítem para recomendaciones:

Nombre: ${item.name}
Categoría: ${item.category}
Descripción: ${item.description}
Tags: ${item.tags.join(', ')}

Proporciona:
1. Clasificación de contenido
2. Audiencia objetivo
3. Potencial de recomendación
4. Optimizaciones sugeridas`;
  
  const result = await aiRouter.callAI(prompt, {
    systemPrompt: 'Eres un analista de contenido experto en recomendaciones.',
    maxTokens: 200,
    temperature: 0.4,
  });
  
  return {
    analysis: result.response,
    provider: result.provider,
  };
}

// ==============================================================================
// MÉTRICAS
// ==============================================================================

/**
 * Obtiene métricas del motor de recomendaciones
 */
function getRecommendationMetrics() {
  const totalUsers = users.size;
  const totalItems = items.size;
  const totalInteractions = Array.from(interactions.values())
    .reduce((sum, arr) => sum + arr.length, 0);
  const totalRecommendations = recommendations.size;
  
  return {
    users: {
      total: totalUsers,
      active: Array.from(users.values()).filter(u => u.behavior.totalInteractions > 0).length,
    },
    items: {
      total: totalItems,
      byCategory: getItemCategoryDistribution(),
    },
    interactions: {
      total: totalInteractions,
      averagePerUser: totalUsers > 0 ? totalInteractions / totalUsers : 0,
    },
    recommendations: {
      total: totalRecommendations,
      averageConfidence: getAverageConfidence(),
    },
    config: RECOMMENDATION_CONFIG,
    timestamp: new Date().toISOString(),
  };
}

/**
 * Obtiene distribución de categorías
 */
function getItemCategoryDistribution() {
  const distribution = {};
  
  items.forEach(item => {
    const cat = item.category || 'uncategorized';
    distribution[cat] = (distribution[cat] || 0) + 1;
  });
  
  return distribution;
}

/**
 * Obtiene confianza promedio
 */
function getAverageConfidence() {
  if (recommendations.size === 0) return 0;
  
  const total = Array.from(recommendations.values())
    .reduce((sum, r) => sum + r.confidence, 0);
  
  return (total / recommendations.size).toFixed(2);
}

// ==============================================================================
// API ENDPOINTS
// ==============================================================================

/**
 * POST /api/recommendations/users
 * Crea perfil de usuario
 */
export async function createUserProfileEndpoint(req, res) {
  try {
    const result = await createUserProfile(req.body);
    res.json(result);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
}

/**
 * GET /api/recommendations/users/:userId
 * Obtiene perfil de usuario
 */
export function getUserProfileEndpoint(req, res) {
  try {
    const profile = getUserProfile(req.params.userId);
    res.json(profile);
  } catch (error) {
    res.status(404).json({ error: error.message });
  }
}

/**
 * POST /api/recommendations/items
 * Registra un ítem
 */
export async function registerItemEndpoint(req, res) {
  try {
    const result = await registerItem(req.body);
    res.json(result);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
}

/**
 * POST /api/recommendations/interactions
 * Registra interacción
 */
export async function recordInteractionEndpoint(req, res) {
  try {
    const result = await recordInteraction(req.body.userId, req.body.itemId, req.body.interactionData);
    res.json(result);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
}

/**
 * POST /api/recommendations/generate
 * Genera recomendaciones
 */
export async function generateRecommendationsEndpoint(req, res) {
  try {
    const result = await generateRecommendations(req.body.userId, req.body.options);
    res.json(result);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
}

/**
 * GET /api/recommendations/metrics
 * Métricas del sistema
 */
export function getRecommendationMetricsEndpoint(req, res) {
  res.json(getRecommendationMetrics());
}

/**
 * GET /api/recommendations/status
 * Estado del motor de recomendaciones
 */
export function getRecommendationStatus(req, res) {
  res.json({
    status: 'active',
    config: RECOMMENDATION_CONFIG,
    metrics: getRecommendationMetrics(),
    timestamp: new Date().toISOString(),
  });
}

// ==============================================================================
// EXPORTACIONES
// ==============================================================================

export {
  createUserProfile,
  getUserProfile,
  updateUserProfile,
  listUserProfiles,
  registerItem,
  getItem,
  listItems,
  recordInteraction,
  getUserInteractions,
  getItemInteractions,
  generateRecommendations,
  getUserRecommendations,
  listAllRecommendations,
  getRecommendationMetrics,
  RECOMMENDATION_CONFIG,
};

export default {
  createUserProfileEndpoint,
  getUserProfileEndpoint,
  registerItemEndpoint,
  recordInteractionEndpoint,
  generateRecommendationsEndpoint,
  getRecommendationMetricsEndpoint,
  getRecommendationStatus,
  createUserProfile,
  getUserProfile,
  updateUserProfile,
  listUserProfiles,
  registerItem,
  getItem,
  listItems,
  recordInteraction,
  getUserInteractions,
  getItemInteractions,
  generateRecommendations,
  getUserRecommendations,
  listAllRecommendations,
  getRecommendationMetrics,
};
