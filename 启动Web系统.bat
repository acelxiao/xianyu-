@echo off
chcp 65001 >nul
cls
echo ========================================
echo 闲鱼数据管理系统
echo Web后台 + 爬虫功能
echo ========================================
echo.

echo 正在启动Web系统...
echo 首次启动会自动创建数据库
echo.

cd /d "C:\Users\Administrator\Desktop\闲鱼"
python web_app.py

echo.
echo Web系统已关闭！
pause