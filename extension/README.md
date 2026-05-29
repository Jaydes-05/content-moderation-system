# ContentGuard Browser Extension

A Chrome browser extension that brings AI-powered content moderation to any social platform — Twitter/X, Reddit, Instagram, YouTube, and more.

## Features

- 📊 **Live Toxicity Statistics** — Instant breakdown of toxic vs safe comments with category charts
- 🚫 **Block Recommendations** — Surfaces accounts with highest toxicity rates
- 💬 **Per-Comment Analysis** — Every comment color-coded by severity (Safe 🟢 / Warning 🟡 / Toxic 🔴)
- 🌐 **Comment Translation** — Translate any comment to 12+ languages with one click (no API key needed)
- 🖱️ **Draggable Panel** — Floating glassmorphism panel, drag anywhere on the page

## Supported Platforms

| Platform | Support |
|---|---|
| Twitter / X | ✅ Full |
| Reddit | ✅ Full |
| YouTube | ✅ Full |
| Instagram | ✅ Best-effort |
| Hacker News | ✅ Full |
| Any website | ✅ Generic fallback |

---

## Setup

### Step 1 — Start the FastAPI Backend

The extension requires the existing ML backend to be running locally.

```bash
# From the project root
uvicorn api.main:app --reload
```

The API will be available at `http://localhost:8000`.

### Step 2 — Load the Extension in Chrome

1. Open Chrome and go to `chrome://extensions`
2. Enable **Developer Mode** (toggle in the top-right)
3. Click **Load unpacked**
4. Select the `extension/` folder in this project

The ContentGuard icon will appear in your browser toolbar.

### Step 3 — Use It

1. Visit Twitter, Reddit, Instagram, YouTube, etc.
2. Scroll down to the comments section
3. Click the purple **ContentGuard** floating button on the page (bottom-right)
4. The analysis panel slides in and begins analyzing comments
5. Switch between **Stats**, **Comments**, and **Block List** tabs
6. Click 🌐 **Translate** on any comment and pick a language

---

## Extension File Structure

```
extension/
├── manifest.json       # Chrome MV3 manifest
├── background.js       # Service worker: API calls & state
├── content.js          # Injected script: scraping, panel, translation UI
├── panel.css           # Glassmorphism panel styles
├── popup.html          # Toolbar icon popup
├── popup.js            # Popup logic
└── icons/
    ├── icon16.png
    ├── icon48.png
    └── icon128.png
```

---

## New Backend Endpoints (added for extension)

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/translate` | Translate text to target language (MyMemory free API) |
| `GET` | `/extension-stats` | Aggregated DB stats for extension dashboard |

### POST /translate

```json
// Request
{ "text": "This is amazing!", "target_language": "es" }

// Response  
{ "original": "This is amazing!", "translated": "¡Esto es asombroso!", "target_language": "es", "ok": true }
```

### Supported Languages

`es` Spanish · `fr` French · `de` German · `hi` Hindi · `zh` Chinese · `ar` Arabic · `pt` Portuguese · `ja` Japanese · `ko` Korean · `ru` Russian · `it` Italian · `nl` Dutch

---

## Architecture

```
Browser Extension
  ├── content.js   ──► scrapes comments from page DOM
  │                    injects floating panel
  │                    handles translate button clicks
  │
  ├── background.js ──► calls FastAPI /batch-moderate
  │                     calls MyMemory translation API
  │                     manages per-tab state
  │
  └── popup.js     ──► shows backend status
                       shows cached stats summary
                       triggers panel open

FastAPI Backend (localhost:8000)
  ├── /batch-moderate  ← ML toxicity scoring (DistilBERT)
  ├── /translate       ← Translation via MyMemory
  └── /extension-stats ← Aggregated analytics
```
