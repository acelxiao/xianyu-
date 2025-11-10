@echo off
chcp 65001 >nul
echo ===================================
echo 测试集成版爬虫 - 鼠标悬停功能
echo ===================================
echo.
echo 功能说明：
echo - 已将鼠标悬停功能集成到正式版爬虫
echo - 优先尝试悬停在'新发布'状态栏
echo - 包含多重备用方案确保成功率
echo.
echo 开始测试集成版爬虫...
echo.

cd /d "C:\Users\Administrator\Desktop\闲鱼"
echo [测试] 打开网页进行手动测试...
start http://127.0.0.1:5000/scrape

echo.
echo 测试说明：
echo 1. 在网页中输入关键词并开始爬取
echo 2. 观察控制台日志，查看排序设置过程
echo 3. 特别注意是否成功使用鼠标悬停功能
echo.
echo 测试完成后查看日志输出...
pause