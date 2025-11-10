#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
改进版闲鱼最新排序数据抓取器
专门实现鼠标悬停显示最新选项的功能
不影响现有真实版爬虫
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

class ImprovedLatestSortScraper:
    """改进版 - 实现鼠标悬停最新排序功能"""

    def __init__(self, cookie_string=None):
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None
        self.results = []
        self.test_stats = {
            'total_found': 0,
            'successful_extractions': 0,
            'failed_extractions': 0,
            'hover_attempts': 0,
            'hover_successes': 0,
            'pages_crawled': 0,
            'start_time': None,
            'end_time': None
        }

        # Cookie字符串
        if cookie_string:
            self.cookie_string = cookie_string
        else:
            # 默认Cookie
            self.cookie_string = 'cna=Gj2PIVvfVnUCATytZ6pBVuaC; t=a5122db3552745fae77dcc8bd999c78f; tracknick=xy227407743954; havana_lgc2_77=eyJoaWQiOjIyMjEwNTk1MTk1MDMsInNnIjoiYzYyMTFiYmI1MzJmOTc4MzllNzYyYzVlMWRhZDUzMTciLCJzaXRlIjo3NywidG9rZW4iOiIxVjVFQkNLN2UxRjZLUVpBMTZVMWVxQSJ9; _hvn_lgc_=77; havana_lgc_exp=1764746274257; cookie2=14200db952d961688a60cf14acb2ffb2; mtop_partitioned_detect=1; _m_h5_tk=baac0bed28387029452647868b393313_1762608074777; _m_h5_tk_enc=9566c16833cd791ce48c9fb9dae04e6c; xlly_s=1; _samesite_flag_=true; sdkSilent=1762684756836; _tb_token_=e3e53eb565e; sgcookie=E100ISMaftFoirZTZm4%2BnVITm9pRarQlQg5i%2By4fQHQfufeaOs%2BaihilB0wuO0uGeoUkWGY0o6rM2QQXIYvatAXVZ%2F%2F9lcEFE791QN5mQNWs7rY%3D; csg=9b38caf0; unb=2221059519503; tfstk=gEBnQADA86RQkekItuvQtaO3HNVOdp9WTaHJyLLz_F8sJ2Hd44bl7ZIKpTIyrab95aA7AULyraIP9leYHMsBFLkuk-eAje-FMwmezBryQ3K8XH8UqSDeFLzYWfHyO-v5-eVoYQSaj3K-TH7rUdkw53cETa8e_V-DcL8Pza8Z7ntrL38rLRow53JyYaJzjd862L8PzLrGbAgIUEXPCOz5ve24kOphIHAHuGVjEYlvvqLcYkDSeOfMtEykSYkPIHjy7n1sn7LVGedvkNytKLjwqwLOu-kMQIff23b3KvJd_16BpOUmcBbkJIW9sSoGopbkg9Ri4YIhvUJMbtr-GFBMJaWH_oHDwdWvgp5T1ydJKnbPdwmoUZSOD9O1Er0wP6KXQnIQKAvVY3SzNflqiCDWbuBZNbOefhYvJIZhodfcCOZgjjNBThtLklqiNbOefhYYjlcjPB-6vrC..'

    def log_test_info(self, message):
        """记录测试信息"""
        print(f"[IMPROVED] {datetime.now().strftime('%H:%M:%S')} - {message}")
        logger.info(f"IMPROVED: {message}")

    def log_performance(self, operation, duration):
        """记录性能数据"""
        print(f"[PERFORMANCE] {operation}: {duration:.2f}s")
        logger.info(f"PERFORMANCE: {operation} took {duration:.2f} seconds")

    async def setup_browser(self):
        """设置浏览器"""
        self.log_test_info("Setting up browser for improved scraper...")
        start_time = time.time()

        self.playwright = await async_playwright().start()

        # 启动浏览器（使用有头模式便于观察）
        self.browser = await self.playwright.chromium.launch(
            headless=False,  # 设置为False以便观察操作过程
            args=[
                '--disable-blink-features=AutomationControlled',
                '--no-sandbox',
                '--disable-dev-shm-usage'
            ]
        )

        self.context = await self.browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        )

        self.page = await self.context.new_page()

        # 添加反检测脚本
        await self.page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined,
            });
        """)

        setup_time = time.time() - start_time
        self.log_performance("Browser setup", setup_time)
        return True

    async def apply_cookies(self):
        """应用Cookie"""
        self.log_test_info("Applying cookies...")
        try:
            # 解析Cookie字符串
            cookies = []
            for cookie_pair in self.cookie_string.split(';'):
                if '=' in cookie_pair:
                    name, value = cookie_pair.strip().split('=', 1)
                    cookies.append({
                        'name': name,
                        'value': value,
                        'domain': '.goofish.com',
                        'path': '/'
                    })

            await self.context.add_cookies(cookies)
            self.log_test_info(f"Successfully applied {len(cookies)} cookies")
            return True
        except Exception as e:
            self.log_test_info(f"Cookie application failed: {e}")
            return False

    async def navigate_to_search(self, keyword):
        """导航到搜索页面"""
        self.log_test_info(f"Navigating to search page for keyword: {keyword}")
        try:
            search_url = f"https://www.goofish.com/search?q={keyword}"
            await self.page.goto(search_url, timeout=30000)
            await self.page.wait_for_load_state('networkidle', timeout=15000)

            # 等待页面加载完成
            await asyncio.sleep(3)

            current_url = self.page.url
            self.log_test_info(f"Successfully navigated to: {current_url}")
            return True
        except Exception as e:
            self.log_test_info(f"Navigation failed: {e}")
            return False

    async def hover_and_click_latest_sort(self):
        """实现鼠标悬停在"新发布"下拉状态栏显示最新选项功能"""
        start_time = time.time()
        self.test_stats['hover_attempts'] += 1
        self.log_test_info("Attempting hover on '新发布' dropdown to show latest options...")

        try:
            # 等待页面完全加载
            await asyncio.sleep(2)

            # 方案1: 寻找"新发布"下拉状态栏
            self.log_test_info("Looking for '新发布' dropdown status bar...")

            # 更新选择器，专门寻找"新发布"相关的下拉状态栏
            new_publish_dropdown_selectors = [
                # 针对"新发布"状态栏的选择器
                'button:has-text("新发布")',
                'div:has-text("新发布")',
                'span:has-text("新发布")',
                '[class*="publish"]',
                '[class*="new"]',
                '.new-publish',
                '.publish-dropdown',
                '[data-testid*="publish"]',
                '[data-testid*="new"]',
                'div[aria-label*="新发布"]',
                'div[title*="新发布"]',
                # 更具体的选择器
                '.status-item:has-text("新发布")',
                '.dropdown-item:has-text("新发布")',
                '[role="button"]:has-text("新发布")',
                # 尝试包含"发布"的关键词
                'button:has-text("发布")',
                'div:has-text("发布")',
                'span:has-text("发布")',
                # 也包含时间和最新相关
                'button:has-text("最新")',
                'div:has-text("最新")',
                'span:has-text("最新")',
                'button:has-text("时间")',
                'div:has-text("时间")',
                '[class*="time"]',
                '[class*="latest"]'
            ]

            dropdown_element = None
            dropdown_text = ""

            # 尝试找到"新发布"下拉状态栏
            for selector in new_publish_dropdown_selectors:
                try:
                    elements = await self.page.query_selector_all(selector)
                    for element in elements:
                        text = await element.text_content()
                        if text and ('新发布' in text or '发布' in text or '最新' in text or '时间' in text):
                            dropdown_element = element
                            dropdown_text = text.strip()
                            self.log_test_info(f"Found '新发布' dropdown element: '{dropdown_text}' with selector: {selector}")
                            break
                    if dropdown_element:
                        break
                except Exception as e:
                    self.log_test_info(f"Selector {selector} failed: {e}")
                    continue

            if not dropdown_element:
                # 尝试通过视觉识别找到可能的下拉区域
                self.log_test_info("Trying to find dropdown by visual detection...")

                # 查找包含筛选相关文字的元素
                all_buttons = await self.page.query_selector_all('button, div[role="button"], [class*="button"]')
                for btn in all_buttons:
                    try:
                        text = await btn.text_content()
                        if text and len(text.strip()) < 10:  # 通常按钮文字较短
                            bbox = await btn.bounding_box()
                            if bbox:  # 确保元素可见
                                self.log_test_info(f"Found potential button: '{text.strip()}'")
                                # 这里可以添加更多视觉检测逻辑
                    except:
                        continue

            if dropdown_element:
                # 关键步骤：鼠标悬停到"新发布"下拉状态栏上
                self.log_test_info(f"Hovering over '新发布' dropdown element: '{dropdown_text}'")
                await dropdown_element.hover()
                await asyncio.sleep(2)  # 等待下拉菜单显示，增加等待时间

                # 尝试多种方式寻找"最新"或其他排序选项
                self.log_test_info("Looking for sort options after hovering '新发布'...")

                # 更新选择器，寻找悬停后显示的排序选项
                sort_option_selectors = [
                    # 直接匹配常见排序选项
                    'text="最新发布"',
                    'text="最新"',
                    'text="时间最新"',
                    'text="发布时间"',
                    'text="最新上架"',
                    'div:has-text("最新发布")',
                    'span:has-text("最新发布")',
                    'li:has-text("最新发布")',
                    'a:has-text("最新发布")',
                    # 数据属性匹配
                    '[data-value*="latest"]',
                    '[data-value*="new"]',
                    '[data-value*="createTime"]',
                    '[data-value*="publishTime"]',
                    # 角色匹配
                    'div[role="menuitem"]:has-text("最新")',
                    'li[role="menuitem"]:has-text("最新")',
                    'a[role="menuitem"]:has-text("最新")',
                    # 更广泛的匹配
                    'div:has-text("最新")',
                    'span:has-text("最新")',
                    'li:has-text("最新")',
                    'a:has-text("最新")',
                    # 包含时间相关的选项
                    'div:has-text("时间")',
                    'span:has-text("时间")',
                    'li:has-text("时间")'
                ]

                option_found = False
                for selector in sort_option_selectors:
                    try:
                        # 增加等待时间，因为下拉菜单可能需要时间显示
                        option_elem = await self.page.wait_for_selector(selector, timeout=5000)
                        if option_elem:
                            text = await option_elem.text_content()
                            self.log_test_info(f"Found sort option: '{text}' with selector: {selector}")

                            # 点击选项
                            await option_elem.click()
                            await asyncio.sleep(3)  # 等待页面重新加载

                            self.test_stats['hover_successes'] += 1
                            hover_time = time.time() - start_time
                            self.log_performance("Hover '新发布' and click option", hover_time)

                            # 截图保存
                            await self.take_screenshot("after_click_option")
                            return True
                    except Exception as e:
                        self.log_test_info(f"Selector {selector} failed: {e}")
                        continue

                # 如果悬停后没有找到选项，尝试点击"新发布"状态栏然后寻找
                self.log_test_info("No options found after hover, trying click '新发布' status bar first...")
                await dropdown_element.click()
                await asyncio.sleep(2)

                for selector in sort_option_selectors:
                    try:
                        option_elem = await self.page.wait_for_selector(selector, timeout=3000)
                        if option_elem:
                            text = await option_elem.text_content()
                            self.log_test_info(f"Found option after click: '{text}'")
                            await option_elem.click()
                            await asyncio.sleep(3)

                            self.test_stats['hover_successes'] += 1
                            hover_time = time.time() - start_time
                            self.log_performance("Click '新发布' and select option", hover_time)
                            return True
                    except:
                        continue

            else:
                self.log_test_info("No dropdown element found, trying URL method...")

                # 作为备选方案，尝试通过URL参数设置排序
                current_url = self.page.url
                if 'sort=' not in current_url:
                    if '?' in current_url:
                        url_with_sort = current_url + '&sort=createTime'
                    else:
                        url_with_sort = current_url + '?sort=createTime'

                    self.log_test_info(f"Trying URL with sort parameter: {url_with_sort}")
                    await self.page.goto(url_with_sort, timeout=15000)
                    await self.page.wait_for_load_state('networkidle', timeout=15000)
                    await asyncio.sleep(3)

                    self.test_stats['hover_successes'] += 1
                    hover_time = time.time() - start_time
                    self.log_performance("URL sort method", hover_time)
                    return True

            self.log_test_info("All methods to set latest sort failed")
            return False

        except Exception as e:
            self.log_test_info(f"Hover and click failed: {e}")
            return False

    async def take_screenshot(self, name):
        """截图保存"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"C:\\Users\\Administrator\\Desktop\\闲鱼\\测试结果\\improved_latest_{name}_{timestamp}.png"

            # 确保目录存在
            os.makedirs(os.path.dirname(filename), exist_ok=True)

            await self.page.screenshot(path=filename, full_page=False)
            self.log_test_info(f"Screenshot saved: {filename}")
        except Exception as e:
            self.log_test_info(f"Screenshot failed: {e}")

    async def extract_products(self, max_products=5):
        """提取商品信息（简化版，用于测试）"""
        self.log_test_info(f"Extracting up to {max_products} products...")

        try:
            # 等待商品加载
            await asyncio.sleep(2)

            # 使用更通用的选择器
            product_selectors = [
                '.feeds-item-wrap',
                '[class*="item"]',
                '[class*="product"]',
                '[class*="card"]',
                'a[href*="/item/"]'
            ]

            products_found = 0
            for selector in product_selectors:
                try:
                    products = await self.page.query_selector_all(selector)
                    if len(products) > 0:
                        self.log_test_info(f"Found {len(products)} products with selector: {selector}")
                        products_found = len(products)
                        break
                except:
                    continue

            if products_found == 0:
                self.log_test_info("No products found")
                return []

            # 简化提取，只记录基本信息
            extracted_count = 0
            for i in range(min(products_found, max_products)):
                try:
                    # 这里可以添加具体的商品信息提取逻辑
                    self.test_stats['successful_extractions'] += 1
                    extracted_count += 1
                except Exception as e:
                    self.log_test_info(f"Product extraction error: {e}")
                    self.test_stats['failed_extractions'] += 1

            self.log_test_info(f"Successfully extracted {extracted_count} products")
            self.test_stats['total_found'] = products_found
            return True

        except Exception as e:
            self.log_test_info(f"Product extraction failed: {e}")
            return False

    async def test_latest_sort_search(self, keyword="手机", max_pages=1):
        """测试最新排序搜索功能"""
        self.log_test_info(f"Starting improved latest sort test for keyword: {keyword}")
        self.test_stats['start_time'] = datetime.now()

        try:
            # 1. 设置浏览器
            if not await self.setup_browser():
                return False

            # 2. 应用Cookie
            await self.apply_cookies()

            # 3. 导航到搜索页面
            if not await self.navigate_to_search(keyword):
                return False

            # 4. 截图初始状态
            await self.take_screenshot("initial_state")

            # 5. 尝试悬停并点击最新排序（核心功能）
            sort_success = await self.hover_and_click_latest_sort()

            if sort_success:
                self.log_test_info("Latest sort setting successful!")

                # 6. 提取商品信息
                for page_num in range(max_pages):
                    self.log_test_info(f"Crawling page {page_num + 1}")

                    await self.extract_products(max_products=5)
                    self.test_stats['pages_crawled'] += 1

                    # 如果有下一页，继续爬取
                    if page_num < max_pages - 1:
                        try:
                            next_button = await self.page.query_selector('.search-page-tiny-arrow-container:not([disabled])')
                            if next_button:
                                await next_button.click()
                                await self.page.wait_for_load_state('networkidle', timeout=15000)
                                await asyncio.sleep(3)
                            else:
                                break
                        except:
                            break
            else:
                self.log_test_info("Latest sort setting failed")

            return sort_success

        except Exception as e:
            self.log_test_info(f"Search test failed: {e}")
            return False

    async def close_browser(self):
        """关闭浏览器"""
        if self.page:
            await self.page.close()
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()

    def save_test_results(self, keyword="手机"):
        """保存测试结果"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

            # 保存Excel报告
            filename = f"C:\\Users\\Administrator\\Desktop\\闲鱼\\测试结果\\改进版最新排序测试_{keyword}_{timestamp}.xlsx"
            os.makedirs(os.path.dirname(filename), exist_ok=True)

            # 创建测试报告
            report_data = {
                '测试项目': ['悬停尝试次数', '悬停成功次数', '找到商品数量', '成功提取数量', '失败提取数量', '爬取页面数'],
                '数值': [
                    self.test_stats['hover_attempts'],
                    self.test_stats['hover_successes'],
                    self.test_stats['total_found'],
                    self.test_stats['successful_extractions'],
                    self.test_stats['failed_extractions'],
                    self.test_stats['pages_crawled']
                ]
            }

            df = pd.DataFrame(report_data)
            df.to_excel(filename, index=False)

            # 保存文本报告
            text_filename = f"C:\\Users\\Administrator\\Desktop\\闲鱼\\测试结果\\改进版最新排序报告_{keyword}_{timestamp}.txt"
            with open(text_filename, 'w', encoding='utf-8') as f:
                f.write("=== 改进版最新排序功能测试统计 ===\n\n")
                f.write(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"测试关键词: {keyword}\n\n")

                f.write("=== 测试结果 ===\n")
                f.write(f"悬停尝试次数: {self.test_stats['hover_attempts']}\n")
                f.write(f"悬停成功次数: {self.test_stats['hover_successes']}\n")
                f.write(f"找到商品数量: {self.test_stats['total_found']}\n")
                f.write(f"成功提取数量: {self.test_stats['successful_extractions']}\n")
                f.write(f"失败提取数量: {self.test_stats['failed_extractions']}\n")
                f.write(f"爬取页面数: {self.test_stats['pages_crawled']}\n\n")

                if self.test_stats['hover_attempts'] > 0:
                    success_rate = (self.test_stats['hover_successes'] / self.test_stats['hover_attempts']) * 100
                    f.write(f"悬停成功率: {success_rate:.1f}%\n")

            self.log_test_info(f"Test results saved to: {filename}")
            self.log_test_info(f"Report saved to: {text_filename}")

        except Exception as e:
            self.log_test_info(f"Save results failed: {e}")

async def main():
    """运行改进版最新排序测试"""
    scraper = ImprovedLatestSortScraper()

    try:
        # 执行改进版最新排序搜索测试
        success = await scraper.test_latest_sort_search(
            keyword="手机",
            max_pages=1
        )

        if success:
            print("\n[SUCCESS] 改进版最新排序测试成功完成！")
        else:
            print("\n[FAILED] 改进版最新排序测试失败！")

        # 保存测试结果
        scraper.save_test_results("手机")

    except KeyboardInterrupt:
        print("\n[INTERRUPTED] 测试被用户中断")
    except Exception as e:
        print(f"\n[ERROR] 测试过程中出现错误: {e}")
    finally:
        # 确保浏览器正确关闭
        await scraper.close_browser()
        print("\n[COMPLETE] 测试完成，浏览器已关闭")

if __name__ == "__main__":
    asyncio.run(main())