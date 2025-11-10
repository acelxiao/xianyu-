#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sqlite3
from datetime import datetime, timedelta

def fix_trial_account():
    """修复体验账户的过期时间"""
    try:
        conn = sqlite3.connect('instance/xianyu_data.db')
        cursor = conn.cursor()

        # 为体验账户设置2小时的体验时间（从现在开始）
        expires_at = datetime.now() + timedelta(hours=2)
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
        print(f"体验时长: 2小时")

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
        print(f"修复失败: {e}")

if __name__ == "__main__":
    fix_trial_account()