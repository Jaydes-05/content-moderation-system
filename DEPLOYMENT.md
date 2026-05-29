# ContentGuard - Quick Deployment Guide

Choose your deployment method:

## 🚀 Quick Start (Recommended)

### Windows
```bash
# Run deployment script
scripts\deploy.bat

# Choose option 5 (Full Setup)
```

### Linux/Mac
```bash
# Make script executable
chmod +x scripts/deploy.sh

# Run deployment script
./scripts/deploy.sh

# Choose option 5 (Full Setup)
```

## 🐳 Docker (Easiest)

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

**Access:**
- API: http://localhost:8000
- Dashboard: http://localhost:8501
- API Docs: http://localhost:8000/docs

## 🔧 Manual Setup

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Start Backend API
```bash
python -m uvicorn api.main:app --reload
```
API available at: http://localhost:8000

### 3. Start Dashboard (Optional)
```bash
streamlit run dashboard/app.py
```
Dashboard available at: http://localhost:8501

### 4. Load Browser Extension

**Chrome/Edge:**
1. Go to `chrome://extensions/` (or `edge://extensions/`)
2. Enable "Developer mode"
3. Click "Load unpacked"
4. Select the `extension/` folder

**Firefox:**
1. Go to `about:debugging#/runtime/this-firefox`
2. Click "Load Temporary Add-on"
3. Select `extension/manifest.json`

## 📦 Extension Publishing

### Chrome Web Store
1. Package extension:
   ```bash
   cd extension
   zip -r contentguard-extension.zip .
   ```
2. Go to [Chrome Web Store Developer Dashboard](https://chrome.google.com/webstore/devconsole)
3. Upload ZIP file
4. Fill store listing
5. Submit for review

See `docs/DEPLOYMENT_GUIDE.md` for detailed instructions.

## 🌐 Production Deployment

### Option 1: VPS (DigitalOcean, AWS, etc.)
```bash
# SSH into server
ssh user@your-server.com

# Clone repository
git clone https://github.com/yourusername/content-moderation-system.git
cd content-moderation-system

# Run setup
./scripts/deploy.sh
```

### Option 2: Heroku
```bash
# Install Heroku CLI
curl https://cli-assets.heroku.com/install.sh | sh

# Login and create app
heroku login
heroku create contentguard-api

# Add Procfile
echo "web: uvicorn api.main:app --host 0.0.0.0 --port \$PORT" > Procfile

# Deploy
git push heroku main
```

### Option 3: Streamlit Cloud (Dashboard)
1. Push code to GitHub
2. Go to [Streamlit Cloud](https://streamlit.io/cloud)
3. Connect repository
4. Deploy `dashboard/app.py`

## 🔒 Security Checklist

- [ ] Change default API keys
- [ ] Enable HTTPS/SSL
- [ ] Configure CORS properly
- [ ] Set up rate limiting
- [ ] Enable authentication
- [ ] Configure firewall
- [ ] Set up backups
- [ ] Monitor logs

## 📊 Architecture

```
┌─────────────────┐
│  Browser        │
│  Extension      │◄─── Users interact here
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  FastAPI        │
│  Backend        │◄─── http://localhost:8000
│  (Port 8000)    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Streamlit      │
│  Dashboard      │◄─── http://localhost:8501
│  (Port 8501)    │
└─────────────────┘
```

## 🆘 Troubleshooting

### Extension not loading
- Check manifest.json syntax
- Reload extension in browser
- Check console for errors

### API not starting
```bash
# Check if port is in use
netstat -ano | findstr :8000  # Windows
lsof -i :8000                 # Linux/Mac

# Kill process if needed
taskkill /PID <PID> /F        # Windows
kill -9 <PID>                 # Linux/Mac
```

### Database errors
```bash
# Reinitialize database
python -c "from api.database.db import init_db; init_db()"
```

### Import errors
```bash
# Reinstall dependencies
pip install -r requirements.txt --force-reinstall
```

## 📚 Documentation

- **Full Deployment Guide**: `docs/DEPLOYMENT_GUIDE.md`
- **Testing Guide**: `extension/TESTING_GUIDE.md`
- **API Documentation**: http://localhost:8000/docs
- **Architecture**: `docs/ARCHITECTURE.md`

## 💡 Tips

1. **Start with extension only** - Works standalone with rule-based detection
2. **Add backend later** - Enables BERT ML model (92.8% accuracy)
3. **Use demo mode** - API works without ML models for testing
4. **Monitor logs** - Check console for debugging info
5. **Test locally first** - Before deploying to production

## 🎯 Deployment Options Summary

| Method | Difficulty | Cost | Best For |
|--------|-----------|------|----------|
| Local | Easy | Free | Development |
| Docker | Easy | Free | Testing |
| VPS | Medium | $5-20/mo | Production |
| Heroku | Easy | Free-$7/mo | Small scale |
| Cloud Run | Medium | Pay-per-use | Auto-scaling |
| Streamlit Cloud | Easy | Free | Dashboard only |

## 📞 Support

- **Issues**: Open an issue on GitHub
- **Documentation**: Check `docs/` folder
- **Testing**: See `extension/TESTING_GUIDE.md`

---

**Ready to deploy?** Start with the Quick Start section above! 🚀
