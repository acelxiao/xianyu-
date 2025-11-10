#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查数据库中的商品数据
"""

import sqlite3
import os
from datetime import datetime

def check_database():
    """检查数据库中的数据"""
    db_path = 'instance/xianyu_data.db'

    if not os.path.exists(db_path):
        print("数据库文件不存在")
        return

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # 检查表是否存在
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()

        if not tables:
            print("数据库中没有表")
            return

        print("数据库中的表:")
        for table in tables:
            print(f"   - {table[0]}")

        # 检查xianyu_products表
        if ('xianyu_products',) in tables:
            cursor.execute("SELECT COUNT(*) FROM xianyu_products")
            count = cursor.fetchone()[0]
            print(f"\nxianyu_products表中共有 {count} 条记录")

            if count > 0:
                # 获取最新的几条记录
                cursor.execute("""
                    SELECT product_id, title, price, location, seller_credit,
                           keyword, search_time, created_at
                    FROM xianyu_products
                    ORDER BY created_at DESC
                    LIMIT 5
                """)

                records = cursor.fetchall()

                print("\n最新5条记录:")
                for i, (product_id, title, price, location, seller_credit, keyword, search_time, created_at) in enumerate(records, 1):
                    print(f"\n记录 {i}:")
                    print(f"   商品ID: {product_id}")
                    print(f"   标题: {title[:50]}..." if len(title) > 50 else f"   标题: {title}")
                    try:
                        print(f"   价格: '{repr(price)}'")
                    except:
                        print("   价格: [编码错误]")
                    try:
                        print(f"   地区: '{location}'")
                    except:
                        print("   地区: [编码错误]")
                    print(f"   卖家信用: '{seller_credit}'")
                    print(f"   关键词: {keyword}")
                    print(f"   搜索时间: {search_time}")
                    print(f"   创建时间: {created_at}")

                    # 检查价格和地区是否为空
                    if not price or price.strip() == '':
                        print("   价格为空")
                    if not location or location.strip() == '':
                        print("   地区为空")
                    else:
                        print(f"   地区长度: {len(location)} 字符")

            # 统计价格和地区数据
            cursor.execute("""
                SELECT
                    COUNT(*) as total,
                    COUNT(CASE WHEN price IS NOT NULL AND price != '' THEN 1 END) as has_price,
                    COUNT(CASE WHEN location IS NOT NULL AND location != '' THEN 1 END) as has_location,
                    COUNT(CASE WHEN price IS NULL OR price = '' THEN 1 END) as no_price,
                    COUNT(CASE WHEN location IS NULL OR location = '' THEN 1 END) as no_location
                FROM xianyu_products
            """)

            stats = cursor.fetchone()
            total, has_price, has_location, no_price, no_location = stats

            print(f"\n数据统计:")
            print(f"   总记录数: {total}")
            print(f"   有价格: {has_price} ({has_price/total*100:.1f}%)" if total > 0 else "   有价格: 0")
            print(f"   有地区: {has_location} ({has_location/total*100:.1f}%)" if total > 0 else "   有地区: 0")
            print(f"   无价格: {no_price} ({no_price/total*100:.1f}%)" if total > 0 else "   无价格: 0")
            print(f"   无地区: {no_location} ({no_location/total*100:.1f}%)" if total > 0 else "   无地区: 0")

        conn.close()

    except Exception as e:
        print(f"检查数据库时出错: {e}")

if __name__ == "__main__":
    print("开始检查数据库...")
    check_database()
    print("\n检查完成")