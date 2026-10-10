/**
 * AI Router Inteligente - AIG
 * 
 * Gestiona automáticamente la rotación entre providers gratuitos:
 * - DeepSeek (principal)
 * - OpenRouter (fallback)
 * - Gemini (fallback)
 * - Groq (fallback)
 * - HuggingFace (fallback)
 * 
 * Características:
 * - Rotación automática si un provider falla
 * - Rate limiting por provider
 * - Estadísticas de uso
 * - Fallback a respuesta local si todos fallan
 */

// ==============================================================================
// CONFIGURACIÓN DE PROVIDERS
// ==============================================================================

// Solo providers GRATUITOS - APIs de pago eliminadas
// Soluciones chinas open source + providers gratuitos
const PROVIDERS = [
  {
    id: 'qwen',
    name: 'Qwen (Alibaba)',
    endpoint: 'https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions',
    keyEnv: 'QWEN_API_KEY',
    model: 'qwen-turbo',
    priority: 1,
    rateLimit: 100,
    enabled: true,
  },
  {
    id: 'deepseek',
    name: 'DeepSeek',
    endpoint: 'https://api.deepseek.com/v1/chat/completions',
    keyEnv: 'DEEPSEEK_API_KEY',
    model: 'deepseek-chat',
    priority: 2,
    rateLimit: 50,
    enabled: true,
  },
  {
    id: 'openrouter',
    name: 'OpenRouter',
    endpoint: 'https://openrouter.ai/api/v1/chat/completions',
    keyEnv: 'OPENROUTER_API_KEY',
    model: 'openrouter/free',
    priority: 3,
    rateLimit: 100,
    enabled: true,
  },
  {
    id: 'gemini',
    name: 'Google Gemini',
    endpoint: 'https://generativelanguage.googleapis.com/v1beta/models',
    keyEnv: 'GEMINI_API_KEY',
    model: 'gemini-1.5-flash',
    priority: 4,
    rateLimit: 60,
    enabled: true,
  },
  {
    id: 'groq',
    name: 'Groq',
    endpoint: 'https://api.groq.com/openai/v1/chat/completions',
    keyEnv: 'GROQ_API_KEY',
    model: 'llama-3.3-70b-versatile',
    priority: 5,
    rateLimit: 14400,
    enabled: true,
  },
  {
    id: 'huggingface',
    name: 'HuggingFace',
    endpoint: 'https://api-inference.huggingface.co/models',
    keyEnv: 'HUGGINGFACE_API_KEY',
    model: 'mistralai/Mistral-7B-Instruct-v0.2',
    priority: 6,
    rateLimit: 300,
    enabled: true,
  },
  {
    id: 'mistral',
    name: 'Mistral',
    endpoint: 'https://api.mistral.ai/v1/chat/completions',
    keyEnv: 'MISTRAL_API_KEY',
    model: 'mistral-small-latest',
    priority: 7,
    rateLimit: 100,
    enabled: true,
  },
  {
    id: 'cohere',
    name: 'Cohere',
    endpoint: 'https://api.cohere.ai/v1/chat',
    keyEnv: 'COHERE_API_KEY',
    model: 'command-r-plus',
    priority: 8,
    rateLimit: 100,
    enabled: true,
  },
];

// ==============================================================================
// ESTADO DEL ROUTER
// ==============================================================================

const routerState = {
  currentProvider: 0,
  usageStats: {},
  lastUsed: {},
  errors: {},
};

// Inicializar estadísticas
PROVIDERS.forEach(p => {
  routerState.usageStats[p.id] = { requests: 0, errors: 0, tokens: 0 };
  routerState.lastUsed[p.id] = null;
  routerState.errors[p.id] = 0;
});

// ==============================================================================
// FUNCIÓN PRINCIPAL: LLAMAR A IA
// ==============================================================================

/**
 * Llama a un modelo de IA usando el router inteligente.
 * 
 * @param {string} prompt - Prompt para el modelo
 * @param {Object} options - Opciones adicionales
 * @returns {Object} Respuesta del modelo
 */
async function callAI(prompt, options = {}) {
  const systemPrompt = options.systemPrompt || 'Eres Daniela, asistente de IA para AIG. Responde conciso y útil en español.';
  const maxTokens = options.maxTokens || 200;
  const temperature = options.temperature || 0.7;
  
  // Intentar cada provider en orden de prioridad
  for (let i = 0; i < PROVIDERS.length; i++) {
    const provider = PROVIDERS[(routerState.currentProvider + i) % PROVIDERS.length];
    
    if (!provider.enabled) continue;
    
    // Verificar rate limit
    if (isRateLimited(provider.id)) {
      console.log(`[AI Router] ${provider.name} rate limit alcanzado, saltando...`);
      continue;
    }
    
    try {
      console.log(`[AI Router] Intentando con ${provider.name}...`);
      const response = await callProvider(provider, prompt, systemPrompt, maxTokens, temperature);
      
      // Actualizar estadísticas
      routerState.usageStats[provider.id].requests++;
      routerState.lastUsed[provider.id] = Date.now();
      routerState.currentProvider = (routerState.currentProvider + i) % PROVIDERS.length;
      
      return {
        success: true,
        response,
        provider: provider.id,
        providerName: provider.name,
      };
    } catch (error) {
      console.error(`[AI Router] Error con ${provider.name}:`, error.message);
      routerState.usageStats[provider.id].errors++;
      routerState.errors[provider.id]++;
    }
  }
  
  // Si todos fallan, usar respuesta local
  console.log('[AI Router] Todos los providers fallaron, usando respuesta local');
  return {
    success: false,
    response: generateLocalResponse(prompt),
    provider: 'local',
    providerName: 'Local (fallback)',
  };
}

/**
 * Llama a un provider específico.
 */
async function callProvider(provider, prompt, systemPrompt, maxTokens, temperature) {
  const apiKey = process.env[provider.keyEnv];
  
  if (!apiKey) {
    throw new Error(`API key no configurada: ${provider.keyEnv}`);
  }
  
  const response = await fetch(provider.endpoint, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${apiKey}`,
    },
    body: JSON.stringify({
      model: provider.model,
      messages: [
        { role: 'system', content: systemPrompt },
        { role: 'user', content: prompt }
      ],
      temperature,
      max_tokens: maxTokens,
    }),
  });
  
  if (!response.ok) {
    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
  }
  
  const data = await response.json();
  return data.choices[0].message.content;
}

/**
 * Verifica si un provider está rate limited.
 */
function isRateLimited(providerId) {
  const stats = routerState.usageStats[providerId];
  const lastUsed = routerState.lastUsed[providerId];
  
  if (!lastUsed) return false;
  
  const provider = PROVIDERS.find(p => p.id === providerId);
  const timeSinceLastUse = (Date.now() - lastUsed) / 1000 / 60; // minutos
  
  // Si ha hecho más requests que el límite en el último minuto
  if (timeSinceLastUse < 1 && stats.requests > provider.rateLimit) {
    return true;
  }
  
  return false;
}

/**
 * Genera una respuesta local cuando todos los providers fallan.
 */
function generateLocalResponse(prompt) {
  const lower = prompt.toLowerCase();
  
  if (lower.includes('hola') || lower.includes('hello')) {
    return '¡Hola! Soy Daniela, tu asistente. ¿En qué puedo ayudarte?';
  }
  if (lower.includes('ayuda') || lower.includes('help')) {
    return 'Puedo ayudarte con: comandos de voz, búsqueda, análisis, y más.';
  }
  if (lower.includes('volar') || lower.includes('navegar')) {
    return 'Entendido. Navegando a la ubicación solicitada.';
  }
  if (lower.includes('buscar') || lower.includes('search')) {
    return 'Buscando información...';
  }
  
  return `Comando "${prompt}" procesado. ¿En qué más puedo ayudarte?`;
}

// ==============================================================================
// ESTADÍSTICAS Y MONITOREO
// ==============================================================================

/**
 * Obtiene estadísticas de uso del router.
 */
export function getRouterStats() {
  return {
    providers: PROVIDERS.map(p => ({
      id: p.id,
      name: p.name,
      enabled: p.enabled,
      stats: routerState.usageStats[p.id],
      lastUsed: routerState.lastUsed[p.id],
    })),
    currentProvider: PROVIDERS[routerState.currentProvider]?.id,
  };
}

/**
 * Obtiene la lista de providers disponibles.
 */
export function getAvailableProviders() {
  return PROVIDERS.filter(p => p.enabled && process.env[p.keyEnv]).map(p => ({
    id: p.id,
    name: p.name,
    priority: p.priority,
  }));
}

/**
 * Activa/desactiva un provider.
 */
export function toggleProvider(providerId, enabled) {
  const provider = PROVIDERS.find(p => p.id === providerId);
  if (provider) {
    provider.enabled = enabled;
    console.log(`[AI Router] ${provider.name} ${enabled ? 'activado' : 'desactivado'}`);
  }
}

// ==============================================================================
// EXPORTACIONES
// ==============================================================================

export default {
  callAI,
  getRouterStats,
  getAvailableProviders,
  toggleProvider,
  PROVIDERS,
};
