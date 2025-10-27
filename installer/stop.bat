@echo off
chcp 65001 >nul
REM ========================================
REM   CMS自动化系统 - 停止脚本
REM ========================================

echo.
echo ========================================
echo   停止 CMS自动化系统
echo ========================================
echo.

echo 正在停止所有服务...
docker-compose down

echo.
echo [√] 系统已停止
echo.

set /p REMOVE_DATA="是否删除数据库数据? (y/N): "
if /i "%REMOVE_DATA%"=="y" (
    echo.
    echo [警告] 正在删除数据...
    docker-compose down -v
    echo [√] 数据已删除
)

echo.
pause
