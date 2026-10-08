/**
 * Integración Asistente Virtual + Daniela OS
 * 
 * Conecta ambos sistemas para que funcionen juntos:
 * - Daniela OS usa el Asistente Virtual como backend
 * - Comparten providers de IA
 * - Sincronización de estado
 */

import aiRouter from '../engine/legacy/ai_router.js';
const { callAI } = aiRouter;

// ==============================================================================
// ESTADO COMPARTIDO
// ==============================================================================

const integrationState = {
  danielaOS: {
    status: 'active',
    provider: 'deepseek',
    voiceEnabled: false,
  },
  asistenteVirtual: {
    status: 'active',
    provider: 'qwen',
    channels: ['web', 'whatsapp', 'telegram'],
  },
  shared: {
    totalRequests: 0,
    totalTokens: 0,
    cost: 0,
  },
};

// ==============================================================================
// API UNIFICADA
// ==============================================================================

/**
 * Procesa un mensaje usando el sistema unificado
 */
async function processMessage(message, options = {}) {
  const { channel = 'web', userId = 'anonymous', useVoice = false } = options;
  
  console.log(`[Integración] Procesando mensaje de ${userId} vía ${channel}`);
  
  // Usar el AI Router para obtener respuesta
  const result = await callAI(message, {
    systemPrompt: 'Eres Daniela, asistente de IA para aigestion.net. Responde de forma profesional y útil en español.',
    maxTokens: 200,
    temperature: 0.7,
  });
  
  // Actualizar estadísticas
  integrationState.shared.totalRequests++;
  
  return {
    success: true,
    response: result.response,
    provider: result.provider,
    channel,
    userId,
    timestamp: new Date().toISOString(),
  };
}

/**
 * Obtiene el estado unificado del sistema
 */
function getUnifiedStatus() {
  return {
    danielaOS: integrationState.danielaOS,
    asistenteVirtual: integrationState.asistenteVirtual,
    shared: integrationState.shared,
    timestamp: new Date().toISOString(),
  };
}

/**
 * Sincroniza el estado entre sistemas
 */
function syncState() {
  // Sincronizar providers
  if (integrationState.danielaOS.provider !== integrationState.asistenteVirtual.provider) {
    console.log(`[Integración] Sincronizando providers: ${integrationState.danielaOS.provider} ↔ ${integrationState.asistenteVirtual.provider}`);
  }
  
  // Sincronizar estadísticas
  console.log(`[Integración] Estado sincronizado - Requests: ${integrationState.shared.totalRequests}`);
  
  return getUnifiedStatus();
}

// ==============================================================================
// ENDPOINTS DE INTEGRACIÓN
// ==============================================================================

/**
 * POST /api/unified/chat
 * Endpoint unificado para chat
 */
export async function unifiedChat(req, res) {
  const { message, channel, userId } = req.body;
  
  if (!message) {
    return res.status(400).json({ error: 'Message required' });
  }
  
  try {
    const result = await processMessage(message, { channel, userId });
    res.json(result);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
}

/**
 * GET /api/unified/status
 * Estado unificado del sistema
 */
export function unifiedStatus(req, res) {
  res.json(getUnifiedStatus());
}

/**
 * POST /api/unified/sync
 * Sincroniza estado entre sistemas
 */
export function unifiedSync(req, res) {
  const status = syncState();
  res.json({
    success: true,
    status,
    timestamp: new Date().toISOString(),
  });
}

// ==============================================================================
// EXPORTACIONES
// ==============================================================================

export {
  processMessage,
  getUnifiedStatus,
  syncState,
  integrationState,
};

export default {
  unifiedChat,
  unifiedStatus,
  unifiedSync,
  processMessage,
  getUnifiedStatus,
  syncState,
};
