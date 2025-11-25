#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自动运行版闲鱼数据抓取器
使用预设参数自动执行，无需用户输入
"""

import asyncio
import pandas as pd
from datetime import datetime
from playwright.async_api import async_playwright
import re
import random
import time

# 配置日志 - 使用简化版避免编码问题
import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

class AutoXianyuScraper:
    def __init__(self, cookie_string=None, headless=True):
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None
        self.results = []
        self.headless = headless  # 保存显示模式设置

        # Cookie字符串 - 支持从外部传入
        if cookie_string:
            self.cookie_string = cookie_string
        else:
            # 默认Cookie（向后兼容）
            self.cookie_string = 'cna=Gj2PIVvfVnUCATytZ6pBVuaC; t=a5122db3552745fae77dcc8bd999c78f; tracknick=xy227407743954; havana_lgc2_77=eyJoaWQiOjIyMjEwNTk1MTk1MDMsInNnIjoiYzYyMTFiYmI1MzJmOTc4MzllNzYyYzVlMWRhZDUzMTciLCJzaXRlIjo3NywidG9rZW4iOiIxVjVFQkNLN2UxRjZLUVpBMTZVMWVxQSJ9; _hvn_lgc_=77; havana_lgc_exp=1764746274257; cookie2=14200db952d961688a60cf14acb2ffb2; mtop_partitioned_detect=1; _m_h5_tk=baac0bed28387029452647868b393313_1762608074777; _m_h5_tk_enc=9566c16833cd791ce48c9fb9dae04e6c; xlly_s=1; _samesite_flag_=true; sdkSilent=1762684756836; _tb_token_=e3e53eb565e; sgcookie=E100ISMaftFoirZTZm4%2BnVITm9pRarQlQg5i%2By4fQHQfufeaOs%2BaihilB0wuO0uGeoUkWGY0o6rM2QQXIYvatAXVZ%2F%2F9lcEFE791QN5mQNWs7rY%3D; csg=9b38caf0; unb=2221059519503; tfstk=gEBnQADA86RQkekItuvQtaO3HNVOdp9WTaHJyLLz_F8sJ2Hd44bl7ZIKpTIyrab95aA7AULyraIP9leYHMsBFLkuk-eAje-FMwmezBryQ3K8XH8UqSDeFLzYWfHyO-v5-eVoYQSaj3K-TH7rUdkw53cETa8e_V-DcL8Pza8Z7ntrL38rLRow53JyYaJzjd862L8PzLrGbAgIUEXPCOz5ve24kOphIHAHuGVjEYlvvqLcYkDSeOfMtEykSYkPIHjy7n1sn7LVGedvkNytKLjwqwLOu-kMQIff23b3KvJd_16BpOUmcBbkJIW9sSoGopbkg9Ri4YIhvUJMbtr-GFBMJaWH_oHDwdWvgp5T1ydJKnbPdwmoUZSOD9O1Er0wP6KXQnIQKAvVY3SzNflqiCDWbuBZNbOefhYvJIZhodfcCOZgjjNBThtLklqiNbOefhYYjlcjPB-6vrC..'

    def smart_delay(self, base_delay=2):
        """
        智能延迟函数
        添加随机性避免规律性行为，模拟真实用户操作
        """
        # 添加随机浮动 (±30%)
        random_factor = random.uniform(0.7, 1.3)
        actual_delay = base_delay * random_factor

        # 添加额外随机延迟 (0-2秒)
        extra_delay = random.uniform(0, 2)
        total_delay = actual_delay + extra_delay

        print(f"[智能延迟] 执行 {total_delay:.1f}秒")
        print(f"[延迟分析] 基础{base_delay}秒 × {random_factor:.2f} + {extra_delay:.1f}秒随机")

        return asyncio.sleep(total_delay)

    async def setup_browser(self, headless=None):
        """设置Playwright浏览器"""
        # 使用传入的headless参数，如果没有则使用实例变量
        if headless is None:
            headless = self.headless

        print(f"Setting up Playwright browser (headless={headless})...")

        try:
            self.playwright = await async_playwright().start()

            # Chromium浏览器配置
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

            # 根据显示模式调整配置
            if not headless:
                # 有头模式下的特殊配置
                browser_args.extend([
                    '--start-maximized',  # 启动时最大化
                    '--disable-background-timer-throttling',
                    '--disable-backgrounding-occluded-windows',
                    '--disable-renderer-backgrounding'
                ])

            self.browser = await self.playwright.chromium.launch(
                headless=headless,
                args=browser_args,
                slow_mo=1000 if not headless else 0  # 有头模式下减慢操作速度便于观察
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

            print("Browser setup successful")
            return True

        except Exception as e:
            print(f"Browser setup failed: {str(e)}")
            return False

    async def apply_cookies(self):
        """应用Cookie到Playwright页面"""
        print("Applying cookies...")

        try:
            # 先访问闲鱼主页，增加重试机制
            print(f"[页面访问] 正在访问闲鱼主页...")
            for attempt in range(3):  # 最多重试3次
                try:
                    response = await self.page.goto("https://www.goofish.com",
                                                   timeout=30000,
                                                   wait_until='domcontentloaded')
                    print(f"[页面访问] 访问尝试 {attempt + 1} - 状态: {response.status if response else 'No response'}")

                    # 检查页面是否加载成功
                    if response and response.status == 200:
                        break
                    else:
                        print(f"[页面访问] 第{attempt + 1}次尝试失败，状态码: {response.status if response else 'No response'}")
                        if attempt < 2:  # 不是最后一次尝试
                            await asyncio.sleep(2)
                except Exception as e:
                    print(f"[页面访问] 第{attempt + 1}次尝试异常: {str(e)}")
                    if attempt < 2:  # 不是最后一次尝试
                        await asyncio.sleep(2)
                    else:
                        raise e

            await asyncio.sleep(3)
            print(f"[页面访问] 主页加载完成")

            # 解析并设置Cookie
            cookies = []
            print(f"[Cookie设置] 当前cookie_string {self.cookie_string}")
            for item in self.cookie_string.split(';'):
                if '=' in item:
                    key, value = item.strip().split('=', 1)
                    cookies.append({
                        'name': key.strip(),
                        'value': value.strip(),
                        'domain': '.goofish.com',
                        'path': '/'
                    })

            print(f"[Cookie设置] 准备设置 {len(cookies)} 个Cookie")

            # 设置Cookie
            await self.context.add_cookies(cookies)
            print(f"[Cookie设置] Cookie添加到上下文成功")

            # 刷新页面使Cookie生效
            await self.page.reload()
            await asyncio.sleep(2)

            print(f"[Cookie设置] 成功应用 {len(cookies)} 个Cookie")
            return True

        except Exception as e:
            print(f"[Cookie设置错误] Cookie application failed: {str(e)}")
            print(f"[Cookie设置错误] 错误类型: {type(e).__name__}")

            # 尝试不使用Cookie直接访问来测试网络连接
            try:
                print("[网络测试] 尝试测试基本网络连接...")
                await self.page.goto("https://www.baidu.com", timeout=10000)
                print("[网络测试] 网络连接正常")
            except Exception as net_e:
                print(f"[网络测试] 网络连接异常: {str(net_e)}")

            return False

    async def search_products(self, keyword="手机", max_pages=3, delay=2, sort_by_latest=True):
        """搜索闲鱼商品，支持按时间排序"""
        sort_mode = "最新发布" if sort_by_latest else "默认排序"
        print(f"[搜索开始] 关键词: {keyword}, 目标页数: {max_pages}, 排序方式: {sort_mode}")
        print(f"[进度状态] 正在初始化浏览器并应用Cookie...")

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
            print(f"[搜索框定位] 正在寻找搜索框...")
            for selector in search_selectors:
                try:
                    search_input = await self.page.wait_for_selector(selector, timeout=10000)
                    print(f"[搜索框定位] 成功找到搜索框: {selector}")
                    break
                except:
                    continue

            if not search_input:
                print(f"[搜索框定位] 错误: 未找到搜索框")
                return False

            # 执行搜索
            print(f"[搜索执行] 正在输入关键词: {keyword}")
            await search_input.click()
            await search_input.fill("")  # 清空
            await search_input.type(keyword, delay=100)
            await asyncio.sleep(2)
            await search_input.press('Enter')
            print(f"[搜索执行] 已提交搜索，等待结果加载...")

            # 等待搜索结果加载
            print(f"[结果加载] 正在等待搜索结果页面加载...")
            await self.page.wait_for_load_state('networkidle', timeout=30000)
            print(f"[结果加载] 页面加载完成，开始智能延迟...")
            # 首次加载使用较长的智能延迟
            await self.smart_delay(max(delay, 3))

            # 设置排序方式为最新发布
            if sort_by_latest:
                print(f"[排序设置] 正在设置排序方式为最新发布...")
                sort_success = await self.set_sort_to_latest()
                if sort_success:
                    print(f"[排序设置] 排序设置成功，优先显示最新发布的商品")
                else:
                    print(f"[排序设置] 排序设置失败，使用默认排序")

            # 检查页面是否加载成功
            current_url = self.page.url
            print(f"[页面状态] 当前页面: {current_url}")

            # 提取多页数据
            print(f"[数据提取] 开始提取商品数据，目标页数: {max_pages}")
            for page in range(1, max_pages + 1):
                print(f"[数据提取] ===== 正在提取第 {page} 页数据 =====")
                page_products = await self.extract_products_from_page(page, keyword)

                if page_products:
                    self.results.extend(page_products)
                    print(f"[数据提取] 第 {page} 页成功提取 {len(page_products)} 个商品")
                    print(f"[数据提取] 当前总计: {len(self.results)} 个商品")
                else:
                    print(f"[数据提取] 第 {page} 页未提取到商品，结束爬取")
                    break

                # 尝试翻页
                if page < max_pages:
                    print(f"[翻页操作] 准备翻转到第 {page+1} 页...")
                    next_success = await self.go_to_next_page()
                    if not next_success:
                        print(f"[翻页操作] 翻页失败，结束爬取")
                        break
                    print(f"[翻页操作] 翻页成功，开始智能延迟...")
                    # 使用智能延迟替代固定延迟
                    await self.smart_delay(delay)

            print(f"[爬取完成] ===== 爬取结束 =====")
            print(f"[爬取完成] 总计提取 {len(self.results)} 个商品")
            return len(self.results) > 0

        except Exception as e:
            print(f"[搜索错误] 搜索过程中发生异常: {str(e)}")
            print(f"[搜索错误] 爬取失败，请检查网络连接和Cookie状态")
            return False

    async def extract_products_from_page(self, page_num, keyword):
        """从当前页面提取商品信息"""
        products = []

        try:
            # 优化的商品选择器
            product_selectors = [
                '.feeds-item-wrap--rGdH_KoF',  # 主要商品包装元素
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
                        print(f"Using selector '{selector}' found {len(found_elements)} elements")
                        elements = found_elements
                        break
                except:
                    continue

            # 如果还是没找到，尝试所有商品链接
            if not elements:
                all_links = await self.page.query_selector_all('a[href*="item?id"]')
                print(f"Using backup selector found {len(all_links)} product links")
                elements = all_links

            # 限制处理数量
            max_items = min(len(elements), 30)
            print(f"Processing {max_items} out of {len(elements)} products")

            for i, element in enumerate(elements[:max_items]):
                try:
                    product_info = await self.extract_single_product(element, i + 1)
                    if product_info and product_info.get('商品标题', '').strip():
                        products.append(product_info)
                except Exception as e:
                    print(f"Failed to extract product {i+1}: {str(e)}")
                    continue

        except Exception as e:
            print(f"Failed to extract page products: {str(e)}")

        return products

    async def extract_single_product(self, element, index):
        """提取单个商品的详细信息"""
        try:
            # 获取商品链接
            product_link = ''
            if await element.query_selector('a[href*="item?id"]'):
                link_elem = await element.query_selector('a[href*="item?id"]')
                product_link = await link_elem.get_attribute('href')
            elif hasattr(element, 'get_attribute'):
                try:
                    product_link = await element.get_attribute('href')
                except:
                    pass

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

            # 提取地区/卖家信息
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

            # 提取卖家信用
            credit = ''
            credit_selectors = [
                '.gradient-image-text--YUZj27iZ',
                '[class*="credit"]',
                '[class*="seller"] span'
            ]

            for selector in credit_selectors:
                try:
                    credit_elem = await element.query_selector(selector)
                    if credit_elem:
                        credit_text = await credit_elem.text_content()
                        if credit_text and credit_text.strip():
                            credit = credit_text.strip()
                            if credit not in title and len(credit) < 20:
                                break
                except:
                    continue

            # 提取商品图片
            product_image = ''
            try:
                # 更精确的图片选择器，优先获取商品主图
                image_selectors = [
                    # 闲鱼/咸鱼商品图选择器 - 优先级最高
                    '.mainPic img',
                    '.feeds-image--TDRC4fV1 img',
                    '.picR img',
                    '.pic img',
                    '.goods-pic img',
                    '.item-pic img',
                    '.cover img',
                    # 通用商品图选择器 - 中等优先级
                    '[class*="pic"] img:not([class*="avatar"]):not([class*="logo"])',
                    '[class*="image"] img:not([class*="avatar"]):not([class*="logo"])',
                    '[class*="photo"] img:not([class*="avatar"]):not([class*="logo"])',
                    '.product-image img',
                    '.product-pic img',
                    '.thumbnail img',
                    '.gallery img',
                    # 备用选择器（最后使用，但要更严格过滤）
                    'img[src*="alicdn.com"]:not([src*="avatar"]):not([src*="logo"]):not([src*="icon"])',
                    'img[src*="taobao.com"]:not([src*="avatar"]):not([src*="logo"]):not([src*="icon"])',
                    'img[src*="tbcdn.cn"]:not([src*="avatar"]):not([src*="logo"]):not([src*="icon"])'
                ]

                for selector in image_selectors:
                    try:
                        img_elem = await element.query_selector(selector)
                        if img_elem:
                            product_image = await img_elem.get_attribute('src')
                            if product_image:
                                # 添加https前缀（如果是//开头）
                                if product_image.startswith('//'):
                                    product_image = 'https:' + product_image

                                # 严格的图片验证条件
                                if ('alicdn.com' in product_image or
                                    'taobao.com' in product_image or
                                    'tbcdn.cn' in product_image) and \
                                   ('avatar' not in product_image and
                                    'logo' not in product_image and
                                    'icon' not in product_image and
                                    'placeholder' not in product_image and
                                    'default' not in product_image and
                                    '2-tps-2-2' not in product_image):  # 排除小占位图
                                    break
                                else:
                                    product_image = ''  # 重置，继续下一个选择器
                    except:
                        continue

                # 如果没有找到有效图片，设置为空字符串而不是占位符
                if not product_image or '2-tps-2-2' in product_image:
                    product_image = ''
                    print(f"[图片警告] 商品 {title[:20]}... 未找到有效图片")

            except Exception as e:
                print(f"图片提取失败: {e}")
                product_image = ''  # 确保异常情况下也不使用占位符

            info = {
                '序号': index,
                '商品标题': title,
                '价格': price,
                '地区': location,
                '卖家信用': credit,
                '商品链接': product_link,
                '商品ID': product_id,
                '商品图片': product_image,
                '搜索时间': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                '关键词': '手机',
                '数据来源': 'Playwright+真实Cookie'
            }

            return info

        except Exception as e:
            print(f"Failed to extract product info: {str(e)}")
            return None

    async def go_to_next_page(self):
        """翻到下一页"""
        try:
            print(f"[翻页操作] 正在寻找下一页按钮...")
            # 多种翻页选择器
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
                        print(f"[翻页操作] 找到翻页按钮，正在点击: {selector}")
                        await next_button.click()
                        print(f"[翻页操作] 点击成功，等待页面稳定...")
                        # 翻页后使用固定短延迟，避免页面跳动
                        await asyncio.sleep(2)
                        return True
                except:
                    continue

            print(f"[翻页操作] 错误: 未找到可用的翻页按钮")
            return False
        except Exception as e:
            print(f"[翻页操作] 异常: {str(e)}")
            return False

    def save_results(self, keyword="手机", format_type='excel'):
        """保存搜索结果"""
        if not self.results:
            print("No data to save")
            return None

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        try:
            import os
            os.makedirs("C:\\Users\\Administrator\\Desktop\\闲鱼", exist_ok=True)

            if format_type == 'excel':
                filename = f"C:\\Users\\Administrator\\Desktop\\闲鱼\\自动抓取_{keyword}_{timestamp}.xlsx"
                df = pd.DataFrame(self.results)
                df.to_excel(filename, index=False, engine='openpyxl')
            elif format_type == 'csv':
                filename = f"C:\\Users\\Administrator\\Desktop\\闲鱼\\自动抓取_{keyword}_{timestamp}.csv"
                df = pd.DataFrame(self.results)
                df.to_csv(filename, index=False, encoding='utf-8-sig')

            print(f"Data saved to: {filename}")
            print(f"Total {len(self.results)} products saved")
            return filename
        except Exception as e:
            print(f"Failed to save data: {str(e)}")
            return None

    def display_results(self, count=5):
        """显示结果"""
        print(f"\n=== SEARCH RESULTS ===")
        print(f"Total products: {len(self.results)}")

        print(f"\nFirst {count} products:")
        print("=" * 60)

        for i, item in enumerate(self.results[:count]):
            print(f"\n{i+1}. {item.get('商品标题', '')}")
            print(f"   Price: {item.get('价格', '')}")
            print(f"   Location: {item.get('地区', '')}")
            print(f"   Credit: {item.get('卖家信用', '')}")
            print(f"   ID: {item.get('商品ID', '')}")
            print("-" * 60)

        # 统计分析
        print(f"\n=== STATISTICS ===")

        # 价格统计
        prices = []
        for item in self.results:
            price_str = item.get('价格', '').replace('¥', '').replace(',', '').strip()
            if price_str and price_str.isdigit():
                prices.append(float(price_str))

        if prices:
            print(f"Price range: ¥{min(prices):.0f} - ¥{max(prices):.0f}")
            print(f"Average price: ¥{sum(prices)/len(prices):.0f}")

        # 地区统计
        locations = {}
        for item in self.results:
            location = item.get('地区', '').strip()
            if location:
                locations[location] = locations.get(location, 0) + 1

        if locations:
            print(f"\nLocation distribution:")
            for location, count in sorted(locations.items(), key=lambda x: x[1], reverse=True)[:5]:
                print(f"  {location}: {count} products")

    async def set_sort_to_latest(self):
        """设置排序方式为最新发布 - 集成鼠标悬停功能"""
        try:
            print("[排序设置] 正在设置最新发布排序（集成鼠标悬停功能）...")

            # 等待页面完全加载
            await asyncio.sleep(3)

            # 步骤1: 优先尝试鼠标悬停在"新发布"状态栏
            print("[排序设置] 步骤1: 尝试鼠标悬停在'新发布'状态栏...")

            # 使用改进版测试中成功的选择器
            new_publish_selectors = [
                'span:has-text("新发布")',
                'button:has-text("新发布")',
                'div:has-text("新发布")',
                '[class*="publish"]',
                '[class*="new"]',
                'span:has-text("发布")',
                'button:has-text("发布")',
                'div:has-text("发布")',
                'span:has-text("最新")',
                'button:has-text("最新")',
                'div:has-text("最新")',
                '[class*="time"]',
                '[class*="latest"]'
            ]

            new_publish_element = None
            new_publish_text = ""

            for selector in new_publish_selectors:
                try:
                    elements = await self.page.query_selector_all(selector)
                    for element in elements:
                        text = await element.text_content()
                        if text and ('新发布' in text or '发布' in text or '最新' in text):
                            new_publish_element = element
                            new_publish_text = text.strip()
                            print(f"[排序设置] 找到'新发布'状态栏: '{new_publish_text}'")
                            break
                    if new_publish_element:
                        break
                except Exception as e:
                    print(f"[排序设置] 检查选择器 {selector} 失败: {str(e)}")
                    continue

            if new_publish_element:
                print("[排序设置] 鼠标悬停在'新发布'状态栏上...")
                await new_publish_element.hover()
                await asyncio.sleep(2)  # 等待下拉菜单显示

                print("[排序设置] 寻找悬停后显示的排序选项...")

                # 寻找悬停后显示的排序选项
                sort_option_selectors = [
                    'text="最新发布"',
                    'text="最新"',
                    'text="时间最新"',
                    'text="发布时间"',
                    'text="最新上架"',
                    'div:has-text("最新发布")',
                    'span:has-text("最新发布")',
                    'li:has-text("最新发布")',
                    'a:has-text("最新发布")',
                    '[data-value*="latest"]',
                    '[data-value*="new"]',
                    '[data-value*="createTime"]',
                    '[data-value*="publishTime"]',
                    'div[role="menuitem"]:has-text("最新")',
                    'li[role="menuitem"]:has-text("最新")',
                    'a[role="menuitem"]:has-text("最新")',
                    'div:has-text("最新")',
                    'span:has-text("最新")',
                    'li:has-text("最新")',
                    'a:has-text("最新")',
                    'div:has-text("时间")',
                    'span:has-text("时间")',
                    'li:has-text("时间")'
                ]

                for selector in sort_option_selectors:
                    try:
                        option_elem = await self.page.wait_for_selector(selector, timeout=5000)
                        if option_elem:
                            text = await option_elem.text_content()
                            print(f"[排序设置] 找到排序选项: '{text}'")

                            # 点击选项
                            await option_elem.click()
                            await asyncio.sleep(5)

                            # 等待页面重新加载
                            await self.page.wait_for_load_state('networkidle', timeout=15000)
                            print("[排序设置] 鼠标悬停方式排序设置完成！")
                            return True
                    except:
                        continue

                # 如果悬停后没有找到选项，尝试点击"新发布"状态栏
                print("[排序设置] 悬停后未找到选项，尝试点击'新发布'状态栏...")
                await new_publish_element.click()
                await asyncio.sleep(3)

                for selector in sort_option_selectors:
                    try:
                        option_elem = await self.page.wait_for_selector(selector, timeout=3000)
                        if option_elem:
                            text = await option_elem.text_content()
                            print(f"[排序设置] 点击后找到选项: '{text}'")
                            await option_elem.click()
                            await asyncio.sleep(5)

                            await self.page.wait_for_load_state('networkidle', timeout=15000)
                            print("[排序设置] 点击'新发布'方式排序设置完成！")
                            return True
                    except:
                        continue

            # 步骤2: 备用方案 - 使用原有的点击排序区域方法
            print("[排序设置] 步骤2: 备用方案 - 查找排序/筛选区域...")

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
                'span:has-text("排序")',
                'div:has-text("综合")',
                'div:has-text("默认")'
            ]

            sort_area = None
            for selector in sort_trigger_selectors:
                try:
                    elements = await self.page.query_selector_all(selector)
                    print(f"[排序设置] 备用方案检查选择器 '{selector}': 找到 {len(elements)} 个元素")

                    for element in elements:
                        try:
                            text = await element.text_content()
                            if text and ('排序' in text or '筛选' in text or '综合' in text or '默认' in text):
                                sort_area = element
                                print(f"[排序设置] 备用方案找到排序区域: {selector}")
                                print(f"[排序设置] 排序区域文本: {text}")
                                break
                        except:
                            continue
                    if sort_area:
                        break
                except Exception as e:
                    print(f"[排序设置] 备用方案检查选择器 {selector} 时出错: {str(e)}")
                    continue

            if sort_area:
                print("[排序设置] 备用方案 - 点击排序区域...")
                await sort_area.click()
                await asyncio.sleep(3)

                latest_option = await self.find_latest_option()

                if latest_option:
                    print("[排序设置] 备用方案 - 点击最新发布选项...")
                    await latest_option.click()
                    await asyncio.sleep(5)

                    await self.page.wait_for_load_state('networkidle', timeout=15000)
                    print("[排序设置] 备用方案排序设置完成！")
                    return True
                else:
                    print("[排序设置] 备用方案也未找到选项，使用URL排序...")
                    return await self.set_sort_by_url()
            else:
                print("[排序设置] 所有方案都失败，直接使用URL排序...")
                return await self.set_sort_by_url()

        except Exception as e:
            print(f"[排序设置] 排序设置失败: {str(e)}")
            return False

    async def find_latest_option(self):
        """查找最新发布选项"""
        print("[排序设置] 正在查找最新发布选项...")

        # 最新发布选项的各种可能选择器 - 使用改进版测试中成功的逻辑
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
                print(f"[排序设置] 检查选择器 '{selector}': 找到 {len(elements)} 个元素")

                for element in elements:
                    try:
                        text = await element.text_content()
                        print(f"[排序设置] 元素文本: '{text}'")

                        # 检查是否包含最新相关的关键词
                        if (text and ('最新发布' in text or '最新' in text or '时间排序' in text or
                                    '发布时间' in text or '最新上架' in text or '发布' in text)):

                            # 确保不是其他包含这些词的选项
                            if not ('默认排序' in text or '综合排序' in text or '价格' in text):
                                latest_option = element
                                print(f"[排序设置] 找到最新发布选项: {selector}")
                                print(f"[排序设置] 选项文本: '{text}'")
                                break
                    except:
                        continue

                if latest_option:
                    break

            except Exception as e:
                print(f"[排序设置] 检查选择器 {selector} 时出错: {str(e)}")
                continue

        return latest_option

    async def set_sort_by_url(self):
        """通过URL设置排序"""
        try:
            current_url = self.page.url
            print(f"[排序设置] 当前URL: {current_url}")

            # 添加排序参数到URL
            if '?' in current_url:
                new_url = current_url + '&sort=createTime'
            else:
                new_url = current_url + '?sort=createTime'

            print(f"[排序设置] 通过URL设置排序: {new_url}")
            await self.page.goto(new_url, timeout=15000)
            await self.page.wait_for_load_state('networkidle', timeout=15000)
            await asyncio.sleep(3)
            print("[排序设置] URL排序设置完成")
            return True

        except Exception as e:
            print(f"[排序设置] URL排序设置失败: {str(e)}")
            return False

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

async def run_scraper(keyword="手机", max_pages=3, headless=True):
    """独立运行的爬虫函数 - 使用预设参数"""
    print("=" * 60)
    print("AUTO XIANYU SCRAPER")
    print("Using Playwright + Real Cookies")
    print("=" * 60)

    scraper = AutoXianyuScraper(headless=headless)

    try:
        print(f"Starting automatic search...")
        print(f"Keyword: {keyword}")
        print(f"Max pages: {max_pages}")
        print(f"Display mode: {'Headless (background)' if headless else 'Headed (visible browser)'}")

        # 设置浏览器
        if not await scraper.setup_browser():
            print("Browser setup failed")
            return False, "Browser setup failed"

        # 应用Cookie
        if not await scraper.apply_cookies():
            print("Cookie setup failed")
            return False, "Cookie setup failed"

        # 执行搜索（启用最新发布排序）
        success = await scraper.search_products(keyword, max_pages, delay=2, sort_by_latest=True)

        if success and scraper.results:
            # 保存结果
            filename = scraper.save_results(keyword)

            # 显示结果
            scraper.display_results(5)

            print(f"\n=== SUCCESS ===")
            print(f"File: {filename}")
            print(f"Products: {len(scraper.results)}")

            return True, f"成功爬取 {len(scraper.results)} 个商品"

        else:
            print("\n=== SEARCH FAILED ===")
            print("Possible reasons:")
            print("- Cookies expired")
            print("- Network issues")
            print("- Website anti-scraping updated")
            print("- Search conditions too strict")

            return False, "Search failed or no data found"

    except Exception as e:
        print(f"\nProgram error: {str(e)}")
        return False, f"Program error: {str(e)}"
    finally:
        await scraper.close()

async def main():
    """主函数 - 使用预设参数"""
    # 默认使用无头模式
    await run_scraper("手机", 3, headless=True)

if __name__ == "__main__":
    asyncio.run(main())