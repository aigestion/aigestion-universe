/**
 * Qwen Provider - Alibaba Cloud Open Source
 * 
 * Modelos disponibles:
 * - Qwen-72B-Chat (más potente)
 * - Qwen-14B-Chat (balance)
 * - Qwen-7B-Chat (ligero)
 * - Qwen-Turbo (gratuito, rápido)
 * 
 * API: https://dashscope.aliyuncs.com/compatible-mode/v1
 */

const QWEN_CONFIG = {
  endpoint: 'https://dashscope.aliyuncs.com/compatible-mode/v1',
  models: {
    turbo: 'qwen-turbo',      // Gratuito, rápido
    plus: 'qwen-plus',        // Balance
    max: 'qwen-max',          // Más potente
  },
  rateLimit: 100, // requests per minute
};

/**
 * Llama a Qwen API (gratuito con tier free)
 */
async function callQwen(prompt, options = {}) {
  const apiKey = process.env.QWEN_API_KEY || process.env.DASHSCOPE_API_KEY;
  
  if (!apiKey) {
    throw new Error('QWEN_API_KEY no configurada');
  }
  
  const model = options.model || QWEN_CONFIG.models.turbo;
  const systemPrompt = options.systemPrompt || 'Eres Daniela, asistente de IA para AIG. Responde conciso y útil en español.';
  
  const response = await fetch(QWEN_CONFIG.endpoint + '/chat/completions', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${apiKey}`,
    },
    body: JSON.stringify({
      model,
      messages: [
        { role: 'system', content: systemPrompt },
        { role: 'user', content: prompt }
      ],
      temperature: options.temperature || 0.7,
      max_tokens: options.maxTokens || 200,
    }),
  });
  
  if (!response.ok) {
    throw new Error(`Qwen HTTP ${response.status}`);
  }
  
  const data = await response.json();
  return data.choices[0].message.content;
}

export { callQwen, QWEN_CONFIG };
