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

# Function to stop a system service (cross-platform)
stop_system_service() {
    local service_name=$1
    local display_name=$2
    
    print_status "Stopping $display_name..."
    
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS - use brew or mysql.server
        if command -v brew &> /dev/null && brew services list 2>/dev/null | grep "$service_name" | grep -q "started"; then
            brew services stop "$service_name" 2>/dev/null
            print_success "$display_name stopped"
        elif command -v mysql.server &> /dev/null && [ "$service_name" = "mysql" ]; then
            mysql.server stop 2>/dev/null
            print_success "$display_name stopped"
        else
            print_success "$display_name is not running"
        fi
    else
        # Linux - use systemctl or service command
        if command -v systemctl &> /dev/null && systemctl is-active --quiet "$service_name" 2>/dev/null; then
            sudo systemctl stop "$service_name" 2>/dev/null
            print_success "$display_name stopped"
        elif command -v service &> /dev/null; then
            sudo service "$service_name" stop 2>/dev/null && print_success "$display_name stopped" || print_success "$display_name is not running"
        else
            print_success "$display_name is not running"
        fi
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

# Also try to stop via system service (in case it was started that way)
if [[ "$OSTYPE" == "darwin"* ]]; then
    if command -v brew &> /dev/null && brew services list 2>/dev/null | grep elasticsearch-full | grep -q "started"; then
        brew services stop elasticsearch-full 2>/dev/null
    fi
else
    if command -v systemctl &> /dev/null && systemctl is-active --quiet elasticsearch 2>/dev/null; then
        sudo systemctl stop elasticsearch 2>/dev/null
    elif command -v service &> /dev/null; then
        sudo service elasticsearch stop 2>/dev/null || true
    fi
fi

# 5. Optionally stop MySQL (ask user first)
echo
read -p "Do you want to stop MySQL database? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    if [[ "$OSTYPE" == "darwin"* ]]; then
        stop_system_service "mysql" "MySQL Database"
    else
        # Try mysql first, then mariadb on Linux
        if command -v systemctl &> /dev/null; then
            if systemctl is-active --quiet mysql 2>/dev/null; then
                stop_system_service "mysql" "MySQL Database"
            elif systemctl is-active --quiet mariadb 2>/dev/null; then
                stop_system_service "mariadb" "MariaDB Database"
            else
                print_success "MySQL/MariaDB is not running"
            fi
        else
            # Fallback for systems without systemctl
            sudo service mysql stop 2>/dev/null || sudo service mariadb stop 2>/dev/null || print_success "MySQL/MariaDB is not running"
        fi
    fi
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

# Check arXivDigest processes (exclude SSH and grep)
if pgrep -f "python.*arxivdigest" > /dev/null; then
    print_warning "Some arXivDigest processes may still be running:"
    ps aux | grep "python.*arxivdigest" | grep -v grep || true
else
    print_success "All arXivDigest processes stopped"
fi

# Check Elasticsearch
if pgrep -f "elasticsearch" > /dev/null; then
    print_warning "Elasticsearch may still be running"
else
    print_success "Elasticsearch stopped"
fi

# Check MySQL - use port check for reliability
if command -v nc &> /dev/null; then
    mysql_running=$(nc -z localhost 3306 2>/dev/null && echo "yes" || echo "no")
elif command -v timeout &> /dev/null; then
    mysql_running=$(timeout 1 bash -c "</dev/tcp/localhost/3306" 2>/dev/null && echo "yes" || echo "no")
else
    mysql_running=$(bash -c "</dev/tcp/localhost/3306" 2>/dev/null && echo "yes" || echo "no")
fi

if [ "$mysql_running" = "yes" ]; then
    print_status "MySQL/MariaDB is still running (as requested or by choice)"
else
    print_success "MySQL/MariaDB stopped"
fi

echo
print_status "To start all services again, run: ./scripts/start_services.sh"
echo
