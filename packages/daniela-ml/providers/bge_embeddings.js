/**
 * BGE Embeddings Provider - BAAI Open Source
 * 
 * Embeddings chinos open source
 * Modelo: BAAI/bge-large-zh-v1.5
 * 
 * Uso: Vectorización de texto para búsqueda semántica
 */

const BGE_CONFIG = {
  model: 'BAAI/bge-large-zh-v1.5',
  dimension: 1024,
  endpoint: 'https://api-inference.huggingface.co/models/BAAI/bge-large-zh-v1.5',
  keyEnv: 'HUGGINGFACE_API_KEY',
};

/**
 * Genera embeddings para un texto usando BGE
 */
async function generateEmbeddings(text) {
  const apiKey = process.env[BGE_CONFIG.keyEnv];
  
  if (!apiKey) {
    throw new Error('HUGGINGFACE_API_KEY no configurada');
  }
  
  const response = await fetch(BGE_CONFIG.endpoint, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${apiKey}`,
    },
    body: JSON.stringify({
      inputs: text,
      options: { wait_for_model: true },
    }),
  });
  
  if (!response.ok) {
    throw new Error(`BGE HTTP ${response.status}`);
  }
  
  const data = await response.json();
  return data; // Array de embeddings
}

/**
 * Calcula similitud coseno entre dos vectores
 */
function cosineSimilarity(vecA, vecB) {
  let dotProduct = 0;
  let normA = 0;
  let normB = 0;
  
  for (let i = 0; i < vecA.length; i++) {
    dotProduct += vecA[i] * vecB[i];
    normA += vecA[i] * vecA[i];
    normB += vecB[i] * vecB[i];
  }
  
  return dotProduct / (Math.sqrt(normA) * Math.sqrt(normB));
}

export { generateEmbeddings, cosineSimilarity, BGE_CONFIG };
