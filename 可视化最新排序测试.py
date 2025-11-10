#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
可视化最新排序功能测试 - 有头模式
用于验证爬取的确实是最新发布的商品
"""

import asyncio
import pandas as pd
from datetime import datetime
from playwright.async_api import async_playwright
import re
import random
import time
import os

# 配置日志
import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

class VisualLatestSortTest:
    """可视化最新排序测试"""

    def __init__(self, cookie_string=None):
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None
        self.results = []

        # Cookie字符串
        if cookie_string:
            self.cookie_string = cookie_string
        else:
            self.cookie_string = 'cna=Gj2PIVvfVnUCATytZ6pBVuaC; t=a5122db3552745fae77dcc8bd999c78f; tracknick=xy227407743954; havana_lgc2_77=eyJoaWQiOjIyMjEwNTk1MTk1MDMsInNnIjoiYzYyMTFiYmI1MzJmOTc4MzllNzYyYzVlMWRhZDUzMTciLCJzaXRlIjo3NywidG9rZW4iOiIxVjVFQkNLN2UxRjZLUVpBMTZVMWVxQSJ9; _hvn_lgc_=77; havana_lgc_exp=1764746274257; cookie2=14200db952d961688a60cf14acb2ffb2; mtop_partitioned_detect=1; _m_h5_tk=baac0bed28387029452647868b393313_1762608074777; _m_h5_tk_enc=9566c16833cd791ce48c9fb9dae04e6c; xlly_s=1; _samesite_flag_=true; sdkSilent=1762684756836; _tb_token_=e3e53eb565e; sgcookie=E100ISMaftFoirZTZm4%2BnVITm9pRarQlQg5i%2By4fQHQfufeaOs%2BaihilB0wuO0uGeoUkWGY0o6rM2QQXIYvatAXVZ%2F%2F9lcEFE791QN5mQNWs7rY%3D; csg=9b38caf0; unb=2221059519503; tfstk=gEBnQADA86RQkekItuvQtaO3HNVOdp9WTaHJyLLz_F8sJ2Hd44bl7ZIKpTIyrab95aA7AULyraIP9leYHMsBFLkuk-eAje-FMwmezBryQ3K8XH8UqSDeFLzYWfHyO-v5-eVoYQSaj3K-TH7rUdkw53cETa8e_V-DcL8Pza8Z7ntrL38rLRow53JyYaJzjd862L8PzLrGbAgIUEXPCOz5ve24kOphIHAHuGVjEYlvvqLcYkDSeOfMtEykSYkPIHjy7n1sn7LVGedvkNytKLjwqwLOu-kMQIff23b3KvJd_16BpOUmcBbkJIW9sSoGopbkg9Ri4YIhvUJMbtr-GFBMJaWH_oHDwdWvgp5T1ydJKnbPdwmoUZSOD9O1Er0wP6KXQnIQKAvVY3SzNflqiCDWbuBZNbOefhYvJIZhodfcCOZgjjNBThtLklqiNbOefhYYjlcjPB-6vrC..'

    def log_info(self, message):
        """记录信息"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[可视化测试 {timestamp}] {message}")

    async def setup_browser(self, headless=False):
        """设置浏览器 - 默认有头模式"""
        self.log_info("正在设置可视化浏览器（有头模式）...")

        try:
            self.playwright = await async_playwright().start()

            # 浏览器配置 - 适合可视化观察
            browser_args = [
                '--no-sandbox',
                '--disable-blink-features=AutomationControlled',
                '--disable-dev-shm-usage',
                '--disable-extensions',
                '--no-first-run',
                '--disable-default-apps',
                '--disable-sync'
            ]

            # 有头模式，窗口大小适中便于观察
            self.browser = await self.playwright.chromium.launch(
                headless=headless,  # 设置为False启用有头模式
                args=browser_args,
                slow_mo=1000  # 减慢操作速度便于观察
            )

            # 创建浏览器上下文（桌面端模拟，便于观察）
            self.context = await self.browser.new_context(
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                viewport={'width': 1366, 'height': 768},  # 桌面分辨率
                device_scale_factor=1,
                is_mobile=False,
                has_touch=False
            )

            # 创建页面
            self.page = await self.context.new_page()

            # 添加反检测脚本
            await self.page.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
                window.chrome = {runtime: {}, loadTimes: function() {}, csi: function() {}};
                Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]};
                Object.defineProperty(navigator, 'languages', {get: () => ['zh-CN', 'zh', 'en']};
                Object.defineProperty(navigator, 'automation', {get: () => undefined});
            """)

            self.log_info("可视化浏览器设置成功！您将能够看到整个操作过程")
            return True

        except Exception as e:
            self.log_info(f"浏览器设置失败: {str(e)}")
            return False

    async def apply_cookies_and_navigate(self):
        """应用Cookie并导航到搜索页面"""
        self.log_info("正在应用Cookie并访问闲鱼...")

        try:
            # 访问闲鱼主页
            self.log_info("访问咸鱼主页...")
            await self.page.goto("https://www.goofish.com", timeout=30000)
            await asyncio.sleep(3)

            # 显示当前页面状态
            current_url = self.page.url
            self.log_info(f"当前页面: {current_url}")

            # 解析并设置Cookie
            cookies = []
            for item in self.cookie_string.split(';'):
                if '=' in item:
                    key, value = item.strip().split('=', 1)
                    cookies.append({
                        'name': key.strip(),
                        'value': value.strip(),
                        'domain': '.goofish.com',
                        'path': '/'
                    })

            self.log_info(f"准备设置 {len(cookies)} 个Cookie")
            await self.context.add_cookies(cookies)

            # 刷新页面使Cookie生效
            await self.page.reload()
            await asyncio.sleep(3)

            self.log_info("Cookie应用成功，已重新加载页面")
            return True

        except Exception as e:
            self.log_info(f"Cookie应用失败: {str(e)}")
            return False

    async def demonstrate_search_and_sort(self, keyword="手机"):
        """演示搜索和排序过程"""
        self.log_info(f"=== 开始搜索演示 ===")
        self.log_info(f"搜索关键词: {keyword}")

        try:
            # 第一步：寻找搜索框
            self.log_info("第一步：正在寻找搜索框...")
            await asyncio.sleep(2)  # 给用户时间观察

            search_selectors = [
                'input[placeholder*="搜索"]',
                'input[type="search"]',
                '[class*="search"] input',
                '.search-input'
            ]

            search_input = None
            for selector in search_selectors:
                try:
                    search_input = await self.page.wait_for_selector(selector, timeout=5000)
                    self.log_info(f"找到搜索框: {selector}")
                    # 高亮搜索框
                    await search_input.evaluate('el => el.style.border = "3px solid red"')
                    await asyncio.sleep(1)  # 让用户看到高亮
                    break
                except:
                    continue

            if not search_input:
                self.log_info("未找到搜索框！")
                return False

            # 第二步：输入搜索关键词
            self.log_info("第二步：正在输入搜索关键词...")
            await search_input.click()
            await search_input.fill("")  # 清空
            await search_input.type(keyword, delay=200)  # 慢速输入便于观察
            await asyncio.sleep(2)

            # 第三步：提交搜索
            self.log_info("第三步：提交搜索请求...")
            await search_input.press('Enter')

            # 等待搜索结果加载
            self.log_info("等待搜索结果加载...")
            await self.page.wait_for_load_state('networkidle', timeout=30000)
            await asyncio.sleep(3)

            # 显示搜索结果页面URL
            search_url = self.page.url
            self.log_info(f"搜索结果页面: {search_url}")

            # 截图保存搜索结果页面
            await self.page.screenshot(path="搜索结果页面.png")
            self.log_info("已保存搜索结果页面截图")

            # 第四步：演示排序设置
            self.log_info("第四步：正在设置最新发布排序...")
            await self.demonstrate_latest_sort()

            # 第五步：展示当前是最新排序状态
            await asyncio.sleep(2)
            await self.page.screenshot(path="最新排序状态.png")
            self.log_info("已保存最新排序状态截图")

            return True

        except Exception as e:
            self.log_info(f"搜索演示失败: {str(e)}")
            return False

    async def demonstrate_latest_sort(self):
        """演示设置最新排序的详细过程"""
        self.log_info("详细演示最新排序设置过程...")

        try:
            # 方法1: 尝试通过URL参数
            current_url = self.page.url
            self.log_info(f"当前URL: {current_url}")

            # 添加排序参数
            if '?' in current_url:
                sorted_url = current_url + '&sort=createTime'
            else:
                sorted_url = current_url + '?sort=createTime'

            self.log_info(f"尝试通过URL设置排序: {sorted_url}")
            await self.page.goto(sorted_url, timeout=15000)
            await self.page.wait_for_load_state('networkidle', timeout=15000)
            await asyncio.sleep(2)

            # 方法2: 查找并点击排序按钮
            self.log_info("寻找排序按钮...")

            sort_selectors = [
                '[class*="sort"]',
                '[class*="filter"]',
                '[class*="order"]',
                '.sort-bar',
                '.filter-bar'
            ]

            sort_element = None
            for selector in sort_selectors:
                try:
                    elements = await self.page.query_selector_all(selector)
                    for element in elements:
                        text = await element.text_content()
                        if text and ('排序' in text or '筛选' in text or '综合' in text):
                            sort_element = element
                            self.log_info(f"找到排序元素: {selector}")
                            self.log_info(f"排序元素文本: {text}")

                            # 高亮排序按钮
                            await element.evaluate('el => el.style.border = "3px solid blue"')
                            await asyncio.sleep(1)
                            break
                    if sort_element:
                        break
                except:
                    continue

            if sort_element:
                self.log_info("点击排序按钮...")
                await sort_element.click()
                await asyncio.sleep(2)

                # 寻找最新发布选项
                self.log_info("寻找最新发布选项...")
                latest_options = [
                    'text="最新发布"',
                    'text="最新"',
                    'text="时间"',
                    'text="发布时间"',
                    'div:has-text("最新发布")',
                    'span:has-text("最新发布")'
                ]

                for option in latest_options:
                    try:
                        latest_elem = await self.page.wait_for_selector(option, timeout=3000)
                        self.log_info(f"找到最新发布选项: {option}")

                        # 高亮最新选项
                        await latest_elem.evaluate('el => el.style.border = "3px solid green"')
                        await asyncio.sleep(1)

                        self.log_info("点击最新发布选项...")
                        await latest_elem.click()
                        await asyncio.sleep(3)
                        self.log_info("最新发布排序设置完成！")
                        return True
                    except:
                        continue

                self.log_info("未找到明确的最新发布选项，但URL排序可能已生效")
            else:
                self.log_info("未找到排序按钮，仅使用URL参数排序")

            return True

        except Exception as e:
            self.log_info(f"排序演示失败: {str(e)}")
            return False

    async def extract_and_display_latest_products(self, max_count=5):
        """提取并显示最新的几个商品"""
        self.log_info(f"=== 提取并显示前{max_count}个最新商品 ===")

        try:
            # 等待页面稳定
            await asyncio.sleep(3)

            # 查找商品元素
            product_selectors = [
                '.feeds-item-wrap--rGdH_KoF',
                '[class*="feeds-item"]',
                '[class*="item-wrap"]',
                'a[href*="item?id"]'
            ]

            elements = []
            for selector in product_selectors:
                try:
                    found_elements = await self.page.query_selector_all(selector)
                    if found_elements:
                        self.log_info(f"使用选择器 '{selector}' 找到 {len(found_elements)} 个商品")
                        elements = found_elements
                        break
                except:
                    continue

            if not elements:
                self.log_info("未找到商品元素")
                return []

            # 处理前几个商品
            products = []
            for i, element in enumerate(elements[:max_count]):
                try:
                    self.log_info(f"正在处理第 {i+1} 个商品...")

                    # 高亮当前处理的商品
                    await element.evaluate('el => el.style.border = "3px solid orange"')
                    await asyncio.sleep(1)  # 给用户时间观察

                    product_info = await self.extract_product_details(element, i + 1)
                    if product_info:
                        products.append(product_info)
                        self.display_product_info(product_info)

                    # 取消高亮
                    await element.evaluate('el => el.style.border = ""')

                except Exception as e:
                    self.log_info(f"处理第 {i+1} 个商品失败: {str(e)}")
                    continue

            self.log_info(f"成功提取 {len(products)} 个商品信息")
            return products

        except Exception as e:
            self.log_info(f"商品提取失败: {str(e)}")
            return []

    async def extract_product_details(self, element, index):
        """提取商品详细信息"""
        try:
            # 商品标题
            title = ""
            title_selectors = [
                '.main-title--sMrtWSJa',
                '[class*="title"]',
                '.row1-wrap-title--qIlOySTh'
            ]

            for selector in title_selectors:
                try:
                    title_elem = await element.query_selector(selector)
                    if title_elem:
                        title = await title_elem.text_content()
                        if title and title.strip():
                            title = title.strip()
                            break
                except:
                    continue

            # 价格
            price = ""
            price_selectors = [
                '.number--NKh1vXWM',
                '[class*="price"]',
                '.price-wrap'
            ]

            for selector in price_selectors:
                try:
                    price_elem = await element.query_selector(selector)
                    if price_elem:
                        price_text = await price_elem.text_content()
                        if price_text and price_text.strip():
                            price = f"¥{price_text.strip()}"
                            break
                except:
                    continue

            # 地区
            location = ""
            location_selectors = [
                '.seller-text--Rr2Y3EbB',
                '[class*="location"]',
                '.seller-left--OBwJil87 p'
            ]

            for selector in location_selectors:
                try:
                    location_elem = await element.query_selector(selector)
                    if location_elem:
                        location_text = await location_elem.text_content()
                        if location_text and location_text.strip():
                            location = location_text.strip()
                            break
                except:
                    continue

            # 商品链接
            product_link = ""
            if await element.query_selector('a[href*="item?id"]'):
                link_elem = await element.query_selector('a[href*="item?id"]')
                product_link = await link_elem.get_attribute('href')

            # 提取商品ID
            product_id = ""
            if product_link:
                match = re.search(r'item\?id=([^&]+)', product_link)
                if match:
                    product_id = match.group(1)

            return {
                '序号': index,
                '商品标题': title,
                '价格': price,
                '地区': location,
                '商品链接': product_link,
                '商品ID': product_id,
                '提取时间': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }

        except Exception as e:
            self.log_info(f"提取商品详情失败: {str(e)}")
            return None

    def display_product_info(self, product):
        """显示商品信息"""
        print(f"\n{'='*60}")
        print(f"商品 #{product['序号']}")
        print(f"标题: {product['商品标题']}")
        print(f"价格: {product['价格']}")
        print(f"地区: {product['地区']}")
        print(f"商品ID: {product['商品ID']}")
        print(f"提取时间: {product['提取时间']}")
        print(f"{'='*60}")

    async def save_results(self, products):
        """保存结果"""
        if not products:
            self.log_info("没有数据可保存")
            return

        try:
            os.makedirs("C:\\Users\\Administrator\\Desktop\\闲鱼\\可视化测试结果", exist_ok=True)

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"C:\\Users\\Administrator\\Desktop\\闲鱼\\可视化测试结果\\可视化最新排序测试_{timestamp}.xlsx"

            df = pd.DataFrame(products)
            df.to_excel(filename, index=False, engine='openpyxl')

            self.log_info(f"结果已保存到: {filename}")
            self.log_info(f"共保存了 {len(products)} 个商品信息")

        except Exception as e:
            self.log_info(f"保存失败: {str(e)}")

    async def close(self):
        """关闭浏览器"""
        if self.page:
            await self.page.close()
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()

async def run_visual_test():
    """运行可视化测试"""
    print("=" * 80)
    print("可视化最新排序功能测试")
    print("您将能够看到整个操作过程")
    print("=" * 80)
    print("\n重要提示:")
    print("1. 浏览器将以有头模式启动，您可以看到所有操作")
    print("2. 操作速度会放慢，便于观察")
    print("3. 重要元素会被高亮显示")
    print("4. 会自动截图保存关键状态")
    print("5. 请观察排序是否确实设置为最新发布")
    print("\n按回车键开始测试...")
    input()

    test = VisualLatestSortTest()

    try:
        # 设置浏览器（有头模式）
        if not await test.setup_browser(headless=False):
            print("浏览器设置失败")
            return

        # 应用Cookie并导航
        if not await test.apply_cookies_and_navigate():
            print("导航失败")
            return

        print("\n现在您应该能看到浏览器窗口打开了")
        print("观察浏览器中的操作过程...")
        await asyncio.sleep(3)

        # 演示搜索和排序
        if not await test.demonstrate_search_and_sort("手机"):
            print("搜索演示失败")
            return

        # 提取并显示商品
        products = await test.extract_and_display_latest_products(5)

        # 保存结果
        await test.save_results(products)

        print(f"\n测试完成！")
        print(f"提取了 {len(products)} 个商品")
        print("请查看截图文件验证排序效果")
        print("\n按回车键关闭浏览器...")
        input()

    except Exception as e:
        print(f"测试过程中发生错误: {str(e)}")
    finally:
        await test.close()

if __name__ == "__main__":
    asyncio.run(run_visual_test())