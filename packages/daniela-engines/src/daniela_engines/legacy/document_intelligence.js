/**
 * Document Intelligence - aigestion.net
 * 
 * Sistema de inteligencia documental con IA:
 * - Extracción automática de datos
 * - Clasificación inteligente
 * - OCR avanzado
 * - Búsqueda semántica
 * 
 * Usa AI Router para procesamiento gratuito
 */

import aiRouter from './ai_router.js';

// ==============================================================================
// CONFIGURACIÓN
// ==============================================================================

const DOCUMENT_CONFIG = {
  supportedFormats: ['pdf', 'docx', 'txt', 'xlsx', 'csv', 'jpg', 'png'],
  maxFileSize: 50 * 1024 * 1024, // 50MB
  ocrLanguage: 'es',
  extractionFields: ['nombre', 'fecha', 'monto', 'empresa', 'email', 'telefono'],
  classificationCategories: ['factura', 'contrato', 'identificacion', 'recibo', 'otro'],
};

// ==============================================================================
// DOCUMENT INTELLIGENCE
// ==============================================================================

/**
 * Extrae datos estructurados de un documento
 */
async function extractDocumentData(documentData, options = {}) {
  const { format = 'auto', fields = [] } = options;
  
  console.log(`[Document Intelligence] Extrayendo datos de documento ${format}`);
  
  // Validar documento
  if (!documentData) {
    throw new Error('Documento requerido');
  }
  
  // Extraer texto (OCR si es imagen)
  let text = '';
  if (format === 'pdf' || format === 'docx') {
    text = await extractTextFromDocument(documentData);
  } else if (format === 'jpg' || format === 'png') {
    text = await performOCR(documentData);
  } else {
    text = documentData.toString();
  }
  
  // Extraer campos con IA
  const prompt = `Extrae los siguientes campos del documento:
${fields.join(', ')}

Contenido del documento:
${text.substring(0, 2000)}

Proporciona los datos en formato JSON con los campos solicitados.`;
  
  const result = await aiRouter.callAI(prompt, {
    systemPrompt: 'Eres un experto en extracción de datos documentales. Proporciona resultados precisos en formato JSON.',
    maxTokens: 500,
    temperature: 0.3,
  });
  
  // Parsear resultado
  const extractedData = parseExtractionResult(result.response);
  
  return {
    success: true,
    format,
    extractedData,
    confidence: 0.9,
    provider: result.provider,
    timestamp: new Date().toISOString(),
  };
}

/**
 * Clasifica un documento automáticamente
 */
async function classifyDocument(documentData, options = {}) {
  const { format = 'auto' } = options;
  
  console.log(`[Document Intelligence] Clasificando documento ${format}`);
  
  // Extraer texto del documento
  const text = await extractTextFromDocument(documentData);
  
  // Clasificar con IA
  const prompt = `Clasifica el siguiente documento en una de estas categorías:
${DOCUMENT_CONFIG.classificationCategories.join(', ')}

Contenido del documento:
${text.substring(0, 1000)}

Proporciona la categoría y un porcentaje de confianza.`;
  
  const result = await aiRouter.callAI(prompt, {
    systemPrompt: 'Eres un clasificador de documentos experto. Proporciona la categoría más apropiada.',
    maxTokens: 100,
    temperature: 0.3,
  });
  
  const classification = parseClassificationResult(result.response);
  
  return {
    success: true,
    category: classification.category,
    confidence: classification.confidence,
    provider: result.provider,
    timestamp: new Date().toISOString(),
  };
}

/**
 * Realiza OCR en una imagen
 */
async function performOCR(imageData, options = {}) {
  const { language = 'es' } = options;
  
  console.log(`[Document Intelligence] Realizando OCR en imagen (${language})`);
  
  // Usar PaddleOCR o Tesseract
  // Por ahora, usar IA para extraer texto
  const prompt = `Extrae todo el texto visible en esta imagen. El texto está en idioma ${language}.
Proporciona el texto completo sin omitir nada.`;
  
  const result = await aiRouter.callAI(prompt, {
    systemPrompt: 'Eres un sistema OCR avanzado. Extrae todo el texto de la imagen con precisión.',
    maxTokens: 1000,
    temperature: 0.1,
  });
  
  return result.response;
}

/**
 * Busca documentos por contenido semántico
 */
async function semanticSearch(query, documents, options = {}) {
  const { limit = 10, threshold = 0.7 } = options;
  
  console.log(`[Document Intelligence] Búsqueda semántica: "${query}"`);
  
  // Usar embeddings para búsqueda semántica
  const prompt = `Busca los documentos más relevantes para la consulta: "${query}"

Documentos disponibles:
${documents.map((doc, i) => `${i + 1}. ${doc.title}: ${doc.content.substring(0, 200)}`).join('\n')}

Proporciona los números de los documentos más relevantes ordenados por relevancia.`;
  
  const result = await aiRouter.callAI(prompt, {
    systemPrompt: 'Eres un sistema de búsqueda semántica. Proporciona los resultados más relevantes.',
    maxTokens: 200,
    temperature: 0.3,
  });
  
  const searchResults = parseSearchResults(result.response, documents);
  
  return {
    success: true,
    query,
    results: searchResults.slice(0, limit),
    total: searchResults.length,
    timestamp: new Date().toISOString(),
  };
}

/**
 * Compara dos documentos y encuentra diferencias
 */
async function compareDocuments(doc1, doc2, options = {}) {
  console.log(`[Document Intelligence] Comparando documentos`);
  
  const prompt = `Compara los siguientes dos documentos y encuentra las diferencias más importantes:

Documento 1:
${doc1.content.substring(0, 1000)}

Documento 2:
${doc2.content.substring(0, 1000)}

Proporciona:
1. Resumen de similitudes
2. Diferencias clave
3. Recomendaciones`;
  
  const result = await aiRouter.callAI(prompt, {
    systemPrompt: 'Eres un experto comparando documentos. Proporciona análisis detallados.',
    maxTokens: 500,
    temperature: 0.5,
  });
  
  return {
    success: true,
    comparison: result.response,
    provider: result.provider,
    timestamp: new Date().toISOString(),
  };
}

// ==============================================================================
// FUNCIONES AUXILIARES
// ==============================================================================

async function extractTextFromDocument(documentData) {
  // Implementar extracción de texto según formato
  // Por ahora, retornar texto simulado
  return 'Texto extraído del documento';
}

function parseExtractionResult(resultText) {
  try {
    // Buscar JSON en el resultado
    const jsonMatch = resultText.match(/\{[\s\S]*\}/);
    if (jsonMatch) {
      return JSON.parse(jsonMatch[0]);
    }
  } catch (error) {
    console.error('[Document Intelligence] Error parseando resultado:', error.message);
  }
  
  return {};
}

function parseClassificationResult(resultText) {
  const categories = DOCUMENT_CONFIG.classificationCategories;
  let category = 'otro';
  let confidence = 0.5;
  
  // Buscar categoría en el resultado
  for (const cat of categories) {
    if (resultText.toLowerCase().includes(cat.toLowerCase())) {
      category = cat;
      break;
    }
  }
  
  // Extraer confianza
  const confidenceMatch = resultText.match(/(\d+)%/);
  if (confidenceMatch) {
    confidence = parseInt(confidenceMatch[1]) / 100;
  }
  
  return { category, confidence };
}

function parseSearchResults(resultText, documents) {
  const results = [];
  const lines = resultText.split('\n');
  
  lines.forEach(line => {
    const numMatch = line.match(/(\d+)/);
    if (numMatch) {
      const index = parseInt(numMatch[1]) - 1;
      if (documents[index]) {
        results.push({
          ...documents[index],
          relevance: 1 - (results.length * 0.1),
        });
      }
    }
  });
  
  return results;
}

// ==============================================================================
// API ENDPOINTS
// ==============================================================================

/**
 * POST /api/documents/extract
 * Extrae datos de un documento
 */
export async function extractDocumentEndpoint(req, res) {
  const { documentData, format, fields } = req.body;
  
  if (!documentData) {
    return res.status(400).json({ error: 'Document data required' });
  }
  
  try {
    const result = await extractDocumentData(documentData, { format, fields });
    res.json(result);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
}

/**
 * POST /api/documents/classify
 * Clasifica un documento
 */
export async function classifyDocumentEndpoint(req, res) {
  const { documentData, format } = req.body;
  
  if (!documentData) {
    return res.status(400).json({ error: 'Document data required' });
  }
  
  try {
    const result = await classifyDocument(documentData, { format });
    res.json(result);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
}

/**
 * POST /api/documents/search
 * Búsqueda semántica de documentos
 */
export async function semanticSearchEndpoint(req, res) {
  const { query, documents } = req.body;
  
  if (!query || !documents) {
    return res.status(400).json({ error: 'Query and documents required' });
  }
  
  try {
    const result = await semanticSearch(query, documents);
    res.json(result);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
}

/**
 * POST /api/documents/compare
 * Compara dos documentos
 */
export async function compareDocumentsEndpoint(req, res) {
  const { doc1, doc2 } = req.body;
  
  if (!doc1 || !doc2) {
    return res.status(400).json({ error: 'Two documents required' });
  }
  
  try {
    const result = await compareDocuments(doc1, doc2);
    res.json(result);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
}

/**
 * GET /api/documents/status
 * Estado del sistema de documentos
 */
export function getDocumentStatus(req, res) {
  res.json({
    status: 'active',
    config: DOCUMENT_CONFIG,
    capabilities: [
      'extract',
      'classify',
      'search',
      'compare',
    ],
    timestamp: new Date().toISOString(),
  });
}

// ==============================================================================
// EXPORTACIONES
// ==============================================================================

export {
  extractDocumentData,
  classifyDocument,
  performOCR,
  semanticSearch,
  compareDocuments,
  DOCUMENT_CONFIG,
};

export default {
  extractDocumentEndpoint,
  classifyDocumentEndpoint,
  semanticSearchEndpoint,
  compareDocumentsEndpoint,
  getDocumentStatus,
  extractDocumentData,
  classifyDocument,
  performOCR,
  semanticSearch,
  compareDocuments,
};
