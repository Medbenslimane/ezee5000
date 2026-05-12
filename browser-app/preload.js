const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('ezeeAPI', {
  // Window controls
  minimize: () => ipcRenderer.invoke('window-minimize'),
  maximize: () => ipcRenderer.invoke('window-maximize'),
  close: () => ipcRenderer.invoke('window-close'),

  // Ad blocker
  toggleAdBlock: (enabled) => ipcRenderer.invoke('toggle-ad-block', enabled),
  toggleTrackerBlock: (enabled) => ipcRenderer.invoke('toggle-tracker-block', enabled),
  getStats: () => ipcRenderer.invoke('get-stats'),

  // Theme
  getTheme: () => ipcRenderer.invoke('get-theme'),
  setTheme: (theme) => ipcRenderer.invoke('set-theme', theme),

  // Privacy
  clearBrowsingData: () => ipcRenderer.invoke('clear-browsing-data'),
  clearCookies: () => ipcRenderer.invoke('clear-cookies'),

  // Screenshot
  takeScreenshot: (rect) => ipcRenderer.invoke('take-screenshot', rect),

  // Events
  onStatsUpdate: (callback) => ipcRenderer.on('stats-update', (event, data) => callback(data)),
  onDownloadStarted: (callback) => ipcRenderer.on('download-started', (event, data) => callback(data)),
  onDownloadProgress: (callback) => ipcRenderer.on('download-progress', (event, data) => callback(data)),
  onDownloadComplete: (callback) => ipcRenderer.on('download-complete', (event, data) => callback(data))
});
