/**
 * Daniela OS — Jarvis Desktop Overlay
 * Main Electron Process
 */

const { app, BrowserWindow, globalShortcut, Tray, Menu, screen, ipcMain, nativeImage } = require('electron');
const path = require('path');
const Store = require('electron-store');

const store = new Store();
let mainWindow = null;
let tray = null;
let isOverlayVisible = true;
let isClickThrough = false;

const isDev = process.env.ELECTRON_DEV === '1';
const DJANGO_URL = 'http://localhost:5000';

// ═══════════════════════════════════════════════════════════════
// WINDOW CREATION
// ═══════════════════════════════════════════════════════════════

function createOverlay() {
  const { width, height } = screen.getPrimaryDisplay().workAreaSize;

  mainWindow = new BrowserWindow({
    width: width,
    height: height,
    x: 0,
    y: 0,
    transparent: true,
    frame: false,
    alwaysOnTop: true,
    skipTaskbar: true,
    hasShadow: false,
    resizable: false,
    focusable: true,
    webPreferences: {
      nodeIntegration: true,
      contextIsolation: false,
      enableRemoteModule: true
    }
  });

  mainWindow.loadFile(path.join(__dirname, 'overlay', 'index.html'));

  // Enable click-through on transparent areas (Windows)
  if (process.platform === 'win32') {
    enableClickThrough(mainWindow);
  }

  // Open DevTools in development
  if (isDev) {
    mainWindow.webContents.openDevTools({ mode: 'detach' });
  }

  // Prevent window from being closed (minimize to tray)
  mainWindow.on('close', (e) => {
    if (!app.isQuitting) {
      e.preventDefault();
      mainWindow.hide();
    }
  });

  mainWindow.on('closed', () => {
    mainWindow = null;
  });
}

// ═══════════════════════════════════════════════════════════════
// CLICK-THROUGH (Windows)
// ═══════════════════════════════════════════════════════════════

function enableClickThrough(win) {
  // Use Win32 API to set extended window styles
  // WS_EX_LAYERED | WS_EX_TRANSPARENT | WS_EX_TOPMOST
  const { exec } = require('child_process');
  
  // We'll use a PowerShell script to set the window style
  const hwnd = win.getNativeWindowHandle();
  
  // For now, we handle click-through via CSS pointer-events
  // The renderer process toggles pointer-events based on hover
  console.log('[Jarvis] Click-through managed via CSS pointer-events');
}

// ═══════════════════════════════════════════════════════════════
// SYSTEM TRAY
// ═══════════════════════════════════════════════════════════════

function createTray() {
  // Create a simple icon (16x16 cyan circle)
  const icon = nativeImage.createFromDataURL(
    'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAYAAAAf8/9hAAAABHNCSVQICAgIfAhkiAAAAAlwSFlzAAAAbwAAAG8B8aLcQwAAABl0RVh0U29mdHdhcmUAd3d3Lmlua3NjYXBlLm9yZ5vuPBoAAABYSURBVDiNY/z//z8DMwMDAwMTE5DBQAMABQYGAEkgCQYGKA0IYBnBMgJpBNMIpBFMI5BGMI1AGsE0AmkE0wikEUwjkEYwjWAagTSCaQTScrAAAPN3A/VhOJRRAAAAAElFTkSuQmCC'
  );

  tray = new Tray(icon);
  tray.setToolTip('Daniela Jarvis');

  const contextMenu = Menu.buildFromTemplate([
    {
      label: 'Toggle Overlay',
      click: () => toggleOverlay(),
      accelerator: 'CmdOrCtrl+Shift+J'
    },
    { type: 'separator' },
    {
      label: 'Settings',
      click: () => mainWindow?.webContents.send('open-settings')
    },
    {
      label: 'Health Check',
      click: () => mainWindow?.webContents.send('run-health-check')
    },
    { type: 'separator' },
    {
      label: 'Quit Daniela Jarvis',
      click: () => {
        app.isQuitting = true;
        app.quit();
      }
    }
  ]);

  tray.setContextMenu(contextMenu);
  tray.on('click', () => toggleOverlay());
}

// ═══════════════════════════════════════════════════════════════
// TOGGLE OVERLAY
// ═══════════════════════════════════════════════════════════════

function toggleOverlay() {
  if (!mainWindow) return;

  isOverlayVisible = !isOverlayVisible;
  if (isOverlayVisible) {
    mainWindow.show();
    mainWindow.focus();
  } else {
    mainWindow.hide();
  }
}

// ═══════════════════════════════════════════════════════════════
// IPC HANDLERS
// ═══════════════════════════════════════════════════════════════

ipcMain.handle('get-system-info', async () => {
  const os = require('os');
  return {
    platform: os.platform(),
    arch: os.arch(),
    hostname: os.hostname(),
    cpus: os.cpus().length,
    totalMemory: os.totalmem(),
    freeMemory: os.freemem(),
    uptime: os.uptime()
  };
});

ipcMain.handle('get-screen-size', () => {
  const { width, height } = screen.getPrimaryDisplay().workAreaSize;
  return { width, height };
});

ipcMain.handle('set-click-through', (event, enabled) => {
  isClickThrough = enabled;
  mainWindow?.webContents.send('click-through-changed', enabled);
});

// ═══════════════════════════════════════════════════════════════
// APP LIFECYCLE
// ═══════════════════════════════════════════════════════════════

app.whenReady().then(() => {
  createOverlay();
  createTray();

  // Register global hotkey
  globalShortcut.register('CommandOrCtrl+Shift+J', toggleOverlay);

  console.log('[Daniela Jarvis] Overlay started');
  console.log('[Daniela Jarvis] Press Ctrl+Shift+J to toggle');
  console.log('[Daniela Jarvis] Right-click tray icon for options');
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

app.on('will-quit', () => {
  globalShortcut.unregisterAll();
  if (tray) tray.destroy();
});
