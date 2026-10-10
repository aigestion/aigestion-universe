# aig Mobile - PWA

Progressive Web App for monitoring and managing AI services on mobile devices.

## Features

- **Dark Theme** - #0a0a1a background, optimized for OLED
- **Bottom Navigation** - Home / Daniela / Hermes / Settings
- **Service Status Cards** - Real-time service monitoring
- **Pull-to-Refresh** - Native-like refresh gesture
- **Offline Indicator** - Shows connection status banner
- **Install Prompt** - Add to home screen as PWA
- **Push Notifications** - Service alerts and updates
- **Background Sync** - Sync service status when back online
- **Responsive** - Mobile-first, scales to tablet/desktop
- **Auto-refresh** - 30-second polling when online

## Install

### Development

```bash
cd mobile-app
# Serve locally
npx serve .
# or
python -m http.server 8090
```

Open `http://localhost:8080` in mobile browser.

### Docker

```bash
docker build -t aig-mobile .
docker run -p 8080:8080 aig-mobile
```

### PWA Install

1. Open the app in Chrome/Safari on mobile
2. Tap "Install" on the banner or use browser menu
3. Add to Home Screen

## Project Structure

```
mobile-app/       # Árbol único de cliente (PWA + pixel/ + phone_deploy/)
├── manifest.json        # PWA manifest
├── sw.js               # Service Worker (pre-cachéa JS + runtime three)
├── index.html          # Main SPA + importmap de three
├── Dockerfile          # nginx:alpine container (cachea .glb 1 año)
├── assets/
│   └── daniela3d.glb   # Avatar 3D de Daniela, 3,2 MB (ver "Avatar 3D")
├── css/
│   └── mobile.css      # Mobile CSS + escenario del avatar
├── js/
│   ├── app.js          # Router, SW, notifications (módulo ES)
│   ├── api.js          # API client (AIGApi)
│   ├── views.js        # View controllers
│   ├── daniela-avatar.js # Motor 3D del avatar (lazy, import dinámico)
│   ├── gev.js          # Puente God's Eye View (postMessage)
│   ├── sensors.js      # Sensores del dispositivo
│   └── notifications.js # Notificaciones de Daniela
├── vendor/three/       # three.js 0.180 vendorizado (sin CDN, funciona offline)
│   ├── build/          # three.module.min.js + three.core.min.js
│   └── examples/jsm/   # GLTFLoader, RoomEnvironment, meshopt_decoder
└── icons/
    ├── icon-192.png    # PWA icon 192px
    └── icon-512.png    # PWA icon 512px
```

## Views

| View | Description |
|------|-------------|
| Home | System stats, service list, recent logs |
| Daniela | Avatar 3D animado + AI assistant profile, conversations |
| Hermes | Gateway status, metrics, logs |
| Settings | App config, notifications, cache |

## Avatar 3D de Daniela

La vista **Daniela** monta `assets/daniela3d.glb` con three.js:

- **Origen:** exportado desde Blender, malla estática de 1,5 M de triángulos y
  79 MB. Se optimizó a **3,2 MB / 374 k triángulos** con `gltf-transform`
  (`--simplify-ratio 0.25` + texturas WebP 2048). Calidad verificada:
  PSNR 39,8 / 40,6 / 45,8 dB sobre las texturas originales.
- **Animación procedural:** el modelo no tiene esqueleto ni morph targets
  (`skins=0`, `animations=0`, `morphTargets=0`), así que no hay lip-sync real.
  `js/daniela-avatar.js` anima respiración, mirada con sacádicas, balanceo de
  postura y un envoltorio de volumen de voz sobre el transform del nodo.
- **Estados:** `idle` · `listening` · `thinking` · `talking`.
- **Voz:** `speak()` usa Web Speech API (offline) y `speakAudio(url)` engancha
  un `AnalyserNode` para sincronizar el movimiento con la amplitud real del
  TTS del servidor.
- **Carga diferida:** three.js (~890 KB) sólo se descarga al abrir la pestaña.
- **Fallback:** sin WebGL se muestra el icono estático en lugar de un hueco.

## API Integration

The app connects to the aig backend at `/api/*`:

- `GET /api/services` - List all services
- `GET /api/services/:id/status` - Service status
- `GET /api/system/stats` - System statistics
- `GET /api/hermes/*` - Hermes gateway
- `GET /api/daniela/*` - Daniela assistant
- `PUT /api/settings` - Update settings

## Icons

Replace placeholder files with actual icons:

```bash
# Generate from source image
convert icon-source.png -resize 192x192 mobile-app/icons/icon-192.png
convert icon-source.png -resize 512x512 mobile-app/icons/icon-512.png
```

## Configuration

Environment variables for Docker:

| Variable | Default | Description |
|----------|---------|-------------|
| `API_URL` | `/api` | Backend API base URL |

## Browser Support

- Chrome 67+
- Safari 11.1+
- Firefox 63+
- Edge 79+
