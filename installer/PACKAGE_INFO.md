# CMS自动化系统 - Windows一键安装包说明

## 📦 安装包信息

**版本:** 1.0.0
**生成日期:** 2025-10-26
**包大小:** 448KB（代码+配置，不含Docker镜像）
**平台:** Windows 10/11

---

## 🎯 回答你的核心问题

### ❓ 可以做成安装包吗？
**✅ 可以！已完成！**

### ❓ 必须在WSL里运行吗？
**❌ 不必！可以直接在Windows运行！**

只需要：
1. 安装 Docker Desktop for Windows
2. 解压安装包
3. 双击 install.bat
4. 双击 start.bat

**不需要 WSL！不需要 Claude Code！**

---

## 📁 安装包结构

```
cms-automation-installer-v1.0.0/
│
├── 📝 管理脚本（一键操作）
│   ├── install.bat          # 初始化配置
│   ├── start.bat           # 启动系统
│   ├── stop.bat            # 停止系统
│   ├── restart.bat         # 重启系统
│   ├── status.bat          # 查看状态
│   └── logs.bat            # 查看日志
│
├── 📚 文档
│   ├── README.md           # 完整使用手册（中文）
│   ├── QUICKSTART.txt      # 快速开始指南
│   └── 部署检查清单.txt    # 逐步检查清单
│
├── ⚙️ 配置文件
│   ├── .env.example        # 环境变量模板
│   └── docker-compose.yml  # Docker服务配置
│
├── 💻 后端代码
│   └── backend/
│       ├── src/            # Python源代码
│       ├── migrations/     # 数据库迁移
│       ├── tools/          # 工具脚本
│       │   └── extract_wordpress_selectors.js
│       ├── docs/           # 技术文档
│       ├── credentials/    # 凭证文件目录
│       ├── config/         # 配置文件目录
│       ├── pyproject.toml  # Python依赖
│       └── Dockerfile      # Docker镜像配置
│
└── 🎨 前端代码
    └── frontend/
        ├── src/            # React源代码
        ├── package.json    # npm依赖
        └── Dockerfile.dev  # Docker镜像配置
```

---

## 🚀 核心特性

### 1. 一键安装
- ✅ 双击 install.bat 自动配置
- ✅ 交互式配置向导
- ✅ 自动检测环境
- ✅ 自动生成配置文件

### 2. 一键启动
- ✅ 双击 start.bat 自动启动
- ✅ 自动拉取Docker镜像
- ✅ 自动初始化数据库
- ✅ 自动打开浏览器

### 3. 智能管理
- ✅ status.bat 查看运行状态
- ✅ logs.bat 分服务查看日志
- ✅ restart.bat 一键重启
- ✅ stop.bat 优雅停止

### 4. 完整功能
- ✅ AI驱动的文章生成
- ✅ 自动发布到WordPress
- ✅ Google Drive图片存储
- ✅ SEO优化
- ✅ Computer Use智能发布（Anthropic API）
- ✅ Playwright免费发布（可选）
- ✅ 任务队列管理
- ✅ 实时监控面板

---

## 💾 使用方式

### Windows电脑上的3步部署

#### 步骤1: 安装Docker Desktop
```
1. 访问 https://www.docker.com/products/docker-desktop/
2. 下载 Windows版本
3. 双击安装
4. 重启电脑
```

#### 步骤2: 解压并配置
```
1. 解压 cms-automation-installer-v1.0.0.tar.gz
   （使用7-Zip或WinRAR）

2. 右键点击 install.bat
   → 以管理员身份运行

3. 按提示输入配置信息

4. 复制 google-drive-credentials.json 到
   backend\credentials\
```

#### 步骤3: 启动系统
```
双击 start.bat
等待 1-2分钟

完成！访问 http://localhost:3000
```

---

## 🎁 安装包亮点

### ✅ 完全不需要命令行
- 所有操作都有批处理脚本
- 双击即可完成
- 图形化配置向导

### ✅ 完全不需要WSL
- 直接在Windows运行
- 使用Docker Desktop
- 原生Windows体验

### ✅ 完全不需要手动配置
- 自动检测环境
- 自动生成配置
- 自动初始化数据库

### ✅ 完全离线可用（除Docker镜像）
- 所有代码已打包
- 所有依赖在镜像中
- 只需下载Docker镜像（一次性）

---

## 🔧 技术架构

### 容器化部署
```
┌─────────────────────────────────────┐
│     Docker Desktop (Windows)        │
│                                     │
│  ┌──────────┐  ┌──────────┐       │
│  │ Frontend │  │ Backend  │       │
│  │  React   │  │  FastAPI │       │
│  └──────────┘  └──────────┘       │
│                                     │
│  ┌──────────┐  ┌──────────┐       │
│  │PostgreSQL│  │  Redis   │       │
│  └──────────┘  └──────────┘       │
│                                     │
│  ┌──────────┐  ┌──────────┐       │
│  │ Celery   │  │  Flower  │       │
│  │ Worker   │  │ (Monitor)│       │
│  └──────────┘  └──────────┘       │
└─────────────────────────────────────┘
         ↓              ↓
    WordPress    Google Drive
```

### 服务列表
| 服务 | 端口 | 说明 |
|------|------|------|
| Frontend | 3000 | React前端界面 |
| Backend API | 8000 | FastAPI后端 |
| PostgreSQL | 5432 | 数据库 |
| Redis | 6379 | 缓存/队列 |
| Flower | 5555 | 任务监控 |

---

## 📊 对比传统部署

| 项目 | 传统部署 | 一键安装包 |
|------|---------|-----------|
| 需要WSL | ✅ 是 | ❌ 否 |
| 需要命令行 | ✅ 大量 | ❌ 否 |
| 配置复杂度 | ⚠️ 高 | ✅ 低 |
| 部署时间 | ⏱️ 2-3小时 | ⏱️ 15分钟 |
| 技术门槛 | 🔴 中等 | 🟢 很低 |
| 错误风险 | ⚠️ 较高 | ✅ 很低 |

---

## 🎓 适用对象

### ✅ 适合使用一键安装包的用户
- 不熟悉命令行的用户
- 需要在多台Windows电脑部署
- 想要快速测试系统
- 追求简单可靠的部署

### ⚠️ 不适合的场景
- 云服务器（Linux）部署 → 推荐用原始docker-compose
- 需要深度定制 → 推荐手动配置
- 开发调试 → 推荐本地开发环境

---

## 📝 文件清单

### 批处理脚本（7个）
- install.bat (配置向导)
- start.bat (启动系统)
- stop.bat (停止系统)
- restart.bat (重启系统)
- status.bat (查看状态)
- logs.bat (查看日志)
- *(自动生成)* .env (环境配置)

### 文档文件（4个）
- README.md (完整手册，20KB)
- QUICKSTART.txt (快速指南)
- 部署检查清单.txt (逐步检查)
- .env.example (配置模板)

### 代码文件（完整项目）
- Backend: Python FastAPI (50+ 文件)
- Frontend: React TypeScript (30+ 文件)
- Docker: 配置文件
- 工具: CSS选择器提取工具

---

## 🔐 安全说明

### 敏感文件（不包含在安装包中）
- ❌ .env (需要用户配置)
- ❌ google-drive-credentials.json (需要用户提供)
- ❌ wordpress_selectors.json (可选，需要用户生成)

### 安全建议
- ✅ 不要分享 .env 文件
- ✅ 妥善保管 API Key
- ✅ 定期更换密码
- ✅ 使用强密码

---

## 🆘 故障排查

### 常见问题速查

**Docker无法启动**
→ 确保已重启电脑
→ 检查Hyper-V或WSL2是否启用

**端口被占用**
→ 修改 docker-compose.yml 端口映射
→ 关闭占用端口的程序

**无法连接WordPress**
→ 检查URL格式（不要以/结尾）
→ 验证应用密码是否正确

**Google Drive上传失败**
→ 必须使用Shared Drive，不是个人Drive
→ 服务账号必须已添加到Shared Drive

---

## 📈 后续更新

### 更新安装包步骤
1. 停止系统: stop.bat
2. 备份数据（可选）
3. 解压新版安装包覆盖
4. 启动系统: start.bat

### 数据库迁移
系统会自动处理数据库迁移

---

## 🎉 总结

### 你问的问题答案：

**Q: 可以做成安装包吗？**
**A: ✅ 可以！已经做好了！**

**Q: 必须在WSL里运行吗？**
**A: ❌ 不必！直接在Windows运行！**

**Q: 需要安装Claude Code吗？**
**A: ❌ 不需要！只需Docker Desktop！**

---

### 这个安装包提供：

✅ 完全图形化操作（双击即可）
✅ 自动环境检测
✅ 交互式配置向导
✅ 一键启动/停止
✅ 实时状态监控
✅ 详细日志查看
✅ 完整功能（Computer Use + Playwright）
✅ 中文文档
✅ 部署检查清单

---

### 只需要：

1. Windows 10/11 电脑
2. Docker Desktop（免费）
3. 15分钟时间

**就能拥有完整的CMS自动化系统！**

---

**安装包位置:**
`dist/cms-automation-installer-v1.0.0.tar.gz`

**复制到Windows后直接使用！** 🚀
