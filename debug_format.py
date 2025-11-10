#!/usr/bin/env python3
# -*- coding: utf-8 -*-

def clean_location(location_str):
    """清理地区数据"""
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

def test_format():
    # 模拟数据
    location = '河南'
    time_str = '刚刚'

    print("=== 测试地区数据清理 ===")
    print(f"原始地区: {repr(location)}")
    print(f"清理后地区: {repr(clean_location(location))}")

    # 模拟推送内容
    content_parts = [
        f"-💰:元1198  -⏰:{time_str}  -🗺:{clean_location(location)}"
    ]

    content = "\n".join(content_parts)
    print(f"\n推送内容: {repr(content)}")

    # 测试解析
    lines = content.split('\n')
    product_info = {}

    for line in lines:
        print(f"\n处理行: {repr(line)}")
        if '🗺:' in line:
            print("找到地区标识符")
            location_part = line.split('🗺:')[1].strip()
            print(f"提取的地区部分: {repr(location_part)}")

            try:
                clean_location_part = str(location_part).strip()
                print(f"清理后的地区: {repr(clean_location_part)}")
                if clean_location_part:
                    product_info['location'] = clean_location_part
                    print(f"最终地区: {repr(product_info['location'])}")
                else:
                    print("地区为空，设置为未知")
                    product_info['location'] = '未知'
            except Exception as e:
                print(f"处理地区时出错: {e}")
                product_info['location'] = '未知'

    print(f"\n解析结果: {repr(product_info.get('location', '未知'))}")

if __name__ == "__main__":
    test_format()