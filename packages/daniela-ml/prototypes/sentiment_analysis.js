/**
 * Sentiment Analysis - aigestion.net
 * 
 * Sistema de análisis de sentimiento con IA:
 * - Análisis de emociones
 * - Clasificación de opiniones
 * - Tendencias de sentimiento
 * - Análisis de feedback
 * - Integración con IA
 * 
 * 100% gratuito con APIs open source
 */

import aiRouter from './ai_router.js';

// ==============================================================================
// CONFIGURACIÓN
// ==============================================================================

const SENTIMENT_CONFIG = {
  name: 'aig Sentiment Analysis',
  version: '1.0.0',
  languages: ['es', 'en', 'fr', 'de', 'it', 'pt'],
  emotions: ['joy', 'sadness', 'anger', 'fear', 'surprise', 'disgust', 'neutral'],
  sentimentScale: {
    veryNegative: { min: -1, max: -0.6 },
    negative: { min: -0.6, max: -0.2 },
    neutral: { min: -0.2, max: 0.2 },
    positive: { min: 0.2, max: 0.6 },
    veryPositive: { min: 0.6, max: 1 },
  },
  aspects: ['product', 'service', 'price', 'quality', 'support', 'delivery'],
};

// ==============================================================================
// BASE DE DATOS
// ==============================================================================

const sentimentHistory = new Map();
const emotionTrends = new Map();
const feedbackStore = new Map();

// ==============================================================================
// ANÁLISIS DE SENTIMIENTO
// ==============================================================================

/**
 * Analiza sentimiento de un texto
 */
async function analyzeSentiment(text, options = {}) {
  const { language = 'es', includeEmotions = true, includeAspects = false } = options;
  
  console.log(`[Sentiment] Analizando texto en ${language}`);
  
  const prompt = `Analiza el siguiente texto y determina su sentimiento:

Texto: "${text}"
Idioma: ${language}

Proporciona:
1. Sentimiento general (muy negativo, negativo, neutral, positivo, muy positivo)
2. Puntuación de sentimiento (-1 a 1)
3. Emociones detectadas ${includeEmotions ? '(alegría, tristeza, enojo, miedo, sorpresa, asco)' : ''}
4. Intensidad emocional (0-100%)
5. ${includeAspects ? 'Aspectos mencionados (producto, servicio, precio, calidad, soporte)' : ''}

Formato JSON:
{
  "sentiment": "positive",
  "score": 0.65,
  "confidence": 0.85,
  "emotions": [{"emotion": "joy", "intensity": 80}],
  "aspects": [{"aspect": "product", "sentiment": "positive"}]
}`;
  
  const result = await aiRouter.callAI(prompt, {
    systemPrompt: 'Eres un analista de sentimiento experto. Proporciona análisis precisos en formato JSON.',
    maxTokens: 400,
    temperature: 0.3,
  });
  
  const analysis = parseSentimentResult(result.response);
  
  // Guardar en historial
  const analysisId = `sent_${Date.now()}`;
  sentimentHistory.set(analysisId, {
    id: analysisId,
    text,
    language,
    analysis,
    timestamp: new Date().toISOString(),
  });
  
  return {
    success: true,
    id: analysisId,
    text,
    language,
    sentiment: analysis.sentiment,
    score: analysis.score,
    confidence: analysis.confidence,
    emotions: analysis.emotions,
    aspects: analysis.aspects,
    provider: result.provider,
    timestamp: new Date().toISOString(),
  };
}

/**
 * Parsea resultado del análisis
 */
function parseSentimentResult(resultText) {
  try {
    const jsonMatch = resultText.match(/\{[\s\S]*\}/);
    if (jsonMatch) {
      return JSON.parse(jsonMatch[0]);
    }
  } catch (error) {
    console.error('[Sentiment] Error parseando resultado:', error.message);
  }
  
  // Resultado por defecto
  return {
    sentiment: 'neutral',
    score: 0,
    confidence: 0.5,
    emotions: [{ emotion: 'neutral', intensity: 50 }],
    aspects: [],
  };
}

// ==============================================================================
// ANÁLISIS DE EMOCIONES
// ==============================================================================

/**
 * Analiza emociones en texto
 */
async function analyzeEmotions(text, options = {}) {
  const { language = 'es', detailed = false } = options;
  
  console.log(`[Sentiment] Analizando emociones: "${text.substring(0, 50)}..."`);
  
  const prompt = `Identifica las emociones presentes en el siguiente texto:

Texto: "${text}"
Idioma: ${language}

Emociones a detectar: alegría, tristeza, enojo, miedo, sorpresa, asco, neutral

Proporciona:
1. Emoción dominante
2. Lista de emociones con intensidad (0-100%)
3. ${detailed ? 'Análisis detallado de cada emoción' : ''}

Formato JSON:
{
  "dominant": "joy",
  "emotions": [
    {"emotion": "joy", "intensity": 80},
    {"emotion": "surprise", "intensity": 30}
  ],
  "emotionalValence": "positive"
}`;
  
  const result = await aiRouter.callAI(prompt, {
    systemPrompt: 'Eres un psicólogo experto en emociones. Proporciona análisis precisos.',
    maxTokens: 300,
    temperature: 0.3,
  });
  
  return {
    success: true,
    text,
    language,
    analysis: result.response,
    provider: result.provider,
    timestamp: new Date().toISOString(),
  };
}

/**
 * Detecta cambios emocionales
 */
async function detectEmotionalShifts(texts, options = {}) {
  console.log(`[Sentiment] Detectando cambios emocionales en ${texts.length} textos`);
  
  const prompt = `Analiza la evolución emocional en los siguientes textos:

${texts.map((t, i) => `${i + 1}. "${t}"`).join('\n')}

Proporciona:
1. Evolución emocional
2. Puntos de inflexión
3. Tendencia general
4. Recomendaciones

Formato JSON:
{
  "evolution": ["positive", "neutral", "negative"],
  "inflectionPoints": [{"index": 1, "change": "positive to neutral"}],
  "trend": "declining",
  "recommendations": ["..."]
}`;
  
  const result = await aiRouter.callAI(prompt, {
    systemPrompt: 'Eres un analista de tendencias emocionales.',
    maxTokens: 400,
    temperature: 0.5,
  });
  
  return {
    success: true,
    textsCount: texts.length,
    analysis: result.response,
    provider: result.provider,
    timestamp: new Date().toISOString(),
  };
}

// ==============================================================================
// ANÁLISIS DE OPINIONES
// ==============================================================================

/**
 * Analiza opiniones y reviews
 */
async function analyzeOpinions(reviews, options = {}) {
  const { language = 'es', groupBy = 'sentiment' } = options;
  
  console.log(`[Sentiment] Analizando ${reviews.length} opiniones`);
  
  const prompt = `Analiza las siguientes opiniones de clientes:

${reviews.map((r, i) => `${i + 1}. "${r}"`).join('\n')}

Proporciona:
1. Sentimiento general
2. Temas principales mencionados
3. Aspectos positivos y negativos
4. Recomendaciones de mejora

Formato JSON:
{
  "overallSentiment": "positive",
  "themes": ["..."],
  "positive": ["..."],
  "negative": ["..."],
  "recommendations": ["..."]
}`;
  
  const result = await aiRouter.callAI(prompt, {
    systemPrompt: 'Eres un analista de feedback de clientes. Proporciona análisis accionables.',
    maxTokens: 600,
    temperature: 0.5,
  });
  
  return {
    success: true,
    reviewsCount: reviews.length,
    language,
    analysis: result.response,
    provider: result.provider,
    timestamp: new Date().toISOString(),
  };
}

/**
 * Clasifica feedback por categoría
 */
async function classifyFeedback(feedback, options = {}) {
  const { categories = SENTIMENT_CONFIG.aspects } = options;
  
  console.log(`[Sentiment] Clasificando feedback en ${categories.length} categorías`);
  
  const prompt = `Clasifica el siguiente feedback según estas categorías: ${categories.join(', ')}

Feedback: "${feedback}"

Proporciona:
1. Categoría principal
2. Sentimiento
3. Prioridad
4. Acción recomendada

Formato JSON:
{
  "category": "product",
  "sentiment": "positive",
  "priority": "medium",
  "action": "..."
}`;
  
  const result = await aiRouter.callAI(prompt, {
    systemPrompt: 'Eres un clasificador de feedback. Sé preciso y consistente.',
    maxTokens: 200,
    temperature: 0.3,
  });
  
  return {
    success: true,
    feedback,
    classification: result.response,
    provider: result.provider,
    timestamp: new Date().toISOString(),
  };
}

// ==============================================================================
// TENDENCIAS DE SENTIMIENTO
// ==============================================================================

/**
 * Analiza tendencias de sentimiento
 */
async function analyzeSentimentTrends(options = {}) {
  const { period = '7d', groupBy = 'day' } = options;
  
  console.log(`[Sentiment] Analizando tendencias (${period})`);
  
  const allAnalyses = Array.from(sentimentHistory.values());
  
  if (allAnalyses.length === 0) {
    return {
      success: true,
      message: 'No hay datos suficientes',
      data: null,
    };
  }
  
  const prompt = `Analiza las tendencias de sentimiento basadas en:

Total análisis: ${allAnalyses.length}
Período: ${period}
Últimos análisis: ${JSON.stringify(allAnalyses.slice(-10))}

Proporciona:
1. Tendencia general
2. Cambios significativos
3. Predicción próxima semana
4. Alertas necesarias`;
  
  const result = await aiRouter.callAI(prompt, {
    systemPrompt: 'Eres un analista de tendencias de sentimiento.',
    maxTokens: 400,
    temperature: 0.4,
  });
  
  return {
    success: true,
    period,
    totalAnalyses: allAnalyses.length,
    trends: result.response,
    provider: result.provider,
    timestamp: new Date().toISOString(),
  };
}

/**
 * Genera reporte de sentimiento
 */
async function generateSentimentReport(options = {}) {
  const { period = '30d', format = 'detailed' } = options;
  
  console.log(`[Sentiment] Generando reporte (${period})`);
  
  const allAnalyses = Array.from(sentimentHistory.values());
  
  const prompt = `Genera un reporte de sentimiento ${format} para el período ${period}:

Total análisis: ${allAnalyses.length}
Datos: ${JSON.stringify(allAnalyses.slice(-20))}

Incluye:
1. Resumen ejecutivo
2. Métricas clave
3. Tendencias
4. Hallazgos principales
5. Recomendaciones`;
  
  const result = await aiRouter.callAI(prompt, {
    systemPrompt: 'Eres un analista de datos que genera reportes ejecutivos.',
    maxTokens: 800,
    temperature: 0.5,
  });
  
  return {
    success: true,
    period,
    format,
    report: result.response,
    provider: result.provider,
    timestamp: new Date().toISOString(),
  };
}

// ==============================================================================
// MÉTRICAS
// ==============================================================================

/**
 * Obtiene métricas del sistema de sentimiento
 */
function getSentimentMetrics() {
  const totalAnalyses = sentimentHistory.size;
  
  const sentimentDistribution = {
    veryPositive: 0,
    positive: 0,
    neutral: 0,
    negative: 0,
    veryNegative: 0,
  };
  
  sentimentHistory.forEach(analysis => {
    const sentiment = analysis.analysis?.sentiment || 'neutral';
    sentimentDistribution[sentiment]++;
  });
  
  return {
    totalAnalyses,
    sentimentDistribution,
    emotions: Array.from(emotionTrends.keys()),
    feedbackCount: feedbackStore.size,
    config: SENTIMENT_CONFIG,
    timestamp: new Date().toISOString(),
  };
}

// ==============================================================================
// API ENDPOINTS
// ==============================================================================

/**
 * POST /api/sentiment/analyze
 * Analiza sentimiento
 */
export async function analyzeSentimentEndpoint(req, res) {
  try {
    const result = await analyzeSentiment(req.body.text, req.body.options);
    res.json(result);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
}

/**
 * POST /api/sentiment/emotions
 * Analiza emociones
 */
export async function analyzeEmotionsEndpoint(req, res) {
  try {
    const result = await analyzeEmotions(req.body.text, req.body.options);
    res.json(result);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
}

/**
 * POST /api/sentiment/shifts
 * Detecta cambios emocionales
 */
export async function detectEmotionalShiftsEndpoint(req, res) {
  try {
    const result = await detectEmotionalShifts(req.body.texts, req.body.options);
    res.json(result);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
}

/**
 * POST /api/sentiment/opinions
 * Analiza opiniones
 */
export async function analyzeOpinionsEndpoint(req, res) {
  try {
    const result = await analyzeOpinions(req.body.reviews, req.body.options);
    res.json(result);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
}

/**
 * POST /api/sentiment/classify
 * Clasifica feedback
 */
export async function classifyFeedbackEndpoint(req, res) {
  try {
    const result = await classifyFeedback(req.body.feedback, req.body.options);
    res.json(result);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
}

/**
 * POST /api/sentiment/trends
 * Analiza tendencias
 */
export async function analyzeSentimentTrendsEndpoint(req, res) {
  try {
    const result = await analyzeSentimentTrends(req.body.options);
    res.json(result);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
}

/**
 * POST /api/sentiment/report
 * Genera reporte
 */
export async function generateSentimentReportEndpoint(req, res) {
  try {
    const result = await generateSentimentReport(req.body.options);
    res.json(result);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
}

/**
 * GET /api/sentiment/metrics
 * Métricas del sistema
 */
export function getSentimentMetricsEndpoint(req, res) {
  res.json(getSentimentMetrics());
}

/**
 * GET /api/sentiment/status
 * Estado del sistema
 */
export function getSentimentStatus(req, res) {
  res.json({
    status: 'active',
    config: SENTIMENT_CONFIG,
    metrics: getSentimentMetrics(),
    timestamp: new Date().toISOString(),
  });
}

// ==============================================================================
// EXPORTACIONES
// ==============================================================================

export {
  analyzeSentiment,
  analyzeEmotions,
  detectEmotionalShifts,
  analyzeOpinions,
  classifyFeedback,
  analyzeSentimentTrends,
  generateSentimentReport,
  getSentimentMetrics,
  SENTIMENT_CONFIG,
};

export default {
  analyzeSentimentEndpoint,
  analyzeEmotionsEndpoint,
  detectEmotionalShiftsEndpoint,
  analyzeOpinionsEndpoint,
  classifyFeedbackEndpoint,
  analyzeSentimentTrendsEndpoint,
  generateSentimentReportEndpoint,
  getSentimentMetricsEndpoint,
  getSentimentStatus,
  analyzeSentiment,
  analyzeEmotions,
  detectEmotionalShifts,
  analyzeOpinions,
  classifyFeedback,
  analyzeSentimentTrends,
  generateSentimentReport,
  getSentimentMetrics,
};
