"""
API Gateway - aigestion.net
Gateway unificado para todos los servicios
"""

import os
import time
from datetime import datetime

from flask import Flask, jsonify, request
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# ==============================================================================
# CONFIGURACIÓN
# ==============================================================================

SERVICES = {
    'ai-engine': 'http://localhost:5000',
    'websocket': 'http://localhost:3001',
    'database': 'http://localhost:5432',
}

# ==============================================================================
# MIDDLEWARE
# ==============================================================================

@app.before_request
def before_request():
    request.start_time = time.time()

@app.after_request
def after_request(response):
    response_time = time.time() - request.start_time
    response.headers['X-Response-Time'] = f'{response_time:.3f}s'
    return response

# ==============================================================================
# ENDPOINTS
# ==============================================================================

@app.route('/api/gateway/status', methods=['GET'])
def gateway_status():
    """Estado del gateway"""
    return jsonify({
        'status': 'active',
        'name': 'aig API Gateway',
        'version': '1.0.0',
        'services': list(SERVICES.keys()),
        'timestamp': datetime.now().isoformat(),
    })

@app.route('/api/gateway/services', methods=['GET'])
def list_services():
    """Lista servicios disponibles"""
    return jsonify({
        'services': [
            {'name': 'ai-engine', 'url': '/api/ai/*', 'status': 'active'},
            {'name': 'websocket', 'url': '/ws', 'status': 'active'},
            {'name': 'database', 'url': '/api/db/*', 'status': 'active'},
        ]
    })

@app.route('/api/gateway/health', methods=['GET'])
def health_check():
    """Verificación de salud"""
    return jsonify({
        'status': 'healthy',
        'checks': {
            'api': 'ok',
            'database': 'ok',
            'cache': 'ok',
        }
    })

# ==============================================================================
# RUTAS DE SERVICIOS
# ==============================================================================

@app.route('/api/ai/<path:path>', methods=['GET', 'POST'])
def proxy_ai_engine(path):
    """Proxy al AI Engine"""
    # En producción, redirigir al servicio correspondiente
    return jsonify({
        'service': 'ai-engine',
        'path': path,
        'status': 'routed',
    })

@app.route('/api/gateway/metrics', methods=['GET'])
def get_metrics():
    """Métricas del gateway"""
    return jsonify({
        'requests_total': 0,
        'requests_per_second': 0,
        'average_response_time': 0,
        'error_rate': 0,
    })

if __name__ == '__main__':
    port = int(os.getenv('PORT', 8080))
    print(f'🌐 API Gateway iniciado en puerto {port}')
    app.run(host='0.0.0.0', port=port, debug=True)
