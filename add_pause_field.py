#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sqlite3

def add_pause_field():
    """为体验账户添加暂停状态字段"""
    try:
        conn = sqlite3.connect('instance/xianyu_data.db')
        cursor = conn.cursor()

        # 添加 paused 字段（0=正常计时，1=暂停计时）
        cursor.execute('ALTER TABLE users ADD COLUMN paused INTEGER DEFAULT 0')

        # 添加 paused_at 字段（记录暂停时间）
        cursor.execute('ALTER TABLE users ADD COLUMN paused_at TEXT')

        # 添加 paused_remaining_minutes 字段（记录暂停时的剩余分钟数）
        cursor.execute('ALTER TABLE users ADD COLUMN paused_remaining_minutes INTEGER DEFAULT 0')

        conn.commit()
        conn.close()

        print("成功添加暂停功能字段")
        print("   - paused: 暂停状态（0=正常，1=暂停）")
        print("   - paused_at: 暂停时间")
        print("   - paused_remaining_minutes: 暂停时剩余分钟数")

    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e):
            print("字段已存在，无需添加")
        else:
            print(f"添加字段失败: {e}")
    except Exception as e:
        print(f"操作失败: {e}")

if __name__ == "__main__":
    add_pause_field()