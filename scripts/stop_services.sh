#!/bin/bash

# arXivDigest Service Shutdown Script
# This script stops all arXivDigest services gracefully

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

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

# Function to stop a process by name
stop_process() {
    local process_name=$1
    local display_name=$2
    
    print_status "Stopping $display_name..."
    
    # Get PIDs of matching processes
    local pids=$(pgrep -f "$process_name" || true)
    
    if [ -z "$pids" ]; then
        print_success "$display_name is not running"
        return 0
    fi
    
    # Try graceful shutdown first (SIGTERM)
    echo "$pids" | xargs kill -TERM 2>/dev/null || true
    
    # Wait a bit for graceful shutdown
    sleep 3
    
    # Check if processes are still running
    local remaining_pids=$(pgrep -f "$process_name" || true)
    
    if [ -z "$remaining_pids" ]; then
        print_success "$display_name stopped gracefully"
        return 0
    fi
    
    # Force kill if still running (SIGKILL)
    print_warning "$display_name didn't stop gracefully, forcing shutdown..."
    echo "$remaining_pids" | xargs kill -KILL 2>/dev/null || true
    
    sleep 2
    
    # Final check
    local final_check=$(pgrep -f "$process_name" || true)
    if [ -z "$final_check" ]; then
        print_success "$display_name stopped (forced)"
    else
        print_error "Failed to stop $display_name"
        return 1
    fi
}

# Function to stop Homebrew service
stop_brew_service() {
    local service_name=$1
    local display_name=$2
    
    print_status "Stopping $display_name..."
    
    if brew services list | grep "$service_name" | grep -q "started"; then
        brew services stop "$service_name"
        print_success "$display_name stopped"
    else
        print_success "$display_name is not running"
    fi
}

echo "======================================"
echo "  arXivDigest Service Shutdown"
echo "======================================"
echo

# Stop services in reverse order (opposite of startup)

# 1. Stop API Service
stop_process "arxivdigest.api.app" "arXivDigest API"

# 2. Stop Frontend Service
stop_process "arxivdigest.frontend.app" "arXivDigest Frontend"

# 3. Stop any other arXivDigest Python processes
print_status "Checking for other arXivDigest processes..."
stop_process "python.*arxivdigest" "Other arXivDigest processes"

# 4. Stop Elasticsearch
print_status "Stopping Elasticsearch..."
stop_process "elasticsearch" "Elasticsearch"

# Also try to stop via Homebrew service (in case it was started that way)
if brew services list | grep elasticsearch-full | grep -q "started"; then
    brew services stop elasticsearch-full
fi

# 5. Optionally stop MySQL (ask user first)
echo
read -p "Do you want to stop MySQL database? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    stop_brew_service "mysql" "MySQL Database"
else
    print_status "Keeping MySQL running as requested"
fi

# Clean up log files (optional)
echo
read -p "Do you want to clean up log files? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    print_status "Cleaning up log files..."
    rm -f /tmp/elasticsearch.log
    rm -f /tmp/arxivdigest_frontend.log
    rm -f /tmp/arxivdigest_api.log
    print_success "Log files cleaned up"
else
    print_status "Keeping log files"
fi

echo
echo "======================================"
echo "  Service Shutdown Complete!"
echo "======================================"
echo

# Show final status
print_status "Final service status:"

# Check arXivDigest processes
if pgrep -f "arxivdigest" > /dev/null; then
    print_warning "Some arXivDigest processes may still be running:"
    ps aux | grep arxivdigest | grep -v grep || true
else
    print_success "All arXivDigest processes stopped"
fi

# Check Elasticsearch
if pgrep -f "elasticsearch" > /dev/null; then
    print_warning "Elasticsearch may still be running"
else
    print_success "Elasticsearch stopped"
fi

# Check MySQL
if brew services list | grep mysql | grep -q "started"; then
    print_status "MySQL is still running (as requested or by choice)"
else
    print_success "MySQL stopped"
fi

echo
print_status "To start all services again, run: ./scripts/start_services.sh"
echo
