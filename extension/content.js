/**
 * ContentGuard — Content Script
 * Injected into every page. Detects platform, scrapes comments,
 * injects the floating panel, and handles per-comment interactions.
 */

(function () {
  'use strict';

  // Prevent double-injection
  if (window.__contentGuardInjected) return;
  window.__contentGuardInjected = true;

  // ── Constants ───────────────────────────────────────────────────────────────
  const PANEL_ID = 'contentguard-panel';
  const FAB_ID = 'contentguard-fab';
  const SUPPORTED_LANGS = [
    { code: 'es', name: 'Spanish' },
    { code: 'fr', name: 'French' },
    { code: 'de', name: 'German' },
    { code: 'hi', name: 'Hindi' },
    { code: 'zh', name: 'Chinese' },
    { code: 'ar', name: 'Arabic' },
    { code: 'pt', name: 'Portuguese' },
    { code: 'ja', name: 'Japanese' },
    { code: 'ko', name: 'Korean' },
    { code: 'ru', name: 'Russian' },
    { code: 'it', name: 'Italian' },
    { code: 'nl', name: 'Dutch' },
  ];

  // ── Platform Detection ──────────────────────────────────────────────────────
  const PLATFORMS = {
    twitter: {
      name: 'Twitter / X',
      icon: '𝕏',
      detect: () => /twitter\.com|x\.com/.test(location.hostname),
      scrapeComments: scrapeTwitter,
      commentSelector: '[data-testid="tweet"], article[role="article"], div[lang]',
    },
    facebook: {
      name: 'Facebook',
      icon: '👥',
      detect: () => /facebook\.com/.test(location.hostname),
      scrapeComments: scrapeFacebook,
      commentSelector: '[role="article"], div[dir="auto"]',
    },
    linkedin: {
      name: 'LinkedIn',
      icon: '💼',
      detect: () => /linkedin\.com/.test(location.hostname),
      scrapeComments: scrapeLinkedIn,
      commentSelector: '.comments-comment-item, .comment-item',
    },
    tiktok: {
      name: 'TikTok',
      icon: '🎵',
      detect: () => /tiktok\.com/.test(location.hostname),
      scrapeComments: scrapeTikTok,
      commentSelector: '[data-e2e="comment-item"], .comment-item',
    },
    reddit: {
      name: 'Reddit',
      icon: '🤖',
      detect: () => /reddit\.com/.test(location.hostname),
      scrapeComments: scrapeReddit,
      commentSelector: '[data-testid="comment"], .Comment, p',
    },
    instagram: {
      name: 'Instagram',
      icon: '📸',
      detect: () => /instagram\.com/.test(location.hostname),
      scrapeComments: scrapeInstagram,
      commentSelector: '._a9zs, ._a9ym, span[class*="comment"]',
    },
    youtube: {
      name: 'YouTube',
      icon: '▶️',
      detect: () => /youtube\.com/.test(location.hostname),
      scrapeComments: scrapeYouTube,
      commentSelector: 'ytd-comment-renderer, #content-text',
    },
    hackernews: {
      name: 'Hacker News',
      icon: '🔶',
      detect: () => /news\.ycombinator\.com/.test(location.hostname),
      scrapeComments: scrapeHackerNews,
      commentSelector: '.comment',
    },
    generic: {
      name: 'This Page',
      icon: '🌐',
      detect: () => true,
      scrapeComments: scrapeGeneric,
      commentSelector: '[class*="comment"], article p, [role="article"]',
    },
  };

  // ── State ───────────────────────────────────────────────────────────────────
  let state = {
    isOpen: false,
    isAnalyzing: false,
    platform: null,
    results: null,
    backendOnline: false,
    activeTab: 'stats', // 'stats' | 'comments' | 'block' | 'analytics' | 'insights' | 'batch' | 'health'
    selectedLang: 'es',
    translating: {}, // commentId → {loading, translated}
    history: [], // Historical analysis data for trends
    userReputation: new Map(), // username → reputation score
    batchMode: false, // Batch moderation mode
    selectedComments: new Set(), // Selected comment IDs for batch operations
    communityHealth: null, // Community health metrics
    settings: {
      autoHide: false,
      customKeywords: [],
      whitelist: [],
      notifyHighToxicity: true,
      toxicityThreshold: 0.5, // Changed from 0.7 to 0.5 for better detection
      showHeatmap: true,
      showReplySuggestions: true,
      trackHistory: true,
      detectSarcasm: true // AI context analysis for sarcasm
    }
  };

  // ── Init ────────────────────────────────────────────────────────────────────
  function init() {
    state.platform = detectPlatform();
    injectFAB();
    checkBackend();

    // Watch for navigation (SPA)
    const origPushState = history.pushState.bind(history);
    history.pushState = function (...args) {
      origPushState(...args);
      setTimeout(() => {
        state.results = null;
        if (state.isOpen) analyzeAndRender();
      }, 1500);
    };
    window.addEventListener('popstate', () => {
      state.results = null;
      if (state.isOpen) setTimeout(analyzeAndRender, 1500);
    });
  }

  // ── Platform Detection ──────────────────────────────────────────────────────
  function detectPlatform() {
    for (const [key, p] of Object.entries(PLATFORMS)) {
      if (key !== 'generic' && p.detect()) return p;
    }
    return PLATFORMS.generic;
  }

  // ── Backend Check ───────────────────────────────────────────────────────────
  async function checkBackend() {
    const res = await sendMessage({ type: 'CHECK_BACKEND' });
    state.backendOnline = res?.online || false;
    updateFABStatus();
  }

  // ── FAB (Floating Action Button) ────────────────────────────────────────────
  function injectFAB() {
    if (document.getElementById(FAB_ID)) return;

    const fab = document.createElement('div');
    fab.id = FAB_ID;
    fab.innerHTML = `
      <div class="cg-fab-inner">
        <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
          <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-1 15l-4-4 1.41-1.41L11 14.17l7.59-7.59L20 8l-9 9z" fill="currentColor"/>
        </svg>
        <span class="cg-fab-label">ContentGuard</span>
        <span class="cg-fab-dot" id="cg-status-dot"></span>
      </div>
    `;
    fab.title = 'Open ContentGuard Panel';
    fab.addEventListener('click', togglePanel);
    document.body.appendChild(fab);
  }

  function updateFABStatus() {
    const dot = document.getElementById('cg-status-dot');
    if (dot) {
      dot.className = 'cg-fab-dot ' + (state.backendOnline ? 'online' : 'offline');
      dot.title = state.backendOnline ? 'Backend connected' : 'Backend offline — start uvicorn';
    }
  }

  // ── Panel ───────────────────────────────────────────────────────────────────
  function togglePanel() {
    if (state.isOpen) {
      closePanel();
    } else {
      openPanel();
    }
  }

  function openPanel() {
    state.isOpen = true;
    let panel = document.getElementById(PANEL_ID);
    if (!panel) {
      panel = createPanelElement();
      document.body.appendChild(panel);
      makeDraggable(panel);
    }
    panel.classList.add('cg-panel--visible');
    // Don't auto-analyze, wait for user to click refresh
  }

  function closePanel() {
    state.isOpen = false;
    const panel = document.getElementById(PANEL_ID);
    if (panel) panel.classList.remove('cg-panel--visible');
  }

  function createPanelElement() {
    const panel = document.createElement('div');
    panel.id = PANEL_ID;
    panel.className = 'cg-panel';
    panel.innerHTML = getPanelHTML();
    bindPanelEvents(panel);
    return panel;
  }

  function getPanelHTML() {
    return `
      <div class="cg-panel__header" id="cg-drag-handle">
        <div class="cg-panel__logo">
          <div class="cg-logo-icon">
            <svg viewBox="0 0 24 24" fill="none"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-1 15l-4-4 1.41-1.41L11 14.17l7.59-7.59L20 8l-9 9z" fill="currentColor"/></svg>
          </div>
          <div>
            <div class="cg-panel__title">ContentGuard <span class="cg-ml-tag">ML</span></div>
            <div class="cg-panel__subtitle" id="cg-platform-label">BERT Model • 92.8% Accuracy</div>
          </div>
        </div>
        <div class="cg-panel__actions">
          <button class="cg-btn-icon" id="cg-settings-btn" title="Settings">
            <svg viewBox="0 0 24 24" fill="none"><path d="M19.14 12.94c.04-.3.06-.61.06-.94 0-.32-.02-.64-.07-.94l2.03-1.58c.18-.14.23-.41.12-.61l-1.92-3.32c-.12-.22-.37-.29-.59-.22l-2.39.96c-.5-.38-1.03-.7-1.62-.94L14.4 2.81c-.04-.24-.24-.41-.48-.41h-3.84c-.24 0-.43.17-.47.41l-.36 2.54c-.59.24-1.13.57-1.62.94l-2.39-.96c-.22-.08-.47 0-.59.22L2.74 8.87c-.12.21-.08.47.12.61l2.03 1.58c-.05.3-.09.63-.09.94s.02.64.07.94l-2.03 1.58c-.18.14-.23.41-.12.61l1.92 3.32c.12.22.37.29.59.22l2.39-.96c.5.38 1.03.7 1.62.94l.36 2.54c.05.24.24.41.48.41h3.84c.24 0 .44-.17.47-.41l.36-2.54c.59-.24 1.13-.56 1.62-.94l2.39.96c.22.08.47 0 .59-.22l1.92-3.32c.12-.22.07-.47-.12-.61l-2.01-1.58zM12 15.6c-1.98 0-3.6-1.62-3.6-3.6s1.62-3.6 3.6-3.6 3.6 1.62 3.6 3.6-1.62 3.6-3.6 3.6z" fill="currentColor"/></svg>
          </button>
          <button class="cg-btn-icon" id="cg-export-btn" title="Export Report">
            <svg viewBox="0 0 24 24" fill="none"><path d="M19 12v7H5v-7H3v7c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2v-7h-2zm-6 .67l2.59-2.58L17 11.5l-5 5-5-5 1.41-1.41L11 12.67V3h2z" fill="currentColor"/></svg>
          </button>
          <div class="cg-export-menu" id="cg-export-menu" style="display: none;">
            <button class="cg-export-option" data-format="csv">📊 Export CSV</button>
            <button class="cg-export-option" data-format="json">📄 Export JSON</button>
            <button class="cg-export-option" data-format="pdf">📕 Export PDF</button>
          </div>
          <button class="cg-btn-icon" id="cg-refresh-btn" title="Re-analyze">
            <svg viewBox="0 0 24 24" fill="none"><path d="M17.65 6.35A7.958 7.958 0 0012 4c-4.42 0-7.99 3.58-7.99 8s3.57 8 7.99 8c3.73 0 6.84-2.55 7.73-6h-2.08A5.99 5.99 0 0112 18c-3.31 0-6-2.69-6-6s2.69-6 6-6c1.66 0 3.14.69 4.22 1.78L13 11h7V4l-2.35 2.35z" fill="currentColor"/></svg>
          </button>
          <button class="cg-btn-icon" id="cg-close-btn" title="Close">
            <svg viewBox="0 0 24 24" fill="none"><path d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z" fill="currentColor"/></svg>
          </button>
        </div>
      </div>

      <div class="cg-panel__body">
        <!-- Content (always visible) -->
        <div class="cg-content" id="cg-content">
          <!-- Tabs -->
          <div class="cg-tabs">
            <button class="cg-tab active" data-tab="stats">📊 Stats</button>
            <button class="cg-tab" data-tab="health">💚 Health</button>
            <button class="cg-tab" data-tab="comments">💬 Comments</button>
            <button class="cg-tab" data-tab="batch">📦 Batch</button>
            <button class="cg-tab" data-tab="analytics">📈 Analytics</button>
            <button class="cg-tab" data-tab="insights">🧠 AI Insights</button>
            <button class="cg-tab" data-tab="block">🚫 Block</button>
            <button class="cg-tab" data-tab="settings">⚙️ Settings</button>
          </div>

          <!-- Stats Tab -->
          <div class="cg-tab-content active" id="tab-stats">
            <div class="cg-stat-grid" id="cg-stat-grid">
              <div class="cg-stat-card cg-stat-total">
                <div class="cg-stat-value">0</div>
                <div class="cg-stat-label">Total Comments</div>
              </div>
              <div class="cg-stat-card cg-stat-toxic">
                <div class="cg-stat-value">0</div>
                <div class="cg-stat-label">Toxic (0%)</div>
              </div>
              <div class="cg-stat-card cg-stat-safe">
                <div class="cg-stat-value">0</div>
                <div class="cg-stat-label">Safe (0%)</div>
              </div>
            </div>
            <div class="cg-sentiment-chart" id="cg-sentiment-chart" style="margin-top: 15px;">
              <div class="cg-chart-title">Sentiment Analysis</div>
              <div class="cg-sentiment-bars" id="cg-sentiment-bars"></div>
            </div>
          </div>

          <!-- Community Health Tab -->
          <div class="cg-tab-content" id="tab-health">
            <div class="cg-health-dashboard">
              <div class="cg-health-score-container">
                <svg class="cg-health-gauge" viewBox="0 0 200 200" width="200" height="200">
                  <circle cx="100" cy="100" r="80" fill="none" stroke="rgba(255,255,255,0.1)" stroke-width="20"/>
                  <circle id="cg-health-circle" cx="100" cy="100" r="80" fill="none" stroke="url(#healthGradient)" stroke-width="20" 
                          stroke-dasharray="502.4" stroke-dashoffset="502.4" stroke-linecap="round" 
                          transform="rotate(-90 100 100)" style="transition: stroke-dashoffset 1.5s ease;"/>
                  <defs>
                    <linearGradient id="healthGradient" x1="0%" y1="0%" x2="100%" y2="100%">
                      <stop offset="0%" style="stop-color:#10B981;stop-opacity:1" />
                      <stop offset="100%" style="stop-color:#06B6D4;stop-opacity:1" />
                    </linearGradient>
                  </defs>
                  <text x="100" y="95" text-anchor="middle" font-size="48" font-weight="700" fill="#fff" id="cg-health-value">0</text>
                  <text x="100" y="115" text-anchor="middle" font-size="14" fill="#94A3B8">Health Score</text>
                </svg>
                <div class="cg-health-status" id="cg-health-status">Analyzing...</div>
              </div>
              
              <div class="cg-health-metrics">
                <div class="cg-health-metric">
                  <div class="cg-metric-icon">🎯</div>
                  <div class="cg-metric-info">
                    <div class="cg-metric-label">Toxicity Rate</div>
                    <div class="cg-metric-value" id="cg-metric-toxicity">0%</div>
                  </div>
                </div>
                <div class="cg-health-metric">
                  <div class="cg-metric-icon">👥</div>
                  <div class="cg-metric-info">
                    <div class="cg-metric-label">User Engagement</div>
                    <div class="cg-metric-value" id="cg-metric-engagement">0%</div>
                  </div>
                </div>
                <div class="cg-health-metric">
                  <div class="cg-metric-icon">😊</div>
                  <div class="cg-metric-info">
                    <div class="cg-metric-label">Sentiment Balance</div>
                    <div class="cg-metric-value" id="cg-metric-sentiment">0%</div>
                  </div>
                </div>
                <div class="cg-health-metric">
                  <div class="cg-metric-icon">🛡️</div>
                  <div class="cg-metric-info">
                    <div class="cg-metric-label">Moderation Effectiveness</div>
                    <div class="cg-metric-value" id="cg-metric-moderation">0%</div>
                  </div>
                </div>
              </div>

              <div class="cg-health-trend">
                <div class="cg-trend-label">Trend</div>
                <div class="cg-trend-indicator" id="cg-trend-indicator">
                  <span class="cg-trend-arrow">→</span>
                  <span class="cg-trend-text">Stable</span>
                </div>
              </div>
            </div>
          </div>

          <!-- Comments Tab -->
          <div class="cg-tab-content" id="tab-comments">
            <div class="cg-comment-filter">
              <button class="cg-filter-btn active" data-filter="all">All</button>
              <button class="cg-filter-btn" data-filter="toxic">🔴 Toxic</button>
              <button class="cg-filter-btn" data-filter="safe">🟢 Safe</button>
            </div>
            <div class="cg-comment-list" id="cg-comment-list">
              <div class="cg-empty">Click refresh to analyze comments</div>
            </div>
          </div>

          <!-- Batch Moderation Tab -->
          <div class="cg-tab-content" id="tab-batch">
            <div class="cg-batch-header">
              <div class="cg-batch-title">Batch Moderation Mode</div>
              <div class="cg-batch-actions">
                <button class="cg-batch-btn" id="cg-select-all-toxic">Select All Toxic</button>
                <button class="cg-batch-btn" id="cg-select-all">Select All</button>
                <button class="cg-batch-btn" id="cg-deselect-all">Deselect All</button>
              </div>
            </div>
            <div class="cg-batch-selected">
              <span id="cg-batch-count">0</span> comments selected
            </div>
            <div class="cg-batch-operations">
              <button class="cg-batch-op-btn cg-batch-hide" id="cg-batch-hide-btn">
                <svg viewBox="0 0 24 24" width="16" height="16"><path fill="currentColor" d="M12 7c2.76 0 5 2.24 5 5 0 .65-.13 1.26-.36 1.83l2.92 2.92c1.51-1.26 2.7-2.89 3.43-4.75-1.73-4.39-6-7.5-11-7.5-1.4 0-2.74.25-3.98.7l2.16 2.16C10.74 7.13 11.35 7 12 7zM2 4.27l2.28 2.28.46.46A11.804 11.804 0 001 12c1.73 4.39 6 7.5 11 7.5 1.55 0 3.03-.3 4.38-.84l.42.42L19.73 22 21 20.73 3.27 3 2 4.27zM7.53 9.8l1.55 1.55c-.05.21-.08.43-.08.65 0 1.66 1.34 3 3 3 .22 0 .44-.03.65-.08l1.55 1.55c-.67.33-1.41.53-2.2.53-2.76 0-5-2.24-5-5 0-.79.2-1.53.53-2.2zm4.31-.78l3.15 3.15.02-.16c0-1.66-1.34-3-3-3l-.17.01z"/></svg>
                Hide Selected
              </button>
              <button class="cg-batch-op-btn cg-batch-block" id="cg-batch-block-btn">
                <svg viewBox="0 0 24 24" width="16" height="16"><path fill="currentColor" d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zM4 12c0-4.42 3.58-8 8-8 1.85 0 3.55.63 4.9 1.69L5.69 16.9C4.63 15.55 4 13.85 4 12zm8 8c-1.85 0-3.55-.63-4.9-1.69L18.31 7.1C19.37 8.45 20 10.15 20 12c0 4.42-3.58 8-8 8z"/></svg>
                Block Users
              </button>
              <button class="cg-batch-op-btn cg-batch-approve" id="cg-batch-approve-btn">
                <svg viewBox="0 0 24 24" width="16" height="16"><path fill="currentColor" d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41z"/></svg>
                Approve Selected
              </button>
              <button class="cg-batch-op-btn cg-batch-export" id="cg-batch-export-btn">
                <svg viewBox="0 0 24 24" width="16" height="16"><path fill="currentColor" d="M19 12v7H5v-7H3v7c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2v-7h-2zm-6 .67l2.59-2.58L17 11.5l-5 5-5-5 1.41-1.41L11 12.67V3h2z"/></svg>
                Export Selected
              </button>
            </div>
            <div class="cg-batch-list" id="cg-batch-list">
              <div class="cg-empty">Click refresh to analyze comments</div>
            </div>
          </div>

          <!-- Block List Tab -->
          <div class="cg-tab-content" id="tab-block">
            <div class="cg-block-header">Users with toxic comments</div>
            <div class="cg-block-list" id="cg-block-list">
              <div class="cg-empty">No toxic users yet</div>
            </div>
          </div>

          <!-- Settings Tab -->
          <div class="cg-tab-content" id="tab-settings">
            <div class="cg-settings">
              <div class="cg-setting-group">
                <div class="cg-setting-header">🎯 Auto-Moderation</div>
                <label class="cg-setting-item">
                  <input type="checkbox" id="cg-auto-hide" />
                  <span>Auto-hide toxic comments on page</span>
                </label>
                <label class="cg-setting-item">
                  <input type="checkbox" id="cg-notify" checked />
                  <span>Notify when high toxicity detected</span>
                </label>
                <label class="cg-setting-item">
                  <input type="checkbox" id="cg-show-heatmap" checked />
                  <span>Show toxicity heatmap visualization</span>
                </label>
                <label class="cg-setting-item">
                  <input type="checkbox" id="cg-reply-suggestions" checked />
                  <span>Show AI reply suggestions</span>
                </label>
                <label class="cg-setting-item">
                  <input type="checkbox" id="cg-track-history" checked />
                  <span>Track toxicity trends over time</span>
                </label>
                <label class="cg-setting-item">
                  <input type="checkbox" id="cg-detect-sarcasm" checked />
                  <span>AI Context Analysis (detect sarcasm & jokes)</span>
                </label>
              </div>
              
              <div class="cg-setting-group">
                <div class="cg-setting-header">🔍 Custom Keywords</div>
                <input type="text" id="cg-keywords-input" placeholder="Add words to flag (comma-separated)" class="cg-input" />
                <button id="cg-keywords-save" class="cg-btn-small">Save Keywords</button>
                <div id="cg-keywords-list" class="cg-keywords-list"></div>
              </div>

              <div class="cg-setting-group">
                <div class="cg-setting-header">✅ Whitelist Users</div>
                <input type="text" id="cg-whitelist-input" placeholder="Add usernames to never flag" class="cg-input" />
                <button id="cg-whitelist-save" class="cg-btn-small">Add to Whitelist</button>
                <div id="cg-whitelist-list" class="cg-whitelist-list"></div>
              </div>

              <div class="cg-setting-group">
                <div class="cg-setting-header">⚡ Toxicity Threshold</div>
                <input type="range" id="cg-threshold" min="0" max="100" value="50" class="cg-slider" />
                <div class="cg-threshold-value"><span id="cg-threshold-display">50</span>%</div>
                <div style="font-size: 10px; color: var(--cg-text-dim); margin-top: 8px;">
                  Lower = more strict (flags more), Higher = more lenient (flags less)
                </div>
              </div>
            </div>
          </div>

          <!-- Analytics Tab -->
          <div class="cg-tab-content" id="tab-analytics">
            <div class="cg-analytics">
              <div class="cg-analytics-header">📈 Toxicity Trends</div>
              <div class="cg-trend-chart" id="cg-trend-chart">
                <canvas id="cg-trend-canvas" width="440" height="150"></canvas>
              </div>
              
              <div class="cg-analytics-header">🔥 Toxicity Heatmap</div>
              <div class="cg-heatmap" id="cg-heatmap">
                <div class="cg-heatmap-grid" id="cg-heatmap-grid"></div>
                <div class="cg-heatmap-legend">
                  <span class="cg-legend-item"><span class="cg-legend-box" style="background: var(--cg-green);"></span> Safe</span>
                  <span class="cg-legend-item"><span class="cg-legend-box" style="background: var(--cg-yellow);"></span> Low</span>
                  <span class="cg-legend-item"><span class="cg-legend-box" style="background: var(--cg-orange);"></span> Medium</span>
                  <span class="cg-legend-item"><span class="cg-legend-box" style="background: var(--cg-red);"></span> High</span>
                </div>
              </div>

              <div class="cg-analytics-header">👥 User Reputation Scores</div>
              <div class="cg-reputation-list" id="cg-reputation-list"></div>
            </div>
          </div>

          <!-- AI Insights Tab -->
          <div class="cg-tab-content" id="tab-insights">
            <div class="cg-insights">
              <div class="cg-insight-card cg-insight-summary">
                <div class="cg-insight-icon">🤖</div>
                <div class="cg-insight-title">AI Summary</div>
                <div class="cg-insight-content" id="cg-ai-summary">
                  Analyze comments to see AI-generated insights...
                </div>
              </div>

              <div class="cg-insight-card">
                <div class="cg-insight-icon">🎯</div>
                <div class="cg-insight-title">Toxic Patterns Detected</div>
                <div class="cg-insight-content" id="cg-toxic-patterns">
                  <div class="cg-empty-small">No patterns detected yet</div>
                </div>
              </div>

              <div class="cg-insight-card">
                <div class="cg-insight-icon">💡</div>
                <div class="cg-insight-title">Recommendations</div>
                <div class="cg-insight-content" id="cg-recommendations">
                  <div class="cg-empty-small">Analyze comments to get recommendations</div>
                </div>
              </div>

              <div class="cg-insight-card">
                <div class="cg-insight-icon">⚠️</div>
                <div class="cg-insight-title">High-Risk Users</div>
                <div class="cg-insight-content" id="cg-high-risk-users">
                  <div class="cg-empty-small">No high-risk users detected</div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    `;
  }

  function bindPanelEvents(panel) {
    // Load settings
    loadSettings();
    
    // Close button
    panel.querySelector('#cg-close-btn').addEventListener('click', closePanel);

    // Refresh button
    panel.querySelector('#cg-refresh-btn').addEventListener('click', () => {
      state.results = null;
      analyzeAndRender();
    });

    // Export button - show menu
    panel.querySelector('#cg-export-btn').addEventListener('click', (e) => {
      e.stopPropagation();
      const menu = document.getElementById('cg-export-menu');
      menu.style.display = menu.style.display === 'none' ? 'block' : 'none';
    });

    // Export menu options
    document.addEventListener('click', () => {
      const menu = document.getElementById('cg-export-menu');
      if (menu) menu.style.display = 'none';
    });

    panel.querySelectorAll('.cg-export-option').forEach(btn => {
      btn.addEventListener('click', (e) => {
        e.stopPropagation();
        const format = btn.dataset.format;
        exportReport(format);
        document.getElementById('cg-export-menu').style.display = 'none';
      });
    });

    // Settings button
    panel.querySelector('#cg-settings-btn').addEventListener('click', () => {
      state.activeTab = 'settings';
      panel.querySelectorAll('.cg-tab').forEach(t => t.classList.remove('active'));
      panel.querySelector('[data-tab="settings"]').classList.add('active');
      panel.querySelectorAll('.cg-tab-content').forEach(t => t.classList.remove('active'));
      panel.querySelector('#tab-settings').classList.add('active');
    });

    // Tabs
    panel.querySelectorAll('.cg-tab').forEach(tab => {
      tab.addEventListener('click', () => {
        const tabName = tab.dataset.tab;
        state.activeTab = tabName;
        
        // Update active tab button
        panel.querySelectorAll('.cg-tab').forEach(t => t.classList.remove('active'));
        tab.classList.add('active');
        
        // Update active tab content
        panel.querySelectorAll('.cg-tab-content').forEach(t => t.classList.remove('active'));
        const tabContent = panel.querySelector(`#tab-${tabName}`);
        if (tabContent) {
          tabContent.classList.add('active');
        }
      });
    });

    // Filter buttons (comments tab)
    panel.querySelectorAll('.cg-filter-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        panel.querySelectorAll('.cg-filter-btn').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        filterComments(btn.dataset.filter);
      });
    });

    // Settings: Auto-hide checkbox
    panel.querySelector('#cg-auto-hide').addEventListener('change', (e) => {
      state.settings.autoHide = e.target.checked;
      saveSettings();
      if (state.settings.autoHide && state.results) {
        applyAutoHide();
      }
    });

    // Settings: Notify checkbox
    panel.querySelector('#cg-notify').addEventListener('change', (e) => {
      state.settings.notifyHighToxicity = e.target.checked;
      saveSettings();
    });

    // Settings: Show heatmap checkbox
    panel.querySelector('#cg-show-heatmap').addEventListener('change', (e) => {
      state.settings.showHeatmap = e.target.checked;
      saveSettings();
    });

    // Settings: Reply suggestions checkbox
    panel.querySelector('#cg-reply-suggestions').addEventListener('change', (e) => {
      state.settings.showReplySuggestions = e.target.checked;
      saveSettings();
      if (state.results) {
        updateCommentsLive(panel, state.results.comments);
      }
    });

    // Settings: Track history checkbox
    panel.querySelector('#cg-track-history').addEventListener('change', (e) => {
      state.settings.trackHistory = e.target.checked;
      saveSettings();
    });

    // Settings: Detect sarcasm checkbox
    panel.querySelector('#cg-detect-sarcasm').addEventListener('change', (e) => {
      state.settings.detectSarcasm = e.target.checked;
      saveSettings();
    });

    // Batch mode handlers
    panel.querySelector('#cg-select-all-toxic')?.addEventListener('click', selectAllToxic);
    panel.querySelector('#cg-select-all')?.addEventListener('click', selectAll);
    panel.querySelector('#cg-deselect-all')?.addEventListener('click', deselectAll);
    panel.querySelector('#cg-batch-hide-btn')?.addEventListener('click', batchHide);
    panel.querySelector('#cg-batch-block-btn')?.addEventListener('click', batchBlock);
    panel.querySelector('#cg-batch-approve-btn')?.addEventListener('click', batchApprove);
    panel.querySelector('#cg-batch-export-btn')?.addEventListener('click', () => exportReport('csv', true));

    // Settings: Custom keywords
    panel.querySelector('#cg-keywords-save').addEventListener('click', () => {
      const input = panel.querySelector('#cg-keywords-input');
      const keywords = input.value.split(',').map(k => k.trim()).filter(k => k.length > 0);
      state.settings.customKeywords = [...new Set([...state.settings.customKeywords, ...keywords])];
      saveSettings();
      input.value = '';
      renderKeywordsList(panel);
    });

    // Settings: Whitelist
    panel.querySelector('#cg-whitelist-save').addEventListener('click', () => {
      const input = panel.querySelector('#cg-whitelist-input');
      const users = input.value.split(',').map(u => u.trim()).filter(u => u.length > 0);
      state.settings.whitelist = [...new Set([...state.settings.whitelist, ...users])];
      saveSettings();
      input.value = '';
      renderWhitelistList(panel);
    });

    // Settings: Toxicity threshold
    panel.querySelector('#cg-threshold').addEventListener('input', (e) => {
      const value = parseInt(e.target.value);
      state.settings.toxicityThreshold = value / 100;
      panel.querySelector('#cg-threshold-display').textContent = value;
      saveSettings();
    });

    // Initialize settings UI
    panel.querySelector('#cg-auto-hide').checked = state.settings.autoHide;
    panel.querySelector('#cg-notify').checked = state.settings.notifyHighToxicity;
    panel.querySelector('#cg-show-heatmap').checked = state.settings.showHeatmap !== false;
    panel.querySelector('#cg-reply-suggestions').checked = state.settings.showReplySuggestions !== false;
    panel.querySelector('#cg-track-history').checked = state.settings.trackHistory !== false;
    panel.querySelector('#cg-detect-sarcasm').checked = state.settings.detectSarcasm !== false;
    panel.querySelector('#cg-threshold').value = state.settings.toxicityThreshold * 100;
    panel.querySelector('#cg-threshold-display').textContent = Math.round(state.settings.toxicityThreshold * 100);
    renderKeywordsList(panel);
    renderWhitelistList(panel);

    // Copy reply button handler (delegated)
    panel.addEventListener('click', (e) => {
      if (e.target.classList.contains('cg-copy-reply')) {
        const text = e.target.dataset.text;
        navigator.clipboard.writeText(text).then(() => {
          e.target.textContent = '✓ Copied!';
          setTimeout(() => {
            e.target.textContent = '📋 Copy';
          }, 2000);
        });
      }
    });
  }

  // ── Analyze & Render ────────────────────────────────────────────────────────
  async function analyzeAndRender() {
    const panel = document.getElementById(PANEL_ID);
    if (!panel) return;

    // Check if backend is online
    if (!state.backendOnline) {
      showBackendRequiredMessage(panel);
      return;
    }

    // Update platform label
    panel.querySelector('#cg-platform-label').textContent = `Analyzing ${state.platform.name} with BERT ML...`;

    // Scrape comments
    const comments = state.platform.scrapeComments();
    console.log('[ContentGuard] Scraped comments:', comments);

    if (!comments || comments.length === 0) {
      panel.querySelector('#cg-platform-label').textContent = 'No comments found';
      panel.querySelector('#cg-comment-list').innerHTML = '<div class="cg-empty">No comments found. Try scrolling down.</div>';
      return;
    }

    // Initialize stats
    let totalAnalyzed = 0;
    let toxicCount = 0;
    let highToxicCount = 0;
    const analyzedComments = [];
    const authorStats = new Map();
    const sentimentCounts = { positive: 0, negative: 0, neutral: 0 };

    // Analyze comments one by one in real-time using BERT
    for (const comment of comments) {
      // Try BERT first, fallback to client-side if needed
      let analyzed;
      try {
        analyzed = await analyzeCommentWithBERT(comment);
        analyzed.usedML = true; // Mark as ML-analyzed
      } catch (error) {
        console.warn('[ContentGuard] BERT analysis failed, using client-side:', error);
        analyzed = analyzeCommentClientSide(comment);
        analyzed.usedML = false;
      }
      
      analyzedComments.push(analyzed);
      totalAnalyzed++;
      
      if (analyzed.is_toxic) toxicCount++;
      if (analyzed.severity === 'HIGH' || analyzed.severity === 'CRITICAL') highToxicCount++;
      
      // Count sentiment
      sentimentCounts[analyzed.sentiment]++;
      
      // Update author stats
      if (!authorStats.has(analyzed.author)) {
        authorStats.set(analyzed.author, { author: analyzed.author, toxicCount: 0, totalComments: 0, maxSeverity: 'NONE', worstAction: 'ALLOW' });
      }
      const authorEntry = authorStats.get(analyzed.author);
      authorEntry.totalComments++;
      if (analyzed.is_toxic) authorEntry.toxicCount++;
      if (analyzed.severity === 'HIGH' || analyzed.severity === 'CRITICAL') authorEntry.maxSeverity = analyzed.severity;
      if (analyzed.action === 'BLOCK' || analyzed.action === 'HIDE') authorEntry.worstAction = analyzed.action;
      
      // Update UI every 5 comments or on last comment
      if (totalAnalyzed % 5 === 0 || totalAnalyzed === comments.length) {
        updateStatsLive(panel, totalAnalyzed, toxicCount, sentimentCounts);
        updateCommentsLive(panel, analyzedComments);
        updateBlockListLive(panel, authorStats);
        panel.querySelector('#cg-platform-label').textContent = 
          `${state.platform.name} · ${totalAnalyzed}/${comments.length} analyzed`;
      }
      
      // Small delay to show progress (remove for instant)
      if (totalAnalyzed % 10 === 0) {
        await new Promise(resolve => setTimeout(resolve, 10));
      }
    }

    // Final update
    panel.querySelector('#cg-platform-label').textContent = `${state.platform.name} · ${totalAnalyzed} comments`;
    
    // Store results
    state.results = {
      comments: analyzedComments,
      stats: {
        total: totalAnalyzed,
        toxicCount: toxicCount,
        safeCount: totalAnalyzed - toxicCount,
        toxicPercent: Math.round((toxicCount / totalAnalyzed) * 100),
        safePercent: Math.round(((totalAnalyzed - toxicCount) / totalAnalyzed) * 100),
        sentimentCounts: sentimentCounts
      }
    };

    // Calculate and render community health
    state.communityHealth = calculateCommunityHealth(analyzedComments, state.results.stats);
    renderCommunityHealth(panel, state.communityHealth);

    // Save to history
    saveToHistory(state.results.stats);

    // Calculate user reputation
    const userStats = calculateUserReputation(analyzedComments);
    state.userReputation = userStats;

    // Render analytics tab
    renderHeatmap(panel, analyzedComments);
    renderTrendChart(panel);
    renderReputationList(panel, userStats);

    // Render batch moderation list
    renderBatchList(panel, analyzedComments);

    // Generate and render AI insights
    const insights = generateAIInsights(analyzedComments);
    renderAIInsights(panel, insights);

    // Apply auto-hide if enabled
    if (state.settings.autoHide) {
      applyAutoHide();
    }

    // Notify if high toxicity detected
    if (highToxicCount > 0) {
      notifyHighToxicity(highToxicCount);
    }
  }

  function analyzeCommentClientSide(comment) {
    // Check whitelist first
    if (state.settings.whitelist.includes(comment.author)) {
      return {
        ...comment,
        is_toxic: false,
        predictions: { toxic: 0 },
        action: 'ALLOW',
        severity: 'NONE',
        confidence: 0,
        primary_label: 'none',
        sentiment: 'neutral'
      };
    }

    // Expanded toxic keywords with more variations
    const toxicKeywords = [
      'idiot', 'stupid', 'hate', 'kill', 'die', 'fuck', 'shit', 'damn', 'ass', 'bitch', 
      'dumb', 'moron', 'loser', 'ugly', 'fat', 'retard', 'crap', 'suck', 'trash', 'garbage',
      'hell', 'bastard', 'piss', 'dick', 'cock', 'pussy', 'whore', 'slut', 'fag', 'nigger',
      'retarded', 'autistic', 'cancer', 'kys', 'stfu', 'gtfo', 'screw', 'sucks', 'pathetic',
      'worthless', 'useless', 'disgusting', 'vile', 'scum', 'filth', 'degenerate'
    ];
    
    // Add custom keywords
    const allKeywords = [...toxicKeywords, ...state.settings.customKeywords.map(k => k.toLowerCase())];
    
    const text = comment.text.toLowerCase();
    let toxicScore = 0;
    let matchedKeywords = [];
    
    // Check for keyword matches (higher score per match)
    allKeywords.forEach(keyword => {
      if (text.includes(keyword)) {
        toxicScore += 0.5; // Increased from 0.35 to 0.5
        matchedKeywords.push(keyword);
      }
    });
    
    // Check for aggressive patterns
    if (text.match(/\b(you('re| are) (an? )?(idiot|stupid|dumb|moron))\b/i)) {
      toxicScore += 0.3; // Personal attack
    }
    if (text.match(/\b(go (to )?hell|burn in hell|rot in hell)\b/i)) {
      toxicScore += 0.4; // Severe insult
    }
    if (text.match(/\b(kill yourself|kys|end yourself)\b/i)) {
      toxicScore += 0.9; // Extremely toxic
    }
    if (text.match(/\b(shut (the )?(fuck )?up|stfu)\b/i)) {
      toxicScore += 0.3; // Aggressive
    }
    
    // Check for excessive caps (shouting)
    const capsRatio = (text.match(/[A-Z]/g) || []).length / text.length;
    if (capsRatio > 0.5 && text.length > 10) {
      toxicScore += 0.2; // Aggressive tone
    }
    
    // Check for excessive punctuation (!!!, ???)
    if (text.match(/[!?]{3,}/)) {
      toxicScore += 0.1; // Aggressive tone
    }
    
    toxicScore = Math.min(toxicScore, 0.99);
    
    // AI Context Analysis - Sarcasm Detection
    let isSarcasm = false;
    let contextNote = '';
    if (state.settings.detectSarcasm && toxicScore > 0.3) {
      const sarcasmResult = detectSarcasm(comment.text, toxicScore);
      isSarcasm = sarcasmResult.isSarcasm;
      contextNote = sarcasmResult.note;
      
      // Reduce toxicity score if sarcasm detected
      if (isSarcasm) {
        toxicScore = toxicScore * 0.4; // Reduce by 60%
        console.log('[ContentGuard] Sarcasm detected, reduced score:', toxicScore);
      }
    }
    
    // Use threshold from settings (default 0.5 instead of 0.7)
    const threshold = state.settings.toxicityThreshold || 0.5;
    const isToxic = toxicScore >= threshold;
    
    let action = 'ALLOW';
    let severity = 'NONE';
    
    if (toxicScore >= 0.8) {
      action = 'BLOCK';
      severity = 'CRITICAL';
    } else if (toxicScore >= 0.6) {
      action = 'HIDE';
      severity = 'HIGH';
    } else if (toxicScore >= threshold) {
      action = 'WARNING';
      severity = 'MEDIUM';
    } else if (toxicScore >= 0.3) {
      action = 'WARNING';
      severity = 'LOW';
    }

    // Sentiment analysis
    const sentiment = analyzeSentiment(comment.text);
    
    // Debug logging
    if (toxicScore > 0) {
      console.log('[ContentGuard] Toxic detected:', {
        text: comment.text.substring(0, 50),
        score: toxicScore,
        threshold: threshold,
        isToxic: isToxic,
        matched: matchedKeywords
      });
    }
    
    return {
      ...comment,
      is_toxic: isToxic,
      predictions: { toxic: toxicScore },
      action: action,
      severity: severity,
      confidence: toxicScore,
      primary_label: isToxic ? 'toxic' : 'none',
      sentiment: sentiment,
      matchedKeywords: matchedKeywords, // For debugging
      isSarcasm: isSarcasm,
      contextNote: contextNote
    };
  }

  // ── Sentiment Analysis ──────────────────────────────────────────────────────
  function analyzeSentiment(text) {
    const positiveWords = ['good', 'great', 'excellent', 'amazing', 'love', 'wonderful', 'fantastic', 'awesome', 'best', 'perfect', 'nice', 'happy', 'thanks', 'thank', 'appreciate', 'helpful', 'brilliant', 'beautiful', 'agree', 'correct', 'right', 'yes', 'exactly'];
    const negativeWords = ['bad', 'terrible', 'awful', 'horrible', 'hate', 'worst', 'poor', 'disappointing', 'useless', 'wrong', 'no', 'never', 'nothing', 'nobody', 'nowhere', 'sad', 'angry', 'annoying', 'stupid', 'dumb', 'idiot'];
    
    const lowerText = text.toLowerCase();
    let positiveCount = 0;
    let negativeCount = 0;
    
    positiveWords.forEach(word => {
      if (lowerText.includes(word)) positiveCount++;
    });
    
    negativeWords.forEach(word => {
      if (lowerText.includes(word)) negativeCount++;
    });
    
    if (positiveCount > negativeCount) return 'positive';
    if (negativeCount > positiveCount) return 'negative';
    return 'neutral';
  }

  // ── Sarcasm Detection (AI Context Analysis) ─────────────────────────────────
  function detectSarcasm(text, toxicScore) {
    const lowerText = text.toLowerCase();
    let sarcasmScore = 0;
    const indicators = [];
    
    // Sarcasm indicators
    const sarcasmMarkers = [
      { pattern: /\blol\b|\blmao\b|\bhaha\b|\blmfao\b/i, weight: 0.3, label: 'laughter' },
      { pattern: /\bjk\b|\bjust kidding\b|\bkidding\b/i, weight: 0.5, label: 'explicit joke' },
      { pattern: /\/s\b|\bsarcasm\b/i, weight: 0.9, label: 'sarcasm tag' },
      { pattern: /😂|🤣|😅|😆/g, weight: 0.25, label: 'laughing emoji' },
      { pattern: /\byeah right\b|\bsure\b.*\b(buddy|pal|friend)\b/i, weight: 0.4, label: 'sarcastic phrase' },
      { pattern: /\boh (really|wow|great)\b/i, weight: 0.3, label: 'sarcastic exclamation' },
      { pattern: /"[^"]+"/g, weight: 0.2, label: 'air quotes' },
      { pattern: /\.\.\./g, weight: 0.15, label: 'ellipsis' }
    ];
    
    sarcasmMarkers.forEach(marker => {
      const matches = text.match(marker.pattern);
      if (matches) {
        sarcasmScore += marker.weight * matches.length;
        indicators.push(marker.label);
      }
    });
    
    // Context clues: positive words + toxic words = likely sarcasm
    const positiveWords = ['great', 'wonderful', 'amazing', 'perfect', 'excellent', 'brilliant'];
    const hasPositive = positiveWords.some(word => lowerText.includes(word));
    if (hasPositive && toxicScore > 0.5) {
      sarcasmScore += 0.3;
      indicators.push('positive + toxic mix');
    }
    
    // Exaggeration patterns
    if (text.match(/!{2,}/)) {
      sarcasmScore += 0.1;
      indicators.push('excessive punctuation');
    }
    
    const isSarcasm = sarcasmScore >= 0.5;
    const note = isSarcasm ? `Likely sarcasm/joke (${indicators.join(', ')})` : '';
    
    return { isSarcasm, sarcasmScore, note };
  }

  // ── BERT ML Analysis ────────────────────────────────────────────────────────
  async function analyzeCommentWithBERT(comment) {
    try {
      const response = await sendMessage({
        type: 'ANALYZE_COMMENT',
        comment: comment
      });

      if (!response || !response.success) {
        throw new Error('BERT analysis failed');
      }

      const result = response.result;
      
      // Apply sarcasm detection on top of BERT results
      let toxicScore = result.predictions?.toxic || 0;
      let isSarcasm = false;
      let contextNote = '';
      
      if (state.settings.detectSarcasm && toxicScore > 0.3) {
        const sarcasmResult = detectSarcasm(comment.text, toxicScore);
        isSarcasm = sarcasmResult.isSarcasm;
        contextNote = sarcasmResult.note;
        
        // Reduce toxicity score if sarcasm detected
        if (isSarcasm) {
          toxicScore = toxicScore * 0.4; // Reduce by 60%
          console.log('[ContentGuard] BERT + Sarcasm: reduced score from', result.predictions.toxic, 'to', toxicScore);
        }
      }

      // Determine severity and action based on adjusted score
      let action = 'ALLOW';
      let severity = 'NONE';
      
      if (toxicScore >= 0.8) {
        action = 'BLOCK';
        severity = 'CRITICAL';
      } else if (toxicScore >= 0.6) {
        action = 'HIDE';
        severity = 'HIGH';
      } else if (toxicScore >= state.settings.toxicityThreshold) {
        action = 'WARNING';
        severity = 'MEDIUM';
      } else if (toxicScore >= 0.3) {
        action = 'WARNING';
        severity = 'LOW';
      }

      return {
        ...comment,
        is_toxic: toxicScore >= state.settings.toxicityThreshold,
        predictions: { toxic: toxicScore },
        action: action,
        severity: severity,
        confidence: result.confidence || toxicScore,
        primary_label: result.primary_label || (toxicScore >= state.settings.toxicityThreshold ? 'toxic' : 'none'),
        sentiment: analyzeSentiment(comment.text),
        isSarcasm: isSarcasm,
        contextNote: contextNote,
        usedML: true,
        modelName: 'BERT',
        modelAccuracy: 92.8
      };
    } catch (error) {
      console.error('[ContentGuard] BERT analysis error:', error);
      throw error;
    }
  }

  // ── Backend Required Message ────────────────────────────────────────────────
  function showBackendRequiredMessage(panel) {
    panel.querySelector('#cg-platform-label').textContent = 'Backend Required';
    
    const content = panel.querySelector('#cg-content');
    if (!content) return;
    
    // Hide tabs
    const tabs = panel.querySelector('.cg-tabs');
    if (tabs) tabs.style.display = 'none';
    
    // Show message in all tab contents
    const tabContents = panel.querySelectorAll('.cg-tab-content');
    tabContents.forEach(tab => {
      tab.innerHTML = `
        <div class="cg-backend-required">
          <div class="cg-ml-icon">🤖</div>
          <div class="cg-ml-title">BERT ML Model Required</div>
          <div class="cg-ml-subtitle">ContentGuard uses a trained BERT transformer model for accurate toxicity detection</div>
          
          <div class="cg-ml-stats">
            <div class="cg-ml-stat">
              <div class="cg-ml-stat-value">92.8%</div>
              <div class="cg-ml-stat-label">Model Accuracy</div>
            </div>
            <div class="cg-ml-stat">
              <div class="cg-ml-stat-value">10K</div>
              <div class="cg-ml-stat-label">Training Samples</div>
            </div>
            <div class="cg-ml-stat">
              <div class="cg-ml-stat-value">BERT</div>
              <div class="cg-ml-stat-label">Transformer Model</div>
            </div>
          </div>

          <div class="cg-ml-instructions">
            <div class="cg-ml-step">
              <div class="cg-ml-step-number">1</div>
              <div class="cg-ml-step-text">
                <strong>Open Terminal</strong>
                <code>cd c:\\Users\\AMISHA\\Desktop\\Codes\\content-moderation-system-main</code>
              </div>
            </div>
            <div class="cg-ml-step">
              <div class="cg-ml-step-number">2</div>
              <div class="cg-ml-step-text">
                <strong>Start Backend</strong>
                <code>python -m uvicorn api.main:app --reload</code>
              </div>
            </div>
            <div class="cg-ml-step">
              <div class="cg-ml-step-number">3</div>
              <div class="cg-ml-step-text">
                <strong>Wait for BERT to Load</strong>
                <span>Backend will start at http://localhost:8000</span>
              </div>
            </div>
            <div class="cg-ml-step">
              <div class="cg-ml-step-number">4</div>
              <div class="cg-ml-step-text">
                <strong>Refresh This Page</strong>
                <span>The status dot will turn green when ready</span>
              </div>
            </div>
          </div>

          <div class="cg-ml-features">
            <div class="cg-ml-feature">✅ Deep learning-based detection</div>
            <div class="cg-ml-feature">✅ Context-aware analysis</div>
            <div class="cg-ml-feature">✅ Multi-label classification</div>
            <div class="cg-ml-feature">✅ Trained on Jigsaw dataset</div>
          </div>

          <button class="cg-ml-retry" onclick="location.reload()">
            🔄 Check Backend Status
          </button>
        </div>
      `;
    });
  }

  // ── Community Health Calculator ─────────────────────────────────────────────
  function calculateCommunityHealth(comments, stats) {
    // Health score components (0-100 each)
    const toxicityRate = 100 - stats.toxicPercent; // Lower toxicity = better
    
    // User engagement (based on comment length and variety)
    const avgLength = comments.reduce((sum, c) => sum + c.text.length, 0) / comments.length;
    const engagement = Math.min(100, (avgLength / 200) * 100); // 200 chars = 100%
    
    // Sentiment balance (more positive = better)
    const positivePercent = (stats.sentimentCounts.positive / stats.total) * 100;
    const sentimentBalance = Math.min(100, positivePercent * 1.5);
    
    // Moderation effectiveness (based on action distribution)
    const allowedPercent = (comments.filter(c => c.action === 'ALLOW').length / comments.length) * 100;
    const moderation = allowedPercent; // Higher allowed = better moderation
    
    // Overall health score (weighted average)
    const healthScore = Math.round(
      toxicityRate * 0.4 +
      engagement * 0.2 +
      sentimentBalance * 0.2 +
      moderation * 0.2
    );
    
    // Determine status
    let status = '';
    let statusColor = '';
    if (healthScore >= 80) {
      status = '🎉 Excellent - Very healthy community!';
      statusColor = 'var(--cg-green)';
    } else if (healthScore >= 60) {
      status = '✅ Good - Community is doing well';
      statusColor = 'var(--cg-cyan)';
    } else if (healthScore >= 40) {
      status = '⚠️ Fair - Needs attention';
      statusColor = 'var(--cg-yellow)';
    } else if (healthScore >= 20) {
      status = '🔴 Poor - Requires moderation';
      statusColor = 'var(--cg-orange)';
    } else {
      status = '🚨 Critical - Immediate action needed';
      statusColor = 'var(--cg-red)';
    }
    
    // Calculate trend
    const history = loadHistory();
    let trend = 'stable';
    let trendArrow = '→';
    if (history.length >= 2) {
      const prev = history[history.length - 2];
      const current = stats.toxicPercent;
      const diff = prev.toxicPercent - current; // Positive diff = improving
      
      if (diff > 10) {
        trend = 'improving';
        trendArrow = '↗️';
      } else if (diff < -10) {
        trend = 'declining';
        trendArrow = '↘️';
      }
    }
    
    return {
      healthScore,
      status,
      statusColor,
      metrics: {
        toxicityRate: Math.round(toxicityRate),
        engagement: Math.round(engagement),
        sentimentBalance: Math.round(sentimentBalance),
        moderation: Math.round(moderation)
      },
      trend,
      trendArrow
    };
  }

  function renderCommunityHealth(panel, health) {
    if (!health) return;
    
    // Update gauge
    const circle = panel.querySelector('#cg-health-circle');
    const value = panel.querySelector('#cg-health-value');
    const status = panel.querySelector('#cg-health-status');
    
    if (circle && value && status) {
      const circumference = 502.4;
      const offset = circumference - (health.healthScore / 100) * circumference;
      
      circle.style.strokeDashoffset = offset;
      value.textContent = health.healthScore;
      status.textContent = health.status;
      status.style.color = health.statusColor;
      
      // Update gradient based on score
      const gradient = circle.ownerSVGElement.querySelector('#healthGradient');
      if (gradient) {
        const stops = gradient.querySelectorAll('stop');
        if (health.healthScore >= 70) {
          stops[0].style.stopColor = '#10B981';
          stops[1].style.stopColor = '#06B6D4';
        } else if (health.healthScore >= 40) {
          stops[0].style.stopColor = '#F59E0B';
          stops[1].style.stopColor = '#F97316';
        } else {
          stops[0].style.stopColor = '#EF4444';
          stops[1].style.stopColor = '#B91C1C';
        }
      }
    }
    
    // Update metrics
    panel.querySelector('#cg-metric-toxicity').textContent = health.metrics.toxicityRate + '%';
    panel.querySelector('#cg-metric-engagement').textContent = health.metrics.engagement + '%';
    panel.querySelector('#cg-metric-sentiment').textContent = health.metrics.sentimentBalance + '%';
    panel.querySelector('#cg-metric-moderation').textContent = health.metrics.moderation + '%';
    
    // Update trend
    const trendIndicator = panel.querySelector('#cg-trend-indicator');
    if (trendIndicator) {
      trendIndicator.innerHTML = `
        <span class="cg-trend-arrow">${health.trendArrow}</span>
        <span class="cg-trend-text">${health.trend.charAt(0).toUpperCase() + health.trend.slice(1)}</span>
      `;
      
      if (health.trend === 'improving') {
        trendIndicator.style.color = 'var(--cg-green)';
      } else if (health.trend === 'declining') {
        trendIndicator.style.color = 'var(--cg-red)';
      } else {
        trendIndicator.style.color = 'var(--cg-text-muted)';
      }
    }
  }

  // ── Batch Moderation Functions ──────────────────────────────────────────────
  function selectAllToxic() {
    if (!state.results) return;
    state.selectedComments.clear();
    state.results.comments.forEach(c => {
      if (c.is_toxic) state.selectedComments.add(c.id || c.text);
    });
    updateBatchUI();
  }

  function selectAll() {
    if (!state.results) return;
    state.selectedComments.clear();
    state.results.comments.forEach(c => {
      state.selectedComments.add(c.id || c.text);
    });
    updateBatchUI();
  }

  function deselectAll() {
    state.selectedComments.clear();
    updateBatchUI();
  }

  function batchHide() {
    if (state.selectedComments.size === 0) {
      alert('No comments selected');
      return;
    }
    
    const count = state.selectedComments.size;
    if (confirm(`Hide ${count} selected comment${count > 1 ? 's' : ''}?`)) {
      // Apply hide to selected comments
      state.results.comments.forEach(c => {
        if (state.selectedComments.has(c.id || c.text)) {
          const elements = findCommentElements(c.text);
          elements.forEach(el => {
            el.style.opacity = '0.3';
            el.style.filter = 'blur(5px)';
          });
        }
      });
      
      alert(`${count} comment${count > 1 ? 's' : ''} hidden`);
      deselectAll();
    }
  }

  function batchBlock() {
    if (state.selectedComments.size === 0) {
      alert('No comments selected');
      return;
    }
    
    const users = new Set();
    state.results.comments.forEach(c => {
      if (state.selectedComments.has(c.id || c.text)) {
        users.add(c.author);
      }
    });
    
    const count = users.size;
    if (confirm(`Block ${count} user${count > 1 ? 's' : ''}?`)) {
      alert(`${count} user${count > 1 ? 's' : ''} blocked (feature demo)`);
      deselectAll();
    }
  }

  function batchApprove() {
    if (state.selectedComments.size === 0) {
      alert('No comments selected');
      return;
    }
    
    const count = state.selectedComments.size;
    if (confirm(`Approve ${count} selected comment${count > 1 ? 's' : ''}?`)) {
      alert(`${count} comment${count > 1 ? 's' : ''} approved`);
      deselectAll();
    }
  }

  function updateBatchUI() {
    const panel = document.getElementById(PANEL_ID);
    if (!panel) return;
    
    const countEl = panel.querySelector('#cg-batch-count');
    if (countEl) {
      countEl.textContent = state.selectedComments.size;
    }
    
    // Update checkboxes
    panel.querySelectorAll('.cg-batch-checkbox').forEach(checkbox => {
      const commentId = checkbox.dataset.commentId;
      checkbox.checked = state.selectedComments.has(commentId);
    });
  }

  function renderBatchList(panel, comments) {
    const list = panel.querySelector('#cg-batch-list');
    if (!list) return;
    
    if (!comments || comments.length === 0) {
      list.innerHTML = '<div class="cg-empty">No comments to display</div>';
      return;
    }
    
    list.innerHTML = comments.map(c => {
      const commentId = c.id || c.text;
      const isSelected = state.selectedComments.has(commentId);
      
      return `
        <div class="cg-batch-item ${c.is_toxic ? 'cg-batch-toxic' : ''}">
          <input type="checkbox" class="cg-batch-checkbox" data-comment-id="${escapeHTML(commentId)}" ${isSelected ? 'checked' : ''} />
          <div class="cg-batch-content">
            <div class="cg-batch-author">${escapeHTML(c.author)}</div>
            <div class="cg-batch-text">${escapeHTML(c.text.substring(0, 100))}${c.text.length > 100 ? '...' : ''}</div>
            <div class="cg-batch-meta">
              <span class="cg-batch-score" style="color: ${c.is_toxic ? 'var(--cg-red)' : 'var(--cg-green)'};">
                ${Math.round(c.confidence * 100)}% ${c.is_toxic ? 'toxic' : 'safe'}
              </span>
              ${c.isSarcasm ? '<span class="cg-sarcasm-badge">😏 Sarcasm</span>' : ''}
            </div>
          </div>
        </div>
      `;
    }).join('');
    
    // Bind checkbox events
    list.querySelectorAll('.cg-batch-checkbox').forEach(checkbox => {
      checkbox.addEventListener('change', (e) => {
        const commentId = checkbox.dataset.commentId;
        if (e.target.checked) {
          state.selectedComments.add(commentId);
        } else {
          state.selectedComments.delete(commentId);
        }
        updateBatchUI();
      });
    });
  }

  // ── Settings Persistence ────────────────────────────────────────────────────
  function loadSettings() {
    try {
      const saved = localStorage.getItem('contentguard_settings');
      if (saved) {
        const parsed = JSON.parse(saved);
        state.settings = { ...state.settings, ...parsed };
      }
    } catch (e) {
      console.error('[ContentGuard] Failed to load settings:', e);
    }
  }

  function saveSettings() {
    try {
      localStorage.setItem('contentguard_settings', JSON.stringify(state.settings));
    } catch (e) {
      console.error('[ContentGuard] Failed to save settings:', e);
    }
  }

  function renderKeywordsList(panel) {
    const list = panel.querySelector('#cg-keywords-list');
    if (state.settings.customKeywords.length === 0) {
      list.innerHTML = '<div style="font-size: 11px; color: var(--cg-text-dim); margin-top: 8px;">No custom keywords added</div>';
      return;
    }
    list.innerHTML = state.settings.customKeywords.map(keyword => `
      <span class="cg-keyword-chip">
        ${escapeHTML(keyword)}
        <button class="cg-keyword-remove" data-keyword="${escapeHTML(keyword)}">×</button>
      </span>
    `).join('');
    
    // Bind remove buttons
    list.querySelectorAll('.cg-keyword-remove').forEach(btn => {
      btn.addEventListener('click', () => {
        const keyword = btn.dataset.keyword;
        state.settings.customKeywords = state.settings.customKeywords.filter(k => k !== keyword);
        saveSettings();
        renderKeywordsList(panel);
      });
    });
  }

  function renderWhitelistList(panel) {
    const list = panel.querySelector('#cg-whitelist-list');
    if (state.settings.whitelist.length === 0) {
      list.innerHTML = '<div style="font-size: 11px; color: var(--cg-text-dim); margin-top: 8px;">No whitelisted users</div>';
      return;
    }
    list.innerHTML = state.settings.whitelist.map(user => `
      <span class="cg-keyword-chip">
        ${escapeHTML(user)}
        <button class="cg-keyword-remove" data-user="${escapeHTML(user)}">×</button>
      </span>
    `).join('');
    
    // Bind remove buttons
    list.querySelectorAll('.cg-keyword-remove').forEach(btn => {
      btn.addEventListener('click', () => {
        const user = btn.dataset.user;
        state.settings.whitelist = state.settings.whitelist.filter(u => u !== user);
        saveSettings();
        renderWhitelistList(panel);
      });
    });
  }

  // ── Export Report ───────────────────────────────────────────────────────────
  function exportReport(format = 'csv', selectedOnly = false) {
    if (!state.results || !state.results.comments) {
      alert('No data to export. Please analyze comments first.');
      return;
    }

    const comments = selectedOnly 
      ? state.results.comments.filter(c => state.selectedComments.has(c.id || c.text))
      : state.results.comments;

    if (comments.length === 0) {
      alert('No comments to export.');
      return;
    }

    let content, mimeType, extension;

    switch (format) {
      case 'json':
        content = generateJSON(comments);
        mimeType = 'application/json';
        extension = 'json';
        break;
      case 'pdf':
        generatePDF(comments);
        return; // PDF generation handles download internally
      case 'csv':
      default:
        content = generateCSV(comments);
        mimeType = 'text/csv;charset=utf-8;';
        extension = 'csv';
    }

    const blob = new Blob([content], { type: mimeType });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `contentguard-report-${Date.now()}.${extension}`;
    link.click();
    URL.revokeObjectURL(url);
  }

  function generateCSV(comments) {
    const headers = ['Author', 'Text', 'Is Toxic', 'Toxicity Score', 'Action', 'Severity', 'Sentiment', 'Sarcasm', 'Context Note'];
    const rows = comments.map(c => [
      c.author || 'Unknown',
      c.text.replace(/"/g, '""'), // Escape quotes
      c.is_toxic ? 'Yes' : 'No',
      (c.predictions?.toxic || 0).toFixed(3),
      c.action || 'ALLOW',
      c.severity || 'NONE',
      c.sentiment || 'neutral',
      c.isSarcasm ? 'Yes' : 'No',
      c.contextNote || ''
    ]);
    
    const csvContent = [
      headers.join(','),
      ...rows.map(row => row.map(cell => `"${cell}"`).join(','))
    ].join('\n');
    
    return csvContent;
  }

  function generateJSON(comments) {
    const report = {
      generated: new Date().toISOString(),
      platform: state.platform.name,
      url: location.href,
      stats: state.results.stats,
      communityHealth: state.communityHealth,
      comments: comments.map(c => ({
        author: c.author,
        text: c.text,
        isToxic: c.is_toxic,
        toxicityScore: c.predictions?.toxic || 0,
        action: c.action,
        severity: c.severity,
        sentiment: c.sentiment,
        isSarcasm: c.isSarcasm,
        contextNote: c.contextNote,
        matchedKeywords: c.matchedKeywords
      }))
    };
    
    return JSON.stringify(report, null, 2);
  }

  function generatePDF(comments) {
    // Simple PDF generation using HTML and print
    const reportWindow = window.open('', '_blank');
    const html = `
      <!DOCTYPE html>
      <html>
      <head>
        <title>ContentGuard Report</title>
        <style>
          body { font-family: Arial, sans-serif; padding: 20px; }
          h1 { color: #7C3AED; }
          .stats { display: grid; grid-template-columns: repeat(3, 1fr); gap: 15px; margin: 20px 0; }
          .stat-card { border: 2px solid #7C3AED; border-radius: 8px; padding: 15px; text-align: center; }
          .stat-value { font-size: 32px; font-weight: bold; color: #7C3AED; }
          .stat-label { font-size: 14px; color: #666; margin-top: 5px; }
          table { width: 100%; border-collapse: collapse; margin-top: 20px; }
          th, td { border: 1px solid #ddd; padding: 12px; text-align: left; }
          th { background-color: #7C3AED; color: white; }
          .toxic { background-color: #fee; }
          .safe { background-color: #efe; }
          @media print { button { display: none; } }
        </style>
      </head>
      <body>
        <h1>🛡️ ContentGuard Moderation Report</h1>
        <p><strong>Platform:</strong> ${state.platform.name}</p>
        <p><strong>URL:</strong> ${location.href}</p>
        <p><strong>Generated:</strong> ${new Date().toLocaleString()}</p>
        
        <div class="stats">
          <div class="stat-card">
            <div class="stat-value">${state.results.stats.total}</div>
            <div class="stat-label">Total Comments</div>
          </div>
          <div class="stat-card">
            <div class="stat-value">${state.results.stats.toxicCount}</div>
            <div class="stat-label">Toxic (${state.results.stats.toxicPercent}%)</div>
          </div>
          <div class="stat-card">
            <div class="stat-value">${state.results.stats.safeCount}</div>
            <div class="stat-label">Safe (${state.results.stats.safePercent}%)</div>
          </div>
        </div>

        ${state.communityHealth ? `
          <h2>Community Health Score: ${state.communityHealth.healthScore}/100</h2>
          <p>${state.communityHealth.status}</p>
        ` : ''}
        
        <h2>Comments Analysis</h2>
        <table>
          <thead>
            <tr>
              <th>Author</th>
              <th>Comment</th>
              <th>Toxic</th>
              <th>Score</th>
              <th>Action</th>
              <th>Sentiment</th>
            </tr>
          </thead>
          <tbody>
            ${comments.map(c => `
              <tr class="${c.is_toxic ? 'toxic' : 'safe'}">
                <td>${escapeHTML(c.author)}</td>
                <td>${escapeHTML(c.text.substring(0, 100))}${c.text.length > 100 ? '...' : ''}</td>
                <td>${c.is_toxic ? '🔴 Yes' : '🟢 No'}</td>
                <td>${Math.round((c.predictions?.toxic || 0) * 100)}%</td>
                <td>${c.action}</td>
                <td>${c.sentiment}</td>
              </tr>
            `).join('')}
          </tbody>
        </table>
        
        <button onclick="window.print()" style="margin-top: 20px; padding: 10px 20px; background: #7C3AED; color: white; border: none; border-radius: 8px; cursor: pointer; font-size: 16px;">
          Print / Save as PDF
        </button>
      </body>
      </html>
    `;
    
    reportWindow.document.write(html);
    reportWindow.document.close();
  }

  // ── Auto-Hide Toxic Comments ────────────────────────────────────────────────
  function applyAutoHide() {
    if (!state.results || !state.results.comments) return;
    
    const toxicComments = state.results.comments.filter(c => c.is_toxic);
    console.log('[ContentGuard] Auto-hiding', toxicComments.length, 'toxic comments');
    
    // Find and hide toxic comments on the actual page
    toxicComments.forEach(comment => {
      const elements = findCommentElements(comment.text);
      elements.forEach(el => {
        if (!el.dataset.cgHidden) {
          el.dataset.cgHidden = 'true';
          el.dataset.cgOriginalDisplay = el.style.display || '';
          el.style.opacity = '0.3';
          el.style.filter = 'blur(5px)';
          el.style.pointerEvents = 'none';
          el.style.userSelect = 'none';
          
          // Add overlay
          const overlay = document.createElement('div');
          overlay.className = 'cg-hidden-overlay';
          overlay.innerHTML = `
            <div style="background: rgba(239, 68, 68, 0.9); color: white; padding: 8px 12px; border-radius: 8px; font-size: 12px; font-weight: 600; cursor: pointer;">
              🚫 Hidden by ContentGuard (Click to reveal)
            </div>
          `;
          overlay.style.cssText = 'position: absolute; top: 0; left: 0; right: 0; bottom: 0; display: flex; align-items: center; justify-content: center; z-index: 10; background: rgba(0,0,0,0.1);';
          
          overlay.addEventListener('click', () => {
            el.style.opacity = '1';
            el.style.filter = 'none';
            el.style.pointerEvents = 'auto';
            el.style.userSelect = 'auto';
            overlay.remove();
          });
          
          if (el.style.position === 'static' || !el.style.position) {
            el.style.position = 'relative';
          }
          el.appendChild(overlay);
        }
      });
    });
  }

  function findCommentElements(text) {
    // Try to find DOM elements containing this exact text
    const elements = [];
    const selector = state.platform.commentSelector;
    
    document.querySelectorAll(selector).forEach(el => {
      if (el.textContent.includes(text.substring(0, 50))) {
        elements.push(el);
      }
    });
    
    return elements;
  }

  // ── Notifications ───────────────────────────────────────────────────────────
  function notifyHighToxicity(count) {
    if (!state.settings.notifyHighToxicity) return;
    if (count === 0) return;
    
    // Browser notification
    if ('Notification' in window && Notification.permission === 'granted') {
      new Notification('ContentGuard Alert', {
        body: `Found ${count} highly toxic comment${count > 1 ? 's' : ''} on this page`,
        icon: chrome.runtime.getURL('icons/icon48.png'),
        badge: chrome.runtime.getURL('icons/icon16.png')
      });
    } else if ('Notification' in window && Notification.permission !== 'denied') {
      Notification.requestPermission().then(permission => {
        if (permission === 'granted') {
          notifyHighToxicity(count);
        }
      });
    }
  }

  // ── AI Reply Suggestions ────────────────────────────────────────────────────
  function generateReplySuggestion(toxicText) {
    // Extract the core message without toxic language
    const suggestions = [
      "I understand your perspective, but let's keep the discussion respectful.",
      "I appreciate your input. Could we discuss this more constructively?",
      "I see your point. Let's focus on the facts rather than personal attacks.",
      "Thank you for sharing. I'd like to understand your viewpoint better.",
      "I respect your opinion, even though we may disagree on this.",
      "Let's try to have a productive conversation about this topic.",
      "I hear what you're saying. Can we explore this idea further?",
      "Your feedback is noted. Let's work together to find common ground."
    ];
    
    // Simple logic: pick based on text length
    const index = toxicText.length % suggestions.length;
    return suggestions[index];
  }

  // ── Explanation Generator ───────────────────────────────────────────────────
  function generateExplanation(comment) {
    const reasons = [];
    const text = comment.text.toLowerCase();
    
    // Check for specific patterns
    if (text.match(/\b(idiot|stupid|dumb|moron)\b/)) {
      reasons.push('personal insults');
    }
    if (text.match(/\b(hate|kill|die)\b/)) {
      reasons.push('threatening language');
    }
    if (text.match(/\b(fuck|shit|damn|ass|bitch)\b/)) {
      reasons.push('profanity');
    }
    
    // Check custom keywords
    state.settings.customKeywords.forEach(keyword => {
      if (text.includes(keyword.toLowerCase())) {
        reasons.push(`custom keyword "${keyword}"`);
      }
    });
    
    if (reasons.length === 0) {
      return `High toxicity score (${Math.round(comment.confidence * 100)}%)`;
    }
    
    return `Contains ${reasons.join(', ')} (${Math.round(comment.confidence * 100)}% confidence)`;
  }

  // ── Toxicity Heatmap ────────────────────────────────────────────────────────
  function renderHeatmap(panel, comments) {
    if (!state.settings.showHeatmap) return;
    
    const grid = panel.querySelector('#cg-heatmap-grid');
    if (!grid) return;
    
    // Create 10x10 grid representing comment distribution
    const gridSize = 100;
    const cellsPerRow = 10;
    const cells = [];
    
    // Distribute comments into cells
    comments.forEach((comment, index) => {
      const cellIndex = Math.floor((index / comments.length) * gridSize);
      if (!cells[cellIndex]) cells[cellIndex] = [];
      cells[cellIndex].push(comment);
    });
    
    // Render grid
    let html = '';
    for (let i = 0; i < gridSize; i++) {
      const cellComments = cells[i] || [];
      const avgToxicity = cellComments.length > 0
        ? cellComments.reduce((sum, c) => sum + (c.confidence || 0), 0) / cellComments.length
        : 0;
      
      let color = 'var(--cg-green)';
      if (avgToxicity > 0.8) color = 'var(--cg-red)';
      else if (avgToxicity > 0.5) color = 'var(--cg-orange)';
      else if (avgToxicity > 0.3) color = 'var(--cg-yellow)';
      
      html += `<div class="cg-heatmap-cell" style="background: ${color};" title="${cellComments.length} comments, ${Math.round(avgToxicity * 100)}% toxic"></div>`;
      
      if ((i + 1) % cellsPerRow === 0) html += '<br>';
    }
    
    grid.innerHTML = html;
  }

  // ── Trend Chart ─────────────────────────────────────────────────────────────
  function renderTrendChart(panel) {
    const canvas = panel.querySelector('#cg-trend-canvas');
    if (!canvas) return;
    
    const ctx = canvas.getContext('2d');
    const width = canvas.width;
    const height = canvas.height;
    
    // Clear canvas
    ctx.clearRect(0, 0, width, height);
    
    // Get history data
    const history = loadHistory();
    if (history.length === 0) {
      // Show "no data" message
      ctx.fillStyle = '#94A3B8';
      ctx.font = '13px Inter, sans-serif';
      ctx.textAlign = 'center';
      ctx.textBaseline = 'middle';
      ctx.fillText('No historical data yet', width / 2, height / 2);
      ctx.font = '11px Inter, sans-serif';
      ctx.fillStyle = '#64748B';
      ctx.fillText('Analyze comments multiple times to see trends', width / 2, height / 2 + 20);
      return;
    }
    
    // Prepare data
    const maxPoints = Math.min(history.length, 20);
    const recentHistory = history.slice(-maxPoints);
    const padding = { top: 20, right: 20, bottom: 30, left: 50 };
    const chartWidth = width - padding.left - padding.right;
    const chartHeight = height - padding.top - padding.bottom;
    
    // Draw background grid
    ctx.strokeStyle = 'rgba(255,255,255,0.05)';
    ctx.lineWidth = 1;
    
    // Horizontal grid lines
    for (let i = 0; i <= 4; i++) {
      const y = padding.top + (chartHeight / 4) * i;
      ctx.beginPath();
      ctx.moveTo(padding.left, y);
      ctx.lineTo(width - padding.right, y);
      ctx.stroke();
    }
    
    // Draw axes
    ctx.strokeStyle = 'rgba(255,255,255,0.2)';
    ctx.lineWidth = 2;
    ctx.beginPath();
    ctx.moveTo(padding.left, padding.top);
    ctx.lineTo(padding.left, height - padding.bottom);
    ctx.lineTo(width - padding.right, height - padding.bottom);
    ctx.stroke();
    
    // Draw Y-axis labels
    ctx.fillStyle = '#94A3B8';
    ctx.font = '10px Inter, sans-serif';
    ctx.textAlign = 'right';
    ctx.textBaseline = 'middle';
    for (let i = 0; i <= 4; i++) {
      const y = padding.top + (chartHeight / 4) * i;
      const value = 100 - (i * 25);
      ctx.fillText(value + '%', padding.left - 10, y);
    }
    
    // Draw data line
    if (recentHistory.length > 0) {
      const xStep = chartWidth / (maxPoints - 1 || 1);
      
      // Draw gradient fill
      const gradient = ctx.createLinearGradient(0, padding.top, 0, height - padding.bottom);
      gradient.addColorStop(0, 'rgba(124, 58, 237, 0.3)');
      gradient.addColorStop(1, 'rgba(124, 58, 237, 0.0)');
      
      ctx.fillStyle = gradient;
      ctx.beginPath();
      ctx.moveTo(padding.left, height - padding.bottom);
      
      recentHistory.forEach((entry, i) => {
        const x = padding.left + i * xStep;
        const y = height - padding.bottom - (entry.toxicPercent / 100) * chartHeight;
        if (i === 0) {
          ctx.lineTo(x, y);
        } else {
          ctx.lineTo(x, y);
        }
      });
      
      ctx.lineTo(padding.left + (recentHistory.length - 1) * xStep, height - padding.bottom);
      ctx.closePath();
      ctx.fill();
      
      // Draw line
      ctx.strokeStyle = '#7C3AED';
      ctx.lineWidth = 3;
      ctx.lineCap = 'round';
      ctx.lineJoin = 'round';
      ctx.beginPath();
      
      recentHistory.forEach((entry, i) => {
        const x = padding.left + i * xStep;
        const y = height - padding.bottom - (entry.toxicPercent / 100) * chartHeight;
        
        if (i === 0) {
          ctx.moveTo(x, y);
        } else {
          ctx.lineTo(x, y);
        }
      });
      
      ctx.stroke();
      
      // Draw points
      ctx.fillStyle = '#7C3AED';
      recentHistory.forEach((entry, i) => {
        const x = padding.left + i * xStep;
        const y = height - padding.bottom - (entry.toxicPercent / 100) * chartHeight;
        
        ctx.beginPath();
        ctx.arc(x, y, 4, 0, Math.PI * 2);
        ctx.fill();
        
        // Highlight last point
        if (i === recentHistory.length - 1) {
          ctx.strokeStyle = '#A78BFA';
          ctx.lineWidth = 2;
          ctx.beginPath();
          ctx.arc(x, y, 6, 0, Math.PI * 2);
          ctx.stroke();
        }
      });
      
      // Draw X-axis labels (show first, middle, last)
      ctx.fillStyle = '#64748B';
      ctx.font = '9px Inter, sans-serif';
      ctx.textAlign = 'center';
      ctx.textBaseline = 'top';
      
      if (recentHistory.length > 0) {
        // First point
        const firstDate = new Date(recentHistory[0].timestamp);
        ctx.fillText(firstDate.toLocaleDateString('en-US', { month: 'short', day: 'numeric' }), 
                     padding.left, height - padding.bottom + 5);
        
        // Last point
        const lastDate = new Date(recentHistory[recentHistory.length - 1].timestamp);
        ctx.fillText(lastDate.toLocaleDateString('en-US', { month: 'short', day: 'numeric' }), 
                     padding.left + (recentHistory.length - 1) * xStep, height - padding.bottom + 5);
      }
    }
  }

  // ── User Reputation System ──────────────────────────────────────────────────
  function calculateUserReputation(comments) {
    const userStats = new Map();
    
    comments.forEach(comment => {
      if (!userStats.has(comment.author)) {
        userStats.set(comment.author, {
          author: comment.author,
          totalComments: 0,
          toxicComments: 0,
          avgToxicity: 0,
          reputation: 100
        });
      }
      
      const stats = userStats.get(comment.author);
      stats.totalComments++;
      if (comment.is_toxic) stats.toxicComments++;
      stats.avgToxicity = (stats.avgToxicity * (stats.totalComments - 1) + (comment.confidence || 0)) / stats.totalComments;
    });
    
    // Calculate reputation score (0-100)
    userStats.forEach(stats => {
      const toxicRate = stats.toxicComments / stats.totalComments;
      stats.reputation = Math.max(0, Math.round(100 - (toxicRate * 100 + stats.avgToxicity * 50)));
    });
    
    return userStats;
  }

  function renderReputationList(panel, userStats) {
    const list = panel.querySelector('#cg-reputation-list');
    if (!list) return;
    
    const sortedUsers = Array.from(userStats.values())
      .sort((a, b) => a.reputation - b.reputation)
      .slice(0, 10);
    
    if (sortedUsers.length === 0) {
      list.innerHTML = '<div class="cg-empty-small">No users analyzed yet</div>';
      return;
    }
    
    list.innerHTML = sortedUsers.map(user => {
      const repColor = user.reputation > 70 ? 'var(--cg-green)' : user.reputation > 40 ? 'var(--cg-yellow)' : 'var(--cg-red)';
      return `
        <div class="cg-reputation-card">
          <div class="cg-rep-avatar">${escapeHTML(user.author).charAt(0).toUpperCase()}</div>
          <div class="cg-rep-info">
            <div class="cg-rep-name">${escapeHTML(user.author)}</div>
            <div class="cg-rep-stats">${user.totalComments} comments · ${user.toxicComments} toxic</div>
          </div>
          <div class="cg-rep-score" style="color: ${repColor};">
            <div class="cg-rep-value">${user.reputation}</div>
            <div class="cg-rep-label">REP</div>
          </div>
        </div>
      `;
    }).join('');
  }

  // ── AI Insights Generator ───────────────────────────────────────────────────
  function generateAIInsights(comments) {
    const total = comments.length;
    const toxic = comments.filter(c => c.is_toxic).length;
    const toxicPercent = Math.round((toxic / total) * 100);
    
    // Generate summary
    let summary = '';
    if (toxicPercent > 50) {
      summary = `⚠️ <strong>High toxicity detected!</strong> ${toxicPercent}% of comments are toxic. This community may need immediate moderation attention.`;
    } else if (toxicPercent > 20) {
      summary = `⚡ <strong>Moderate toxicity.</strong> ${toxicPercent}% of comments are toxic. Consider implementing stricter moderation policies.`;
    } else if (toxicPercent > 5) {
      summary = `✅ <strong>Healthy community.</strong> Only ${toxicPercent}% of comments are toxic. Current moderation appears effective.`;
    } else {
      summary = `🎉 <strong>Excellent community!</strong> Less than ${toxicPercent}% toxicity. This is a very positive environment.`;
    }
    
    // Detect patterns
    const patterns = [];
    const allText = comments.map(c => c.text.toLowerCase()).join(' ');
    
    if (allText.match(/\b(idiot|stupid|dumb)\b/g)?.length > 3) {
      patterns.push('• Frequent personal insults detected');
    }
    if (allText.match(/\b(hate|kill|die)\b/g)?.length > 2) {
      patterns.push('• Threatening language present');
    }
    if (allText.match(/\b(fuck|shit)\b/g)?.length > 5) {
      patterns.push('• High profanity usage');
    }
    
    // Generate recommendations
    const recommendations = [];
    if (toxicPercent > 30) {
      recommendations.push('• Enable auto-hide for toxic comments');
      recommendations.push('• Add custom keywords for platform-specific slang');
      recommendations.push('• Consider lowering toxicity threshold');
    } else if (toxicPercent > 10) {
      recommendations.push('• Monitor high-risk users more closely');
      recommendations.push('• Review and update custom keyword list');
    } else {
      recommendations.push('• Current settings are working well');
      recommendations.push('• Continue monitoring trends');
    }
    
    // High-risk users
    const userStats = calculateUserReputation(comments);
    const highRisk = Array.from(userStats.values())
      .filter(u => u.reputation < 30 && u.totalComments > 2)
      .sort((a, b) => a.reputation - b.reputation)
      .slice(0, 5);
    
    return {
      summary,
      patterns,
      recommendations,
      highRisk
    };
  }

  function renderAIInsights(panel, insights) {
    // Summary
    const summaryEl = panel.querySelector('#cg-ai-summary');
    if (summaryEl) {
      summaryEl.innerHTML = insights.summary;
    }
    
    // Patterns
    const patternsEl = panel.querySelector('#cg-toxic-patterns');
    if (patternsEl) {
      if (insights.patterns.length === 0) {
        patternsEl.innerHTML = '<div class="cg-empty-small">No significant patterns detected</div>';
      } else {
        patternsEl.innerHTML = insights.patterns.map(p => `<div class="cg-insight-item">${p}</div>`).join('');
      }
    }
    
    // Recommendations
    const recsEl = panel.querySelector('#cg-recommendations');
    if (recsEl) {
      recsEl.innerHTML = insights.recommendations.map(r => `<div class="cg-insight-item">${r}</div>`).join('');
    }
    
    // High-risk users
    const riskEl = panel.querySelector('#cg-high-risk-users');
    if (riskEl) {
      if (insights.highRisk.length === 0) {
        riskEl.innerHTML = '<div class="cg-empty-small">No high-risk users detected</div>';
      } else {
        riskEl.innerHTML = insights.highRisk.map(u => `
          <div class="cg-risk-user">
            <span class="cg-risk-avatar">${escapeHTML(u.author).charAt(0).toUpperCase()}</span>
            <span class="cg-risk-name">${escapeHTML(u.author)}</span>
            <span class="cg-risk-score" style="color: var(--cg-red);">${u.reputation} REP</span>
          </div>
        `).join('');
      }
    }
  }

  // ── History Tracking ────────────────────────────────────────────────────────
  function saveToHistory(stats) {
    if (!state.settings.trackHistory) return;
    
    try {
      const history = loadHistory();
      history.push({
        timestamp: Date.now(),
        url: location.href,
        platform: state.platform.name,
        total: stats.total,
        toxic: stats.toxicCount,
        toxicPercent: stats.toxicPercent
      });
      
      // Keep only last 100 entries
      const trimmed = history.slice(-100);
      localStorage.setItem('contentguard_history', JSON.stringify(trimmed));
    } catch (e) {
      console.error('[ContentGuard] Failed to save history:', e);
    }
  }

  function loadHistory() {
    try {
      const saved = localStorage.getItem('contentguard_history');
      return saved ? JSON.parse(saved) : [];
    } catch (e) {
      return [];
    }
  }

  function updateStatsLive(panel, total, toxic, sentimentCounts) {
    const safe = total - toxic;
    const toxicPercent = total > 0 ? Math.round((toxic / total) * 100) : 0;
    const safePercent = total > 0 ? Math.round((safe / total) * 100) : 0;
    
    const grid = panel.querySelector('#cg-stat-grid');
    grid.innerHTML = `
      <div class="cg-stat-card cg-stat-total">
        <div class="cg-stat-value">${total}</div>
        <div class="cg-stat-label">Total Comments</div>
      </div>
      <div class="cg-stat-card cg-stat-toxic">
        <div class="cg-stat-value">${toxic}</div>
        <div class="cg-stat-label">Toxic (${toxicPercent}%)</div>
      </div>
      <div class="cg-stat-card cg-stat-safe">
        <div class="cg-stat-value">${safe}</div>
        <div class="cg-stat-label">Safe (${safePercent}%)</div>
      </div>
    `;

    // Update sentiment chart
    const sentimentBars = panel.querySelector('#cg-sentiment-bars');
    if (sentimentBars && sentimentCounts) {
      const positivePercent = total > 0 ? Math.round((sentimentCounts.positive / total) * 100) : 0;
      const negativePercent = total > 0 ? Math.round((sentimentCounts.negative / total) * 100) : 0;
      const neutralPercent = total > 0 ? Math.round((sentimentCounts.neutral / total) * 100) : 0;
      
      sentimentBars.innerHTML = `
        <div class="cg-sentiment-row">
          <div class="cg-sentiment-label">😊 Positive</div>
          <div class="cg-sentiment-bar-wrap">
            <div class="cg-sentiment-bar" style="width: ${positivePercent}%; background: var(--cg-green);"></div>
          </div>
          <div class="cg-sentiment-value">${sentimentCounts.positive} (${positivePercent}%)</div>
        </div>
        <div class="cg-sentiment-row">
          <div class="cg-sentiment-label">😐 Neutral</div>
          <div class="cg-sentiment-bar-wrap">
            <div class="cg-sentiment-bar" style="width: ${neutralPercent}%; background: var(--cg-text-muted);"></div>
          </div>
          <div class="cg-sentiment-value">${sentimentCounts.neutral} (${neutralPercent}%)</div>
        </div>
        <div class="cg-sentiment-row">
          <div class="cg-sentiment-label">😠 Negative</div>
          <div class="cg-sentiment-bar-wrap">
            <div class="cg-sentiment-bar" style="width: ${negativePercent}%; background: var(--cg-red);"></div>
          </div>
          <div class="cg-sentiment-value">${sentimentCounts.negative} (${negativePercent}%)</div>
        </div>
      `;
    }
  }

  function updateCommentsLive(panel, comments) {
    const list = panel.querySelector('#cg-comment-list');
    list.innerHTML = comments.map(c => buildCommentHTML(c)).join('');
  }

  function updateBlockListLive(panel, authorStats) {
    const blockList = panel.querySelector('#cg-block-list');
    
    const toxicAuthors = Array.from(authorStats.values())
      .filter(a => a.toxicCount > 0)
      .map(a => ({ ...a, toxicRate: Math.round((a.toxicCount / a.totalComments) * 100) }))
      .sort((a, b) => b.toxicRate - a.toxicRate || b.toxicCount - a.toxicCount)
      .slice(0, 10);
    
    if (toxicAuthors.length === 0) {
      blockList.innerHTML = '<div class="cg-empty">No toxic users detected 🎉</div>';
      return;
    }
    
    blockList.innerHTML = toxicAuthors.map(a => `
      <div class="cg-block-card">
        <div class="cg-block-card__avatar">${a.author.charAt(0).toUpperCase()}</div>
        <div class="cg-block-card__info">
          <div class="cg-block-card__name">${escapeHTML(a.author)}</div>
          <div class="cg-block-card__stats">
            ${a.toxicCount} toxic of ${a.totalComments} comments · <strong>${a.toxicRate}%</strong> toxic rate
          </div>
          <div class="cg-block-card__action">
            <span class="cg-action-badge cg-action-${a.worstAction.toLowerCase()}">${a.worstAction}</span>
          </div>
        </div>
      </div>
    `).join('');
  }

  // ── Render: Stats (removed - using live updates) ───────────────────────────

  // ── Render: Comments (removed - using live updates) ────────────────────────

  function buildCommentHTML(c) {
    const severityClass = getSeverityClass(c.severity);
    const action = c.action || 'ALLOW';
    const actionEmoji = { ALLOW: '🟢', WARNING: '🟡', HIDE: '🟠', BLOCK: '🔴' }[action] || '⚪';
    const truncated = c.text.length > 200 ? c.text.slice(0, 200) + '…' : c.text;
    const safeText = escapeHTML(truncated);
    const safeAuthor = escapeHTML(c.author || 'Anonymous');
    const confidence = Math.round((c.confidence || 0) * 100);
    const sentimentEmoji = { positive: '😊', negative: '😠', neutral: '😐' }[c.sentiment] || '😐';

    // ML Badge
    const mlBadge = c.usedML 
      ? `<span class="cg-ml-badge" title="Analyzed by BERT ML Model (92.8% accuracy)">🤖 BERT</span>`
      : `<span class="cg-rules-badge" title="Analyzed by rule-based detection">📋 Rules</span>`;

    // Sarcasm Badge
    const sarcasmBadge = c.isSarcasm 
      ? `<span class="cg-sarcasm-badge" title="${escapeHTML(c.contextNote || 'Sarcasm detected')}">😏 Sarcasm</span>`
      : '';

    // Generate reply suggestion if toxic
    let replySuggestion = '';
    if (c.is_toxic && state.settings.showReplySuggestions) {
      const suggestion = generateReplySuggestion(c.text);
      replySuggestion = `
        <div class="cg-reply-suggestion">
          <div class="cg-reply-header">
            <span class="cg-reply-icon">💡</span>
            <span class="cg-reply-label">AI Suggested Reply:</span>
          </div>
          <div class="cg-reply-text">${escapeHTML(suggestion)}</div>
          <button class="cg-copy-reply" data-text="${escapeHTML(suggestion)}">📋 Copy</button>
        </div>
      `;
    }

    // Explanation of why it's toxic
    let explanation = '';
    if (c.is_toxic) {
      explanation = `
        <div class="cg-explanation">
          <strong>Why flagged:</strong> ${generateExplanation(c)}
        </div>
      `;
    }

    return `
      <div class="cg-comment ${severityClass}" data-id="${escapeHTML(c.id)}" data-toxic="${c.is_toxic}">
        <div class="cg-comment__header">
          <div class="cg-comment__author">
            <div class="cg-avatar">${safeAuthor.charAt(0).toUpperCase()}</div>
            <span class="cg-comment__name">${safeAuthor}</span>
            <span class="cg-sentiment-badge">${sentimentEmoji}</span>
          </div>
          <div class="cg-comment__badge">
            <span class="cg-action-badge cg-action-${action.toLowerCase()}">${actionEmoji}</span>
            <span class="cg-confidence-badge" title="ML Confidence">${confidence}%</span>
          </div>
        </div>
        <div class="cg-comment__text">${safeText}</div>
        <div class="cg-comment__badges">
          ${mlBadge}
          ${sarcasmBadge}
        </div>
        ${explanation}
        ${replySuggestion}
      </div>
    `;
  }

  function filterComments(filter) {
    const panel = document.getElementById(PANEL_ID);
    if (!panel) return;
    panel.querySelectorAll('.cg-comment').forEach(el => {
      const isToxic = el.dataset.toxic === 'true';
      if (filter === 'all') el.style.display = '';
      else if (filter === 'toxic') el.style.display = isToxic ? '' : 'none';
      else if (filter === 'safe') el.style.display = !isToxic ? '' : 'none';
    });
  }

  // ── Render: Block Recommendations (removed - using live updates) ───────────

  // ── Draggable Panel ──────────────────────────────────────────────────────────
  function makeDraggable(panel) {
    const handle = panel.querySelector('#cg-drag-handle');
    let startX, startY, startLeft, startTop, dragging = false;

    handle.addEventListener('mousedown', (e) => {
      dragging = true;
      startX = e.clientX;
      startY = e.clientY;
      const rect = panel.getBoundingClientRect();
      startLeft = rect.left;
      startTop = rect.top;
      panel.style.transition = 'none';
      e.preventDefault();
    });

    document.addEventListener('mousemove', (e) => {
      if (!dragging) return;
      const dx = e.clientX - startX;
      const dy = e.clientY - startY;
      panel.style.right = 'auto';
      panel.style.bottom = 'auto';
      panel.style.left = Math.max(0, startLeft + dx) + 'px';
      panel.style.top = Math.max(0, startTop + dy) + 'px';
    });

    document.addEventListener('mouseup', () => {
      dragging = false;
      panel.style.transition = '';
    });
  }

  // ── Platform Comment Scrapers ────────────────────────────────────────────────

  function scrapeTwitter() {
    const results = [];
    console.log('[ContentGuard] Scraping Twitter/X comments...');
    
    // Strategy 1: Look for tweets and replies with multiple selectors
    const tweetSelectors = [
      '[data-testid="tweet"]',
      '[data-testid="tweetText"]',
      'article[role="article"]',
      '[data-testid="cellInnerDiv"]'
    ];
    
    const processedTexts = new Set(); // Avoid duplicates
    
    // Try each selector strategy
    for (const selector of tweetSelectors) {
      const elements = document.querySelectorAll(selector);
      console.log(`[ContentGuard] Found ${elements.length} elements with selector: ${selector}`);
      
      elements.forEach((element, i) => {
        // Look for text content in multiple ways
        let textEl = element.querySelector('[data-testid="tweetText"]');
        if (!textEl) {
          textEl = element.querySelector('[lang]'); // Twitter uses lang attribute on text
        }
        if (!textEl && element.hasAttribute('lang')) {
          textEl = element; // The element itself might be the text container
        }
        if (!textEl) {
          // Look for any div with substantial text content
          const divs = element.querySelectorAll('div[dir="auto"]');
          for (const div of divs) {
            const text = div.innerText?.trim();
            if (text && text.length > 10 && text.length < 5000) {
              textEl = div;
              break;
            }
          }
        }
        
        if (!textEl) return;
        
        const text = textEl.innerText?.trim();
        if (!text || text.length < 2 || text.length > 5000) return;
        
        // Skip if we've already processed this text
        if (processedTexts.has(text)) return;
        processedTexts.add(text);
        
        // Find author - try multiple strategies
        let author = 'Unknown';
        let authorEl = element.querySelector('[data-testid="User-Name"]');
        
        if (authorEl) {
          // Get the first span which usually contains the display name
          const spans = authorEl.querySelectorAll('span');
          for (const span of spans) {
            const name = span.innerText?.trim();
            if (name && name.length > 0 && name.length < 50 && !name.startsWith('@')) {
              author = name;
              break;
            }
          }
        }
        
        // Alternative: look for username with @
        if (author === 'Unknown') {
          const usernameEl = element.querySelector('a[href*="/"]');
          if (usernameEl) {
            const href = usernameEl.getAttribute('href');
            const match = href?.match(/\/([^\/]+)$/);
            if (match && match[1] && !match[1].includes('status')) {
              author = '@' + match[1];
            }
          }
        }
        
        // Alternative: look for any link that looks like a username
        if (author === 'Unknown') {
          const links = element.querySelectorAll('a');
          for (const link of links) {
            const linkText = link.innerText?.trim();
            if (linkText && linkText.startsWith('@') && linkText.length < 30) {
              author = linkText;
              break;
            }
          }
        }
        
        results.push({
          id: `tw-${results.length}`,
          text: text,
          author: author,
          avatar: null
        });
      });
      
      // If we found comments with this selector, we're done
      if (results.length > 0) break;
    }
    
    // Fallback: Look for any text that looks like a tweet/comment
    if (results.length === 0) {
      console.log('[ContentGuard] Using fallback strategy for Twitter...');
      const allDivs = document.querySelectorAll('div[lang], div[dir="auto"]');
      
      allDivs.forEach((div, i) => {
        const text = div.innerText?.trim();
        if (!text || text.length < 10 || text.length > 5000) return;
        if (processedTexts.has(text)) return;
        
        // Skip UI elements
        const uiKeywords = ['Retweet', 'Like', 'Reply', 'Share', 'Follow', 'Home', 'Explore', 'Notifications'];
        if (uiKeywords.some(keyword => text === keyword || text.startsWith(keyword))) return;
        
        processedTexts.add(text);
        
        // Try to find author nearby
        let author = 'Unknown';
        let parent = div.parentElement;
        for (let depth = 0; depth < 10 && parent; depth++) {
          const authorLink = parent.querySelector('a[href*="/"]');
          if (authorLink) {
            const href = authorLink.getAttribute('href');
            const match = href?.match(/\/([^\/]+)$/);
            if (match && match[1] && !match[1].includes('status') && !match[1].includes('photo')) {
              author = '@' + match[1];
              break;
            }
          }
          parent = parent.parentElement;
        }
        
        results.push({
          id: `tw-fb-${i}`,
          text: text,
          author: author,
          avatar: null
        });
      });
    }
    
    console.log(`[ContentGuard] Scraped ${results.length} Twitter/X comments`);
    if (results.length > 0) {
      console.log('[ContentGuard] Sample:', results.slice(0, 2).map(c => `${c.author}: ${c.text.substring(0, 40)}...`));
    }
    
    return results.slice(0, 200); // Limit to 200 comments
  }

  function scrapeFacebook() {
    const results = [];
    console.log('[ContentGuard] Scraping Facebook comments...');
    
    const processedTexts = new Set();
    
    // Facebook uses role="article" for posts and comments
    const articles = document.querySelectorAll('[role="article"]');
    console.log(`[ContentGuard] Found ${articles.length} Facebook articles`);
    
    articles.forEach((article, i) => {
      // Look for text content
      const textDivs = article.querySelectorAll('div[dir="auto"]');
      
      for (const div of textDivs) {
        const text = div.innerText?.trim();
        if (!text || text.length < 5 || text.length > 5000) continue;
        if (processedTexts.has(text)) continue;
        
        // Skip UI elements
        const uiKeywords = ['Like', 'Comment', 'Share', 'Send', 'See more', 'See less', 'Write a comment'];
        if (uiKeywords.some(keyword => text === keyword || text.startsWith(keyword))) continue;
        
        processedTexts.add(text);
        
        // Find author
        let author = 'Unknown';
        const authorLink = article.querySelector('a[role="link"]');
        if (authorLink) {
          author = authorLink.innerText?.trim() || authorLink.getAttribute('aria-label') || 'Unknown';
        }
        
        results.push({
          id: `fb-${results.length}`,
          text: text,
          author: author,
          avatar: null
        });
      }
    });
    
    console.log(`[ContentGuard] Scraped ${results.length} Facebook comments`);
    return results.slice(0, 200);
  }

  function scrapeLinkedIn() {
    const results = [];
    console.log('[ContentGuard] Scraping LinkedIn comments...');
    
    const processedTexts = new Set();
    
    // LinkedIn comment selectors
    const commentSelectors = [
      '.comments-comment-item',
      '.comment-item',
      '[data-id*="comment"]',
      '.feed-shared-update-v2__commentary'
    ];
    
    for (const selector of commentSelectors) {
      const comments = document.querySelectorAll(selector);
      console.log(`[ContentGuard] Found ${comments.length} elements with selector: ${selector}`);
      
      comments.forEach((comment, i) => {
        const text = comment.innerText?.trim();
        if (!text || text.length < 5 || text.length > 5000) return;
        if (processedTexts.has(text)) return;
        
        processedTexts.add(text);
        
        // Find author
        let author = 'Unknown';
        const authorLink = comment.querySelector('a[href*="/in/"]');
        if (authorLink) {
          author = authorLink.innerText?.trim() || 'Unknown';
        }
        
        results.push({
          id: `li-${results.length}`,
          text: text,
          author: author,
          avatar: null
        });
      });
      
      if (results.length > 0) break;
    }
    
    console.log(`[ContentGuard] Scraped ${results.length} LinkedIn comments`);
    return results.slice(0, 200);
  }

  function scrapeTikTok() {
    const results = [];
    console.log('[ContentGuard] Scraping TikTok comments...');
    
    const processedTexts = new Set();
    
    // TikTok comment selectors
    const commentSelectors = [
      '[data-e2e="comment-item"]',
      '.comment-item',
      '[class*="CommentItem"]',
      '[class*="comment-text"]'
    ];
    
    for (const selector of commentSelectors) {
      const comments = document.querySelectorAll(selector);
      console.log(`[ContentGuard] Found ${comments.length} elements with selector: ${selector}`);
      
      comments.forEach((comment, i) => {
        const text = comment.innerText?.trim();
        if (!text || text.length < 2 || text.length > 5000) return;
        if (processedTexts.has(text)) return;
        
        processedTexts.add(text);
        
        // Find author
        let author = 'Unknown';
        const authorEl = comment.querySelector('[data-e2e="comment-username"], [class*="username"]');
        if (authorEl) {
          author = authorEl.innerText?.trim() || 'Unknown';
        }
        
        results.push({
          id: `tt-${results.length}`,
          text: text,
          author: author,
          avatar: null
        });
      });
      
      if (results.length > 0) break;
    }
    
    console.log(`[ContentGuard] Scraped ${results.length} TikTok comments`);
    return results.slice(0, 200);
  }

  function scrapeReddit() {
    const results = [];
    
    console.log('[ContentGuard] Scraping Reddit comments...');
    
    // Strategy 1: Look for any paragraph elements that look like comments
    const allParagraphs = document.querySelectorAll('p');
    console.log('[ContentGuard] Found', allParagraphs.length, 'paragraph elements');
    
    allParagraphs.forEach((p, i) => {
      const text = p.textContent?.trim();
      
      // Filter: must be substantial text, not UI elements
      if (!text || text.length < 15 || text.length > 5000) return;
      
      // Skip if it looks like UI text
      const uiKeywords = ['Reply', 'Share', 'Award', 'Save', 'Hide', 'Report', 'Sort by', 'Best', 'Top', 'New', 'Controversial', 'Old', 'Q&A', 'Give Award', 'Upvote', 'Downvote'];
      if (uiKeywords.some(keyword => text === keyword || text.startsWith(keyword + ' '))) return;
      
      // Skip if it's just numbers or very short
      if (/^\d+$/.test(text) || text.split(' ').length < 3) return;
      
      // Skip if it contains "ago" (likely timestamp)
      if (text.includes(' ago') && text.split(' ').length < 5) return;
      
      // Try to find author - look in multiple places
      let author = 'Unknown';
      let currentEl = p;
      
      // Strategy 1: Look for author link in parent elements
      for (let depth = 0; depth < 15; depth++) {
        if (!currentEl) break;
        
        // Look for username links
        const authorLink = currentEl.querySelector('a[href*="/user/"], a[href*="/u/"]');
        if (authorLink) {
          const username = authorLink.textContent?.trim();
          if (username && username.length > 0 && username.length < 30 && !username.includes(' ')) {
            author = username;
            break;
          }
        }
        
        // Look for author in attributes
        const authorAttr = currentEl.getAttribute('author') || currentEl.getAttribute('data-author');
        if (authorAttr) {
          author = authorAttr;
          break;
        }
        
        currentEl = currentEl.parentElement;
      }
      
      // Strategy 2: Look for author in siblings
      if (author === 'Unknown') {
        const parent = p.parentElement;
        if (parent) {
          const siblings = Array.from(parent.children);
          for (const sibling of siblings) {
            const authorLink = sibling.querySelector('a[href*="/user/"], a[href*="/u/"]');
            if (authorLink) {
              const username = authorLink.textContent?.trim();
              if (username && username.length > 0 && username.length < 30 && !username.includes(' ')) {
                author = username;
                break;
              }
            }
          }
        }
      }
      
      // Strategy 3: Look for any nearby username link (within 200 chars of DOM distance)
      if (author === 'Unknown') {
        const nearbyLinks = document.querySelectorAll('a[href*="/user/"], a[href*="/u/"]');
        for (const link of nearbyLinks) {
          // Check if this link is near our paragraph
          const linkRect = link.getBoundingClientRect();
          const pRect = p.getBoundingClientRect();
          const distance = Math.abs(linkRect.top - pRect.top);
          
          if (distance < 100) { // Within 100px vertically
            const username = link.textContent?.trim();
            if (username && username.length > 0 && username.length < 30 && !username.includes(' ')) {
              author = username;
              break;
            }
          }
        }
      }
      
      results.push({
        id: `rd-p-${i}`,
        text: text,
        author: author,
        avatar: null
      });
    });
    
    // Remove duplicates
    const seen = new Set();
    const filtered = results.filter(r => {
      if (seen.has(r.text)) return false;
      seen.add(r.text);
      return true;
    });
    
    console.log('[ContentGuard] Scraped', filtered.length, 'unique comments');
    console.log('[ContentGuard] Sample:', filtered.slice(0, 3).map(c => `${c.author}: ${c.text.substring(0, 30)}...`));
    
    return filtered;
  }

  function scrapeInstagram() {
    const results = [];
    console.log('[ContentGuard] Scraping Instagram comments...');
    
    const processedTexts = new Set();
    
    // Instagram comments (class names change frequently, use multiple strategies)
    const selectors = [
      '._a9zs',
      '._a9ym',
      'span[class*="comment"]',
      'li span',
      '[role="button"] + span',
      'ul li span'
    ];
    
    for (const sel of selectors) {
      const elements = document.querySelectorAll(sel);
      console.log(`[ContentGuard] Found ${elements.length} elements with selector: ${sel}`);
      
      elements.forEach((el, i) => {
        const text = el.innerText?.trim();
        if (!text || text.length < 2 || text.length > 2000) return;
        if (processedTexts.has(text)) return;
        
        // Skip UI elements
        const uiKeywords = ['Reply', 'Like', 'View replies', 'Load more', 'See translation'];
        if (uiKeywords.some(keyword => text === keyword || text.startsWith(keyword))) return;
        
        processedTexts.add(text);
        
        // Find author
        let author = 'Unknown';
        const authorEl = el.closest('li')?.querySelector('a') || el.closest('div')?.querySelector('a');
        if (authorEl) {
          author = authorEl.innerText?.trim() || authorEl.getAttribute('href')?.split('/')[1] || 'Unknown';
        }
        
        results.push({
          id: `ig-${results.length}`,
          text: text,
          author: author,
          avatar: null
        });
      });
      
      if (results.length > 0) break;
    }
    
    console.log(`[ContentGuard] Scraped ${results.length} Instagram comments`);
    return results.slice(0, 200);
  }

  function scrapeYouTube() {
    const results = [];
    console.log('[ContentGuard] Scraping YouTube comments...');
    
    const processedTexts = new Set();
    
    // YouTube comment selectors (multiple strategies)
    const commentSelectors = [
      'ytd-comment-renderer',
      'ytd-comment-thread-renderer',
      '#content-text'
    ];
    
    for (const selector of commentSelectors) {
      const elements = document.querySelectorAll(selector);
      console.log(`[ContentGuard] Found ${elements.length} elements with selector: ${selector}`);
      
      elements.forEach((el, i) => {
        let textEl = el.querySelector('#content-text');
        if (!textEl && selector === '#content-text') {
          textEl = el;
        }
        
        if (!textEl) return;
        
        const text = textEl.innerText?.trim();
        if (!text || text.length < 2 || text.length > 5000) return;
        if (processedTexts.has(text)) return;
        
        processedTexts.add(text);
        
        // Find author
        let author = 'Unknown';
        const authorEl = el.querySelector('#author-text, ytd-channel-name a');
        if (authorEl) {
          author = authorEl.innerText?.trim() || 'Unknown';
        }
        
        results.push({
          id: `yt-${results.length}`,
          text: text,
          author: author,
          avatar: null
        });
      });
      
      if (results.length > 0) break;
    }
    
    console.log(`[ContentGuard] Scraped ${results.length} YouTube comments`);
    return results.slice(0, 200);
  }

  function scrapeHackerNews() {
    const results = [];
    document.querySelectorAll('.comment').forEach((el, i) => {
      const textEl = el.querySelector('.commtext');
      const authorEl = el.closest('.comtr')?.querySelector('.hnuser');
      if (textEl) {
        results.push({
          id: `hn-${i}`,
          text: textEl.innerText.trim(),
          author: authorEl?.innerText?.trim() || 'Unknown',
          avatar: null
        });
      }
    });
    return results;
  }

  function scrapeGeneric() {
    const results = [];
    console.log('[ContentGuard] Using generic scraper...');
    
    const processedTexts = new Set();
    
    // Generic selectors that work on most sites
    const selectors = [
      '[class*="comment"]:not([class*="commentcount"]):not([class*="commentbox"]):not([class*="comment-form"])',
      '[id*="comment"]',
      '[role="article"] p',
      'article p',
      '[data-comment]',
      '.post-content p',
      '.entry-content p'
    ];
    
    for (const sel of selectors) {
      const elements = document.querySelectorAll(sel);
      console.log(`[ContentGuard] Found ${elements.length} elements with selector: ${sel}`);
      
      elements.forEach((el, i) => {
        const text = el.innerText?.trim();
        if (!text || text.length < 10 || text.length > 2000) return;
        if (processedTexts.has(text)) return;
        
        // Skip navigation and UI text
        const uiKeywords = ['Home', 'About', 'Contact', 'Login', 'Sign up', 'Menu', 'Search', 'Subscribe'];
        if (uiKeywords.some(keyword => text === keyword)) return;
        
        processedTexts.add(text);
        
        // Try to find author
        let author = 'Unknown';
        let parent = el.parentElement;
        for (let depth = 0; depth < 5 && parent; depth++) {
          const authorEl = parent.querySelector('[class*="author"], [class*="user"], [class*="name"]');
          if (authorEl && authorEl !== el) {
            const authorText = authorEl.innerText?.trim();
            if (authorText && authorText.length < 50) {
              author = authorText;
              break;
            }
          }
          parent = parent.parentElement;
        }
        
        results.push({
          id: `gen-${results.length}`,
          text: text,
          author: author,
          avatar: null
        });
      });
      
      if (results.length > 20) break; // Found enough with this selector
    }
    
    console.log(`[ContentGuard] Scraped ${results.length} generic comments`);
    return results.slice(0, 100);
  }

  // ── Helpers ─────────────────────────────────────────────────────────────────
  function getSeverityClass(severity) {
    const map = { NONE: 'cg-safe', LOW: 'cg-low', MEDIUM: 'cg-medium', HIGH: 'cg-high', CRITICAL: 'cg-critical' };
    return map[severity] || 'cg-safe';
  }

  function escapeHTML(str) {
    return String(str).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
  }

  function escapeAttr(str) {
    return String(str).replace(/"/g, '&quot;').replace(/'/g, '&#39;').slice(0, 300);
  }

  function sendMessage(msg) {
    return new Promise((resolve) => {
      try {
        chrome.runtime.sendMessage(msg, (response) => {
          if (chrome.runtime.lastError) {
            console.warn('[ContentGuard]', chrome.runtime.lastError.message);
            resolve(null);
          } else {
            resolve(response);
          }
        });
      } catch (e) {
        resolve(null);
      }
    });
  }

  // ── Start ───────────────────────────────────────────────────────────────────
  init();

})();
