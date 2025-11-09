#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修改超级管理员密码脚本
"""

import sqlite3
import os
from werkzeug.security import generate_password_hash

def change_admin_password():
    """修改超级管理员密码"""
    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'instance', 'xianyu_data.db')

    if not os.path.exists(db_path):
        print(f"数据库文件不存在: {db_path}")
        return False

    try:
        # 连接数据库
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # 检查管理员是否存在
        cursor.execute("SELECT username FROM users WHERE username = ?", ('admin',))
        admin_user = cursor.fetchone()

        if not admin_user:
            print("未找到超级管理员账户")
            return False

        # 生成新密码的哈希
        new_password = "funnyadmin123"
        password_hash = generate_password_hash(new_password)

        # 更新密码
        cursor.execute("UPDATE users SET password_hash = ? WHERE username = ?", (password_hash, 'admin'))
        conn.commit()

        print(f"超级管理员密码已成功修改为: {new_password}")

        # 验证更新
        cursor.execute("SELECT username, role, is_active FROM users WHERE username = ?", ('admin',))
        updated_user = cursor.fetchone()

        if updated_user:
            print(f"账户信息验证成功:")
            print(f"   用户名: {updated_user[0]}")
            print(f"   角色: {updated_user[1]}")
            print(f"   状态: {'活跃' if updated_user[2] else '未激活'}")

        conn.close()
        return True

    except Exception as e:
        print(f"修改密码时出错: {e}")
        return False

if __name__ == "__main__":
    print("=== 修改超级管理员密码 ===")
    success = change_admin_password()
    if success:
        print("\n请使用以下凭据登录:")
        print("用户名: admin")
        print("密码: funnyadmin123")
        print("\n登录页面: http://127.0.0.1:5001/login")
    else:
        print("\n修改失败！")