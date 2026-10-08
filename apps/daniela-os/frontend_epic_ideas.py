#!/usr/bin/env python3
"""
AIGestion Frontend Audit & Epic Ideas Module
============================================
Comprehensive audit of all frontend files (HTML, CSS, JS) in the codebase,
with epic ideas for improvement and a phased roadmap.

Author: Daniela OS // AIGestion
"""

import json
import os
from dataclasses import asdict, dataclass, field

# ==============================================================================
# DATA STRUCTURES
# ==============================================================================


@dataclass
class FrontendFile:
    """Represents a single frontend file in the codebase."""

    path: str
    file_type: str  # html, js, css
    lines: int
    role: str  # main_ui, landing, 3d_experience, mobile, extension, server, module
    status: str  # production, partial, placeholder, stub
    description: str
    key_features: list[str] = field(default_factory=list)
    issues: list[str] = field(default_factory=list)


@dataclass
class EpicIdea:
    """An epic improvement idea for the frontend."""

    id: str
    title: str
    category: str  # architecture, ui_ux, agent_integration, realtime, metaverse, mobile, marketing
    priority: str  # critical, high, medium, low
    effort: str  # S, M, L, XL
    description: str
    files_affected: list[str] = field(default_factory=list)
    dependencies: list[str] = field(default_factory=list)
    impact: str = ""


@dataclass
class RoadmapPhase:
    """A phase in the implementation roadmap."""

    phase: int
    name: str
    duration_weeks: int
    ideas: list[str]  # idea IDs
    goal: str


# ==============================================================================
# FRONTEND FILE AUDIT
# ==============================================================================

FILE_AUDIT: list[FrontendFile] = [
    FrontendFile(
        path="index.html",
        file_type="html",
        lines=29,
        role="landing",
        status="partial",
        description="Minimal landing page. Dark bg card, AIGestion.net title, tagline, 3 service items. No JS, no links to app.",
        key_features=["Dark theme", "Service list"],
        issues=[
            "No navigation to app",
            "No JS",
            "No SEO meta tags",
            "No responsive design",
            "Not connected to brand kit",
        ],
    ),
    FrontendFile(
        path="templates/index.html",
        file_type="html",
        lines=1,
        role="redirect",
        status="placeholder",
        description="Single line redirect to Termux path. Dead link on any non-Termux system.",
        key_features=[],
        issues=[
            "Points to /data/data/com.termux/... (dead on PC)",
            "No fallback",
            "No meta refresh or JS redirect",
        ],
    ),
    FrontendFile(
        path="full_ui_v2.html",
        file_type="html",
        lines=530,
        role="main_ui",
        status="production",
        description="Main Daniela OS UI. Cyberpunk HUD with Three.js 3D particle avatar (420 particles, cyan+magenta). Chat with proposal cards. Gemini dock. Speech synthesis. Camera toggle. File upload.",
        key_features=[
            "Three.js particle avatar",
            "Chat interface",
            "Proposal cards (approve/reject)",
            "Speech synthesis API",
            "Camera getUserMedia",
            "File upload",
            "Dream ideas system",
            "Fetch /api/chat",
        ],
        issues=[
            "Monolithic: 530 lines inline CSS+JS",
            "No CSS extraction",
            "No component reuse",
            "Hardcoded dream ideas",
            "No agent status display",
            "No real-time updates",
            "Colors differ from brand kit",
        ],
    ),
    FrontendFile(
        path="templates/index_sovereign_master.html",
        file_type="html",
        lines=378,
        role="mobile",
        status="production",
        description="Mobile-first core UI. Canvas 2D neural sphere (120 points). Draggable PIP camera. Popup menus. Live conversational mode (red button). API: /api/chat, /api/tts, /api/stt, /api/camera/snap.",
        key_features=[
            "100dvh mobile layout",
            "Safe-area-inset support",
            "Canvas 2D neural sphere",
            "Draggable PIP camera window",
            "Touch event support",
            "Live conversation mode",
            "STT/TTS via API",
            "Popup menu system",
        ],
        issues=[
            "No connection to full_ui_v2.html features",
            "Separate codebase from desktop UI",
            "No shared components",
            "Missing agent squad integration",
        ],
    ),
    FrontendFile(
        path="static/landing.html",
        file_type="html",
        lines=621,
        role="landing",
        status="production",
        description="Full marketing page. Three.js 3D neural network (10 nodes, raycaster click). Features grid. Modules grid. Pricing tiers. Demo chat (keyword matching). VR badge.",
        key_features=[
            "Three.js neural network visualization",
            "Raycaster node click → popup",
            "6 feature cards",
            "10 module tags",
            "3 pricing tiers (Free/Pro/Enterprise)",
            "Demo chat with keyword responses",
            "VR/WebXR badge",
            "Responsive media queries",
        ],
        issues=[
            "Demo chat is fake (keyword matching, not AI)",
            "Stats are static (10+, 10x, 24/7)",
            "No link to actual app/dashboard",
            "No real backend connection",
            "Pricing not wired to billing system",
            "CSS inline (621 lines)",
        ],
    ),
    FrontendFile(
        path="static/neural_city.html",
        file_type="html",
        lines=631,
        role="3d_experience",
        status="production",
        description="3D metaverse city. Ten buildings representing AI modules. Roads, vehicles, drones, stars. OrbitControls. Building info cards. Minimap. Decentraland integration.",
        key_features=[
            "Three.js city with 10 module buildings",
            "OrbitControls + auto-rotate",
            "Animated vehicles (20) and drones (15)",
            "Raycaster building selection",
            "Building info cards with stats",
            "Minimap with player position",
            "Decentraland link (-25,42)",
            "Loading screen with progress",
            "VR support (WebXR)",
        ],
        issues=[
            "No connection to real agent data",
            "Stats are hardcoded",
            "No multi-user (unlike metaverse.html)",
            "No link back to app",
            "Standalone page, not integrated",
        ],
    ),
    FrontendFile(
        path="static/daniela_hologram.html",
        file_type="html",
        lines=460,
        role="3d_experience",
        status="production",
        description="3D holographic avatar. Head with jaw (lip-sync), eyes (blink), hair, neck, shoulders. Scan line effect. Hologram platform. Speech synthesis. Voice recognition.",
        key_features=[
            "Three.js humanoid hologram",
            "Lip-sync animation (jaw movement)",
            "Eye blink animation",
            "Scan line holographic effect",
            "Platform with rings + light beam",
            "Speech synthesis (es-ES)",
            "Voice recognition (webkitSpeechRecognition)",
            "Keyword-based responses",
            "Mouse-tracking head rotation",
            "Glitch effect",
        ],
        issues=[
            "Responses are keyword-based, not AI",
            "No backend connection",
            "No integration with full_ui_v2.html",
            "Standalone page",
            "No TTS voice selection",
        ],
    ),
    FrontendFile(
        path="static/datacenter_live.html",
        file_type="html",
        lines=404,
        role="3d_experience",
        status="production",
        description="3D globe visualization. Wireframe earth with atmosphere shader. 10 region nodes (lat/lon). Animated data packets on bezier curves. HUD with real-time counters.",
        key_features=[
            "Three.js globe with atmosphere shader",
            "Lat/lon to 3D position conversion",
            "10 region nodes with glow",
            "Animated data packets on bezier curves",
            "HUD: total requests, system status, traffic by region, active modules",
            "Real-time counter updates (setInterval)",
            "Star field background",
            "Mouse-tracking rotation",
        ],
        issues=[
            "Data is all fake (random increments)",
            "No WebSocket for real-time data",
            "No connection to actual backend metrics",
            "Standalone page",
            "No agent status",
        ],
    ),
    FrontendFile(
        path="static/metaverse.html",
        file_type="html",
        lines=1431,
        role="metaverse",
        status="production",
        description="Multi-user metaverse. 5 zones (Plaza, Torre, Auditorio, Jardin, Daniela Hub). WebSocket connection. Avatars. Chat. Emotes. Zone portals.",
        key_features=[
            "Three.js 5-zone metaverse",
            "WebSocket real-time sync",
            "User avatars (self + remote)",
            "Real-time chat with history",
            "Emote system (wave, dance, clap, think, heart)",
            "Zone portals (torus + particles)",
            "Loading screen + name modal",
            "FPS counter",
            "Connection status indicator",
            "WASD movement",
            "CanvasTexture labels",
        ],
        issues=[
            "No connection to agent system",
            "No AI NPCs (only user avatars)",
            "No persistence (zones reset on reload)",
            "No admin controls",
            "Requires metaverse_server.js running",
            "Large monolithic file",
        ],
    ),
    FrontendFile(
        path="view_3d_office.html",
        file_type="html",
        lines=1393,
        role="3d_experience",
        status="production",
        description="Massive 3D office. 10 blocks of features (50+ items). GLTF loader. Swarm lasers, task orbs, vector cloud, security scanner, dolly zoom, cyber vision, FPS mode, day/night, emergency dome, audio visualizer, data rain, holographic keyboard, video screen, positional 3D audio, monorepo graph, mic recording, Android twin, ping display, media studio, drones, plasma, firewall, radar, gamepad, task stack, ventures 3D, git deploy, quantum ring.",
        key_features=[
            "Three.js + GLTFLoader + OrbitControls + Tween.js",
            "GLTF model loading (oficina3d.glb, daniela3d.glb)",
            "50+ interactive 3D features across 10 blocks",
            "Positional 3D audio (AudioListener + PositionalAudio)",
            "WebRTC mic recording → Flask backend",
            "CanvasTexture live log screens",
            "Raycaster → swarm dispatch",
            "FPS WASD movement",
            "Day/night cycle (real time)",
            "Gamepad API support",
            "Radar minimap (Canvas2D)",
            "Monorepo graph 3D visualization",
            "Video texture screens",
            "Emergency dome shield",
            "Data rain particles",
            "Holographic keyboard",
        ],
        issues=[
            "EXTREMELY monolithic: 1393 lines, 10 script blocks",
            "No code organization",
            "Hardcoded local paths (C:/Users/Alejandro/Downloads/)",
            "Hardcoded backend IP (192.168.1.133:5059)",
            "No error handling for missing GLTF files",
            "No mobile support",
            "No loading state management",
            "Impossible to maintain without refactoring",
        ],
    ),
    FrontendFile(
        path="chrome-extension/sidepanel.html",
        file_type="html",
        lines=22,
        role="extension",
        status="partial",
        description="Chrome extension sidepanel. 2 buttons (Analyze Tab, Extract Graph). Output div.",
        key_features=[
            "Chrome sidePanel API",
            "Tab content extraction",
            "Gemini integration via localhost:8085",
        ],
        issues=["Hardcoded localhost:8085", "Only 2 features", "No UI polish", "No error recovery"],
    ),
    FrontendFile(
        path="chrome-extension/sidepanel.js",
        file_type="js",
        lines=27,
        role="extension",
        status="partial",
        description="Gets active tab DOM innerText, sends to localhost:8085/api/chat, displays response.",
        key_features=[
            "chrome.tabs.query",
            "chrome.scripting.executeScript",
            "Fetch to local backend",
        ],
        issues=["Hardcoded localhost:8085", "No streaming", "4KB text limit", "No auth"],
    ),
    FrontendFile(
        path="chrome-extension/background.js",
        file_type="js",
        lines=3,
        role="extension",
        status="production",
        description="Sets sidePanel behavior (openPanelOnActionClick).",
        key_features=["chrome.sidePanel.setPanelBehavior"],
        issues=["Minimal, could have more background logic"],
    ),
    FrontendFile(
        path="app.js",
        file_type="js",
        lines=187,
        role="module",
        status="production",
        description="Companion JS for full_ui_v2.html. Speech recognition (es-ES, continuous). Camera PIP (front/back). Sentry mode (captures frames every 10s). Backend communication.",
        key_features=[
            "SpeechRecognition API (es-ES)",
            "getUserMedia camera (front/back)",
            "Sentry mode (interval frame capture)",
            "Neural audio playback",
            "Silence detection timer",
        ],
        issues=[
            "Not modular (IIFE, no exports)",
            "Couples to specific DOM IDs",
            "No error recovery for STT",
            "Sentry interval is hardcoded 10s",
        ],
    ),
    FrontendFile(
        path="metaverse_server.js",
        file_type="js",
        lines=318,
        role="server",
        status="production",
        description="Node.js WebSocket server for metaverse. Multi-user world state. Chat history. User management. Static file serving.",
        key_features=[
            "WebSocket (ws) server",
            "HTTP static file server",
            "User management (100 max)",
            "Chat history (500 messages)",
            "Position/rotation sync",
            "Zone change broadcast",
            "Emote broadcast",
            "Heartbeat (30s)",
            "REST API (/api/status, /api/users)",
            "Auto-reconnect on client side",
        ],
        issues=[
            "No persistence (state lost on restart)",
            "No auth",
            "No rate limiting",
            "No SSL/TLS",
            "No admin controls",
            "No room/zone isolation",
        ],
    ),
    FrontendFile(
        path="static/daniela_haptics.js",
        file_type="js",
        lines=23,
        role="module",
        status="production",
        description="Vibration API wrapper. 3 patterns: alert, confirmation, tuning.",
        key_features=["navigator.vibrate wrapper", "3 vibration patterns"],
        issues=[
            "No feature detection beyond 'vibrate' in navigator",
            "Overrides playUISound globally",
        ],
    ),
    FrontendFile(
        path="static/daniela_mobile_sync.js",
        file_type="js",
        lines=17,
        role="module",
        status="production",
        description="Mobile detection + WakeLock API. Body class 'mobile-view'.",
        key_features=["Mobile UA detection", "WakeLock API", "Body class toggle"],
        issues=["Very minimal", "No tablet optimization", "No orientation handling"],
    ),
    FrontendFile(
        path="plugins/daniela_sentinel.js",
        file_type="js",
        lines=46,
        role="extension",
        status="production",
        description="Google Apps Script. Scans Gmail for invoice emails, saves PDFs to Drive, labels threads.",
        key_features=[
            "GmailApp.search",
            "DriveApp folder management",
            "PDF/image attachment extraction",
            "Auto-labeling",
        ],
        issues=["Apps Script only (not browser JS)", "No OCR", "No deduplication", "No logging"],
    ),
    FrontendFile(
        path="projects/mi-dashboard/index.html",
        file_type="html",
        lines=1,
        role="placeholder",
        status="placeholder",
        description="1-line placeholder: 'mi-dashboard - App Premium Soberana'",
        issues=["Not a real page", "No content", "No styling"],
    ),
    FrontendFile(
        path="projects/sistema-dashboard/index.html",
        file_type="html",
        lines=1,
        role="placeholder",
        status="placeholder",
        description="1-line placeholder: 'sistema-dashboard - App Premium Soberana'",
        issues=["Not a real page", "No content", "No styling"],
    ),
]


# ==============================================================================
# ARCHITECTURE ANALYSIS
# ==============================================================================

ARCHITECTURE_SUMMARY = {
    "total_files": 19,  # 11 HTML + 8 JS (excluding .venv)
    "total_lines": 0,  # calculated below
    "html_files": 11,
    "js_files": 8,
    "css_files": 0,  # ALL inline
    "framework": "None (vanilla JS + Three.js r128 from CDN)",
    "bundler": "None",
    "typescript": "No",
    "state_management": "None",
    "router": "None (static HTML files)",
    "shared_css": "None (all inline)",
    "shared_components": "None",
    "cdn_dependencies": [
        "Three.js r128 (cdnjs.cloudflare.com)",
        "Three.js OrbitControls r128 (cdn.jsdelivr.net)",
        "Three.js GLTFLoader r128 (cdn.jsdelivr.net)",
        "Three.js OutlineEffect r128 (cdn.jsdelivr.net)",
        "Tween.js 18.6.4 (cdnjs.cloudflare.com)",
        "Google Fonts: Orbitron, Rajdhani, Share Tech Mono",
        "Font Awesome (CDN)",
        "ws (npm, for metaverse_server.js)",
    ],
    "color_inconsistencies": {
        "full_ui_v2.html": {"cyan": "#00f0ff", "magenta": "#e026de", "bg": "#03060a"},
        "index_sovereign_master.html": {
            "cyan": "#00f0ff",
            "green": "#00ff66",
            "magenta": "#ff0055",
        },
        "landing.html": {"primary": "#0ea5e9", "secondary": "#8b5cf6", "bg": "#0f172a"},
        "neural_city.html": {"primary": "#0ea5e9", "secondary": "#8b5cf6", "bg": "#050510"},
        "daniela_hologram.html": {"primary": "#0ea5e9", "accent": "#00ffcc", "bg": "#000000"},
        "datacenter_live.html": {"primary": "#0ea5e9", "green": "#22c55e", "bg": "#000000"},
        "metaverse.html": {"cyan": "#00f0ff", "magenta": "#ff00ff", "green": "#00ff88"},
        "view_3d_office.html": {"cyan": "#00f3ff", "magenta": "#ff0055", "bg": "#030611"},
    },
    "api_endpoints_used": [
        "/api/chat (full_ui_v2.html, index_sovereign_master.html, app.js)",
        "/api/tts (index_sovereign_master.html)",
        "/api/stt (index_sovereign_master.html)",
        "/api/camera/snap (index_sovereign_master.html)",
        "/api/speech (app.js)",
        "http://localhost:8085/api/chat (chrome-extension/sidepanel.js)",
        "http://192.168.1.133:5059/api/swarm/dispatch (view_3d_office.html)",
        "http://192.168.1.133:5059/api/voice/process (view_3d_office.html)",
        "ws://host:7777 (metaverse.html → metaverse_server.js)",
    ],
}

for f in FILE_AUDIT:
    ARCHITECTURE_SUMMARY["total_lines"] += f.lines


# ==============================================================================
# EPIC IDEAS
# ==============================================================================

EPIC_IDEAS: list[EpicIdea] = [
    # --- ARCHITECTURE ---
    EpicIdea(
        id="FE-01",
        title="Extract all inline CSS into shared design system",
        category="architecture",
        priority="critical",
        effort="M",
        description="Create a single `static/css/` directory with: `variables.css` (brand colors, fonts, spacing), `base.css` (reset, typography, utilities), `components.css` (buttons, cards, panels, chat bubbles), `hud.css` (HUD panels, status badges, pills), and `3d-experiences.css` (canvas containers, loading screens, overlays). Every HTML file imports these instead of inline styles. This eliminates the 7+ different color palettes and creates a single source of truth for the brand identity.",
        files_affected=["ALL HTML files"],
        dependencies=[],
        impact="Eliminates color inconsistencies, enables theme switching, reduces page weight by 40%+",
    ),
    EpicIdea(
        id="FE-02",
        title="Create shared JavaScript component library",
        category="architecture",
        priority="critical",
        effort="L",
        description="Extract reusable JS into `static/js/components/`: `ChatPanel.js` (shared chat UI used by full_ui_v2, landing demo, metaverse), `CameraPIP.js` (shared camera module from app.js + sovereign_master), `VoiceInput.js` (shared STT from app.js + hologram), `ThreeScene.js` (base Three.js setup with scene/camera/renderer/controls), `HudPanel.js` (shared HUD panel component), `ProposalCard.js` (approve/reject cards from full_ui_v2). Use ES6 modules (import/export) instead of global IIFEs.",
        files_affected=[
            "app.js",
            "full_ui_v2.html",
            "templates/index_sovereign_master.html",
            "static/daniela_hologram.html",
            "static/metaverse.html",
        ],
        dependencies=["FE-01"],
        impact="Eliminates code duplication, enables feature consistency, reduces maintenance burden",
    ),
    EpicIdea(
        id="FE-03",
        title="Implement SPA router with lazy-loaded views",
        category="architecture",
        priority="high",
        effort="L",
        description="Build a lightweight client-side router (hash-based or History API) that loads views on demand: `/` → landing, `/app` → full_ui_v2, `/metaverse` → metaverse, `/city` → neural_city, `/globe` → datacenter_live, `/hologram` → daniela_hologram, `/office` → view_3d_office, `/dashboard` → agent dashboard (new), `/mobile` → sovereign_master. Each view lazy-loads its Three.js scene only when visited, reducing initial load from ~50MB+ of 3D content to ~2MB.",
        files_affected=["ALL HTML files", "NEW: static/js/router.js"],
        dependencies=["FE-01", "FE-02"],
        impact="Transforms 11 standalone pages into a unified SPA, dramatically improves load time",
    ),
    EpicIdea(
        id="FE-04",
        title="Centralize API client with WebSocket fallback",
        category="architecture",
        priority="high",
        effort="M",
        description="Create `static/js/api-client.js` that unifies all API calls. Single base URL (configurable via env), automatic REST→WebSocket fallback, request queuing, retry logic, and auth token injection. Replaces the 4 different hardcoded endpoints (localhost:8085, 192.168.1.133:5059, /api/chat, /api/speech) with one configurable client.",
        files_affected=[
            "app.js",
            "full_ui_v2.html",
            "templates/index_sovereign_master.html",
            "chrome-extension/sidepanel.js",
            "view_3d_office.html",
        ],
        dependencies=[],
        impact="Fixes broken endpoints, enables deployment to any environment, simplifies debugging",
    ),
    # --- AGENT INTEGRATION ---
    EpicIdea(
        id="FE-05",
        title="Build real-time Agent Squad dashboard",
        category="agent_integration",
        priority="critical",
        effort="L",
        description="Create a new `/dashboard` view showing the 9 agents (4 core + 5 squad) as live cards. Each card shows: agent name, color, status (online/offline/busy), current task, last activity timestamp, and message count. Data comes from the message_broker.py SQLite database via a new `/api/agents/status` WebSocket endpoint. Cards pulse when agents send messages. Clicking a card opens the agent's activity log (from ActivityLogger JSONL files). This connects the backend agent system to the frontend for the first time.",
        files_affected=[
            "NEW: templates/dashboard.html",
            "NEW: static/js/agent-dashboard.js",
            "message_broker.py",
            "agents.py",
        ],
        dependencies=["FE-01", "FE-02", "FE-04"],
        impact="First real-time visibility into agent operations, connects backend to frontend",
    ),
    EpicIdea(
        id="FE-06",
        title="Wire 5 squad agents into main UI with action buttons",
        category="agent_integration",
        priority="high",
        effort="M",
        description="Add 5 agent action buttons to the full_ui_v2.html Gemini dock (alongside existing camera/file/magic/mic): 📧 Correo (shows inbox summary from agent_correo.py), 📅 Calendario (shows today's events from agent_calendario.py), 📄 Documentos (generates document from agent_documentos.py), 📱 Redes (shows social queue from agent_redes.py), 🛡️ Vigía (shows system health from agent_vigia.py). Each button triggers a fetch to a new `/api/agent/{name}/status` endpoint that calls the corresponding Python agent module.",
        files_affected=[
            "full_ui_v2.html",
            "agent_correo.py",
            "agent_calendario.py",
            "agent_documentos.py",
            "agent_redes.py",
            "agent_vigia.py",
        ],
        dependencies=["FE-04", "FE-05"],
        impact="Connects the 5 fictional-to-real agents to the user interface, completing the fusion",
    ),
    EpicIdea(
        id="FE-07",
        title="Visualize inter-agent message flow in real-time",
        category="agent_integration",
        priority="medium",
        effort="L",
        description="Create a real-time network graph visualization (D3.js or custom Canvas) showing agents as nodes and messages as animated edges. When agent_correo sends a message to agent_documentos via the broker, a glowing particle travels along the edge. Priority is color-coded (URGENT=red, HIGH=orange, NORMAL=cyan, LOW=green). This uses the message_broker.py get_history() method to show the last N messages and subscribes to new ones via WebSocket.",
        files_affected=["NEW: static/js/message-graph.js", "message_broker.py"],
        dependencies=["FE-05"],
        impact="Makes the agent communication visible and debuggable, great for demos",
    ),
    # --- UI/UX ---
    EpicIdea(
        id="FE-08",
        title="Unify color palette to brand kit specification",
        category="ui_ux",
        priority="critical",
        effort="S",
        description="Replace all 7+ color variants with the brand kit colors: Cyan #00ffff, Magenta #ff0055, dark background #03060a. Update CSS variables in all files. Create `static/css/variables.css` as the single source. The 3D experiences keep their per-module accent colors but the base UI (HUD, panels, text, borders) all use brand colors.",
        files_affected=["ALL HTML files"],
        dependencies=["FE-01"],
        impact="Instant brand consistency, professional appearance",
    ),
    EpicIdea(
        id="FE-09",
        title="Add dark/light theme toggle with system preference detection",
        category="ui_ux",
        priority="medium",
        effort="M",
        description="Implement CSS custom properties for both dark and light themes. Auto-detect via `prefers-color-scheme` media query. Add a toggle button in the HUD. The 3D experiences always stay dark (they're space/night scenes), but the chat, panels, and text adapt. Light theme: bg #f0f4f8, text #1a1a2e, borders #cbd5e1, primary #0ea5e9.",
        files_affected=["ALL HTML files"],
        dependencies=["FE-01", "FE-08"],
        impact="Accessibility, user preference, modern UX expectation",
    ),
    EpicIdea(
        id="FE-10",
        title="Replace fake demo chat with real Gemini connection",
        category="ui_ux",
        priority="high",
        effort="S",
        description="In static/landing.html, replace the `demoResponses` keyword-matching object with a real fetch to `/api/chat` (same endpoint as full_ui_v2.html). Add a loading spinner. Show a 'Demo mode - limited responses' badge. Rate-limit to 5 messages per session (localStorage counter). This turns the landing page into a real product demo.",
        files_affected=["static/landing.html"],
        dependencies=["FE-04"],
        impact="Landing page becomes a genuine conversion tool, not a mockup",
    ),
    EpicIdea(
        id="FE-11",
        title="Add notification system with toast notifications",
        category="ui_ux",
        priority="medium",
        effort="M",
        description="Create a shared toast notification component (`static/js/components/Toast.js`) that shows slide-in notifications for: agent alerts (from Vigía), new email classified (from Correo), calendar reminders (from Calendario), social post scheduled (from Redes), document generated (from Documentos). Toasts auto-dismiss after 5s, stack in bottom-right, support click-to-expand. Different colors per agent (blue/gold/green/magenta/red).",
        files_affected=["full_ui_v2.html", "templates/index_sovereign_master.html"],
        dependencies=["FE-02", "FE-06"],
        impact="Users see agent activity without opening the dashboard",
    ),
    # --- REAL-TIME ---
    EpicIdea(
        id="FE-12",
        title="Connect datacenter globe to real backend metrics",
        category="realtime",
        priority="medium",
        effort="M",
        description="Replace the fake setInterval counter in datacenter_live.html with a WebSocket connection to a new `/ws/metrics` endpoint. The backend pushes: request count, active agents, CPU/RAM (from agent_vigia.py), messages/sec (from message_broker.py). Region nodes show real traffic from actual API request logs. Data packets animate only when real requests are processed.",
        files_affected=["static/datacenter_live.html", "agent_vigia.py", "message_broker.py"],
        dependencies=["FE-04"],
        impact="Datacenter becomes a real ops dashboard, not a decoration",
    ),
    EpicIdea(
        id="FE-13",
        title="Add live agent activity stream to main UI",
        category="realtime",
        priority="high",
        effort="M",
        description="Add a collapsible sidebar to full_ui_v2.html showing a live activity feed. Each entry shows: timestamp, agent name (colored), action, and result. Data comes from ActivityLogger JSONL files via a new `/api/activity/stream` SSE (Server-Sent Events) endpoint. The feed auto-scrolls, supports pause/resume, and can be filtered by agent. This is the 'black box' of agent operations visible to the user.",
        files_affected=["full_ui_v2.html", "message_broker.py"],
        dependencies=["FE-02", "FE-05"],
        impact="Transparency into autonomous agent operations, builds trust",
    ),
    # --- METAVERSE ---
    EpicIdea(
        id="FE-14",
        title="Add AI NPC agents to the metaverse",
        category="metaverse",
        priority="medium",
        effort="L",
        description="Populate the metaverse with AI-controlled NPC avatars for each of the 9 agents (Daniela, Guardian, Analyst, Operator, Coder, Correo, Calendario, Documentos, Redes, Vigia). Each NPC has a unique 3D model (or colored capsule with name tag), patrols its zone, and responds when clicked (shows agent info + status). NPCs are server-driven (metaverse_server.js spawns them on startup).",
        files_affected=["static/metaverse.html", "metaverse_server.js", "agents.py"],
        dependencies=["FE-05"],
        impact="Metaverse becomes a living workspace, not just empty rooms",
    ),
    EpicIdea(
        id="FE-15",
        title="Connect neural city buildings to real agent data",
        category="metaverse",
        priority="medium",
        effort="M",
        description="Update neural_city.html building info cards to show real data from agents: uptime (from last startup), request count (from broker stats), current task, status. Buildings glow green when agent is online, red when offline, pulse when processing. Clicking a building navigates to the agent dashboard filtered to that agent.",
        files_affected=["static/neural_city.html", "agents.py", "message_broker.py"],
        dependencies=["FE-05", "FE-12"],
        impact="3D city becomes a real monitoring tool",
    ),
    # --- MOBILE ---
    EpicIdea(
        id="FE-16",
        title="Build progressive web app (PWA) with offline support",
        category="mobile",
        priority="high",
        effort="L",
        description="Add a `manifest.json` with app name, icons (from brand kit), theme color, start_url. Add a service worker that caches: index.html, CSS, JS, and Three.js CDN. Enable 'Add to Home Screen' on Android/iOS. Cache the last chat session for offline viewing. Show a custom offline page with cached data. This makes AIGestion installable as a native app.",
        files_affected=[
            "NEW: manifest.json",
            "NEW: static/js/sw.js",
            "index.html",
            "full_ui_v2.html",
        ],
        dependencies=["FE-01", "FE-03"],
        impact="Native app experience, offline capability, app store readiness",
    ),
    EpicIdea(
        id="FE-17",
        title="Unify mobile and desktop UIs with responsive breakpoints",
        category="mobile",
        priority="high",
        effort="L",
        description="Merge templates/index_sovereign_master.html and full_ui_v2.html into a single responsive UI. Desktop: full HUD with 3D avatar + chat sidebar + proposal cards. Mobile: compact HUD with neural sphere + banner responses + bottom dock. Use CSS Grid + Flexbox with breakpoints at 768px and 1024px. Touch events fall back to mouse events. PIP camera works on both.",
        files_affected=["full_ui_v2.html", "templates/index_sovereign_master.html"],
        dependencies=["FE-01", "FE-02"],
        impact="Single codebase for all devices, eliminates mobile/desktop divergence",
    ),
    # --- MARKETING ---
    EpicIdea(
        id="FE-18",
        title="Wire landing page to real app with auth flow",
        category="marketing",
        priority="high",
        effort="M",
        description="Update landing.html 'Dashboard' button to link to `/app` (the SPA route). Add a login modal (email + password, or Google OAuth). If not authenticated, redirect to landing. If authenticated, redirect to dashboard. Add a 'Try Demo' button that opens a sandboxed version with rate-limited API calls. Pricing buttons trigger signup flow. Connect to billing_system.py for plan selection.",
        files_affected=["static/landing.html", "auth_system.py", "billing_system.py"],
        dependencies=["FE-03", "FE-10"],
        impact="Landing page becomes the real entry point to the product",
    ),
    EpicIdea(
        id="FE-19",
        title="Add SEO optimization and social media meta tags",
        category="marketing",
        priority="medium",
        effort="S",
        description="Add to index.html and landing.html: Open Graph tags (og:title, og:description, og:image from brand kit), Twitter Card tags, structured data (JSON-LD for Organization + SoftwareApplication), sitemap.xml, robots.txt. Optimize page titles and meta descriptions. Add canonical URLs. This makes AIGestion discoverable on Google and shareable on social media.",
        files_affected=["index.html", "static/landing.html", "NEW: sitemap.xml", "NEW: robots.txt"],
        dependencies=[],
        impact="Organic discovery, professional social sharing",
    ),
    EpicIdea(
        id="FE-20",
        title="Build project dashboard templates for clients",
        category="marketing",
        priority="low",
        effort="L",
        description="Replace the 1-line placeholder files in projects/ with real dashboard templates. mi-dashboard: personal KPI dashboard (tasks, emails, calendar, budget). sistema-dashboard: system overview (agent status, server health, message flow, uptime). Both use the shared CSS/JS components and connect to the same backend. These become the 'client portal' view.",
        files_affected=[
            "projects/mi-dashboard/index.html",
            "projects/sistema-dashboard/index.html",
        ],
        dependencies=["FE-01", "FE-02", "FE-05"],
        impact="Client-facing dashboards, replaces placeholders with real value",
    ),
]


# ==============================================================================
# ROADMAP
# ==============================================================================

ROADMAP: list[RoadmapPhase] = [
    RoadmapPhase(
        phase=1,
        name="Foundation & Brand Unity",
        duration_weeks=2,
        ideas=["FE-01", "FE-08", "FE-04", "FE-10"],
        goal="Extract shared CSS, unify colors to brand kit, centralize API client, make landing demo real",
    ),
    RoadmapPhase(
        phase=2,
        name="Component Architecture",
        duration_weeks=3,
        ideas=["FE-02", "FE-03", "FE-17"],
        goal="Build shared JS components, implement SPA router, unify mobile/desktop UI",
    ),
    RoadmapPhase(
        phase=3,
        name="Agent Integration Layer",
        duration_weeks=3,
        ideas=["FE-05", "FE-06", "FE-13", "FE-11"],
        goal="Connect 9 agents to frontend: dashboard, action buttons, activity stream, notifications",
    ),
    RoadmapPhase(
        phase=4,
        name="Real-Time & PWA",
        duration_weeks=2,
        ideas=["FE-12", "FE-16", "FE-09"],
        goal="Wire datacenter to real metrics, build PWA with offline, add theme toggle",
    ),
    RoadmapPhase(
        phase=5,
        name="Metaverse & Marketing",
        duration_weeks=3,
        ideas=["FE-14", "FE-15", "FE-18", "FE-19", "FE-20", "FE-07"],
        goal="Populate metaverse with AI NPCs, connect city to agent data, wire landing to auth, SEO, client dashboards, message flow graph",
    ),
]


# ==============================================================================
# EXPORT FUNCTIONS
# ==============================================================================


def export_json():
    """Export all data to JSON files in static/brand/."""
    export_dir = os.path.join(os.path.dirname(__file__), "static", "brand")
    os.makedirs(export_dir, exist_ok=True)

    # File audit
    audit_data = [asdict(f) for f in FILE_AUDIT]
    with open(os.path.join(export_dir, "frontend_audit.json"), "w", encoding="utf-8") as f:
        json.dump(audit_data, f, indent=2, ensure_ascii=False)

    # Architecture summary
    with open(os.path.join(export_dir, "frontend_architecture.json"), "w", encoding="utf-8") as f:
        json.dump(ARCHITECTURE_SUMMARY, f, indent=2, ensure_ascii=False)

    # Epic ideas
    ideas_data = [asdict(i) for i in EPIC_IDEAS]
    with open(os.path.join(export_dir, "frontend_epic_ideas.json"), "w", encoding="utf-8") as f:
        json.dump(ideas_data, f, indent=2, ensure_ascii=False)

    # Roadmap
    roadmap_data = [asdict(r) for r in ROADMAP]
    with open(os.path.join(export_dir, "frontend_roadmap.json"), "w", encoding="utf-8") as f:
        json.dump(roadmap_data, f, indent=2, ensure_ascii=False)

    print(f"[Frontend Epic Ideas] Exported 4 JSON files to {export_dir}/")
    return export_dir


# ==============================================================================
# CLI
# ==============================================================================


def print_summary():
    """Print a formatted summary to console."""
    print("\n" + "=" * 70)
    print("  AIGESTION FRONTEND AUDIT & EPIC IDEAS")
    print("=" * 70)

    print(f"\n  FILES AUDITED: {ARCHITECTURE_SUMMARY['total_files']}")
    print(f"  TOTAL LINES: {ARCHITECTURE_SUMMARY['total_lines']:,}")
    print(f"  HTML FILES: {ARCHITECTURE_SUMMARY['html_files']}")
    print(f"  JS FILES: {ARCHITECTURE_SUMMARY['js_files']}")
    print(f"  CSS FILES: {ARCHITECTURE_SUMMARY['css_files']} (ALL INLINE)")
    print(f"  FRAMEWORK: {ARCHITECTURE_SUMMARY['framework']}")

    print(
        f"\n  COLOR INCONSISTENCIES: {len(ARCHITECTURE_SUMMARY['color_inconsistencies'])} different palettes"
    )
    for file, colors in ARCHITECTURE_SUMMARY["color_inconsistencies"].items():
        print(f"    {file}: {colors}")

    print(f"\n  API ENDPOINTS: {len(ARCHITECTURE_SUMMARY['api_endpoints_used'])} different URLs")
    for ep in ARCHITECTURE_SUMMARY["api_endpoints_used"]:
        print(f"    {ep}")

    print(f"\n  EPIC IDEAS: {len(EPIC_IDEAS)}")
    by_priority = {}
    for idea in EPIC_IDEAS:
        by_priority.setdefault(idea.priority, []).append(idea)
    for prio in ["critical", "high", "medium", "low"]:
        ideas = by_priority.get(prio, [])
        print(f"    {prio.upper()}: {len(ideas)}")

    by_category = {}
    for idea in EPIC_IDEAS:
        by_category.setdefault(idea.category, []).append(idea)
    print("\n  BY CATEGORY:")
    for cat, ideas in sorted(by_category.items()):
        print(f"    {cat}: {len(ideas)}")

    print(
        f"\n  ROADMAP: {len(ROADMAP)} phases, ~{sum(r.duration_weeks for r in ROADMAP)} weeks total"
    )
    for phase in ROADMAP:
        print(
            f"    Phase {phase.phase}: {phase.name} ({phase.duration_weeks}w) — {len(phase.ideas)} ideas"
        )
        print(f"      Goal: {phase.goal}")

    print("\n" + "=" * 70)
    print("  DETAILED IDEAS:")
    print("=" * 70)
    for idea in EPIC_IDEAS:
        print(f"\n  [{idea.id}] {idea.title}")
        print(f"    Category: {idea.category} | Priority: {idea.priority} | Effort: {idea.effort}")
        print(f"    {idea.description[:150]}...")
        if idea.impact:
            print(f"    Impact: {idea.impact}")


def main():

    import sys

    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        if cmd == "export":
            export_json()
        elif cmd == "summary" or cmd == "all":
            print_summary()
            if cmd == "all":
                export_json()
        else:
            print(f"Unknown command: {cmd}")
            print("Usage: python frontend_epic_ideas.py [summary|export|all]")
    else:
        print_summary()


if __name__ == "__main__":
    main()
