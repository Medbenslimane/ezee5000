const { app, BrowserWindow, ipcMain, session, dialog, Menu, nativeTheme } = require('electron');
const path = require('path');
const fs = require('fs');

// Ad blocking filter lists
const AD_DOMAINS = [
  '*://*.doubleclick.net/*',
  '*://*.googlesyndication.com/*',
  '*://*.googleadservices.com/*',
  '*://*.google-analytics.com/*',
  '*://*.adnxs.com/*',
  '*://*.adsrvr.org/*',
  '*://*.facebook.com/tr*',
  '*://*.amazon-adsystem.com/*',
  '*://*.outbrain.com/*',
  '*://*.taboola.com/*',
  '*://*.criteo.com/*',
  '*://*.rubiconproject.com/*',
  '*://*.pubmatic.com/*',
  '*://*.moatads.com/*',
  '*://*.scorecardresearch.com/*',
  '*://*.quantserve.com/*',
  '*://*.adform.net/*',
  '*://*.ads-twitter.com/*',
  '*://*.chartbeat.com/*',
  '*://*.hotjar.com/*'
];

// Tracker domains
const TRACKER_DOMAINS = [
  '*://*.facebook.com/plugins/*',
  '*://*.facebook.net/*',
  '*://*.analytics.google.com/*',
  '*://*.mixpanel.com/*',
  '*://*.segment.io/*',
  '*://*.amplitude.com/*',
  '*://*.fullstory.com/*',
  '*://*.mouseflow.com/*',
  '*://*.crazyegg.com/*',
  '*://*.optimizely.com/*'
];

let mainWindow;
let adBlockEnabled = true;
let trackerBlockEnabled = true;
let blockedAdsCount = 0;
let blockedTrackersCount = 0;

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1400,
    height: 900,
    minWidth: 800,
    minHeight: 600,
    frame: false,
    titleBarStyle: 'hidden',
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      preload: path.join(__dirname, 'preload.js'),
      webviewTag: true
    },
    icon: path.join(__dirname, 'assets', 'icon.png'),
    backgroundColor: '#1a1a2e'
  });

  mainWindow.loadFile('index.html');

  // Setup ad blocker
  setupAdBlocker();

  // Setup download manager
  setupDownloadManager();

  mainWindow.on('closed', () => {
    mainWindow = null;
  });
}

function setupAdBlocker() {
  const filter = { urls: ['<all_urls>'] };

  session.defaultSession.webRequest.onBeforeRequest(filter, (details, callback) => {
    const url = details.url;

    if (adBlockEnabled) {
      for (const pattern of AD_DOMAINS) {
        const regex = patternToRegex(pattern);
        if (regex.test(url)) {
          blockedAdsCount++;
          mainWindow?.webContents.send('stats-update', { ads: blockedAdsCount, trackers: blockedTrackersCount });
          callback({ cancel: true });
          return;
        }
      }
    }

    if (trackerBlockEnabled) {
      for (const pattern of TRACKER_DOMAINS) {
        const regex = patternToRegex(pattern);
        if (regex.test(url)) {
          blockedTrackersCount++;
          mainWindow?.webContents.send('stats-update', { ads: blockedAdsCount, trackers: blockedTrackersCount });
          callback({ cancel: true });
          return;
        }
      }
    }

    callback({ cancel: false });
  });
}

function patternToRegex(pattern) {
  const escaped = pattern
    .replace(/[.+?^${}()|[\]\\]/g, '\\$&')
    .replace(/\*/g, '.*');
  return new RegExp(escaped);
}

function setupDownloadManager() {
  session.defaultSession.on('will-download', (event, item, webContents) => {
    const fileName = item.getFilename();
    const totalBytes = item.getTotalBytes();

    mainWindow?.webContents.send('download-started', {
      fileName,
      totalBytes,
      url: item.getURL()
    });

    item.on('updated', (event, state) => {
      if (state === 'progressing') {
        const received = item.getReceivedBytes();
        mainWindow?.webContents.send('download-progress', {
          fileName,
          received,
          totalBytes,
          percent: totalBytes > 0 ? Math.round((received / totalBytes) * 100) : 0
        });
      }
    });

    item.once('done', (event, state) => {
      mainWindow?.webContents.send('download-complete', {
        fileName,
        state,
        path: item.getSavePath()
      });
    });
  });
}

// IPC Handlers
ipcMain.handle('toggle-ad-block', (event, enabled) => {
  adBlockEnabled = enabled;
  return adBlockEnabled;
});

ipcMain.handle('toggle-tracker-block', (event, enabled) => {
  trackerBlockEnabled = enabled;
  return trackerBlockEnabled;
});

ipcMain.handle('get-stats', () => {
  return { ads: blockedAdsCount, trackers: blockedTrackersCount };
});

ipcMain.handle('get-theme', () => {
  return nativeTheme.shouldUseDarkColors ? 'dark' : 'light';
});

ipcMain.handle('set-theme', (event, theme) => {
  nativeTheme.themeSource = theme;
  return theme;
});

ipcMain.handle('clear-browsing-data', async () => {
  await session.defaultSession.clearStorageData();
  await session.defaultSession.clearCache();
  return true;
});

ipcMain.handle('clear-cookies', async () => {
  await session.defaultSession.clearStorageData({ storages: ['cookies'] });
  return true;
});

ipcMain.handle('window-minimize', () => {
  mainWindow?.minimize();
});

ipcMain.handle('window-maximize', () => {
  if (mainWindow?.isMaximized()) {
    mainWindow.unmaximize();
  } else {
    mainWindow?.maximize();
  }
});

ipcMain.handle('window-close', () => {
  mainWindow?.close();
});

ipcMain.handle('take-screenshot', async (event, rect) => {
  try {
    const image = await mainWindow.webContents.capturePage();
    const buffer = image.toPNG();
    const downloadsPath = app.getPath('downloads');
    const fileName = `ezee-screenshot-${Date.now()}.png`;
    const filePath = path.join(downloadsPath, fileName);
    fs.writeFileSync(filePath, buffer);
    return { success: true, path: filePath, fileName };
  } catch (error) {
    return { success: false, error: error.message };
  }
});

app.whenReady().then(createWindow);

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

app.on('activate', () => {
  if (BrowserWindow.getAllWindows().length === 0) {
    createWindow();
  }
});
