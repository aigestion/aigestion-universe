/**
 * AIGestion Metaverse Server
 * WebSocket multiusuario para el metaverso web propio
 * v1.0.0 - 2026
 */

const WebSocket = require('ws');
const http = require('http');
const fs = require('fs');
const path = require('path');

const PORT = process.env.METAVERSE_PORT || 7777;
const MAX_USERS = 100;

// Estado del mundo
const world = {
  users: new Map(), // ws -> userData
  objects: new Map(), // objectId -> objectData
  chatHistory: [],
  startTime: Date.now()
};

// Colores para avatares
const AVATAR_COLORS = [
  '#00f0ff', '#ff00ff', '#00ff88', '#ffaa00', '#ff4444',
  '#4488ff', '#ff88ff', '#88ff44', '#ff8844', '#44ff88'
];

// Nombres de usuario por defecto
const DEFAULT_NAMES = [
  'Usuario', 'Invitado', 'Viajero', 'Explorador', 'Visitante',
  'Navegante', 'Pionero', 'Visitante', 'Turista', 'Aventurero'
];

function generateId() {
  return Math.random().toString(36).substring(2, 10) + Date.now().toString(36);
}

function getRandomColor() {
  return AVATAR_COLORS[Math.floor(Math.random() * AVATAR_COLORS.length)];
}

function getRandomName() {
  return DEFAULT_NAMES[Math.floor(Math.random() * DEFAULT_NAMES.length)] + '_' + Math.floor(Math.random() * 999);
}

// Crear servidor HTTP para servir archivos estáticos del metaverso
const server = http.createServer((req, res) => {
  // CORS headers
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

  if (req.method === 'OPTIONS') {
    res.writeHead(200);
    res.end();
    return;
  }

  // API endpoints
  if (req.url === '/api/status') {
    res.writeHead(200, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify({
      online: true,
      users: world.users.size,
      maxUsers: MAX_USERS,
      uptime: Date.now() - world.startTime,
      version: '1.0.0'
    }));
    return;
  }

  if (req.url === '/api/users') {
    const userList = Array.from(world.users.values()).map(u => ({
      id: u.id,
      name: u.name,
      color: u.color,
      position: u.position,
      zone: u.zone
    }));
    res.writeHead(200, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify(userList));
    return;
  }

  // Servir archivos estáticos
  let filePath = req.url === '/' ? '/metaverse.html' : req.url;
  const ext = path.extname(filePath);
  const contentTypes = {
    '.html': 'text/html',
    '.js': 'application/javascript',
    '.css': 'text/css',
    '.json': 'application/json',
    '.png': 'image/png',
    '.jpg': 'image/jpeg',
    '.gif': 'image/gif',
    '.svg': 'image/svg+xml',
    '.ico': 'image/x-icon'
  };

  const fullPath = path.join(__dirname, 'static', filePath);

  fs.readFile(fullPath, (err, data) => {
    if (err) {
      res.writeHead(404, { 'Content-Type': 'text/plain' });
      res.end('Not Found');
      return;
    }
    res.writeHead(200, { 'Content-Type': contentTypes[ext] || 'application/octet-stream' });
    res.end(data);
  });
});

// WebSocket server
const wss = new WebSocket.Server({ server });

wss.on('connection', (ws, req) => {
  const clientIp = req.socket.remoteAddress;
  console.log(`[METAVERSE] Nueva conexion desde ${clientIp}`);

  if (world.users.size >= MAX_USERS) {
    ws.send(JSON.stringify({
      type: 'error',
      message: 'Servidor lleno. Maximo 100 usuarios.'
    }));
    ws.close();
    return;
  }

  const userId = generateId();
  const userData = {
    id: userId,
    name: getRandomName(),
    color: getRandomColor(),
    position: { x: 0, y: 0, z: 0 },
    rotation: { x: 0, y: 0, z: 0 },
    zone: 'plaza-central',
    connectedAt: Date.now(),
    ws: ws
  };

  world.users.set(ws, userData);

  // Enviar bienvenida
  ws.send(JSON.stringify({
    type: 'init',
    userId: userId,
    name: userData.name,
    color: userData.color,
    position: userData.position,
    usersOnline: world.users.size,
    chatHistory: world.chatHistory.slice(-50) // Ultimos 50 mensajes
  }));

  // Notificar a otros usuarios
  broadcast({
    type: 'user-joined',
    userId: userId,
    name: userData.name,
    color: userData.color,
    position: userData.position
  }, ws);

  // Manejar mensajes
  ws.on('message', (message) => {
    try {
      const data = JSON.parse(message);
      handleMessage(ws, data);
    } catch (e) {
      console.error('[METAVERSE] Error parsing message:', e.message);
    }
  });

  ws.on('close', () => {
    const user = world.users.get(ws);
    if (user) {
      console.log(`[METAVERSE] Desconectado: ${user.name}`);
      world.users.delete(ws);
      broadcast({
        type: 'user-left',
        userId: user.id,
        name: user.name
      });
    }
  });

  ws.on('error', (err) => {
    console.error('[METAVERSE] WebSocket error:', err.message);
  });
});

function handleMessage(ws, data) {
  const user = world.users.get(ws);
  if (!user) return;

  switch (data.type) {
    case 'position':
      user.position = data.position;
      user.rotation = data.rotation || user.rotation;
      broadcast({
        type: 'user-moved',
        userId: user.id,
        position: user.position,
        rotation: user.rotation
      }, ws);
      break;

    case 'chat':
      const chatMsg = {
        type: 'chat',
        userId: user.id,
        name: user.name,
        color: user.color,
        message: data.message.substring(0, 500), // Max 500 chars
        timestamp: Date.now()
      };
      world.chatHistory.push(chatMsg);
      if (world.chatHistory.length > 500) {
        world.chatHistory.shift();
      }
      broadcast(chatMsg);
      break;

    case 'name-change':
      const oldName = user.name;
      user.name = data.name.substring(0, 20).replace(/[^\w\s]/g, '');
      broadcast({
        type: 'name-changed',
        userId: user.id,
        oldName: oldName,
        newName: user.name
      });
      break;

    case 'zone-change':
      user.zone = data.zone;
      broadcast({
        type: 'user-zone',
        userId: user.id,
        zone: data.zone
      });
      break;

    case 'emote':
      broadcast({
        type: 'emote',
        userId: user.id,
        name: user.name,
        emote: data.emote
      });
      break;

    case 'object-interact':
      broadcast({
        type: 'object-interact',
        userId: user.id,
        objectId: data.objectId,
        action: data.action
      });
      break;

    case 'ping':
      ws.send(JSON.stringify({ type: 'pong', timestamp: Date.now() }));
      break;

    default:
      console.log('[METAVERSE] Unknown message type:', data.type);
  }
}

function broadcast(data, excludeWs = null) {
  const message = JSON.stringify(data);
  world.users.forEach((user, ws) => {
    if (ws !== excludeWs && ws.readyState === WebSocket.OPEN) {
      ws.send(message);
    }
  });
}

// Heartbeat para mantener conexiones vivas
setInterval(() => {
  world.users.forEach((user, ws) => {
    if (ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify({
        type: 'heartbeat',
        usersOnline: world.users.size,
        timestamp: Date.now()
      }));
    }
  });
}, 30000);

// Stats logging cada 5 minutos
setInterval(() => {
  console.log(`[METAVERSE STATS] Usuarios online: ${world.users.size}, Uptime: ${Math.floor((Date.now() - world.startTime) / 60000)}min`);
}, 300000);

server.listen(PORT, () => {
  console.log(`
========================================
  AIGESTION METAVERSE SERVER v1.0.0
========================================
  Puerto: ${PORT}
  Max usuarios: ${MAX_USERS}
  WebSocket: ws://localhost:${PORT}
  HTTP: http://localhost:${PORT}
  
  Zonas disponibles:
    - plaza-central
    - torre-neural (oficina virtual)
    - auditorio-holografico
    - jardin-digital
    - mercado-nft
========================================
  `);
});

module.exports = { server, wss, world };
