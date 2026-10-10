/**
 * Blockchain + IA - aigestion.net
 * 
 * Sistema de blockchain con inteligencia artificial:
 * - Contratos inteligentes con IA
 * - Verificación de datos en blockchain
 * - Trazabilidad con IA
 * - Análisis de transacciones
 * - Detección de fraudes
 * 
 * 100% gratuito con APIs open source
 */

import aiRouter from './ai_router.js';

// ==============================================================================
// CONFIGURACIÓN
// ==============================================================================

const BLOCKCHAIN_CONFIG = {
  name: 'aig Blockchain',
  version: '1.0.0',
  network: 'local',
  consensus: 'poa', // Proof of Authority
  blockTime: 5000, // 5 segundos
  maxTransactionsPerBlock: 100,
  aiEnabled: true,
};

// ==============================================================================
// BASE DE DATOS BLOCKCHAIN
// ==============================================================================

const blockchain = [];
const pendingTransactions = [];
const smartContracts = new Map();
const aiModels = new Map();

/**
 * Crea un bloque genesis
 */
function createGenesisBlock() {
  const genesisBlock = {
    index: 0,
    timestamp: Date.now(),
    transactions: [],
    previousHash: '0'.repeat(64),
    hash: calculateHash(0, Date.now(), [], '0'.repeat(64)),
    nonce: 0,
  };
  
  blockchain.push(genesisBlock);
  
  return genesisBlock;
}

/**
 * Calcula hash de un bloque
 */
function calculateHash(index, timestamp, transactions, previousHash) {
  const data = JSON.stringify({ index, timestamp, transactions, previousHash });
  // Simplificación: en producción usar SHA-256
  return '0'.repeat(64) + Math.abs(hashCode(data)).toString(16).padStart(64, '0');
}

/**
 * Hash simple para demostración
 */
function hashCode(str) {
  let hash = 0;
  for (let i = 0; i < str.length; i++) {
    const char = str.charCodeAt(i);
    hash = ((hash << 5) - hash) + char;
    hash = hash & hash;
  }
  return hash;
}

// ==============================================================================
// TRANSACCIONES
// ==============================================================================

/**
 * Crea una nueva transacción
 */
async function createTransaction(transactionData) {
  const { from, to, amount, type, metadata = {} } = transactionData;
  
  console.log(`[Blockchain] Creando transacción: ${from} → ${to} (${amount})`);
  
  const transaction = {
    id: `tx_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
    from,
    to,
    amount,
    type,
    metadata,
    timestamp: Date.now(),
    status: 'pending',
    aiAnalysis: null,
  };
  
  // Análisis con IA de la transacción
  if (BLOCKCHAIN_CONFIG.aiEnabled) {
    transaction.aiAnalysis = await analyzeTransaction(transaction);
  }
  
  pendingTransactions.push(transaction);
  
  // Minar bloque si hay suficientes transacciones
  if (pendingTransactions.length >= BLOCKCHAIN_CONFIG.maxTransactionsPerBlock) {
    await mineBlock();
  }
  
  return {
    success: true,
    transaction,
    message: 'Transacción creada exitosamente',
  };
}

/**
 * Analiza una transacción con IA
 */
async function analyzeTransaction(transaction) {
  const prompt = `Analiza la siguiente transacción blockchain:

De: ${transaction.from}
Para: ${transaction.to}
Monto: ${transaction.amount}
Tipo: ${transaction.type}
Metadata: ${JSON.stringify(transaction.metadata)}

Proporciona:
1. Riesgo de fraude (0-100)
2. Patrón detectado
3. Recomendación
4. Puntuación de confianza`;
  
  const result = await aiRouter.callAI(prompt, {
    systemPrompt: 'Eres un analista de blockchain experto. Detecta fraudes y patrones sospechosos.',
    maxTokens: 200,
    temperature: 0.3,
  });
  
  return {
    riskScore: extractRiskScore(result.response),
    pattern: extractPattern(result.response),
    recommendation: extractRecommendation(result.response),
    confidence: extractConfidence(result.response),
    provider: result.provider,
  };
}

/**
 * Extrae puntuación de riesgo del análisis
 */
function extractRiskScore(text) {
  const match = text.match(/(\d+)\s*\/\s*100|riesgo.*?(\d+)/i);
  return match ? parseInt(match[1] || match[2]) : 50;
}

/**
 * Extrae patrón detectado
 */
function extractPattern(text) {
  const match = text.match(/patrón:\s*(.+)/i);
  return match ? match[1].trim() : 'Normal';
}

/**
 * Extrae recomendación
 */
function extractRecommendation(text) {
  const match = text.match(/recomendación:\s*(.+)/i);
  return match ? match[1].trim() : 'Proceder con normalidad';
}

/**
 * Extrae confianza del análisis
 */
function extractConfidence(text) {
  const match = text.match(/confianza:\s*(\d+)%/i);
  return match ? parseInt(match[1]) / 100 : 0.7;
}

// ==============================================================================
// MINERÍA
// ==============================================================================

/**
 * Mina un nuevo bloque
 */
async function mineBlock() {
  if (pendingTransactions.length === 0) {
    return null;
  }
  
  console.log(`[Blockchain] Minando bloque con ${pendingTransactions.length} transacciones`);
  
  const previousBlock = blockchain[blockchain.length - 1];
  const transactions = [...pendingTransactions];
  
  const newBlock = {
    index: blockchain.length,
    timestamp: Date.now(),
    transactions,
    previousHash: previousBlock.hash,
    hash: '',
    nonce: 0,
  };
  
  // Calcular hash
  newBlock.hash = calculateHash(
    newBlock.index,
    newBlock.timestamp,
    newBlock.transactions,
    newBlock.previousHash
  );
  
  // Limpiar transacciones pendientes
  pendingTransactions.length = 0;
  
  // Actualizar estado de transacciones
  transactions.forEach(tx => {
    tx.status = 'confirmed';
    tx.blockIndex = newBlock.index;
  });
  
  blockchain.push(newBlock);
  
  return {
    success: true,
    block: newBlock,
    message: 'Bloque minado exitosamente',
  };
}

/**
 * Obtiene el último bloque
 */
function getLatestBlock() {
  return blockchain[blockchain.length - 1] || null;
}

/**
 * Obtiene toda la blockchain
 */
function getBlockchain() {
  return blockchain.map(block => ({
    index: block.index,
    timestamp: block.timestamp,
    transactions: block.transactions.length,
    hash: block.hash,
    previousHash: block.previousHash,
  }));
}

/**
 * Obtiene una transacción por ID
 */
function getTransaction(txId) {
  for (const block of blockchain) {
    const tx = block.transactions.find(t => t.id === txId);
    if (tx) {
      return {
        ...tx,
        blockIndex: block.index,
        confirmations: blockchain.length - block.index,
      };
    }
  }
  return null;
}

/**
 * Verifica la integridad de la blockchain
 */
function verifyBlockchain() {
  for (let i = 1; i < blockchain.length; i++) {
    const current = blockchain[i];
    const previous = blockchain[i - 1];
    
    if (current.previousHash !== previous.hash) {
      return {
        valid: false,
        error: `Hash mismatch at block ${i}`,
      };
    }
    
    const recalculatedHash = calculateHash(
      current.index,
      current.timestamp,
      current.transactions,
      current.previousHash
    );
    
    if (current.hash !== recalculatedHash) {
      return {
        valid: false,
        error: `Invalid hash at block ${i}`,
      };
    }
  }
  
  return {
    valid: true,
    blocks: blockchain.length,
    message: 'Blockchain integrity verified',
  };
}

// ==============================================================================
// CONTRATOS INTELIGENTES
// ==============================================================================

/**
 * Despliega un contrato inteligente
 */
async function deployContract(contractData) {
  const { name, code, owner, aiEnabled = false } = contractData;
  
  console.log(`[Blockchain] Desplegando contrato: ${name}`);
  
  const contract = {
    id: `contract_${Date.now()}`,
    name,
    code,
    owner,
    aiEnabled,
    status: 'active',
    deployedAt: new Date().toISOString(),
    transactions: [],
  };
  
  // Análisis del contrato con IA
  if (aiEnabled) {
    contract.aiAnalysis = await analyzeContract(code);
  }
  
  smartContracts.set(contract.id, contract);
  
  return {
    success: true,
    contract,
    message: 'Contrato desplegado exitosamente',
  };
}

/**
 * Analiza un contrato inteligente con IA
 */
async function analyzeContract(code) {
  const prompt = `Analiza el siguiente contrato inteligente:

${code}

Proporciona:
1. Vulnerabilidades detectadas
2. Optimizaciones sugeridas
3. Puntuación de seguridad (0-100)
4. Costo estimado de gas`;
  
  const result = await aiRouter.callAI(prompt, {
    systemPrompt: 'Eres un auditor de contratos inteligentes experto. Detecta vulnerabilidades y optimizaciones.',
    maxTokens: 400,
    temperature: 0.3,
  });
  
  return {
    analysis: result.response,
    vulnerabilities: extractVulnerabilities(result.response),
    securityScore: extractSecurityScore(result.response),
    provider: result.provider,
  };
}

/**
 * Extrae vulnerabilidades del análisis
 */
function extractVulnerabilities(text) {
  const vulnerabilities = [];
  
  if (text.toLowerCase().include('reentrancy')) {
    vulnerabilities.push({ type: 'reentrancy', severity: 'high' });
  }
  if (text.toLowerCase().include('overflow')) {
    vulnerabilities.push({ type: 'overflow', severity: 'high' });
  }
  if (text.toLowerCase().include('access control')) {
    vulnerabilities.push({ type: 'access_control', severity: 'medium' });
  }
  
  return vulnerabilities;
}

/**
 * Extrae puntuación de seguridad
 */
function extractSecurityScore(text) {
  const match = text.match(/(\d+)\s*\/\s*100|seguridad.*?(\d+)/i);
  return match ? parseInt(match[1] || match[2]) : 70;
}

/**
 * Ejecuta una función del contrato
 */
async function executeContractFunction(contractId, functionName, params) {
  const contract = smartContracts.get(contractId);
  
  if (!contract) {
    throw new Error(`Contrato no encontrado: ${contractId}`);
  }
  
  console.log(`[Blockchain] Ejecutando ${functionName} en contrato ${contract.name}`);
  
  // Crear transacción
  const tx = await createTransaction({
    from: params.from,
    to: contractId,
    amount: params.amount || 0,
    type: 'contract_call',
    metadata: { function: functionName, params },
  });
  
  contract.transactions.push(tx.id);
  
  return {
    success: true,
    transaction: tx,
    contract: contract.name,
    function: functionName,
  };
}

/**
 * Obtiene todos los contratos desplegados
 */
function getContracts() {
  return Array.from(smartContracts.values()).map(c => ({
    id: c.id,
    name: c.name,
    owner: c.owner,
    status: c.status,
    aiEnabled: c.aiEnabled,
    transactions: c.transactions.length,
    deployedAt: c.deployedAt,
  }));
}

/**
 * Obtiene un contrato por ID
 */
function getContract(contractId) {
  const contract = smartContracts.get(contractId);
  
  if (!contract) {
    throw new Error(`Contrato no encontrado: ${contractId}`);
  }
  
  return contract;
}

// ==============================================================================
// DETECCIÓN DE FRAUDES
// ==============================================================================

/**
 * Detecta patrones de fraude en transacciones
 */
async function detectFraudPatterns(transactions) {
  console.log(`[Blockchain] Analizando ${transactions.length} transacciones para fraude`);
  
  const prompt = `Analiza las siguientes transacciones blockchain y detecta patrones de fraude:

${JSON.stringify(transactions.slice(0, 20))}

Busca:
1. Transacciones sospechosas
2. Patrones inusuales
3. Direcciones de alto riesgo
4. Montos anómalos

Proporciona una lista de transacciones sospechosas con razones.`;
  
  const result = await aiRouter.callAI(prompt, {
    systemPrompt: 'Eres un analista de fraudes blockchain. Detecta patrones sospechosos.',
    maxTokens: 400,
    temperature: 0.3,
  });
  
  return {
    success: true,
    analysis: result.response,
    suspiciousCount: extractSuspiciousCount(result.response),
    provider: result.provider,
    timestamp: new Date().toISOString(),
  };
}

/**
 * Extrae conteo de sospechosos
 */
function extractSuspiciousCount(text) {
  const match = text.match(/(\d+)\s*sospechoso/i);
  return match ? parseInt(match[1]) : 0;
}

// ==============================================================================
// MÉTRICAS
// ==============================================================================

/**
 * Obtiene métricas de la blockchain
 */
function getBlockchainMetrics() {
  const totalTransactions = blockchain.reduce(
    (sum, block) => sum + block.transactions.length, 0
  );
  
  const totalContracts = smartContracts.size;
  
  const avgBlockTime = blockchain.length > 1
    ? (blockchain[blockchain.length - 1].timestamp - blockchain[0].timestamp) / blockchain.length
    : 0;
  
  return {
    blocks: blockchain.length,
    transactions: totalTransactions,
    pendingTransactions: pendingTransactions.length,
    contracts: totalContracts,
    avgBlockTime,
    difficulty: 1,
    timestamp: new Date().toISOString(),
  };
}

// ==============================================================================
// INICIALIZACIÓN
// ==============================================================================

// Crear bloque genesis
createGenesisBlock();

// ==============================================================================
// API ENDPOINTS
// ==============================================================================

/**
 * POST /api/blockchain/transaction
 * Crea una transacción
 */
export async function createTransactionEndpoint(req, res) {
  try {
    const result = await createTransaction(req.body);
    res.json(result);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
}

/**
 * GET /api/blockchain/blocks
 * Lista todos los bloques
 */
export function getBlocksEndpoint(req, res) {
  res.json({
    blocks: getBlockchain(),
    total: blockchain.length,
  });
}

/**
 * GET /api/blockchain/blocks/:index
 * Obtiene un bloque específico
 */
export function getBlockEndpoint(req, res) {
  const index = parseInt(req.params.index);
  const block = blockchain[index];
  
  if (!block) {
    return res.status(404).json({ error: 'Block not found' });
  }
  
  res.json(block);
}

/**
 * GET /api/blockchain/transaction/:id
 * Obtiene una transacción
 */
export function getTransactionEndpoint(req, res) {
  const tx = getTransaction(req.params.id);
  
  if (!tx) {
    return res.status(404).json({ error: 'Transaction not found' });
  }
  
  res.json(tx);
}

/**
 * POST /api/blockchain/mine
 * Mina un nuevo bloque
 */
export async function mineBlockEndpoint(req, res) {
  const result = await mineBlock();
  
  if (!result) {
    return res.status(400).json({ error: 'No transactions to mine' });
  }
  
  res.json(result);
}

/**
 * GET /api/blockchain/verify
 * Verifica integridad de la blockchain
 */
export function verifyBlockchainEndpoint(req, res) {
  res.json(verifyBlockchain());
}

/**
 * POST /api/blockchain/contract
 * Despliega un contrato inteligente
 */
export async function deployContractEndpoint(req, res) {
  try {
    const result = await deployContract(req.body);
    res.json(result);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
}

/**
 * GET /api/blockchain/contracts
 * Lista contratos desplegados
 */
export function getContractsEndpoint(req, res) {
  res.json({
    contracts: getContracts(),
    total: smartContracts.size,
  });
}

/**
 * POST /api/blockchain/contract/:id/execute
 * Ejecuta función de contrato
 */
export async function executeContractEndpoint(req, res) {
  try {
    const result = await executeContractFunction(
      req.params.id,
      req.body.functionName,
      req.body.params
    );
    res.json(result);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
}

/**
 * POST /api/blockchain/fraud-detection
 * Detecta patrones de fraude
 */
export async function detectFraudEndpoint(req, res) {
  const { transactions } = req.body;
  
  if (!transactions) {
    return res.status(400).json({ error: 'Transactions required' });
  }
  
  try {
    const result = await detectFraudPatterns(transactions);
    res.json(result);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
}

/**
 * GET /api/blockchain/metrics
 * Métricas de la blockchain
 */
export function getBlockchainMetricsEndpoint(req, res) {
  res.json(getBlockchainMetrics());
}

/**
 * GET /api/blockchain/status
 * Estado de la blockchain
 */
export function getBlockchainStatus(req, res) {
  res.json({
    status: 'active',
    config: BLOCKCHAIN_CONFIG,
    metrics: getBlockchainMetrics(),
    timestamp: new Date().toISOString(),
  });
}

// ==============================================================================
// EXPORTACIONES
// ==============================================================================

export {
  createTransaction,
  mineBlock,
  getLatestBlock,
  getBlockchain,
  getTransaction,
  verifyBlockchain,
  deployContract,
  executeContractFunction,
  getContracts,
  detectFraudPatterns,
  getBlockchainMetrics,
  BLOCKCHAIN_CONFIG,
};

export default {
  createTransactionEndpoint,
  getBlocksEndpoint,
  getBlockEndpoint,
  getTransactionEndpoint,
  mineBlockEndpoint,
  verifyBlockchainEndpoint,
  deployContractEndpoint,
  getContractsEndpoint,
  executeContractEndpoint,
  detectFraudEndpoint,
  getBlockchainMetricsEndpoint,
  getBlockchainStatus,
  createTransaction,
  mineBlock,
  getLatestBlock,
  getBlockchain,
  getTransaction,
  verifyBlockchain,
  deployContract,
  executeContractFunction,
  getContracts,
  detectFraudPatterns,
  getBlockchainMetrics,
};
