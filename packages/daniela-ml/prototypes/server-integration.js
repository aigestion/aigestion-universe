/**
 * Servidor Maestro Unificado - aigestion.net
 * 
 * Punto de entrada único para todo el ecosistema:
 * - Daniela OS (PC) - Puerto 5000
 * - God's Eye View (Web) - Puerto 4173
 * - Android App (Pixel 8a) - ADB
 * - AI Router (8 providers)
 * 
 * Puerto: 3000
 */

import express from 'express';
import cors from 'cors';
import { exec } from 'child_process';
import { promisify } from 'util';

const execAsync = promisify(exec);

const app = express();
const PORT = process.env.PORT || 3000;

app.use(cors());
app.use(express.json());

// ==============================================================================
// ESTADO GLOBAL
// ==============================================================================

const estadoGlobal = {
  nombre: 'aigestion.net - Servidor Maestro',
  version: '1.0.0',
  estado: 'activo',
  componentes: {
    danielaOS: { estado: 'desconectado', puerto: 5000, url: 'http://localhost:5000' },
    godsEyeView: { estado: 'desconectado', puerto: 4173, url: 'http://localhost:4173' },
    androidApp: { estado: 'desconectado', dispositivo: 'Pixel 8a', conexion: 'adb' },
    aiRouter: { estado: 'activo', providers: 8, modelos: 200 },
  },
  metricas: {
    solicitudesTotales: 0,
    tokensTotales: 0,
    costo: 0,
  },
  modulos: [
    'enrutador-ia',
    'motor-decision',
    'automatizacion-procesos',
    'analitica-tiempo-real',
    'procesamiento-documentos',
    'generacion-contenido',
    'analisis-sentimientos',
    'recomendaciones',
    'asistente-virtual',
    'personalizacion-ia',
    'computacion-borde',
    'ide-assistant',
    'mantenimiento-predictivo',
    'motor-recomendaciones',
    'procesamiento-documentos',
    'analisis-sentimientos',
    'generacion-contenido',
    'recomendaciones',
    'asistente-virtual',
    'personalizacion-ia',
    'computacion-borde',
    'ide-assistant',
    'mantenimiento-predictivo',
    'motor-recomendaciones',
  ],
};

// ==============================================================================
// VERIFICACIÓN DE COMPONENTES
// ==============================================================================

async function verificarComponentes() {
  // Verificar Daniela OS
  try {
    const res = await fetch('http://localhost:5000/api/status', {
      signal: AbortSignal.timeout(2000),
    });
    if (res.ok) {
      estadoGlobal.componentes.danielaOS.estado = 'conectado';
    }
  } catch {
    estadoGlobal.componentes.danielaOS.estado = 'desconectado';
  }

  // Verificar God's Eye View
  try {
    const res = await fetch('http://localhost:4173/', {
      signal: AbortSignal.timeout(2000),
    });
    if (res.ok) {
      estadoGlobal.componentes.godsEyeView.estado = 'conectado';
    }
  } catch {
    estadoGlobal.componentes.godsEyeView.estado = 'desconectado';
  }

  // Verificar Android
  try {
    const { stdout } = await execAsync('adb devices');
    if (stdout.includes('device')) {
      estadoGlobal.componentes.androidApp.estado = 'conectado';
    }
  } catch {
    estadoGlobal.componentes.androidApp.estado = 'desconectado';
  }
}

// Verificar cada 30 segundos
setInterval(verificarComponentes, 30000);
verificarComponentes();

// ==============================================================================
// API ENDPOINTS
// ==============================================================================

/**
 * GET /api/estado
 * Estado completo del ecosistema
 */
app.get('/api/estado', (req, res) => {
  estadoGlobal.metricas.solicitudesTotales++;
  res.json(estadoGlobal);
});

/**
 * GET /api/modulos
 * Lista de módulos disponibles
 */
app.get('/api/modulos', (req, res) => {
  res.json({
    modulos: estadoGlobal.modulos,
    total: estadoGlobal.modulos.length,
  });
});

/**
 * POST /api/chat
 * Chat con IA (usa el enrutador)
 */
app.post('/api/chat', async (req, res) => {
  const { mensaje, modulo = 'general' } = req.body;
  
  if (!mensaje) {
    return res.status(400).json({ error: 'Mensaje requerido' });
  }

  try {
    const { default: aiRouter } = await import('./ai_router.js');
    const result = await aiRouter.callAI(mensaje, {
      systemPrompt: `Eres un asistente de ${modulo} para aigestion.net. Responde en español.`,
    });

    estadoGlobal.metricas.solicitudesTotales++;
    if (result.usage) {
      estadoGlobal.metricas.tokensTotales += result.usage.total_tokens || 0;
    }

    res.json({
      exito: true,
      respuesta: result.response,
      modulo,
      proveedor: result.provider,
      timestamp: new Date().toISOString(),
    });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

/**
 * POST /api/comando
 * Envía comando a Daniela OS
 */
app.post('/api/comando', async (req, res) => {
  const { comando, contexto = {} } = req.body;
  
  if (!comando) {
    return res.status(400).json({ error: 'Comando requerido' });
  }

  try {
    const respuesta = await fetch('http://localhost:5000/api/command', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ command: comando, context: contexto }),
    });

    const datos = await respuesta.json();
    res.json({
      exito: true,
      comando,
      respuesta: datos,
      timestamp: new Date().toISOString(),
    });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

/**
 * GET /api/android/dispositivos
 * Lista dispositivos Android conectados
 */
app.get('/api/android/dispositivos', async (req, res) => {
  try {
    const { stdout } = await execAsync('adb devices -l');
    const dispositivos = stdout
      .trim()
      .split('\n')
      .slice(1)
      .map(linea => {
        const partes = linea.trim().split(/\s+/);
        return {
          id: partes[0],
          estado: partes[1],
          detalles: partes.slice(2).join(' '),
        };
      });

    res.json({ dispositivos, total: dispositivos.length });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

/**
 * POST /api/android/comando
 * Ejecuta comando ADB en el dispositivo
 */
app.post('/api/android/comando', async (req, res) => {
  const { comando, deviceId } = req.body;
  
  if (!comando) {
    return res.status(400).json({ error: 'Comando requerido' });
  }

  try {
    const comandoCompleto = deviceId 
      ? `adb -s ${deviceId} ${comando}`
      : `adb ${comando}`;
    
    const { stdout, stderr } = await execAsync(comandoCompleto);
    res.json({
      exito: true,
      comando,
      salida: stdout,
      error: stderr || null,
    });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

/**
 * GET /api/salud
 * Verificación de salud del sistema
 */
app.get('/api/salud', (req, res) => {
  const componentes = Object.entries(estadoGlobal.componentes).map(([nombre, comp]) => ({
    nombre,
    estado: comp.estado,
  }));

  const todosConectados = componentes.every(c => c.estado === 'conectado');

  res.json({
    estado: todosConectados ? 'saludable' : 'degradado',
    componentes,
    timestamp: new Date().toISOString(),
  });
});

/**
 * GET /api/metricas
 * Métricas del sistema
 */
app.get('/api/metricas', (req, res) => {
  res.json({
    ...estadoGlobal.metricas,
    memoria: process.memoryUsage(),
    uptime: process.uptime(),
    timestamp: new Date().toISOString(),
  });
});

// ==============================================================================
// INICIAR SERVIDOR
// ==============================================================================

app.listen(PORT, () => {
  console.log('═══════════════════════════════════════════════════════════');
  console.log('  🚀 aigestion.net - Servidor de Integración Completa');
  console.log('═══════════════════════════════════════════════════════════');
  console.log(`  📡 URL: http://localhost:${PORT}`);
  console.log(`  💰 Costo: €0/mes`);
  console.log(`  🤖 Módulos: 24`);
  console.log(`  🌐 Idioma: Español`);
  console.log('═══════════════════════════════════════════════════════════');
  console.log('');
  console.log('  Endpoints disponibles:');
  console.log('    GET  /api/estado              - Estado del servidor');
  console.log('    GET  /api/modulos             - Módulos disponibles');
  console.log('    POST /api/chat                - Chat con IA');
  console.log('    POST /api/comando             - Comando a Daniela OS');
  console.log('    GET  /api/android/dispositivos - Dispositivos Android');
  console.log('    POST /api/android/comando     - Comando ADB');
  console.log('    GET  /api/salud               - Verificación de salud');
  console.log('    GET  /api/metricas            - Métricas del sistema');
  console.log('');
});

export default app;
