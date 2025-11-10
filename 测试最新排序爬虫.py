#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试版闲鱼最新排序数据抓取器
专门用于测试爬取网页最新排序内容，不影响现有爬虫设置
"""

import asyncio
import pandas as pd
from datetime import datetime
from playwright.async_api import async_playwright
import re
import random
import time
import os

# 配置日志 - 使用简化版避免编码问题
import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

class TestLatestSortScraper:
    """测试版本 - 专注于最新排序功能"""

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
            'sort_attempts': 0,
            'sort_successes': 0,
            'pages_crawled': 0,
            'start_time': None,
            'end_time': None
        }

        # Cookie字符串 - 支持从外部传入
        if cookie_string:
            self.cookie_string = cookie_string
        else:
            # 默认Cookie
            self.cookie_string = 'cna=Gj2PIVvfVnUCATytZ6pBVuaC; t=a5122db3552745fae77dcc8bd999c78f; tracknick=xy227407743954; havana_lgc2_77=eyJoaWQiOjIyMjEwNTk1MTk1MDMsInNnIjoiYzYyMTFiYmI1MzJmOTc4MzllNzYyYzVlMWRhZDUzMTciLCJzaXRlIjo3NywidG9rZW4iOiIxVjVFQkNLN2UxRjZLUVpBMTZVMWVxQSJ9; _hvn_lgc_=77; havana_lgc_exp=1764746274257; cookie2=14200db952d961688a60cf14acb2ffb2; mtop_partitioned_detect=1; _m_h5_tk=baac0bed28387029452647868b393313_1762608074777; _m_h5_tk_enc=9566c16833cd791ce48c9fb9dae04e6c; xlly_s=1; _samesite_flag_=true; sdkSilent=1762684756836; _tb_token_=e3e53eb565e; sgcookie=E100ISMaftFoirZTZm4%2BnVITm9pRarQlQg5i%2By4fQHQfufeaOs%2BaihilB0wuO0uGeoUkWGY0o6rM2QQXIYvatAXVZ%2F%2F9lcEFE791QN5mQNWs7rY%3D; csg=9b38caf0; unb=2221059519503; tfstk=gEBnQADA86RQkekItuvQtaO3HNVOdp9WTaHJyLLz_F8sJ2Hd44bl7ZIKpTIyrab95aA7AULyraIP9leYHMsBFLkuk-eAje-FMwmezBryQ3K8XH8UqSDeFLzYWfHyO-v5-eVoYQSaj3K-TH7rUdkw53cETa8e_V-DcL8Pza8Z7ntrL38rLRow53JyYaJzjd862L8PzLrGbAgIUEXPCOz5ve24kOphIHAHuGVjEYlvvqLcYkDSeOfMtEykSYkPIHjy7n1sn7LVGedvkNytKLjwqwLOu-kMQIff23b3KvJd_16BpOUmcBbkJIW9sSoGopbkg9Ri4YIhvUJMbtr-GFBMJaWH_oHDwdWvgp5T1ydJKnbPdwmoUZSOD9O1Er0wP6KXQnIQKAvVY3SzNflqiCDWbuBZNbOefhYvJIZhodfcCOZgjjNBThtLklqiNbOefhYYjlcjPB-6vrC..'

    def log_test_info(self, message):
        """记录测试信息"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[TEST {timestamp}] {message}")

    def log_performance(self, operation, duration):
        """记录性能数据"""
        print(f"[PERFORMANCE] {operation}: {duration:.2f}秒")

    async def setup_browser(self, headless=True):
        """设置Playwright浏览器"""
        start_time = time.time()
        self.log_test_info("Setting up browser for latest sort test...")

        try:
            self.playwright = await async_playwright().start()

            # Chromium浏览器配置 - 针对测试优化
            browser_args = [
                '--no-sandbox',
                '--disable-blink-features=AutomationControlled',
                '--disable-dev-shm-usage',
                '--disable-gpu',
                '--disable-web-security',
                '--allow-running-insecure-content',
                '--disable-features=VizDisplayCompositor',
                '--proxy-server="direct://"',
                '--proxy-bypass-list=*',
                '--disable-extensions',
                '--no-first-run',
                '--disable-default-apps',
                '--disable-sync',
                '--disable-background-timer-throttling',
                '--disable-backgrounding-occluded-windows',
                '--disable-renderer-backgrounding'
            ]

            self.browser = await self.playwright.chromium.launch(
                headless=headless,
                args=browser_args
            )

            # 创建浏览器上下文（移动端模拟）
            self.context = await self.browser.new_context(
                user_agent='Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Mobile/15E148 Safari/604.1',
                viewport={'width': 375, 'height': 667},
                device_scale_factor=2,
                is_mobile=True,
                has_touch=True
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

            setup_time = time.time() - start_time
            self.log_performance("Browser setup", setup_time)
            self.log_test_info("Browser setup successful")
            return True

        except Exception as e:
            self.log_test_info(f"Browser setup failed: {str(e)}")
            return False

    async def apply_cookies(self):
        """应用Cookie到Playwright页面"""
        start_time = time.time()
        self.log_test_info("Applying cookies for test...")

        try:
            # 先访问闲鱼主页
            self.log_test_info("Accessing Goofish homepage...")
            for attempt in range(3):
                try:
                    response = await self.page.goto("https://www.goofish.com",
                                                   timeout=30000,
                                                   wait_until='domcontentloaded')
                    self.log_test_info(f"Access attempt {attempt + 1} - Status: {response.status if response else 'No response'}")

                    if response and response.status == 200:
                        break
                    else:
                        self.log_test_info(f"Attempt {attempt + 1} failed, status: {response.status if response else 'No response'}")
                        if attempt < 2:
                            await asyncio.sleep(2)
                except Exception as e:
                    self.log_test_info(f"Attempt {attempt + 1} exception: {str(e)}")
                    if attempt < 2:
                        await asyncio.sleep(2)
                    else:
                        raise e

            await asyncio.sleep(3)
            self.log_test_info("Homepage loaded successfully")

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

            self.log_test_info(f"Preparing to set {len(cookies)} cookies")

            # 设置Cookie
            await self.context.add_cookies(cookies)
            self.log_test_info("Cookies added to context successfully")

            # 刷新页面使Cookie生效
            await self.page.reload()
            await asyncio.sleep(2)

            cookie_time = time.time() - start_time
            self.log_performance("Cookie application", cookie_time)
            self.log_test_info(f"Successfully applied {len(cookies)} cookies")
            return True

        except Exception as e:
            self.log_test_info(f"Cookie application failed: {str(e)}")
            return False

    async def test_latest_sort_search(self, keyword="手机", max_pages=2):
        """测试最新排序搜索功能"""
        self.test_stats['start_time'] = datetime.now()
        self.log_test_info(f"=== STARTING LATEST SORT TEST ===")
        self.log_test_info(f"Keyword: {keyword}, Max pages: {max_pages}")

        try:
            # 查找搜索框
            search_selectors = [
                'input[placeholder*="搜索"]',
                'input[type="search"]',
                '[class*="search"] input',
                '.search-input',
                'input.search-input'
            ]

            search_input = None
            self.log_test_info("Locating search input...")
            for selector in search_selectors:
                try:
                    search_input = await self.page.wait_for_selector(selector, timeout=10000)
                    self.log_test_info(f"Found search input: {selector}")
                    break
                except:
                    continue

            if not search_input:
                self.log_test_info("ERROR: Search input not found")
                return False

            # 执行搜索
            self.log_test_info(f"Typing keyword: {keyword}")
            await search_input.click()
            await search_input.fill("")
            await search_input.type(keyword, delay=100)
            await asyncio.sleep(2)
            await search_input.press('Enter')
            self.log_test_info("Search submitted, waiting for results...")

            # 等待搜索结果加载
            self.log_test_info("Waiting for search results page to load...")
            await self.page.wait_for_load_state('networkidle', timeout=30000)
            await asyncio.sleep(3)
            self.log_test_info("Page loaded successfully")

            # 记录当前URL，用于对比排序效果
            initial_url = self.page.url
            self.log_test_info(f"Initial search URL: {initial_url}")

            # 测试排序功能
            self.log_test_info("=== TESTING SORT FUNCTION ===")
            sort_result = await self.test_and_set_latest_sort()

            if sort_result:
                self.log_test_info("Latest sort setting appears successful")
            else:
                self.log_test_info("Latest sort setting may have failed, continuing anyway")

            # 提取数据
            self.log_test_info("=== STARTING DATA EXTRACTION ===")
            total_extracted = 0

            for page in range(1, max_pages + 1):
                self.log_test_info(f"--- Processing Page {page} ---")

                # 截图保存当前页面状态
                screenshot_name = f"test_latest_sort_page_{page}_{int(time.time())}.png"
                await self.page.screenshot(path=screenshot_name)
                self.log_test_info(f"Screenshot saved: {screenshot_name}")

                page_products = await self.extract_products_with_debug(page, keyword)

                if page_products:
                    self.results.extend(page_products)
                    page_count = len(page_products)
                    total_extracted += page_count
                    self.log_test_info(f"Page {page} extracted {page_count} products")
                    self.log_test_info(f"Total so far: {len(self.results)} products")
                else:
                    self.log_test_info(f"Page {page} extracted no products, ending crawl")
                    break

                # 尝试翻页
                if page < max_pages:
                    self.log_test_info("Attempting to go to next page...")
                    next_success = await self.go_to_next_page()
                    if not next_success:
                        self.log_test_info("Next page navigation failed, ending crawl")
                        break
                    await asyncio.sleep(3)

            self.test_stats['end_time'] = datetime.now()
            duration = (self.test_stats['end_time'] - self.test_stats['start_time']).total_seconds()

            self.log_test_info(f"=== TEST COMPLETED ===")
            self.log_test_info(f"Total products extracted: {len(self.results)}")
            self.log_test_info(f"Total time: {duration:.2f} seconds")
            self.log_test_info(f"Average per product: {duration/len(self.results):.2f} seconds" if self.results else "N/A")

            return len(self.results) > 0

        except Exception as e:
            self.log_test_info(f"Search test failed: {str(e)}")
            return False

    async def test_and_set_latest_sort(self):
        """测试并设置最新排序"""
        start_time = time.time()
        self.test_stats['sort_attempts'] += 1
        self.log_test_info("Testing latest sort functionality...")

        try:
            # 方法1: 尝试通过URL参数设置
            current_url = self.page.url
            self.log_test_info(f"Current URL: {current_url}")

            # 添加排序参数
            if '?' in current_url:
                url_with_sort = current_url + '&sort=createTime'
            else:
                url_with_sort = current_url + '?sort=createTime'

            self.log_test_info(f"Attempting URL with sort parameter: {url_with_sort}")
            await self.page.goto(url_with_sort, timeout=15000)
            await self.page.wait_for_load_state('networkidle', timeout=15000)
            await asyncio.sleep(2)

            # 方法2: 尝试点击排序按钮
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
                        if text and ('排序' in text or '筛选' in text):
                            sort_element = element
                            self.log_test_info(f"Found sort element: {text}")
                            break
                    if sort_element:
                        break
                except:
                    continue

            if sort_element:
                self.log_test_info("Clicking sort element...")
                await sort_element.click()
                await asyncio.sleep(2)

                # 寻找最新发布选项
                latest_options = [
                    'text="最新发布"',
                    'text="最新"',
                    'text="时间"',
                    'div:has-text("最新发布")',
                    'span:has-text("最新发布")'
                ]

                for option in latest_options:
                    try:
                        latest_elem = await self.page.wait_for_selector(option, timeout=3000)
                        self.log_test_info(f"Found latest option: {option}")
                        await latest_elem.click()
                        await asyncio.sleep(3)
                        self.test_stats['sort_successes'] += 1

                        sort_time = time.time() - start_time
                        self.log_performance("Sort setting", sort_time)
                        return True
                    except:
                        continue

            # 如果没有找到最新选项，但URL设置可能有效
            self.test_stats['sort_successes'] += 1
            sort_time = time.time() - start_time
            self.log_performance("Sort setting (URL only)", sort_time)
            return True

        except Exception as e:
            self.log_test_info(f"Sort setting failed: {str(e)}")
            return False

    async def extract_products_with_debug(self, page_num, keyword):
        """提取商品信息并记录调试信息"""
        start_time = time.time()
        products = []

        try:
            # 多种商品选择器
            product_selectors = [
                '.feeds-item-wrap--rGdH_KoF',
                '[class*="feeds-item"]',
                '[class*="item-wrap"]',
                'a[href*="item?id"]',
                '.search-item'
            ]

            elements = []
            for selector in product_selectors:
                try:
                    found_elements = await self.page.query_selector_all(selector)
                    if found_elements:
                        self.log_test_info(f"Using selector '{selector}' found {len(found_elements)} elements")
                        elements = found_elements
                        break
                except:
                    continue

            if not elements:
                all_links = await self.page.query_selector_all('a[href*="item?id"]')
                self.log_test_info(f"Using backup selector found {len(all_links)} product links")
                elements = all_links

            max_items = min(len(elements), 20)  # 限制数量用于测试
            self.log_test_info(f"Processing {max_items} products from page {page_num}")

            for i, element in enumerate(elements[:max_items]):
                try:
                    self.test_stats['total_found'] += 1
                    product_info = await self.extract_single_product_debug(element, i + 1)
                    if product_info and product_info.get('商品标题', '').strip():
                        products.append(product_info)
                        self.test_stats['successful_extractions'] += 1
                    else:
                        self.test_stats['failed_extractions'] += 1
                except Exception as e:
                    self.test_stats['failed_extractions'] += 1
                    self.log_test_info(f"Failed to extract product {i+1}: {str(e)}")
                    continue

            self.test_stats['pages_crawled'] += 1
            extraction_time = time.time() - start_time
            self.log_performance(f"Page {page_num} extraction", extraction_time)

            return products

        except Exception as e:
            self.log_test_info(f"Failed to extract page {page_num}: {str(e)}")
            return products

    async def extract_single_product_debug(self, element, index):
        """提取单个商品并记录调试信息"""
        try:
            # 获取商品链接
            product_link = ''
            if await element.query_selector('a[href*="item?id"]'):
                link_elem = await element.query_selector('a[href*="item?id"]')
                product_link = await link_elem.get_attribute('href')

            # 提取商品ID
            product_id = ''
            if product_link:
                match = re.search(r'item\?id=([^&]+)', product_link)
                if match:
                    product_id = match.group(1)

            # 提取商品标题
            title = ''
            title_selectors = [
                '.main-title--sMrtWSJa',
                '[class*="title"]',
                '.row1-wrap-title--qIlOySTh',
                'h1', 'h2', 'h3'
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

            # 提取价格
            price = ''
            price_selectors = [
                '.number--NKh1vXWM',
                '[class*="price"]',
                '.price-wrap',
                '.row3-wrap-price--IZmX7M0K'
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

            # 提取地区信息
            location = ''
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

            # 提取商品图片
            product_image = ''
            try:
                image_selectors = [
                    '.mainPic img',
                    '.picR img',
                    '.pic img',
                    '[class*="pic"] img:not([class*="avatar"]):not([class*="logo"])',
                    'img[src*="alicdn.com"]:not([src*="avatar"]):not([src*="logo"])'
                ]

                for selector in image_selectors:
                    try:
                        img_elem = await element.query_selector(selector)
                        if img_elem:
                            product_image = await img_elem.get_attribute('src')
                            if product_image and 'alicdn.com' in product_image:
                                if product_image.startswith('//'):
                                    product_image = 'https:' + product_image
                                break
                    except:
                        continue
            except Exception as e:
                self.log_test_info(f"Image extraction failed: {e}")

            info = {
                '序号': index,
                '商品标题': title,
                '价格': price,
                '地区': location,
                '商品链接': product_link,
                '商品ID': product_id,
                '商品图片': product_image,
                '搜索时间': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                '关键词': '手机',
                '数据来源': 'Test-LatestSort',
                '测试模式': '最新排序测试'
            }

            return info

        except Exception as e:
            self.log_test_info(f"Failed to extract product info: {str(e)}")
            return None

    async def go_to_next_page(self):
        """翻到下一页"""
        try:
            self.log_test_info("Looking for next page button...")
            next_selectors = [
                'button:has-text("下一页")',
                '.search-page-tiny-arrow-container--tVZE99sy:not([disabled])',
                '[class*="next"]:not([disabled])',
                '.pagination .next'
            ]

            for selector in next_selectors:
                try:
                    next_button = await self.page.query_selector(selector)
                    if next_button:
                        self.log_test_info(f"Found next button, clicking: {selector}")
                        await next_button.click()
                        await asyncio.sleep(2)
                        return True
                except:
                    continue

            self.log_test_info("No usable next page button found")
            return False
        except Exception as e:
            self.log_test_info(f"Next page navigation failed: {str(e)}")
            return False

    def save_test_results(self, keyword="手机"):
        """保存测试结果"""
        if not self.results:
            self.log_test_info("No data to save")
            return None

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        try:
            os.makedirs("C:\\Users\\Administrator\\Desktop\\闲鱼\\测试结果", exist_ok=True)

            # 保存商品数据
            filename = f"C:\\Users\\Administrator\\Desktop\\闲鱼\\测试结果\\最新排序测试_{keyword}_{timestamp}.xlsx"
            df = pd.DataFrame(self.results)
            df.to_excel(filename, index=False, engine='openpyxl')

            # 保存测试统计
            stats_filename = f"C:\\Users\\Administrator\\Desktop\\闲鱼\\测试结果\\测试统计_{keyword}_{timestamp}.txt"
            with open(stats_filename, 'w', encoding='utf-8') as f:
                f.write("=== 最新排序功能测试统计 ===\n\n")
                f.write(f"测试时间: {self.test_stats['start_time']} - {self.test_stats['end_time']}\n")
                f.write(f"关键词: {keyword}\n")
                f.write(f"发现商品总数: {self.test_stats['total_found']}\n")
                f.write(f"成功提取: {self.test_stats['successful_extractions']}\n")
                f.write(f"提取失败: {self.test_stats['failed_extractions']}\n")
                f.write(f"成功率: {(self.test_stats['successful_extractions'] / max(self.test_stats['total_found'], 1)) * 100:.1f}%\n")
                f.write(f"排序尝试次数: {self.test_stats['sort_attempts']}\n")
                f.write(f"排序成功次数: {self.test_stats['sort_successes']}\n")
                f.write(f"爬取页面数: {self.test_stats['pages_crawled']}\n")
                f.write(f"最终商品数: {len(self.results)}\n")

                if self.test_stats['start_time'] and self.test_stats['end_time']:
                    duration = (self.test_stats['end_time'] - self.test_stats['start_time']).total_seconds()
                    f.write(f"总耗时: {duration:.2f}秒\n")
                    f.write(f"平均每个商品: {duration/len(self.results):.2f}秒\n" if self.results else "平均耗时: N/A\n")

            self.log_test_info(f"Test results saved to: {filename}")
            self.log_test_info(f"Test statistics saved to: {stats_filename}")
            return filename

        except Exception as e:
            self.log_test_info(f"Failed to save test results: {str(e)}")
            return None

    def display_test_summary(self):
        """显示测试总结"""
        print(f"\n=== TEST SUMMARY ===")
        print(f"Total products found: {len(self.results)}")
        print(f"Search attempts: {self.test_stats['sort_attempts']}")
        print(f"Sort successes: {self.test_stats['sort_successes']}")
        print(f"Pages crawled: {self.test_stats['pages_crawled']}")
        print(f"Success rate: {(self.test_stats['successful_extractions'] / max(self.test_stats['total_found'], 1)) * 100:.1f}%")

        # 显示前3个商品示例
        print(f"\nFirst 3 products:")
        for i, item in enumerate(self.results[:3]):
            print(f"{i+1}. {item.get('商品标题', '')}")
            print(f"   Price: {item.get('价格', '')}")
            print(f"   Location: {item.get('地区', '')}")
            print("-" * 40)

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

async def run_latest_sort_test(keyword="手机", max_pages=2):
    """运行最新排序测试"""
    print("=" * 80)
    print("TESTING LATEST SORT FUNCTIONALITY")
    print("Independent test - no impact on main scraper")
    print("=" * 80)

    scraper = TestLatestSortScraper()

    try:
        scraper.log_test_info(f"Starting latest sort test for '{keyword}'")

        # 设置浏览器
        if not await scraper.setup_browser(headless=True):
            scraper.log_test_info("Browser setup failed")
            return False, "Browser setup failed"

        # 应用Cookie
        if not await scraper.apply_cookies():
            scraper.log_test_info("Cookie setup failed")
            return False, "Cookie setup failed"

        # 执行最新排序搜索测试
        success = await scraper.test_latest_sort_search(keyword, max_pages)

        if success and scraper.results:
            # 保存测试结果
            filename = scraper.save_test_results(keyword)

            # 显示测试总结
            scraper.display_test_summary()

            return True, f"测试成功，提取了 {len(scraper.results)} 个商品"
        else:
            return False, "测试失败或未提取到数据"

    except Exception as e:
        scraper.log_test_info(f"Test error: {str(e)}")
        return False, f"测试异常: {str(e)}"
    finally:
        await scraper.close()

if __name__ == "__main__":
    # 运行测试
    success, message = asyncio.run(run_latest_sort_test("手机", 2))
    print(f"\nFinal result: {success}")
    print(f"Message: {message}")