# aig Metaverse v1.0.0

## Tu Oficina Virtual en el Metaverso

### Inicio Rapido

```bash
# Instalar dependencias
npm install -g ws
# o
npm install

# Iniciar servidor
node metaverse_server.js
```

El servidor arranca en `http://localhost:7777`

### Acceso

- **Metaverse Web**: http://localhost:7777/metaverse.html
- **Status API**: http://localhost:7777/api/status
- **Usuarios Online**: http://localhost:7777/api/users

### Zonas Disponibles

1. **Plaza Central** - Edificios representando cada modulo de aig
2. **Torre Neural** - Centro de procesamiento IA con anillos holograficos
3. **Auditorio Holografico** - Sala de reuniones y presentaciones
4. **Jardin Digital** - Espacio de relax con arboles digitales
5. **Daniela Hub** - Avatar holografico de tu asistente AI

### Controles

- **WASD / Flechas**: Mover avatar
- **Raton + Click**: Rotar camara (OrbitControls)
- **Scroll**: Zoom
- **Enter**: Enviar mensaje de chat

### Features

- Multiusuario en tiempo real (WebSocket)
- 5 zonas 3D interactivas
- Chat global con historial
- Sistema de emotes
- Cambio de nombre de usuario
- Transicion entre zonas con portales
- FPS counter y estadisticas
- Avatares con colores personalizados
- Labels flotantes con nombres

### Decentraland Worlds

La carpeta `decentraland/` contiene la escena lista para desplegar en Decentraland Worlds (gratis):

```bash
cd decentraland
npm install -g decentraland
dcl deploy
```

Acceso tras deploy: `https://play.decentraland.org/?realm=aig.dcl.eth`

### Stack Tecnologico

- **Frontend**: Three.js r128, HTML5 Canvas, CSS3
- **Backend**: Node.js, WebSocket (ws)
- **3D**: WebGL, OrbitControls
- **Fonts**: Orbitron, Rajdhani (Google Fonts)

---
aig 2026 - El futuro de la gestoria ya esta aqui.
