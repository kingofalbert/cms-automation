# CMS自动化系统 - Windows一键安装包

## 📦 系统简介

这是一个智能的内容管理系统(CMS)自动化工具，具有以下功能：

- ✅ AI驱动的文章生成
- ✅ 自动发布到WordPress
- ✅ Google Drive图片存储
- ✅ SEO优化
- ✅ 任务队列管理
- ✅ Computer Use智能发布（支持Anthropic API和Playwright免费方案）

---

## 💻 系统要求

### 必需条件：
- Windows 10/11 (专业版/企业版/家庭版均可)
- 至少 8GB RAM
- 至少 20GB 可用磁盘空间
- 稳定的网络连接

### 需要安装的软件：
- **Docker Desktop** (必需)
  - 下载地址：https://www.docker.com/products/docker-desktop/
  - Windows 10/11 专业版/企业版：使用Hyper-V
  - Windows 10/11 家庭版：使用WSL2

---

## 🚀 快速开始（5步完成）

### 步骤 1：安装Docker Desktop

1. 访问 https://www.docker.com/products/docker-desktop/
2. 下载Windows版本
3. 双击安装包安装
4. 安装完成后**重启电脑**
5. 启动Docker Desktop

**验证安装：**
```cmd
打开命令提示符（CMD）或PowerShell
运行：docker --version
应该看到：Docker version 24.x.x
```

---

### 步骤 2：解压安装包

1. 将 `cms-automation-installer.zip` 解压到任意文件夹
   - 推荐路径：`C:\cms-automation\`
   - 避免路径包含中文或空格

2. 解压后应该看到这些文件：
   ```
   cms-automation/
   ├── install.bat          # 安装配置脚本
   ├── start.bat           # 启动系统
   ├── stop.bat            # 停止系统
   ├── restart.bat         # 重启系统
   ├── status.bat          # 查看状态
   ├── logs.bat            # 查看日志
   ├── README.md           # 本文档
   ├── docker-compose.yml  # Docker配置
   └── backend/
       ├── credentials/    # 凭证文件目录
       └── config/         # 配置文件目录
   ```

---

### 步骤 3：准备配置信息

在运行安装脚本前，请准备好以下信息：

#### 3.1 Anthropic API Key
- 访问：https://console.anthropic.com/
- 登录并创建API Key
- 复制保存（格式：sk-ant-api03-...）

#### 3.2 WordPress信息
- WordPress网站URL（如：https://your-site.com）
- WordPress管理员用户名
- WordPress应用密码（Application Password）
  - 在WordPress后台：用户 → 个人资料 → 应用密码

#### 3.3 Google Drive配置
- Google Drive服务账号凭证文件（JSON）
- Google Drive Shared Drive文件夹ID

**如何获取Shared Drive文件夹ID：**
1. 在Google Drive创建Shared Drive
2. 添加服务账号为成员
3. 打开Shared Drive，URL中的ID即为文件夹ID
   - 示例：`https://drive.google.com/drive/folders/1ABC...XYZ`
   - 文件夹ID：`1ABC...XYZ`

---

### 步骤 4：运行安装配置

1. 右键点击 `install.bat`
2. 选择"以管理员身份运行"（推荐）

3. 按照提示输入配置信息：
   ```
   请输入Anthropic API Key: sk-ant-api03-...
   WordPress网站URL: https://your-site.com
   WordPress用户名: admin
   WordPress应用密码: xxxx xxxx xxxx xxxx
   Google Drive Shared Drive文件夹ID: 1ABC...XYZ
   ```

4. 配置完成后会生成 `.env` 文件

5. **重要：** 复制Google Drive凭证文件
   - 将 `google-drive-credentials.json` 复制到：
   - `backend\credentials\google-drive-credentials.json`

---

### 步骤 5：启动系统

1. 双击 `start.bat`
2. 等待1-2分钟，系统将自动：
   - 拉取Docker镜像
   - 启动所有服务
   - 初始化数据库

3. 看到以下信息表示启动成功：
   ```
   ========================================
     系统已启动！
   ========================================

   访问地址：
     前端界面:  http://localhost:3000
     API文档:   http://localhost:8000/docs
     任务监控:  http://localhost:5555
   ```

4. 在浏览器访问：
   - http://localhost:3000 （前端界面）
   - http://localhost:8000/docs （API文档）

---

## 🎮 日常使用

### 启动系统
```cmd
双击：start.bat
```

### 停止系统
```cmd
双击：stop.bat
```

### 重启系统
```cmd
双击：restart.bat
```

### 查看状态
```cmd
双击：status.bat
```

### 查看日志
```cmd
双击：logs.bat
然后选择要查看的服务日志
```

---

## 🔧 高级配置

### 配置Playwright免费发布方案（可选）

如果想使用完全免费的Playwright发布方案：

1. 登录WordPress后台
2. 按 F12 打开开发者工具
3. 切换到 Console 标签
4. 复制粘贴 `backend\tools\extract_wordpress_selectors.js` 的内容
5. 运行 `autoDetect()` 或分步提取
6. 复制输出的JSON配置
7. 保存为 `backend\config\wordpress_selectors.json`
8. 重启系统

配置完成后，系统会自动使用Playwright免费方案发布简单文章。

---

## 📊 系统架构

```
┌─────────────────────────────────────────────────┐
│                    用户界面                      │
│          http://localhost:3000                  │
└──────────────────┬──────────────────────────────┘
                   │
┌──────────────────┴──────────────────────────────┐
│              FastAPI 后端                        │
│          http://localhost:8000                  │
│                                                  │
│  ┌──────────────┐  ┌──────────────┐            │
│  │  文章生成    │  │  SEO优化     │            │
│  └──────────────┘  └──────────────┘            │
│                                                  │
│  ┌──────────────┐  ┌──────────────┐            │
│  │  图片管理    │  │  发布管理    │            │
│  └──────────────┘  └──────────────┘            │
└──────────────────┬──────────────────────────────┘
                   │
┌──────────────────┴──────────────────────────────┐
│              Celery 任务队列                     │
│                                                  │
│  ┌──────────────┐  ┌──────────────┐            │
│  │  Worker      │  │  Beat        │            │
│  └──────────────┘  └──────────────┘            │
└──────────────────┬──────────────────────────────┘
                   │
┌──────────────────┴──────────────────────────────┐
│              数据存储                            │
│                                                  │
│  ┌──────────────┐  ┌──────────────┐            │
│  │  PostgreSQL  │  │  Redis       │            │
│  └──────────────┘  └──────────────┘            │
└──────────────────────────────────────────────────┘

         ┌──────────────┐  ┌──────────────┐
         │ Google Drive │  │  WordPress   │
         │    存储      │  │    CMS       │
         └──────────────┘  └──────────────┘
```

---

## 🔌 端口使用

| 服务 | 端口 | 访问地址 |
|------|------|---------|
| 前端 | 3000 | http://localhost:3000 |
| API | 8000 | http://localhost:8000 |
| Flower监控 | 5555 | http://localhost:5555 |
| PostgreSQL | 5432 | localhost:5432 |
| Redis | 6379 | localhost:6379 |

---

## ❓ 常见问题

### Q1: Docker无法启动
**A:**
- 确保已重启电脑
- 检查Hyper-V或WSL2是否启用
- 查看Docker Desktop设置

### Q2: 端口被占用
**A:**
```cmd
# 修改 docker-compose.yml 中的端口映射
# 例如将3000改为3001：
ports:
  - "3001:3000"
```

### Q3: 无法连接WordPress
**A:**
- 检查WordPress URL是否正确
- 确认应用密码是否有效
- 查看防火墙设置

### Q4: Google Drive上传失败
**A:**
- 确认凭证文件路径正确
- 检查服务账号是否已添加到Shared Drive
- 验证Shared Drive文件夹ID

### Q5: 系统运行缓慢
**A:**
- 给Docker分配更多资源
  - Docker Desktop → Settings → Resources
  - 增加CPU和内存限制

### Q6: 如何更新系统
**A:**
```cmd
1. 停止系统: stop.bat
2. 拉取最新代码/镜像
3. 运行: start.bat
```

---

## 📝 配置文件说明

### .env 文件
所有环境配置都在此文件中，可手动编辑：

```bash
# 打开方式
notepad .env
```

主要配置项：
- `ANTHROPIC_API_KEY` - Anthropic API密钥
- `CMS_BASE_URL` - WordPress网址
- `GOOGLE_DRIVE_FOLDER_ID` - Google Drive文件夹ID

### docker-compose.yml
Docker服务编排配置，一般无需修改。

---

## 🛡️ 安全建议

1. **不要**将 `.env` 文件提交到代码仓库
2. **不要**分享你的API密钥
3. 定期更换WordPress应用密码
4. 使用强密码
5. 定期备份数据库

---

## 💾 数据备份

### 备份数据库
```cmd
docker exec cms_automation_postgres pg_dump -U cms_user cms_automation > backup.sql
```

### 恢复数据库
```cmd
docker exec -i cms_automation_postgres psql -U cms_user cms_automation < backup.sql
```

---

## 📈 性能优化

### 给Docker分配更多资源
1. 打开 Docker Desktop
2. Settings → Resources
3. 调整 CPU 和 Memory
   - 推荐：CPU 4核，Memory 4GB+

### 清理Docker缓存
```cmd
docker system prune -a
```

---

## 🆘 获取帮助

### 查看日志排查问题
```cmd
运行：logs.bat
选择相应服务查看日志
```

### 常用Docker命令
```cmd
# 查看所有容器
docker ps -a

# 进入backend容器
docker exec -it cms_automation_backend bash

# 重启特定服务
docker-compose restart backend

# 查看容器日志
docker logs cms_automation_backend
```

---

## 📜 许可证

本项目采用 MIT 许可证

---

## 🎉 享受使用！

安装完成后，你将拥有一个功能强大的CMS自动化系统：

- 🤖 AI驱动的内容生成
- 🚀 一键发布到WordPress
- 💾 智能图片管理
- 📊 实时任务监控
- 🎯 SEO优化
- 💰 可选免费发布方案

祝你使用愉快！
