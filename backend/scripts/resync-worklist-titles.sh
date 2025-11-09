#!/bin/bash
set -e

echo "🔄 重新同步Worklist标题"
echo "====================================="
echo ""

BACKEND_URL="${1:-https://cms-automation-backend-baau2zqeqq-ue.a.run.app}"

echo "后端URL: $BACKEND_URL"
echo ""

# 触发Google Drive同步
echo "📥 触发Google Drive同步..."
RESPONSE=$(curl -s -X POST "$BACKEND_URL/v1/import/sync-google-drive" -H "Content-Type: application/json")

echo "同步结果:"
echo "$RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$RESPONSE"
echo ""

# 等待3秒
sleep 3

# 检查worklist，显示更新后的标题
echo "📋 检查更新后的标题..."
curl -s "$BACKEND_URL/v1/worklist" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    print('\n更新后的Worklist标题:')
    print('='*80)
    for item in data.get('items', []):
        print(f\"ID {item['id']:>2}: {item['title']}\")
        # 同时显示metadata中的名字作为对比
        metadata_name = item['metadata'].get('name', 'N/A')
        if metadata_name != item['title']:
            print(f\"         (元数据名字: {metadata_name})\")
        print()
except json.JSONDecodeError as e:
    print(f'解析JSON失败: {e}', file=sys.stderr)
    sys.exit(1)
"

echo ""
echo "✅ 同步完成！"
