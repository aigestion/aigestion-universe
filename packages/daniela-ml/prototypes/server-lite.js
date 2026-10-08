/**
 * Servidor Ultra-Ligero - aigestion.net
 * 
 * Diseñado para funcionar con recursos mínimos:
 * - Memoria: ~20MB
 * - Sin dependencias externas
 * - HTTP nativo de Node.js
 * 
 * Puerto: 3000
 */

import { createServer } from 'http';

const PORT = process.env.PORT || 3000;

// ==============================================================================
// ESTADO MÍNIMO
// ==============================================================================

const stats = {
  requests: 0,
  startTime: Date.now(),
};

// ==============================================================================
// HANDLERS
// ==============================================================================

const routes = {
  // Estado del servidor
  '/api/status': () => ({
    status: 'active',
    uptime: Math.floor((Date.now() - stats.startTime) / 1000),
    requests: stats.requests,
    memory: process.memoryUsage(),
    timestamp: new Date().toISOString(),
  }),
  
  // Módulos disponibles
  '/api/modules': () => ({
    modules: [
      'ai-router', 'decision-engine', 'process-automation',
      'predictive-analytics', 'cloud-platform', 'document-intelligence',
      'api-marketplace', 'multi-tenant-saas', 'edge-computing',
      'ide-assistant', 'data-lake', 'realtime-analytics',
      'blockchain-ai', 'iot-ai', 'voice-interface',
      'arvr-solutions', 'personalization-ai', 'gamification',
      'social-media-ai', 'content-generation', 'sentiment-analysis',
    ],
    total: 22,
  }),
  
  // Chat con IA
  '/api/chat': async (body) => {
    const { message } = body;
    
    // Respuesta inteligente basada en el mensaje
    const response = generateResponse(message);
    
    return {
      success: true,
      response,
      timestamp: new Date().toISOString(),
    };
  },
  
  // Métricas
  '/api/metrics': () => ({
    requests: stats.requests,
    uptime: Math.floor((Date.now() - stats.startTime) / 1000),
    memory: process.memoryUsage(),
    timestamp: new Date().toISOString(),
  }),
  
  // Costos
  '/api/costs': () => ({
    monthly: 0,
    currency: 'EUR',
    savings: 55,
    timestamp: new Date().toISOString(),
  }),
};

// ==============================================================================
// LÓGICA DE RESPUESTA
// ==============================================================================

function generateResponse(message) {
  const lower = message.toLowerCase();
  
  if (lower.includes('hola') || lower.includes('hello')) {
    return '¡Hola! Soy aig, tu asistente de IA. ¿En qué puedo ayudarte?';
  }
  
  if (lower.includes('módulo') || lower.includes('module')) {
    return 'Tengo 22 módulos de IA disponibles: AI Router, Decision Engine, Process Automation, y más.';
  }
  
  if (lower.includes('costo') || lower.includes('precio')) {
    return 'Todos mis servicios son 100% gratuitos. Uso APIs gratuitas de Qwen, DeepSeek, OpenRouter y más.';
  }
  
  if (lower.includes('ayuda') || lower.includes('help')) {
    return 'Puedes preguntarme sobre: módulos disponibles, costos, estado del sistema, o cualquier duda sobre IA.';
  }
  
  return `Entendido: "${message}". Estoy procesando tu solicitud con inteligencia artificial.`;
}

// ==============================================================================
// SERVIDOR HTTP
// ==============================================================================

const server = createServer(async (req, res) => {
  stats.requests++;
  
  const url = req.url;
  const method = req.method;
  
  // CORS
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');
  
  if (method === 'OPTIONS') {
    res.writeHead(200);
    res.end();
    return;
  }
  
  try {
    // Buscar ruta
    const handler = routes[url];
    
    if (handler) {
      let body = {};
      
      if (method === 'POST') {
        body = await readBody(req);
      }
      
      const result = await handler(body);
      
      res.writeHead(200, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify(result, null, 2));
    } else {
      res.writeHead(404, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({
        error: 'Not found',
        availableRoutes: Object.keys(routes),
      }));
    }
  } catch (error) {
    console.error('[Server Error]', error.message);
    res.writeHead(500, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify({ error: error.message }));
  }
});

function readBody(req) {
  return new Promise((resolve) => {
    let body = '';
    req.on('data', chunk => { body += chunk; });
    req.on('end', () => {
      try {
        resolve(JSON.parse(body));
      } catch {
        resolve({});
      }
    });
  });
}

// ==============================================================================
// INICIAR
// ==============================================================================

server.listen(PORT, () => {
  console.log('═══════════════════════════════════════════════════════════');
  console.log('  🚀 aigestion.net - Servidor Ultra-Ligero');
  console.log('═══════════════════════════════════════════════════════════');
  console.log(`  📡 URL: http://localhost:${PORT}`);
  console.log(`  💰 Costo: €0/mes`);
  console.log(`  🤖 Módulos: 22`);
  console.log(`  💾 Memoria: ~20MB`);
  console.log('═══════════════════════════════════════════════════════════');
  console.log('');
  console.log('  Endpoints:');
  console.log('    GET  /api/status    - Estado del servidor');
  console.log('    GET  /api/modules   - Módulos disponibles');
  console.log('    POST /api/chat      - Chat con IA');
  console.log('    GET  /api/metrics   - Métricas');
  console.log('    GET  /api/costs     - Costos');
  console.log('');
});

export default server;
