/**
 * Personalización IA - aigestion.net
 * 
 * Sistema de personalización con inteligencia artificial:
 * - Perfiles de usuario personalizados
 * - Adaptación de contenido
 * - Recomendaciones personalizadas
 * - Aprendizaje de preferencias
 * - Integración con IA
 * 
 * 100% gratuito con APIs open source
 */

import aiRouter from './ai_router.js';

// ==============================================================================
// CONFIGURACIÓN
// ==============================================================================

const PERSONALIZATION_CONFIG = {
  name: 'aig Personalization',
  version: '1.0.0',
  maxProfiles: 1000,
  learningRate: 0.1,
  adaptationSpeed: 'medium', // 'slow', 'medium', 'fast'
  categories: ['content', 'ui', 'notifications', 'recommendations'],
};

// ==============================================================================
// BASE DE DATOS DE PERFILES
// ==============================================================================

const userProfiles = new Map();
const preferences = new Map();
const interactions = new Map();

// ==============================================================================
// GESTIÓN DE PERFILES
// ==============================================================================

/**
 * Crea un perfil de usuario personalizado
 */
async function createUserProfile(userData) {
  const { userId, name, email, preferences: userPrefs = {} } = userData;
  
  console.log(`[Personalization] Creando perfil para: ${name}`);
  
  const profile = {
    id: `profile_${Date.now()}`,
    userId,
    name,
    email,
    preferences: userPrefs,
    segments: [],
    behavior: {
      totalInteractions: 0,
      lastActive: null,
      averageSessionTime: 0,
      topCategories: [],
    },
    recommendations: [],
    createdAt: new Date().toISOString(),
    updatedAt: new Date().toISOString(),
  };
  
  // Análisis inicial del usuario con IA
  const aiAnalysis = await analyzeUserProfile(profile);
  profile.aiAnalysis = aiAnalysis;
  
  userProfiles.set(userId, profile);
  
  return {
    success: true,
    profile,
    aiAnalysis,
    message: 'Perfil creado exitosamente',
  };
}

/**
 * Obtiene perfil de usuario
 */
function getUserProfile(userId) {
  const profile = userProfiles.get(userId);
  
  if (!profile) {
    throw new Error(`Perfil no encontrado: ${userId}`);
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
    message: 'Perfil actualizado exitosamente',
  };
}

/**
 * Lista todos los perfiles
 */
function listUserProfiles(options = {}) {
  const { limit = 50, offset = 0 } = options;
  
  const profiles = Array.from(userProfiles.values());
  
  return {
    profiles: profiles.slice(offset, offset + limit),
    total: profiles.length,
    limit,
    offset,
  };
}

// ==============================================================================
// PREFERENCIAS
// ==============================================================================

/**
 * Establece preferencias de usuario
 */
function setUserPreferences(userId, prefs) {
  console.log(`[Personalization] Estableciendo preferencias para: ${userId}`);
  
  const currentPrefs = preferences.get(userId) || {};
  
  preferences.set(userId, {
    ...currentPrefs,
    ...prefs,
    updatedAt: new Date().toISOString(),
  });
  
  // Actualizar perfil
  const profile = userProfiles.get(userId);
  if (profile) {
    profile.preferences = { ...profile.preferences, ...prefs };
    profile.updatedAt = new Date().toISOString();
  }
  
  return {
    success: true,
    preferences: preferences.get(userId),
  };
}

/**
 * Obtiene preferencias de usuario
 */
function getUserPreferences(userId) {
  const prefs = preferences.get(userId);
  
  if (!prefs) {
    return null;
  }
  
  return prefs;
}

/**
 * Aprende preferencias automáticamente
 */
async function learnPreferences(userId, interactionData) {
  console.log(`[Personalization] Aprendiendo preferencias de: ${userId}`);
  
  const currentPrefs = preferences.get(userId) || {};
  
  // Analizar interacción con IA
  const prompt = `Basado en la siguiente interacción del usuario, sugiere preferencias:

Interacción: ${JSON.stringify(interactionData)}
Preferencias actuales: ${JSON.stringify(currentPrefs)}

Proporciona nuevas preferencias en formato JSON.`;
  
  const result = await aiRouter.callAI(prompt, {
    systemPrompt: 'Eres un sistema de aprendizaje de preferencias. Proporciona preferencias personalizadas.',
    maxTokens: 200,
    temperature: 0.5,
  });
  
  const learnedPrefs = parsePreferences(result.response);
  
  // Aplicar nuevas preferencias
  preferences.set(userId, {
    ...currentPrefs,
    ...learnedPrefs,
    lastLearned: new Date().toISOString(),
  });
  
  return {
    success: true,
    learned: learnedPrefs,
    provider: result.provider,
  };
}

// ==============================================================================
// RECOMENDACIONES
// ==============================================================================

/**
 * Genera recomendaciones personalizadas
 */
async function generateRecommendations(userId, options = {}) {
  const { category = 'all', limit = 10, context = {} } = options;
  
  console.log(`[Personalization] Generando recomendaciones para: ${userId}`);
  
  const profile = getUserProfile(userId);
  const prefs = getUserPreferences(userId) || {};
  
  const prompt = `Genera recomendaciones personalizadas para el usuario:

Usuario: ${profile.name}
Preferencias: ${JSON.stringify(prefs)}
Comportamiento: ${JSON.stringify(profile.behavior)}
Categoría: ${category}
Contexto: ${JSON.stringify(context)}

Proporciona recomendaciones relevantes y personalizadas.`;
  
  const result = await aiRouter.callAI(prompt, {
    systemPrompt: 'Eres un sistema de recomendaciones personalizado. Proporciona sugerencias relevantes.',
    maxTokens: 400,
    temperature: 0.7,
  });
  
  // Guardar recomendaciones en el perfil
  profile.recommendations = [{
    category,
    items: result.response,
    generatedAt: new Date().toISOString(),
  }];
  
  return {
    success: true,
    userId,
    category,
    recommendations: result.response,
    provider: result.provider,
    timestamp: new Date().toISOString(),
  };
}

/**
 * Obtiene recomendaciones del usuario
 */
function getUserRecommendations(userId, options = {}) {
  const profile = getUserProfile(userId);
  
  const { category, limit = 10 } = options;
  
  let recommendations = profile.recommendations || [];
  
  if (category) {
    recommendations = recommendations.filter(r => r.category === category);
  }
  
  return {
    recommendations: recommendations.slice(0, limit),
    total: recommendations.length,
  };
}

// ==============================================================================
// ADAPTACIÓN DE CONTENIDO
// ==============================================================================

/**
 * Adapta contenido según perfil de usuario
 */
async function adaptContent(userId, content, options = {}) {
  const { contentType = 'text', context = {} } = options;
  
  console.log(`[Personalization] Adaptando contenido para: ${userId}`);
  
  const profile = getUserProfile(userId);
  const prefs = getUserPreferences(userId) || {};
  
  const prompt = `Adapta el siguiente contenido según el perfil del usuario:

Contenido original: ${content}
Tipo: ${contentType}
Preferencias del usuario: ${JSON.stringify(prefs)}
Perfil: ${JSON.stringify(profile.behavior)}
Contexto: ${JSON.stringify(context)}

Proporciona contenido adaptado y personalizado.`;
  
  const result = await aiRouter.callAI(prompt, {
    systemPrompt: 'Eres un sistema de adaptación de contenido. Personaliza el contenido según el usuario.',
    maxTokens: 500,
    temperature: 0.6,
  });
  
  return {
    success: true,
    original: content,
    adapted: result.response,
    userId,
    contentType,
    provider: result.provider,
    timestamp: new Date().toISOString(),
  };
}

/**
 * Personaliza UI según preferencias
 */
async function personalizeUI(userId, uiElements, options = {}) {
  console.log(`[Personalization] Personalizando UI para: ${userId}`);
  
  const prefs = getUserPreferences(userId) || {};
  
  const prompt = `Personaliza los siguientes elementos de UI según las preferencias del usuario:

Elementos: ${JSON.stringify(uiElements)}
Preferencias: ${JSON.stringify(prefs)}

Proporciona modificaciones de UI personalizadas.`;
  
  const result = await aiRouter.callAI(prompt, {
    systemPrompt: 'Eres un diseñador UI/UX que personaliza interfaces según preferencias.',
    maxTokens: 300,
    temperature: 0.5,
  });
  
  return {
    success: true,
    personalizedUI: result.response,
    provider: result.provider,
  };
}

// ==============================================================================
// ANÁLISIS DE COMPORTAMIENTO
// ==============================================================================

/**
 * Registra interacción del usuario
 */
async function trackInteraction(userId, interactionData) {
  const { type, data, timestamp = new Date().toISOString() } = interactionData;
  
  console.log(`[Personalization] Registrando interacción: ${type} para ${userId}`);
  
  const userInteractions = interactions.get(userId) || [];
  
  userInteractions.push({
    type,
    data,
    timestamp,
  });
  
  // Mantener solo últimas 1000 interacciones
  if (userInteractions.length > 1000) {
    userInteractions.shift();
  }
  
  interactions.set(userId, userInteractions);
  
  // Actualizar comportamiento del perfil
  const profile = userProfiles.get(userId);
  if (profile) {
    profile.behavior.totalInteractions++;
    profile.behavior.lastActive = timestamp;
  }
  
  // Aprender preferencias automáticamente
  if (userInteractions.length % 10 === 0) {
    await learnPreferences(userId, interactionData);
  }
  
  return {
    success: true,
    userId,
    type,
    timestamp,
  };
}

/**
 * Analiza comportamiento del usuario
 */
async function analyzeBehavior(userId, options = {}) {
  const { period = '7d' } = options;
  
  console.log(`[Personalization] Analizando comportamiento de: ${userId}`);
  
  const userInteractions = interactions.get(userId) || [];
  
  const prompt = `Analiza el siguiente comportamiento de usuario y proporciona insights:

Interacciones: ${JSON.stringify(userInteractions.slice(-50))}
Periodo: ${period}

Proporciona:
1. Patrones de comportamiento identificados
2. Preferencias inferidas
3. Áreas de mejora
4. Recomendaciones personalizadas`;
  
  const result = await aiRouter.callAI(prompt, {
    systemPrompt: 'Eres un analista de comportamiento de usuario. Proporciona insights accionables.',
    maxTokens: 500,
    temperature: 0.5,
  });
  
  return {
    success: true,
    userId,
    period,
    analysis: result.response,
    provider: result.provider,
    timestamp: new Date().toISOString(),
  };
}

/**
 * Predice próximas acciones del usuario
 */
async function predictNextActions(userId, options = {}) {
  console.log(`[Personalization] Prediciendo acciones para: ${userId}`);
  
  const userInteractions = interactions.get(userId) || [];
  const profile = userProfiles.get(userId);
  
  const prompt = `Predice las próximas acciones más probables del usuario:

Interacciones recientes: ${JSON.stringify(userInteractions.slice(-20))}
Perfil: ${JSON.stringify(profile)}

Proporciona las 5 acciones más probables con porcentaje de confianza.`;
  
  const result = await aiRouter.callAI(prompt, {
    systemPrompt: 'Eres un sistema de predicción de comportamiento. Proporciona predicciones precisas.',
    maxTokens: 300,
    temperature: 0.4,
  });
  
  return {
    success: true,
    predictions: result.response,
    provider: result.provider,
    timestamp: new Date().toISOString(),
  };
}

// ==============================================================================
// ANÁLISIS CON IA
// ==============================================================================

/**
 * Analiza perfil de usuario con IA
 */
async function analyzeUserProfile(profile) {
  const prompt = `Analiza el siguiente perfil de usuario y proporciona insights:

Perfil: ${JSON.stringify(profile)}

Proporciona:
1. Resumen del usuario
2. Fortalezas y debilidades
3. Recomendaciones personalizadas
4. Sugerencias de mejora`;
  
  const result = await aiRouter.callAI(prompt, {
    systemPrompt: 'Eres un analista de perfiles de usuario. Proporciona insights valiosos.',
    maxTokens: 300,
    temperature: 0.5,
  });
  
  return {
    analysis: result.response,
    provider: result.provider,
  };
}

/**
 * Parsea preferencias del resultado IA
 */
function parsePreferences(resultText) {
  try {
    const jsonMatch = resultText.match(/\{[\s\S]*\}/);
    if (jsonMatch) {
      return JSON.parse(jsonMatch[0]);
    }
  } catch (error) {
    console.error('[Personalization] Error parseando preferencias:', error.message);
  }
  
  return {};
}

// ==============================================================================
// MÉTRICAS
// ==============================================================================

/**
 * Obtiene métricas del sistema de personalización
 */
function getPersonalizationMetrics() {
  return {
    profiles: {
      total: userProfiles.size,
      active: Array.from(userProfiles.values()).filter(p => p.behavior.totalInteractions > 0).length,
    },
    preferences: {
      total: preferences.size,
      learned: Array.from(preferences.values()).filter(p => p.lastLearned).length,
    },
    interactions: {
      total: Array.from(interactions.values()).reduce((sum, arr) => sum + arr.length, 0),
    },
    config: PERSONALIZATION_CONFIG,
    timestamp: new Date().toISOString(),
  };
}

// ==============================================================================
// API ENDPOINTS
// ==============================================================================

/**
 * POST /api/personalization/profiles
 * Crea un perfil de usuario
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
 * GET /api/personalization/profiles/:userId
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
 * PUT /api/personalization/profiles/:userId
 * Actualiza perfil de usuario
 */
export function updateUserProfileEndpoint(req, res) {
  try {
    const result = updateUserProfile(req.params.userId, req.body);
    res.json(result);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
}

/**
 * POST /api/personalization/preferences
 * Establece preferencias
 */
export function setUserPreferencesEndpoint(req, res) {
  const { userId, preferences: prefs } = req.body;
  
  if (!userId || !prefs) {
    return res.status(400).json({ error: 'UserId and preferences required' });
  }
  
  const result = setUserPreferences(userId, prefs);
  res.json(result);
}

/**
 * GET /api/personalization/preferences/:userId
 * Obtiene preferencias
 */
export function getUserPreferencesEndpoint(req, res) {
  const prefs = getUserPreferences(req.params.userId);
  
  if (!prefs) {
    return res.status(404).json({ error: 'Preferences not found' });
  }
  
  res.json(prefs);
}

/**
 * POST /api/personalization/recommendations
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
 * POST /api/personalization/adapt
 * Adapta contenido
 */
export async function adaptContentEndpoint(req, res) {
  try {
    const result = await adaptContent(req.body.userId, req.body.content, req.body.options);
    res.json(result);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
}

/**
 * POST /api/personalization/track
 * Registra interacción
 */
export async function trackInteractionEndpoint(req, res) {
  try {
    const result = await trackInteraction(req.body.userId, req.body.interactionData);
    res.json(result);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
}

/**
 * POST /api/personalization/analyze
 * Analiza comportamiento
 */
export async function analyzeBehaviorEndpoint(req, res) {
  try {
    const result = await analyzeBehavior(req.body.userId, req.body.options);
    res.json(result);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
}

/**
 * GET /api/personalization/metrics
 * Métricas del sistema
 */
export function getPersonalizationMetricsEndpoint(req, res) {
  res.json(getPersonalizationMetrics());
}

/**
 * GET /api/personalization/status
 * Estado del sistema
 */
export function getPersonalizationStatus(req, res) {
  res.json({
    status: 'active',
    config: PERSONALIZATION_CONFIG,
    metrics: getPersonalizationMetrics(),
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
  setUserPreferences,
  getUserPreferences,
  learnPreferences,
  generateRecommendations,
  getUserRecommendations,
  adaptContent,
  personalizeUI,
  trackInteraction,
  analyzeBehavior,
  predictNextActions,
  getPersonalizationMetrics,
  PERSONALIZATION_CONFIG,
};

export default {
  createUserProfileEndpoint,
  getUserProfileEndpoint,
  updateUserProfileEndpoint,
  setUserPreferencesEndpoint,
  getUserPreferencesEndpoint,
  generateRecommendationsEndpoint,
  adaptContentEndpoint,
  trackInteractionEndpoint,
  analyzeBehaviorEndpoint,
  getPersonalizationMetricsEndpoint,
  getPersonalizationStatus,
  createUserProfile,
  getUserProfile,
  updateUserProfile,
  listUserProfiles,
  setUserPreferences,
  getUserPreferences,
  learnPreferences,
  generateRecommendations,
  getUserRecommendations,
  adaptContent,
  personalizeUI,
  trackInteraction,
  analyzeBehavior,
  predictNextActions,
  getPersonalizationMetrics,
};
