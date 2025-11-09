#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
将体验账户时间设置为2分钟（用于测试倒计时功能）
"""

import sqlite3
import os
from datetime import datetime, timedelta

def set_trial_to_2minutes():
    """将体验账户时间设置为2分钟"""
    db_path = os.path.join(os.path.dirname(__file__), 'instance', 'xianyu_data.db')

    if not os.path.exists(db_path):
        print(f"数据库文件不存在: {db_path}")
        return False

    try:
        # 连接数据库
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # 查找体验账户
        cursor.execute("SELECT username, trial_expires_at FROM users WHERE role = 'trial'")
        trial_users = cursor.fetchall()

        if not trial_users:
            print("未找到体验账户")
            return False

        # 设置体验账户时间为2分钟后
        new_expiry = datetime.utcnow() + timedelta(minutes=2)
        new_expiry_str = new_expiry.strftime('%Y-%m-%d %H:%M:%S')

        cursor.execute("""
            UPDATE users
            SET trial_expires_at = ?, trial_expired = FALSE
            WHERE role = 'trial'
        """, (new_expiry_str,))

        conn.commit()

        # 验证更新
        cursor.execute("SELECT username, trial_expires_at, trial_expired FROM users WHERE role = 'trial'")
        updated_users = cursor.fetchall()

        print("体验账户时间已设置为2分钟：")
        for user in updated_users:
            username, expires_at, expired = user
            print(f"  用户名: {username}")
            print(f"  过期时间: {expires_at}")
            print(f"  已过期: {expired}")
            print()

        # 计算具体的秒数
        now = datetime.utcnow()
        expires_datetime = datetime.strptime(expires_at.split('.')[0], '%Y-%m-%d %H:%M:%S')
        remaining = expires_datetime - now
        seconds = remaining.total_seconds()
        print(f"剩余时间: {seconds:.0f} 秒 ({seconds/60:.1f} 分钟)")

        conn.close()
        return True

    except Exception as e:
        print(f"设置失败: {e}")
        return False

if __name__ == "__main__":
    print("=== 设置体验账户时间为2分钟 ===")
    success = set_trial_to_2minutes()
    if success:
        print("体验账户时间已设置为2分钟，可以测试倒计时功能！")
        print("请使用体验账户登录：用户名 trial，密码 trial123")
        print("登录页面: http://127.0.0.1:5001/login")
    else:
        print("设置失败！")