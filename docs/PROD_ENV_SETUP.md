# 生产环境配置指南

**创建日期**: 2025-10-27
**状态**: ✅ 已验证

---

## 🔒 安全配置概述

生产环境 WordPress 的登录信息已安全存储在 `.env` 文件中，该文件：
- ✅ 已加入 `.gitignore`，不会被提交到版本控制
- ✅ 权限设置为 `600`（仅所有者可读写）
- ✅ 包含敏感凭证，请妥善保管

---

## 📋 配置验证结果

### 测试时间
- 2025-10-27

### 测试结果
- ✅ **HTTP Basic Auth 验证**: 成功
- ✅ **WordPress 登录**: 成功
- ✅ **后台访问**: 完全可用
- ✅ **关键功能**: 全部可访问
- ✅ **当前用户**: 紐約報社-Ping Xie

### 生产环境信息

**WordPress URL**: `https://admin.epochtimes.com`

**认证层级**:
1. **第一层**: HTTP Basic Authentication
   - 用途：服务器级别访问控制
   - 凭证：存储在 `PROD_FIRST_LAYER_*` 变量中

2. **第二层**: WordPress 应用登录
   - 用途：WordPress 用户认证
   - 凭证：存储在 `PROD_USERNAME` 和 `PROD_PASSWORD` 中

### 验证截图

测试过程生成的截图保存在 `/tmp/` 目录：
- `prod_after_basic_auth.png` - Basic Auth 通过后的页面
- `prod_wp_login_form.png` - WordPress 登录表单
- `prod_dashboard.png` - 后台仪表板
- `prod_posts_submenu.png` - 文章菜单

---

## 🔐 环境变量说明

### .env 文件结构

```bash
# 生产环境 WordPress
PROD_WORDPRESS_URL=https://admin.epochtimes.com
PROD_LOGIN_URL=https://admin.epochtimes.com/wp-login.php

# 第一层认证（HTTP Basic Auth）
PROD_FIRST_LAYER_USERNAME=djy
PROD_FIRST_LAYER_PASSWORD=djy2013

# 个人账号（WordPress）
PROD_USERNAME=ping.xie
PROD_PASSWORD=kfS*qxdQqm@zic6lXvnR(ih!
```

### 使用方法

在 Python 代码中：

```python
from dotenv import load_dotenv
import os

# 加载环境变量
load_dotenv()

# 读取生产环境配置
prod_url = os.getenv("PROD_WORDPRESS_URL")
prod_username = os.getenv("PROD_USERNAME")
prod_password = os.getenv("PROD_PASSWORD")

# 读取 HTTP Basic Auth 凭证
http_username = os.getenv("PROD_FIRST_LAYER_USERNAME")
http_password = os.getenv("PROD_FIRST_LAYER_PASSWORD")
```

---

## 🚀 使用生产环境

### Playwright 配置示例

```python
from playwright.async_api import async_playwright

async def init_prod_browser():
    """初始化生产环境浏览器"""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)

        # 创建带 HTTP Basic Auth 的上下文
        context = await browser.new_context(
            http_credentials={
                "username": os.getenv("PROD_FIRST_LAYER_USERNAME"),
                "password": os.getenv("PROD_FIRST_LAYER_PASSWORD")
            }
        )

        page = await context.new_page()

        # 访问 WordPress 登录页面
        await page.goto(os.getenv("PROD_LOGIN_URL"))

        # WordPress 登录
        await page.fill("#user_login", os.getenv("PROD_USERNAME"))
        await page.fill("#user_pass", os.getenv("PROD_PASSWORD"))
        await page.click("#wp-submit")

        return browser, context, page
```

---

## ⚠️ 安全注意事项

### 必须遵守

1. **切勿提交 .env 文件**
   - `.env` 已在 `.gitignore` 中
   - 提交前务必检查：`git status`

2. **定期更换密码**
   - 建议每 3-6 个月更换一次
   - 更换后更新 `.env` 文件

3. **限制文件权限**
   - `.env` 文件权限应为 `600` 或 `400`
   - 检查：`ls -l .env`

4. **备份凭证**
   - 将 `.env` 安全备份到密码管理器
   - 不要通过邮件或聊天工具传输

5. **测试时不创建内容**
   - 使用 `prod_env_test_v2.py` 仅验证配置
   - 实际发布前先在测试环境验证

### 生产环境使用原则

```
✅ DO（推荐）:
- 使用环境变量管理凭证
- 先在测试环境验证
- 记录所有生产操作
- 使用审计日志
- 定期备份

❌ DON'T（禁止）:
- 硬编码凭证到代码
- 直接在生产环境测试
- 跳过错误处理
- 忽略日志记录
- 未经测试就部署
```

---

## 🧪 测试脚本使用

### 验证配置

```bash
# 激活虚拟环境
source .venv/bin/activate

# 运行生产环境配置测试（只读，不创建内容）
python tests/prod_env_test_v2.py
```

### 测试功能

- ✅ 验证 HTTP Basic Auth
- ✅ 验证 WordPress 登录
- ✅ 检查后台可访问性
- ✅ 检查关键功能入口
- ✅ 生成验证截图

### 测试保证

- ⚠️ **只读测试**: 不会创建、修改或删除任何内容
- ⚠️ **安全验证**: 仅验证登录和界面访问
- ⚠️ **快速退出**: 测试完成后自动关闭

---

## 📊 配置对比

### 测试环境 vs 生产环境

| 项目 | 测试环境 | 生产环境 |
|------|---------|---------|
| URL | http://localhost:8001 | https://admin.epochtimes.com |
| HTTP Auth | ❌ 无 | ✅ 有（djy/djy2013） |
| WP 账号 | admin | ping.xie |
| WP 密码 | password | kfS*qxdQqm@zic6lXvnR(ih! |
| 用途 | 开发测试 | 实际发布 |
| 安全级别 | 低 | 高（双层认证） |

---

## 🔧 故障排查

### 问题1: 无法访问生产环境

**症状**: `ERR_INVALID_AUTH_CREDENTIALS`

**解决方案**:
1. 检查 HTTP Basic Auth 凭证是否正确
2. 确认 `.env` 文件已正确加载
3. 验证网络连接

```bash
# 测试网络连接
curl -I https://admin.epochtimes.com

# 测试 Basic Auth
curl -u "djy:djy2013" https://admin.epochtimes.com/wp-login.php
```

### 问题2: WordPress 登录失败

**症状**: 停留在 wp-login.php 页面

**解决方案**:
1. 确认 WordPress 用户名和密码正确
2. 检查是否需要额外的验证（2FA）
3. 查看错误消息

### 问题3: 找不到元素

**症状**: 选择器失效

**解决方案**:
1. 检查 WordPress 版本是否更新
2. 使用浏览器开发工具检查元素
3. 更新 `config/selectors.yaml`

---

## 📝 变更日志

### 2025-10-27
- ✅ 初始配置
- ✅ 添加双层认证支持
- ✅ 验证配置成功
- ✅ 生成测试脚本

---

## 📞 支持

如有问题，请：
1. 查看本文档的故障排查部分
2. 检查测试截图（`/tmp/prod_*.png`）
3. 查看详细日志

**重要提醒**:
- 🔐 请勿在公共渠道讨论生产环境凭证
- 🔐 定期审查访问日志
- 🔐 保持软件版本更新
