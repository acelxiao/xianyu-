#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
项目打包脚本 - 用于打包项目以便在其他电脑上部署
"""

import os
import shutil
import zipfile
from datetime import datetime
import sys

def create_package():
    """创建项目压缩包"""
    print("🐟 闲鱼数据管理系统 - 项目打包工具")
    print("=" * 50)

    # 项目名称和版本
    project_name = "xianyu-data-system"
    version = datetime.now().strftime("%Y%m%d_%H%M%S")
    package_name = f"{project_name}_{version}"

    print(f"📦 打包名称：{package_name}")
    print(f"📅 打包时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # 需要包含的文件和目录
    include_files = [
        "web_app.py",
        "requirements.txt",
        "deploy_start.py",
        "check_deployment.py",
        "change_admin_password.py",
        "Cookie获取指南.txt",
        "完整部署教程.md",
        "部署说明.md",
        "README.md",
        "故障排除指南.md",
        "系统设置功能说明.md",
        "新功能说明.md",
        "启动Web系统.bat",
        "启动系统.bat"
    ]

    include_dirs = [
        "templates",
        "static",
        "instance"
    ]

    # 排除的文件和目录
    exclude_patterns = [
        "__pycache__",
        "*.pyc",
        ".git",
        "xianyu_data.db",
        "logs",
        "uploads",
        "test_*.py",
        "debug_*.py",
        "check_*.py",
        "fix_*.py",
        "reset_*.py",
        "set_*.py",
        "extend_*.py",
        "add_*.py",
        "*.png",
        "*.xlsx",
        "测试结果",
        "改进版测试结果",
        "检测_*.png"
    ]

    # 创建临时目录
    temp_dir = package_name
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)
    os.makedirs(temp_dir)

    try:
        print("📁 复制文件...")

        # 复制文件
        for file in include_files:
            if os.path.exists(file):
                shutil.copy2(file, os.path.join(temp_dir, file))
                print(f"  ✅ {file}")
            else:
                print(f"  ⚠️  跳过不存在的文件：{file}")

        # 复制目录
        for dir_name in include_dirs:
            if os.path.exists(dir_name):
                dest_dir = os.path.join(temp_dir, dir_name)
                if dir_name == "instance":
                    # 复制instance目录但不包含数据库文件
                    os.makedirs(dest_dir, exist_ok=True)
                    for item in os.listdir(dir_name):
                        if item != "xianyu_data.db" and not item.startswith("."):
                            src_path = os.path.join(dir_name, item)
                            dest_path = os.path.join(dest_dir, item)
                            if os.path.isdir(src_path):
                                shutil.copytree(src_path, dest_path, ignore=shutil.ignore_patterns("__pycache__"))
                            else:
                                shutil.copy2(src_path, dest_path)
                else:
                    # 复制其他目录
                    shutil.copytree(dir_name, dest_dir, ignore=shutil.ignore_patterns(*exclude_patterns))
                print(f"  ✅ {dir_name}/")
            else:
                print(f"  ⚠️  跳过不存在的目录：{dir_name}")

        print()
        print("📦 创建压缩包...")

        # 创建ZIP文件
        zip_filename = f"{package_name}.zip"
        with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(temp_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, temp_dir)
                    zipf.write(file_path, arcname)

        print(f"✅ 压缩包创建成功：{zip_filename}")
        print(f"📊 压缩包大小：{os.path.getsize(zip_filename) / 1024 / 1024:.1f} MB")

        # 创建部署说明
        readme_content = f"""# 闲鱼数据管理系统 - 部署包

## 📦 包信息
- **打包时间**：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- **版本**：{version}

## 🚀 快速部署

### 1. 解压文件
将本压缩包解压到任意目录

### 2. 运行部署检查（推荐）
```bash
python check_deployment.py
```

### 3. 一键部署
```bash
python deploy_start.py
```

### 4. 访问系统
- **系统地址**：http://127.0.0.1:5000
- **登录页面**：http://127.0.0.1:5000/login

## 👤 默认账户
- **管理员**：admin / funnyadmin123
- **体验账户**：trial / trial123

## 📋 部署要求
- Python 3.8+
- 4GB+ RAM
- 2GB+ 磁盘空间
- 网络连接

## 📖 详细文档
- `完整部署教程.md` - 详细部署指南
- `部署说明.md` - 简明部署说明
- `故障排除指南.md` - 常见问题解决

## ⚠️ 注意事项
1. 首次部署需要安装Playwright浏览器
2. 确保网络连接正常
3. 防火墙需允许端口5000访问

祝您使用愉快！🎉
"""

        with open(os.path.join(temp_dir, "README_部署包.txt"), "w", encoding="utf-8") as f:
            f.write(readme_content)

        print("✅ 部署说明文件创建完成")

    except Exception as e:
        print(f"❌ 打包失败：{e}")
        return False

    finally:
        # 清理临时目录
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)

    print()
    print("🎉 打包完成！")
    print(f"📁 文件位置：{os.path.abspath(zip_filename)}")
    print()
    print("📋 下一步：")
    print("1. 将压缩包复制到目标电脑")
    print("2. 解压缩到目标目录")
    print("3. 运行 python deploy_start.py 开始部署")
    print()
    print("🔧 如需检查环境，可先运行：")
    print("   python check_deployment.py")

    return True

def main():
    """主函数"""
    try:
        create_package()
    except KeyboardInterrupt:
        print("\n❌ 打包被用户取消")
    except Exception as e:
        print(f"❌ 打包失败：{e}")
        input("按任意键退出...")

if __name__ == "__main__":
    main()