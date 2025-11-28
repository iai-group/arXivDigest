#!/bin/bash

# arXivDigest Service Status Script
# This script checks the status of all arXivDigest services

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Function to print colored output
print_header() {
    echo -e "${CYAN}$1${NC}"
}

print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[RUNNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[STOPPED]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Function to check if a service is responding on a port
check_port() {
    local port=$1
    if curl -s "http://localhost:$port" > /dev/null 2>&1; then
        return 0
    else
        return 1
    fi
}

# Function to check if a process is running
check_process() {
    local process_name=$1
    if pgrep -f "$process_name" > /dev/null; then
        return 0
    else
        return 1
    fi
}

# Function to get process count and PIDs
get_process_info() {
    local process_name=$1
    local pids=$(pgrep -f "$process_name" || true)
    if [ -n "$pids" ]; then
        local count=$(echo "$pids" | wc -l | tr -d ' ')
        echo "$count process(es) - PIDs: $pids"
    else
        echo "0 processes"
    fi
}

# Configuration file path
CONFIG_FILE="${ARXIVDIGEST_CONFIG:-/etc/arxivdigest/config.json}"

# Function to read config values using Python (more reliable for JSON parsing)
get_config_value() {
    local key_path=$1
    python3 -c "
import json
with open('$CONFIG_FILE') as f:
    config = json.load(f)
keys = '$key_path'.split('.')
val = config
for k in keys:
    val = val[k]
print(val)
" 2>/dev/null
}

# Function to check database connectivity
check_database() {
    # Read credentials from config file
    local db_user=$(get_config_value "sql_config.user")
    local db_pass=$(get_config_value "sql_config.password")
    local db_host=$(get_config_value "sql_config.host")
    local db_name=$(get_config_value "sql_config.database")
    
    # Fallback to defaults if config reading fails
    db_user="${db_user:-root}"
    db_pass="${db_pass:-root}"
    db_host="${db_host:-localhost}"
    db_name="${db_name:-arxivdigest}"
    
    local result=$(mysql -u "$db_user" -p"$db_pass" -h "$db_host" -e "SELECT COUNT(*) as count FROM ${db_name}.articles;" 2>/dev/null | tail -1)
    if [ $? -eq 0 ] && [ -n "$result" ] && [ "$result" != "count" ]; then
        echo "$result articles in database"
        return 0
    else
        echo "Database connection failed"
        return 1
    fi
}

# Function to check Elasticsearch index
check_elasticsearch_index() {
    local es_host="${ES_HOST:-localhost}"
    local es_port="${ES_PORT:-9200}"
    local result=$(curl -s "${es_host}:${es_port}/_cat/indices/arxiv*?h=docs.count" 2>/dev/null)
    if [ $? -eq 0 ] && [ -n "$result" ]; then
        echo "$result documents indexed"
        return 0
    else
        echo "No arXiv index found"
        return 1
    fi
}

clear
echo "======================================"
echo "  arXivDigest Service Status"
echo "======================================"
echo -e "Checked at: ${CYAN}$(date)${NC}"
echo

# 1. MySQL Database
print_header "🗄️  MySQL Database (Port 3306)"

# Detect OS and check MySQL status accordingly
mysql_running=false
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS - use brew
    if brew services list | grep mysql | grep -q "started"; then
        mysql_running=true
    fi
else
    # Linux - use systemctl
    if systemctl is-active --quiet mysql 2>/dev/null || systemctl is-active --quiet mariadb 2>/dev/null; then
        mysql_running=true
    fi
fi

if $mysql_running; then
    print_success "MySQL service is running"
    db_info=$(check_database)
    if [ $? -eq 0 ]; then
        echo "   └─ Database accessible: $db_info"
    else
        print_warning "   └─ Database not accessible: $db_info"
    fi
else
    print_error "MySQL service is not running"
fi
echo

# 2. Elasticsearch
ES_HOST="${ES_HOST:-localhost}"
ES_PORT="${ES_PORT:-9200}"
print_header "🔍 Elasticsearch (Port ${ES_PORT})"
if check_process "elasticsearch"; then
    es_info=$(get_process_info "elasticsearch")
    print_success "Elasticsearch is running - $es_info"
    
    if check_port "${ES_PORT}"; then
        echo "   └─ HTTP API accessible"
        # Get cluster health
        health=$(curl -s "${ES_HOST}:${ES_PORT}/_cluster/health?pretty" 2>/dev/null | grep '"status"' | cut -d'"' -f4)
        if [ -n "$health" ]; then
            case $health in
                "green") echo -e "   └─ Cluster health: ${GREEN}$health${NC}" ;;
                "yellow") echo -e "   └─ Cluster health: ${YELLOW}$health${NC}" ;;
                "red") echo -e "   └─ Cluster health: ${RED}$health${NC}" ;;
                *) echo "   └─ Cluster health: $health" ;;
            esac
        fi
        
        # Check if articles are indexed
        index_info=$(check_elasticsearch_index)
        echo "   └─ Index status: $index_info"
    else
        print_warning "   └─ HTTP API not accessible"
    fi
else
    print_error "Elasticsearch is not running"
fi
echo

# 3. Frontend Service
FRONTEND_HOST="${FRONTEND_HOST:-localhost}"
FRONTEND_PORT="${FRONTEND_PORT:-8080}"
print_header "🌐 Frontend Service (Port ${FRONTEND_PORT})"
if check_process "arxivdigest.frontend.app"; then
    frontend_info=$(get_process_info "arxivdigest.frontend.app")
    print_success "Frontend is running - $frontend_info"
    
    if check_port "${FRONTEND_PORT}"; then
        echo "   └─ Web interface accessible at http://${FRONTEND_HOST}:${FRONTEND_PORT}"
    else
        print_warning "   └─ Web interface not accessible"
    fi
else
    print_error "Frontend is not running"
fi
echo

# 4. API Service
API_HOST="${API_HOST:-localhost}"
API_PORT="${API_PORT:-5002}"
print_header "🔧 API Service (Port ${API_PORT})"
if check_process "arxivdigest.api.app"; then
    api_info=$(get_process_info "arxivdigest.api.app")
    print_success "API is running - $api_info"
    
    if check_port "${API_PORT}"; then
        echo "   └─ API accessible at http://${API_HOST}:${API_PORT}"
    else
        print_warning "   └─ API not accessible"
    fi
else
    print_error "API is not running"
fi
echo

# 5. Other arXivDigest Processes
print_header "⚙️  Other arXivDigest Processes"
other_processes=$(ps aux | grep -E "python.*arxivdigest" | grep -v "frontend.app" | grep -v "api.app" | grep -v grep || true)
if [ -n "$other_processes" ]; then
    print_warning "Found other arXivDigest processes:"
    echo "$other_processes" | while read line; do
        echo "   └─ $line"
    done
else
    print_status "No other arXivDigest processes running"
fi
echo

# 6. System Resources
print_header "💾 System Resources"
# Memory usage
total_mem=$(ps aux | grep -E "(mysql|elasticsearch|arxivdigest)" | grep -v grep | awk '{sum += $6} END {print sum/1024}' || echo "0")
echo "   └─ Memory usage by services: ${total_mem} MB"

# Disk usage for logs
log_size=$(du -sh /tmp/*arxiv* /tmp/elasticsearch.log 2>/dev/null | awk '{sum += $1} END {print sum}' || echo "0")
if [ "$log_size" != "0" ]; then
    echo "   └─ Log files size: $log_size"
fi

# Port usage
echo "   └─ Port status:"
for port in 3306 ${API_PORT:-5002} ${FRONTEND_PORT:-8080} ${ES_PORT:-9200}; do
    # Use ss on Linux (netstat replacement), fall back to netstat on macOS
    if command -v ss &> /dev/null; then
        port_listening=$(ss -tuln | grep -q ":$port " && echo "yes" || echo "no")
    else
        port_listening=$(netstat -an | grep -q ":$port.*LISTEN" && echo "yes" || echo "no")
    fi
    
    if [ "$port_listening" = "yes" ]; then
        echo -e "      • Port $port: ${GREEN}LISTENING${NC}"
    else
        echo -e "      • Port $port: ${RED}NOT IN USE${NC}"
    fi
done
echo

# 7. Quick Actions
print_header "🚀 Quick Actions"
echo "   • Start all services: ./scripts/start_services.sh"
echo "   • Stop all services:  ./scripts/stop_services.sh"
echo "   • View this status:   ./scripts/check_services.sh"
echo

# 8. Service URLs (if running)
running_services=0
print_header "🌍 Service URLs"
if check_port "${FRONTEND_PORT:-8080}"; then
    echo "   • Frontend: http://${FRONTEND_HOST:-localhost}:${FRONTEND_PORT:-8080}"
    running_services=$((running_services + 1))
fi
if check_port "${API_PORT:-5002}"; then
    echo "   • API: http://${API_HOST:-localhost}:${API_PORT:-5002}"
    running_services=$((running_services + 1))
fi
if check_port "${ES_PORT:-9200}"; then
    echo "   • Elasticsearch: http://${ES_HOST:-localhost}:${ES_PORT:-9200}"
    running_services=$((running_services + 1))
fi

if [ $running_services -eq 0 ]; then
    print_error "No web services are accessible"
fi

echo
echo "======================================"
if [ $running_services -gt 0 ]; then
    print_success "System Status: $running_services/3 web services running"
else
    print_error "System Status: All services appear to be down"
fi
echo "======================================"
