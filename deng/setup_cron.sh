#!/bin/bash
# Setup cron jobs for Indieflix theater scrapers
# Run each scraper daily at different times to avoid overwhelming servers

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PYTHON_PATH=$(which python3)

# Create data directory if it doesn't exist
mkdir -p "$SCRIPT_DIR/data"

# Display current crontab
echo "Current crontab:"
crontab -l 2>/dev/null || echo "No crontab found"
echo ""

# Proposed cron jobs (commented out - user can uncomment to activate)
cat << 'EOF'
# Indieflix Theater Scrapers - Run daily at 2 AM
# Uncomment the lines below and run: crontab -e
# Then paste these lines:

# IFC Center - Run at 2:00 AM daily
0 2 * * * cd SCRIPT_DIR && python3 ingestion/ifc_center.py >> logs/ifc_center.log 2>&1

# Metrograph - Run at 2:15 AM daily
15 2 * * * cd SCRIPT_DIR && python3 ingestion/metrograph.py >> logs/metrograph.log 2>&1

# Syndicated BK - Run at 2:30 AM daily
30 2 * * * cd SCRIPT_DIR && python3 ingestion/syndicatedbk.py >> logs/syndicatedbk.log 2>&1

# Alternative: Run all at once (simpler but less staggered)
# 0 2 * * * cd SCRIPT_DIR && for script in ingestion/*.py; do python3 "$script"; done >> logs/all_scrapers.log 2>&1

EOF

echo ""
echo "Replace SCRIPT_DIR with: $SCRIPT_DIR"
echo ""
echo "To set up cron jobs:"
echo "1. Create logs directory: mkdir -p $SCRIPT_DIR/logs"
echo "2. Edit crontab: crontab -e"
echo "3. Add the cron job lines above (replacing SCRIPT_DIR)"
echo "4. Save and exit"
echo ""
echo "To test scrapers manually:"
echo "  cd $SCRIPT_DIR"
echo "  python3 ingestion/ifc_center.py"
echo "  python3 ingestion/metrograph.py"
echo "  python3 ingestion/syndicatedbk.py"
