#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sqlite3
from datetime import datetime, timedelta

def extend_trial_to_3_days():
    """将体验账户延长到3天"""
    try:
        conn = sqlite3.connect('instance/xianyu_data.db')
        cursor = conn.cursor()

        # 将体验账户设置为3天（从现在开始）
        expires_at = datetime.now() + timedelta(days=3)
        expires_at_str = expires_at.strftime('%Y-%m-%d %H:%M:%S')

        # 更新体验账户的过期时间
        cursor.execute('''
            UPDATE users
            SET trial_expires_at = ?, trial_expired = 0
            WHERE role = 'trial'
        ''', (expires_at_str,))

        conn.commit()
        conn.close()

        print(f"体验账户过期时间已设置为: {expires_at_str}")
        print(f"体验时长: 3天")

        # 计算准确的剩余时间
        remaining = expires_at - datetime.now()
        days = remaining.days
        hours = remaining.seconds // 3600
        minutes = (remaining.seconds % 3600) // 60
        print(f"准确剩余时间: {days}天{hours}小时{minutes}分钟")

        # 验证更新
        conn = sqlite3.connect('instance/xianyu_data.db')
        cursor = conn.cursor()
        cursor.execute('SELECT username, role, trial_expires_at, trial_expired FROM users WHERE role = "trial"')
        user = cursor.fetchone()
        if user:
            username, role, trial_expires_at, trial_expired = user
            print(f"验证成功 - 用户名: {username}, 过期时间: {trial_expires_at}, 是否过期: {trial_expired}")
        conn.close()

    except Exception as e:
        print(f"设置失败: {e}")

if __name__ == "__main__":
    extend_trial_to_3_days()