/**
 * ContentGuard Popup Script
 * Runs in the extension popup window
 */

const PLATFORMS = {
  'twitter.com': 'Twitter / X  𝕏',
  'x.com': 'Twitter / X  𝕏',
  'reddit.com': 'Reddit 🤖',
  'instagram.com': 'Instagram 📸',
  'youtube.com': 'YouTube ▶️',
  'facebook.com': 'Facebook 👤',
  'news.ycombinator.com': 'Hacker News 🔶',
  'linkedin.com': 'LinkedIn 💼',
};

function detectPlatformFromUrl(url) {
  try {
    const hostname = new URL(url).hostname.replace('www.', '');
    for (const [domain, name] of Object.entries(PLATFORMS)) {
      if (hostname.includes(domain)) return name;
    }
    return 'This Page 🌐';
  } catch {
    return 'Unknown';
  }
}

async function init() {
  // Get current tab info
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });

  if (tab?.url) {
    const urlEl = document.getElementById('page-url');
    const platformEl = document.getElementById('page-platform');

    try {
      const url = new URL(tab.url);
      urlEl.textContent = url.hostname + url.pathname.slice(0, 30) + (url.pathname.length > 30 ? '…' : '');
    } catch {
      urlEl.textContent = tab.url.slice(0, 50);
    }

    platformEl.textContent = detectPlatformFromUrl(tab.url);
  }

  // Check backend status
  checkBackend();

  // Check for existing results in this tab
  if (tab?.id) {
    const state = await chrome.runtime.sendMessage({ type: 'GET_STATE', tabId: tab.id });
    if (state?.results) {
      showMiniStats(state.results.stats);
    }
  }

  // Open panel button
  document.getElementById('open-panel-btn').addEventListener('click', async () => {
    if (tab?.id) {
      // Inject and activate panel via content script message
      try {
        await chrome.scripting.executeScript({
          target: { tabId: tab.id },
          func: () => {
            // Toggle the panel if content script is loaded
            if (window.__contentGuardToggle) {
              window.__contentGuardToggle();
            } else {
              // Content script not loaded yet — try to trigger it
              document.getElementById('contentguard-fab')?.click();
            }
          }
        });
      } catch (e) {
        console.warn('Could not inject script:', e);
      }
      window.close();
    }
  });
}

async function checkBackend() {
  const dot = document.getElementById('status-dot');
  const text = document.getElementById('status-text');
  const hint = document.getElementById('status-hint');

  dot.className = 'status-dot checking';
  text.textContent = 'Checking backend...';

  try {
    const res = await chrome.runtime.sendMessage({ type: 'CHECK_BACKEND' });

    if (res?.online) {
      dot.className = 'status-dot online';
      text.textContent = res.modelLoaded ? 'AI Model Ready' : 'Backend online (model loading...)';
      hint.textContent = 'localhost:8000';
    } else {
      dot.className = 'status-dot offline';
      text.textContent = 'Backend offline';
      hint.textContent = 'Start uvicorn first';

      // Disable button
      const btn = document.getElementById('open-panel-btn');
      btn.title = 'Start the FastAPI backend first';
      // Don't disable — still let them open panel to see error message
    }
  } catch {
    dot.className = 'status-dot offline';
    text.textContent = 'Cannot reach backend';
    hint.textContent = 'localhost:8000';
  }
}

function showMiniStats(stats) {
  if (!stats || !stats.total) return;
  document.getElementById('mini-stats-section').style.display = 'block';
  document.getElementById('s-total').textContent = stats.total;
  document.getElementById('s-toxic').textContent = stats.toxicPercent + '%';
  document.getElementById('s-safe').textContent = stats.safePercent + '%';
}

// Expose toggle function for content script communication
window.__contentGuardToggle = () => {
  document.getElementById('contentguard-fab')?.click();
};

init();
