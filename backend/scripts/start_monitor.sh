#!/bin/bash
#
# 啟動 Pipeline 監控 API
#

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_DIR"

# 檢查是否已經在運行
PID=$(pgrep -f "pipeline_monitor_api.py" 2>/dev/null)
if [ -n "$PID" ]; then
    echo "監控 API 已在運行 (PID: $PID)"
    echo "訪問地址: http://localhost:5050"
    exit 0
fi

echo "啟動 Pipeline 監控 API..."

# 啟動虛擬環境並執行
source venv/bin/activate
python scripts/pipeline_monitor_api.py
