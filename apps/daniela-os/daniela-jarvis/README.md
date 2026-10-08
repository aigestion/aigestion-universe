# Daniela Jarvis — Desktop Overlay

Jarvis-style transparent holographic overlay for Windows.

## Features
- **Arc Reactor Core** — Animated Three.js holographic center
- **System Widgets** — CPU, RAM, Network, Disk (real-time)
- **Voice Control** — Microphone button with waveform visualizer
- **Quick Actions** — Briefing, Deploy, Chat, Health, Search, Settings
- **Always-on-Top** — Transparent overlay above all windows
- **Global Hotkey** — Ctrl+Shift+J to toggle

## Quick Start

```bash
cd daniela-jarvis
npm install
npm start
```

## Development

```bash
set ELECTRON_DEV=1
npm start
```

## Backend (Optional)

For real-time system metrics:

```bash
cd backend
pip install fastapi uvicorn psutil
python server.py
```

## Build

```bash
npm run build
```

Creates installer in `dist/`.

## Architecture

- `main.js` — Electron main process
- `overlay/` — HTML/CSS/JS frontend
- `backend/` — FastAPI system monitor
