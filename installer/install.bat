@echo off
chcp 65001 >nul
REM ========================================
REM   CMS自动化系统 - Windows安装脚本
REM   版本: 1.0.0
REM ========================================

echo.
echo ========================================
echo   CMS自动化系统 - 安装向导
echo ========================================
echo.

REM 检查管理员权限
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo [警告] 建议以管理员身份运行此脚本
    echo.
    timeout /t 3 >nul
)

REM 步骤1：检查Docker
echo [步骤 1/5] 检查Docker是否已安装...
docker --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [×] Docker未安装！
    echo.
    echo 请先安装Docker Desktop for Windows:
    echo https://www.docker.com/products/docker-desktop/
    echo.
    echo 安装完成后请重启电脑，然后重新运行此脚本。
    pause
    exit /b 1
)

for /f "tokens=3" %%i in ('docker --version') do set DOCKER_VERSION=%%i
echo [√] Docker已安装 (版本: %DOCKER_VERSION%)
echo.

REM 步骤2：检查Docker是否运行
echo [步骤 2/5] 检查Docker服务是否运行...
docker ps >nul 2>&1
if %errorlevel% neq 0 (
    echo [×] Docker服务未运行！
    echo.
    echo 请启动Docker Desktop，然后重新运行此脚本。
    pause
    exit /b 1
)
echo [√] Docker服务正在运行
echo.

REM 步骤3：检查docker-compose
echo [步骤 3/5] 检查docker-compose...
docker-compose --version >nul 2>&1
if %errorlevel% neq 0 (
    docker compose version >nul 2>&1
    if %errorlevel% neq 0 (
        echo [×] docker-compose未安装！
        echo.
        echo 请确保Docker Desktop已正确安装。
        pause
        exit /b 1
    )
    set COMPOSE_CMD=docker compose
) else (
    set COMPOSE_CMD=docker-compose
)
echo [√] docker-compose已就绪
echo.

REM 步骤4：环境配置
echo [步骤 4/5] 配置环境变量...
echo.

if exist .env (
    echo [提示] 发现已存在的.env文件
    set /p OVERWRITE="是否覆盖现有配置? (y/N): "
    if /i not "%OVERWRITE%"=="y" (
        echo [√] 保留现有配置
        goto :skip_config
    )
)

echo 请按照提示输入配置信息：
echo.

REM Anthropic API Key
echo ┌─────────────────────────────────────┐
echo │  Anthropic API配置                  │
echo └─────────────────────────────────────┘
set /p ANTHROPIC_KEY="请输入Anthropic API Key: "

REM WordPress配置
echo.
echo ┌─────────────────────────────────────┐
echo │  WordPress配置                      │
echo └─────────────────────────────────────┘
set /p WORDPRESS_URL="WordPress网站URL (如: https://example.com): "
set /p WORDPRESS_USER="WordPress用户名: "
set /p WORDPRESS_PASS="WordPress应用密码: "

REM Google Drive配置
echo.
echo ┌─────────────────────────────────────┐
echo │  Google Drive配置                   │
echo └─────────────────────────────────────┘
set /p GOOGLE_DRIVE_FOLDER="Google Drive Shared Drive文件夹ID: "

REM 生成随机密钥
for /f %%i in ('powershell -Command "[guid]::NewGuid().ToString('N')"') do set SECRET_KEY=%%i

REM 创建.env文件
echo # CMS自动化系统环境配置 > .env
echo # 生成时间: %date% %time% >> .env
echo. >> .env
echo # Anthropic API >> .env
echo ANTHROPIC_API_KEY=%ANTHROPIC_KEY% >> .env
echo. >> .env
echo # 数据库配置 >> .env
echo DATABASE_NAME=cms_automation >> .env
echo DATABASE_USER=cms_user >> .env
echo DATABASE_PASSWORD=cms_pass_123 >> .env
echo DATABASE_HOST=localhost >> .env
echo DATABASE_PORT=5432 >> .env
echo DATABASE_URL=postgresql://cms_user:cms_pass_123@postgres:5432/cms_automation >> .env
echo DATABASE_POOL_SIZE=20 >> .env
echo. >> .env
echo # Redis配置 >> .env
echo REDIS_HOST=localhost >> .env
echo REDIS_PORT=6379 >> .env
echo REDIS_URL=redis://redis:6379/0 >> .env
echo. >> .env
echo # WordPress配置 >> .env
echo CMS_TYPE=wordpress >> .env
echo CMS_BASE_URL=%WORDPRESS_URL% >> .env
echo CMS_USERNAME=%WORDPRESS_USER% >> .env
echo CMS_APPLICATION_PASSWORD=%WORDPRESS_PASS% >> .env
echo. >> .env
echo # 应用配置 >> .env
echo API_PORT=8000 >> .env
echo FRONTEND_PORT=3000 >> .env
echo FLOWER_PORT=5555 >> .env
echo LOG_LEVEL=INFO >> .env
echo ENVIRONMENT=production >> .env
echo. >> .env
echo # 安全配置 >> .env
echo SECRET_KEY=%SECRET_KEY% >> .env
echo ALLOWED_ORIGINS=http://localhost:3000,http://localhost:8000 >> .env
echo. >> .env
echo # 功能开关 >> .env
echo ENABLE_SEMANTIC_SIMILARITY=true >> .env
echo SIMILARITY_THRESHOLD=0.85 >> .env
echo MAX_CONCURRENT_GENERATIONS=10 >> .env
echo. >> .env
echo # AI生成配置 >> .env
echo MAX_ARTICLE_WORD_COUNT=10000 >> .env
echo MIN_ARTICLE_WORD_COUNT=100 >> .env
echo DEFAULT_ARTICLE_WORD_COUNT=1000 >> .env
echo MAX_ARTICLE_GENERATION_TIME=300 >> .env
echo MAX_ARTICLE_COST=0.50 >> .env
echo. >> .env
echo # 重试配置 >> .env
echo MAX_RETRIES=3 >> .env
echo RETRY_DELAY=300 >> .env
echo. >> .env
echo # 监控配置 >> .env
echo ENABLE_METRICS=true >> .env
echo METRICS_PORT=9090 >> .env
echo. >> .env
echo # Google Drive配置 >> .env
echo GOOGLE_DRIVE_CREDENTIALS_PATH=/app/credentials/google-drive-credentials.json >> .env
echo GOOGLE_DRIVE_FOLDER_ID=%GOOGLE_DRIVE_FOLDER% >> .env

echo [√] 配置文件已生成
echo.

:skip_config

REM 步骤5：创建必要目录
echo [步骤 5/5] 创建必要目录...
if not exist "backend\credentials" mkdir backend\credentials
if not exist "backend\config" mkdir backend\config
echo [√] 目录结构已创建
echo.

echo ========================================
echo   安装完成！
echo ========================================
echo.
echo 重要提示：
echo 1. 请将Google Drive凭证文件复制到:
echo    backend\credentials\google-drive-credentials.json
echo.
echo 2. (可选) 如需使用Playwright免费方案，请配置:
echo    backend\config\wordpress_selectors.json
echo.
echo 3. 准备好后，运行 start.bat 启动系统
echo.
pause
