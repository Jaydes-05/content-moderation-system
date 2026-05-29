# Privacy Policy for ContentGuard

**Last Updated**: May 26, 2026

## Overview
ContentGuard is a browser extension that provides AI-powered content moderation for social media platforms. We are committed to protecting your privacy.

## Data Collection
ContentGuard does **NOT** collect, store, or transmit any personal information to external servers.

### What We Access:
- **Page Content**: The extension reads comments from web pages you visit to perform toxicity analysis
- **Local Storage**: Settings and preferences are stored locally in your browser

### What We Do NOT Collect:
- ❌ Personal information
- ❌ Browsing history
- ❌ Login credentials
- ❌ Social media account data
- ❌ Analytics or tracking data

## How It Works
1. You visit a social media page (Twitter, Reddit, YouTube, etc.)
2. The extension extracts visible comments from the page
3. Comments are sent to **your local API** (running on localhost:8000)
4. The API analyzes toxicity using machine learning
5. Results are displayed in the extension panel
6. **Nothing is sent to external servers**

## Third-Party Services

### Translation Feature
When you use the translation feature, text is sent to MyMemory Translation API (https://mymemory.translated.net) to provide translations. This is the only external service used, and it's only activated when you explicitly click "Translate."

### Local API Requirement
This extension requires you to run a local FastAPI backend on your computer. All content analysis happens on your machine.

## Permissions Explained

### Required Permissions:
- **activeTab**: To read comments from the current page
- **storage**: To save your settings locally
- **scripting**: To inject the moderation panel
- **tabs**: To manage extension state per tab

### Host Permissions:
- **localhost:8000**: To communicate with your local API
- **api.mymemory.translated.net**: For translation feature (optional)

## Data Security
- All data processing happens locally on your machine
- No cloud storage or external databases
- No user accounts or authentication required
- Open source code available for review

## Changes to Privacy Policy
We may update this policy occasionally. Changes will be posted with a new "Last Updated" date.

## Contact
For questions about privacy, please open an issue on our GitHub repository.

## Your Rights
Since we don't collect any data, there's nothing to delete, export, or modify. You maintain complete control over your information.

---

**Summary**: ContentGuard is privacy-first. Everything stays on your computer.
