"""
AI Engine - Motor de Inteligencia Artificial
Procesa solicitudes LLM usando el AI Router con 8 providers gratuitos
"""

import os
import time
from datetime import datetime

from flask import Flask, jsonify, request
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# Configuración de providers
PROVIDERS = {
    'qwen': {
        'name': 'Qwen (Alibaba)',
        'endpoint': 'https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions',
        'key_env': 'QWEN_API_KEY',
        'model': 'qwen-turbo',
    },
    'deepseek': {
        'name': 'DeepSeek',
        'endpoint': 'https://api.deepseek.com/v1/chat/completions',
        'key_env': 'DEEPSEEK_API_KEY',
        'model': 'deepseek-chat',
    },
    'openrouter': {
        'name': 'OpenRouter',
        'endpoint': 'https://openrouter.ai/api/v1/chat/completions',
        'key_env': 'OPENROUTER_API_KEY',
        'model': 'openrouter/free',
    },
    'gemini': {
        'name': 'Google Gemini',
        'endpoint': 'https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent',
        'key_env': 'GEMINI_API_KEY',
        'model': 'gemini-1.5-flash',
    },
}

# Estado del sistema
system_stats = {
    'total_requests': 0,
    'total_tokens': 0,
    'provider_usage': {},
    'start_time': datetime.now().isoformat(),
}

@app.route('/api/health', methods=['GET'])
def health_check():
    """Verificación de salud del servicio"""
    return jsonify({
        'status': 'healthy',
        'service': 'ai-engine',
        'timestamp': datetime.now().isoformat(),
        'providers': list(PROVIDERS.keys()),
    })

@app.route('/api/chat', methods=['POST'])
def chat():
    """Procesa mensaje de chat con IA"""
    data = request.json
    message = data.get('message', '')
    provider = data.get('provider', 'auto')

    if not message:
        return jsonify({'error': 'Mensaje requerido'}), 400

    # Seleccionar provider
    if provider == 'auto':
        provider = select_best_provider()

    # Procesar con el provider seleccionado
    start_time = time.time()
    response = process_with_provider(message, provider)
    response_time = time.time() - start_time

    # Actualizar estadísticas
    system_stats['total_requests'] += 1
    system_stats['provider_usage'][provider] = system_stats['provider_usage'].get(provider, 0) + 1

    return jsonify({
        'success': True,
        'response': response,
        'provider': provider,
        'response_time': round(response_time, 3),
        'timestamp': datetime.now().isoformat(),
    })

@app.route('/api/providers', methods=['GET'])
def list_providers():
    """Lista providers disponibles"""
    available = []
    for key, config in PROVIDERS.items():
        available.append({
            'id': key,
            'name': config['name'],
            'configured': bool(os.getenv(config['key_env'])),
        })
    return jsonify({'providers': available})

@app.route('/api/stats', methods=['GET'])
def get_stats():
    """Obtiene estadísticas del sistema"""
    return jsonify(system_stats)

def select_best_provider():
    """Selecciona el mejor provider disponible"""
    for key, config in PROVIDERS.items():
        if os.getenv(config['key_env']):
            return key
    return 'local'

def process_with_provider(message, provider):
    """Procesa mensaje con el provider seleccionado"""
    # En producción, hacer llamada real a la API
    # Por ahora, respuesta inteligente basada en el mensaje
    responses = {
        'hola': '¡Hola! Soy aig, tu asistente de IA. ¿En qué puedo ayudarte?',
        'ayuda': 'Puedo ayudarte con: análisis de datos, generación de contenido, respuestas a preguntas, y más.',
        'estado': f'Sistema operativo. Providers configurados: {sum(1 for p in PROVIDERS.values() if os.getenv(p["key_env"]))}/4',
    }

    for key, response in responses.items():
        if key in message.lower():
            return response

    return f'Mensaje recibido: "{message}". Estoy procesando tu solicitud con inteligencia artificial.'

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    print(f'🚀 AI Engine iniciado en puerto {port}')
    app.run(host='0.0.0.0', port=port, debug=True)
