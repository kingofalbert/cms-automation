# Chrome Debug Service 使用说明

Chrome Debug Service 是一个系统级服务，用于为 MCP (Model Context Protocol) chrome-devtools 提供调试端点。

## 服务状态

### ✅ 已配置
- 服务文件位置: `~/.config/systemd/user/chrome-debug.service`
- 开机自启: **已启用**
- 端口: `9222`
- 用户数据目录: `/tmp/chrome-debug-profile`

## 管理命令

### 查看服务状态
```bash
systemctl --user status chrome-debug.service
```

### 启动服务
```bash
systemctl --user start chrome-debug.service
```

### 停止服务
```bash
systemctl --user stop chrome-debug.service
```

### 重启服务
```bash
systemctl --user restart chrome-debug.service
```

### 查看日志
```bash
# 查看最近的日志
journalctl --user -u chrome-debug.service -n 50

# 实时跟踪日志
journalctl --user -u chrome-debug.service -f
```

### 禁用开机自启
```bash
systemctl --user disable chrome-debug.service
```

### 重新启用开机自启
```bash
systemctl --user enable chrome-debug.service
```

## 验证服务

### 检查端口是否开启
```bash
curl http://localhost:9222/json/version
```

### 检查 WebSocket 连接
```bash
netstat -tuln | grep 9222
```

## 系统行为

- ✅ **开机自动启动**: 系统启动时自动运行
- ✅ **登录后运行**: 即使未登录图形界面也会运行（已启用 lingering）
- ✅ **自动恢复**: 如果服务崩溃，5 秒后自动重启
- ✅ **后台运行**: 不影响系统性能

## 与 MCP 集成

现在可以在 Claude Desktop 中使用 MCP chrome-devtools：

1. 运行 `/mcp` 命令
2. MCP 会自动连接到 `ws://localhost:9222`
3. 开始使用 Chrome DevTools 功能

## 问题排查

### 服务无法启动
```bash
# 查看详细错误信息
systemctl --user status chrome-debug.service
journalctl --user -xeu chrome-debug.service
```

### 端口被占用
```bash
# 查找占用端口的进程
lsof -i:9222

# 停止所有 Chrome 调试实例
pkill -f "remote-debugging-port=9222"
```

### 完全重置服务
```bash
# 停止并禁用服务
systemctl --user stop chrome-debug.service
systemctl --user disable chrome-debug.service

# 清理用户数据
rm -rf /tmp/chrome-debug-profile

# 重新启动
systemctl --user enable chrome-debug.service
systemctl --user start chrome-debug.service
```

## 卸载

如果不再需要此服务：

```bash
# 停止并禁用服务
systemctl --user stop chrome-debug.service
systemctl --user disable chrome-debug.service

# 删除服务文件
rm ~/.config/systemd/user/chrome-debug.service

# 重新加载 systemd
systemctl --user daemon-reload

# 清理用户数据
rm -rf /tmp/chrome-debug-profile
```

## 注意事项

- 服务使用的 Chrome 实例与你的正常 Chrome 浏览器完全独立
- 用户数据保存在临时目录 `/tmp/chrome-debug-profile`
- 每次服务启动时会清理 Singleton 锁文件，防止冲突
- 服务输出记录在系统日志中（使用 journalctl 查看）
