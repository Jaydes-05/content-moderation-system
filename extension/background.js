/**
 * ContentGuard Background Service Worker
 * Handles API calls, state management, and message routing
 */

const API_BASE = 'http://43.220.4.108:8000';
const TRANSLATE_API = 'https://api.mymemory.translated.net/get';
const BATCH_SIZE = 50; // max comments per batch request

// Keep service worker alive
let keepAliveInterval;

function startKeepAlive() {
  if (keepAliveInterval) return;
  keepAliveInterval = setInterval(() => {
    console.log('[ContentGuard] Service worker keepalive ping');
  }, 20000); // Every 20 seconds
}

function stopKeepAlive() {
  if (keepAliveInterval) {
    clearInterval(keepAliveInterval);
    keepAliveInterval = null;
  }
}

// Start keepalive
startKeepAlive();

// ── State ─────────────────────────────────────────────────────────────────────
const tabState = new Map(); // tabId → { enabled, results, loading }

// ── Message Router ────────────────────────────────────────────────────────────
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  const tabId = sender.tab?.id || message.tabId;

  switch (message.type) {
    case 'ANALYZE_COMMENTS':
      analyzeComments(message.comments, tabId).then(sendResponse);
      return true; // async

    case 'TRANSLATE_COMMENT':
      translateComment(message.text, message.targetLang).then(sendResponse);
      return true; // async

    case 'GET_STATE':
      sendResponse(tabState.get(tabId) || { enabled: false, results: null });
      return false;

    case 'SET_ENABLED':
      const current = tabState.get(tabId) || {};
      tabState.set(tabId, { ...current, enabled: message.enabled });
      sendResponse({ ok: true });
      return false;

    case 'CHECK_BACKEND':
      checkBackend().then(sendResponse);
      return true;
  }
});

// ── Tab cleanup ───────────────────────────────────────────────────────────────
chrome.tabs.onRemoved.addListener((tabId) => {
  tabState.delete(tabId);
});

// ── API Functions ─────────────────────────────────────────────────────────────

/**
 * Check if the FastAPI backend is reachable
 */
async function checkBackend() {
  try {
    console.log('[ContentGuard] Checking backend at:', API_BASE);
    
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 3000);
    
    const res = await fetch(`${API_BASE}/health`, { 
      signal: controller.signal,
      method: 'GET',
      headers: {
        'Content-Type': 'application/json'
      },
      mode: 'cors',
      cache: 'no-cache'
    });
    
    clearTimeout(timeoutId);
    
    console.log('[ContentGuard] Backend response status:', res.status);
    
    if (!res.ok) {
      console.error('[ContentGuard] Backend returned non-OK status:', res.status);
      return { online: false, modelLoaded: false };
    }
    
    const data = await res.json();
    console.log('[ContentGuard] Backend data:', data);
    return { online: true, modelLoaded: data.model_loaded || false };
    
  } catch (error) {
    console.error('[ContentGuard] Backend check failed:', error);
    console.error('[ContentGuard] Error name:', error.name);
    console.error('[ContentGuard] Error message:', error.message);
    
    // If it's a CORS error, the backend is running but CORS is blocking
    if (error.name === 'TypeError' && error.message.includes('Failed to fetch')) {
      console.error('[ContentGuard] This might be a CORS or network error');
      console.error('[ContentGuard] Make sure:');
      console.error('[ContentGuard] 1. Backend is running on http://localhost:8000');
      console.error('[ContentGuard] 2. Extension has host_permissions for localhost:8000');
      console.error('[ContentGuard] 3. CORS is properly configured in the backend');
    }
    
    return { online: false, modelLoaded: false };
  }
}

/**
 * Analyze a batch of comments using the FastAPI backend
 * @param {Array<{text: string, author: string, id: string}>} comments
 * @param {number} tabId
 */
async function analyzeComments(comments, tabId) {
  if (!comments || comments.length === 0) {
    return { error: 'No comments provided' };
  }

  // Update loading state
  tabState.set(tabId, { ...(tabState.get(tabId) || {}), loading: true });

  try {
    // Split into batches
    const batches = [];
    for (let i = 0; i < comments.length; i += BATCH_SIZE) {
      batches.push(comments.slice(i, i + BATCH_SIZE));
    }

    const allResults = [];

    for (const batch of batches) {
      const texts = batch.map(c => c.text);

      const res = await fetch(`${API_BASE}/batch-moderate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ texts }),
        signal: AbortSignal.timeout(30000)
      });

      if (!res.ok) {
        throw new Error(`Backend error: ${res.status}`);
      }

      const data = await res.json();

      // Merge results with original comment metadata
      for (let i = 0; i < batch.length; i++) {
        const modResult = data.results[i];
        allResults.push({
          id: batch[i].id,
          author: batch[i].author,
          text: batch[i].text,
          avatar: batch[i].avatar || null,
          ...modResult
        });
      }
    }

    // Compute aggregate stats
    const stats = computeStats(allResults);

    // Compute block recommendations
    const blockRecs = computeBlockRecommendations(allResults);

    const finalResult = {
      comments: allResults,
      stats,
      blockRecommendations: blockRecs,
      analyzedAt: new Date().toISOString()
    };

    tabState.set(tabId, { ...(tabState.get(tabId) || {}), loading: false, results: finalResult });

    return finalResult;

  } catch (err) {
    tabState.set(tabId, { ...(tabState.get(tabId) || {}), loading: false });
    console.error('[ContentGuard] Analysis failed:', err);
    return { error: err.message };
  }
}

/**
 * Translate a comment using MyMemory free API
 * @param {string} text
 * @param {string} targetLang e.g. 'es', 'fr', 'hi', 'de'
 */
async function translateComment(text, targetLang) {
  try {
    const params = new URLSearchParams({
      q: text,
      langpair: `en|${targetLang}`
    });

    const res = await fetch(`${TRANSLATE_API}?${params}`, {
      signal: AbortSignal.timeout(10000)
    });

    if (!res.ok) throw new Error('Translation API error');

    const data = await res.json();

    if (data.responseStatus === 200) {
      return {
        translated: data.responseData.translatedText,
        targetLang,
        ok: true
      };
    } else {
      throw new Error(data.responseDetails || 'Translation failed');
    }
  } catch (err) {
    console.error('[ContentGuard] Translation failed:', err);
    return { error: err.message, ok: false };
  }
}

/**
 * Compute aggregate statistics from analysis results
 */
function computeStats(results) {
  const total = results.length;
  if (total === 0) return {};

  const toxicCount = results.filter(r => r.is_toxic).length;
  const safeCount = total - toxicCount;

  // Category breakdown
  const categories = { toxic: 0, severe_toxic: 0, obscene: 0, threat: 0, insult: 0, identity_hate: 0 };
  for (const r of results) {
    if (r.predictions) {
      for (const [key, val] of Object.entries(r.predictions)) {
        if (key in categories && val > 0.5) categories[key]++;
      }
    }
  }

  // Action breakdown
  const actions = {};
  for (const r of results) {
    const action = r.action || 'UNKNOWN';
    actions[action] = (actions[action] || 0) + 1;
  }

  // Severity breakdown
  const severities = {};
  for (const r of results) {
    const sev = r.severity || 'NONE';
    severities[sev] = (severities[sev] || 0) + 1;
  }

  return {
    total,
    toxicCount,
    safeCount,
    toxicPercent: Math.round((toxicCount / total) * 100),
    safePercent: Math.round((safeCount / total) * 100),
    categories,
    actions,
    severities
  };
}

/**
 * Compute block recommendations sorted by toxicity score
 */
function computeBlockRecommendations(results) {
  const authorMap = new Map();

  for (const r of results) {
    if (!r.author) continue;
    if (!authorMap.has(r.author)) {
      authorMap.set(r.author, {
        author: r.author,
        avatar: r.avatar,
        toxicCount: 0,
        totalComments: 0,
        maxSeverity: 'NONE',
        worstAction: 'ALLOW',
        totalConfidence: 0
      });
    }
    const entry = authorMap.get(r.author);
    entry.totalComments++;
    entry.totalConfidence += r.confidence || 0;
    if (r.is_toxic) {
      entry.toxicCount++;
    }
    // Track worst severity
    const severityOrder = ['NONE', 'LOW', 'MEDIUM', 'HIGH', 'CRITICAL'];
    const actionOrder = ['ALLOW', 'WARNING', 'HIDE', 'BLOCK'];
    if (severityOrder.indexOf(r.severity) > severityOrder.indexOf(entry.maxSeverity)) {
      entry.maxSeverity = r.severity;
    }
    if (actionOrder.indexOf(r.action) > actionOrder.indexOf(entry.worstAction)) {
      entry.worstAction = r.action;
    }
  }

  // Sort by toxicity rate desc, then toxic count desc
  return Array.from(authorMap.values())
    .map(e => ({
      ...e,
      toxicRate: e.totalComments > 0 ? Math.round((e.toxicCount / e.totalComments) * 100) : 0,
      avgConfidence: e.totalComments > 0 ? e.totalConfidence / e.totalComments : 0
    }))
    .filter(e => e.toxicCount > 0)
    .sort((a, b) => b.toxicRate - a.toxicRate || b.toxicCount - a.toxicCount)
    .slice(0, 5);
}
