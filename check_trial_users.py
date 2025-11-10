#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sqlite3

def check_trial_users():
    """检查体验账户数据"""
    try:
        conn = sqlite3.connect('instance/xianyu_data.db')
        cursor = conn.cursor()

        # 检查所有用户
        cursor.execute('SELECT username, role, trial_expires_at, trial_expired, created_at FROM users')
        users = cursor.fetchall()

        print("=== 数据库中的用户信息 ===")
        for user in users:
            username, role, trial_expires_at, trial_expired, created_at = user
            print(f"用户名: {username}")
            print(f"  角色: {role}")
            print(f"  体验到期时间: {trial_expires_at}")
            print(f"  是否过期: {trial_expired}")
            print(f"  创建时间: {created_at}")
            print()

        # 检查体验账户
        cursor.execute('SELECT COUNT(*) FROM users WHERE role = "trial"')
        trial_count = cursor.fetchone()[0]
        print(f"体验账户总数: {trial_count}")

        # 检查管理员账户
        cursor.execute('SELECT COUNT(*) FROM users WHERE role = "admin"')
        admin_count = cursor.fetchone()[0]
        print(f"管理员账户总数: {admin_count}")

        conn.close()

    except Exception as e:
        print(f"检查失败: {e}")

if __name__ == "__main__":
    check_trial_users()