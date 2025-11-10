#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试推送数据的问题
"""

import sqlite3
import sys
import os

def test_push_data():
    """测试推送数据"""
    db_path = 'instance/xianyu_data.db'

    if not os.path.exists(db_path):
        print("数据库文件不存在")
        return

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # 获取一条最新记录
        cursor.execute("""
            SELECT product_id, title, price, location, seller_credit,
                   keyword, search_time, created_at
            FROM xianyu_products
            ORDER BY created_at DESC
            LIMIT 1
        """)

        record = cursor.fetchone()
        if not record:
            print("没有数据")
            return

        product_id, title, price, location, seller_credit, keyword, search_time, created_at = record

        print("=== 最新商品数据测试 ===")
        print(f"商品ID: {product_id}")
        print(f"标题: {title}")

        # 测试价格数据
        print(f"\n=== 价格数据测试 ===")
        print(f"原始价格数据: {repr(price)}")
        print(f"价格数据类型: {type(price)}")
        print(f"价格是否为None: {price is None}")

        if price:
            print(f"价格长度: {len(price)}")
            print(f"价格是否为空字符串: {price == ''}")
            print(f"价格去除空白后: '{price.strip()}'")
            print(f"价格去除空白后是否为空: {price.strip() == ''}")

            # 测试编码问题
            try:
                print(f"价格正常显示: {price}")
            except Exception as e:
                print(f"价格显示错误: {e}")

            # 尝试移除特殊字符
            clean_price = price.replace('¥', 'RMB').replace('￥', 'RMB')
            print(f"清理后价格: {clean_price}")
        else:
            print("价格数据为空或None")

        # 测试地区数据
        print(f"\n=== 地区数据测试 ===")
        print(f"原始地区数据: '{location}'")
        print(f"地区数据类型: {type(location)}")
        print(f"地区是否为None: {location is None}")

        if location:
            print(f"地区长度: {len(location)}")
            print(f"地区是否为空字符串: {location == ''}")
            print(f"地区去除空白后: '{location.strip()}'")
            print(f"地区去除空白后是否为空: {location.strip() == ''}")
        else:
            print("地区数据为空或None")

        # 模拟推送逻辑
        print(f"\n=== 模拟推送逻辑测试 ===")
        price_display = price or '面议'
        location_display = location or '未知'

        print(f"推送将显示的价格: {price_display}")
        print(f"推送将显示的地区: {location_display}")

        # 检查是否与推送显示一致
        if price_display == '面议':
            print("⚠️  价格将被显示为'面议'")
        else:
            print("✅ 价格将正常显示")

        if location_display == '未知':
            print("⚠️  地区将被显示为'未知'")
        else:
            print("✅ 地区将正常显示")

        conn.close()

    except Exception as e:
        print(f"测试时出错: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("开始测试推送数据...")
    test_push_data()
    print("\n测试完成")