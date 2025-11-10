#!/usr/bin/env python3
# -*- coding: utf-8 -*-

def test_emoji_parsing():
    # 模拟实际推送内容
    content = """-💰:元1198  -⏰:刚刚  -🗺:河南
----------------------------------------
- 🔗 商品链接：手机链接"""

    print("=== Emoji解析测试 ===")
    print("原始内容:", repr(content))
    print()

    lines = content.split('\n')
    product_info = {}

    for i, line in enumerate(lines):
        print(f"行 {i+1}: {repr(line)}")

        # 测试价格解析
        if '💰:' in line:
            print("  -> 找到价格标识符")
            try:
                price_part = line.split('💰:')[1].strip()
                print(f"  -> 价格部分: {repr(price_part)}")

                if '  -⏰:' in price_part:
                    price_part = price_part.split('  -⏰:')[0].strip()
                elif '  -' in price_part:
                    price_part = price_part.split('  -')[0].strip()

                print(f"  -> 清理后价格: {repr(price_part)}")
                if price_part:
                    product_info['price'] = price_part
            except Exception as e:
                print(f"  -> 价格解析错误: {e}")

        # 测试时间解析
        elif '⏰:' in line:
            print("  -> 找到时间标识符")
            try:
                time_part = line.split('⏰:')[1].strip()
                print(f"  -> 时间部分: {repr(time_part)}")

                if '  -🗺:' in time_part:
                    time_part = time_part.split('  -🗺:')[0].strip()
                elif '  -' in time_part:
                    time_part = time_part.split('  -')[0].strip()

                print(f"  -> 清理后时间: {repr(time_part)}")
                if time_part:
                    product_info['time'] = time_part
            except Exception as e:
                print(f"  -> 时间解析错误: {e}")

        # 测试地区解析
        elif '🗺:' in line:
            print("  -> 找到地区标识符")
            try:
                location_part = line.split('🗺:')[1].strip()
                print(f"  -> 地区部分: {repr(location_part)}")

                # 尝试清理地区数据
                clean_location = str(location_part).strip()
                print(f"  -> 清理后地区: {repr(clean_location)}")

                if clean_location:
                    product_info['location'] = clean_location
                else:
                    product_info['location'] = '未知'

                print(f"  -> 最终地区: {repr(product_info['location'])}")
            except Exception as e:
                print(f"  -> 地区解析错误: {e}")

    print()
    print("=== 解析结果 ===")
    print(f"价格: {repr(product_info.get('price', '面议'))}")
    print(f"时间: {repr(product_info.get('time', '刚刚'))}")
    print(f"地区: {repr(product_info.get('location', '未知'))}")

if __name__ == "__main__":
    test_emoji_parsing()