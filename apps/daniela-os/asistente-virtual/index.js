/**
 * aigestion.net - Asistente Virtual Enterprise
 * 
 * API REST para asistente virtual IA
 * - LLM: Qwen/DeepSeek (gratuito)
 * - TTS: PaddleTTS (gratuito)
 * - STT: Whisper (gratuito)
 * - Memory: Redis/VectorDB
 */

import express from 'express';
import cors from 'cors';
import dotenv from 'dotenv';
import { readFileSync } from 'fs';
import { unifiedChat, unifiedStatus, unifiedSync } from './integration.js';

// Cargar variables de entorno desde daniela-os/.env
try {
  const envPath = new URL('../../AIG/daniela-os/.env', import.meta.url);
  const envContent = readFileSync(envPath, 'utf8');
  envContent.split('\n').forEach(line => {
    const [key, ...valueParts] = line.split('=');
    if (key && valueParts.length > 0) {
      process.env[key.trim()] = valueParts.join('=').trim();
    }
  });
  console.log('✅ Variables de entorno cargadas desde daniela-os/.env');
} catch (e) {
  console.warn('⚠️ No se pudo cargar .env:', e.message);
}
dotenv.config();

const app = express();
const PORT = process.env.ASSISTANT_PORT || 3001;

// Middleware
app.use(cors());
app.use(express.json());

// ==============================================================================
// ESTADO DEL ASISTENTE
// ==============================================================================

const assistantState = {
  name: 'aig Assistant',
  version: '1.0.0',
  status: 'active',
  provider: 'qwen',
  channels: ['web', 'whatsapp', 'telegram'],
  metrics: {
    totalChats: 0,
    totalMessages: 0,
    avgResponseTime: 0,
  },
};

// ==============================================================================
// API ENDPOINTS
// ==============================================================================

/**
 * GET /api/status
 * Estado del asistente
 */
app.get('/api/status', (req, res) => {
  res.json({
    ...assistantState,
    timestamp: new Date().toISOString(),
  });
});

/**
 * POST /api/chat
 * Procesa un mensaje y devuelve respuesta IA
 */
app.post('/api/chat', async (req, res) => {
  const { message, channel = 'web', userId = 'anonymous' } = req.body;
  
  if (!message) {
    return res.status(400).json({ error: 'Message required' });
  }
  
  const startTime = Date.now();
  
  try {
    // Llamar a LLM (Qwen/DeepSeek)
    const response = await callLLM(message);
    
    const responseTime = Date.now() - startTime;
    
    // Actualizar métricas
    assistantState.metrics.totalMessages++;
    assistantState.metrics.avgResponseTime = 
      (assistantState.metrics.avgResponseTime * (assistantState.metrics.totalMessages - 1) + responseTime) 
      / assistantState.metrics.totalMessages;
    
    res.json({
      success: true,
      response,
      channel,
      userId,
      responseTime,
      provider: assistantState.provider,
      timestamp: new Date().toISOString(),
    });
    
  } catch (error) {
    res.status(500).json({
      error: error.message,
      timestamp: new Date().toISOString(),
    });
  }
});

/**
 * POST /api/voice
 * Procesa audio y devuelve respuesta
 */
app.post('/api/voice', async (req, res) => {
  const { audio, channel = 'web' } = req.body;
  
  if (!audio) {
    return res.status(400).json({ error: 'Audio data required' });
  }
  
  try {
    // STT: Audio → Texto
    const text = await speechToText(audio);
    
    // LLM: Texto → Respuesta
    const response = await callLLM(text);
    
    // TTS: Respuesta → Audio
    const audioResponse = await textToSpeech(response);
    
    res.json({
      success: true,
      text,
      response,
      audio: audioResponse,
      channel,
      timestamp: new Date().toISOString(),
    });
    
  } catch (error) {
    res.status(500).json({
      error: error.message,
      timestamp: new Date().toISOString(),
    });
  }
});

/**
 * GET /api/metrics
 * Métricas de uso
 */
app.get('/api/metrics', (req, res) => {
  res.json({
    ...assistantState.metrics,
    uptime: process.uptime(),
    timestamp: new Date().toISOString(),
  });
});

// ==============================================================================
// LLM INTEGRATION
// ==============================================================================

async function callLLM(message) {
  const provider = process.env.LLM_PROVIDER || 'qwen';
  
  if (provider === 'qwen') {
    return callQwen(message);
  } else if (provider === 'deepseek') {
    return callDeepSeek(message);
  }
  
  throw new Error(`Provider no soportado: ${provider}`);
}

async function callQwen(message) {
  const apiKey = process.env.QWEN_API_KEY;
  
  if (!apiKey) {
    throw new Error('QWEN_API_KEY no configurada');
  }
  
  const response = await fetch('https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${apiKey}`,
    },
    body: JSON.stringify({
      model: 'qwen-turbo',
      messages: [
        { role: 'system', content: 'Eres aig Assistant, un asistente virtual empresarial. Responde de forma profesional y útil en español.' },
        { role: 'user', content: message }
      ],
      temperature: 0.7,
      max_tokens: 200,
    }),
  });
  
  if (!response.ok) {
    throw new Error(`Qwen HTTP ${response.status}`);
  }
  
  const data = await response.json();
  return data.choices[0].message.content;
}

async function callDeepSeek(message) {
  const apiKey = process.env.DEEPSEEK_API_KEY;
  
  if (!apiKey) {
    throw new Error('DEEPSEEK_API_KEY no configurada');
  }
  
  const response = await fetch('https://api.deepseek.com/v1/chat/completions', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${apiKey}`,
    },
    body: JSON.stringify({
      model: 'deepseek-chat',
      messages: [
        { role: 'system', content: 'Eres aig Assistant, un asistente virtual empresarial. Responde de forma profesional y útil en español.' },
        { role: 'user', content: message }
      ],
      temperature: 0.7,
      max_tokens: 200,
    }),
  });
  
  if (!response.ok) {
    throw new Error(`DeepSeek HTTP ${response.status}`);
  }
  
  const data = await response.json();
  return data.choices[0].message.content;
}

// ==============================================================================
// VOICE INTEGRATION
// ==============================================================================

async function speechToText(audio) {
  // Integrar Whisper API
  // Por ahora, retornar texto simulado
  return 'Texto transcrito del audio';
}

async function textToSpeech(text) {
  // Integrar PaddleTTS
  // Por ahora, retornar audio simulado
  return 'audio_base64_data';
}

// ==============================================================================
// INTEGRACIÓN CON DANIELA OS
// ==============================================================================

/**
 * POST /api/unified/chat
 * Endpoint unificado para chat
 */
app.post('/api/unified/chat', unifiedChat);

/**
 * GET /api/unified/status
 * Estado unificado del sistema
 */
app.get('/api/unified/status', unifiedStatus);

/**
 * POST /api/unified/sync
 * Sincroniza estado entre sistemas
 */
app.post('/api/unified/sync', unifiedSync);

// ==============================================================================
// START SERVER
// ==============================================================================

app.listen(PORT, () => {
  console.log(`✅ aig Assistant activo en http://localhost:${PORT}`);
  console.log(`📡 Canales: ${assistantState.channels.join(', ')}`);
  console.log(`🤖 Provider: ${assistantState.provider}`);
  console.log(`💰 Costo: €0 (solo APIs gratuitas)`);
  console.log(`🔗 Integración con Daniela OS: ✅ Activa`);
});

export default app;
