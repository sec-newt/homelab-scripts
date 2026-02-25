#!/bin/bash
# Home Network Status Check
# Simple monitoring script for non-technical users — checks local services,
# server connectivity, disk space, and container health over SSH.
#
# Usage: bash home-network-status.sh

# ------------------------------------------------------------------------------
# Configuration — edit these for your setup
# ------------------------------------------------------------------------------
MAIN_SERVER="zeus"                          # SSH hostname of your server
DASHBOARD_URL="http://home.local"
MEDIA_URL="http://jellyfin.local"
CLOUD_URL="http://nextcloud.local"
PASSWORD_MANAGER_URL=""                     # e.g. http://192.168.1.x:PORT

DOCS_EMERGENCY=""                           # path to emergency guide (optional)
DOCS_REFERENCE=""                           # path to quick-reference guide (optional)
# ------------------------------------------------------------------------------

echo "Home Network Status Check"
echo "===================================="
echo ""

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to test service and show status
test_service() {
    local name="$1"
    local url="$2"
    if curl -s "$url" > /dev/null 2>&1; then
        echo -e "  ${GREEN}[OK]${NC}   $name"
    else
        echo -e "  ${RED}[DOWN]${NC} $name"
    fi
}

# Test main services
echo "Network Services:"
test_service "Dashboard" "$DASHBOARD_URL"
test_service "Jellyfin (media)" "$MEDIA_URL"
test_service "Nextcloud (files)" "$CLOUD_URL"
[[ -n "$PASSWORD_MANAGER_URL" ]] && test_service "Password Manager" "$PASSWORD_MANAGER_URL"

echo ""

# Test main server connectivity
echo "Main Server ($MAIN_SERVER):"
if ping -c 1 "$MAIN_SERVER" > /dev/null 2>&1 || ping -c 1 "${MAIN_SERVER}.local" > /dev/null 2>&1; then
    echo -e "  ${GREEN}[OK]${NC}   $MAIN_SERVER responding"
else
    echo -e "  ${RED}[DOWN]${NC} $MAIN_SERVER unreachable"
fi

echo ""

# Test internet connectivity
echo "Internet:"
if ping -c 1 one.one.one.one > /dev/null 2>&1; then
    echo -e "  ${GREEN}[OK]${NC}   Internet connection OK"
else
    echo -e "  ${RED}[DOWN]${NC} Internet connection DOWN"
fi

echo ""

# Check server disk space (if accessible via SSH)
echo "Storage (via SSH to $MAIN_SERVER):"
if ssh -o ConnectTimeout=5 "$MAIN_SERVER" "df -h | grep library" > /tmp/disk_usage 2>/dev/null; then
    while read -r line; do
        usage=$(echo "$line" | awk '{print $5}' | sed 's/%//')
        mount=$(echo "$line" | awk '{print $6}')
        if [ "$usage" -gt 90 ]; then
            echo -e "  ${RED}[CRIT]${NC} $mount at ${usage}% — contact admin"
        elif [ "$usage" -gt 80 ]; then
            echo -e "  ${YELLOW}[WARN]${NC} $mount at ${usage}% — getting full"
        else
            echo -e "  ${GREEN}[OK]${NC}   $mount at ${usage}%"
        fi
    done < /tmp/disk_usage
    rm -f /tmp/disk_usage
else
    echo -e "  ${RED}[SKIP]${NC} Cannot check — $MAIN_SERVER unreachable"
fi

echo ""

# Check container status
echo "Containers (via SSH to $MAIN_SERVER):"
if ssh -o ConnectTimeout=5 "$MAIN_SERVER" "docker ps --format 'table {{.Names}}\t{{.Status}}' 2>/dev/null | tail -n +2" > /tmp/containers 2>/dev/null; then
    healthy_count=0
    unhealthy_count=0

    while read -r line; do
        if echo "$line" | grep -q "Up"; then
            healthy_count=$((healthy_count + 1))
        else
            unhealthy_count=$((unhealthy_count + 1))
            echo -e "  ${YELLOW}[WARN]${NC} $(echo "$line" | awk '{print $1}') may have issues"
        fi
    done < /tmp/containers

    if [ "$unhealthy_count" -eq 0 ]; then
        echo -e "  ${GREEN}[OK]${NC}   All $healthy_count containers running"
    else
        echo -e "  ${YELLOW}[WARN]${NC} $healthy_count OK, $unhealthy_count need attention"
    fi
    rm -f /tmp/containers
else
    echo -e "  ${RED}[SKIP]${NC} Cannot check — $MAIN_SERVER unreachable"
fi

echo ""

# Summary
echo "Summary:"
failed_services=0

curl -s "$DASHBOARD_URL" > /dev/null 2>&1   || failed_services=$((failed_services + 1))
curl -s "$MEDIA_URL" > /dev/null 2>&1       || failed_services=$((failed_services + 1))
curl -s "$CLOUD_URL" > /dev/null 2>&1       || failed_services=$((failed_services + 1))
ping -c 1 "$MAIN_SERVER" > /dev/null 2>&1  || failed_services=$((failed_services + 1))

if [ "$failed_services" -eq 0 ]; then
    echo -e "${GREEN}  All services OK. No action needed.${NC}"
elif [ "$failed_services" -eq 1 ]; then
    echo -e "${YELLOW}  One service may need attention. Try restarting it.${NC}"
else
    echo -e "${RED}  Multiple services down. Admin attention required.${NC}"
fi

echo ""
echo "Next steps:"
if [ "$failed_services" -gt 0 ]; then
    [[ -n "$DOCS_EMERGENCY" ]] && echo "  - Emergency guide: $DOCS_EMERGENCY"
    echo "  - Try: ssh $MAIN_SERVER && docker compose -f services.yml restart"
else
    echo "  - No immediate action needed"
    echo "  - Run this check weekly for maintenance"
fi

[[ -n "$DOCS_REFERENCE" ]] && echo "" && echo "More help: $DOCS_REFERENCE"
