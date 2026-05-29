# ContentGuard Extension - Testing Guide

## 🧪 How to Test Comment Detection

### Prerequisites
1. Backend API running: `python -m uvicorn api.main:app --reload`
2. Extension loaded in browser (Chrome/Edge)

### Supported Platforms

The extension now detects comments on:

#### ✅ Fully Supported
- **Twitter / X** (twitter.com, x.com)
- **Facebook** (facebook.com)
- **LinkedIn** (linkedin.com)
- **TikTok** (tiktok.com)
- **Reddit** (reddit.com)
- **Instagram** (instagram.com)
- **YouTube** (youtube.com)
- **Hacker News** (news.ycombinator.com)
- **Any Website** (generic fallback)

### Testing Steps

#### 1. Load the Extension
```bash
1. Open Chrome/Edge
2. Go to chrome://extensions/ (or edge://extensions/)
3. Enable "Developer mode"
4. Click "Load unpacked"
5. Select the extension/ folder
```

#### 2. Start the Backend
```bash
python -m uvicorn api.main:app --reload
```
Backend should be running at http://127.0.0.1:8000

#### 3. Test on Twitter/X

**Option A: Visit a Tweet with Replies**
1. Go to https://twitter.com or https://x.com
2. Click on any tweet with replies
3. Scroll down to see replies
4. Click the ContentGuard floating button (bottom-right)
5. Click "Refresh" to analyze comments

**Option B: Visit Your Timeline**
1. Go to https://twitter.com/home
2. Scroll through your timeline
3. Click the ContentGuard button
4. Click "Refresh" - it will analyze visible tweets

**What to Expect:**
- Extension should detect tweets and replies
- Each comment shows: text, author, toxicity score
- Console logs show: "Scraped X Twitter/X comments"

#### 4. Test on Other Platforms

**Facebook:**
1. Visit any Facebook post with comments
2. Click ContentGuard button → Refresh
3. Should detect post content and comments

**YouTube:**
1. Visit any YouTube video
2. Scroll down to comments section
3. Click ContentGuard button → Refresh
4. Should detect video comments

**Reddit:**
1. Visit any Reddit post with comments
2. Click ContentGuard button → Refresh
3. Should detect all comment text

**LinkedIn:**
1. Visit LinkedIn feed with posts
2. Click ContentGuard button → Refresh
3. Should detect post content and comments

**Instagram:**
1. Visit any Instagram post
2. Click ContentGuard button → Refresh
3. Should detect comments (if visible)

**TikTok:**
1. Visit any TikTok video
2. Click ContentGuard button → Refresh
3. Should detect comments

### Debugging

#### Check Console Logs
1. Right-click on page → Inspect
2. Go to Console tab
3. Look for ContentGuard logs:
   ```
   [ContentGuard] Scraping Twitter/X comments...
   [ContentGuard] Found X elements with selector: ...
   [ContentGuard] Scraped X Twitter/X comments
   [ContentGuard] Sample: @user: comment text...
   ```

#### Common Issues

**No Comments Detected:**
- Make sure comments are loaded on the page (scroll down)
- Check console for errors
- Try clicking "Refresh" again
- Some platforms load comments dynamically - wait a few seconds

**Backend Not Connected:**
- Extension shows "Backend Required" screen
- Make sure API is running: `python -m uvicorn api.main:app --reload`
- Check http://127.0.0.1:8000/health in browser

**Extension Not Working:**
- Reload the extension in chrome://extensions/
- Refresh the webpage
- Check for JavaScript errors in console

### Testing Toxicity Detection

#### Test with Known Toxic Comments
Visit pages with potentially toxic content:
- Controversial news articles
- Heated debate threads
- Gaming community discussions

#### Test with Safe Comments
Visit pages with positive content:
- Wholesome subreddits (r/aww, r/wholesome)
- Educational content
- Professional discussions

### Expected Results

**Stats Tab:**
- Total Comments: Shows count of detected comments
- Toxic: Shows count and percentage of toxic comments
- Safe: Shows count and percentage of safe comments
- Sentiment chart with bars

**Comments Tab:**
- List of all comments with:
  - 🤖 BERT badge (if backend connected)
  - Confidence score (0-100%)
  - Toxicity labels (toxic, insult, threat, etc.)
  - Author name
  - Comment text

**Community Health Tab:**
- Health score (0-100)
- Toxicity rate
- Engagement metrics
- Trend indicator

**Batch Moderation Tab:**
- Checkboxes to select comments
- Bulk operations (Hide, Block, Approve, Export)

### Performance

- **Small pages** (< 50 comments): < 2 seconds
- **Medium pages** (50-200 comments): 2-5 seconds
- **Large pages** (> 200 comments): Limited to 200, ~5 seconds

### Platform-Specific Notes

**Twitter/X:**
- Detects both tweets and replies
- Works on timeline, profile pages, and individual tweets
- May need to scroll to load more comments

**Facebook:**
- Detects posts and comments
- Works best on public posts
- Private posts may have limited access

**YouTube:**
- Must scroll down to comments section first
- Works on all video pages
- Detects both top-level and reply comments

**Reddit:**
- Works on post pages with comments
- Detects all visible comment text
- Very robust detection

**Instagram:**
- Works on post pages
- Must be logged in to see comments
- Class names change frequently (may need updates)

**LinkedIn:**
- Works on feed posts
- Detects post content and comments
- Best on public posts

**TikTok:**
- Works on video pages
- Detects comment section
- Must scroll to comments

### Troubleshooting Commands

```bash
# Check if backend is running
curl http://127.0.0.1:8000/health

# Test backend moderation
curl -X POST http://127.0.0.1:8000/moderate \
  -H "Content-Type: application/json" \
  -d '{"text": "This is a test comment"}'

# Restart backend
# Press Ctrl+C to stop, then:
python -m uvicorn api.main:app --reload

# Reload extension
# Go to chrome://extensions/ and click reload icon
```

### Reporting Issues

If comment detection isn't working:
1. Note which platform (Twitter, Facebook, etc.)
2. Check console logs for errors
3. Take screenshot of the page
4. Note any error messages
5. Check if comments are visible on the page

### Next Steps

After confirming comment detection works:
1. Test toxicity detection accuracy
2. Try batch moderation features
3. Export reports (CSV, JSON, PDF)
4. Test on different types of content
5. Adjust toxicity threshold in Settings tab

## 🎯 Quick Test Checklist

- [ ] Backend API running
- [ ] Extension loaded in browser
- [ ] Tested on Twitter/X
- [ ] Tested on YouTube
- [ ] Tested on Reddit
- [ ] Comments detected correctly
- [ ] Toxicity scores showing
- [ ] BERT badge visible
- [ ] Stats tab showing data
- [ ] Community health calculated
- [ ] Batch mode working
- [ ] Export features working

## 📝 Notes

- Extension works offline with rule-based detection
- Backend connection enables BERT ML model (92.8% accuracy)
- All data is processed locally - no data sent to external servers
- Extension respects platform rate limits
- Some platforms may block scraping - this is expected
