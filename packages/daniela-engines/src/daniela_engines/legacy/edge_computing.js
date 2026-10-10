/**
 * Edge Computing IA - aigestion.net
 * 
 * Sistema de computación en edge devices:
 * - Procesamiento local en dispositivos
 * - Caché inteligente
 * - Sincronización offline
 * - Modelos ligeros optimizados
 * - Optimización de recursos
 * 
 * 100% gratuito con APIs open source
 */

import aiRouter from './ai_router.js';

// ==============================================================================
// CONFIGURACIÓN
// ==============================================================================

const EDGE_CONFIG = {
  name: 'aig Edge',
  version: '1.0.0',
  maxCacheSize: 100 * 1024 * 1024, // 100MB
  syncInterval: 300000, // 5 minutos
  maxConcurrentTasks: 5,
  modelOptimization: 'balanced', // 'speed', 'balanced', 'accuracy'
};

// ==============================================================================
// GESTIÓN DE CACHE
// ==============================================================================

const cache = new Map();
let cacheSize = 0;

/**
 * Almacena datos en caché local
 */
function setCache(key, value, ttl = 3600000) {
  const serialized = JSON.stringify(value);
  const size = serialized.length;
  
  // Verificar límite de caché
  if (cacheSize + size > EDGE_CONFIG.maxCacheSize) {
    evictCache();
  }
  
  cache.set(key, {
    value,
    size,
    createdAt: Date.now(),
    expiresAt: Date.now() + ttl,
  });
  
  cacheSize += size;
  
  return true;
}

/**
 * Obtiene datos de caché
 */
function getCache(key) {
  const entry = cache.get(key);
  
  if (!entry) {
    return null;
  }
  
  // Verificar expiración
  if (Date.now() > entry.expiresAt) {
    cache.delete(key);
    cacheSize -= entry.size;
    return null;
  }
  
  return entry.value;
}

/**
 * Elimina elementos antiguos de caché
 */
function evictCache() {
  const entries = Array.from(cache.entries())
    .sort((a, b) => a[1].createdAt - b[1].createdAt);
  
  // Eliminar 10% más antiguo
  const toRemove = Math.ceil(entries.length * 0.1);
  
  for (let i = 0; i < toRemove; i++) {
    const [key, entry] = entries[i];
    cache.delete(key);
    cacheSize -= entry.size;
  }
  
  console.log(`[Edge] Cache evicted: ${toRemove} items`);
}

/**
 * Limpia caché expirado
 */
function cleanupCache() {
  const now = Date.now();
  let removed = 0;
  
  for (const [key, entry] of cache.entries()) {
    if (now > entry.expiresAt) {
      cache.delete(key);
      cacheSize -= entry.size;
      removed++;
    }
  }
  
  return removed;
}

// ==============================================================================
// SINCRONIZACIÓN OFFLINE
// ==============================================================================

const syncQueue = [];
let isSyncing = false;

/**
 * Añade tarea a la cola de sincronización
 */
function queueSync(task) {
  syncQueue.push({
    ...task,
    queuedAt: Date.now(),
    attempts: 0,
  });
  
  if (!isSyncing) {
    processSyncQueue();
  }
}

/**
 * Procesa cola de sincronización
 */
async function processSyncQueue() {
  if (isSyncing || syncQueue.length === 0) {
    return;
  }
  
  isSyncing = true;
  
  while (syncQueue.length > 0) {
    const task = syncQueue.shift();
    
    try {
      await executeSyncTask(task);
      console.log(`[Edge] Sync task completed: ${task.type}`);
    } catch (error) {
      console.error(`[Edge] Sync task failed: ${task.type}`, error.message);
      
      // Reintentar si no se ha excedido el límite
      if (task.attempts < 3) {
        task.attempts++;
        syncQueue.push(task);
      }
    }
  }
  
  isSyncing = false;
}

/**
 * Ejecuta tarea de sincronización
 */
async function executeSyncTask(task) {
  switch (task.type) {
    case 'data-upload':
      return await uploadData(task.data);
    case 'model-update':
      return await updateModel(task.data);
    case 'config-sync':
      return await syncConfig(task.data);
    default:
      throw new Error(`Unknown sync task type: ${task.type}`);
  }
}

/**
 * Sube datos al servidor
 */
async function uploadData(data) {
  // Implementar upload real
  console.log(`[Edge] Uploading data: ${Object.keys(data).length} items`);
  return { success: true };
}

/**
 * Actualiza modelo local
 */
async function updateModel(modelData) {
  // Implementar actualización de modelo
  console.log(`[Edge] Updating model: ${modelData.version}`);
  return { success: true };
}

/**
 * Sincroniza configuración
 */
async function syncConfig(config) {
  // Implementar sync de configuración
  console.log(`[Edge] Syncing config`);
  return { success: true };
}

// ==============================================================================
// MODELOS LIGEROS
// ==============================================================================

const lightModels = {
  'qwen-turbo': {
    name: 'Qwen Turbo',
    size: 'small',
    speed: 'fast',
    accuracy: 'good',
    useCase: 'General purpose',
  },
  'qwen-mini': {
    name: 'Qwen Mini',
    size: 'tiny',
    speed: 'very-fast',
    accuracy: 'basic',
    useCase: 'Simple queries',
  },
  'deepseek-lite': {
    name: 'DeepSeek Lite',
    size: 'small',
    speed: 'fast',
    accuracy: 'good',
    useCase: 'Code and analysis',
  },
};

/**
 * Selecciona modelo según recursos disponibles
 */
function selectModel(task) {
  const availableMemory = getAvailableMemory();
  const requiredSpeed = task.speed || 'normal';
  
  // Si hay poca memoria, usar modelo más ligero
  if (availableMemory < 500 * 1024 * 1024) { // < 500MB
    return lightModels['qwen-mini'];
  }
  
  // Si se necesita velocidad
  if (requiredSpeed === 'fast') {
    return lightModels['qwen-turbo'];
  }
  
  // Balance por defecto
  return lightModels['deepseek-lite'];
}

/**
 * Ejecuta inferencia en edge
 */
async function runInference(input, options = {}) {
  const model = selectModel(options);
  
  console.log(`[Edge] Running inference with model: ${model.name}`);
  
  const result = await aiRouter.callAI(input, {
    systemPrompt: options.systemPrompt || 'Eres un asistente útil.',
    maxTokens: options.maxTokens || 100,
    temperature: options.temperature || 0.7,
  });
  
  return {
    success: true,
    response: result.response,
    model: model.name,
    provider: result.provider,
    responseTime: 0, // Medir tiempo real
    timestamp: new Date().toISOString(),
  };
}

// ==============================================================================
// OPTIMIZACIÓN DE RECURSOS
// ==============================================================================

/**
 * Obtiene memoria disponible
 */
function getAvailableMemory() {
  try {
    const os = require('os');
    return os.freemem();
  } catch {
    return 1024 * 1024 * 1024; // 1GB default
  }
}

/**
 * Obtiene uso de CPU
 */
function getCpuUsage() {
  try {
    const os = require('os');
    const cpus = os.cpus();
    const usage = cpus.map(cpu => {
      const total = Object.values(cpu.times).reduce((a, b) => a + b, 0);
      const idle = cpu.times.idle;
      return (total - idle) / total;
    });
    return usage.reduce((a, b) => a + b, 0) / usage.length;
  } catch {
    return 0;
  }
}

/**
 * Optimiza rendimiento según recursos
 */
function optimizePerformance() {
  const memory = getAvailableMemory();
  const cpu = getCpuUsage();
  
  let optimization = 'balanced';
  
  if (memory < 200 * 1024 * 1024 || cpu > 0.8) {
    optimization = 'speed';
    console.log('[Edge] Optimizing for speed (low resources)');
  } else if (memory > 1024 * 1024 * 1024 && cpu < 0.3) {
    optimization = 'accuracy';
    console.log('[Edge] Optimizing for accuracy (high resources)');
  }
  
  return optimization;
}

// ==============================================================================
// GESTIÓN DE TAREAS
// ==============================================================================

const taskQueue = [];
let activeTasks = 0;

/**
 * Añade tarea a la cola
 */
function queueTask(task) {
  return new Promise((resolve, reject) => {
    taskQueue.push({
      ...task,
      resolve,
      reject,
      queuedAt: Date.now(),
    });
    
    processTaskQueue();
  });
}

/**
 * Procesa cola de tareas
 */
async function processTaskQueue() {
  if (activeTasks >= EDGE_CONFIG.maxConcurrentTasks || taskQueue.length === 0) {
    return;
  }
  
  activeTasks++;
  const task = taskQueue.shift();
  
  try {
    const result = await executeTask(task);
    task.resolve(result);
  } catch (error) {
    task.reject(error);
  } finally {
    activeTasks--;
    processTaskQueue();
  }
}

/**
 * Ejecuta tarea
 */
async function executeTask(task) {
  switch (task.type) {
    case 'inference':
      return await runInference(task.input, task.options);
    case 'cache-update':
      return setCache(task.key, task.value, task.ttl);
    case 'sync':
      queueSync(task.syncData);
      return { queued: true };
    default:
      throw new Error(`Unknown task type: ${task.type}`);
  }
}

// ==============================================================================
// MÉTRICAS Y MONITOREO
// ==============================================================================

/**
 * Obtiene métricas del edge
 */
function getEdgeMetrics() {
  return {
    cache: {
      size: cacheSize,
      items: cache.size,
      maxSize: EDGE_CONFIG.maxCacheSize,
    },
    sync: {
      queueLength: syncQueue.length,
      isSyncing,
    },
    tasks: {
      queueLength: taskQueue.length,
      activeTasks,
      maxConcurrent: EDGE_CONFIG.maxConcurrentTasks,
    },
    resources: {
      availableMemory: getAvailableMemory(),
      cpuUsage: getCpuUsage(),
    },
    timestamp: new Date().toISOString(),
  };
}

// ==============================================================================
// API ENDPOINTS
// ==============================================================================

/**
 * POST /api/edge/inference
 * Ejecuta inferencia en edge
 */
export async function runInferenceEndpoint(req, res) {
  const { input, options } = req.body;
  
  if (!input) {
    return res.status(400).json({ error: 'Input required' });
  }
  
  try {
    const result = await runInference(input, options);
    res.json(result);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
}

/**
 * POST /api/edge/cache
 * Almacena en caché
 */
export function setCacheEndpoint(req, res) {
  const { key, value, ttl } = req.body;
  
  if (!key || !value) {
    return res.status(400).json({ error: 'Key and value required' });
  }
  
  setCache(key, value, ttl);
  
  res.json({
    success: true,
    key,
    size: JSON.stringify(value).length,
  });
}

/**
 * GET /api/edge/cache/:key
 * Obtiene de caché
 */
export function getCacheEndpoint(req, res) {
  const value = getCache(req.params.key);
  
  if (!value) {
    return res.status(404).json({ error: 'Cache miss' });
  }
  
  res.json({
    success: true,
    value,
  });
}

/**
 * POST /api/edge/sync
 * Añade tarea de sincronización
 */
export function queueSyncEndpoint(req, res) {
  const { type, data } = req.body;
  
  queueSync({ type, data });
  
  res.json({
    success: true,
    queued: true,
    queueLength: syncQueue.length,
  });
}

/**
 * GET /api/edge/metrics
 * Métricas del edge
 */
export function getEdgeMetricsEndpoint(req, res) {
  res.json(getEdgeMetrics());
}

/**
 * GET /api/edge/status
 * Estado del edge
 */
export function getEdgeStatus(req, res) {
  res.json({
    status: 'active',
    config: EDGE_CONFIG,
    metrics: getEdgeMetrics(),
    timestamp: new Date().toISOString(),
  });
}

// ==============================================================================
// EXPORTACIONES
// ==============================================================================

export {
  setCache,
  getCache,
  queueSync,
  runInference,
  optimizePerformance,
  getEdgeMetrics,
  EDGE_CONFIG,
};

export default {
  runInferenceEndpoint,
  setCacheEndpoint,
  getCacheEndpoint,
  queueSyncEndpoint,
  getEdgeMetricsEndpoint,
  getEdgeStatus,
  setCache,
  getCache,
  queueSync,
  runInference,
  optimizePerformance,
  getEdgeMetrics,
};
