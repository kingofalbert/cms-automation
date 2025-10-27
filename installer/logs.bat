@echo off
chcp 65001 >nul
REM ========================================
REM   CMS自动化系统 - 日志查看
REM ========================================

echo.
echo ========================================
echo   选择要查看的日志
echo ========================================
echo.
echo 1. 所有服务日志
echo 2. 后端API日志
echo 3. Celery Worker日志
echo 4. PostgreSQL日志
echo 5. Redis日志
echo 6. 前端日志
echo 0. 退出
echo.

set /p CHOICE="请选择 (1-6): "

if "%CHOICE%"=="1" (
    echo.
    echo [显示所有服务日志]
    echo 按 Ctrl+C 停止
    echo.
    docker-compose logs -f --tail=100
)

if "%CHOICE%"=="2" (
    echo.
    echo [显示后端API日志]
    echo 按 Ctrl+C 停止
    echo.
    docker-compose logs -f --tail=100 backend
)

if "%CHOICE%"=="3" (
    echo.
    echo [显示Celery Worker日志]
    echo 按 Ctrl+C 停止
    echo.
    docker-compose logs -f --tail=100 celery_worker
)

if "%CHOICE%"=="4" (
    echo.
    echo [显示PostgreSQL日志]
    echo 按 Ctrl+C 停止
    echo.
    docker-compose logs -f --tail=100 postgres
)

if "%CHOICE%"=="5" (
    echo.
    echo [显示Redis日志]
    echo 按 Ctrl+C 停止
    echo.
    docker-compose logs -f --tail=100 redis
)

if "%CHOICE%"=="6" (
    echo.
    echo [显示前端日志]
    echo 按 Ctrl+C 停止
    echo.
    docker-compose logs -f --tail=100 frontend
)

if "%CHOICE%"=="0" exit

pause
