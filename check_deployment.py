#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
部署检查脚本 - 检查系统环境是否满足部署要求
"""

import sys
import os
import subprocess
import shutil

def check_python_version():
    """检查Python版本"""
    print("检查Python版本...")
    version = sys.version_info
    if version >= (3, 8):
        print(f"[OK] Python版本符合要求：{version.major}.{version.minor}.{version.micro}")
        return True
    else:
        print(f"[ERROR] Python版本过低：{version.major}.{version.minor}.{version.micro}，需要3.8+")
        return False

def check_pip():
    """检查pip是否可用"""
    print("检查pip...")
    try:
        subprocess.run([sys.executable, "-m", "pip", "--version"],
                      capture_output=True, check=True)
        print("[OK] pip可用")
        return True
    except subprocess.CalledProcessError:
        print("[ERROR] pip不可用")
        return False

def check_files():
    """检查必要文件是否存在"""
    print("检查项目文件...")
    required_files = [
        "web_app.py",
        "requirements.txt",
        "templates/base.html",
        "templates/index.html",
        "static/css/main.css"
    ]

    missing_files = []
    for file in required_files:
        if not os.path.exists(file):
            missing_files.append(file)

    if missing_files:
        print(f"[ERROR] 缺少必要文件：{', '.join(missing_files)}")
        return False
    else:
        print("[OK] 所有必要文件存在")
        return True

def check_directories():
    """检查并创建目录"""
    print("检查目录结构...")
    directories = ["instance", "logs", "uploads", "static/uploads"]

    for directory in directories:
        if not os.path.exists(directory):
            try:
                os.makedirs(directory)
                print(f"[INFO] 创建目录：{directory}")
            except Exception as e:
                print(f"[ERROR] 无法创建目录{directory}：{e}")
                return False
        else:
            print(f"[INFO] 目录存在：{directory}")

    return True

def check_dependencies():
    """检查依赖是否可以安装"""
    print("检查依赖安装...")
    try:
        result = subprocess.run([sys.executable, "-m", "pip", "show", "Flask"],
                              capture_output=True, text=True)
        if result.returncode == 0:
            print("[OK] Flask已安装")
        else:
            print("[WARN] Flask未安装，将使用requirements.txt安装")
    except Exception as e:
        print(f"[WARN] 无法检查Flask：{e}")

    return True

def check_playwright():
    """检查Playwright浏览器"""
    print("检查Playwright浏览器...")
    try:
        result = subprocess.run([sys.executable, "-m", "playwright", "install", "--dry-run"],
                              capture_output=True, text=True)
        if result.returncode == 0:
            print("[OK] Playwright可以安装")
            return True
        else:
            print("[WARN] Playwright安装可能需要额外配置")
            return True  # 不阻止部署
    except Exception as e:
        print(f"[WARN] 无法检查Playwright：{e}")
        return True

def check_port():
    """检查端口是否可用"""
    print("检查端口5000...")
    try:
        import socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = sock.connect_ex(('127.0.0.1', 5000))
        sock.close()

        if result == 0:
            print("[WARN] 端口5000已被占用")
            return False
        else:
            print("[OK] 端口5000可用")
            return True
    except Exception as e:
        print(f"[WARN] 无法检查端口：{e}")
        return True

def generate_report():
    """生成部署报告"""
    print("\n" + "="*60)
    print("部署环境检查报告")
    print("="*60)

    checks = [
        ("Python版本", check_python_version),
        ("pip包管理器", check_pip),
        ("项目文件", check_files),
        ("目录结构", check_directories),
        ("依赖包", check_dependencies),
        ("Playwright", check_playwright),
        ("端口5000", check_port)
    ]

    passed = 0
    total = len(checks)

    for name, check_func in checks:
        if check_func():
            passed += 1

    print(f"\n[SUMMARY] 检查结果：{passed}/{total} 项通过")

    if passed == total:
        print("[SUCCESS] 环境检查完全通过，可以开始部署！")
        print("\n[INFO] 快速部署命令：")
        print("   python deploy_start.py")
        print("\n[INFO] 部署后访问地址：")
        print("   http://127.0.0.1:5000")
        return True
    else:
        print("[WARNING] 发现问题，请根据上述提示解决后再部署")
        return False

def main():
    """主函数"""
    print("闲鱼数据管理系统 - 部署环境检查")
    print("="*60)

    success = generate_report()

    if success:
        print("\n[TIPS] 提示：")
        print("1. 确保网络连接正常（下载依赖需要）")
        print("2. 建议使用虚拟环境部署")
        print("3. 首次部署需要安装Playwright浏览器")

        choice = input("\n是否现在开始部署？(y/n): ").lower().strip()
        if choice in ['y', 'yes', '是']:
            print("\n[INFO] 启动部署脚本...")
            try:
                subprocess.run([sys.executable, "deploy_start.py"], check=True)
            except subprocess.CalledProcessError as e:
                print(f"[ERROR] 部署失败：{e}")
            except FileNotFoundError:
                print("[ERROR] 找不到deploy_start.py文件")
    else:
        print("\n[ACTION] 请解决上述问题后重新运行检查")
        input("按任意键退出...")

if __name__ == "__main__":
    main()