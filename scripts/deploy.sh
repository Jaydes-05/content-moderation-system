#!/bin/bash

# ContentGuard Deployment Script
# This script helps deploy ContentGuard components

set -e

echo "╔════════════════════════════════════════════════════════════╗"
echo "║         ContentGuard Deployment Script                     ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Functions
print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

# Check if Python is installed
check_python() {
    if command -v python3 &> /dev/null; then
        PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
        print_success "Python $PYTHON_VERSION found"
        return 0
    else
        print_error "Python 3 not found. Please install Python 3.9+"
        return 1
    fi
}

# Check if pip is installed
check_pip() {
    if command -v pip3 &> /dev/null; then
        print_success "pip found"
        return 0
    else
        print_error "pip not found. Please install pip"
        return 1
    fi
}

# Install dependencies
install_dependencies() {
    print_info "Installing Python dependencies..."
    pip3 install -r requirements.txt
    print_success "Dependencies installed"
}

# Create necessary directories
create_directories() {
    print_info "Creating necessary directories..."
    mkdir -p data/processed
    mkdir -p models/bert/final_model
    mkdir -p logs
    print_success "Directories created"
}

# Initialize database
init_database() {
    print_info "Initializing database..."
    python3 -c "from api.database.db import init_db; init_db()"
    print_success "Database initialized"
}

# Package extension
package_extension() {
    print_info "Packaging browser extension..."
    cd extension
    if command -v zip &> /dev/null; then
        zip -r ../contentguard-extension.zip . -x "*.git*" -x "*node_modules*" -x "*.DS_Store"
        print_success "Extension packaged: contentguard-extension.zip"
    else
        print_warning "zip command not found. Skipping extension packaging."
    fi
    cd ..
}

# Start API
start_api() {
    print_info "Starting API server..."
    print_info "API will be available at: http://localhost:8000"
    print_info "API docs will be available at: http://localhost:8000/docs"
    python3 -m uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
}

# Start Dashboard
start_dashboard() {
    print_info "Starting Streamlit dashboard..."
    print_info "Dashboard will be available at: http://localhost:8501"
    streamlit run dashboard/app.py
}

# Main menu
show_menu() {
    echo ""
    echo "What would you like to deploy?"
    echo ""
    echo "1) Setup Environment (install dependencies, create directories)"
    echo "2) Start API Server (FastAPI backend)"
    echo "3) Start Dashboard (Streamlit)"
    echo "4) Package Extension (create ZIP for Chrome Web Store)"
    echo "5) Full Setup (setup + start API)"
    echo "6) Check System Requirements"
    echo "7) Exit"
    echo ""
    read -p "Enter your choice [1-7]: " choice
}

# Check system requirements
check_requirements() {
    echo ""
    print_info "Checking system requirements..."
    echo ""
    
    # Python
    if check_python; then
        :
    else
        return 1
    fi
    
    # pip
    if check_pip; then
        :
    else
        return 1
    fi
    
    # Git
    if command -v git &> /dev/null; then
        GIT_VERSION=$(git --version | cut -d' ' -f3)
        print_success "Git $GIT_VERSION found"
    else
        print_warning "Git not found (optional)"
    fi
    
    # Node.js (optional)
    if command -v node &> /dev/null; then
        NODE_VERSION=$(node --version)
        print_success "Node.js $NODE_VERSION found"
    else
        print_warning "Node.js not found (optional)"
    fi
    
    # Docker (optional)
    if command -v docker &> /dev/null; then
        DOCKER_VERSION=$(docker --version | cut -d' ' -f3 | tr -d ',')
        print_success "Docker $DOCKER_VERSION found"
    else
        print_warning "Docker not found (optional)"
    fi
    
    echo ""
    print_success "System requirements check complete"
}

# Setup environment
setup_environment() {
    echo ""
    print_info "Setting up environment..."
    echo ""
    
    check_python || exit 1
    check_pip || exit 1
    create_directories
    install_dependencies
    init_database
    
    echo ""
    print_success "Environment setup complete!"
    echo ""
    print_info "Next steps:"
    echo "  1. Start API: ./scripts/deploy.sh (choose option 2)"
    echo "  2. Start Dashboard: ./scripts/deploy.sh (choose option 3)"
    echo "  3. Load extension in browser (see docs/DEPLOYMENT_GUIDE.md)"
}

# Main script
main() {
    while true; do
        show_menu
        
        case $choice in
            1)
                setup_environment
                ;;
            2)
                start_api
                ;;
            3)
                start_dashboard
                ;;
            4)
                package_extension
                ;;
            5)
                setup_environment
                echo ""
                read -p "Press Enter to start API server..."
                start_api
                ;;
            6)
                check_requirements
                ;;
            7)
                print_info "Goodbye!"
                exit 0
                ;;
            *)
                print_error "Invalid choice. Please enter 1-7."
                ;;
        esac
        
        echo ""
        read -p "Press Enter to continue..."
    done
}

# Run main
main
