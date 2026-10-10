/**
 * Document Processing - aigestion.net
 * 
 * Sistema de procesamiento documental con IA:
 * - Extracción de texto de documentos
 * - Análisis de contenido
 * - Clasificación automática
 * - Búsqueda semántica
 * - Resumen automático
 * 
 * 100% gratuito con APIs open source
 */

import aiRouter from './ai_router.js';

// ==============================================================================
// CONFIGURACIÓN
// ==============================================================================

const DOCUMENT_CONFIG = {
  name: 'aig Document Processor',
  version: '1.0.0',
  supportedFormats: ['pdf', 'docx', 'txt', 'xlsx', 'csv', 'json', 'md'],
  maxFileSize: 10 * 1024 * 1024, // 10MB
  ocrLanguages: ['es', 'en', 'fr', 'de', 'it', 'pt'],
  extractionDepth: 'standard', // 'basic', 'standard', 'deep'
  enableOCR: true,
  enableClassification: true,
  enableSummarization: true,
};

// ==============================================================================
// BASE DE DATOS
// ==============================================================================

const documents = new Map();
const classifications = new Map();
const summaries = new Map();
const searchIndex = new Map();

// ==============================================================================
// EXTRACCIÓN DE DOCUMENTOS
// ==============================================================================

/**
 * Extrae texto de un documento
 */
async function extractDocument(documentData, options = {}) {
  const { format = 'auto', pages = 'all', includeMetadata = true } = options;
  
  console.log(`[Document] Extrayendo documento (${format})`);
  
  const document = {
    id: `doc_${Date.now()}`,
    name: documentData.name || 'document',
    format: format === 'auto' ? detectFormat(documentData) : format,
    size: documentData.size || 0,
    pages: 0,
    content: '',
    metadata: {},
    extractedAt: new Date().toISOString(),
  };
  
  // Extraer contenido según formato
  switch (document.format) {
    case 'pdf':
      document.content = await extractFromPDF(documentData, options);
      break;
    case 'docx':
      document.content = await extractFromDOCX(documentData, options);
      break;
    case 'txt':
    case 'md':
      document.content = documentData.content || '';
      break;
    case 'xlsx':
    case 'csv':
      document.content = await extractFromSpreadsheet(documentData, options);
      break;
    case 'json':
      document.content = JSON.stringify(documentData.content, null, 2);
      break;
    default:
      throw new Error(`Formato no soportado: ${document.format}`);
  }
  
  // Extraer metadatos
  if (includeMetadata) {
    document.metadata = extractMetadata(document);
  }
  
  // Guardar documento
  documents.set(document.id, document);
  
  // Actualizar índice de búsqueda
  updateSearchIndex(document);
  
  return {
    success: true,
    document,
    stats: {
      characters: document.content.length,
      words: document.content.split(/\s+/).length,
      lines: document.content.split('\n').length,
    },
  };
}

/**
 * Detecta formato del documento
 */
function detectFormat(documentData) {
  if (documentData.format) return documentData.format;
  if (documentData.name) {
    const ext = documentData.name.split('.').pop().toLowerCase();
    if (DOCUMENT_CONFIG.supportedFormats.includes(ext)) return ext;
  }
  return 'txt';
}

/**
 * Extrae texto de PDF
 */
async function extractFromPDF(documentData, options) {
  // En producción, usar pdf-parse o similar
  console.log(`[Document] Extrayendo PDF: ${options.pages} páginas`);
  return 'Texto extraído del PDF';
}

/**
 * Extrae texto de DOCX
 */
async function extractFromDOCX(documentData, options) {
  // En producción, usar mammoth o similar
  console.log(`[Document] Extrayendo DOCX`);
  return 'Texto extraído del DOCX';
}

/**
 * Extrae texto de hoja de cálculo
 */
async function extractFromSpreadsheet(documentData, options) {
  // En producción, usar xlsx o similar
  console.log(`[Document] Extrayendo hoja de cálculo`);
  return 'Datos extraídos de la hoja de cálculo';
}

/**
 * Extrae metadatos del documento
 */
function extractMetadata(document) {
  return {
    title: extractTitle(document),
    author: extractAuthor(document),
    creationDate: extractCreationDate(document),
    wordCount: document.content.split(/\s+/).length,
    language: detectLanguage(document.content),
    topics: extractTopics(document.content),
  };
}

/**
 * Extrae título del documento
 */
function extractTitle(document) {
  const firstLine = document.content.split('\n')[0];
  return firstLine ? firstLine.substring(0, 100) : document.name;
}

/**
 * Extrae autor del documento
 */
function extractAuthor(document) {
  // Buscar patrones comunes de autor
  const authorPatterns = [
    /Autor:\s*(.+)/i,
    /Author:\s*(.+)/i,
    /Por:\s*(.+)/i,
  ];
  
  for (const pattern of authorPatterns) {
    const match = document.content.match(pattern);
    if (match) return match[1].trim();
  }
  
  return 'Desconocido';
}

/**
 * Extrae fecha de creación
 */
function extractCreationDate(document) {
  const datePatterns = [
    /(\d{1,2}\/\d{1,2}\/\d{4})/,
    /(\d{4}-\d{2}-\d{2})/,
    /(\d{1,2}-\d{1,2}-\d{4})/,
  ];
  
  for (const pattern of datePatterns) {
    const match = document.content.match(pattern);
    if (match) return match[1];
  }
  
  return document.extractedAt;
}

/**
 * Detecta idioma del documento
 */
function detectLanguage(text) {
  // En producción, usar librería de detección de idioma
  const spanishWords = ['el', 'la', 'los', 'las', 'de', 'en', 'que', 'y'];
  const englishWords = ['the', 'a', 'an', 'of', 'in', 'to', 'and'];
  
  const words = text.toLowerCase().split(/\s+/);
  let spanishCount = 0;
  let englishCount = 0;
  
  words.forEach(word => {
    if (spanishWords.includes(word)) spanishCount++;
    if (englishWords.includes(word)) englishCount++;
  });
  
  return spanishCount > englishCount ? 'es' : 'en';
}

/**
 * Extrae temas principales del documento
 */
function extractTopics(text) {
  // En producción, usar NLP para extraer temas
  const commonWords = new Set(['el', 'la', 'de', 'en', 'que', 'y', 'a', 'un', 'una']);
  const wordFreq = new Map();
  
  const words = text.toLowerCase().split(/\s+/);
  words.forEach(word => {
    if (!commonWords.has(word) && word.length > 3) {
      wordFreq.set(word, (wordFreq.get(word) || 0) + 1);
    }
  });
  
  return Array.from(wordFreq.entries())
    .sort((a, b) => b[1] - a[1])
    .slice(0, 5)
    .map(([word]) => word);
}

// ==============================================================================
// CLASIFICACIÓN DE DOCUMENTOS
// ==============================================================================

/**
 * Clasifica un documento automáticamente
 */
async function classifyDocument(documentId, options = {}) {
  const { model = 'auto', includeConfidence = true } = options;
  
  console.log(`[Document] Clasificando documento: ${documentId}`);
  
  const document = documents.get(documentId);
  
  if (!document) {
    throw new Error(`Documento no encontrado: ${documentId}`);
  }
  
  const prompt = `Clasifica el siguiente documento en una de estas categorías:
- contrato
- factura
- identificacion
- recibo
- informe
- carta
- formulario
- otro

Contenido del documento:
"${document.content.substring(0, 1500)}"

Proporciona:
1. Categoría principal
2. Subcategoría
3. Confianza (0-100%)
4. Características identificadas`;
  
  const result = await aiRouter.callAI(prompt, {
    systemPrompt: 'Eres un clasificador de documentos experto. Sé preciso y proporciona confianza.',
    maxTokens: 300,
    temperature: 0.3,
  });
  
  const classification = {
    id: `class_${Date.now()}`,
    documentId,
    category: extractCategory(result.response),
    subCategory: extractSubCategory(result.response),
    confidence: extractConfidence(result.response),
    characteristics: extractCharacteristics(result.response),
    model,
    provider: result.provider,
    timestamp: new Date().toISOString(),
  };
  
  classifications.set(classification.id, classification);
  
  return {
    success: true,
    classification,
  };
}

/**
 * Obtiene clasificación de un documento
 */
function getDocumentClassification(documentId) {
  const docClassifications = Array.from(classifications.values())
    .filter(c => c.documentId === documentId);
  
  if (docClassifications.length === 0) {
    return null;
  }
  
  return docClassifications.sort((a, b) => 
    new Date(b.timestamp) - new Date(a.timestamp)
  )[0];
}

/**
 * Lista todas las clasificaciones
 */
function listClassifications(options = {}) {
  const { category, limit = 50, offset = 0 } = options;
  
  let result = Array.from(classifications.values());
  
  if (category) {
    result = result.filter(c => c.category === category);
  }
  
  return {
    classifications: result.slice(offset, offset + limit),
    total: result.length,
    limit,
    offset,
  };
}

// ==============================================================================
// RESUMEN AUTOMÁTICO
// ==============================================================================

/**
 * Genera resumen de un documento
 */
async function summarizeDocument(documentId, options = {}) {
  const { length = 'medium', style = 'professional', focus = '' } = options;
  
  console.log(`[Document] Generando resumen: ${documentId}`);
  
  const document = documents.get(documentId);
  
  if (!document) {
    throw new Error(`Documento no encontrado: ${documentId}`);
  }
  
  const lengthMap = {
    short: 'máximo 100 palabras',
    medium: 'máximo 250 palabras',
    long: 'máximo 500 palabras',
  };
  
  const prompt = `Resume el siguiente documento:

"${document.content}"

Requisitos:
- Longitud: ${lengthMap[length] || lengthMap.medium}
- Estilo: ${style}
- ${focus ? `Enfoque: ${focus}` : ''}

Proporciona un resumen claro, conciso y profesional.`;
  
  const result = await aiRouter.callAI(prompt, {
    systemPrompt: 'Eres un experto en resumen de documentos. Proporciona resúmenes claros y concisos.',
    maxTokens: getMaxTokens(length),
    temperature: 0.4,
  });
  
  const summary = {
    id: `summary_${Date.now()}`,
    documentId,
    content: result.response,
    length,
    style,
    focus,
    provider: result.provider,
    timestamp: new Date().toISOString(),
  };
  
  summaries.set(summary.id, summary);
  
  return {
    success: true,
    summary,
  };
}

/**
 * Obtiene resumen de un documento
 */
function getDocumentSummary(documentId) {
  const docSummaries = Array.from(summaries.values())
    .filter(s => s.documentId === documentId);
  
  if (docSummaries.length === 0) {
    return null;
  }
  
  return docSummaries.sort((a, b) => 
    new Date(b.timestamp) - new Date(a.timestamp)
  )[0];
}

/**
 * Lista todos los resúmenes
 */
function listSummaries(options = {}) {
  const { limit = 50, offset = 0 } = options;
  
  const allSummaries = Array.from(summaries.values());
  
  return {
    summaries: allSummaries.slice(offset, offset + limit),
    total: allSummaries.length,
    limit,
    offset,
  };
}

// ==============================================================================
// BÚSQUEDA SEMÁNTICA
// ==============================================================================

/**
 * Busca documentos semánticamente
 */
async function semanticSearch(query, options = {}) {
  const { limit = 10, minRelevance = 0.5, filters = {} } = options;
  
  console.log(`[Document] Búsqueda semántica: "${query}"`);
  
  // Analizar consulta con IA
  const prompt = `Analiza la siguiente búsqueda y determina qué tipo de documentos serían relevantes:

Búsqueda: "${query}"

Proporciona:
1. Conceptos clave
2. Sinónimos
3. Términos relacionados
4. Categorías relevantes`;
  
  const analysis = await aiRouter.callAI(prompt, {
    systemPrompt: 'Eres un experto en búsqueda semántica de documentos.',
    maxTokens: 200,
    temperature: 0.3,
  });
  
  // Buscar en índice
  const results = performSemanticSearch(query, analysis.response, filters);
  
  // Filtrar por relevancia
  const filteredResults = results
    .filter(r => r.relevance >= minRelevance)
    .slice(0, limit);
  
  return {
    success: true,
    query,
    results: filteredResults,
    total: results.length,
    analysis: analysis.response,
    provider: analysis.provider,
    timestamp: new Date().toISOString(),
  };
}

/**
 * Realiza búsqueda semántica en el índice
 */
function performSemanticSearch(query, analysis, filters) {
  const results = [];
  const queryLower = query.toLowerCase();
  
  for (const [id, document] of documents.entries()) {
    let relevance = 0;
    
    // Búsqueda por contenido
    if (document.content.toLowerCase().includes(queryLower)) {
      relevance += 0.5;
    }
    
    // Búsqueda por nombre
    if (document.name.toLowerCase().includes(queryLower)) {
      relevance += 0.3;
    }
    
    // Búsqueda por metadatos
    if (document.metadata.keywords) {
      const keywords = document.metadata.keywords.toLowerCase();
      if (keywords.includes(queryLower)) {
        relevance += 0.2;
      }
    }
    
    // Aplicar filtros
    if (filters.format && document.format !== filters.format) continue;
    if (filters.dateFrom && new Date(document.extractedAt) < new Date(filters.dateFrom)) continue;
    if (filters.dateTo && new Date(document.extractedAt) > new Date(filters.dateTo)) continue;
    
    if (relevance > 0) {
      results.push({
        id: document.id,
        name: document.name,
        format: document.format,
        relevance,
        snippet: generateSnippet(document.content, query),
        metadata: document.metadata,
      });
    }
  }
  
  // Ordenar por relevancia
  results.sort((a, b) => b.relevance - a.relevance);
  
  return results;
}

/**
 * Genera snippet de documento
 */
function generateSnippet(content, query, maxLength = 150) {
  const index = content.toLowerCase().indexOf(query.toLowerCase());
  
  if (index === -1) {
    return content.substring(0, maxLength) + '...';
  }
  
  const start = Math.max(0, index - 50);
  const end = Math.min(content.length, index + maxLength);
  
  let snippet = content.substring(start, end);
  
  if (start > 0) snippet = '...' + snippet;
  if (end < content.length) snippet = snippet + '...';
  
  return snippet;
}

/**
 * Actualiza índice de búsqueda
 */
function updateSearchIndex(document) {
  searchIndex.set(document.id, {
    name: document.name.toLowerCase(),
    content: document.content.toLowerCase(),
    format: document.format,
    metadata: document.metadata,
    indexedAt: Date.now(),
  });
}

/**
 * Limpia documentos del índice
 */
function cleanSearchIndex() {
  const now = Date.now();
  const retentionMs = 30 * 24 * 60 * 60 * 1000; // 30 días
  
  let removed = 0;
  for (const [id, entry] of searchIndex.entries()) {
    if (now - entry.indexedAt > retentionMs) {
      searchIndex.delete(id);
      removed++;
    }
  }
  
  return { removed, remaining: searchIndex.size };
}

// ==============================================================================
// FUNCIONES AUXILIARES
// ==============================================================================

function extractCategory(text) {
  const match = text.match(/categoría:\s*(.+)/i);
  return match ? match[1].trim().toLowerCase() : 'otro';
}

function extractSubCategory(text) {
  const match = text.match(/subcategoría:\s*(.+)/i);
  return match ? match[1].trim().toLowerCase() : '';
}

function extractConfidence(text) {
  const match = text.match(/confianza:\s*(\d+)%/i);
  return match ? parseInt(match[1]) : 70;
}

function extractCharacteristics(text) {
  const characteristics = [];
  const lines = text.split('\n');
  
  lines.forEach(line => {
    if (line.toLowerCase().includes('característica')) {
      characteristics.push(line.trim());
    }
  });
  
  return characteristics;
}

function getMaxTokens(length) {
  const tokens = {
    short: 150,
    medium: 400,
    long: 800,
  };
  return tokens[length] || tokens.medium;
}

// ==============================================================================
// MÉTRICAS
// ==============================================================================

function getDocumentMetrics() {
  const totalDocuments = documents.size;
  const totalClassifications = classifications.size;
  const totalSummaries = summaries.size;
  const totalSearchResults = searchIndex.size;
  
  return {
    documents: {
      total: totalDocuments,
      byFormat: getDocumentFormatDistribution(),
      totalSize: Array.from(documents.values()).reduce((sum, d) => sum + d.size, 0),
    },
    classifications: {
      total: totalClassifications,
      byCategory: getClassificationDistribution(),
    },
    summaries: {
      total: totalSummaries,
    },
    searchIndex: {
      total: totalSearchResults,
    },
    config: DOCUMENT_CONFIG,
    timestamp: new Date().toISOString(),
  };
}

function getDocumentFormatDistribution() {
  const distribution = {};
  documents.forEach(doc => {
    distribution[doc.format] = (distribution[doc.format] || 0) + 1;
  });
  return distribution;
}

function getClassificationDistribution() {
  const distribution = {};
  classifications.forEach(classification => {
    distribution[classification.category] = (distribution[classification.category] || 0) + 1;
  });
  return distribution;
}

// ==============================================================================
// API ENDPOINTS
// ==============================================================================

export async function extractDocumentEndpoint(req, res) {
  try {
    const result = await extractDocument(req.body.documentData, req.body.options);
    res.json(result);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
}

export async function classifyDocumentEndpoint(req, res) {
  try {
    const result = await classifyDocument(req.body.documentId, req.body.options);
    res.json(result);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
}

export async function summarizeDocumentEndpoint(req, res) {
  try {
    const result = await summarizeDocument(req.body.documentId, req.body.options);
    res.json(result);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
}

export async function semanticSearchEndpoint(req, res) {
  try {
    const result = await semanticSearch(req.body.query, req.body.options);
    res.json(result);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
}

export function getDocumentMetricsEndpoint(req, res) {
  res.json(getDocumentMetrics());
}

export function getDocumentStatus(req, res) {
  res.json({
    status: 'active',
    config: DOCUMENT_CONFIG,
    metrics: getDocumentMetrics(),
    timestamp: new Date().toISOString(),
  });
}

// ==============================================================================
// EXPORTACIONES
// ==============================================================================

export {
  extractDocument,
  classifyDocument,
  summarizeDocument,
  semanticSearch,
  getDocumentMetrics,
  DOCUMENT_CONFIG,
};

export default {
  extractDocumentEndpoint,
  classifyDocumentEndpoint,
  summarizeDocumentEndpoint,
  semanticSearchEndpoint,
  getDocumentMetricsEndpoint,
  getDocumentStatus,
  extractDocument,
  classifyDocument,
  summarizeDocument,
  semanticSearch,
  getDocumentMetrics,
};
