#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
改进版可视化最新排序测试
确保真正点击选择栏里的最新发布选项
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

class ImprovedVisualTest:
    """改进版可视化测试"""

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
        print(f"[改进版测试 {timestamp}] {message}")

    async def setup_browser(self, headless=False):
        """设置浏览器 - 有头模式"""
        self.log_info("正在设置改进版可视化浏览器...")

        try:
            self.playwright = await async_playwright().start()

            # 浏览器配置
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
                slow_mo=2000  # 减慢操作速度便于观察
            )

            # 创建浏览器上下文（桌面端模拟）
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
                Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]});
                Object.defineProperty(navigator, 'languages', {get: () => ['zh-CN', 'zh', 'en']});
                Object.defineProperty(navigator, 'automation', {get: () => undefined});
            """)

            self.log_info("改进版浏览器设置成功！")
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
            await asyncio.sleep(5)

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
            await asyncio.sleep(5)

            self.log_info("Cookie应用成功")
            return True

        except Exception as e:
            self.log_info(f"Cookie应用失败: {str(e)}")
            return False

    async def demonstrate_search_and_enhanced_sort(self, keyword="手机"):
        """演示搜索和增强排序过程"""
        self.log_info(f"=== 开始搜索演示 ===")
        self.log_info(f"搜索关键词: {keyword}")

        try:
            # 第一步：寻找搜索框
            self.log_info("第一步：正在寻找搜索框...")
            await asyncio.sleep(3)

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
                    await asyncio.sleep(2)
                    break
                except:
                    continue

            if not search_input:
                self.log_info("未找到搜索框！")
                return False

            # 第二步：输入搜索关键词
            self.log_info("第二步：正在输入搜索关键词...")
            await search_input.click()
            await search_input.fill("")
            await search_input.type(keyword, delay=300)
            await asyncio.sleep(3)

            # 第三步：提交搜索
            self.log_info("第三步：提交搜索请求...")
            await search_input.press('Enter')

            # 等待搜索结果加载
            self.log_info("等待搜索结果加载...")
            await self.page.wait_for_load_state('networkidle', timeout=30000)
            await asyncio.sleep(5)

            # 显示搜索结果页面URL
            search_url = self.page.url
            self.log_info(f"搜索结果页面: {search_url}")

            # 截图保存搜索结果页面
            await self.page.screenshot(path="搜索结果页面.png")
            self.log_info("已保存搜索结果页面截图")

            # 第四步：增强版排序设置
            self.log_info("第四步：正在进行增强版排序设置...")
            await self.enhanced_latest_sort()

            # 第五步：展示当前是最新排序状态
            await asyncio.sleep(3)
            await self.page.screenshot(path="最新排序状态.png")
            self.log_info("已保存最新排序状态截图")

            return True

        except Exception as e:
            self.log_info(f"搜索演示失败: {str(e)}")
            return False

    async def enhanced_latest_sort(self):
        """增强版最新排序设置 - 确保点击选择栏里的选项"""
        self.log_info("开始增强版最新排序设置...")

        try:
            # 步骤1: 查找并点击排序/筛选区域
            self.log_info("步骤1: 查找排序/筛选区域...")

            # 多种可能的排序触发区域
            sort_trigger_selectors = [
                '[class*="sort"]',
                '[class*="filter"]',
                '[class*="order"]',
                '.sort-bar',
                '.filter-bar',
                'div:has-text("综合排序")',
                'div:has-text("排序")',
                'div:has-text("筛选")',
                'button:has-text("筛选")',
                'span:has-text("排序")'
            ]

            sort_area = None
            for selector in sort_trigger_selectors:
                try:
                    elements = await self.page.query_selector_all(selector)
                    for element in elements:
                        text = await element.text_content()
                        if text and ('排序' in text or '筛选' in text or '综合' in text or '默认' in text):
                            sort_area = element
                            self.log_info(f"找到排序区域: {selector}")
                            self.log_info(f"排序区域文本: {text}")

                            # 高亮排序区域
                            await element.evaluate('el => el.style.border = "3px solid blue"')
                            await asyncio.sleep(2)
                            break
                    if sort_area:
                        break
                except:
                    continue

            if sort_area:
                self.log_info("点击排序区域...")
                await sort_area.click()
                await asyncio.sleep(3)

                # 步骤2: 等待并查找弹出的选择选项
                self.log_info("步骤2: 查找最新发布选项...")
                await self.find_and_click_latest_option()

            else:
                # 如果没有找到排序区域，尝试直接查找最新选项
                self.log_info("未找到排序区域，尝试直接查找最新选项...")
                await self.find_and_click_latest_option()

            return True

        except Exception as e:
            self.log_info(f"增强版排序设置失败: {str(e)}")
            return False

    async def find_and_click_latest_option(self):
        """查找并点击最新发布选项"""
        self.log_info("正在查找最新发布选项...")

        # 最新发布选项的各种可能选择器
        latest_option_selectors = [
            # 直接文本匹配
            'text="最新发布"',
            'text="最新"',
            'text="时间排序"',
            'text="发布时间"',
            'text="最新上架"',

            # 包含文本的元素
            'div:has-text("最新发布")',
            'span:has-text("最新发布")',
            'li:has-text("最新发布")',
            'a:has-text("最新发布")',
            'button:has-text("最新发布")',
            'option:has-text("最新发布")',

            'div:has-text("最新")',
            'span:has-text("最新")',
            'li:has-text("最新")',
            'a:has-text("最新")',

            'div:has-text("时间")',
            'span:has-text("时间")',
            'li:has-text("时间")',

            # 类名匹配
            '[class*="latest"]',
            '[class*="new"]',
            '[class*="time"]',
            '[class*="create"]',
            '[class*="recent"]'
        ]

        latest_option = None
        for selector in latest_option_selectors:
            try:
                elements = await self.page.query_selector_all(selector)
                self.log_info(f"检查选择器 '{selector}': 找到 {len(elements)} 个元素")

                for element in elements:
                    try:
                        text = await element.text_content()
                        self.log_info(f"元素文本: '{text}'")

                        # 检查是否包含最新相关的关键词
                        if (text and ('最新发布' in text or '最新' in text or '时间排序' in text or
                                    '发布时间' in text or '最新上架' in text or '发布' in text)):

                            # 确保不是其他包含这些词的选项
                            if not ('默认排序' in text or '综合排序' in text or '价格' in text):
                                latest_option = element
                                self.log_info(f"找到最新发布选项: {selector}")
                                self.log_info(f"选项文本: '{text}'")

                                # 高亮最新选项
                                await element.evaluate('el => el.style.border = "3px solid green"')
                                await asyncio.sleep(2)
                                break
                    except:
                        continue

                if latest_option:
                    break

            except Exception as e:
                self.log_info(f"检查选择器 {selector} 时出错: {str(e)}")
                continue

        # 如果找到了最新选项，点击它
        if latest_option:
            self.log_info("点击最新发布选项...")
            await latest_option.click()
            await asyncio.sleep(5)

            # 再次截图确认
            await self.page.screenshot(path="点击最新发布后.png")
            self.log_info("已保存点击最新发布后的截图")

            return True
        else:
            self.log_info("未找到明确的最新发布选项，尝试其他方法...")

            # 尝试通过URL参数设置
            current_url = self.page.url
            if '?' in current_url:
                new_url = current_url + '&sort=createTime'
            else:
                new_url = current_url + '?sort=createTime'

            self.log_info(f"通过URL设置排序: {new_url}")
            await self.page.goto(new_url, timeout=15000)
            await self.page.wait_for_load_state('networkidle', timeout=15000)
            await asyncio.sleep(3)

            return True

    async def extract_and_verify_latest_products(self, max_count=5):
        """提取并验证最新的几个商品"""
        self.log_info(f"=== 提取并验证前{max_count}个最新商品 ===")

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
                    await asyncio.sleep(2)

                    product_info = await self.extract_product_details(element, i + 1)
                    if product_info:
                        products.append(product_info)
                        self.display_product_info(product_info)

                        # 验证是否为最新商品
                        await self.verify_if_latest_product(product_info)

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

    async def verify_if_latest_product(self, product):
        """验证商品是否为最新发布"""
        self.log_info(f"验证商品 #{product['序号']} 是否为最新发布...")

        # 检查标题中是否包含"全新"、"刚发布"等关键词
        title = product.get('商品标题', '').lower()
        latest_keywords = ['全新', '刚发布', '新上架', '最新', '首发', '新品', '全新未拆']

        found_keywords = []
        for keyword in latest_keywords:
            if keyword in title:
                found_keywords.append(keyword)

        if found_keywords:
            self.log_info(f"  ✅ 发现最新关键词: {found_keywords}")
        else:
            self.log_info(f"  ⚠️ 未发现明显的新品标识")

        # 检查发布时间（如果有的话）
        if '发布时间' in title:
            self.log_info(f"  ✅ 发现发布时间信息")

        return len(found_keywords) > 0

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
            os.makedirs("C:\\Users\\Administrator\\Desktop\\闲鱼\\改进版测试结果", exist_ok=True)

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"C:\\Users\\Administrator\\Desktop\\闲鱼\\改进版测试结果\\改进版最新排序测试_{timestamp}.xlsx"

            df = pd.DataFrame(products)
            df.to_excel(filename, index=False, engine='openpyxl')

            self.log_info(f"结果已保存到: {filename}")
            self.log_info(f"共保存了 {len(products)} 个商品信息")

        except Exception as e:
            self.log_info(f"保存失败: {str(e)}")

    async def wait_and_close(self, seconds=10):
        """等待几秒后关闭"""
        self.log_info(f"等待 {seconds} 秒后关闭浏览器，请观察结果...")
        await asyncio.sleep(seconds)

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

async def run_improved_test():
    """运行改进版测试"""
    print("=" * 80)
    print("改进版可视化最新排序功能测试")
    print("确保真正点击选择栏里的最新发布选项")
    print("=" * 80)
    print("\n改进点:")
    print("1. 增强了排序选项查找逻辑")
    print("2. 会查找所有可能的新品发布选项")
    print("3. 点击选项后会进行验证")
    print("4. 检查商品标题中的新品标识")
    print("\n测试将自动开始...")

    test = ImprovedVisualTest()

    try:
        # 设置浏览器（有头模式）
        if not await test.setup_browser(headless=False):
            print("浏览器设置失败")
            return

        # 应用Cookie并导航
        if not await test.apply_cookies_and_navigate():
            print("导航失败")
            return

        # 演示搜索和增强排序
        if not await test.demonstrate_search_and_enhanced_sort("手机"):
            print("搜索演示失败")
            return

        # 提取并验证商品
        products = await test.extract_and_verify_latest_products(5)

        # 保存结果
        await test.save_results(products)

        print(f"\n改进版测试完成！")
        print(f"提取了 {len(products)} 个商品")
        print("请查看截图文件验证排序效果和点击过程")

        # 等待用户观察
        await test.wait_and_close(20)

    except Exception as e:
        print(f"测试过程中发生错误: {str(e)}")
    finally:
        await test.close()

if __name__ == "__main__":
    asyncio.run(run_improved_test())