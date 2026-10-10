/**
 * Content Generation - aigestion.net
 * 
 * Sistema de generación de contenido con IA:
 * - Artículos y blog posts
 * - Contenido para redes sociales
 * - Emails y newsletters
 * - Descripciones de productos
 * - Guiones y scripts
 * 
 * 100% gratuito con APIs open source
 */

import aiRouter from './ai_router.js';

// ==============================================================================
// CONFIGURACIÓN
// ==============================================================================

const CONTENT_CONFIG = {
  name: 'aig Content Generator',
  version: '1.0.0',
  contentTypes: ['article', 'social', 'email', 'product', 'script', 'video'],
  tones: ['professional', 'casual', 'friendly', 'formal', 'persuasive', 'educational'],
  languages: ['es', 'en', 'fr', 'de', 'it', 'pt'],
  maxLength: 5000,
};

// ==============================================================================
// GENERACIÓN DE CONTENIDO
// ==============================================================================

/**
 * Genera contenido según tipo y parámetros
 */
async function generateContent(type, options = {}) {
  const { topic, tone = 'professional', language = 'es', length = 'medium', keywords = [] } = options;
  
  console.log(`[Content] Generando ${type} sobre: ${topic}`);
  
  const prompt = buildContentPrompt(type, { topic, tone, language, length, keywords });
  
  const result = await aiRouter.callAI(prompt, {
    systemPrompt: getSystemPrompt(type, tone, language),
    maxTokens: getMaxTokens(length),
    temperature: getTemperature(tone),
  });
  
  return {
    success: true,
    type,
    content: result.response,
    metadata: {
      topic,
      tone,
      language,
      length,
      keywords,
      provider: result.provider,
      generatedAt: new Date().toISOString(),
    },
  };
}

/**
 * Genera artículo o blog post
 */
async function generateArticle(options = {}) {
  const { topic, sections = 5, tone = 'professional', language = 'es' } = options;
  
  console.log(`[Content] Generando artículo: ${topic}`);
  
  const prompt = `Escribe un artículo completo sobre "${topic}".

Requisitos:
- Tono: ${tone}
- Idioma: ${language}
- Secciones: ${sections}
- Incluir: introducción, desarrollo, conclusión
- SEO optimizado
- Contenido original y valioso

Proporciona el artículo completo con encabezados.`;
  
  const result = await aiRouter.callAI(prompt, {
    systemPrompt: 'Eres un escritor experto que crea contenido de calidad.',
    maxTokens: 2000,
    temperature: 0.7,
  });
  
  return {
    success: true,
    type: 'article',
    title: topic,
    content: result.response,
    sections,
    tone,
    language,
    provider: result.provider,
    timestamp: new Date().toISOString(),
  };
}

/**
 * Genera contenido para redes sociales
 */
async function generateSocialPost(options = {}) {
  const { topic, platform = 'twitter', tone = 'casual', includeHashtags = true } = options;
  
  console.log(`[Content] Generando post para ${platform}: ${topic}`);
  
  const platformLimits = {
    twitter: 280,
    facebook: 63206,
    instagram: 2200,
    linkedin: 3000,
    telegram: 4096,
  };
  
  const limit = platformLimits[platform] || 280;
  
  const prompt = `Crea un post para ${platform} sobre "${topic}".

Requisitos:
- Tono: ${tone}
- Máximo ${limit} caracteres
- ${includeHashtags ? 'Incluir hashtags relevantes' : 'Sin hashtags'}
- Call to action incluido
- Contenido engaging

Proporciona solo el texto del post.`;
  
  const result = await aiRouter.callAI(prompt, {
    systemPrompt: `Eres un experto en contenido para ${platform}.`,
    maxTokens: Math.ceil(limit / 4),
    temperature: 0.8,
  });
  
  return {
    success: true,
    type: 'social',
    platform,
    content: result.response,
    characterCount: result.response.length,
    limit,
    provider: result.provider,
    timestamp: new Date().toISOString(),
  };
}

/**
 * Genera email o newsletter
 */
async function generateEmail(options = {}) {
  const { subject, type = 'newsletter', tone = 'professional', recipient = 'subscriber' } = options;
  
  console.log(`[Content] Generando email: ${subject}`);
  
  const prompt = `Escribe un email ${type} con asunto "${subject}".

Requisitos:
- Tono: ${tone}
- Destinatario: ${recipient}
- Incluir: subject line, preview text, cuerpo, CTA
- Personalización
- Optimizado para conversión

Proporciona el email completo.`;
  
  const result = await aiRouter.callAI(prompt, {
    systemPrompt: 'Eres un experto en email marketing.',
    maxTokens: 1000,
    temperature: 0.6,
  });
  
  return {
    success: true,
    type: 'email',
    subject,
    emailType: type,
    content: result.response,
    tone,
    provider: result.provider,
    timestamp: new Date().toISOString(),
  };
}

/**
 * Genera descripción de producto
 */
async function generateProductDescription(options = {}) {
  const { productName, features = [], tone = 'persuasive', language = 'es' } = options;
  
  console.log(`[Content] Generando descripción de producto: ${productName}`);
  
  const prompt = `Escribe una descripción de producto para "${productName}".

Características: ${features.join(', ')}
Tono: ${tone}
Idioma: ${language}

Requisitos:
- Descripción atractiva
- Beneficios destacados
- Call to action
- SEO optimizado
- Persuasivo pero honesto

Proporciona la descripción completa.`;
  
  const result = await aiRouter.callAI(prompt, {
    systemPrompt: 'Eres un copywriter experto en descripciones de producto.',
    maxTokens: 500,
    temperature: 0.7,
  });
  
  return {
    success: true,
    type: 'product',
    productName,
    content: result.response,
    features,
    tone,
    provider: result.provider,
    timestamp: new Date().toISOString(),
  };
}

/**
 * Genera guion o script
 */
async function generateScript(options = {}) {
  const { topic, type = 'video', duration = '5min', tone = 'educational' } = options;
  
  console.log(`[Content] Generando guion: ${topic} (${type})`);
  
  const prompt = `Escribe un guion ${type} sobre "${topic}".

Requisitos:
- Duración: ${duration}
- Tono: ${tone}
- Incluir: introducción, desarrollo, conclusión
- Indicaciones de producción
- Transiciones suaves

Proporciona el guion completo.`;
  
  const result = await aiRouter.callAI(prompt, {
    systemPrompt: 'Eres un guionista experto en contenido audiovisual.',
    maxTokens: 1500,
    temperature: 0.7,
  });
  
  return {
    success: true,
    type: 'script',
    scriptType: type,
    topic,
    duration,
    content: result.response,
    tone,
    provider: result.provider,
    timestamp: new Date().toISOString(),
  };
}

// ==============================================================================
// FUNCIONES AUXILIARES
// ==============================================================================

/**
 * Construye prompt según tipo de contenido
 */
function buildContentPrompt(type, options) {
  const { topic, tone, language, length, keywords } = options;
  
  const prompts = {
    article: `Escribe un artículo sobre "${topic}" en ${language} con tono ${tone}.`,
    social: `Crea un post sobre "${topic}" con tono ${tone}.`,
    email: `Escribe un email sobre "${topic}" con tono ${tone}.`,
    product: `Describe "${topic}" con tono ${tone}.`,
    script: `Escribe un guion sobre "${topic}" con tono ${tone}.`,
  };
  
  return prompts[type] || prompts.article;
}

/**
 * Obtiene system prompt según tipo y tono
 */
function getSystemPrompt(type, tone, language) {
  const prompts = {
    article: `Eres un escritor experto en ${language}. Crea contenido de calidad con tono ${tone}.`,
    social: `Eres un experto en redes sociales. Crea contenido engaging con tono ${tone}.`,
    email: `Eres un experto en email marketing. Crea emails efectivos con tono ${tone}.`,
    product: `Eres un copywriter experto. Crea descripciones persuasivas con tono ${tone}.`,
    script: `Eres un guionista. Crea guiones atractivos con tono ${tone}.`,
  };
  
  return prompts[type] || prompts.article;
}

/**
 * Obtiene max tokens según longitud
 */
function getMaxTokens(length) {
  const tokens = {
    short: 200,
    medium: 500,
    long: 1000,
    xlong: 2000,
  };
  
  return tokens[length] || tokens.medium;
}

/**
 * Obtiene temperatura según tono
 */
function getTemperature(tone) {
  const temperatures = {
    professional: 0.5,
    casual: 0.7,
    friendly: 0.7,
    formal: 0.4,
    persuasive: 0.6,
    educational: 0.5,
  };
  
  return temperatures[tone] || 0.6;
}

// ==============================================================================
// MÉTRICAS
// ==============================================================================

/**
 * Obtiene métricas del sistema de contenido
 */
function getContentMetrics() {
  return {
    config: CONTENT_CONFIG,
    capabilities: CONTENT_CONFIG.contentTypes,
    tones: CONTENT_CONFIG.tones,
    languages: CONTENT_CONFIG.languages,
    timestamp: new Date().toISOString(),
  };
}

// ==============================================================================
// API ENDPOINTS
// ==============================================================================

/**
 * POST /api/content/generate
 * Genera contenido
 */
export async function generateContentEndpoint(req, res) {
  try {
    const result = await generateContent(req.body.type, req.body.options);
    res.json(result);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
}

/**
 * POST /api/content/article
 * Genera artículo
 */
export async function generateArticleEndpoint(req, res) {
  try {
    const result = await generateArticle(req.body.options);
    res.json(result);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
}

/**
 * POST /api/content/social
 * Genera post para redes sociales
 */
export async function generateSocialPostEndpoint(req, res) {
  try {
    const result = await generateSocialPost(req.body.options);
    res.json(result);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
}

/**
 * POST /api/content/email
 * Genera email
 */
export async function generateEmailEndpoint(req, res) {
  try {
    const result = await generateEmail(req.body.options);
    res.json(result);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
}

/**
 * POST /api/content/product
 * Genera descripción de producto
 */
export async function generateProductDescriptionEndpoint(req, res) {
  try {
    const result = await generateProductDescription(req.body.options);
    res.json(result);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
}

/**
 * POST /api/content/script
 * Genera guion
 */
export async function generateScriptEndpoint(req, res) {
  try {
    const result = await generateScript(req.body.options);
    res.json(result);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
}

/**
 * GET /api/content/metrics
 * Métricas del sistema
 */
export function getContentMetricsEndpoint(req, res) {
  res.json(getContentMetrics());
}

/**
 * GET /api/content/status
 * Estado del sistema de contenido
 */
export function getContentStatus(req, res) {
  res.json({
    status: 'active',
    config: CONTENT_CONFIG,
    metrics: getContentMetrics(),
    timestamp: new Date().toISOString(),
  });
}

// ==============================================================================
// EXPORTACIONES
// ==============================================================================

export {
  generateContent,
  generateArticle,
  generateSocialPost,
  generateEmail,
  generateProductDescription,
  generateScript,
  getContentMetrics,
  CONTENT_CONFIG,
};

export default {
  generateContentEndpoint,
  generateArticleEndpoint,
  generateSocialPostEndpoint,
  generateEmailEndpoint,
  generateProductDescriptionEndpoint,
  generateScriptEndpoint,
  getContentMetricsEndpoint,
  getContentStatus,
  generateContent,
  generateArticle,
  generateSocialPost,
  generateEmail,
  generateProductDescription,
  generateScript,
  getContentMetrics,
};
