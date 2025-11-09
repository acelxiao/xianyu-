#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
重置体验账户为首次登录状态（清空过期时间，让首次登录时开始3天倒计时）
"""

import sqlite3
import os

def reset_trial_for_first_login():
    """重置体验账户为首次登录状态"""
    db_path = os.path.join(os.path.dirname(__file__), 'instance', 'xianyu_data.db')

    if not os.path.exists(db_path):
        print(f"数据库文件不存在: {db_path}")
        return False

    try:
        # 连接数据库
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # 重置体验账户：清空过期时间，重置过期状态
        cursor.execute("""
            UPDATE users
            SET trial_expires_at = NULL, trial_expired = FALSE
            WHERE role = 'trial'
        """)

        conn.commit()

        # 验证更新
        cursor.execute("SELECT username, trial_expires_at, trial_expired FROM users WHERE role = 'trial'")
        updated_users = cursor.fetchall()

        print("体验账户已重置为首次登录状态：")
        for user in updated_users:
            username, expires_at, expired = user
            print(f"  用户名: {username}")
            print(f"  过期时间: {expires_at} (NULL - 首次登录时设置)")
            print(f"  已过期: {expired}")
            print()

        print("体验账户将在首次登录时开始3天倒计时！")

        conn.close()
        return True

    except Exception as e:
        print(f"重置失败: {e}")
        return False

if __name__ == "__main__":
    print("=== 重置体验账户为首次登录状态 ===")
    success = reset_trial_for_first_login()
    if success:
        print("重置成功！体验账户现在将在首次登录时开始3天倒计时。")
        print("登录页面: http://127.0.0.1:5001/login")
    else:
        print("重置失败！")