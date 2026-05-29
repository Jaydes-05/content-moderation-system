# Publishing ContentGuard to Microsoft Edge Add-ons

## Prerequisites
- Microsoft account (free)
- Your extension files (already ready!)
- Backend API running locally or hosted

## Step 1: Register as Edge Add-ons Developer (FREE)

1. Go to: https://partner.microsoft.com/dashboard/microsoftedge/public/login
2. Sign in with your Microsoft account
3. Accept the developer agreement
4. **No registration fee required!** ✅

## Step 2: Prepare Your Extension Package

Your extension is already compatible with Edge (Chromium-based). We just need to create a ZIP file.

### Files to include:
```
extension.zip
├── manifest.json
├── background.js
├── content.js
├── panel.css
├── popup.html
├── popup.js
└── icons/
    ├── icon16.png
    ├── icon48.png
    └── icon128.png
```

### Create the ZIP:
1. Go to the `extension/` folder
2. Select all files (NOT the folder itself)
3. Right-click → Send to → Compressed (zipped) folder
4. Name it: `contentguard-extension.zip`

## Step 3: Create Store Listing

You'll need to prepare:

### Required Information:
- **Extension Name**: ContentGuard — AI Moderation
- **Short Description**: AI-powered content moderation for social media
- **Detailed Description**: (see below)
- **Category**: Productivity or Social & Communication
- **Language**: English
- **Screenshots**: 1-5 screenshots (1280x800 or 640x400)
- **Privacy Policy URL**: (optional but recommended)

### Detailed Description Template:
```
ContentGuard brings AI-powered content moderation to your browser.

🎯 KEY FEATURES:
• Real-time toxicity analysis for comments
• Visual toxicity breakdown with charts
• Block recommendations for toxic accounts
• Per-comment color coding (Safe/Warning/Toxic)
• Multi-language translation (12+ languages)
• Works on Twitter/X, Reddit, YouTube, Instagram & more

🔒 PRIVACY:
• All analysis happens via your local API
• No data stored on external servers
• Open source and transparent

⚙️ SETUP REQUIRED:
This extension requires running the local API backend. 
Visit our GitHub for setup instructions: [your-github-link]

📊 SUPPORTED PLATFORMS:
✅ Twitter/X
✅ Reddit  
✅ YouTube
✅ Instagram
✅ Hacker News
✅ Any website with comments
```

## Step 4: Submit for Review

1. Log into Partner Center
2. Click "New submission"
3. Upload your ZIP file
4. Fill in all store listing details
5. Add screenshots
6. Submit for review

**Review time**: Usually 1-3 business days

## Step 5: After Approval

Once approved:
- Your extension will be live on Edge Add-ons store
- Users can install with one click
- You can push updates anytime (also free)
- No ongoing fees!

## Important Notes

### Backend Requirement
Your extension needs the FastAPI backend running. You have two options:

**Option A: Local Only (Current)**
- Users must run `python -m uvicorn api.main:app --reload`
- Good for: Personal use, developers, small teams
- In store description: Clearly state "Requires local setup"

**Option B: Hosted Backend (Recommended for Public)**
- Deploy API to: Heroku, Railway, Render, or AWS
- Update `manifest.json` host_permissions to your hosted URL
- Users can install and use immediately
- Better user experience

### Screenshots Needed

Create 3-5 screenshots showing:
1. Extension panel on Twitter/X with toxicity stats
2. Comment analysis with color coding
3. Translation feature in action
4. Block recommendations tab
5. Settings/popup view

Use Windows Snipping Tool or Snip & Sketch to capture.

## Troubleshooting

**Issue**: "Package validation failed"
- Make sure you zipped the FILES, not the folder
- Check manifest.json has no syntax errors

**Issue**: "Missing required fields"
- All fields in Partner Center must be filled
- Add at least 1 screenshot

**Issue**: "Privacy policy required"
- For extensions with host_permissions, Edge may require privacy policy
- Create simple privacy.md explaining data usage

## Next Steps

1. Create the ZIP package
2. Take screenshots
3. Register on Partner Center
4. Submit!

Need help? Check: https://learn.microsoft.com/en-us/microsoft-edge/extensions-chromium/publish/publish-extension
