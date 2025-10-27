@echo off
chcp 65001 >nul
REM ========================================
REM   CMS自动化系统 - 重启脚本
REM ========================================

echo.
echo ========================================
echo   重启 CMS自动化系统
echo ========================================
echo.

echo [1/2] 停止服务...
docker-compose down

echo.
echo [2/2] 启动服务...
docker-compose up -d

echo.
echo [√] 系统已重启
echo.
echo 等待服务就绪...
timeout /t 10 >nul

echo.
echo 系统已就绪！
echo   前端: http://localhost:3000
echo   API:  http://localhost:8000/docs
echo.
pause
