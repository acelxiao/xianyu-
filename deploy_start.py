#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
闲鱼数据管理系统 - 部署启动脚本
"""

import os
import sys
import subprocess
import sqlite3
from datetime import datetime

def check_python_version():
    """检查Python版本"""
    if sys.version_info < (3, 7):
        print("❌ 错误：需要Python 3.7或更高版本")
        print(f"   当前版本：{sys.version}")
        return False
    print(f"✅ Python版本检查通过：{sys.version}")
    return True

def install_dependencies():
    """安装依赖包"""
    print("📦 正在安装依赖包...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ 依赖包安装完成")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ 依赖包安装失败：{e}")
        return False

def check_directories():
    """检查并创建必要的目录"""
    directories = ['instance', 'logs', 'uploads']
    for directory in directories:
        if not os.path.exists(directory):
            os.makedirs(directory)
            print(f"📁 创建目录：{directory}")
        else:
            print(f"📁 目录存在：{directory}")
    return True

def init_database():
    """初始化数据库"""
    print("🗄️ 正在初始化数据库...")
    try:
        from web_app import app, db

        with app.app_context():
            # 创建所有表
            db.create_all()

            # 检查是否存在管理员账户
            from web_app import User
            admin_user = User.query.filter_by(username='admin').first()

            if not admin_user:
                # 创建默认管理员账户
                admin_user = User(
                    username='admin',
                    email='admin@example.com',
                    role='admin',
                    is_active=True
                )
                admin_user.set_password('funnyadmin123')
                db.session.add(admin_user)
                print("👤 创建默认管理员账户：admin / funnyadmin123")

            # 检查是否存在体验账户
            trial_user = User.query.filter_by(username='trial').first()

            if not trial_user:
                # 创建体验账户（首次登录时开始3天倒计时）
                trial_user = User(
                    username='trial',
                    email='trial@example.com',
                    role='trial',
                    is_active=True,
                    trial_expires_at=None,  # 首次登录时设置
                    trial_expired=False
                )
                trial_user.set_password('trial123')
                db.session.add(trial_user)
                print("👤 创建体验账户：trial / trial123（首次登录开始3天倒计时）")

            db.session.commit()
            print("✅ 数据库初始化完成")
            return True

    except Exception as e:
        print(f"❌ 数据库初始化失败：{e}")
        return False

def start_server():
    """启动服务器"""
    print("🚀 正在启动服务器...")
    try:
        # 设置环境变量
        os.environ['FLASK_ENV'] = 'production'
        os.environ['FLASK_DEBUG'] = 'False'

        print("🌐 服务器启动中...")
        print("📍 访问地址：http://127.0.0.1:5001")
        print("📍 登录页面：http://127.0.0.1:5001/login")
        print("📋 默认账户：")
        print("   管理员：admin / funnyadmin123")
        print("   体验账户：trial / trial123")
        print("⚠️  按 Ctrl+C 停止服务器")
        print("=" * 50)

        # 启动Flask应用
        from web_app import app
        app.run(
            host='0.0.0.0',  # 允许外部访问
            port=5001,
            debug=False
        )

    except KeyboardInterrupt:
        print("\n👋 服务器已停止")
    except Exception as e:
        print(f"❌ 服务器启动失败：{e}")

def main():
    """主函数"""
    print("=" * 50)
    print("🐟 闲鱼数据管理系统 - 部署启动")
    print("=" * 50)
    print(f"⏰ 启动时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 50)

    # 检查Python版本
    if not check_python_version():
        input("按任意键退出...")
        return

    # 检查并创建目录
    if not check_directories():
        input("按任意键退出...")
        return

    # 安装依赖包
    if not install_dependencies():
        input("按任意键退出...")
        return

    # 初始化数据库
    if not init_database():
        input("按任意键退出...")
        return

    # 启动服务器
    start_server()

if __name__ == "__main__":
    main()