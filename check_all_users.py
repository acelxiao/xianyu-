#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sqlite3
from datetime import datetime, timedelta

def check_all_users():
    """检查所有用户的详细信息"""
    try:
        conn = sqlite3.connect('instance/xianyu_data.db')
        cursor = conn.cursor()

        # 检查所有用户
        cursor.execute('SELECT username, role, trial_expires_at, trial_expired, is_active, created_at FROM users')
        users = cursor.fetchall()

        print("=== 数据库中所有用户信息 ===")
        for user in users:
            username, role, trial_expires_at, trial_expired, is_active, created_at = user
            print(f"用户名: {username}")
            print(f"  角色: {role}")
            print(f"  是否激活: {is_active}")
            print(f"  体验到期时间: {trial_expires_at}")
            print(f"  是否过期: {trial_expired}")
            print(f"  创建时间: {created_at}")

            # 计算剩余时间
            if role == 'trial' and trial_expires_at:
                try:
                    expires_dt = datetime.strptime(trial_expires_at, '%Y-%m-%d %H:%M:%S')
                    now = datetime.now()
                    remaining = expires_dt - now
                    if remaining.total_seconds() > 0:
                        hours = remaining.seconds // 3600
                        minutes = (remaining.seconds % 3600) // 60
                        print(f"  剩余时间: {hours}小时{minutes}分钟")
                    else:
                        print(f"  剩余时间: 已过期")
                except Exception as e:
                    print(f"  剩余时间: 计算错误 - {e}")
            print()

        conn.close()

    except Exception as e:
        print(f"检查失败: {e}")

if __name__ == "__main__":
    check_all_users()