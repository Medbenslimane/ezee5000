// ======= State Management =======
let tabs = [{ id: '1', title: 'الصفحة الرئيسية', url: '', favicon: '' }];
let activeTabId = '1';
let tabCounter = 1;
let bookmarks = JSON.parse(localStorage.getItem('ezee-bookmarks') || '[]');
let history = JSON.parse(localStorage.getItem('ezee-history') || '[]');
let notes = localStorage.getItem('ezee-notes') || '';
let downloads = [];

// Timer state
let timerInterval = null;
let timerSeconds = 0;

// Calculator state
let calcExpression = '';

// ======= Tab Management =======
function createNewTab(url = '') {
  tabCounter++;
  const tabId = String(tabCounter);
  tabs.push({ id: tabId, title: 'تبويب جديد', url: url, favicon: '' });
  
  renderTabs();
  switchToTab(tabId);
  
  if (url) {
    navigateTo(url, tabId);
  } else {
    showNewTabPage();
  }
}

function closeTab(tabId) {
  if (tabs.length === 1) return;
  
  const index = tabs.findIndex(t => t.id === tabId);
  tabs = tabs.filter(t => t.id !== tabId);
  
  // Remove webview
  const webview = document.querySelector(`webview[data-tab-id="${tabId}"]`);
  if (webview) webview.remove();
  
  if (activeTabId === tabId) {
    const newIndex = Math.min(index, tabs.length - 1);
    switchToTab(tabs[newIndex].id);
  }
  
  renderTabs();
}

function switchToTab(tabId) {
  activeTabId = tabId;
  
  // Update tab UI
  document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
  const activeTab = document.querySelector(`.tab[data-tab-id="${tabId}"]`);
  if (activeTab) activeTab.classList.add('active');
  
  // Update webviews
  document.querySelectorAll('webview').forEach(wv => wv.classList.remove('active'));
  const activeWebview = document.querySelector(`webview[data-tab-id="${tabId}"]`);
  
  const tab = tabs.find(t => t.id === tabId);
  
  if (activeWebview) {
    activeWebview.classList.add('active');
    document.getElementById('newTabPage').style.display = 'none';
    document.getElementById('webviewContainer').style.display = 'block';
    document.getElementById('urlInput').value = tab?.url || '';
  } else {
    document.getElementById('newTabPage').style.display = 'flex';
    document.getElementById('webviewContainer').style.display = 'none';
    document.getElementById('urlInput').value = '';
  }
}

function renderTabs() {
  const container = document.getElementById('tabsContainer');
  container.innerHTML = tabs.map(tab => `
    <div class="tab ${tab.id === activeTabId ? 'active' : ''}" data-tab-id="${tab.id}" onclick="switchToTab('${tab.id}')">
      <i class="fas fa-globe tab-icon"></i>
      <span class="tab-title">${tab.title}</span>
      <button class="tab-close" onclick="event.stopPropagation(); closeTab('${tab.id}')">
        <i class="fas fa-times"></i>
      </button>
    </div>
  `).join('');
}

// ======= Navigation =======
function navigateTo(url, tabId = null) {
  if (!tabId) tabId = activeTabId;
  
  // Process URL
  if (!url.startsWith('http://') && !url.startsWith('https://')) {
    if (url.includes('.') && !url.includes(' ')) {
      url = 'https://' + url;
    } else {
      url = `https://www.google.com/search?q=${encodeURIComponent(url)}`;
    }
  }
  
  // Update tab
  const tab = tabs.find(t => t.id === tabId);
  if (tab) {
    tab.url = url;
    tab.title = url.replace(/https?:\/\/(www\.)?/, '').split('/')[0];
  }
  
  // Create or get webview
  let webview = document.querySelector(`webview[data-tab-id="${tabId}"]`);
  if (!webview) {
    webview = document.createElement('webview');
    webview.setAttribute('data-tab-id', tabId);
    webview.setAttribute('allowpopups', '');
    webview.setAttribute('webpreferences', 'contextIsolation=yes');
    document.getElementById('webviewContainer').appendChild(webview);
    
    setupWebviewEvents(webview, tabId);
  }
  
  webview.src = url;
  
  document.getElementById('newTabPage').style.display = 'none';
  document.getElementById('webviewContainer').style.display = 'block';
  
  // Show active webview
  document.querySelectorAll('webview').forEach(wv => wv.classList.remove('active'));
  webview.classList.add('active');
  
  // Update URL bar
  document.getElementById('urlInput').value = url;
  
  // Add to history
  addToHistory(url, tab?.title || url);
  renderTabs();
}

function setupWebviewEvents(webview, tabId) {
  webview.addEventListener('did-start-loading', () => {
    showLoadingBar();
  });
  
  webview.addEventListener('did-stop-loading', () => {
    hideLoadingBar();
  });
  
  webview.addEventListener('page-title-updated', (e) => {
    const tab = tabs.find(t => t.id === tabId);
    if (tab) {
      tab.title = e.title;
      renderTabs();
    }
  });
  
  webview.addEventListener('did-navigate', (e) => {
    const tab = tabs.find(t => t.id === tabId);
    if (tab) {
      tab.url = e.url;
      if (tabId === activeTabId) {
        document.getElementById('urlInput').value = e.url;
      }
    }
    updateSecurityIcon(e.url);
  });
  
  webview.addEventListener('did-navigate-in-page', (e) => {
    if (tabId === activeTabId) {
      document.getElementById('urlInput').value = e.url;
    }
  });
  
  webview.addEventListener('new-window', (e) => {
    createNewTab(e.url);
  });
}

function goBack() {
  const webview = document.querySelector(`webview[data-tab-id="${activeTabId}"]`);
  if (webview && webview.canGoBack()) webview.goBack();
}

function goForward() {
  const webview = document.querySelector(`webview[data-tab-id="${activeTabId}"]`);
  if (webview && webview.canGoForward()) webview.goForward();
}

function refreshPage() {
  const webview = document.querySelector(`webview[data-tab-id="${activeTabId}"]`);
  if (webview) webview.reload();
}

function goHome() {
  showNewTabPage();
  document.getElementById('urlInput').value = '';
}

function showNewTabPage() {
  document.querySelectorAll('webview').forEach(wv => wv.classList.remove('active'));
  document.getElementById('newTabPage').style.display = 'flex';
  document.getElementById('webviewContainer').style.display = 'none';
}

// ======= URL Bar =======
document.getElementById('urlInput').addEventListener('keypress', (e) => {
  if (e.key === 'Enter') {
    navigateTo(e.target.value);
  }
});

document.getElementById('ntpSearchInput')?.addEventListener('keypress', (e) => {
  if (e.key === 'Enter') {
    navigateTo(e.target.value);
  }
});

// ======= Security Icon =======
function updateSecurityIcon(url) {
  const icon = document.getElementById('securityIcon');
  if (url.startsWith('https://')) {
    icon.className = 'fas fa-lock url-icon';
    icon.style.color = 'var(--success)';
  } else {
    icon.className = 'fas fa-lock-open url-icon';
    icon.style.color = 'var(--warning)';
  }
}

// ======= Loading Bar =======
function showLoadingBar() {
  let bar = document.querySelector('.loading-bar');
  if (!bar) {
    bar = document.createElement('div');
    bar.className = 'loading-bar';
    document.querySelector('.browser-content').prepend(bar);
  }
  bar.style.width = '0%';
  bar.classList.add('active');
  
  let width = 0;
  const interval = setInterval(() => {
    width += Math.random() * 15;
    if (width >= 90) { clearInterval(interval); width = 90; }
    bar.style.width = width + '%';
  }, 200);
  
  bar._interval = interval;
}

function hideLoadingBar() {
  const bar = document.querySelector('.loading-bar');
  if (bar) {
    clearInterval(bar._interval);
    bar.style.width = '100%';
    bar.classList.remove('active');
    setTimeout(() => { bar.style.width = '0%'; }, 300);
  }
}

// ======= Privacy Panel =======
function togglePrivacyPanel() {
  const panel = document.getElementById('privacyPanel');
  closeAllPanels('privacyPanel');
  panel.classList.toggle('active');
  if (panel.classList.contains('active')) updatePrivacyStats();
}

async function updatePrivacyStats() {
  try {
    const stats = await window.ezeeAPI.getStats();
    document.getElementById('panelAdsBlocked').textContent = stats.ads;
    document.getElementById('panelTrackersBlocked').textContent = stats.trackers;
    document.getElementById('totalBlocked').textContent = stats.ads;
    document.getElementById('totalTrackers').textContent = stats.trackers;
    document.getElementById('shieldBadge').textContent = stats.ads + stats.trackers;
  } catch (e) {}
}

async function toggleAdBlock() {
  const enabled = document.getElementById('adBlockToggle').checked;
  await window.ezeeAPI.toggleAdBlock(enabled);
  showToast(enabled ? 'تم تفعيل حظر الإعلانات' : 'تم تعطيل حظر الإعلانات');
}

async function toggleTrackerBlock() {
  const enabled = document.getElementById('trackerBlockToggle').checked;
  await window.ezeeAPI.toggleTrackerBlock(enabled);
  showToast(enabled ? 'تم تفعيل حظر المتتبعات' : 'تم تعطيل حظر المتتبعات');
}

async function clearCookies() {
  await window.ezeeAPI.clearCookies();
  showToast('تم حذف جميع الكوكيز');
}

async function clearBrowsingData() {
  await window.ezeeAPI.clearBrowsingData();
  localStorage.removeItem('ezee-history');
  history = [];
  renderHistory();
  showToast('تم مسح بيانات التصفح');
}

// ======= Theme Management =======
function setTheme(theme) {
  document.querySelectorAll('.theme-btn').forEach(b => b.classList.remove('active'));
  
  if (theme === 'dark') {
    document.body.className = 'dark-theme';
    document.getElementById('darkThemeBtn').classList.add('active');
  } else if (theme === 'light') {
    document.body.className = 'light-theme';
    document.getElementById('lightThemeBtn').classList.add('active');
  } else {
    const hour = new Date().getHours();
    document.body.className = (hour >= 18 || hour < 6) ? 'dark-theme' : 'light-theme';
    document.getElementById('autoThemeBtn').classList.add('active');
  }
  
  localStorage.setItem('ezee-theme', theme);
  window.ezeeAPI.setTheme(theme);
}

// ======= Downloads =======
function toggleDownloads() {
  const panel = document.getElementById('downloadsPanel');
  closeAllPanels('downloadsPanel');
  panel.classList.toggle('active');
}

// ======= Menu =======
function toggleMenu() {
  const panel = document.getElementById('menuPanel');
  closeAllPanels('menuPanel');
  panel.classList.toggle('active');
}

function closeAllPanels(except = '') {
  const panels = ['privacyPanel', 'downloadsPanel', 'menuPanel'];
  panels.forEach(id => {
    if (id !== except) document.getElementById(id)?.classList.remove('active');
  });
}

// ======= Screenshot =======
async function takeScreenshot() {
  try {
    const result = await window.ezeeAPI.takeScreenshot();
    if (result.success) {
      showToast(`تم حفظ لقطة الشاشة: ${result.fileName}`);
    } else {
      showToast('فشل في التقاط الشاشة');
    }
  } catch (e) {
    showToast('فشل في التقاط الشاشة');
  }
}

// ======= Sidebar =======
function toggleSidebar() {
  document.getElementById('sidebar').classList.toggle('active');
}

// ======= Quick Tools =======
function openNotes() {
  hideAllSidebarSections();
  document.getElementById('notesSection').style.display = 'block';
  document.getElementById('notesArea').value = notes;
}

function saveNotes() {
  notes = document.getElementById('notesArea').value;
  localStorage.setItem('ezee-notes', notes);
  showToast('تم حفظ الملاحظات');
}

function clearNotes() {
  notes = '';
  document.getElementById('notesArea').value = '';
  localStorage.removeItem('ezee-notes');
  showToast('تم مسح الملاحظات');
}

function openTimer() {
  hideAllSidebarSections();
  document.getElementById('timerSection').style.display = 'block';
}

function startTimer() {
  if (timerInterval) return;
  timerInterval = setInterval(() => {
    timerSeconds++;
    updateTimerDisplay();
  }, 1000);
}

function pauseTimer() {
  clearInterval(timerInterval);
  timerInterval = null;
}

function resetTimer() {
  pauseTimer();
  timerSeconds = 0;
  updateTimerDisplay();
}

function updateTimerDisplay() {
  const hrs = String(Math.floor(timerSeconds / 3600)).padStart(2, '0');
  const mins = String(Math.floor((timerSeconds % 3600) / 60)).padStart(2, '0');
  const secs = String(timerSeconds % 60).padStart(2, '0');
  document.getElementById('timerDisplay').textContent = `${hrs}:${mins}:${secs}`;
}

function openCalculator() {
  hideAllSidebarSections();
  document.getElementById('calculatorSection').style.display = 'block';
}

function calcInput(val) {
  calcExpression += val;
  document.getElementById('calcDisplay').value = calcExpression;
}

function calcResult() {
  try {
    calcExpression = String(eval(calcExpression));
    document.getElementById('calcDisplay').value = calcExpression;
  } catch {
    document.getElementById('calcDisplay').value = 'خطأ';
    calcExpression = '';
  }
}

function calcClear() {
  calcExpression = '';
  document.getElementById('calcDisplay').value = '';
}

function openTranslator() {
  createNewTab('https://translate.google.com');
  toggleSidebar();
}

function openQRGenerator() {
  const url = tabs.find(t => t.id === activeTabId)?.url || '';
  createNewTab(`https://api.qrserver.com/v1/create-qr-code/?size=300x300&data=${encodeURIComponent(url || 'https://ezee-browser.com')}`);
  toggleSidebar();
}

function openColorPicker() {
  createNewTab('https://htmlcolorcodes.com/color-picker/');
  toggleSidebar();
}

function hideAllSidebarSections() {
  document.getElementById('notesSection').style.display = 'none';
  document.getElementById('timerSection').style.display = 'none';
  document.getElementById('calculatorSection').style.display = 'none';
}

// ======= Bookmarks =======
function toggleBookmark() {
  const tab = tabs.find(t => t.id === activeTabId);
  if (!tab || !tab.url) return;
  
  const exists = bookmarks.findIndex(b => b.url === tab.url);
  if (exists > -1) {
    bookmarks.splice(exists, 1);
    document.getElementById('bookmarkIcon').className = 'far fa-star';
    showToast('تمت إزالة المفضلة');
  } else {
    bookmarks.push({ url: tab.url, title: tab.title });
    document.getElementById('bookmarkIcon').className = 'fas fa-star';
    showToast('تمت إضافة المفضلة');
  }
  
  localStorage.setItem('ezee-bookmarks', JSON.stringify(bookmarks));
  renderBookmarks();
}

function renderBookmarks() {
  const list = document.getElementById('bookmarksList');
  if (bookmarks.length === 0) {
    list.innerHTML = '<p class="empty-state">لا توجد مفضلات بعد</p>';
    return;
  }
  list.innerHTML = bookmarks.map(b => `
    <div class="bookmark-item" onclick="navigateTo('${b.url}')" style="padding:8px;cursor:pointer;border-radius:6px;margin-bottom:4px;font-size:12px;color:var(--text);">
      <i class="fas fa-star" style="color:var(--warning);margin-left:6px;"></i>${b.title}
    </div>
  `).join('');
}

// ======= History =======
function addToHistory(url, title) {
  history.unshift({ url, title, time: new Date().toLocaleString('ar') });
  if (history.length > 50) history.pop();
  localStorage.setItem('ezee-history', JSON.stringify(history));
  renderHistory();
}

function renderHistory() {
  const list = document.getElementById('historyList');
  if (history.length === 0) {
    list.innerHTML = '<p class="empty-state">لا يوجد سجل بعد</p>';
    return;
  }
  list.innerHTML = history.slice(0, 10).map(h => `
    <div onclick="navigateTo('${h.url}')" style="padding:6px 8px;cursor:pointer;border-radius:6px;margin-bottom:3px;font-size:11px;color:var(--text-secondary);">
      <i class="fas fa-clock" style="margin-left:4px;"></i>${h.title}
    </div>
  `).join('');
}

// ======= Menu Actions =======
function toggleFullscreen() {
  if (document.fullscreenElement) {
    document.exitFullscreen();
  } else {
    document.documentElement.requestFullscreen();
  }
  toggleMenu();
}

function zoomIn() {
  const webview = document.querySelector(`webview[data-tab-id="${activeTabId}"]`);
  if (webview) {
    const zoom = webview.getZoomFactor();
    webview.setZoomFactor(zoom + 0.1);
  }
}

function zoomOut() {
  const webview = document.querySelector(`webview[data-tab-id="${activeTabId}"]`);
  if (webview) {
    const zoom = webview.getZoomFactor();
    webview.setZoomFactor(zoom - 0.1);
  }
}

function printPage() {
  const webview = document.querySelector(`webview[data-tab-id="${activeTabId}"]`);
  if (webview) webview.print();
  toggleMenu();
}

function viewSource() {
  const tab = tabs.find(t => t.id === activeTabId);
  if (tab?.url) createNewTab('view-source:' + tab.url);
  toggleMenu();
}

function openDevTools() {
  const webview = document.querySelector(`webview[data-tab-id="${activeTabId}"]`);
  if (webview) webview.openDevTools();
  toggleMenu();
}

function openIncognito() {
  showToast('وضع التصفح الخاص مفعل');
  toggleMenu();
}

// ======= Toast Notification =======
function showToast(message) {
  const toast = document.getElementById('toast');
  document.getElementById('toastMessage').textContent = message;
  toast.classList.add('show');
  setTimeout(() => toast.classList.remove('show'), 3000);
}

// ======= Event Listeners =======
window.ezeeAPI?.onStatsUpdate((data) => {
  document.getElementById('totalBlocked').textContent = data.ads;
  document.getElementById('totalTrackers').textContent = data.trackers;
  document.getElementById('shieldBadge').textContent = data.ads + data.trackers;
  document.getElementById('panelAdsBlocked').textContent = data.ads;
  document.getElementById('panelTrackersBlocked').textContent = data.trackers;
});

window.ezeeAPI?.onDownloadStarted((data) => {
  downloads.push({ ...data, percent: 0, state: 'progressing' });
  renderDownloads();
  const badge = document.getElementById('downloadBadge');
  badge.style.display = 'block';
  badge.textContent = downloads.filter(d => d.state === 'progressing').length;
});

window.ezeeAPI?.onDownloadProgress((data) => {
  const dl = downloads.find(d => d.fileName === data.fileName);
  if (dl) {
    dl.percent = data.percent;
    dl.received = data.received;
    renderDownloads();
  }
});

window.ezeeAPI?.onDownloadComplete((data) => {
  const dl = downloads.find(d => d.fileName === data.fileName);
  if (dl) {
    dl.state = data.state;
    dl.percent = 100;
    renderDownloads();
    showToast(`تم تنزيل: ${data.fileName}`);
  }
  const badge = document.getElementById('downloadBadge');
  const active = downloads.filter(d => d.state === 'progressing').length;
  badge.textContent = active;
  if (active === 0) badge.style.display = 'none';
});

function renderDownloads() {
  const list = document.getElementById('downloadsList');
  if (downloads.length === 0) {
    list.innerHTML = '<p class="empty-state"><i class="fas fa-inbox"></i> لا توجد تنزيلات</p>';
    return;
  }
  list.innerHTML = downloads.map(d => `
    <div class="download-item">
      <div class="download-item-header">
        <span class="download-item-name"><i class="fas fa-file" style="margin-left:6px;"></i>${d.fileName}</span>
        <span class="download-item-percent">${d.state === 'completed' ? '✓' : d.percent + '%'}</span>
      </div>
      <div class="download-progress-bar">
        <div class="download-progress-fill" style="width:${d.percent}%"></div>
      </div>
    </div>
  `).join('');
}

// ======= Keyboard Shortcuts =======
document.addEventListener('keydown', (e) => {
  if (e.ctrlKey && e.key === 't') { e.preventDefault(); createNewTab(); }
  if (e.ctrlKey && e.key === 'w') { e.preventDefault(); closeTab(activeTabId); }
  if (e.ctrlKey && e.key === 'l') { e.preventDefault(); document.getElementById('urlInput').focus(); document.getElementById('urlInput').select(); }
  if (e.ctrlKey && e.key === 'r') { e.preventDefault(); refreshPage(); }
  if (e.ctrlKey && e.key === 'd') { e.preventDefault(); toggleBookmark(); }
  if (e.ctrlKey && e.key === 'b') { e.preventDefault(); toggleSidebar(); }
  if (e.key === 'F11') { e.preventDefault(); toggleFullscreen(); }
  if (e.key === 'F12') { e.preventDefault(); openDevTools(); }
});

// ======= Initialize =======
document.addEventListener('DOMContentLoaded', () => {
  // Load saved theme
  const savedTheme = localStorage.getItem('ezee-theme') || 'dark';
  setTheme(savedTheme);
  
  // Load bookmarks & history
  renderBookmarks();
  renderHistory();
  
  // Update stats
  updatePrivacyStats();
  
  // Close panels on outside click
  document.addEventListener('click', (e) => {
    if (!e.target.closest('.panel') && !e.target.closest('.tool-btn')) {
      closeAllPanels();
    }
  });
});
