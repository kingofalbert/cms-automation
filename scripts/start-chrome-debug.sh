#!/bin/bash
# 启动带有远程调试的 Chrome 实例
# 用于 MCP chrome-devtools 连接

PORT=9222
USER_DATA_DIR="/tmp/chrome-debug-profile"

# 检查是否已经有实例在运行
if lsof -i:$PORT > /dev/null 2>&1; then
    echo "Chrome 调试端口 $PORT 已经在使用中"
    echo "如果需要重启，请先运行: pkill -f 'remote-debugging-port=$PORT'"
    exit 1
fi

# 创建用户数据目录
mkdir -p "$USER_DATA_DIR"

echo "启动 Chrome 调试实例（端口 $PORT）..."
echo "按 Ctrl+C 停止"

# 启动 Chrome
google-chrome \
    --remote-debugging-port=$PORT \
    --user-data-dir="$USER_DATA_DIR" \
    --no-first-run \
    --no-default-browser-check \
    > /tmp/chrome-debug.log 2>&1 &

CHROME_PID=$!

echo "Chrome PID: $CHROME_PID"
echo "调试端口: http://localhost:$PORT"
echo "日志文件: /tmp/chrome-debug.log"
echo ""
echo "现在可以在 Claude Desktop 中使用 /mcp 重新连接"
echo ""
echo "要停止 Chrome，运行: kill $CHROME_PID"

# 保存 PID 以便后续停止
echo $CHROME_PID > /tmp/chrome-debug.pid
