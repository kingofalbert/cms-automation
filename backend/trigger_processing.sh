#!/bin/bash

# 触发 Worklist 文件处理
# 用途：手动触发卡住文件的处理

set -e

API_URL="https://cms-automation-backend-baau2zqeqq-ue.a.run.app"
ITEMS="6 13"

echo "🚀 触发 Worklist 文件处理"
echo "API: $API_URL"
echo "文件 ID: $ITEMS"
echo ""

for ITEM_ID in $ITEMS; do
    echo "───────────────────────────────────────────"
    echo "处理文件 ID: $ITEM_ID"
    echo "───────────────────────────────────────────"

    echo ""
    echo "📋 步骤 1: 触发重新解析 (reparse)..."

    RESPONSE=$(curl -s -X POST "$API_URL/v1/worklist/$ITEM_ID/reparse" \
        -H "Content-Type: application/json" \
        -w "\nHTTP_STATUS:%{http_code}")

    HTTP_STATUS=$(echo "$RESPONSE" | grep "HTTP_STATUS" | cut -d: -f2)
    BODY=$(echo "$RESPONSE" | sed '/HTTP_STATUS/d')

    echo "响应状态: $HTTP_STATUS"
    echo "响应内容: $BODY"

    if [ "$HTTP_STATUS" == "200" ] || [ "$HTTP_STATUS" == "201" ]; then
        echo "✅ 重新解析触发成功"
    else
        echo "⚠️  重新解析触发失败或返回错误"
    fi

    echo ""
    echo "等待 5 秒..."
    sleep 5

    echo ""
    echo "📋 步骤 2: 触发校对处理 (trigger-proofreading)..."

    RESPONSE=$(curl -s -X POST "$API_URL/v1/worklist/$ITEM_ID/trigger-proofreading" \
        -H "Content-Type: application/json" \
        -w "\nHTTP_STATUS:%{http_code}")

    HTTP_STATUS=$(echo "$RESPONSE" | grep "HTTP_STATUS" | cut -d: -f2)
    BODY=$(echo "$RESPONSE" | sed '/HTTP_STATUS/d')

    echo "响应状态: $HTTP_STATUS"
    echo "响应内容: $BODY"

    if [ "$HTTP_STATUS" == "200" ] || [ "$HTTP_STATUS" == "201" ]; then
        echo "✅ 校对处理触发成功"
    else
        echo "⚠️  校对处理触发失败或返回错误"
    fi

    echo ""
    echo "───────────────────────────────────────────"
    echo ""

    sleep 3
done

echo ""
echo "🎉 所有文件处理已触发！"
echo ""
echo "下一步："
echo "1. 等待 2-3 分钟让系统处理"
echo "2. 在 Supabase 中检查文件状态"
echo "3. 查看文件是否从 pending → parsing → parsing_review"
echo ""
echo "验证查询:"
echo "SELECT id, title, status, updated_at FROM worklist_items WHERE id IN (6, 13);"
