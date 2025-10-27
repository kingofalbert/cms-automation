@echo off
chcp 65001 >nul
REM ========================================
REM   CMS自动化系统 - 启动脚本
REM ========================================

echo.
echo ========================================
echo   启动 CMS自动化系统
echo ========================================
echo.

REM 检查Docker是否运行
docker ps >nul 2>&1
if %errorlevel% neq 0 (
    echo [×] Docker服务未运行！
    echo.
    echo 请先启动Docker Desktop，然后重新运行此脚本。
    pause
    exit /b 1
)

REM 检查.env文件
if not exist ".env" (
    echo [×] 配置文件不存在！
    echo.
    echo 请先运行 install.bat 进行初始化配置。
    pause
    exit /b 1
)

REM 检查凭证文件
if not exist "backend\credentials\google-drive-credentials.json" (
    echo [警告] Google Drive凭证文件不存在！
    echo 路径: backend\credentials\google-drive-credentials.json
    echo.
    echo 文件上传功能将无法使用。
    echo 如需使用，请放置凭证文件后重启系统。
    echo.
    timeout /t 5
)

echo [1/4] 拉取最新镜像...
docker-compose pull

echo.
echo [2/4] 构建镜像...
docker-compose build

echo.
echo [3/4] 启动服务...
docker-compose up -d

echo.
echo [4/4] 等待服务就绪...
timeout /t 10 >nul

echo.
echo ========================================
echo   系统已启动！
echo ========================================
echo.
echo 访问地址：
echo.
echo   📱 前端界面:  http://localhost:3000
echo   🔧 API文档:   http://localhost:8000/docs
echo   📊 任务监控:  http://localhost:5555 (Flower)
echo   ❤️  健康检查:  http://localhost:8000/health
echo.
echo 管理命令：
echo   查看日志:  logs.bat
echo   停止系统:  stop.bat
echo   重启系统:  restart.bat
echo   查看状态:  status.bat
echo.
echo 提示: 首次启动需要等待1-2分钟完成数据库初始化
echo.

REM 可选：打开浏览器
set /p OPEN_BROWSER="是否在浏览器中打开系统? (Y/n): "
if /i not "%OPEN_BROWSER%"=="n" (
    start http://localhost:3000
    start http://localhost:8000/docs
)

pause
