@echo off
chcp 65001 >nul
REM ========================================
REM   CMS自动化系统 - 状态检查
REM ========================================

echo.
echo ========================================
echo   CMS自动化系统 - 运行状态
echo ========================================
echo.

echo [容器状态]
echo.
docker-compose ps

echo.
echo ========================================
echo.

echo [健康检查]
echo.
echo 正在检查API健康状态...
curl -s http://localhost:8000/health >nul 2>&1
if %errorlevel% equ 0 (
    echo [√] API服务正常
) else (
    echo [×] API服务异常
)

echo.
echo 正在检查前端服务...
curl -s http://localhost:3000 >nul 2>&1
if %errorlevel% equ 0 (
    echo [√] 前端服务正常
) else (
    echo [×] 前端服务异常
)

echo.
echo 正在检查Flower监控...
curl -s http://localhost:5555 >nul 2>&1
if %errorlevel% equ 0 (
    echo [√] Flower监控正常
) else (
    echo [×] Flower监控异常
)

echo.
echo ========================================
echo.

echo [资源使用]
echo.
docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}"

echo.
echo ========================================
echo.
pause
