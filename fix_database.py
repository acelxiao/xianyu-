#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库修复脚本 - 添加缺失的trial_expired列
"""

import sqlite3
import os

def fix_database():
    """修复数据库结构，添加缺失的trial_expired列"""
    db_path = os.path.join(os.path.dirname(__file__), 'instance', 'xianyu_data.db')

    if not os.path.exists(db_path):
        print(f"数据库文件不存在: {db_path}")
        return False

    try:
        # 连接数据库
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # 检查列是否存在
        cursor.execute("PRAGMA table_info(users)")
        columns = cursor.fetchall()
        column_names = [col[1] for col in columns]

        if 'trial_expired' not in column_names:
            print("添加缺失的trial_expired列...")
            cursor.execute("ALTER TABLE users ADD COLUMN trial_expired BOOLEAN DEFAULT FALSE")
            conn.commit()
            print("trial_expired列添加成功")
        else:
            print("trial_expired列已存在")

        # 再次检查表结构
        cursor.execute("PRAGMA table_info(users)")
        columns = cursor.fetchall()
        print("\n当前users表结构:")
        for col in columns:
            print(f"  {col[1]} ({col[2]}) - 默认值: {col[4]}")

        conn.close()
        return True

    except Exception as e:
        print(f"修复数据库失败: {e}")
        return False

if __name__ == "__main__":
    print("=== 数据库修复工具 ===")
    success = fix_database()
    if success:
        print("\n数据库修复完成！")
    else:
        print("\n数据库修复失败！")