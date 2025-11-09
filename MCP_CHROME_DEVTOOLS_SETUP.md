# Chrome DevTools MCP 配置完成

## 问题诊断和解决过程

### 原始问题
Claude Code 中的 `/mcp` 命令连接 chrome-devtools 失败。

### 发现的问题
1. **Chrome 调试实例未运行** - MCP 需要一个开启远程调试端口的 Chrome 实例
2. **MCP 配置缺失** - `mcp_settings.json` 中没有 chrome-devtools 服务器配置
3. **Node.js 版本不兼容** - 使用的是 v18.20.8，但 chrome-devtools-mcp 需要 v20.19.0+

### 解决方案

#### 1. Chrome 调试服务（自动启动）

**已创建 systemd 服务：**
- 位置: `~/.config/systemd/user/chrome-debug.service`
- 端口: `9222`
- 状态: 开机自启，后台运行
- 日志: `journalctl --user -u chrome-debug.service`

**管理命令：**
```bash
# 查看状态
systemctl --user status chrome-debug.service

# 重启服务
systemctl --user restart chrome-debug.service

# 查看日志
journalctl --user -u chrome-debug.service -f
```

#### 2. Node.js 版本升级

**从 v18.20.8 升级到 v20.19.5**

```bash
# 已设置默认版本
nvm alias default 20

# 验证
node --version  # v20.19.5
```

#### 3. MCP 配置

**配置文件：** `~/.config/claude-code/mcp_settings.json`

**chrome-devtools 配置：**
```json
{
  "servers": {
    "chrome-devtools": {
      "command": "npx",
      "args": ["-y", "chrome-devtools-mcp@latest", "--browserUrl", "http://127.0.0.1:9222"],
      "env": {
        "PATH": "/home/kingofalbert/.nvm/versions/node/v20.19.5/bin:${PATH}"
      }
    }
  }
}
```

**关键参数说明：**
- `chrome-devtools-mcp@latest`: 使用最新版本（当前 v0.10.1）
- `--browserUrl http://127.0.0.1:9222`: 连接到本地 Chrome 调试实例
- `PATH` 环境变量: 确保使用 Node 20.19.5

## 当前状态

✅ **Chrome 调试服务**: 运行中（systemd）
✅ **端口 9222**: 正常响应
✅ **Node.js**: v20.19.5
✅ **MCP 配置**: 已完成

## 使用方法

### 在 Claude Code 中使用

1. **重新加载 Claude Code** - 确保加载新的 MCP 配置
2. **运行 `/mcp` 命令** - 应该能够成功连接到 chrome-devtools
3. **使用 Chrome DevTools 工具** - 可以使用浏览器自动化、性能分析、网络监控等功能

### 可用的 MCP 工具

chrome-devtools-mcp 提供以下能力：

1. **浏览器自动化**
   - 导航到 URL
   - 点击元素
   - 填写表单
   - 执行 JavaScript

2. **调试和检查**
   - 截图
   - 查看控制台日志
   - 分析网络请求
   - 检查 DOM 元素

3. **性能分析**
   - 记录性能追踪
   - 分析加载时间
   - 检查资源使用

## 故障排查

### MCP 连接失败

```bash
# 1. 检查 Chrome 服务
systemctl --user status chrome-debug.service

# 2. 检查端口
curl http://localhost:9222/json/version

# 3. 检查 Node 版本
node --version  # 应该是 v20.19.5

# 4. 测试 MCP 包
source ~/.nvm/nvm.sh && nvm use 20
npx -y chrome-devtools-mcp@latest --help
```

### 重启所有服务

```bash
# 重启 Chrome 调试服务
systemctl --user restart chrome-debug.service

# 重新加载 Claude Code
# （在 Claude Code 中按 Ctrl+R 或重启应用）
```

### 完全重置

```bash
# 1. 停止服务
systemctl --user stop chrome-debug.service

# 2. 清理临时数据
rm -rf /tmp/chrome-debug-profile

# 3. 重启服务
systemctl --user start chrome-debug.service

# 4. 重启 Claude Code
```

## 技术细节

### 为什么需要 Node 20+

chrome-devtools-mcp 使用了 Node.js 20+ 的新特性，不支持旧版本：
```
ERROR: `chrome-devtools-mcp` does not support Node v18.20.8.
Please upgrade to Node 20.19.0 LTS or a newer LTS.
```

### 为什么需要独立的 Chrome 实例

- MCP 通过 Chrome DevTools Protocol (CDP) 连接
- CDP 需要开启远程调试端口（--remote-debugging-port=9222）
- 普通的 Chrome 浏览器实例不会开启此端口
- systemd 服务提供持久的调试实例

### PATH 环境变量

由于 MCP 可能不在交互式 shell 中运行，不会自动加载 nvm，所以需要显式设置 PATH：
```json
"env": {
  "PATH": "/home/kingofalbert/.nvm/versions/node/v20.19.5/bin:${PATH}"
}
```

## 相关文件

- MCP 配置: `~/.config/claude-code/mcp_settings.json`
- systemd 服务: `~/.config/systemd/user/chrome-debug.service`
- 启动脚本: `/home/kingofalbert/projects/CMS/scripts/start-chrome-debug.sh`
- 服务文档: `/home/kingofalbert/projects/CMS/scripts/CHROME_DEBUG_SERVICE_README.md`

## 参考资料

- [Chrome DevTools MCP GitHub](https://github.com/ChromeDevTools/chrome-devtools-mcp)
- [npm 包](https://www.npmjs.com/package/chrome-devtools-mcp)
- [官方博客](https://developer.chrome.com/blog/chrome-devtools-mcp)
- [Chrome DevTools Protocol](https://chromedevtools.github.io/devtools-protocol/)

## 下次重启后

✅ **无需手动操作** - Chrome 调试服务会自动启动
✅ **Node 20 为默认** - 所有新 shell 使用 Node 20
✅ **MCP 配置持久化** - 配置已保存，无需重新配置

现在可以在 Claude Code 中运行 `/mcp` 命令使用 Chrome DevTools 了！
