#!/usr/bin/env python3
# -*- coding: utf-8 -*-

def simple_test():
    # 测试当前数据库中的实际数据
    import sqlite3

    conn = sqlite3.connect('instance/xianyu_data.db')
    cursor = conn.cursor()

    # 获取最新的魅族商品
    cursor.execute('SELECT title, price, location FROM xianyu_products WHERE title LIKE "%魅族20%" LIMIT 1')
    result = cursor.fetchone()

    if result:
        title, price, location = result

        print("魅族商品数据检查:")
        print("标题:", title[:30] + "...")
        print("价格:", type(price), len(price) if price else "None")
        print("地区:", type(location), len(location) if location else "None")

        # 模拟推送逻辑
        print("\n推送数据处理:")

        # 价格处理
        try:
            clean_price = str(price).replace('\xa5', '元').replace('\uffe5', '元')
            print("清理后价格:", clean_price)
        except Exception as e:
            print("价格处理错误:", e)
            clean_price = '面议'

        # 地区处理
        try:
            clean_location = str(location).strip()
            print("清理后地区:", clean_location)
        except Exception as e:
            print("地区处理错误:", e)
            clean_location = '未知'

        # 模拟格式化
        content = f"-价格:{clean_price}  -时间:刚刚  -地区:{clean_location}"
        print("\n推送内容:", content)

        # 模拟解析
        print("\n解析测试:")
        if '地区:' in content:
            location_part = content.split('地区:')[1].strip()
            print("提取的地区:", location_part)

    conn.close()

if __name__ == "__main__":
    simple_test()