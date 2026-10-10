/**
 * Gamification - aigestion.net
 * 
 * Sistema de gamificación con IA:
 * - Puntos y recompensas
 * - Logros y badges
 * - Leaderboards
 * - Desafíos y misiones
 * - Personalización con IA
 * 
 * 100% gratuito con APIs open source
 */

import aiRouter from './ai_router.js';

// ==============================================================================
// CONFIGURACIÓN
// ==============================================================================

const GAMIFICATION_CONFIG = {
  name: 'aig Gamification',
  version: '1.0.0',
  maxLevels: 100,
  pointsPerLevel: 1000,
  categories: ['engagement', 'learning', 'productivity', 'social', 'creativity'],
  rewardTypes: ['points', 'badges', 'unlocks', 'discounts', 'access'],
};

// ==============================================================================
// BASE DE DATOS
// ==============================================================================

const users = new Map();
const achievements = new Map();
const leaderboards = new Map();
const challenges = new Map();
const rewards = new Map();

// ==============================================================================
// SISTEMA DE PUNTOS
// ==============================================================================

/**
 * Otorga puntos a un usuario
 */
async function awardPoints(userId, points, reason, options = {}) {
  const { category = 'engagement', metadata = {} } = options;
  
  console.log(`[Gamification] Otorgando ${points} puntos a ${userId}: ${reason}`);
  
  let user = users.get(userId);
  
  if (!user) {
    user = {
      id: userId,
      totalPoints: 0,
      level: 1,
      pointsToNextLevel: GAMIFICATION_CONFIG.pointsPerLevel,
      achievements: [],
      badges: [],
      streak: 0,
      lastActivity: null,
      history: [],
    };
    users.set(userId, user);
  }
  
  // Sumar puntos
  user.totalPoints += points;
  
  // Verificar subida de nivel
  while (user.totalPoints >= user.pointsToNextLevel && user.level < GAMIFICATION_CONFIG.maxLevels) {
    user.level++;
    user.pointsToNextLevel = user.level * GAMIFICATION_CONFIG.pointsPerLevel;
    console.log(`[Gamification] 🎉 ${userId} subió al nivel ${user.level}`);
  }
  
  // Registrar actividad
  user.history.push({
    type: 'points',
    points,
    reason,
    category,
    metadata,
    timestamp: new Date().toISOString(),
  });
  
  // Mantener solo últimas 1000 entradas
  if (user.history.length > 1000) {
    user.history = user.history.slice(-1000);
  }
  
  user.lastActivity = new Date().toISOString();
  
  // Verificar logros desbloqueados
  await checkAchievements(userId);
  
  return {
    success: true,
    userId,
    points,
    totalPoints: user.totalPoints,
    level: user.level,
    reason,
  };
}

/**
 * Obtiene puntos de un usuario
 */
function getUserPoints(userId) {
  const user = users.get(userId);
  
  if (!user) {
    return null;
  }
  
  return {
    userId,
    totalPoints: user.totalPoints,
    level: user.level,
    pointsToNextLevel: user.pointsToNextLevel,
    progress: (user.totalPoints % GAMIFICATION_CONFIG.pointsPerLevel) / GAMIFICATION_CONFIG.pointsPerLevel,
  };
}

// ==============================================================================
// LOGROS Y BADGES
// ==============================================================================

/**
 * Crea un logro
 */
async function createAchievement(achievementData) {
  const { name, description, icon, points, condition, category = 'engagement' } = achievementData;
  
  console.log(`[Gamification] Creando logro: ${name}`);
  
  const achievement = {
    id: `ach_${Date.now()}`,
    name,
    description,
    icon,
    points,
    condition,
    category,
    createdAt: new Date().toISOString(),
    unlockedBy: [],
  };
  
  achievements.set(achievement.id, achievement);
  
  return {
    success: true,
    achievement,
  };
}

/**
 * Desbloquea un logro para un usuario
 */
async function unlockAchievement(userId, achievementId) {
  const user = users.get(userId);
  const achievement = achievements.get(achievementId);
  
  if (!user) {
    throw new Error(`Usuario no encontrado: ${userId}`);
  }
  
  if (!achievement) {
    throw new Error(`Logro no encontrado: ${achievementId}`);
  }
  
  if (user.achievements.includes(achievementId)) {
    return {
      success: false,
      message: 'Logro ya desbloqueado',
    };
  }
  
  console.log(`[Gamification] 🏆 ${userId} desbloqueó: ${achievement.name}`);
  
  user.achievements.push(achievementId);
  achievement.unlockedBy.push(userId);
  
  // Otorgar puntos del logro
  await awardPoints(userId, achievement.points, `Logro: ${achievement.name}`, { category: achievement.category });
  
  return {
    success: true,
    achievement,
    message: `Logro desbloqueado: ${achievement.name}`,
  };
}

/**
 * Verifica logros desbloqueados
 */
async function checkAchievements(userId) {
  const user = users.get(userId);
  
  if (!user) return;
  
  for (const [id, achievement] of achievements.entries()) {
    if (user.achievements.includes(id)) continue;
    
    // Evaluar condición del logro
    const unlocked = await evaluateAchievementCondition(user, achievement);
    
    if (unlocked) {
      await unlockAchievement(userId, id);
    }
  }
}

/**
 * Evalúa condición de logro
 */
async function evaluateAchievementCondition(user, achievement) {
  // En producción, evaluar condición real
  // Por ahora, usar lógica simple basada en puntos
  const condition = achievement.condition;
  
  if (condition.type === 'points') {
    return user.totalPoints >= condition.value;
  }
  
  if (condition.type === 'level') {
    return user.level >= condition.value;
  }
  
  if (condition.type === 'streak') {
    return user.streak >= condition.value;
  }
  
  return false;
}

/**
 * Obtiene logros de un usuario
 */
function getUserAchievements(userId) {
  const user = users.get(userId);
  
  if (!user) {
    return null;
  }
  
  return {
    achievements: user.achievements.map(id => achievements.get(id)).filter(Boolean),
    total: user.achievements.length,
  };
}

/**
 * Lista todos los logros
 */
function listAchievements(options = {}) {
  const { category, limit = 50, offset = 0 } = options;
  
  let result = Array.from(achievements.values());
  
  if (category) {
    result = result.filter(a => a.category === category);
  }
  
  return {
    achievements: result.slice(offset, offset + limit),
    total: result.length,
    limit,
    offset,
  };
}

// ==============================================================================
// LEADERBOARDS
// ==============================================================================

/**
 * Obtiene leaderboard
 */
function getLeaderboard(options = {}) {
  const { category = 'all', period = 'all', limit = 100 } = options;
  
  let usersArray = Array.from(users.values());
  
  // Filtrar por período
  if (period !== 'all') {
    const now = Date.now();
    const periods = {
      'daily': 86400000,
      'weekly': 604800000,
      'monthly': 2592000000,
    };
    
    const cutoff = now - (periods[period] || 0);
    usersArray = usersArray.filter(u => new Date(u.lastActivity).getTime() > cutoff);
  }
  
  // Ordenar por puntos
  usersArray.sort((a, b) => b.totalPoints - a.totalPoints);
  
  // Generar leaderboard
  const leaderboard = usersArray.slice(0, limit).map((user, index) => ({
    rank: index + 1,
    userId: user.id,
    name: user.name || user.id,
    points: user.totalPoints,
    level: user.level,
    achievements: user.achievements.length,
    badges: user.badges.length,
  }));
  
  return {
    leaderboard,
    total: usersArray.length,
    category,
    period,
    generatedAt: new Date().toISOString(),
  };
}

/**
 * Obtiene posición de un usuario en el leaderboard
 */
function getUserRank(userId) {
  const usersArray = Array.from(users.values())
    .sort((a, b) => b.totalPoints - a.totalPoints);
  
  const index = usersArray.findIndex(u => u.id === userId);
  
  if (index === -1) {
    return null;
  }
  
  return {
    rank: index + 1,
    totalUsers: usersArray.length,
    percentile: ((usersArray.length - index) / usersArray.length * 100).toFixed(1),
  };
}

// ==============================================================================
// DESAFÍOS Y MISIONES
// ==============================================================================

/**
 * Crea un desafío
 */
async function createChallenge(challengeData) {
  const { name, description, type, goal, reward, duration, category = 'engagement' } = challengeData;
  
  console.log(`[Gamification] Creando desafío: ${name}`);
  
  const challenge = {
    id: `challenge_${Date.now()}`,
    name,
    description,
    type,
    goal,
    reward,
    duration,
    category,
    status: 'active',
    participants: [],
    createdAt: new Date().toISOString(),
    endsAt: new Date(Date.now() + duration * 86400000).toISOString(),
  };
  
  challenges.set(challenge.id, challenge);
  
  return {
    success: true,
    challenge,
  };
}

/**
 * Inscribe usuario en desafío
 */
async function joinChallenge(userId, challengeId) {
  const user = users.get(userId);
  const challenge = challenges.get(challengeId);
  
  if (!user) {
    throw new Error(`Usuario no encontrado: ${userId}`);
  }
  
  if (!challenge) {
    throw new Error(`Desafío no encontrado: ${challengeId}`);
  }
  
  if (challenge.participants.includes(userId)) {
    return {
      success: false,
      message: 'Ya participas en este desafío',
    };
  }
  
  challenge.participants.push(userId);
  
  return {
    success: true,
    challenge,
    message: 'Te uniste al desafío exitosamente',
  };
}

/**
 * Actualiza progreso en desafío
 */
async function updateChallengeProgress(userId, challengeId, progress) {
  const user = users.get(userId);
  const challenge = challenges.get(challengeId);
  
  if (!user || !challenge) {
    throw new Error('Usuario o desafío no encontrado');
  }
  
  // Verificar si completó el desafío
  if (progress >= challenge.goal) {
    await awardPoints(userId, challenge.reward, `Desafío completado: ${challenge.name}`, { category: challenge.category });
    
    return {
      success: true,
      completed: true,
      message: `🎉 Desafío completado: ${challenge.name}`,
    };
  }
  
  return {
    success: true,
    completed: false,
    progress,
    goal: challenge.goal,
    remaining: challenge.goal - progress,
  };
}

/**
 * Lista desafíos activos
 */
function listChallenges(options = {}) {
  const { category, status = 'active', limit = 50, offset = 0 } = options;
  
  let result = Array.from(challenges.values());
  
  if (category) {
    result = result.filter(c => c.category === category);
  }
  
  if (status) {
    result = result.filter(c => c.status === status);
  }
  
  return {
    challenges: result.slice(offset, offset + limit),
    total: result.length,
    limit,
    offset,
  };
}

// ==============================================================================
// RECOMPENSAS
// ==============================================================================

/**
 * Crea una recompensa
 */
async function createReward(rewardData) {
  const { name, description, type, cost, availability = 'unlimited' } = rewardData;
  
  console.log(`[Gamification] Creando recompensa: ${name}`);
  
  const reward = {
    id: `reward_${Date.now()}`,
    name,
    description,
    type,
    cost,
    availability,
    redeemedCount: 0,
    createdAt: new Date().toISOString(),
  };
  
  rewards.set(reward.id, reward);
  
  return {
    success: true,
    reward,
  };
}

/**
 * Canjea una recompensa
 */
async function redeemReward(userId, rewardId) {
  const user = users.get(userId);
  const reward = rewards.get(rewardId);
  
  if (!user) {
    throw new Error(`Usuario no encontrado: ${userId}`);
  }
  
  if (!reward) {
    throw new Error(`Recompensa no encontrada: ${rewardId}`);
  }
  
  if (user.totalPoints < reward.cost) {
    throw new Error(`Puntos insuficientes: ${user.totalPoints}/${reward.cost}`);
  }
  
  // Descontar puntos
  user.totalPoints -= reward.cost;
  reward.redeemedCount++;
  
  console.log(`[Gamification] 🎁 ${userId} canjeó: ${reward.name}`);
  
  return {
    success: true,
    reward,
    remainingPoints: user.totalPoints,
    message: `Recompensa canjeada: ${reward.name}`,
  };
}

/**
 * Lista recompensas disponibles
 */
function listRewards(options = {}) {
  const { type, limit = 50, offset = 0 } = options;
  
  let result = Array.from(rewards.values());
  
  if (type) {
    result = result.filter(r => r.type === type);
  }
  
  return {
    rewards: result.slice(offset, offset + limit),
    total: result.length,
    limit,
    offset,
  };
}

// ==============================================================================
// PERSONALIZACIÓN CON IA
// ==============================================================================

/**
 * Genera desafíos personalizados con IA
 */
async function generatePersonalizedChallenge(userId, options = {}) {
  const { difficulty = 'medium', category = 'engagement' } = options;
  
  const user = users.get(userId);
  
  if (!user) {
    throw new Error(`Usuario no encontrado: ${userId}`);
  }
  
  console.log(`[Gamification] Generando desafío personalizado para ${userId}`);
  
  const prompt = `Genera un desafío de gamificación personalizado para el usuario:

Usuario: ${user.name || userId}
Nivel: ${user.level}
Puntos: ${user.totalPoints}
Categoría preferida: ${category}
Dificultad: ${difficulty}

Proporciona:
1. Nombre del desafío
2. Descripción
3. Meta específica
4. Recompensa en puntos
5. Duración en días`;
  
  const result = await aiRouter.callAI(prompt, {
    systemPrompt: 'Eres un diseñador de gamificación. Crea desafíos atractivos y motivadores.',
    maxTokens: 300,
    temperature: 0.7,
  });
  
  return {
    success: true,
    challenge: result.response,
    provider: result.provider,
    timestamp: new Date().toISOString(),
  };
}

/**
 * Analiza engagement del usuario
 */
async function analyzeEngagement(userId, options = {}) {
  const { period = '30d' } = options;
  
  const user = users.get(userId);
  
  if (!user) {
    throw new Error(`Usuario no encontrado: ${userId}`);
  }
  
  console.log(`[Gamification] Analizando engagement de ${userId}`);
  
  const prompt = `Analiza el engagement del siguiente usuario:

Usuario: ${user.name || userId}
Puntos totales: ${user.totalPoints}
Nivel: ${user.level}
Logros: ${user.achievements.length}
Racha: ${user.streak} días
Última actividad: ${user.lastActivity}
Historial reciente: ${JSON.stringify(user.history.slice(-10))}

Proporciona:
1. Nivel de engagement (bajo, medio, alto)
2. Fortalezas
3. Áreas de mejora
4. Recomendaciones personalizadas`;
  
  const result = await aiRouter.callAI(prompt, {
    systemPrompt: 'Eres un analista de engagement. Proporciona insights accionables.',
    maxTokens: 400,
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

// ==============================================================================
// MÉTRICAS
// ==============================================================================

/**
 * Obtiene métricas del sistema de gamificación
 */
function getGamificationMetrics() {
  const totalUsers = users.size;
  const totalPoints = Array.from(users.values())
    .reduce((sum, u) => sum + u.totalPoints, 0);
  const totalAchievements = achievements.size;
  const totalChallenges = challenges.size;
  const totalRewards = rewards.size;
  
  return {
    users: {
      total: totalUsers,
      active: Array.from(users.values()).filter(u => u.lastActivity).length,
    },
    points: {
      total: totalPoints,
      average: totalUsers > 0 ? totalPoints / totalUsers : 0,
    },
    achievements: {
      total: totalAchievements,
      unlocked: Array.from(achievements.values())
        .reduce((sum, a) => sum + a.unlockedBy.length, 0),
    },
    challenges: {
      total: totalChallenges,
      active: Array.from(challenges.values()).filter(c => c.status === 'active').length,
    },
    rewards: {
      total: totalRewards,
      redeemed: Array.from(rewards.values())
        .reduce((sum, r) => sum + r.redeemedCount, 0),
    },
    config: GAMIFICATION_CONFIG,
    timestamp: new Date().toISOString(),
  };
}

// ==============================================================================
// API ENDPOINTS
// ==============================================================================

/**
 * POST /api/gamification/points
 * Otorga puntos a un usuario
 */
export async function awardPointsEndpoint(req, res) {
  try {
    const result = await awardPoints(req.body.userId, req.body.points, req.body.reason, req.body.options);
    res.json(result);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
}

/**
 * GET /api/gamification/users/:userId/points
 * Obtiene puntos de un usuario
 */
export function getUserPointsEndpoint(req, res) {
  const points = getUserPoints(req.params.userId);
  
  if (!points) {
    return res.status(404).json({ error: 'User not found' });
  }
  
  res.json(points);
}

/**
 * POST /api/gamification/achievements
 * Crea un logro
 */
export async function createAchievementEndpoint(req, res) {
  try {
    const result = await createAchievement(req.body);
    res.json(result);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
}

/**
 * POST /api/gamification/achievements/:id/unlock
 * Desbloquea un logro
 */
export async function unlockAchievementEndpoint(req, res) {
  try {
    const result = await unlockAchievement(req.body.userId, req.params.id);
    res.json(result);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
}

/**
 * GET /api/gamification/achievements
 * Lista todos los logros
 */
export function listAchievementsEndpoint(req, res) {
  const { category, limit, offset } = req.query;
  
  res.json(listAchievements({ category, limit, offset }));
}

/**
 * GET /api/gamification/leaderboard
 * Obtiene leaderboard
 */
export function getLeaderboardEndpoint(req, res) {
  const { category, period, limit } = req.query;
  
  res.json(getLeaderboard({ category, period, limit }));
}

/**
 * GET /api/gamification/users/:userId/rank
 * Obtiene posición de un usuario
 */
export function getUserRankEndpoint(req, res) {
  const rank = getUserRank(req.params.userId);
  
  if (!rank) {
    return res.status(404).json({ error: 'User not found' });
  }
  
  res.json(rank);
}

/**
 * POST /api/gamification/challenges
 * Crea un desafío
 */
export async function createChallengeEndpoint(req, res) {
  try {
    const result = await createChallenge(req.body);
    res.json(result);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
}

/**
 * POST /api/gamification/challenges/:id/join
 * Inscribe usuario en desafío
 */
export async function joinChallengeEndpoint(req, res) {
  try {
    const result = await joinChallenge(req.body.userId, req.params.id);
    res.json(result);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
}

/**
 * POST /api/gamification/challenges/:id/progress
 * Actualiza progreso en desafío
 */
export async function updateChallengeProgressEndpoint(req, res) {
  try {
    const result = await updateChallengeProgress(req.body.userId, req.params.id, req.body.progress);
    res.json(result);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
}

/**
 * GET /api/gamification/challenges
 * Lista desafíos activos
 */
export function listChallengesEndpoint(req, res) {
  const { category, status, limit, offset } = req.query;
  
  res.json(listChallenges({ category, status, limit, offset }));
}

/**
 * POST /api/gamification/rewards
 * Crea una recompensa
 */
export async function createRewardEndpoint(req, res) {
  try {
    const result = await createReward(req.body);
    res.json(result);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
}

/**
 * POST /api/gamification/rewards/:id/redeem
 * Canjea una recompensa
 */
export async function redeemRewardEndpoint(req, res) {
  try {
    const result = await redeemReward(req.body.userId, req.params.id);
    res.json(result);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
}

/**
 * GET /api/gamification/rewards
 * Lista recompensas disponibles
 */
export function listRewardsEndpoint(req, res) {
  const { type, limit, offset } = req.query;
  
  res.json(listRewards({ type, limit, offset }));
}

/**
 * POST /api/gamification/challenge/generate
 * Genera desafío personalizado con IA
 */
export async function generatePersonalizedChallengeEndpoint(req, res) {
  try {
    const result = await generatePersonalizedChallenge(req.body.userId, req.body.options);
    res.json(result);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
}

/**
 * POST /api/gamification/analyze
 * Analiza engagement del usuario
 */
export async function analyzeEngagementEndpoint(req, res) {
  try {
    const result = await analyzeEngagement(req.body.userId, req.body.options);
    res.json(result);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
}

/**
 * GET /api/gamification/metrics
 * Métricas del sistema de gamificación
 */
export function getGamificationMetricsEndpoint(req, res) {
  res.json(getGamificationMetrics());
}

/**
 * GET /api/gamification/status
 * Estado del sistema de gamificación
 */
export function getGamificationStatus(req, res) {
  res.json({
    status: 'active',
    config: GAMIFICATION_CONFIG,
    metrics: getGamificationMetrics(),
    timestamp: new Date().toISOString(),
  });
}

// ==============================================================================
// EXPORTACIONES
// ==============================================================================

export {
  awardPoints,
  getUserPoints,
  createAchievement,
  unlockAchievement,
  getUserAchievements,
  listAchievements,
  getLeaderboard,
  getUserRank,
  createChallenge,
  joinChallenge,
  updateChallengeProgress,
  listChallenges,
  createReward,
  redeemReward,
  listRewards,
  generatePersonalizedChallenge,
  analyzeEngagement,
  getGamificationMetrics,
  GAMIFICATION_CONFIG,
};

export default {
  awardPointsEndpoint,
  getUserPointsEndpoint,
  createAchievementEndpoint,
  unlockAchievementEndpoint,
  listAchievementsEndpoint,
  getLeaderboardEndpoint,
  getUserRankEndpoint,
  createChallengeEndpoint,
  joinChallengeEndpoint,
  updateChallengeProgressEndpoint,
  listChallengesEndpoint,
  createRewardEndpoint,
  redeemRewardEndpoint,
  listRewardsEndpoint,
  generatePersonalizedChallengeEndpoint,
  analyzeEngagementEndpoint,
  getGamificationMetricsEndpoint,
  getGamificationStatus,
  awardPoints,
  getUserPoints,
  createAchievement,
  unlockAchievement,
  getUserAchievements,
  listAchievements,
  getLeaderboard,
  getUserRank,
  createChallenge,
  joinChallenge,
  updateChallengeProgress,
  listChallenges,
  createReward,
  redeemReward,
  listRewards,
  generatePersonalizedChallenge,
  analyzeEngagement,
  getGamificationMetrics,
};
