/**
 * PaddleOCR Provider - Baidu Open Source
 * 
 * OCR chino/inglés open source
 * Modelo: PaddleOCR v4
 * 
 * Uso: Reconocimiento de texto en imágenes
 */

const PADDLE_OCR_CONFIG = {
  endpoint: 'https://api.paddlepaddle.org/ocr',
  languages: ['ch', 'en', 'es'],
  model: 'PP-OCRv4',
};

/**
 * Realiza OCR en una imagen usando PaddleOCR
 */
async function recognizeText(imageData, options = {}) {
  const lang = options.lang || 'es';
  
  // En producción, conectar con PaddleOCR local o API
  // Por ahora, usar Tesseract.js como fallback
  if (typeof Tesseract !== 'undefined') {
    return recognizeWithTesseract(imageData, lang);
  }
  
  throw new Error('OCR no disponible');
}

/**
 * Fallback a Tesseract.js
 */
async function recognizeWithTesseract(imageData, lang) {
  const result = await Tesseract.recognize(imageData, lang, {
    logger: m => console.log(m),
  });
  
  return {
    text: result.data.text,
    confidence: result.data.confidence,
    words: result.data.words,
  };
}

export { recognizeText, PADDLE_OCR_CONFIG };
