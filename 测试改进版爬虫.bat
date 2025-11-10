@echo off
chcp 65001 >nul
echo ===================================
echo 改进版最新排序爬虫测试
echo ===================================
echo.
echo 功能说明：
echo - 实现鼠标悬停显示最新选项
echo - 不影响现有真实版爬虫
echo - 有头模式便于观察操作过程
echo.
echo 开始测试...
echo.

cd /d "C:\Users\Administrator\Desktop\闲鱼"
python 改进版最新排序爬虫.py

echo.
echo 测试完成！
echo 结果文件保存在：C:\Users\Administrator\Desktop\闲鱼\测试结果\
echo.
pause