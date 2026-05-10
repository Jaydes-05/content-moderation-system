# Content Moderation Dashboard

Modern Streamlit frontend for AI-based content moderation system.

## Features

### 🔍 Moderation Tool
- **Text Analysis**: Analyze any text for toxicity
- **Real-time Results**: Instant moderation decisions
- **Visual Breakdown**: Interactive toxicity charts
- **Quick Examples**: Pre-loaded test cases
- **Detailed Explanations**: Human-readable moderation reasoning

### 📊 Analytics Dashboard
- **Overview Metrics**: Total analyzed, toxic rate, blocked content
- **Action Distribution**: Visual breakdown of moderation actions
- **Severity Analysis**: Distribution of toxicity levels
- **Recent Activity**: Latest flagged content
- **Performance Stats**: System performance metrics

### ⚙️ System Status
- **Health Monitoring**: Backend API status
- **Model Status**: BERT model loading state
- **Performance Metrics**: Response time and uptime
- **API Endpoints**: Available endpoints documentation
- **Troubleshooting**: Quick fixes for common issues

## Design

- **Modern Dark Theme**: Professional, easy on the eyes
- **Clean Layout**: Minimal, uncluttered interface
- **Responsive Design**: Works on different screen sizes
- **Interactive Charts**: Plotly visualizations
- **Status Badges**: Color-coded indicators
- **Smooth Animations**: Polished user experience

## Prerequisites

### 1. Backend API Running

The dashboard requires the FastAPI backend to be running:

```bash
# Start the API
uvicorn api.main:app --reload
```

The API should be accessible at: `http://127.0.0.1:8000`

### 2. Install Dependencies

```bash
pip install streamlit plotly requests pandas
```

Or add to `requirements.txt`:
```
streamlit==1.31.0
plotly==5.18.0
requests==2.31.0
pandas==2.2.2
```

## Quick Start

### 1. Start the Backend API

```bash
# Terminal 1: Start API
uvicorn api.main:app --reload
```

### 2. Start the Dashboard

```bash
# Terminal 2: Start dashboard
streamlit run dashboard/app.py
```

### 3. Access the Dashboard

The dashboard will open automatically in your browser at:
- **URL**: http://localhost:8501
- **Network URL**: http://192.168.x.x:8501 (for other devices)

## Usage

### Moderation Tool

1. Navigate to **🔍 Moderation Tool**
2. Enter text in the input area or click a quick example
3. Click **🔍 Analyze Content**
4. View results:
   - Toxicity status (Toxic/Clean)
   - Moderation action (ALLOW/WARNING/HIDE/BLOCK)
   - Severity level (NONE/LOW/MEDIUM/HIGH/CRITICAL)
   - Confidence score
   - Toxicity breakdown chart
   - Detailed explanation

### Analytics Dashboard

1. Navigate to **📊 Analytics Dashboard**
2. View overview metrics:
   - Total analyzed comments
   - Toxic content count and rate
   - Blocked content
   - Average confidence
3. Explore charts:
   - Moderation actions distribution
   - Severity levels distribution
4. Review recent flagged content

### System Status

1. Navigate to **⚙️ System Status**
2. Check system health:
   - Backend API status
   - BERT model status
   - Moderation engine status
3. View performance metrics:
   - Response time
   - Requests today
   - Error rate
4. Review available API endpoints

## Configuration

### Change API URL

Edit `dashboard/app.py` line 23:

```python
API_BASE_URL = "http://127.0.0.1:8000"  # Change to your API URL
```

### Customize Theme

Edit the CSS in `dashboard/app.py` (lines 30-150) to customize:
- Colors
- Fonts
- Spacing
- Animations

### Mock Data

The Analytics Dashboard uses mock data for demonstration. To use real data:
1. Implement database logging in the API
2. Create API endpoints for analytics
3. Update `generate_mock_analytics()` to fetch real data

## Screenshots

### Moderation Tool
- Clean, modern interface
- Large text input area
- Quick example buttons
- Real-time analysis results
- Interactive toxicity charts
- Color-coded status badges

### Analytics Dashboard
- Overview metrics cards
- Pie chart for action distribution
- Bar chart for severity distribution
- Recent flagged content table
- Professional data visualization

### System Status
- Health status indicators
- System information cards
- Performance metrics
- API endpoints table
- Troubleshooting guide

## Architecture

```
dashboard/
├── __init__.py       # Package initialization
├── app.py            # Main Streamlit application
└── README.md         # This file
```

### Components

1. **API Functions**: Communication with FastAPI backend
2. **UI Components**: Reusable UI elements (badges, charts)
3. **Pages**: Three main pages (Moderation, Analytics, Status)
4. **Mock Data**: Demo data for analytics
5. **Custom CSS**: Modern dark theme styling

## Troubleshooting

### Dashboard won't start

```
ModuleNotFoundError: No module named 'streamlit'
```

**Solution**: Install dependencies
```bash
pip install streamlit plotly requests pandas
```

### Cannot connect to API

```
API Error: Cannot connect to API
```

**Solution**: Start the backend API
```bash
uvicorn api.main:app --reload
```

### Port already in use

```
Address already in use
```

**Solution**: Use a different port
```bash
streamlit run dashboard/app.py --server.port 8502
```

### Blank page or errors

**Solution**: Clear Streamlit cache
```bash
streamlit cache clear
```

## Development

### Run in Development Mode

```bash
streamlit run dashboard/app.py --server.runOnSave true
```

### Debug Mode

Add to `dashboard/app.py`:
```python
import streamlit as st
st.write(st.session_state)  # Debug session state
```

### Custom Port

```bash
streamlit run dashboard/app.py --server.port 8502
```

## Production Deployment

### Streamlit Cloud

1. Push code to GitHub
2. Go to https://streamlit.io/cloud
3. Connect repository
4. Deploy

### Docker

```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY . /app

RUN pip install streamlit plotly requests pandas

EXPOSE 8501

CMD ["streamlit", "run", "dashboard/app.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

```bash
docker build -t moderation-dashboard .
docker run -p 8501:8501 moderation-dashboard
```

### Environment Variables

```bash
export API_BASE_URL="https://your-api-url.com"
streamlit run dashboard/app.py
```

## Features Roadmap

- [ ] User authentication
- [ ] Real-time analytics from database
- [ ] Export reports (PDF/CSV)
- [ ] Batch upload and analysis
- [ ] Custom moderation rules configuration
- [ ] Multi-language support
- [ ] Dark/Light theme toggle
- [ ] Advanced filtering and search
- [ ] Historical trends and charts
- [ ] Email notifications for critical content

## Performance

- **Load Time**: < 2 seconds
- **Analysis Time**: ~200ms (depends on API)
- **Memory Usage**: ~100MB
- **Concurrent Users**: Supports multiple users

## Browser Support

- Chrome (recommended)
- Firefox
- Safari
- Edge

## License

Part of the Content Moderation System MLOps project.

## Support

For issues or questions:
1. Check if API is running: http://127.0.0.1:8000/health
2. Check Streamlit logs in terminal
3. Clear cache: `streamlit cache clear`
4. Restart both API and dashboard
