"""
Content Moderation Dashboard

Modern Streamlit frontend for AI-based content moderation system.
Connects to FastAPI backend for toxicity detection and moderation decisions.

Usage:
    streamlit run dashboard/app.py
"""

import sys
import os
from pathlib import Path

# Add project root to Python path for module imports
project_root = Path(__file__).parent.parent.absolute()
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import streamlit as st
import requests
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import time
import logging
from typing import Dict, List, Optional

from api.database import (
    get_total_analyzed,
    get_today_analyzed,
    get_toxic_count,
    get_blocked_count,
    get_blocked_today,
    get_average_confidence,
    get_action_distribution,
    get_severity_distribution,
    get_recent_flagged
)

logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════════════════
# Configuration
# ═══════════════════════════════════════════════════════════════════════════

API_BASE_URL = "http://127.0.0.1:8000"

# Page configuration
st.set_page_config(
    page_title="Content Moderation Dashboard",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for modern dark theme
st.markdown("""
<style>
    /* Main theme colors */
    :root {
        --primary-color: #6366f1;
        --secondary-color: #8b5cf6;
        --success-color: #10b981;
        --warning-color: #f59e0b;
        --danger-color: #ef4444;
        --bg-dark: #0f172a;
        --bg-card: #1e293b;
        --text-primary: #f1f5f9;
        --text-secondary: #94a3b8;
    }
    
    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* Main container */
    .main {
        background-color: var(--bg-dark);
    }
    
    /* Sidebar styling */
    [data-testid="stSidebar"] {
        background-color: var(--bg-card);
    }
    
    /* Card styling */
    .metric-card {
        background: linear-gradient(135deg, #1e293b 0%, #334155 100%);
        padding: 1.5rem;
        border-radius: 12px;
        border: 1px solid #334155;
        margin-bottom: 1rem;
    }
    
    /* Result card */
    .result-card {
        background: var(--bg-card);
        padding: 2rem;
        border-radius: 16px;
        border: 1px solid #334155;
        margin: 1rem 0;
    }
    
    /* Status badges */
    .status-badge {
        display: inline-block;
        padding: 0.5rem 1rem;
        border-radius: 20px;
        font-weight: 600;
        font-size: 0.875rem;
    }
    
    .badge-allow {
        background-color: rgba(16, 185, 129, 0.1);
        color: var(--success-color);
        border: 1px solid var(--success-color);
    }
    
    .badge-warning {
        background-color: rgba(245, 158, 11, 0.1);
        color: var(--warning-color);
        border: 1px solid var(--warning-color);
    }
    
    .badge-hide {
        background-color: rgba(239, 68, 68, 0.1);
        color: var(--danger-color);
        border: 1px solid var(--danger-color);
    }
    
    .badge-block {
        background-color: rgba(239, 68, 68, 0.2);
        color: var(--danger-color);
        border: 2px solid var(--danger-color);
    }
    
    /* Severity badges */
    .severity-none { color: var(--success-color); }
    .severity-low { color: #3b82f6; }
    .severity-medium { color: var(--warning-color); }
    .severity-high { color: #f97316; }
    .severity-critical { color: var(--danger-color); }
    
    /* Headers */
    h1, h2, h3 {
        color: var(--text-primary);
        font-weight: 600;
    }
    
    /* Buttons */
    .stButton>button {
        background: linear-gradient(135deg, var(--primary-color) 0%, var(--secondary-color) 100%);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.75rem 2rem;
        font-weight: 600;
        transition: all 0.3s ease;
    }
    
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 10px 20px rgba(99, 102, 241, 0.3);
    }
    
    /* Text input */
    .stTextArea textarea {
        background-color: var(--bg-card);
        border: 1px solid #334155;
        border-radius: 8px;
        color: var(--text-primary);
    }
    
    /* Metrics */
    [data-testid="stMetricValue"] {
        font-size: 2rem;
        font-weight: 700;
        color: var(--text-primary);
    }
    
    /* Progress bars */
    .stProgress > div > div {
        background: linear-gradient(90deg, var(--primary-color) 0%, var(--secondary-color) 100%);
    }
</style>
""", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════
# API Functions
# ═══════════════════════════════════════════════════════════════════════════

def check_api_health() -> Dict:
    """Check if API is available and healthy."""
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=2)
        if response.status_code == 200:
            return response.json()
        return {"status": "unhealthy", "error": f"Status code: {response.status_code}"}
    except requests.exceptions.ConnectionError:
        return {"status": "offline", "error": "Cannot connect to API"}
    except Exception as e:
        return {"status": "error", "error": str(e)}


def moderate_text(text: str) -> Optional[Dict]:
    """Send text to API for moderation."""
    try:
        response = requests.post(
            f"{API_BASE_URL}/moderate",
            json={"text": text},
            timeout=10
        )
        if response.status_code == 200:
            return response.json()
        return None
    except Exception as e:
        st.error(f"API Error: {str(e)}")
        return None


# ═══════════════════════════════════════════════════════════════════════════
# UI Components
# ═══════════════════════════════════════════════════════════════════════════

def render_sidebar():
    """Render sidebar navigation."""
    with st.sidebar:
        st.markdown("# 🛡️ Content Moderation")
        st.markdown("### AI-Powered Platform")
        st.markdown("---")
        
        # Navigation
        page = st.radio(
            "Navigation",
            ["🔍 Moderation Tool", "📊 Analytics Dashboard", "⚙️ System Status"],
            label_visibility="collapsed"
        )
        
        st.markdown("---")
        
        # Quick stats
        st.markdown("### Quick Stats")
        if 'total_analyzed' not in st.session_state:
            st.session_state.total_analyzed = 0
        if 'total_toxic' not in st.session_state:
            st.session_state.total_toxic = 0
        
        st.metric("Analyzed Today", st.session_state.total_analyzed)
        st.metric("Toxic Detected", st.session_state.total_toxic)
        
        st.markdown("---")
        st.markdown("**Version:** 1.0.0")
        st.markdown("**Backend:** FastAPI")
        st.markdown("**Model:** DistilBERT")
    
    return page


def render_action_badge(action: str) -> str:
    """Render action badge HTML."""
    badge_class = {
        "ALLOW": "badge-allow",
        "WARNING": "badge-warning",
        "HIDE": "badge-hide",
        "BLOCK": "badge-block"
    }.get(action, "badge-allow")
    
    return f'<span class="status-badge {badge_class}">{action}</span>'


def render_severity_badge(severity: str) -> str:
    """Render severity badge HTML."""
    severity_class = {
        "NONE": "severity-none",
        "LOW": "severity-low",
        "MEDIUM": "severity-medium",
        "HIGH": "severity-high",
        "CRITICAL": "severity-critical"
    }.get(severity, "severity-none")
    
    return f'<span class="{severity_class}">● {severity}</span>'


def create_toxicity_chart(predictions: Dict) -> go.Figure:
    """Create horizontal bar chart for toxicity predictions."""
    labels = list(predictions.keys())
    values = list(predictions.values())
    
    # Color scale based on values
    colors = ['#ef4444' if v > 0.7 else '#f59e0b' if v > 0.4 else '#10b981' for v in values]
    
    fig = go.Figure(go.Bar(
        x=values,
        y=labels,
        orientation='h',
        marker=dict(
            color=colors,
            line=dict(color='rgba(255,255,255,0.2)', width=1)
        ),
        text=[f'{v:.2%}' for v in values],
        textposition='auto',
    ))
    
    fig.update_layout(
        title="Toxicity Breakdown",
        xaxis_title="Probability",
        yaxis_title="",
        height=300,
        margin=dict(l=20, r=20, t=40, b=20),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color='#f1f5f9'),
        xaxis=dict(
            gridcolor='rgba(255,255,255,0.1)',
            range=[0, 1]
        ),
        yaxis=dict(
            gridcolor='rgba(255,255,255,0.1)'
        )
    )
    
    return fig


# ═══════════════════════════════════════════════════════════════════════════
# Pages
# ═══════════════════════════════════════════════════════════════════════════

def page_moderation_tool():
    """Moderation tool page."""
    st.markdown("# 🔍 Moderation Tool")
    st.markdown("Analyze text content for toxicity and get moderation recommendations")
    st.markdown("---")
    
    # Initialize session state for text input
    if 'current_text' not in st.session_state:
        st.session_state.current_text = ""
    
    # Input section
    col1, col2 = st.columns([2, 1])
    
    with col2:
        st.markdown("### Quick Examples")
        
        examples = {
            "Clean Comment": "This is a great article, thanks for sharing! I really appreciate the detailed analysis and thoughtful perspective.",
            "Mild Toxicity": "I disagree with your opinion, it's not very smart. You should reconsider your position.",
            "Severe Toxicity": "You are an idiot and should be ashamed of yourself! This is the dumbest thing I've ever read.",
            "Threat": "I will hurt you if you don't stop! You better watch your back."
        }
        
        for label, text in examples.items():
            if st.button(label, use_container_width=True, key=f"example_{label}"):
                st.session_state.current_text = text
    
    with col1:
        st.markdown("### Input Text")
        text_input = st.text_area(
            "Enter text to analyze",
            value=st.session_state.current_text,
            height=200,
            placeholder="Type or paste text here...",
            label_visibility="collapsed",
            key="text_input_area"
        )
        
        # Update session state when text changes
        if text_input != st.session_state.current_text:
            st.session_state.current_text = text_input
        
        analyze_button = st.button("🔍 Analyze Content", use_container_width=True)
    
    # Analysis section
    if analyze_button and st.session_state.current_text:
        with st.spinner("Analyzing content..."):
            result = moderate_text(st.session_state.current_text)
            
            if result:
                # Update stats
                st.session_state.total_analyzed += 1
                if result['is_toxic']:
                    st.session_state.total_toxic += 1
                
                st.markdown("---")
                st.markdown("## 📋 Analysis Results")
                
                # Top metrics
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.markdown('<div class="metric-card">', unsafe_allow_html=True)
                    st.markdown("**Toxicity Status**")
                    if result['is_toxic']:
                        st.markdown("🔴 **TOXIC**")
                    else:
                        st.markdown("🟢 **CLEAN**")
                    st.markdown('</div>', unsafe_allow_html=True)
                
                with col2:
                    st.markdown('<div class="metric-card">', unsafe_allow_html=True)
                    st.markdown("**Moderation Action**")
                    st.markdown(render_action_badge(result['action']), unsafe_allow_html=True)
                    st.markdown('</div>', unsafe_allow_html=True)
                
                with col3:
                    st.markdown('<div class="metric-card">', unsafe_allow_html=True)
                    st.markdown("**Severity Level**")
                    st.markdown(render_severity_badge(result['severity']), unsafe_allow_html=True)
                    st.markdown('</div>', unsafe_allow_html=True)
                
                with col4:
                    st.markdown('<div class="metric-card">', unsafe_allow_html=True)
                    st.markdown("**Confidence**")
                    st.markdown(f"**{result['confidence']:.1%}**")
                    st.markdown('</div>', unsafe_allow_html=True)
                
                # Detailed results
                col1, col2 = st.columns([1, 1])
                
                with col1:
                    st.markdown("### Toxicity Breakdown")
                    fig = create_toxicity_chart(result['predictions'])
                    st.plotly_chart(fig, use_container_width=True)
                
                with col2:
                    st.markdown("### Explanation")
                    st.markdown('<div class="result-card">', unsafe_allow_html=True)
                    st.markdown(result['explanation'])
                    st.markdown('</div>', unsafe_allow_html=True)
                    
                    st.markdown("### Primary Category")
                    st.markdown(f"**{result['primary_label'].replace('_', ' ').title()}**")
                    
                    st.markdown("### Recommended Action")
                    action_descriptions = {
                        "ALLOW": "✅ Content is safe to publish",
                        "WARNING": "⚠️ Flag for review or show warning",
                        "HIDE": "🙈 Hide from public view",
                        "BLOCK": "🚫 Block and remove content"
                    }
                    st.markdown(action_descriptions.get(result['action'], ""))


def page_analytics_dashboard():
    """Analytics dashboard page."""
    st.markdown("# 📊 Analytics Dashboard")
    st.markdown("Real-time moderation statistics and trends")
    st.markdown("---")
    
    # Fetch real data from database
    with st.spinner("Loading analytics..."):
        data = fetch_analytics_data()
    
    # Top metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Total Analyzed",
            f"{data['total_analyzed']:,}",
            f"+{data['today_analyzed']} today"
        )
    
    with col2:
        toxic_rate = (data['toxic_count'] / data['total_analyzed'] * 100) if data['total_analyzed'] > 0 else 0
        st.metric(
            "Toxic Content",
            f"{data['toxic_count']:,}",
            f"{toxic_rate:.1f}%"
        )
    
    with col3:
        st.metric(
            "Blocked",
            f"{data['blocked_count']:,}",
            f"{data['blocked_today']} today"
        )
    
    with col4:
        avg_confidence = data['avg_confidence']
        st.metric(
            "Avg Confidence",
            f"{avg_confidence:.1%}",
            "High accuracy"
        )
    
    st.markdown("---")
    
    # Charts
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### Moderation Actions")
        if data['action_distribution']:
            fig_actions = create_action_distribution_chart(data['action_distribution'])
            st.plotly_chart(fig_actions, use_container_width=True)
        else:
            st.info("No moderation data available yet. Start moderating content to see statistics.")
    
    with col2:
        st.markdown("### Severity Distribution")
        if data['severity_distribution']:
            fig_severity = create_severity_distribution_chart(data['severity_distribution'])
            st.plotly_chart(fig_severity, use_container_width=True)
        else:
            st.info("No severity data available yet.")
    
    # Recent flagged content
    st.markdown("---")
    st.markdown("### Recent Flagged Content")
    
    if data['recent_flagged']:
        df = pd.DataFrame(data['recent_flagged'])
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df['text'] = df['text'].str[:60] + '...'
        
        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "timestamp": st.column_config.DatetimeColumn("Time", format="MMM DD, HH:mm"),
                "text": st.column_config.TextColumn("Content", width="large"),
                "action": st.column_config.TextColumn("Action", width="small"),
                "severity": st.column_config.TextColumn("Severity", width="small"),
                "confidence": st.column_config.ProgressColumn("Confidence", format="%.0f%%", min_value=0, max_value=100)
            }
        )
    else:
        st.info("No flagged content yet. Toxic content will appear here as it's detected.")


def page_system_status():
    """System status page."""
    st.markdown("# ⚙️ System Status")
    st.markdown("Monitor backend health and system performance")
    st.markdown("---")
    
    # Check API health
    with st.spinner("Checking system status..."):
        health = check_api_health()
    
    # Status overview
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("### Backend API")
        if health.get('status') == 'healthy':
            st.success("🟢 Online")
        elif health.get('status') == 'offline':
            st.error("🔴 Offline")
        else:
            st.warning("🟡 Degraded")
    
    with col2:
        st.markdown("### BERT Model")
        if health.get('model_loaded'):
            st.success("🟢 Loaded")
        else:
            st.error("🔴 Not Loaded")
    
    with col3:
        st.markdown("### Moderation Engine")
        if health.get('moderator_loaded'):
            st.success("🟢 Ready")
        else:
            st.error("🔴 Not Ready")
    
    st.markdown("---")
    
    # Detailed status
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### System Information")
        st.markdown('<div class="result-card">', unsafe_allow_html=True)
        
        if health.get('status') == 'healthy':
            st.markdown(f"**Status:** 🟢 Healthy")
            st.markdown(f"**API Version:** {health.get('version', 'Unknown')}")
            st.markdown(f"**Backend URL:** `{API_BASE_URL}`")
            st.markdown(f"**Model Status:** {'✅ Loaded' if health.get('model_loaded') else '❌ Not Loaded'}")
            st.markdown(f"**Moderator Status:** {'✅ Ready' if health.get('moderator_loaded') else '❌ Not Ready'}")
        else:
            st.markdown(f"**Status:** 🔴 {health.get('status', 'Unknown').title()}")
            st.markdown(f"**Error:** {health.get('error', 'Unknown error')}")
            st.markdown(f"**Backend URL:** `{API_BASE_URL}`")
            
            st.markdown("---")
            st.markdown("**Troubleshooting:**")
            st.markdown("1. Make sure the API is running:")
            st.code("uvicorn api.main:app --reload", language="bash")
            st.markdown("2. Check if the model is trained:")
            st.code("python train_bert_10k.py", language="bash")
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        st.markdown("### Performance Metrics")
        st.markdown('<div class="result-card">', unsafe_allow_html=True)
        
        if health.get('status') == 'healthy':
            # Test API response time
            start_time = time.time()
            try:
                requests.get(f"{API_BASE_URL}/health", timeout=5)
                response_time = (time.time() - start_time) * 1000
                st.markdown(f"**Response Time:** {response_time:.0f}ms")
                
                if response_time < 100:
                    st.success("Excellent")
                elif response_time < 500:
                    st.info("Good")
                else:
                    st.warning("Slow")
            except:
                st.error("Cannot measure response time")
            
            st.markdown(f"**Uptime:** Monitoring not implemented")
            st.markdown(f"**Requests Today:** {st.session_state.total_analyzed}")
            st.markdown(f"**Error Rate:** 0%")
        else:
            st.error("Cannot retrieve performance metrics")
            st.markdown("API is not responding")
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    # API endpoints
    st.markdown("---")
    st.markdown("### Available Endpoints")
    
    endpoints = [
        {"endpoint": "/health", "method": "GET", "description": "Health check"},
        {"endpoint": "/predict", "method": "POST", "description": "Get toxicity predictions"},
        {"endpoint": "/moderate", "method": "POST", "description": "Get moderation decision"},
        {"endpoint": "/batch-moderate", "method": "POST", "description": "Batch moderation"},
    ]
    
    df = pd.DataFrame(endpoints)
    st.dataframe(df, use_container_width=True, hide_index=True)


# ═══════════════════════════════════════════════════════════════════════════
# Analytics Data Fetching
# ═══════════════════════════════════════════════════════════════════════════

def fetch_analytics_data() -> Dict:
    """
    Fetch real analytics data from the database.
    
    Returns:
        Dict with analytics data structure
    """
    import logging
    
    logger = logging.getLogger(__name__)
    
    try:
        from api.database.db import (
            get_total_analyzed,
            get_today_analyzed,
            get_toxic_count,
            get_blocked_count,
            get_blocked_today,
            get_average_confidence,
            get_action_distribution,
            get_severity_distribution,
            get_recent_flagged
        )
        
        return {
            'total_analyzed': get_total_analyzed(),
            'today_analyzed': get_today_analyzed(),
            'toxic_count': get_toxic_count(),
            'blocked_count': get_blocked_count(),
            'blocked_today': get_blocked_today(),
            'avg_confidence': get_average_confidence(),
            'action_distribution': get_action_distribution(),
            'severity_distribution': get_severity_distribution(),
            'recent_flagged': get_recent_flagged(limit=10)
        }
    except Exception as e:
        logger.error(f"Failed to fetch analytics data: {e}")
        # Return empty/zero data structure on error
        return {
            'total_analyzed': 0,
            'today_analyzed': 0,
            'toxic_count': 0,
            'blocked_count': 0,
            'blocked_today': 0,
            'avg_confidence': 0.0,
            'action_distribution': {},
            'severity_distribution': {},
            'recent_flagged': []
        }


def generate_mock_analytics() -> Dict:
    """Generate mock analytics data for demo (DEPRECATED - use fetch_analytics_data)."""
    return {
        'total_analyzed': 15847,
        'today_analyzed': 342,
        'toxic_count': 1891,
        'blocked_count': 456,
        'blocked_today': 12,
        'avg_confidence': 0.87,
        'action_distribution': {
            'ALLOW': 13245,
            'WARNING': 1234,
            'HIDE': 912,
            'BLOCK': 456
        },
        'severity_distribution': {
            'NONE': 13245,
            'LOW': 1234,
            'MEDIUM': 856,
            'HIGH': 412,
            'CRITICAL': 100
        },
        'recent_flagged': [
            {
                'timestamp': datetime.now() - timedelta(minutes=5),
                'text': 'You are an idiot and should be ashamed of yourself!',
                'action': 'BLOCK',
                'severity': 'HIGH',
                'confidence': 94
            },
            {
                'timestamp': datetime.now() - timedelta(minutes=12),
                'text': 'This is stupid and makes no sense at all.',
                'action': 'WARNING',
                'severity': 'LOW',
                'confidence': 67
            },
            {
                'timestamp': datetime.now() - timedelta(minutes=23),
                'text': 'I will hurt you if you keep doing this!',
                'action': 'BLOCK',
                'severity': 'CRITICAL',
                'confidence': 98
            },
            {
                'timestamp': datetime.now() - timedelta(minutes=34),
                'text': 'You are being ridiculous and annoying.',
                'action': 'HIDE',
                'severity': 'MEDIUM',
                'confidence': 78
            },
            {
                'timestamp': datetime.now() - timedelta(minutes=45),
                'text': 'This comment is offensive and inappropriate.',
                'action': 'HIDE',
                'severity': 'MEDIUM',
                'confidence': 72
            }
        ]
    }


def create_action_distribution_chart(data: Dict) -> go.Figure:
    """Create pie chart for action distribution."""
    colors = ['#10b981', '#3b82f6', '#f59e0b', '#ef4444']
    
    fig = go.Figure(data=[go.Pie(
        labels=list(data.keys()),
        values=list(data.values()),
        hole=0.4,
        marker=dict(colors=colors, line=dict(color='#1e293b', width=2)),
        textinfo='label+percent',
        textfont=dict(size=12, color='white')
    )])
    
    fig.update_layout(
        height=300,
        margin=dict(l=20, r=20, t=20, b=20),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color='#f1f5f9'),
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.2,
            xanchor="center",
            x=0.5
        )
    )
    
    return fig


def create_severity_distribution_chart(data: Dict) -> go.Figure:
    """Create bar chart for severity distribution."""
    colors = ['#10b981', '#3b82f6', '#f59e0b', '#f97316', '#ef4444']
    
    fig = go.Figure(data=[go.Bar(
        x=list(data.keys()),
        y=list(data.values()),
        marker=dict(
            color=colors,
            line=dict(color='rgba(255,255,255,0.2)', width=1)
        ),
        text=list(data.values()),
        textposition='auto',
    )])
    
    fig.update_layout(
        height=300,
        margin=dict(l=20, r=20, t=20, b=20),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color='#f1f5f9'),
        xaxis=dict(
            gridcolor='rgba(255,255,255,0.1)',
            title=""
        ),
        yaxis=dict(
            gridcolor='rgba(255,255,255,0.1)',
            title="Count"
        )
    )
    
    return fig


# ═══════════════════════════════════════════════════════════════════════════
# Main Application
# ═══════════════════════════════════════════════════════════════════════════

def main():
    """Main application entry point."""
    # Initialize session state
    if 'total_analyzed' not in st.session_state:
        st.session_state.total_analyzed = 0
    if 'total_toxic' not in st.session_state:
        st.session_state.total_toxic = 0
    
    # Render sidebar and get selected page
    page = render_sidebar()
    
    # Render selected page
    if page == "🔍 Moderation Tool":
        page_moderation_tool()
    elif page == "📊 Analytics Dashboard":
        page_analytics_dashboard()
    elif page == "⚙️ System Status":
        page_system_status()


if __name__ == "__main__":
    main()
