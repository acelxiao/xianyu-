#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sqlite3
import requests
import json

def final_verification():
    print("=== 最终验证测试 ===")

    # 1. 验证数据库数据
    conn = sqlite3.connect('instance/xianyu_data.db')
    cursor = conn.cursor()

    cursor.execute('SELECT COUNT(*) FROM xianyu_products')
    total_count = cursor.fetchone()[0]
    print(f"1. 数据库中总商品数: {total_count}")

    cursor.execute('SELECT COUNT(*) FROM xianyu_products WHERE location IS NOT NULL AND location != ""')
    has_location_count = cursor.fetchone()[0]
    print(f"2. 有地区数据的商品数: {has_location_count}")
    print(f"   有地区数据比例: {has_location_count/total_count*100:.1f}%" if total_count > 0 else "   有地区数据比例: 0%")

    # 3. 获取一个具体商品进行测试
    cursor.execute('SELECT title, price, location FROM xianyu_products ORDER BY created_at DESC LIMIT 1')
    result = cursor.fetchone()

    if result:
        title, price, location = result
        print(f"3. 最新商品数据:")
        print(f"   标题长度: {len(title)}")
        print(f"   价格数据: {type(price)}, 长度: {len(price) if price else 0}")
        print(f"   地区数据: {type(location)}, 长度: {len(location) if location else 0}")
        print(f"   地区内容: '{location}'")

        # 4. 模拟推送处理逻辑
        print(f"\n4. 模拟推送处理:")

        # 价格处理
        def clean_price(price_str):
            if not price_str:
                return '面议'
            try:
                clean = str(price_str).replace('\xa5', '元').replace('\uffe5', '元')
                if clean.strip():
                    return clean.strip()
                else:
                    return '面议'
            except:
                return '面议'

        # 地区处理
        def clean_location(location_str):
            if not location_str:
                return '未知'
            try:
                clean = str(location_str).strip()
                if clean:
                    return clean
                else:
                    return '未知'
            except:
                return '未知'

        test_price = clean_price(price)
        test_location = clean_location(location)

        print(f"   处理后价格: '{test_price}'")
        print(f"   处理后地区: '{test_location}'")

        # 5. 验证实际推送
        print(f"\n5. 测试实际推送...")
        try:
            response = requests.post(
                "http://127.0.0.1:5000/api/test-latest-products",
                headers={"Content-Type": "application/json"},
                json={"config_id": 1, "count": 1},
                timeout=10
            )

            if response.status_code == 200:
                result = response.json()
                print(f"   推送测试结果: {result.get('success', False)}")
                print(f"   返回消息: {result.get('message', '')}")
            else:
                print(f"   推送失败，状态码: {response.status_code}")
        except Exception as e:
            print(f"   推送测试异常: {e}")

    conn.close()
    print(f"\n=== 验证完成 ===")

if __name__ == "__main__":
    final_verification()