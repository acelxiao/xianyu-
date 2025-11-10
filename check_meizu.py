#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sqlite3

def check_meizu_location():
    conn = sqlite3.connect('instance/xianyu_data.db')
    cursor = conn.cursor()

    cursor.execute('SELECT title, price, location FROM xianyu_products WHERE title LIKE "%魅族20%" LIMIT 1')
    result = cursor.fetchone()

    if result:
        title, price, location = result
        print("魅族20商品数据:")
        print(f"标题长度: {len(title)}")
        print(f"价格数据: {type(price)}")
        print(f"价格是否为None: {price is None}")
        if price:
            print(f"价格长度: {len(price)}")
            print(f"价格是否为空字符串: {price == ''}")
            print(f"价格去除空白后长度: {len(price.strip())}")
        else:
            print("价格为None")

        print(f"地区数据: {type(location)}")
        print(f"地区是否为None: {location is None}")
        if location:
            print(f"地区长度: {len(location)}")
            print(f"地区是否为空字符串: {location == ''}")
            print(f"地区去除空白后长度: {len(location.strip())}")
            print(f"地区内容: '{location}'")
        else:
            print("地区为None")
    else:
        print("未找到魅族20商品")

    conn.close()

if __name__ == "__main__":
    check_meizu_location()