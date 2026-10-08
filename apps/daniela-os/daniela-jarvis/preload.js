/**
 * Daniela OS — Jarvis Desktop Overlay
 * Preload Script (Bridge between main/renderer)
 */

const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('jarvis', {
  // System info
  getSystemInfo: () => ipcRenderer.invoke('get-system-info'),
  getScreenSize: () => ipcRenderer.invoke('get-screen-size'),
  
  // Click-through control
  setClickThrough: (enabled) => ipcRenderer.invoke('set-click-through', enabled),
  
  // Event listeners
  onToggleOverlay: (callback) => ipcRenderer.on('toggle-overlay', callback),
  onOpenSettings: (callback) => ipcRenderer.on('open-settings', callback),
  onRunHealthCheck: (callback) => ipcRenderer.on('run-health-check', callback),
  onClickThroughChanged: (callback) => ipcRenderer.on('click-through-changed', callback),
  
  // Platform info
  platform: process.platform,
  isDev: process.env.ELECTRON_DEV === '1'
});
