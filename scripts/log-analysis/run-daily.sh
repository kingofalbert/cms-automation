#!/bin/bash
set -euo pipefail

# Daily Cloud Run Log Analysis Runner
# Designed to be called from crontab or manually.
# Uses claude CLI in non-interactive mode to execute the /log-analysis command.

export PATH="/usr/local/bin:/opt/homebrew/bin:$PATH"

cd /Users/albertking/ES/cms_automation

REPORT_DIR="scripts/log-analysis/reports"
DATE=$(date +%Y-%m-%d)
LOG_FILE="${REPORT_DIR}/${DATE}-run.log"

mkdir -p "$REPORT_DIR"

echo "[$(date)] Starting daily log analysis..." > "$LOG_FILE"

# Verify gcloud auth is valid before proceeding
if ! gcloud auth print-access-token --account=albert.king@epochtimes.nyc &>/dev/null; then
  echo "[$(date)] ERROR: gcloud auth expired or invalid for albert.king@epochtimes.nyc" >> "$LOG_FILE"
  echo "[$(date)] Run: gcloud auth login albert.king@epochtimes.nyc" >> "$LOG_FILE"
  exit 1
fi

# Run the log analysis slash command via claude CLI
claude -p "$(cat .claude/commands/log-analysis.md)" \
  --allowedTools "Bash,Read,Grep,Glob,Write,Agent" \
  >> "$LOG_FILE" 2>&1

echo "[$(date)] Analysis complete. Report: ${REPORT_DIR}/${DATE}.md" >> "$LOG_FILE"

# Cleanup reports older than 30 days
find "$REPORT_DIR" -name "*.md" -mtime +30 -not -name ".gitkeep" -delete 2>/dev/null || true
find "$REPORT_DIR" -name "*-run.log" -mtime +30 -delete 2>/dev/null || true
