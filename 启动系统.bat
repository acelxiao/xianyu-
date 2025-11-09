@echo off
chcp 65001 >nul
title 闲鱼数据管理系统
color 0A

echo.
echo ========================================
echo    闲鱼数据管理系统 - 启动程序
echo ========================================
echo.

echo 正在启动系统，请稍候...
echo.

python deploy_start.py

echo.
echo 系统已停止运行
pause