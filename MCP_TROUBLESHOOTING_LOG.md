# Chrome DevTools MCP 故障排查日志

## 问题描述
在 Claude Code 中运行 `/mcp` 命令时，chrome-devtools 连接失败：
```
Failed to reconnect to chrome-devtools.
```

## 排查过程

### 第一轮诊断（已解决但不完整）

**发现的问题：**
1. ✅ Chrome 调试实例未运行 → 创建了 systemd 服务
2. ✅ MCP 配置缺失 → 添加了 chrome-devtools 配置
3. ✅ Node.js 版本不兼容 (v18 → v20) → 设置了默认版本

**配置尝试（失败）：**
```json
{
  "command": "npx",
  "args": ["-y", "chrome-devtools-mcp@latest", "--browserUrl", "http://127.0.0.1:9222"],
  "env": {
    "PATH": "/home/kingofalbert/.nvm/versions/node/v20.19.5/bin:${PATH}"
  }
}
```

**问题：** `${PATH}` 变量在 JSON 中不会被展开。

### 第二轮诊断（已解决但不完整）

**配置尝试（失败）：**
```json
{
  "command": "/home/kingofalbert/.nvm/versions/node/v20.19.5/bin/npx",
  "args": ["-y", "chrome-devtools-mcp@latest", "--browserUrl", "http://127.0.0.1:9222"],
  "env": {}
}
```

**测试结果：**
```bash
$ /home/kingofalbert/.nvm/versions/node/v20.19.5/bin/npx -y chrome-devtools-mcp@latest --help
ERROR: `chrome-devtools-mcp` does not support Node v18.20.8.
```

**问题根源：** 即使 npx 本身使用 Node 20 的路径，它内部调用的 `node` 仍然是系统默认的 v18。

### 第三轮诊断（最终解决）

**关键发现：**
- npx 是一个包装器，会从 PATH 中查找 node
- 直接指定 npx 的完整路径不足以解决问题
- 需要在运行时设置 PATH 环境变量

**最终解决方案：**

**1. 创建包装脚本**
位置: `~/.config/claude-code/chrome-mcp-wrapper.sh`

```bash
#!/bin/bash
# Chrome DevTools MCP wrapper script
# 确保使用 Node 20 运行 chrome-devtools-mcp

export PATH="/home/kingofalbert/.nvm/versions/node/v20.19.5/bin:$PATH"
exec npx -y chrome-devtools-mcp@latest "$@"
```

**2. 更新 MCP 配置**
```json
{
  "chrome-devtools": {
    "command": "/home/kingofalbert/.config/claude-code/chrome-mcp-wrapper.sh",
    "args": ["--browserUrl", "http://127.0.0.1:9222"],
    "env": {}
  }
}
```

## 验证测试

所有组件测试通过：

```bash
$ /tmp/test-mcp-full.sh

=== Chrome DevTools MCP 完整测试 ===

1. 检查 Chrome 调试服务
   ✅ Chrome 调试服务正在运行

2. 检查端口 9222
   ✅ 端口 9222 正常响应

3. 检查包装脚本
   ✅ 包装脚本存在且可执行

4. 测试包装脚本运行
   ✅ 包装脚本可以正常运行

5. 检查 MCP 配置
   ✅ MCP 配置文件存在
   ✅ chrome-devtools 配置已添加
```

## 解决方案摘要

### 创建的文件

1. **systemd 服务**
   - 位置: `~/.config/systemd/user/chrome-debug.service`
   - 功能: 开机自启动 Chrome 调试实例
   - 端口: 9222

2. **包装脚本**
   - 位置: `~/.config/claude-code/chrome-mcp-wrapper.sh`
   - 功能: 确保使用 Node 20 运行 chrome-devtools-mcp

3. **MCP 配置**
   - 位置: `~/.config/claude-code/mcp_settings.json`
   - 功能: 配置 chrome-devtools MCP 服务器

### 使用说明

**需要重启 Claude Code** 以加载新的 MCP 配置。

重启后运行：
```
/mcp
```

应该能够成功连接到 chrome-devtools。

## 技术要点

### 为什么需要包装脚本？

1. **MCP 配置的限制**
   - JSON 配置不支持 shell 变量展开（如 `${PATH}`）
   - env 对象只能设置简单的键值对

2. **npx 的工作原理**
   - npx 本身只是一个启动器
   - 它会从 PATH 中查找 node 可执行文件
   - 仅指定 npx 的完整路径不够，还需要确保正确的 node 在 PATH 中

3. **包装脚本的优势**
   - 完全控制执行环境
   - 可以设置任意环境变量
   - 易于调试和测试
   - 未来版本升级只需修改脚本

### Node.js 版本要求

chrome-devtools-mcp 的版本要求：
```
Node.js v20.19.0 LTS 或更新版本
```

错误提示：
```
ERROR: `chrome-devtools-mcp` does not support Node v18.20.8.
Please upgrade to Node 20.19.0 LTS or a newer LTS.
```

## 相关文件

- **问题诊断**: `MCP_CHROME_DEVTOOLS_SETUP.md`
- **服务管理**: `scripts/CHROME_DEBUG_SERVICE_README.md`
- **此文档**: `MCP_TROUBLESHOOTING_LOG.md`

## 故障排查清单

如果 MCP 仍然连接失败，按以下顺序检查：

1. **重启 Claude Code**
   ```
   确保加载最新的 MCP 配置
   ```

2. **检查 Chrome 服务**
   ```bash
   systemctl --user status chrome-debug.service
   ```

3. **检查端口**
   ```bash
   curl http://localhost:9222/json/version
   ```

4. **测试包装脚本**
   ```bash
   /home/kingofalbert/.config/claude-code/chrome-mcp-wrapper.sh --help
   ```

5. **验证 Node 版本**
   ```bash
   export PATH="/home/kingofalbert/.nvm/versions/node/v20.19.5/bin:$PATH"
   node --version  # 应该是 v20.19.5
   ```

6. **运行完整测试**
   ```bash
   /tmp/test-mcp-full.sh
   ```

## 经验教训

1. **环境变量展开** - JSON 配置文件不支持 shell 变量语法
2. **npx 依赖 PATH** - 指定 npx 的完整路径不足以控制它使用的 node 版本
3. **包装脚本最可靠** - 对于复杂的环境配置，包装脚本是最可控的方案
4. **需要重启应用** - MCP 配置更改需要重启 Claude Code 才能生效

## 下次类似问题的快速解决方案

对于任何需要特定 Node 版本的 MCP 服务器：

1. 创建包装脚本 `~/.config/claude-code/<mcp-name>-wrapper.sh`:
   ```bash
   #!/bin/bash
   export PATH="/path/to/specific/node/bin:$PATH"
   exec npx -y <package-name> "$@"
   ```

2. 在 MCP 配置中使用包装脚本：
   ```json
   {
     "command": "/home/user/.config/claude-code/<mcp-name>-wrapper.sh",
     "args": ["..."],
     "env": {}
   }
   ```

3. 重启 Claude Code

这个模式可以应用于任何需要特定环境的 MCP 服务器。
