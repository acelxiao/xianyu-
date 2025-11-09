#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
重置体验账户时间为3天（恢复正常设置）
"""

import sqlite3
import os
from datetime import datetime, timedelta

def reset_trial_to_3days():
    """重置体验账户时间为3天"""
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

        # 重置体验账户时间为3天后
        new_expiry = datetime.utcnow() + timedelta(days=3)
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

        print("体验账户时间已重置为3天：")
        for user in updated_users:
            username, expires_at, expired = user
            print(f"  用户名: {username}")
            print(f"  过期时间: {expires_at}")
            print(f"  已过期: {expired}")
            print()

        # 计算具体的小时数
        now = datetime.utcnow()
        expires_datetime = datetime.strptime(expires_at.split('.')[0], '%Y-%m-%d %H:%M:%S')
        remaining = expires_datetime - now
        hours = remaining.total_seconds() / 3600
        print(f"剩余时间: {hours:.1f} 小时 ({remaining.days} 天 {remaining.seconds // 3600} 小时)")

        conn.close()
        return True

    except Exception as e:
        print(f"重置失败: {e}")
        return False

if __name__ == "__main__":
    print("=== 重置体验账户时间为3天 ===")
    success = reset_trial_to_3days()
    if success:
        print("体验账户时间已恢复正常设置（3天）！")
    else:
        print("重置失败！")