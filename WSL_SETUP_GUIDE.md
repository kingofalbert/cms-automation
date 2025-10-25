# CMS Automation - WSL 環境配置完整指南

**目標系統**: Windows + WSL2 (Ubuntu 20.04/22.04)  
**項目**: CMS Automation MVP  
**最後更新**: 2025-10-25  
**預計設置時間**: 2-3 小時

---

## 📋 目錄

1. [系統要求](#1-系統要求)
2. [WSL2 安裝與配置](#2-wsl2-安裝與配置)
3. [基礎工具安裝](#3-基礎工具安裝)
4. [Python 環境設置](#4-python-環境設置)
5. [Node.js 環境設置](#5-nodejs-環境設置)
6. [Docker 環境配置](#6-docker-環境配置)
7. [Git 配置](#7-git-配置)
8. [項目克隆與設置](#8-項目克隆與設置)
9. [VS Code + Claude Code 配置](#9-vs-code--claude-code-配置)
10. [環境驗證](#10-環境驗證)
11. [故障排除](#11-故障排除)

---

## 1. 系統要求

### Windows 系統要求
- ✅ Windows 10 版本 2004+ (Build 19041+) 或 Windows 11
- ✅ 64-bit 處理器
- ✅ 8GB+ RAM (推薦 16GB)
- ✅ 20GB+ 可用磁碟空間
- ✅ 啟用虛擬化（BIOS/UEFI 中）

### 軟件版本要求
| 工具 | 最低版本 | 推薦版本 | 備註 |
|------|----------|----------|------|
| Python | 3.11+ | 3.13.7 | 當前項目使用 3.13.7 |
| Node.js | 18.0.0+ | 22.19.0 | 當前項目使用 22.19.0 |
| npm | 9.0.0+ | 10.9.3 | 隨 Node.js 安裝 |
| Poetry | 1.5.0+ | 2.2.0+ | Python 包管理 |
| Docker | 20.10+ | 最新版 | Docker Desktop for Windows |
| Git | 2.30+ | 最新版 | 版本控制 |

---

## 2. WSL2 安裝與配置

### 2.1 檢查 Windows 版本

在 PowerShell (管理員) 中運行：

```powershell
# 檢查 Windows 版本
winver

# 檢查 WSL 是否已安裝
wsl --version
```

### 2.2 安裝 WSL2

如果尚未安裝，在 PowerShell (管理員) 中運行：

```powershell
# 安裝 WSL2 和 Ubuntu
wsl --install

# 或指定 Ubuntu 版本
wsl --install -d Ubuntu-22.04

# 重啟電腦
Restart-Computer
```

### 2.3 設置 WSL2 為默認版本

```powershell
# 設置 WSL2 為默認
wsl --set-default-version 2

# 檢查已安裝的發行版
wsl --list --verbose

# 確保使用 WSL2（如果顯示 VERSION 1，需要升級）
wsl --set-version Ubuntu-22.04 2
```

### 2.4 啟動 WSL 並配置用戶

```powershell
# 啟動 Ubuntu
wsl

# 首次啟動會提示創建用戶名和密碼
# 創建後，記住你的密碼（sudo 需要）
```

### 2.5 更新 WSL 系統

在 WSL 終端內運行：

```bash
# 更新包列表
sudo apt update

# 升級所有包
sudo apt upgrade -y

# 安裝基礎構建工具
sudo apt install -y build-essential curl wget git vim nano unzip
```

### 2.6 配置 .wslconfig (可選，性能優化)

在 Windows 用戶目錄創建文件：`C:\Users\<YourUsername>\.wslconfig`

```ini
[wsl2]
# 限制 WSL2 內存使用（推薦系統 RAM 的 50-75%）
memory=8GB

# 限制處理器核心數
processors=4

# 啟用 swap
swap=2GB

# 網絡模式（mirrored 為新功能，需 Windows 11 22H2+）
# networkingMode=mirrored
```

保存後重啟 WSL：

```powershell
wsl --shutdown
wsl
```

---

## 3. 基礎工具安裝

在 WSL 終端內：

### 3.1 安裝通用依賴

```bash
sudo apt install -y \
    build-essential \
    libssl-dev \
    libffi-dev \
    python3-dev \
    libbz2-dev \
    libreadline-dev \
    libsqlite3-dev \
    zlib1g-dev \
    libncurses5-dev \
    libgdbm-dev \
    libnss3-dev \
    libpq-dev \
    ca-certificates \
    gnupg \
    lsb-release
```

### 3.2 安裝 Oh My Zsh (可選，但推薦)

```bash
# 安裝 zsh
sudo apt install -y zsh

# 安裝 Oh My Zsh
sh -c "$(curl -fsSL https://raw.githubusercontent.com/ohmyzsh/ohmyzsh/master/tools/install.sh)"

# 設置為默認 shell
chsh -s $(which zsh)

# 重啟終端生效
exit
wsl
```

---

## 4. Python 環境設置

### 4.1 安裝 pyenv (Python 版本管理)

```bash
# 安裝 pyenv
curl https://pyenv.run | bash

# 添加到 shell 配置（bash 用戶）
echo 'export PYENV_ROOT="$HOME/.pyenv"' >> ~/.bashrc
echo 'command -v pyenv >/dev/null || export PATH="$PYENV_ROOT/bin:$PATH"' >> ~/.bashrc
echo 'eval "$(pyenv init -)"' >> ~/.bashrc

# 或添加到 zsh 配置
echo 'export PYENV_ROOT="$HOME/.pyenv"' >> ~/.zshrc
echo 'command -v pyenv >/dev/null || export PATH="$PYENV_ROOT/bin:$PATH"' >> ~/.zshrc
echo 'eval "$(pyenv init -)"' >> ~/.zshrc

# 重新加載配置
source ~/.zshrc  # 或 source ~/.bashrc
```

### 4.2 安裝 Python 3.13.7

```bash
# 安裝 Python 3.13.7（項目使用版本）
pyenv install 3.13.7

# 設置為全局默認版本
pyenv global 3.13.7

# 驗證安裝
python --version
# 預期輸出: Python 3.13.7

python3 --version
# 預期輸出: Python 3.13.7
```

### 4.3 安裝 Poetry (Python 包管理器)

```bash
# 使用官方安裝腳本
curl -sSL https://install.python-poetry.org | python3 -

# 添加到 PATH
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc

# 驗證安裝
poetry --version
# 預期輸出: Poetry (version 2.2.0 或更高)

# 配置 Poetry（在項目目錄內創建虛擬環境）
poetry config virtualenvs.in-project true
```

---

## 5. Node.js 環境設置

### 5.1 安裝 nvm (Node 版本管理)

```bash
# 安裝 nvm
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.7/install.sh | bash

# 重新加載配置
source ~/.zshrc

# 驗證安裝
nvm --version
# 預期輸出: 0.39.7 或更高
```

### 5.2 安裝 Node.js 22.19.0

```bash
# 安裝 Node.js 22.19.0（項目使用版本）
nvm install 22.19.0

# 設置為默認版本
nvm use 22.19.0
nvm alias default 22.19.0

# 驗證安裝
node --version
# 預期輸出: v22.19.0

npm --version
# 預期輸出: 10.9.3 或類似
```

### 5.3 配置 npm 全局包目錄（可選）

```bash
# 設置全局包安裝路徑（避免權限問題）
mkdir -p ~/.npm-global
npm config set prefix '~/.npm-global'

# 添加到 PATH
echo 'export PATH="$HOME/.npm-global/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc
```

---

## 6. Docker 環境配置

### 6.1 安裝 Docker Desktop for Windows

**在 Windows 主機上操作**：

1. 下載 Docker Desktop：https://www.docker.com/products/docker-desktop/
2. 安裝時確保選擇 **"Use WSL 2 based engine"**
3. 重啟電腦

### 6.2 配置 Docker Desktop 與 WSL2 集成

1. 啟動 Docker Desktop
2. 打開 **Settings** → **Resources** → **WSL Integration**
3. 啟用 **"Enable integration with my default WSL distro"**
4. 啟用你的 Ubuntu 發行版（如 Ubuntu-22.04）
5. 點擊 **"Apply & Restart"**

### 6.3 在 WSL 中驗證 Docker

```bash
# 驗證 Docker 安裝
docker --version
# 預期輸出: Docker version 24.0.x 或更高

docker compose version
# 預期輸出: Docker Compose version v2.x.x

# 測試 Docker 運行
docker run hello-world
# 預期輸出: Hello from Docker!

# 測試 Docker Compose
docker compose version
# 預期輸出: Docker Compose version v2.40.x 或更高
```

### 6.4 配置 Docker 資源限制（可選）

在 Docker Desktop 的 Settings → Resources 中：

- **CPU**: 分配 4-6 核心
- **Memory**: 分配 6-8 GB
- **Swap**: 2 GB
- **Disk image size**: 至少 40 GB

---

## 7. Git 配置

### 7.1 安裝 Git（應該已安裝）

```bash
# 檢查 Git 版本
git --version

# 如果未安裝
sudo apt install -y git
```

### 7.2 配置 Git 用戶信息

```bash
# 配置用戶名和郵箱
git config --global user.name "Your Name"
git config --global user.email "your.email@example.com"

# 配置默認分支名
git config --global init.defaultBranch main

# 配置編輯器（可選）
git config --global core.editor "vim"

# 啟用顏色輸出
git config --global color.ui auto

# 配置 credential helper（避免重複輸入密碼）
git config --global credential.helper store
```

### 7.3 配置 SSH 密鑰（推薦用於 GitHub）

```bash
# 生成 SSH 密鑰
ssh-keygen -t ed25519 -C "your.email@example.com"
# 按 Enter 使用默認路徑，可選輸入密碼

# 啟動 ssh-agent
eval "$(ssh-agent -s)"

# 添加密鑰
ssh-add ~/.ssh/id_ed25519

# 查看公鑰（複製並添加到 GitHub）
cat ~/.ssh/id_ed25519.pub

# 測試 GitHub 連接
ssh -T git@github.com
# 預期輸出: Hi <username>! You've successfully authenticated...
```

**添加 SSH 密鑰到 GitHub**：
1. 複製公鑰內容
2. 訪問 https://github.com/settings/keys
3. 點擊 "New SSH key"
4. 粘貼公鑰，保存

---

## 8. 項目克隆與設置

### 8.1 創建項目目錄

```bash
# 在 WSL 家目錄創建項目目錄
mkdir -p ~/projects
cd ~/projects

# 或者使用 Windows 用戶目錄（推薦用於跨系統訪問）
# cd /mnt/c/Users/<YourUsername>/projects
# mkdir -p cms_automation
```

### 8.2 克隆項目

```bash
# 使用 HTTPS（需要 token 或密碼）
git clone https://github.com/kingofalbert/cms-automation.git
cd cms-automation

# 或使用 SSH（推薦）
git clone git@github.com:kingofalbert/cms-automation.git
cd cms-automation

# 檢查當前分支
git branch -a
git status
```

### 8.3 配置環境變數

```bash
# 複製環境變數示例文件
cp .env.example .env

# 編輯 .env 文件
nano .env  # 或 vim .env
```

**必須配置的變數**：

```bash
# API Keys（必須）
ANTHROPIC_API_KEY=sk-ant-your-api-key-here

# Database Configuration（可使用默認值）
DATABASE_NAME=cms_automation
DATABASE_USER=cms_user
DATABASE_PASSWORD=cms_pass
DATABASE_HOST=localhost
DATABASE_PORT=5432

# Redis Configuration（可使用默認值）
REDIS_HOST=localhost
REDIS_PORT=6379

# CMS Integration（根據實際情況配置）
CMS_TYPE=wordpress
CMS_BASE_URL=https://your-test-site.com
CMS_USERNAME=admin
CMS_APPLICATION_PASSWORD=xxxx xxxx xxxx xxxx

# Security（生成新密鑰）
SECRET_KEY=$(openssl rand -hex 32)

# Application Configuration
API_PORT=8000
FRONTEND_PORT=3000
LOG_LEVEL=INFO
ENVIRONMENT=development
```

保存文件（Ctrl+O, Enter, Ctrl+X）。

### 8.4 安裝後端依賴

```bash
# 進入後端目錄
cd backend

# 使用 Poetry 安裝依賴（推薦）
poetry install

# 或使用 pip（如果不用 Poetry）
# python -m venv .venv
# source .venv/bin/activate
# pip install -r requirements.txt

# 驗證安裝
poetry run python --version
poetry show | head -10

# 返回項目根目錄
cd ..
```

### 8.5 安裝前端依賴

```bash
# 進入前端目錄
cd frontend

# 安裝 npm 依賴
npm install

# 驗證安裝
npm list --depth=0

# 返回項目根目錄
cd ..
```

### 8.6 啟動 Docker 服務

```bash
# 確保在項目根目錄
pwd
# 應該輸出: /home/<username>/projects/cms-automation

# 啟動 PostgreSQL 和 Redis
docker compose up -d postgres redis

# 檢查服務狀態
docker compose ps

# 等待服務健康（約 10-20 秒）
docker compose logs postgres redis
```

### 8.7 運行數據庫遷移

```bash
# 進入後端目錄
cd backend

# 運行 Alembic 遷移
poetry run alembic upgrade head

# 驗證遷移
poetry run alembic current

# 返回項目根目錄
cd ..
```

### 8.8 驗證 PostgreSQL + pgvector

```bash
# 連接到數據庫
docker compose exec postgres psql -U cms_user -d cms_automation

# 在 psql 中運行：
\dx
# 應該看到 pgvector 擴展

\dt
# 應該看到創建的表：articles, topic_requests, topic_embeddings

\q
# 退出 psql
```

---

## 9. VS Code + Claude Code 配置

### 9.1 安裝 VS Code (Windows)

1. 下載：https://code.visualstudio.com/
2. 安裝時確保勾選 **"Add to PATH"**

### 9.2 安裝 WSL 擴展

在 VS Code 中安裝以下擴展：

1. **Remote - WSL** (ms-vscode-remote.remote-wsl)
2. **Python** (ms-python.python)
3. **Pylance** (ms-python.vscode-pylance)
4. **ESLint** (dbaeumer.vscode-eslint)
5. **Prettier** (esbenp.prettier-vscode)
6. **Tailwind CSS IntelliSense** (bradlc.vscode-tailwindcss)
7. **Docker** (ms-azuretools.vscode-docker)

### 9.3 在 WSL 中打開項目

**方法 1: 從 WSL 終端**

```bash
# 在項目目錄
cd ~/projects/cms-automation

# 使用 VS Code 打開
code .
```

**方法 2: 從 VS Code**

1. 按 `F1` 或 `Ctrl+Shift+P`
2. 輸入 "WSL: Open Folder in WSL"
3. 選擇項目目錄

### 9.4 安裝 Claude Code CLI (在 WSL 內)

```bash
# 方法 1: 使用 npm 全局安裝
npm install -g @anthropic-ai/claude-code

# 方法 2: 使用 npx (無需安裝)
npx @anthropic-ai/claude-code --version

# 配置 Claude API Key
export ANTHROPIC_API_KEY=sk-ant-your-api-key-here

# 添加到 shell 配置（永久）
echo 'export ANTHROPIC_API_KEY=sk-ant-your-api-key-here' >> ~/.zshrc
source ~/.zshrc

# 驗證安裝
claude --version
# 或
npx @anthropic-ai/claude-code --version
```

### 9.5 配置 VS Code 設置（在 WSL 項目中）

創建 `.vscode/settings.json`：

```bash
mkdir -p .vscode
cat > .vscode/settings.json <<'JSON'
{
  "python.defaultInterpreterPath": "${workspaceFolder}/backend/.venv/bin/python",
  "python.linting.enabled": true,
  "python.linting.pylintEnabled": false,
  "python.linting.ruffEnabled": true,
  "python.formatting.provider": "black",
  "editor.formatOnSave": true,
  "editor.codeActionsOnSave": {
    "source.organizeImports": true
  },
  "files.exclude": {
    "**/__pycache__": true,
    "**/.pytest_cache": true,
    "**/.mypy_cache": true,
    "**/.ruff_cache": true,
    "**/node_modules": true
  },
  "[python]": {
    "editor.defaultFormatter": "ms-python.black-formatter",
    "editor.tabSize": 4
  },
  "[typescript]": {
    "editor.defaultFormatter": "esbenp.prettier-vscode",
    "editor.tabSize": 2
  },
  "[typescriptreact]": {
    "editor.defaultFormatter": "esbenp.prettier-vscode",
    "editor.tabSize": 2
  }
}
JSON
```

---

## 10. 環境驗證

### 10.1 快速驗證檢查清單

運行以下命令驗證所有組件：

```bash
# 創建驗證腳本
cat > verify_setup.sh <<'SCRIPT'
#!/bin/bash

echo "=========================================="
echo "CMS Automation 環境驗證"
echo "=========================================="
echo ""

# Python
echo "✓ 檢查 Python..."
python --version || echo "❌ Python 未安裝"
echo ""

# Poetry
echo "✓ 檢查 Poetry..."
poetry --version || echo "❌ Poetry 未安裝"
echo ""

# Node.js
echo "✓ 檢查 Node.js..."
node --version || echo "❌ Node.js 未安裝"
npm --version || echo "❌ npm 未安裝"
echo ""

# Docker
echo "✓ 檢查 Docker..."
docker --version || echo "❌ Docker 未安裝"
docker compose version || echo "❌ Docker Compose 未安裝"
echo ""

# Git
echo "✓ 檢查 Git..."
git --version || echo "❌ Git 未安裝"
echo ""

# PostgreSQL (Docker)
echo "✓ 檢查 PostgreSQL..."
docker compose ps postgres 2>/dev/null || echo "⚠️  PostgreSQL 未運行"
echo ""

# Redis (Docker)
echo "✓ 檢查 Redis..."
docker compose ps redis 2>/dev/null || echo "⚠️  Redis 未運行"
echo ""

# 後端依賴
echo "✓ 檢查後端依賴..."
if [ -f "backend/pyproject.toml" ]; then
    cd backend
    poetry check 2>/dev/null && echo "  Backend dependencies OK" || echo "⚠️  需要運行: cd backend && poetry install"
    cd ..
else
    echo "⚠️  後端目錄未找到"
fi
echo ""

# 前端依賴
echo "✓ 檢查前端依賴..."
if [ -d "frontend/node_modules" ]; then
    echo "  Frontend dependencies OK"
else
    echo "⚠️  需要運行: cd frontend && npm install"
fi
echo ""

# 環境變數
echo "✓ 檢查環境變數..."
if [ -f ".env" ]; then
    echo "  .env 文件存在"
    grep -q "ANTHROPIC_API_KEY=sk-ant-" .env && echo "  ✓ ANTHROPIC_API_KEY 已配置" || echo "  ⚠️  ANTHROPIC_API_KEY 需要配置"
else
    echo "⚠️  需要創建 .env 文件: cp .env.example .env"
fi
echo ""

echo "=========================================="
echo "驗證完成！"
echo "=========================================="
SCRIPT

chmod +x verify_setup.sh
./verify_setup.sh
```

### 10.2 啟動測試

**啟動後端（Terminal 1）**：

```bash
cd backend
poetry run uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

# 在另一個終端測試
curl http://localhost:8000/health
# 預期: {"status":"healthy","service":"cms-automation"}
```

**啟動 Celery Worker（Terminal 2）**：

```bash
cd backend
poetry run celery -A src.workers.celery_app worker --loglevel=info
```

**啟動前端（Terminal 3）**：

```bash
cd frontend
npm run dev

# 瀏覽器訪問: http://localhost:3000
```

### 10.3 驗證 API 文檔

訪問 http://localhost:8000/docs 應該看到 FastAPI 的 OpenAPI 文檔。

---

## 11. 故障排除

### 11.1 常見問題

#### 問題 1: Docker 無法啟動

```bash
# 檢查 Docker Desktop 是否運行（Windows）
# 在 PowerShell 中：
Get-Process "Docker Desktop"

# 重啟 Docker Desktop
# 在 Windows 系統托盤右鍵 Docker 圖標 → Restart

# 在 WSL 中檢查 Docker 守護進程
docker info
```

#### 問題 2: Poetry 虛擬環境問題

```bash
cd backend

# 刪除現有虛擬環境
rm -rf .venv

# 重新安裝
poetry install

# 驗證 Python 路徑
poetry run which python
```

#### 問題 3: npm 權限錯誤

```bash
# 清理 npm 緩存
npm cache clean --force

# 刪除 node_modules
rm -rf node_modules package-lock.json

# 重新安裝
npm install
```

#### 問題 4: PostgreSQL 連接失敗

```bash
# 檢查容器狀態
docker compose ps postgres

# 檢查日誌
docker compose logs postgres

# 重啟容器
docker compose restart postgres

# 測試連接
docker compose exec postgres psql -U cms_user -d cms_automation -c "SELECT 1;"
```

#### 問題 5: WSL 網絡問題

```bash
# 重啟 WSL 網絡
# 在 PowerShell (管理員)：
wsl --shutdown
wsl

# 檢查 WSL IP
ip addr show eth0
```

#### 問題 6: Git 憑證問題

```bash
# 清除保存的憑證
git config --global --unset credential.helper

# 重新配置
git config --global credential.helper store

# 或使用 SSH（推薦）
git remote set-url origin git@github.com:kingofalbert/cms-automation.git
```

### 11.2 性能優化建議

#### 優化 1: 啟用 WSL2 鏡像網絡（Windows 11 22H2+）

編輯 `C:\Users\<YourUsername>\.wslconfig`：

```ini
[wsl2]
networkingMode=mirrored
dnsTunneling=true
firewall=true
autoProxy=true
```

#### 優化 2: 使用 WSL2 文件系統

**推薦**：將項目放在 WSL2 文件系統（`~/projects/`），而不是 Windows 文件系統（`/mnt/c/`）。

原因：
- ✅ 更快的 I/O 性能（約 20-30 倍）
- ✅ 更好的 Git 性能
- ✅ 避免文件權限問題

#### 優化 3: 配置 Docker 內存限制

在 Docker Desktop → Settings → Resources：
- Memory: 6-8 GB
- CPUs: 4-6 核心
- Swap: 2 GB

---

## 12. 快速啟動指令摘要

配置完成後，日常啟動流程：

```bash
# 1. 啟動 Docker 服務
cd ~/projects/cms-automation
docker compose up -d postgres redis

# 2. 啟動後端 (Terminal 1)
cd backend
poetry run uvicorn src.main:app --reload

# 3. 啟動 Worker (Terminal 2)
cd backend
poetry run celery -A src.workers.celery_app worker --loglevel=info

# 4. 啟動前端 (Terminal 3)
cd frontend
npm run dev

# 訪問應用:
# - Frontend: http://localhost:3000
# - Backend API: http://localhost:8000
# - API Docs: http://localhost:8000/docs
```

---

## 13. Claude Code 使用指南

### 13.1 啟動 Claude Code

```bash
# 在項目根目錄
cd ~/projects/cms-automation

# 啟動 Claude Code
claude

# 或使用 npx
npx @anthropic-ai/claude-code
```

### 13.2 常用 Claude Code 命令

```bash
# 在 Claude Code CLI 中:

# 查看幫助
/help

# 列出可用的 slash 命令
/speckit.tasks

# 執行驗證
按照 WSL_SETUP_GUIDE.md 的步驟進行環境驗證

# 開始開發
根據 logs/implementation_roadmap.md 開始實施 Phase 3
```

---

## 14. 檢查清單

使用此清單確保所有配置正確：

### 基礎環境
- [ ] WSL2 已安裝並運行
- [ ] Ubuntu 22.04 已更新到最新
- [ ] Windows 和 WSL 時區同步

### 開發工具
- [ ] Python 3.13.7 已安裝並配置
- [ ] Poetry 2.2.0+ 已安裝
- [ ] Node.js 22.19.0 已安裝
- [ ] npm 10.9.3+ 已安裝
- [ ] Git 已配置（用戶名、郵箱）
- [ ] SSH 密鑰已添加到 GitHub

### Docker 環境
- [ ] Docker Desktop 已安裝
- [ ] WSL2 集成已啟用
- [ ] PostgreSQL 容器運行正常
- [ ] Redis 容器運行正常
- [ ] pgvector 擴展已啟用

### 項目設置
- [ ] 項目已從 GitHub 克隆
- [ ] .env 文件已配置
- [ ] ANTHROPIC_API_KEY 已設置
- [ ] 後端依賴已安裝 (poetry install)
- [ ] 前端依賴已安裝 (npm install)
- [ ] 數據庫遷移已運行 (alembic upgrade head)

### 開發工具
- [ ] VS Code + WSL 擴展已安裝
- [ ] Python 擴展已配置
- [ ] ESLint/Prettier 已配置
- [ ] Claude Code CLI 可用

### 驗證測試
- [ ] 後端健康檢查通過 (curl localhost:8000/health)
- [ ] API 文檔可訪問 (localhost:8000/docs)
- [ ] Celery worker 啟動無錯誤
- [ ] 前端開發服務器運行 (localhost:3000)
- [ ] 可以提交表單並生成文章

---

## 15. 下一步

環境配置完成後：

1. 📖 **閱讀項目文檔**
   - `README.md` - 項目概述
   - `specs/001-cms-automation/quickstart.md` - 快速開始
   - `specs/001-cms-automation/plan.md` - 實施計劃

2. 📊 **查看驗證報告**
   - `logs/verification_summary.md` - MVP 驗證摘要
   - `logs/implementation_roadmap.md` - 實施路線圖

3. 🚀 **開始開發**
   - 按照 5 步計劃實施 MVP
   - 從 GenerationProgress 組件開始
   - 運行 E2E 測試

4. 📝 **使用 Claude Code**
   - 在項目目錄運行 `claude`
   - 參考此文檔進行配置驗證
   - 開始編碼和測試

---

## 附錄 A: 有用的 WSL 命令

```bash
# WSL 管理（在 PowerShell 中）
wsl --list --verbose                 # 列出所有發行版
wsl --shutdown                       # 關閉所有 WSL 實例
wsl --terminate Ubuntu-22.04         # 終止特定發行版
wsl --export Ubuntu-22.04 backup.tar # 導出備份
wsl --import NewUbuntu C:\path backup.tar  # 導入備份

# WSL 內部
explorer.exe .                       # 在 Windows 資源管理器打開當前目錄
code .                               # 在 VS Code 中打開當前目錄
cmd.exe /c start http://localhost:3000  # 在 Windows 瀏覽器打開 URL

# 跨系統訪問
/mnt/c/Users/<Name>/              # 訪問 Windows C 盤
\\wsl$\Ubuntu-22.04\home\<user>\  # 從 Windows 訪問 WSL
```

---

## 附錄 B: 環境變數參考

完整的 `.env` 文件模板：

```bash
# API Keys
ANTHROPIC_API_KEY=sk-ant-api-key-here

# Database Configuration
DATABASE_NAME=cms_automation
DATABASE_USER=cms_user
DATABASE_PASSWORD=cms_pass
DATABASE_HOST=localhost
DATABASE_PORT=5432
DATABASE_URL=postgresql://cms_user:cms_pass@localhost:5432/cms_automation
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=10
DATABASE_POOL_TIMEOUT=30
DATABASE_POOL_RECYCLE=3600

# Redis Configuration
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_URL=redis://localhost:6379/0

# CMS Integration
CMS_TYPE=wordpress
CMS_BASE_URL=https://your-site.com
CMS_USERNAME=admin
CMS_APPLICATION_PASSWORD=xxxx xxxx xxxx xxxx

# Application Configuration
API_PORT=8000
FRONTEND_PORT=3000
FLOWER_PORT=5555
LOG_LEVEL=INFO
ENVIRONMENT=development

# Security
SECRET_KEY=your-secret-key-generated-with-openssl-rand-hex-32
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:8000

# Feature Flags
ENABLE_SEMANTIC_SIMILARITY=true
SIMILARITY_THRESHOLD=0.85
MAX_CONCURRENT_GENERATIONS=10

# AI Generation Settings
MAX_ARTICLE_WORD_COUNT=10000
MIN_ARTICLE_WORD_COUNT=100
DEFAULT_ARTICLE_WORD_COUNT=1000
MAX_ARTICLE_GENERATION_TIME=300
MAX_ARTICLE_COST=0.50

# Retry Configuration
MAX_RETRIES=3
RETRY_DELAY=300

# Monitoring
ENABLE_METRICS=true
METRICS_PORT=9090
```

---

**文檔版本**: 1.0  
**最後更新**: 2025-10-25  
**維護者**: CMS Automation Team  
**問題報告**: https://github.com/kingofalbert/cms-automation/issues

---

**🎉 祝您配置順利！如遇問題請參考故障排除章節或聯繫團隊。**
