# ContentGuard - Deployment Guide

Complete guide for deploying the ContentGuard content moderation system.

## 📋 Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Browser Extension Deployment](#browser-extension-deployment)
3. [Backend API Deployment](#backend-api-deployment)
4. [Dashboard Deployment](#dashboard-deployment)
5. [Production Considerations](#production-considerations)
6. [Monitoring & Maintenance](#monitoring--maintenance)

---

## 🏗️ Architecture Overview

ContentGuard consists of three main components:

```
┌─────────────────────────────────────────────────────────────┐
│                    ContentGuard System                       │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────────┐      ┌──────────────────┐            │
│  │  Browser         │      │  Backend API     │            │
│  │  Extension       │─────▶│  (FastAPI)       │            │
│  │  (Chrome/Edge)   │      │  Port 8000       │            │
│  └──────────────────┘      └──────────────────┘            │
│         │                           │                        │
│         │                           │                        │
│         │                   ┌──────────────────┐            │
│         │                   │  Dashboard       │            │
│         └──────────────────▶│  (Streamlit)     │            │
│                             │  Port 8501       │            │
│                             └──────────────────┘            │
│                                                               │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Shared Resources                                     │  │
│  │  - SQLite Database (data/moderation_history.db)      │  │
│  │  - BERT Model (models/bert/final_model/)             │  │
│  │  - Training Data (data/train.csv)                    │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

**Deployment Options:**
- **Option 1**: Extension only (works standalone with rule-based detection)
- **Option 2**: Extension + Backend API (enables BERT ML model)
- **Option 3**: Full stack (Extension + API + Dashboard)

---

## 🧩 Browser Extension Deployment

### Chrome Web Store (Recommended for Public Release)

#### Prerequisites
- Google Developer Account ($5 one-time fee)
- Extension tested and working
- Privacy policy hosted online
- Screenshots and promotional images

#### Step 1: Prepare Extension Package

```bash
# Navigate to project root
cd content-moderation-system-main

# Create distribution package
cd extension
zip -r contentguard-extension.zip . -x "*.git*" -x "*node_modules*" -x "*.DS_Store"
```

Or use the packaging script:
```bash
python scripts/package_extension.py
```

#### Step 2: Create Chrome Web Store Listing

1. **Go to Chrome Web Store Developer Dashboard**
   - Visit: https://chrome.google.com/webstore/devconsole
   - Sign in with Google account
   - Pay $5 developer registration fee (one-time)

2. **Create New Item**
   - Click "New Item"
   - Upload `contentguard-extension.zip`
   - Wait for upload to complete

3. **Fill Store Listing**

   **Required Information:**
   - **Name**: ContentGuard - AI Content Moderation
   - **Summary**: AI-powered content moderation for social media using BERT ML
   - **Description**: (See below)
   - **Category**: Social & Communication
   - **Language**: English

   **Description Template:**
   ```
   ContentGuard - AI-Powered Content Moderation

   Protect yourself from toxic content across social media platforms using advanced BERT machine learning.

   🎯 KEY FEATURES:
   • Real-time toxicity detection with 92.8% accuracy
   • Supports Twitter/X, Facebook, LinkedIn, YouTube, Reddit, Instagram, TikTok
   • AI Context Analysis with sarcasm detection
   • Community Health Dashboard
   • Batch moderation mode
   • Multi-format export (CSV, JSON, PDF)
   • Privacy-focused - all processing happens locally

   🤖 BERT ML MODEL:
   Uses state-of-the-art DistilBERT transformer model trained on 160k+ comments
   for accurate toxicity detection across 6 categories.

   🛡️ PRIVACY:
   • No data sent to external servers
   • Optional backend for enhanced ML features
   • Open source and transparent

   📊 FEATURES:
   • Toxicity scoring (0-100%)
   • Sentiment analysis
   • User reputation tracking
   • Historical trends
   • Customizable thresholds
   • Auto-hide toxic content

   Perfect for content moderators, community managers, and anyone who wants
   a safer social media experience.
   ```

4. **Upload Assets**

   **Required Screenshots** (1280x800 or 640x400):
   - Extension panel showing stats
   - Comment analysis view
   - Community health dashboard
   - Batch moderation interface
   - Settings panel

   **Promotional Images**:
   - Small tile: 440x280
   - Large tile: 920x680
   - Marquee: 1400x560

5. **Privacy Policy**
   - Host `extension/PRIVACY_POLICY.md` on GitHub Pages or your website
   - Add URL to store listing
   - Example: `https://yourusername.github.io/contentguard/privacy`

6. **Permissions Justification**
   - Explain why each permission is needed
   - `activeTab`: To analyze comments on current page
   - `storage`: To save user settings and preferences
   - `host permissions`: To detect and analyze content on social media sites

7. **Submit for Review**
   - Click "Submit for Review"
   - Review typically takes 1-3 business days
   - Address any feedback from Google

#### Step 3: Edge Add-ons Store (Optional)

Microsoft Edge uses the same extension format:

1. **Go to Edge Add-ons Dashboard**
   - Visit: https://partner.microsoft.com/dashboard/microsoftedge
   - Sign in with Microsoft account (free)

2. **Submit Extension**
   - Upload same ZIP file
   - Fill similar information
   - Review process: 1-2 business days

See `extension/EDGE_PUBLISHING_GUIDE.md` for detailed Edge instructions.

### Manual Installation (For Testing/Private Use)

#### Chrome/Edge

```bash
1. Open browser
2. Go to chrome://extensions/ (or edge://extensions/)
3. Enable "Developer mode" (top-right toggle)
4. Click "Load unpacked"
5. Select the extension/ folder
6. Extension icon appears in toolbar
```

#### Firefox

```bash
1. Open Firefox
2. Go to about:debugging#/runtime/this-firefox
3. Click "Load Temporary Add-on"
4. Select extension/manifest.json
5. Extension loads (temporary - removed on restart)
```

For permanent Firefox installation, you need to sign the extension through Mozilla Add-ons.

---

## 🚀 Backend API Deployment

The FastAPI backend can be deployed in multiple ways:

### Option 1: Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Start API
python -m uvicorn api.main:app --reload --host 0.0.0.0 --port 8000

# API available at:
# http://localhost:8000
# http://localhost:8000/docs (Swagger UI)
```

### Option 2: Production Server (Linux/Ubuntu)

#### Prerequisites
- Ubuntu 20.04+ or similar Linux distribution
- Python 3.9+
- Domain name (optional, for HTTPS)

#### Step 1: Server Setup

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python and dependencies
sudo apt install python3.9 python3.9-venv python3-pip nginx -y

# Create application user
sudo useradd -m -s /bin/bash contentguard
sudo su - contentguard
```

#### Step 2: Deploy Application

```bash
# Clone repository
git clone https://github.com/yourusername/content-moderation-system.git
cd content-moderation-system

# Create virtual environment
python3.9 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create necessary directories
mkdir -p data models/bert logs
```

#### Step 3: Configure Systemd Service

Create `/etc/systemd/system/contentguard-api.service`:

```ini
[Unit]
Description=ContentGuard API Service
After=network.target

[Service]
Type=notify
User=contentguard
Group=contentguard
WorkingDirectory=/home/contentguard/content-moderation-system
Environment="PATH=/home/contentguard/content-moderation-system/venv/bin"
ExecStart=/home/contentguard/content-moderation-system/venv/bin/uvicorn api.main:app --host 0.0.0.0 --port 8000 --workers 4
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start service:

```bash
sudo systemctl daemon-reload
sudo systemctl enable contentguard-api
sudo systemctl start contentguard-api
sudo systemctl status contentguard-api
```

#### Step 4: Configure Nginx Reverse Proxy

Create `/etc/nginx/sites-available/contentguard`:

```nginx
server {
    listen 80;
    server_name api.contentguard.com;  # Replace with your domain

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # CORS headers
        add_header Access-Control-Allow-Origin *;
        add_header Access-Control-Allow-Methods "GET, POST, OPTIONS";
        add_header Access-Control-Allow-Headers "Content-Type, Authorization";
    }

    # Health check endpoint
    location /health {
        proxy_pass http://127.0.0.1:8000/health;
        access_log off;
    }
}
```

Enable site:

```bash
sudo ln -s /etc/nginx/sites-available/contentguard /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

#### Step 5: Setup SSL with Let's Encrypt (Optional but Recommended)

```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx -y

# Obtain SSL certificate
sudo certbot --nginx -d api.contentguard.com

# Auto-renewal is configured automatically
sudo certbot renew --dry-run
```

### Option 3: Docker Deployment

#### Create Dockerfile

Create `Dockerfile` in project root:

```dockerfile
FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Create data directory
RUN mkdir -p data models/bert

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health')"

# Run application
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
```

#### Create docker-compose.yml

```yaml
version: '3.8'

services:
  api:
    build: .
    container_name: contentguard-api
    ports:
      - "8000:8000"
    volumes:
      - ./data:/app/data
      - ./models:/app/models
    environment:
      - PYTHONUNBUFFERED=1
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

  dashboard:
    build: .
    container_name: contentguard-dashboard
    command: streamlit run dashboard/app.py --server.port=8501 --server.address=0.0.0.0
    ports:
      - "8501:8501"
    volumes:
      - ./data:/app/data
    depends_on:
      - api
    restart: unless-stopped
```

#### Deploy with Docker

```bash
# Build and start services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down

# Rebuild after changes
docker-compose up -d --build
```

### Option 4: Cloud Platforms

#### Heroku

```bash
# Install Heroku CLI
curl https://cli-assets.heroku.com/install.sh | sh

# Login
heroku login

# Create app
heroku create contentguard-api

# Add Procfile
echo "web: uvicorn api.main:app --host 0.0.0.0 --port \$PORT" > Procfile

# Deploy
git push heroku main

# Open app
heroku open
```

#### AWS EC2

1. Launch EC2 instance (Ubuntu 20.04)
2. Configure security group (ports 22, 80, 443, 8000)
3. SSH into instance
4. Follow "Production Server" steps above

#### Google Cloud Run

```bash
# Build container
gcloud builds submit --tag gcr.io/PROJECT_ID/contentguard-api

# Deploy
gcloud run deploy contentguard-api \
  --image gcr.io/PROJECT_ID/contentguard-api \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated
```

#### DigitalOcean App Platform

1. Connect GitHub repository
2. Select branch (extension)
3. Configure build:
   - Build command: `pip install -r requirements.txt`
   - Run command: `uvicorn api.main:app --host 0.0.0.0 --port 8080`
4. Deploy

---

## 📊 Dashboard Deployment

### Option 1: Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Start dashboard
streamlit run dashboard/app.py

# Dashboard available at:
# http://localhost:8501
```

### Option 2: Streamlit Cloud (Free Hosting)

1. **Push to GitHub**
   ```bash
   git push origin extension
   ```

2. **Deploy on Streamlit Cloud**
   - Visit: https://streamlit.io/cloud
   - Sign in with GitHub
   - Click "New app"
   - Select repository: `content-moderation-system`
   - Branch: `extension`
   - Main file: `dashboard/app.py`
   - Click "Deploy"

3. **Configure Secrets** (if needed)
   - Go to app settings
   - Add secrets in TOML format
   - Example:
     ```toml
     [database]
     path = "data/moderation_history.db"
     ```

4. **Custom Domain** (Optional)
   - Go to app settings → General
   - Add custom domain
   - Configure DNS CNAME record

### Option 3: Production Server

```bash
# Create systemd service
sudo nano /etc/systemd/system/contentguard-dashboard.service
```

```ini
[Unit]
Description=ContentGuard Dashboard
After=network.target

[Service]
Type=simple
User=contentguard
WorkingDirectory=/home/contentguard/content-moderation-system
Environment="PATH=/home/contentguard/content-moderation-system/venv/bin"
ExecStart=/home/contentguard/content-moderation-system/venv/bin/streamlit run dashboard/app.py --server.port=8501 --server.address=0.0.0.0
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable contentguard-dashboard
sudo systemctl start contentguard-dashboard
```

---

## 🔒 Production Considerations

### Security

1. **API Security**
   ```python
   # Add API key authentication
   from fastapi import Security, HTTPException
   from fastapi.security import APIKeyHeader
   
   API_KEY = "your-secret-key"
   api_key_header = APIKeyHeader(name="X-API-Key")
   
   def verify_api_key(api_key: str = Security(api_key_header)):
       if api_key != API_KEY:
           raise HTTPException(status_code=403, detail="Invalid API Key")
   ```

2. **CORS Configuration**
   ```python
   # In api/main.py - restrict origins in production
   app.add_middleware(
       CORSMiddleware,
       allow_origins=["https://yourdomain.com"],  # Specific domains only
       allow_credentials=True,
       allow_methods=["GET", "POST"],
       allow_headers=["*"],
   )
   ```

3. **Rate Limiting**
   ```bash
   pip install slowapi
   ```
   
   ```python
   from slowapi import Limiter, _rate_limit_exceeded_handler
   from slowapi.util import get_remote_address
   
   limiter = Limiter(key_func=get_remote_address)
   app.state.limiter = limiter
   
   @app.post("/moderate")
   @limiter.limit("10/minute")
   async def moderate(request: Request, data: TextRequest):
       # ... existing code
   ```

4. **Environment Variables**
   ```bash
   # Create .env file
   API_KEY=your-secret-key
   DATABASE_URL=sqlite:///data/moderation_history.db
   MODEL_PATH=models/bert/final_model
   CORS_ORIGINS=https://yourdomain.com
   ```

### Performance

1. **Database Optimization**
   - Use PostgreSQL instead of SQLite for production
   - Add indexes on frequently queried columns
   - Implement connection pooling

2. **Caching**
   ```bash
   pip install redis
   ```
   
   ```python
   import redis
   cache = redis.Redis(host='localhost', port=6379, db=0)
   
   # Cache predictions
   cache_key = f"prediction:{hash(text)}"
   cached = cache.get(cache_key)
   if cached:
       return json.loads(cached)
   ```

3. **Load Balancing**
   - Use multiple API workers
   - Configure Nginx load balancing
   - Use Gunicorn with multiple workers

4. **CDN for Extension**
   - Host extension assets on CDN
   - Reduce load times globally

### Monitoring

1. **Logging**
   ```python
   import logging
   
   logging.basicConfig(
       level=logging.INFO,
       format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
       handlers=[
           logging.FileHandler('logs/api.log'),
           logging.StreamHandler()
       ]
   )
   ```

2. **Health Checks**
   - Monitor `/health` endpoint
   - Set up uptime monitoring (UptimeRobot, Pingdom)
   - Configure alerts for downtime

3. **Metrics**
   ```bash
   pip install prometheus-fastapi-instrumentator
   ```
   
   ```python
   from prometheus_fastapi_instrumentator import Instrumentator
   
   Instrumentator().instrument(app).expose(app)
   ```

4. **Error Tracking**
   - Use Sentry for error tracking
   - Monitor API response times
   - Track user metrics

### Backup

```bash
# Backup database
cp data/moderation_history.db backups/moderation_$(date +%Y%m%d).db

# Automated daily backup
crontab -e
# Add: 0 2 * * * /path/to/backup-script.sh
```

---

## 🔧 Monitoring & Maintenance

### Health Checks

```bash
# API health
curl http://localhost:8000/health

# Dashboard health
curl http://localhost:8501/healthz
```

### Logs

```bash
# API logs
sudo journalctl -u contentguard-api -f

# Dashboard logs
sudo journalctl -u contentguard-dashboard -f

# Nginx logs
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log
```

### Updates

```bash
# Pull latest code
git pull origin extension

# Restart services
sudo systemctl restart contentguard-api
sudo systemctl restart contentguard-dashboard
```

### Database Maintenance

```bash
# Vacuum database
sqlite3 data/moderation_history.db "VACUUM;"

# Check database size
du -h data/moderation_history.db

# Export data
sqlite3 data/moderation_history.db ".dump" > backup.sql
```

---

## 📝 Deployment Checklist

### Pre-Deployment

- [ ] All tests passing
- [ ] Environment variables configured
- [ ] Database migrations completed
- [ ] SSL certificates obtained
- [ ] Backup strategy in place
- [ ] Monitoring configured
- [ ] Documentation updated

### Extension Deployment

- [ ] Extension tested in Chrome/Edge
- [ ] Privacy policy published
- [ ] Screenshots prepared
- [ ] Store listing completed
- [ ] Submitted for review

### API Deployment

- [ ] Server provisioned
- [ ] Dependencies installed
- [ ] Systemd service configured
- [ ] Nginx configured
- [ ] SSL enabled
- [ ] Health checks passing
- [ ] Logs accessible

### Dashboard Deployment

- [ ] Streamlit app deployed
- [ ] Database connection working
- [ ] Custom domain configured (optional)
- [ ] Access controls in place

### Post-Deployment

- [ ] Monitor error rates
- [ ] Check performance metrics
- [ ] Verify backups working
- [ ] Test all features
- [ ] Update documentation
- [ ] Announce to users

---

## 🆘 Troubleshooting

### Extension Not Loading

```bash
# Check manifest.json syntax
cat extension/manifest.json | python -m json.tool

# Check console for errors
# Right-click extension icon → Inspect popup
```

### API Not Starting

```bash
# Check logs
sudo journalctl -u contentguard-api -n 50

# Test manually
cd /home/contentguard/content-moderation-system
source venv/bin/activate
python -m uvicorn api.main:app --reload
```

### Database Errors

```bash
# Check permissions
ls -la data/moderation_history.db

# Fix permissions
sudo chown contentguard:contentguard data/moderation_history.db
```

### High Memory Usage

```bash
# Check memory
free -h

# Reduce workers
# Edit systemd service: --workers 2 instead of 4
```

---

## 📚 Additional Resources

- [FastAPI Deployment](https://fastapi.tiangolo.com/deployment/)
- [Streamlit Deployment](https://docs.streamlit.io/streamlit-community-cloud/get-started/deploy-an-app)
- [Chrome Extension Publishing](https://developer.chrome.com/docs/webstore/publish/)
- [Nginx Configuration](https://nginx.org/en/docs/)
- [Let's Encrypt](https://letsencrypt.org/getting-started/)

---

## 💡 Tips

1. **Start Small**: Deploy extension first, then add backend
2. **Use Demo Mode**: API works without ML models for testing
3. **Monitor Costs**: Cloud services can get expensive
4. **Automate**: Use CI/CD for automated deployments
5. **Document**: Keep deployment notes for future reference

---

**Need Help?** Check the troubleshooting section or open an issue on GitHub.
