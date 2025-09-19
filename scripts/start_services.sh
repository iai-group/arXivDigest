#!/bin/bash

# arXivDigest Service Startup Script
# This script starts all required services for arXivDigest in the correct order

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_DIR="/Users/daud/Desktop/university/DAT620/arXivDigest"
VENV_PATH="$PROJECT_DIR/.venv"
ELASTICSEARCH_LOG="/tmp/elasticsearch.log"
FRONTEND_LOG="/tmp/arxivdigest_frontend.log"
API_LOG="/tmp/arxivdigest_api.log"

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if a service is running
check_service() {
    local service_name=$1
    local port=$2
    local max_attempts=30
    local attempt=1
    
    print_status "Waiting for $service_name to start on port $port..."
    
    while [ $attempt -le $max_attempts ]; do
        if curl -s "http://localhost:$port" > /dev/null 2>&1; then
            print_success "$service_name is running on port $port"
            return 0
        fi
        sleep 2
        attempt=$((attempt + 1))
    done
    
    print_error "$service_name failed to start on port $port after $((max_attempts * 2)) seconds"
    return 1
}

# Function to check if a process is running by name
check_process() {
    local process_name=$1
    if pgrep -f "$process_name" > /dev/null; then
        return 0
    else
        return 1
    fi
}

echo "======================================"
echo "  arXivDigest Service Startup"
echo "======================================"
echo

# Check if we're in the right directory
if [ ! -f "$PROJECT_DIR/config.json" ]; then
    print_error "Project directory not found or config.json missing!"
    print_error "Expected: $PROJECT_DIR"
    exit 1
fi

# Change to project directory
cd "$PROJECT_DIR"

# Activate virtual environment
if [ ! -d "$VENV_PATH" ]; then
    print_error "Virtual environment not found at $VENV_PATH"
    print_error "Please run: python -m venv .venv"
    exit 1
fi

print_status "Activating Python virtual environment..."
source "$VENV_PATH/bin/activate"

# 1. Start MySQL (if not already running)
print_status "Starting MySQL database..."
if brew services list | grep mysql | grep -q "started"; then
    print_success "MySQL is already running"
else
    brew services start mysql
    sleep 5
    if brew services list | grep mysql | grep -q "started"; then
        print_success "MySQL started successfully"
    else
        print_error "Failed to start MySQL"
        exit 1
    fi
fi

# 2. Start Elasticsearch
print_status "Starting Elasticsearch..."
if check_process "elasticsearch"; then
    print_success "Elasticsearch is already running"
else
    print_status "Setting up Elasticsearch environment..."
    export ES_JAVA_HOME=/opt/homebrew/opt/openjdk@11/libexec/openjdk.jdk/Contents/Home
    
    print_status "Starting Elasticsearch in background..."
    nohup /opt/homebrew/opt/elasticsearch-full/bin/elasticsearch > "$ELASTICSEARCH_LOG" 2>&1 &
    
    # Wait for Elasticsearch to start
    if check_service "Elasticsearch" "9200"; then
        print_success "Elasticsearch started successfully"
    else
        print_error "Failed to start Elasticsearch. Check log: $ELASTICSEARCH_LOG"
        exit 1
    fi
fi

# 3. Start Frontend Service
print_status "Starting arXivDigest Frontend..."
if check_process "arxivdigest.frontend.app"; then
    print_warning "Frontend appears to be already running"
    pkill -f "arxivdigest.frontend.app" || true
    sleep 2
fi

print_status "Starting Frontend on port 8080..."
nohup python -m arxivdigest.frontend.app > "$FRONTEND_LOG" 2>&1 &
FRONTEND_PID=$!

# Wait for Frontend to start
if check_service "Frontend" "8080"; then
    print_success "Frontend started successfully (PID: $FRONTEND_PID)"
else
    print_error "Failed to start Frontend. Check log: $FRONTEND_LOG"
    exit 1
fi

# 4. Start API Service (optional, if it exists)
print_status "Checking for API service..."
if [ -f "$PROJECT_DIR/arxivdigest/api/app.py" ]; then
    print_status "Starting arXivDigest API..."
    if check_process "arxivdigest.api.app"; then
        print_warning "API appears to be already running"
        pkill -f "arxivdigest.api.app" || true
        sleep 2
    fi
    
    print_status "Starting API on port 5000..."
    nohup python -m arxivdigest.api.app > "$API_LOG" 2>&1 &
    API_PID=$!
    
    # Wait for API to start
    if check_service "API" "5000"; then
        print_success "API started successfully (PID: $API_PID)"
    else
        print_warning "API failed to start. Check log: $API_LOG"
        print_warning "Continuing without API service..."
    fi
else
    print_warning "API service not found, skipping..."
fi

echo
echo "======================================"
echo "  Service Startup Complete!"
echo "======================================"
echo
print_success "All services are now running:"
echo "  🗄️  MySQL Database: localhost:3306"
echo "  🔍 Elasticsearch: http://localhost:9200"
echo "  🌐 Frontend: http://localhost:8080"
if [ -f "$PROJECT_DIR/arxivdigest/api/app.py" ] && check_process "arxivdigest.api.app"; then
    echo "  🔧 API: http://localhost:5000"
fi
echo
echo "Log files:"
echo "  📋 Elasticsearch: $ELASTICSEARCH_LOG"
echo "  📋 Frontend: $FRONTEND_LOG"
if [ -f "$API_LOG" ]; then
    echo "  📋 API: $API_LOG"
fi
echo
print_status "To stop all services, run: ./scripts/stop_services.sh"
print_status "To check service status, run: ./scripts/check_services.sh"
echo
