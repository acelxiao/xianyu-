#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sqlite3
import sys
import os

def debug_actual_push():
    """调试实际推送过程"""
    print("=== 调试实际推送过程 ===")

    # 1. 获取最新商品数据
    conn = sqlite3.connect('instance/xianyu_data.db')
    cursor = conn.cursor()

    # 获取最新的5个商品
    cursor.execute('''
        SELECT product_id, title, price, location, created_at
        FROM xianyu_products
        ORDER BY created_at DESC
        LIMIT 5
    ''')

    products = cursor.fetchall()

    print(f"最新5个商品:")
    for i, (product_id, title, price, location, created_at) in enumerate(products, 1):
        print(f"\n商品{i}:")
        print(f"  ID: {product_id}")
        print(f"  标题: {title[:30]}...")

        # 测试价格处理
        try:
            clean_price = str(price).replace('\xa5', '元').replace('\uffe5', '元')
            print(f"  原始价格: {repr(price)}")
            print(f"  清理后价格: {repr(clean_price)}")
        except Exception as e:
            print(f"  价格处理错误: {e}")
            clean_price = '面议'

        # 测试地区处理
        try:
            clean_location = str(location).strip()
            print(f"  原始地区: {repr(location)}")
            print(f"  清理后地区: {repr(clean_location)}")
        except Exception as e:
            print(f"  地区处理错误: {e}")
            clean_location = '未知'

        # 模拟推送内容生成
        time_str = "刚刚"
        content_parts = [
            "- 商品详情 -",
            title,
            "----------------------------------------",
            f"-💰:{clean_price}  -⏰:{time_str}  -🗺:{clean_location}",
            "----------------------------------------",
            "- 🔗 商品链接：手机链接"
        ]

        content = "\n".join(content_parts)

        print(f"  推送内容:")
        print(f"    {content}")

        # 模拟解析过程（这和企业微信格式化函数相同）
        lines = content.split('\n')
        product_info = {}

        for line in lines:
            if '🗺:' in line:
                try:
                    location_part = line.split('🗺:')[1].strip()
                    clean_location_part = str(location_part).strip()
                    if clean_location_part:
                        product_info['location'] = clean_location_part
                        print(f"  解析结果地区: {repr(product_info['location'])}")
                    else:
                        product_info['location'] = '未知'
                        print(f"  解析结果地区为空，设置为未知")
                except Exception as e:
                    print(f"  解析地区时出错: {e}")
                    product_info['location'] = '未知'

        print(f"  最终地区显示: {product_info.get('location', '未知')}")

    conn.close()

if __name__ == "__main__":
    debug_actual_push()