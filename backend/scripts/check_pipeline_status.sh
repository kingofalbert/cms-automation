#!/bin/bash
#
# 檢查 Pipeline 執行狀態
#

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_DIR"

echo "============================================================"
echo "大紀元健康文章 Pipeline 狀態"
echo "============================================================"
echo ""

# 檢查進程是否在運行
PID=$(pgrep -f "full_health_articles_pipeline.py" 2>/dev/null)
if [ -n "$PID" ]; then
    echo "✅ Pipeline 運行中 (PID: $PID)"

    # 顯示運行時間
    ps -o etime= -p "$PID" 2>/dev/null | xargs -I {} echo "⏱️  運行時間: {}"
    echo ""
else
    echo "❌ Pipeline 未運行"
    echo ""
fi

# 顯示資料庫狀態
echo "📊 資料庫狀態:"
source venv/bin/activate 2>/dev/null
python -c "
from supabase import create_client
import os
from dotenv import load_dotenv

load_dotenv()

url = os.getenv('SUPABASE_URL')
key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')

client = create_client(url, key)

statuses = ['scraped', 'parsed', 'ready']
total = 0
for status in statuses:
    result = client.table('health_articles').select('count', count='exact').eq('status', status).execute()
    count = result.count or 0
    total += count
    emoji = {'scraped': '📥', 'parsed': '🔄', 'ready': '✅'}[status]
    print(f'   {emoji} {status:10s}: {count:5d} 篇')
print(f'   ────────────────────')
print(f'   📚 總計:       {total:5d} 篇')
" 2>/dev/null

echo ""

# 顯示最新日誌
LATEST_LOG=$(ls -t logs/pipeline_*.log 2>/dev/null | head -1)
if [ -n "$LATEST_LOG" ]; then
    echo "📜 最新日誌 ($LATEST_LOG):"
    echo "   (最後 10 行)"
    echo "   ────────────────────────────────────────"
    tail -10 "$LATEST_LOG" | sed 's/^/   /'
fi

echo ""
echo "============================================================"
