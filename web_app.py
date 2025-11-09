#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
闲鱼数据管理系统
Web后台应用 + 爬虫功能集成
"""

from flask import Flask, render_template, request, jsonify, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash, check_password_hash
import os
import sys
import asyncio
import re
import json

# 添加当前目录到路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 全局停止标志
scraping_should_stop = False

app = Flask(__name__)
app.config['SECRET_KEY'] = 'xianyu_data_management_2024'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///xianyu_data.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# 数据库模型
class User(db.Model):
    """用户模型"""
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, comment='用户名')
    password_hash = db.Column(db.String(255), nullable=False, comment='密码哈希')
    email = db.Column(db.String(120), comment='邮箱')
    role = db.Column(db.String(20), default='user', nullable=False, comment='用户角色 (admin/trial/user)')
    is_active = db.Column(db.Boolean, default=True, comment='账户是否激活')
    created_at = db.Column(db.DateTime, default=datetime.utcnow, comment='创建时间')
    last_login = db.Column(db.DateTime, comment='最后登录时间')
    trial_expires_at = db.Column(db.DateTime, comment='体验账户过期时间')
    trial_expired = db.Column(db.Boolean, default=False, comment='体验账户是否已过期')

    def set_password(self, password):
        """设置密码"""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """验证密码"""
        return check_password_hash(self.password_hash, password)

    def is_trial_expired(self):
        """检查体验账户是否过期"""
        if self.role != 'trial':
            return False

        # 如果已经标记为过期，直接返回
        if self.trial_expired:
            return True

        # 检查是否真的过期
        if not self.trial_expires_at:
            self.trial_expired = True
            return True

        is_expired = datetime.utcnow() > self.trial_expires_at
        if is_expired:
            self.trial_expired = True
            # 这里需要数据库上下文来保存，在外部调用时处理
        return is_expired

    def get_remaining_trial_days(self):
        """获取体验账户剩余天数"""
        if self.role != 'trial' or not self.trial_expires_at:
            return 0
        remaining = self.trial_expires_at - datetime.utcnow()
        return max(0, remaining.days)

    def get_remaining_trial_minutes(self):
        """获取体验账户剩余分钟数"""
        if self.role != 'trial' or not self.trial_expires_at:
            return 0
        remaining = self.trial_expires_at - datetime.utcnow()
        return max(0, int(remaining.total_seconds() / 60))

    def extend_trial(self, minutes=2):
        """延长体验账户时间"""
        if self.role != 'trial':
            return False

        # 重置过期状态
        self.trial_expired = False

        # 延长时间
        if self.trial_expires_at and datetime.utcnow() < self.trial_expires_at:
            # 如果还未过期，在现有时间基础上延长
            self.trial_expires_at += timedelta(minutes=minutes)
        else:
            # 如果已过期，从现在开始计算
            self.trial_expires_at = datetime.utcnow() + timedelta(minutes=minutes)

        return True

    def __repr__(self):
        return f'<User {self.username}>'

class XianyuProduct(db.Model):
    """闲鱼商品模型"""
    __tablename__ = 'xianyu_products'

    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.String(100), unique=True, nullable=False, comment='商品ID')
    title = db.Column(db.Text, comment='商品标题')
    price = db.Column(db.String(50), comment='价格')
    location = db.Column(db.String(100), comment='地区')
    seller_credit = db.Column(db.String(100), comment='卖家信用')
    product_link = db.Column(db.Text, comment='商品链接')
    product_image = db.Column(db.Text, comment='商品图片链接')
    keyword = db.Column(db.String(100), comment='搜索关键词')
    search_time = db.Column(db.DateTime, default=datetime.utcnow, comment='搜索时间')
    data_source = db.Column(db.String(100), default='Playwright+真实Cookie', comment='数据来源')
    created_at = db.Column(db.DateTime, default=datetime.utcnow, comment='创建时间')

    def __repr__(self):
        return f'<Product {self.product_id}>'

class SystemConfig(db.Model):
    """系统配置模型"""
    __tablename__ = 'system_config'

    id = db.Column(db.Integer, primary_key=True)
    config_key = db.Column(db.String(100), unique=True, nullable=False, comment='配置键')
    config_value = db.Column(db.Text, comment='配置值')
    description = db.Column(db.String(255), comment='描述')
    created_at = db.Column(db.DateTime, default=datetime.utcnow, comment='创建时间')
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment='更新时间')

    def __repr__(self):
        return f'<Config {self.config_key}>'

# 快速推送配置管理
class NotificationConfig(db.Model):
    """通知配置模型"""
    __tablename__ = 'notification_config'

    id = db.Column(db.Integer, primary_key=True)
    platform = db.Column(db.String(50), nullable=False, comment='通知平台：dingtalk, feishu, wechat_work, email')
    enabled = db.Column(db.Boolean, default=False, comment='是否启用')
    config_name = db.Column(db.String(100), nullable=False, comment='配置名称')
    webhook_url = db.Column(db.Text, comment='Webhook URL')
    access_token = db.Column(db.String(255), comment='访问令牌')
    secret = db.Column(db.String(255), comment='签名密钥')
    email_address = db.Column(db.String(255), comment='邮箱地址')
    email_smtp = db.Column(db.String(255), comment='SMTP服务器')
    email_password = db.Column(db.String(255), comment='邮箱密码/授权码')
    phone_number = db.Column(db.String(20), comment='手机号码')
    events = db.Column(db.Text, comment='触发事件JSON，如：{"start":true,"success":true,"error":true}')
    description = db.Column(db.String(255), comment='描述')
    latest_product_config = db.Column(db.Text, comment='最新发布商品推送配置JSON')
    created_at = db.Column(db.DateTime, default=datetime.utcnow, comment='创建时间')
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment='更新时间')

    def __repr__(self):
        return f'<NotificationConfig {self.platform}:{self.config_name}>'

class ProductMatchRule(db.Model):
    """产品匹配规则模型"""
    __tablename__ = 'product_match_rule'

    id = db.Column(db.Integer, primary_key=True)
    rule_name = db.Column(db.String(100), nullable=False, comment='规则名称')
    enabled = db.Column(db.Boolean, default=True, comment='是否启用')

    # 关键词匹配
    keywords_include = db.Column(db.Text, comment='包含关键词（逗号分隔）')
    keywords_exclude = db.Column(db.Text, comment='排除关键词（逗号分隔）')

    # 价格匹配
    price_min = db.Column(db.Float, comment='最低价格')
    price_max = db.Column(db.Float, comment='最高价格')

    # 地区匹配
    locations_include = db.Column(db.Text, comment='包含地区（逗号分隔）')
    locations_exclude = db.Column(db.Text, comment='排除地区（逗号分隔）')

    # 卖家信用
    seller_credit_min = db.Column(db.String(50), comment='最低卖家信用')

    # 通知配置
    notification_configs = db.Column(db.Text, comment='关联的通知配置ID列表（JSON）')

    # 匹配条件逻辑：AND/OR
    match_logic = db.Column(db.String(10), default='AND', comment='匹配逻辑：AND/OR')

    description = db.Column(db.String(255), comment='规则描述')
    created_at = db.Column(db.DateTime, default=datetime.utcnow, comment='创建时间')
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment='更新时间')

    def __repr__(self):
        return f'<ProductMatchRule {self.rule_name}>'

class QuickPushConfig:
    """快速推送配置类 - 使用SystemConfig存储配置"""

    @staticmethod
    def get_config():
        """获取快速推送配置"""
        try:
            # 从系统配置中获取快速推送设置
            config = {}

            # 启用状态
            enabled_config = SystemConfig.query.filter_by(config_key='quick_push_enabled').first()
            config['enabled'] = enabled_config.config_value == 'true' if enabled_config else False

            # 关键词
            keywords_config = SystemConfig.query.filter_by(config_key='quick_push_keywords').first()
            config['keywords'] = keywords_config.config_value if keywords_config else ''

            # 最低价格
            min_price_config = SystemConfig.query.filter_by(config_key='quick_push_min_price').first()
            config['min_price'] = float(min_price_config.config_value) if min_price_config and min_price_config.config_value else None

            # 最高价格
            max_price_config = SystemConfig.query.filter_by(config_key='quick_push_max_price').first()
            config['max_price'] = float(max_price_config.config_value) if max_price_config and max_price_config.config_value else None

            # 地区
            locations_config = SystemConfig.query.filter_by(config_key='quick_push_locations').first()
            config['locations'] = locations_config.config_value if locations_config else ''

            # 通知配置
            notifications_config = SystemConfig.query.filter_by(config_key='quick_push_notifications').first()
            if notifications_config and notifications_config.config_value:
                try:
                    config['notification_configs'] = json.loads(notifications_config.config_value)
                except:
                    config['notification_configs'] = []
            else:
                config['notification_configs'] = []

            return config

        except Exception as e:
            print(f"获取快速推送配置失败: {str(e)}")
            # 返回默认配置
            return {
                'enabled': False,
                'keywords': '',
                'min_price': None,
                'max_price': None,
                'locations': '',
                'notification_configs': []
            }

    @staticmethod
    def set_config(config):
        """设置快速推送配置"""
        try:
            # 启用状态
            enabled_config = SystemConfig.query.filter_by(config_key='quick_push_enabled').first()
            if enabled_config:
                enabled_config.config_value = str(config.get('enabled', False)).lower()
            else:
                enabled_config = SystemConfig(
                    config_key='quick_push_enabled',
                    config_value=str(config.get('enabled', False)).lower(),
                    description='快速推送启用状态'
                )
                db.session.add(enabled_config)

            # 关键词
            keywords_config = SystemConfig.query.filter_by(config_key='quick_push_keywords').first()
            if keywords_config:
                keywords_config.config_value = config.get('keywords', '')
            else:
                keywords_config = SystemConfig(
                    config_key='quick_push_keywords',
                    config_value=config.get('keywords', ''),
                    description='快速推送关键词'
                )
                db.session.add(keywords_config)

            # 最低价格
            min_price_config = SystemConfig.query.filter_by(config_key='quick_push_min_price').first()
            if min_price_config:
                min_price_config.config_value = str(config.get('min_price', '')) if config.get('min_price') is not None else ''
            else:
                min_price_config = SystemConfig(
                    config_key='quick_push_min_price',
                    config_value=str(config.get('min_price', '')) if config.get('min_price') is not None else '',
                    description='快速推送最低价格'
                )
                db.session.add(min_price_config)

            # 最高价格
            max_price_config = SystemConfig.query.filter_by(config_key='quick_push_max_price').first()
            if max_price_config:
                max_price_config.config_value = str(config.get('max_price', '')) if config.get('max_price') is not None else ''
            else:
                max_price_config = SystemConfig(
                    config_key='quick_push_max_price',
                    config_value=str(config.get('max_price', '')) if config.get('max_price') is not None else '',
                    description='快速推送最高价格'
                )
                db.session.add(max_price_config)

            # 地区
            locations_config = SystemConfig.query.filter_by(config_key='quick_push_locations').first()
            if locations_config:
                locations_config.config_value = config.get('locations', '')
            else:
                locations_config = SystemConfig(
                    config_key='quick_push_locations',
                    config_value=config.get('locations', ''),
                    description='快速推送地区'
                )
                db.session.add(locations_config)

            # 通知配置
            notifications_config = SystemConfig.query.filter_by(config_key='quick_push_notifications').first()
            if notifications_config:
                notifications_config.config_value = json.dumps(config.get('notification_configs', []))
            else:
                notifications_config = SystemConfig(
                    config_key='quick_push_notifications',
                    config_value=json.dumps(config.get('notification_configs', [])),
                    description='快速推送通知配置'
                )
                db.session.add(notifications_config)

            db.session.commit()
            return True

        except Exception as e:
            print(f"设置快速推送配置失败: {str(e)}")
            db.session.rollback()
            return False

# Cookie管理函数
def get_current_cookie():
    """获取当前Cookie"""
    try:
        config = SystemConfig.query.filter_by(config_key='xianyu_cookie').first()
        return config.config_value if config else None
    except:
        return None

def update_cookie(cookie_string):
    """更新Cookie"""
    try:
        config = SystemConfig.query.filter_by(config_key='xianyu_cookie').first()
        if config:
            config.config_value = cookie_string
            config.updated_at = datetime.utcnow()
        else:
            config = SystemConfig(
                config_key='xianyu_cookie',
                config_value=cookie_string,
                description='闲鱼Cookie字符串'
            )
            db.session.add(config)

        db.session.commit()
        return True
    except Exception as e:
        db.session.rollback()
        print(f"更新Cookie失败: {str(e)}")
        return False

def parse_cookie_info(cookie_string):
    """解析Cookie信息"""
    if not cookie_string:
        return {}

    info = {
        'count': 0,
        'username': '',
        'expiry': ''
    }

    try:
        # 计算Cookie数量
        cookies = [item.strip() for item in cookie_string.split(';') if '=' in item.strip()]
        info['count'] = len(cookies)

        # 查找用户名
        for cookie in cookies:
            if 'tracknick=' in cookie:
                info['username'] = cookie.split('=')[1] if '=' in cookie else ''
                break

        # 设置默认有效期为30天
        info['expiry'] = (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d')

    except Exception as e:
        print(f"解析Cookie失败: {str(e)}")

    return info

def test_cookie_validity(cookie_string):
    """测试Cookie有效性"""
    try:
        # 基本格式检查
        if not cookie_string:
            return {'valid': False, 'error': 'Cookie不能为空'}

        if len(cookie_string) < 50:
            return {'valid': False, 'error': 'Cookie太短，可能无效'}

        if 'tracknick=' not in cookie_string:
            return {'valid': False, 'error': 'Cookie格式错误，缺少tracknick'}

        return {'valid': True}

    except Exception as e:
        return {'valid': False, 'error': f'测试失败: {str(e)}'}

# 数据库初始化函数
def init_db():
    """初始化数据库"""
    with app.app_context():
        # 创建所有表
        db.create_all()

        # 创建默认用户（如果不存在）
        create_default_users()

    print("Database initialized successfully!")

def create_default_users():
    """创建默认用户账户"""
    try:
        # 检查是否已有管理员用户
        admin_user = User.query.filter_by(username='admin').first()
        if not admin_user:
            # 创建超级管理员
            admin_user = User(
                username='admin',
                email='admin@xianyu-system.com',
                role='admin',
                is_active=True
            )
            admin_user.set_password('admin123')
            db.session.add(admin_user)
            print("Created admin user: admin/admin123")

        # 检查是否已有体验用户
        trial_user = User.query.filter_by(username='trial').first()
        if not trial_user:
            # 创建体验账户（2分钟有效期，用于测试）
            trial_user = User(
                username='trial',
                email='trial@xianyu-system.com',
                role='trial',
                is_active=True,
                trial_expires_at=datetime.utcnow() + timedelta(minutes=2)
            )
            trial_user.set_password('trial123')
            db.session.add(trial_user)
            print("Created trial user: trial/trial123 (2 minutes)")

        db.session.commit()
        print("Default users created successfully!")

    except Exception as e:
        print(f"Error creating default users: {e}")
        db.session.rollback()

# 导入爬虫功能
async def scrape_xianyu_data(keyword, max_pages=3, delay=2):
    """爬取闲鱼数据并保存到数据库"""
    global scraping_should_stop
    print(f"[开始爬取] 关键词={keyword}, 页数={max_pages}, 延迟策略={delay}秒")
    print(f"[延迟范围] 预期翻页延迟: {delay*0.7:.1f}-{delay*1.3+2:.1f}秒")

    # 触发开始爬取通知 - 修复编码问题
    try:
        NotificationService.trigger_notification(
            'start',
            '爬取任务开始',
            f"关键词: {keyword}\n目标页数: {max_pages}\n延迟策略: {delay}秒"
        )
    except Exception as e:
        print(f"[通知] 发送开始通知失败: {str(e)}")

    try:
        # 导入爬虫模块
        from 自动运行抓取器 import AutoXianyuScraper

        # 获取当前配置的Cookie
        current_cookie = get_current_cookie()
        if not current_cookie:
            return False, "未配置Cookie，请先在系统设置中添加Cookie"

        scraper = AutoXianyuScraper(cookie_string=current_cookie)

        # 设置浏览器
        if not await scraper.setup_browser(headless=True):
            return False, "浏览器设置失败"

        # 检查是否需要停止
        if scraping_should_stop:
            print("[停止爬取] 用户请求停止任务")
            # 触发停止通知
            try:
                NotificationService.trigger_notification(
                    'stop',
                    '⏹️ 爬取任务已停止',
                    f"用户主动停止了爬取任务\n关键词: {keyword}\n已处理的数据将被保存"
                )
            except Exception as e:
                print(f"[通知] 发送停止通知失败: {str(e)}")
            return False, "用户主动停止爬取"

        # 应用Cookie
        if not await scraper.apply_cookies():
            return False, "Cookie设置失败"

        # 检查是否需要停止
        if scraping_should_stop:
            print("[停止爬取] 用户请求停止任务")
            return False, "用户主动停止爬取"

        # 执行搜索（启用最新发布排序）
        success = await scraper.search_products(keyword, max_pages, delay, sort_by_latest=True)

        # 检查是否需要停止
        if scraping_should_stop:
            print("[停止爬取] 用户请求停止任务")
            return False, "用户主动停止爬取"

        if success and scraper.results:
            # 保存到数据库
            saved_count = 0
            duplicate_count = 0
            for item in scraper.results:
                # 检查是否需要停止
                if scraping_should_stop:
                    print("[停止爬取] 用户请求停止任务，正在保存已爬取的数据...")
                    break
                try:
                    product_id = item.get('商品ID', '')
                    title = item.get('商品标题', '')

                    if product_id and title:
                        # 检查是否已存在
                        existing = XianyuProduct.query.filter_by(product_id=product_id).first()
                        if not existing:
                            product = XianyuProduct(
                                product_id=product_id,
                                title=title,
                                price=item.get('价格', ''),
                                location=item.get('地区', ''),
                                seller_credit=item.get('卖家信用', ''),
                                product_link=item.get('商品链接', ''),
                                product_image=item.get('商品图片', ''),
                                keyword=keyword,  # 直接使用搜索的关键词
                                search_time=datetime.now()
                            )
                            db.session.add(product)
                            db.session.commit()  # 立即提交以便获取ID

                            # 立即检查产品匹配规则
                            try:
                                product_data = {
                                    'title': title,
                                    'price': item.get('价格', ''),
                                    'location': item.get('地区', ''),
                                    'seller_credit': item.get('卖家信用', ''),
                                    'keyword': keyword,
                                    'product_link': item.get('商品链接', ''),
                                    'product_id': product_id
                                }

                                matched = NotificationService.process_product_matching(product_data)
                                if matched:
                                    print(f"[产品匹配] 发现匹配产品: {title[:30]}...")

                            except Exception as e:
                                print(f"[产品匹配] 处理匹配时出错: {str(e)}")

                            saved_count += 1
                        else:
                            duplicate_count += 1
                except Exception as e:
                    print(f"保存商品失败: {str(e)}")
                    continue

            # 最后再提交一次（以防有未提交的数据）
            try:
                db.session.commit()
            except:
                pass  # 如果已经提交过，忽略错误
            await scraper.close()

            # 修复字符编码问题 - 使用ASCII安全的消息
            message = f"成功爬取 {len(scraper.results)} 个商品"
            if saved_count > 0:
                message += f"，保存 {saved_count} 个新商品"
            if duplicate_count > 0:
                message += f"，跳过 {duplicate_count} 个重复商品"

            # 确保消息可以正确编码
            try:
                message.encode('utf-8')
            except UnicodeEncodeError:
                message = "爬取完成，请查看详细日志"

            # 触发成功通知 - 修复编码问题
            try:
                NotificationService.trigger_notification(
                    'success',
                    '爬取任务完成',
                    f"{message}\n\n统计详情:\n• 爬取商品: {len(scraper.results)} 个\n• 新增商品: {saved_count} 个\n• 重复商品: {duplicate_count} 个"
                )
            except Exception as e:
                print(f"[通知] 发送成功通知失败: {str(e)}")

            # 自动触发最新发布商品推送
            if saved_count > 0:
                try:
                    print(f"[最新推送] 开始推送最新商品，新增 {saved_count} 个商品")
  
                    # 获取启用了最新商品推送的通知配置
                    latest_product_configs = NotificationService.get_latest_product_configs()

                    if latest_product_configs:
                        sent_count = 0
                        # 获取最新的商品（根据保存数量获取）
                        latest_products = XianyuProduct.query.order_by(XianyuProduct.search_time.desc()).limit(saved_count).all()

                        for config in latest_product_configs:
                            try:
                                # 为每个商品单独发送推送
                                for product in latest_products:
                                    # 计算时间差
                                    time_diff = datetime.now() - product.search_time
                                    if time_diff.total_seconds() < 3600:  # 1小时内
                                        time_str = f"{int(time_diff.total_seconds() / 60)}分钟前"
                                    elif time_diff.total_seconds() < 86400:  # 1天内
                                        time_str = f"{int(time_diff.total_seconds() / 3600)}小时前"
                                    else:
                                        time_str = f"{time_diff.days}天前"

                                    # 构建推送内容 - 修复编码问题
                                    title = "新商品推送!"
                                    product_title = product.title or '无标题'
                                    product_id = product.product_id

                                    # 生成移动端链接
                                    def generate_mobile_xianyu_links(product_id):
                                        """生成官方Goofish H5链接格式"""
                                        links = {}
                                        links['goofish_h5'] = f"https://h5.m.goofish.com/item?forceFlush=1&id={product_id}&hitNativeDetail=true&from_kun_share=default"
                                        return links

                                    mobile_links = generate_mobile_xianyu_links(product_id)

                                    # 构建链接文本
                                    link_text = f"[闲鱼APP]({mobile_links['goofish_h5']})"

                                    # 构建完整内容 - 添加图片信息
                                    content_parts = [
                                        "",
                                        "- 商品详情 -",
                                        f"{product_title}",
                                        "----------------------------------------"
                                    ]

                                    # 添加图片信息（如果有图片）
                                    if product.product_image and product.product_image.strip():
                                        content_parts.append(f"- 📷 商品图片：{product.product_image}")
                                        content_parts.append("----------------------------------------")

                                    content_parts.extend([
                                        f"-💰价格:{product.price or '面议'}  -⏰时间:{time_str}  -🗺地区:{product.location or '未知'}",
                                        "----------------------------------------",
                                        f"- 🔗 商品链接：{link_text}"
                                    ])
                                    content = "\n".join(content_parts)

                                    # 发送通知
                                    if NotificationService.send_notification(config, title, content):
                                        sent_count += 1
                                        print(f"[最新推送] 成功推送商品: {product_title[:30]}...")
                                        time.sleep(1)  # 避免发送过快
                                    else:
                                        print(f"[最新推送] 推送失败: {product_title[:30]}...")

                                print(f"[最新推送] 配置 '{config.config_name}' 推送完成，共推送 {sent_count} 个商品")

                            except Exception as e:
                                print(f"[最新推送] 配置 '{config.config_name}' 推送失败: {str(e)}")

                        print(f"[最新推送] 所有配置推送完成，总计推送 {sent_count} 个商品")
                    else:
                        print("[最新推送] 没有找到启用最新商品推送的配置")

                except Exception as e:
                    print(f"[最新推送] 自动推送失败: {str(e)}")

            return True, message
        else:
            await scraper.close()
            error_message = "爬取失败或没有获取到数据"
            # 触发错误通知
            try:
                NotificationService.trigger_notification(
                    'error',
                    '❌ 爬取任务失败',
                    f"错误信息: {error_message}\n关键词: {keyword}\n请检查网络连接和Cookie配置"
                )
            except Exception as e:
                print(f"[通知] 发送错误通知失败: {str(e)}")
            return False, error_message

    except Exception as e:
        error_message = f"爬取过程出错: {str(e)}"
        # 触发错误通知
        try:
            NotificationService.trigger_notification(
                'error',
                '❌ 爬取任务异常',
                f"异常信息: {error_message}\n关键词: {keyword}\n请检查系统配置和网络连接"
            )
        except Exception as e:
            print(f"[通知] 发送异常通知失败: {str(e)}")
        return False, error_message

# Web路由
def parse_price(price_str):
    """解析价格字符串为数字"""
    if not price_str:
        return 0
    try:
        # 移除常见的货币符号和非数字字符
        import re
        cleaned = re.sub(r'[^\d.]', '', str(price_str))
        return float(cleaned) if cleaned else 0
    except:
        return 0


# 登录验证装饰器
def login_required(f):
    """登录验证装饰器"""
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))

        user = User.query.get(session['user_id'])
        if not user or not user.is_active:
            session.clear()
            return redirect(url_for('login'))

        # 体验账户严格检查
        if user.role == 'trial':
            # 检查是否过期
            if user.is_trial_expired():
                # 标记为已过期并保存到数据库
                user.trial_expired = True
                db.session.commit()
                flash('您的体验账户已过期，请联系管理员续费', 'error')
                session.clear()
                return redirect(url_for('login'))

            # 如果即将过期（剩余少于30秒），显示警告
            remaining_minutes = user.get_remaining_trial_minutes()
            if remaining_minutes <= 0.5:  # 30秒
                # 标记为已过期并保存到数据库
                user.trial_expired = True
                db.session.commit()
                flash('您的体验账户已过期，请联系管理员续费', 'error')
                session.clear()
                return redirect(url_for('login'))

        return f(*args, **kwargs)
    return decorated_function

# 登录路由
@app.route('/login', methods=['GET', 'POST'])
def login():
    """登录页面"""
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')

        if not username or not password:
            flash('请输入用户名和密码', 'error')
            return render_template('login.html')

        # 查找用户
        user = User.query.filter_by(username=username).first()

        if not user or not user.check_password(password):
            flash('用户名或密码错误', 'error')
            return render_template('login.html')

        if not user.is_active:
            flash('账户已被禁用', 'error')
            return render_template('login.html')

        # 如果是体验账户且还没有设置过期时间，则在首次登录时开始3天倒计时
        if user.role == 'trial' and not user.trial_expires_at:
            user.trial_expires_at = datetime.utcnow() + timedelta(days=3)
            user.trial_expired = False

        # 检查体验账户是否过期
        if user.is_trial_expired():
            flash('您的体验账户已过期，请联系管理员', 'error')
            return render_template('login.html')

        # 登录成功，设置会话
        session['user_id'] = user.id
        session['username'] = user.username
        session['role'] = user.role
        user.last_login = datetime.utcnow()
        db.session.commit()

        flash(f'欢迎回来，{user.username}！', 'success')
        return redirect(url_for('index'))

    return render_template('login.html')

# 登出路由
@app.route('/logout')
def logout():
    """登出"""
    session.clear()
    flash('您已成功登出', 'info')
    return redirect(url_for('login'))

@app.route('/')
@login_required
def index():
    """首页 - 显示商品列表"""
    page = request.args.get('page', 1, type=int)
    search_query = request.args.get('search', '')
    keyword_filter = request.args.get('keyword', '')
    sort_by = request.args.get('sort_by', 'created_at')  # 默认按创建时间排序
    sort_order = request.args.get('sort_order', 'desc')   # 默认降序

    # 构建查询 - 只显示有图片的产品
    query = XianyuProduct.query.filter(
        XianyuProduct.product_image.isnot(None),
        XianyuProduct.product_image != ''
    )

    if search_query:
        query = query.filter(XianyuProduct.title.contains(search_query))

    if keyword_filter:
        query = query.filter(XianyuProduct.keyword.contains(keyword_filter))

    
    # 排序逻辑
    if sort_by == 'price':
        # 价格排序需要在Python层面处理，先获取所有数据
        all_products = query.all()

        # 解析价格并排序
        def get_price_for_sort(product):
            return parse_price(product.price)

        # 排序
        all_products.sort(key=get_price_for_sort, reverse=(sort_order == 'desc'))

        # 手动分页
        per_page = 15
        start = (page - 1) * per_page
        end = start + per_page
        page_products = all_products[start:end]

        # 创建简单的分页对象
        class SimplePagination:
            def __init__(self, items, total, page, per_page):
                self.items = items
                self.total = total
                self.page = page
                self.per_page = per_page
                self.pages = (total + per_page - 1) // per_page
                self.has_prev = page > 1
                self.has_next = page < self.pages
                self.prev_num = page - 1 if self.has_prev else None
                self.next_num = page + 1 if self.has_next else None

            def iter_pages(self):
                """生成页码范围，用于模板渲染"""
                left_edge = 2
                right_edge = 2
                left_current = max(1, self.page - left_edge)
                right_current = min(self.pages, self.page + right_edge)

                if left_current > 1:
                    yield 1
                    if left_current > 2:
                        yield None

                for page_num in range(left_current, right_current + 1):
                    yield page_num

                if right_current < self.pages:
                    if right_current < self.pages - 1:
                        yield None
                    yield self.pages

        products = SimplePagination(page_products, len(all_products), page, per_page)
    elif sort_by == 'search_time':
        # 按搜索时间排序
        if sort_order == 'asc':
            query = query.order_by(XianyuProduct.search_time.asc().nulls_last())
        else:
            query = query.order_by(XianyuProduct.search_time.desc().nulls_last())

        products = query.paginate(page=page, per_page=15, error_out=False)
    else:
        # 默认按创建时间排序
        if sort_order == 'asc':
            query = query.order_by(XianyuProduct.created_at.asc())
        else:
            query = query.order_by(XianyuProduct.created_at.desc())

        products = query.paginate(page=page, per_page=15, error_out=False)

    # 获取所有关键词
    keywords = db.session.query(XianyuProduct.keyword).distinct().all()
    keywords = [k[0] for k in keywords if k[0]]

    return render_template('index.html',
                         products=products,
                         search_query=search_query,
                         keyword_filter=keyword_filter,
                         keywords=keywords,
                         sort_by=sort_by,
                         sort_order=sort_order,
                         parse_price=parse_price)

@app.route('/product/<int:id>')
@login_required
def product_detail(id):
    """商品详情页"""
    product = XianyuProduct.query.get_or_404(id)
    return render_template('product_detail.html', product=product)

@app.route('/scrape', methods=['GET', 'POST'])
@login_required
def scrape():
    """爬取页面"""
    if request.method == 'GET':
        return render_template('scrape.html')

    # 处理POST请求
    keyword = request.form.get('keyword', '手机')
    max_pages = int(request.form.get('max_pages', 3))
    delay = int(request.form.get('delay', 2))  # 接收延迟参数，默认2秒

    try:
        # 重置全局停止标志
        global scraping_should_stop
        scraping_should_stop = False

        # 在新的事件循环中运行异步爬虫
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        success, message = loop.run_until_complete(scrape_xianyu_data(keyword, max_pages, delay))
        loop.close()

        if success:
            return jsonify({
                'success': True,
                'message': message,
                'redirect': url_for('index')
            })
        else:
            return jsonify({'success': False, 'message': message})

    except Exception as e:
        # 修复字符编码问题
        error_msg = str(e)
        if hasattr(error_msg, 'encode'):
            try:
                error_msg = error_msg.encode('utf-8', errors='ignore').decode('utf-8')
            except:
                error_msg = "执行过程中出现错误，请检查日志"
        return jsonify({'success': False, 'message': f'执行出错: {error_msg}'})

@app.route('/api/products')
def api_products():
    """API接口 - 获取商品数据"""
    search_query = request.args.get('search', '')
    keyword_filter = request.args.get('keyword', '')
    page = request.args.get('page', 1, type=int)
    sort_by = request.args.get('sort_by', 'created_at')  # 默认按创建时间排序
    sort_order = request.args.get('sort_order', 'desc')   # 默认降序

    # 构建查询 - 只显示有图片的产品
    query = XianyuProduct.query.filter(
        XianyuProduct.product_image.isnot(None),
        XianyuProduct.product_image != ''
    )

    if search_query:
        query = query.filter(XianyuProduct.title.contains(search_query))

    if keyword_filter:
        query = query.filter(XianyuProduct.keyword.contains(keyword_filter))

    # 排序逻辑
    if sort_by == 'price':
        # 价格排序需要在Python层面处理，先获取所有数据
        all_products = query.all()

        # 解析价格并排序
        def get_price_for_sort(product):
            return parse_price(product.price)

        # 排序
        all_products.sort(key=get_price_for_sort, reverse=(sort_order == 'desc'))

        # 手动分页
        per_page = 15
        start = (page - 1) * per_page
        end = start + per_page
        page_products = all_products[start:end]

        # 创建简单的分页对象
        class SimplePagination:
            def __init__(self, items, total, page, per_page):
                self.items = items
                self.total = total
                self.page = page
                self.per_page = per_page
                self.pages = (total + per_page - 1) // per_page
                self.has_prev = page > 1
                self.has_next = page < self.pages
                self.prev_num = page - 1 if self.has_prev else None
                self.next_num = page + 1 if self.has_next else None

            def iter_pages(self):
                """生成页码范围，用于模板渲染"""
                left_edge = 2
                right_edge = 2
                left_current = max(1, self.page - left_edge)
                right_current = min(self.pages, self.page + right_edge)

                if left_current > 1:
                    yield 1
                    if left_current > 2:
                        yield None

                for page_num in range(left_current, right_current + 1):
                    yield page_num

                if right_current < self.pages:
                    if right_current < self.pages - 1:
                        yield None
                    yield self.pages

        products = SimplePagination(page_products, len(all_products), page, per_page)
    else:
        # 默认按创建时间排序
        if sort_order == 'asc':
            query = query.order_by(XianyuProduct.created_at.asc())
        else:
            query = query.order_by(XianyuProduct.created_at.desc())

        products = query.paginate(page=page, per_page=15, error_out=False)

    # 转换为JSON
    result = {
        'products': [
            {
                'id': p.id,
                'product_id': p.product_id,
                'title': p.title,
                'price': p.price,
                'location': p.location,
                'seller_credit': p.seller_credit,
                'keyword': p.keyword,
                'search_time': p.search_time.strftime('%Y-%m-%d %H:%M:%S') if p.search_time else '',
                'data_source': p.data_source,
                'created_at': p.created_at.strftime('%Y-%m-%d %H:%M:%S') if p.created_at else ''
            }
            for p in products.items
        ],
        'pagination': {
            'page': products.page,
            'pages': products.pages,
            'per_page': products.per_page,
            'total': products.total,
            'has_next': products.has_next,
            'has_prev': products.has_prev
        },
        'sort_info': {
            'sort_by': sort_by,
            'sort_order': sort_order
        }
    }

    return jsonify(result)

@app.route('/api/trial-info')
@login_required
def api_trial_info():
    """API接口 - 获取体验账户信息"""
    if 'user_id' not in session:
        return jsonify({'error': '未登录'}), 401

    user = User.query.get(session['user_id'])
    if not user or user.role != 'trial':
        return jsonify({'error': '不是体验账户'}), 400

    remaining_minutes = user.get_remaining_trial_minutes()
    return jsonify({
        'remaining_minutes': remaining_minutes,
        'remaining_seconds': remaining_minutes * 60,
        'trial_expires_at': user.trial_expires_at.isoformat() if user.trial_expires_at else None,
        'is_expired': user.is_trial_expired(),
        'trial_expired': user.trial_expired
    })

@app.route('/api/admin/extend-trial', methods=['POST'])
@login_required
def api_extend_trial():
    """API接口 - 管理员延长体验账户时间"""
    if 'user_id' not in session:
        return jsonify({'error': '未登录'}), 401

    # 只有管理员可以延长体验账户
    current_user = User.query.get(session['user_id'])
    if not current_user or current_user.role != 'admin':
        return jsonify({'error': '权限不足'}), 403

    # 获取要延长的用户
    data = request.get_json()
    target_username = data.get('username')
    extend_minutes = data.get('minutes', 2)

    if not target_username:
        return jsonify({'error': '缺少用户名参数'}), 400

    # 查找目标用户
    target_user = User.query.filter_by(username=target_username).first()
    if not target_user:
        return jsonify({'error': '用户不存在'}), 404

    if target_user.role != 'trial':
        return jsonify({'error': '只能延长体验账户时间'}), 400

    try:
        # 延长体验时间
        success = target_user.extend_trial(extend_minutes)
        if success:
            db.session.commit()
            return jsonify({
                'success': True,
                'message': f'已为用户 {target_username} 延长体验时间 {extend_minutes} 分钟',
                'new_expires_at': target_user.trial_expires_at.isoformat(),
                'remaining_minutes': target_user.get_remaining_trial_minutes()
            })
        else:
            return jsonify({'error': '延长失败'}), 500
    except Exception as e:
        return jsonify({'error': f'延长失败: {str(e)}'}), 500

@app.route('/api/admin/trial-users-status', methods=['GET'])
@login_required
def api_trial_users_status():
    """API接口 - 获取所有体验账户状态"""
    if 'user_id' not in session:
        return jsonify({'error': '未登录'}), 401

    # 只有管理员可以查看体验账户状态
    current_user = User.query.get(session['user_id'])
    if not current_user or current_user.role != 'admin':
        return jsonify({'error': '权限不足'}), 403

    try:
        # 获取所有体验账户
        trial_users = User.query.filter_by(role='trial').all()

        users_status = []
        for user in trial_users:
            remaining_minutes = user.get_remaining_trial_minutes()
            users_status.append({
                'username': user.username,
                'remaining_minutes': remaining_minutes,
                'remaining_seconds': remaining_minutes * 60,
                'is_expired': user.is_trial_expired(),
                'trial_expired': user.trial_expired,
                'trial_expires_at': user.trial_expires_at.isoformat() if user.trial_expires_at else None
            })

        return jsonify({
            'success': True,
            'trial_users': users_status,
            'total_count': len(users_status)
        })
    except Exception as e:
        return jsonify({'error': f'获取状态失败: {str(e)}'}), 500

@app.route('/api/stats')
def api_stats():
    """API接口 - 获取统计信息"""
    # 只统计有图片的产品
    total_products = XianyuProduct.query.filter(
        XianyuProduct.product_image.isnot(None),
        XianyuProduct.product_image != ''
    ).count()

    # 价格统计 - 只统计有图片的产品
    products_with_prices = XianyuProduct.query.filter(
        XianyuProduct.product_image.isnot(None),
        XianyuProduct.product_image != '',
        XianyuProduct.price.isnot(None)
    ).all()
    prices = []
    for p in products_with_prices:
        price_str = p.price.replace('¥', '').replace(',', '').strip()
        if price_str and price_str.replace('.', '').isdigit():
            try:
                prices.append(float(price_str))
            except:
                continue

    # 关键词统计
    keyword_stats = db.session.query(
        XianyuProduct.keyword,
        db.func.count(XianyuProduct.id)
    ).group_by(XianyuProduct.keyword).all()

    # 今日新增统计 - 只统计有图片的产品
    from datetime import date
    today = date.today()
    today_products = XianyuProduct.query.filter(
        XianyuProduct.product_image.isnot(None),
        XianyuProduct.product_image != '',
        db.func.date(XianyuProduct.created_at) == today
    ).count()

    stats = {
        'total_products': total_products,
        'today_new': today_products,  # 添加今日新增数据
        'price_stats': {
            'count': len(prices),
            'min_price': min(prices) if prices else 0,
            'max_price': max(prices) if prices else 0,
            'avg_price': sum(prices)/len(prices) if prices else 0
        },
        'keyword_distribution': [
            {'keyword': k[0], 'count': k[1]}
            for k in keyword_stats if k[0]
        ]
    }

    return jsonify(stats)

@app.route('/delete/<int:id>', methods=['POST'])
def delete_product(id):
    """删除商品"""
    product = XianyuProduct.query.get_or_404(id)
    db.session.delete(product)
    db.session.commit()

    return jsonify({'success': True, 'message': '商品已删除'})

@app.route('/stats')
@login_required
def stats():
    """统计页面"""
    return render_template('stats.html')

@app.route('/system_settings')
@login_required
def system_settings():
    """系统设置页面"""
    current_cookie = get_current_cookie()
    return render_template('system_settings.html', current_cookie=current_cookie)

@app.route('/push-diagnosis')
def push_diagnosis():
    """推送诊断页面"""
    return render_template('推送诊断.html')

@app.route('/scrape-diagnosis')
def scrape_diagnosis():
    """爬取诊断页面"""
    return render_template('爬取诊断.html')


@app.route('/api/check-cookie', methods=['POST'])
def api_check_cookie():
    """检查Cookie有效性"""
    try:
        # 获取前端传来的Cookie参数
        cookie_to_test = None

        # 尝试从JSON数据获取Cookie
        try:
            data = request.get_json()
            if data and 'cookie' in data:
                cookie_to_test = data['cookie'].strip()
        except:
            pass

        # 如果JSON中没有Cookie，尝试从表单数据获取
        if not cookie_to_test:
            cookie_to_test = request.form.get('cookie', '').strip()

        # 如果都没有，使用当前配置的Cookie
        if not cookie_to_test:
            cookie_to_test = get_current_cookie()
            if not cookie_to_test:
                return jsonify({'valid': False, 'message': '没有配置Cookie'})

        if not cookie_to_test:
            return jsonify({'valid': False, 'message': 'Cookie为空'})

        # 使用同步的Cookie检查函数
        test_result = test_cookie_validity(cookie_to_test)
        info = parse_cookie_info(cookie_to_test)

        if test_result['valid']:
            result = {
                'valid': True,
                'message': 'Cookie验证通过',
                'cookie_count': len(cookie_to_test.split(';')),
                'username': info.get('username', '已登录'),
                'expiry': info.get('expiry', '未知'),
                'info': info
            }
        else:
            result = {'valid': False, 'message': test_result.get('error', 'Cookie无效或已过期')}

        return jsonify(result)
    except Exception as e:
        return jsonify({'valid': False, 'message': f'验证过程出错: {str(e)}'})

@app.route('/api/update-cookie', methods=['POST'])
def api_update_cookie():
    """更新Cookie"""
    try:
        data = request.get_json()
        cookie_string = data.get('cookie', '').strip()

        if not cookie_string:
            return jsonify({'success': False, 'message': 'Cookie不能为空'})

        if update_cookie(cookie_string):
            return jsonify({'success': True, 'message': 'Cookie更新成功'})
        else:
            return jsonify({'success': False, 'message': 'Cookie更新失败'})

    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/stop-scraping', methods=['POST'])
def api_stop_scraping():
    """停止爬虫任务"""
    global scraping_should_stop
    try:
        # 设置全局停止标志
        scraping_should_stop = True

        return jsonify({
            'success': True,
            'message': '正在停止爬虫任务...'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'停止爬虫失败: {str(e)}'
        })

@app.route('/api/system-info')
def api_system_info():
    """获取系统信息"""
    try:
        import psutil
        import platform

        # 系统基本信息
        info = {
            'system': platform.system(),
            'python_version': platform.python_version(),
            'platform': platform.platform(),
            'cpu_count': psutil.cpu_count(),
            'memory_total': psutil.virtual_memory().total,
            'memory_available': psutil.virtual_memory().available,
            'disk_usage': psutil.disk_usage('/').percent if platform.system() != 'Windows' else psutil.disk_usage('C:').percent,
            'boot_time': datetime.fromtimestamp(psutil.boot_time()).strftime('%Y-%m-%d %H:%M:%S')
        }

        # 计算运行时间
        uptime_seconds = (datetime.now() - datetime.fromtimestamp(psutil.boot_time())).total_seconds()
        days = int(uptime_seconds // 86400)
        hours = int((uptime_seconds % 86400) // 3600)
        minutes = int((uptime_seconds % 3600) // 60)
        info['uptime'] = f"{days}天 {hours}小时 {minutes}分钟"

        return jsonify(info)
    except ImportError:
        # 如果没有安装psutil，返回基本信息
        return jsonify({
            'system': platform.system(),
            'python_version': platform.python_version(),
            'platform': platform.platform(),
            'uptime': '未知'
        })
    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/api/delete-keyword', methods=['POST'])
def api_delete_keyword():
    """删除特定关键词及其所有相关商品"""
    try:
        data = request.get_json()
        keyword = data.get('keyword', '').strip()

        if not keyword:
            return jsonify({'success': False, 'message': '关键词不能为空'})

        # 查找该关键词的所有商品
        products_to_delete = XianyuProduct.query.filter_by(keyword=keyword).all()

        if not products_to_delete:
            return jsonify({'success': False, 'message': f'未找到关键词 "{keyword}" 相关的商品'})

        deleted_count = len(products_to_delete)

        # 删除所有相关商品
        for product in products_to_delete:
            db.session.delete(product)

        db.session.commit()

        return jsonify({
            'success': True,
            'message': f'成功删除关键词 "{keyword}" 及其 {deleted_count} 个商品',
            'deleted_count': deleted_count
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'删除失败: {str(e)}'})

@app.route('/api/cleanup-data', methods=['POST'])
def api_cleanup_data():
    """数据清理API"""
    try:
        data = request.get_json()
        option = data.get('option', 'all')

        deleted_count = 0

        if option == 'all':
            # 删除所有数据
            all_products = XianyuProduct.query.all()
            for product in all_products:
                db.session.delete(product)
            deleted_count = len(all_products)

        elif option == 'old':
            # 删除30天前的数据
            thirty_days_ago = datetime.now() - timedelta(days=30)
            old_products = XianyuProduct.query.filter(
                XianyuProduct.created_at < thirty_days_ago
            ).all()
            for product in old_products:
                db.session.delete(product)
            deleted_count = len(old_products)

        elif option == 'duplicates':
            # 删除重复数据（保留最新的）
            # 查找重复的商品ID
            duplicates = db.session.query(
                XianyuProduct.product_id
            ).group_by(
                XianyuProduct.product_id
            ).having(
                func.count(XianyuProduct.product_id) > 1
            ).all()

            for product_id, in duplicates:
                # 获取该商品ID的所有记录，按创建时间倒序
                duplicate_records = XianyuProduct.query.filter_by(
                    product_id=product_id
                ).order_by(
                    XianyuProduct.created_at.desc()
                ).all()

                # 保留第一条（最新的），删除其余的
                for record in duplicate_records[1:]:
                    db.session.delete(record)
                    deleted_count += 1

        else:
            return jsonify({'success': False, 'message': '无效的清理选项'})

        db.session.commit()

        return jsonify({
            'success': True,
            'message': f'数据清理成功，删除了 {deleted_count} 条记录',
            'deleted_count': deleted_count
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'清理失败: {str(e)}'})

@app.route('/api/quick-delete', methods=['POST'])
def api_quick_delete():
    """快速删除API"""
    try:
        data = request.get_json()
        option = data.get('option', '')
        keyword = data.get('keyword', '').strip()

        deleted_count = 0

        if option == 'low_count':
            # 删除商品数量少于10个的关键词
            # 首先统计每个关键词的商品数量
            from sqlalchemy import text
            keyword_stats = db.session.execute(text("""
                SELECT keyword, COUNT(*) as count
                FROM xianyu_products
                GROUP BY keyword
            """))

            low_count_keywords = []
            for row in keyword_stats:
                if row.count < 10:
                    low_count_keywords.append(row.keyword)

            # 删除这些关键词的所有商品
            for kw in low_count_keywords:
                products_to_delete = XianyuProduct.query.filter_by(keyword=kw).all()
                for product in products_to_delete:
                    db.session.delete(product)
                deleted_count += len(products_to_delete)

        elif option == 'recent':
            # 删除今天添加的数据
            today = datetime.now().date()
            today_products = XianyuProduct.query.filter(
                func.date(XianyuProduct.created_at) == today
            ).all()

            for product in today_products:
                db.session.delete(product)
            deleted_count = len(today_products)

        elif option == 'high_price':
            # 删除价格高于5000元的商品
            high_price_products = XianyuProduct.query.filter(
                XianyuProduct.price.like('%元%')
            ).all()

            for product in high_price_products:
                try:
                    # 提取价格数字
                    import re
                    price_match = re.search(r'(\d+)', product.price)
                    if price_match:
                        price = int(price_match.group(1))
                        if price > 5000:
                            db.session.delete(product)
                            deleted_count += 1
                except:
                    continue

        elif option == 'custom_keyword':
            # 删除指定关键词的所有商品
            if not keyword:
                return jsonify({'success': False, 'message': '关键词不能为空'})

            products_to_delete = XianyuProduct.query.filter_by(keyword=keyword).all()
            for product in products_to_delete:
                db.session.delete(product)
            deleted_count = len(products_to_delete)

        else:
            return jsonify({'success': False, 'message': '无效的删除选项'})

        db.session.commit()

        return jsonify({
            'success': True,
            'message': f'快速删除成功，删除了 {deleted_count} 条记录',
            'deleted_count': deleted_count
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'快速删除失败: {str(e)}'})

# ==================== 通知配置API ====================

@app.route('/api/notification-configs', methods=['GET'])
def api_get_notification_configs():
    """获取所有通知配置"""
    try:
        configs = NotificationConfig.query.order_by(NotificationConfig.created_at.desc()).all()

        config_list = []
        for config in configs:
            config_data = {
                'id': config.id,
                'platform': config.platform,
                'enabled': config.enabled,
                'config_name': config.config_name,
                'webhook_url': config.webhook_url,
                'access_token': config.access_token,
                'email_address': config.email_address,
                'phone_number': config.phone_number,
                'events': json.loads(config.events or '{}'),
                'description': config.description,
                'latest_product_config': json.loads(config.latest_product_config or '{}'),
                'created_at': config.created_at.strftime('%Y-%m-%d %H:%M:%S')
            }
            config_list.append(config_data)

        return jsonify({'success': True, 'configs': config_list})

    except Exception as e:
        return jsonify({'success': False, 'message': f'获取配置失败: {str(e)}'})

@app.route('/api/notification-configs', methods=['POST'])
def api_create_notification_config():
    """创建通知配置"""
    try:
        data = request.get_json()

        config = NotificationConfig(
            platform=data.get('platform'),
            enabled=data.get('enabled', False),
            config_name=data.get('config_name'),
            webhook_url=data.get('webhook_url'),
            access_token=data.get('access_token'),
            secret=data.get('secret'),
            email_address=data.get('email_address'),
            email_smtp=data.get('email_smtp'),
            email_password=data.get('email_password'),
            phone_number=data.get('phone_number'),
            events=json.dumps(data.get('events', {})),
            description=data.get('description'),
            latest_product_config=json.dumps(data.get('latest_product_config', {}))
        )

        db.session.add(config)
        db.session.commit()

        return jsonify({
            'success': True,
            'message': '通知配置创建成功',
            'config_id': config.id
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'创建配置失败: {str(e)}'})

@app.route('/api/notification-configs/<int:config_id>', methods=['PUT'])
def api_update_notification_config(config_id):
    """更新通知配置"""
    try:
        config = NotificationConfig.query.get_or_404(config_id)
        data = request.get_json()

        config.platform = data.get('platform', config.platform)
        config.enabled = data.get('enabled', config.enabled)
        config.config_name = data.get('config_name', config.config_name)
        config.webhook_url = data.get('webhook_url', config.webhook_url)
        config.access_token = data.get('access_token', config.access_token)
        config.secret = data.get('secret', config.secret)
        config.email_address = data.get('email_address', config.email_address)
        config.email_smtp = data.get('email_smtp', config.email_smtp)
        config.email_password = data.get('email_password', config.email_password)
        config.phone_number = data.get('phone_number', config.phone_number)
        config.events = json.dumps(data.get('events', json.loads(config.events or '{}')))
        config.description = data.get('description', config.description)
        config.latest_product_config = json.dumps(data.get('latest_product_config', json.loads(config.latest_product_config or '{}')))

        db.session.commit()

        return jsonify({
            'success': True,
            'message': '通知配置更新成功'
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'更新配置失败: {str(e)}'})

@app.route('/api/notification-configs/<int:config_id>', methods=['DELETE'])
def api_delete_notification_config(config_id):
    """删除通知配置"""
    try:
        config = NotificationConfig.query.get_or_404(config_id)
        db.session.delete(config)
        db.session.commit()

        return jsonify({
            'success': True,
            'message': '通知配置删除成功'
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'删除配置失败: {str(e)}'})

@app.route('/api/test-notification', methods=['POST'])
def api_test_notification():
    """测试通知发送"""
    try:
        data = request.get_json()
        config_id = data.get('config_id')

        config = NotificationConfig.query.get_or_404(config_id)

        # 发送测试通知
        title = "闲鱼数据管理系统 - 测试通知"
        content = "这是一条测试通知，如果您收到此消息，说明通知配置正确！"

        success = False

        if config.platform == 'dingtalk' and config.webhook_url:
            success = NotificationService.send_dingtalk_notification(
                config.webhook_url, config.secret, title, content
            )
        elif config.platform == 'feishu' and config.webhook_url:
            success = NotificationService.send_feishu_notification(
                config.webhook_url, title, content
            )
        elif config.platform == 'wechat_work' and config.webhook_url:
            success = NotificationService.send_wechat_work_notification(
                config.webhook_url, title, content
            )
        elif config.platform == 'email' and config.email_address:
            smtp_config = {
                'smtp': config.email_smtp,
                'username': config.email_address,
                'password': config.email_password,
                'from_email': config.email_address,
                'port': int(config.get('port', 587))
            }
            success = NotificationService.send_email_notification(
                config.email_address, smtp_config, title, content
            )

        if success:
            # 测试成功后自动启用配置
            if not config.enabled:
                config.enabled = True
                db.session.commit()

            return jsonify({
                'success': True,
                'message': f'测试通知发送成功，配置已自动启用 ({config.platform})',
                'enabled': True
            })
        else:
            return jsonify({
                'success': False,
                'message': f'测试通知发送失败 ({config.platform})'
            })

    except Exception as e:
        return jsonify({'success': False, 'message': f'测试通知失败: {str(e)}'})

@app.route('/api/quick-push-status', methods=['GET'])
def api_quick_push_status():
    """获取快速推送状态"""
    try:
        config = QuickPushConfig.get_config()
        return jsonify(config)
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'获取状态失败: {str(e)}'
        }), 500

@app.route('/api/quick-push-config', methods=['POST'])
def api_quick_push_config():
    """设置快速推送配置"""
    try:
        data = request.get_json()

        # 获取通知配置
        config = NotificationConfig.query.first()
        if not config:
            return jsonify({
                'success': False,
                'message': '没有找到通知配置，请先添加通知配置'
            })

        # 设置快速推送配置
        quick_config = {
            'enabled': data.get('enabled', False),
            'keywords': data.get('keywords', ''),
            'min_price': data.get('min_price'),
            'max_price': data.get('max_price'),
            'locations': data.get('locations', ''),
            'notification_configs': [config.id]
        }

        if QuickPushConfig.set_config(quick_config):
            return jsonify({
                'success': True,
                'message': '配置保存成功'
            })
        else:
            return jsonify({
                'success': False,
                'message': '配置保存失败'
            })

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'操作失败: {str(e)}'
        }), 500

@app.route('/api/quick-push-enable', methods=['POST'])
def api_quick_push_enable():
    """快速启用推送功能"""
    try:
        data = request.get_json()
        enable = data.get('enable', True)

        # 获取或创建通知配置
        config = NotificationConfig.query.first()
        if not config:
            config = NotificationConfig(
                config_name='默认推送配置',
                webhook_type='wechat_work',
                webhook_url='',  # 需要用户设置
                events='{"latest_product": true, "matched_product": true}',
                enabled=True,
                description='系统默认推送配置'
            )
            db.session.add(config)
            db.session.commit()

        # 启用快速推送
        quick_config = {
            'enabled': enable,
            'keywords': '',  # 匹配所有关键词
            'min_price': None,
            'max_price': None,
            'locations': '',  # 匹配所有地区
            'notification_configs': [config.id]
        }

        if QuickPushConfig.set_config(quick_config):
            return jsonify({
                'success': True,
                'message': f"已{'启用' if enable else '禁用'}快速推送功能"
            })
        else:
            return jsonify({
                'success': False,
                'message': '设置快速推送配置失败'
            })

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'操作失败: {str(e)}'
        }), 500

@app.route('/api/test-latest-products', methods=['POST'])
def api_test_latest_products():
    """测试最新商品推送功能"""
    try:
        data = request.get_json()
        config_id = data.get('config_id')

        config = NotificationConfig.query.get_or_404(config_id)

        # 检查是否启用了最新商品推送
        events = json.loads(config.events or '{}')
        if not events.get('latest_product', False):
            return jsonify({
                'success': False,
                'message': '该通知配置未启用最新发布商品推送功能'
            })

        # 从数据库获取最新的商品
        latest_products = XianyuProduct.query.order_by(XianyuProduct.search_time.desc()).limit(3).all()

        if not latest_products:
            return jsonify({
                'success': False,
                'message': '数据库中没有找到商品数据，请先爬取一些商品'
            })

        sent_count = 0
        failed_count = 0

        # 为每个商品单独发送一条推送
        for i, product in enumerate(latest_products, 1):
            # 计算时间差
            time_diff = datetime.now() - product.search_time
            if time_diff.total_seconds() < 3600:  # 1小时内
                time_str = f"{int(time_diff.total_seconds() / 60)}分钟前"
            elif time_diff.total_seconds() < 86400:  # 1天内
                time_str = f"{int(time_diff.total_seconds() / 3600)}小时前"
            else:
                time_str = f"{time_diff.days}天前"

            # 为每个商品构建单独的通知内容
            title = f"🚨 新推荐!"

            # 优化商品标题显示，避免过长
            product_title = product.title or '无标题'

            # 生成可点击的链接格式
            product_id = product.product_id

            # 链接转换函数：将各种格式转换为移动端链接
            def convert_to_mobile_link(original_link, product_id):
                """将各种闲鱼链接格式转换为移动端链接"""
                if not original_link:
                    return None

                # 如果已经是移动端链接，直接返回
                if 'm.goofish.com' in original_link or 'm.2.taobao.com' in original_link:
                    return original_link

                # Goofish桌面版链接转换为移动版
                if 'www.goofish.com' in original_link:
                    # 提取商品ID
                    import re
                    id_match = re.search(r'id=([^&]+)', original_link)
                    if id_match:
                        extracted_id = id_match.group(1)
                        # 使用H5格式，确保能跳转APP
                        return f"https://h5.m.goofish.com/item?forceFlush=1&id={extracted_id}&hitNativeDetail=true&from_kun_share=default"

                # 闲鱼桌面版链接转换
                if '2.taobao.com' in original_link and not original_link.startswith('https://m.'):
                    return original_link.replace('https://2.taobao.com', 'https://m.2.taobao.com')

                # 淘宝链接转换为移动版
                if 'taobao.com' in original_link and not original_link.startswith('https://m.'):
                    return original_link.replace('https://detail.taobao.com', 'https://m.detail.taobao.com')

                # 如果无法转换，返回原链接
                return original_link

            # 生成移动端闲鱼链接
            def generate_mobile_xianyu_links(product_id):
                """生成官方Goofish H5链接格式"""
                links = {}

                # 1. 完整的H5链接格式（确保APP跳转）
                links['goofish_h5'] = f"https://h5.m.goofish.com/item?forceFlush=1&itemId={product_id}&hitNativeDetail=true&from_kun_share=default"

                # 2. 备用：标准Goofish移动端链接
                links['goofish_mobile'] = f"https://m.goofish.com/item?id={product_id}"

                # 3. 备用：闲鱼移动端链接
                links['xianyu_mobile'] = f"https://m.2.taobao.com/item.htm?id={product_id}"

                return links

            # 生成移动端链接
            mobile_links = generate_mobile_xianyu_links(product_id)

            if product.product_link:
                # 转换现有链接为移动端格式
                mobile_link = convert_to_mobile_link(product.product_link, product_id)
                product_link = mobile_link if mobile_link else mobile_links['goofish_h5']

                # 使用转换后的移动链接
                mobile_link = convert_to_mobile_link(product.product_link, product_id)
                link_text = f"[手机链接]({mobile_link if mobile_link else product.product_link})"
            else:
                # 没有原始链接时使用移动版链接
                link_text = f"[手机链接]({mobile_links['goofish_h5']})"
                product_link = mobile_links['goofish_h5']  # 用于系统使用

            content_parts = [
                "",
                "- 商品详情 -",
                f"{product_title}",
                "----------------------------------------"
            ]

            # 添加图片信息（如果有图片）
            if product.product_image and product.product_image.strip():
                content_parts.append(f"- 📷 商品图片：{product.product_image}")
                content_parts.append("----------------------------------------")

            content_parts.extend([
                f"-💰:{product.price or '面议'}  -⏰:{time_str}  -🗺:{product.location or '未知'}",
                "----------------------------------------",
                f"- 🔗 商品链接：{link_text}"
            ])

            content = "\n".join(content_parts)

            # 发送单个商品通知
            success = False

            if config.platform == 'dingtalk':
                webhook_url = config.webhook_url
                secret = config.secret
                success = NotificationService.send_dingtalk_notification(
                    webhook_url, secret, title, content
                )
            elif config.platform == 'feishu':
                webhook_url = config.webhook_url
                success = NotificationService.send_feishu_notification(
                    webhook_url, title, content
                )
            elif config.platform == 'wechat_work':
                webhook_url = config.webhook_url
                success = NotificationService.send_wechat_work_notification(
                    webhook_url, title, content
                )
            elif config.platform == 'email':
                smtp_config = {
                    'smtp': config.email_smtp,
                    'username': config.email_address,
                    'password': config.email_password,
                    'from_email': config.email_address,
                    'port': int(config.get('port', 587))
                }
                success = NotificationService.send_email_notification(
                    config.email_address, smtp_config, title, content
                )

            if success:
                sent_count += 1
            else:
                failed_count += 1

            # 在推送之间添加小延迟，避免发送过快
            import time
            time.sleep(1)

        # 构建结果消息
        total_products = len(latest_products)
        if sent_count > 0 and failed_count == 0:
            return jsonify({
                'success': True,
                'message': f'最新商品推送测试成功！已发送 {sent_count} 个商品信息到 {config.platform}（每个商品单独一条推送）'
            })
        elif sent_count > 0:
            return jsonify({
                'success': True,
                'message': f'部分推送成功！成功发送 {sent_count} 个，失败 {failed_count} 个商品信息到 {config.platform}'
            })
        else:
            return jsonify({
                'success': False,
                'message': f'推送测试失败！{failed_count} 个商品推送均失败 ({config.platform})'
            })

    except Exception as e:
        return jsonify({'success': False, 'message': f'测试最新商品推送失败: {str(e)}'})

@app.route('/api/toggle-notification-config', methods=['POST'])
def api_toggle_notification_config():
    """切换通知配置的启用/禁用状态"""
    try:
        data = request.get_json()
        config_id = data.get('config_id')
        enabled = data.get('enabled', False)

        config = NotificationConfig.query.get_or_404(config_id)
        config.enabled = enabled
        db.session.commit()

        status_text = "启用" if enabled else "禁用"
        return jsonify({
            'success': True,
            'message': f'通知配置已{status_text}',
            'enabled': enabled
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'切换配置状态失败: {str(e)}'})

@app.route('/api/product-match-rules', methods=['GET'])
def api_product_match_rules():
    """API接口 - 获取产品匹配规则列表"""
    try:
        rules = ProductMatchRule.query.all()
        result = []
        for rule in rules:
            result.append({
                'id': rule.id,
                'rule_name': rule.rule_name,
                'enabled': rule.enabled,
                'keywords_include': rule.keywords_include,
                'keywords_exclude': rule.keywords_exclude,
                'price_min': rule.price_min,
                'price_max': rule.price_max,
                'locations_include': rule.locations_include,
                'locations_exclude': rule.locations_exclude,
                'seller_credit_min': rule.seller_credit_min,
                'notification_configs': rule.notification_configs,
                'match_logic': rule.match_logic,
                'description': rule.description,
                'created_at': rule.created_at.strftime('%Y-%m-%d %H:%M:%S') if rule.created_at else '',
                'updated_at': rule.updated_at.strftime('%Y-%m-%d %H:%M:%S') if rule.updated_at else ''
            })

        return jsonify(result)

    except Exception as e:
        return jsonify({'error': f'获取匹配规则失败: {str(e)}'}), 500

@app.route('/api/product-match-rules', methods=['POST'])
def api_create_product_match_rule():
    """API接口 - 创建产品匹配规则"""
    try:
        data = request.get_json()

        rule = ProductMatchRule(
            rule_name=data.get('rule_name'),
            enabled=data.get('enabled', True),
            keywords_include=data.get('keywords_include'),
            keywords_exclude=data.get('keywords_exclude'),
            price_min=data.get('price_min'),
            price_max=data.get('price_max'),
            locations_include=data.get('locations_include'),
            locations_exclude=data.get('locations_exclude'),
            seller_credit_min=data.get('seller_credit_min'),
            notification_configs=json.dumps(data.get('notification_configs', [])),
            match_logic=data.get('match_logic', 'AND'),
            description=data.get('description')
        )

        db.session.add(rule)
        db.session.commit()

        return jsonify({
            'success': True,
            'message': '匹配规则创建成功',
            'rule_id': rule.id
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'创建匹配规则失败: {str(e)}'}), 500

@app.route('/api/product-match-rules/<int:rule_id>', methods=['PUT'])
def api_update_product_match_rule(rule_id):
    """API接口 - 更新产品匹配规则"""
    try:
        rule = ProductMatchRule.query.get_or_404(rule_id)
        data = request.get_json()

        rule.rule_name = data.get('rule_name', rule.rule_name)
        rule.enabled = data.get('enabled', rule.enabled)
        rule.keywords_include = data.get('keywords_include', rule.keywords_include)
        rule.keywords_exclude = data.get('keywords_exclude', rule.keywords_exclude)
        rule.price_min = data.get('price_min', rule.price_min)
        rule.price_max = data.get('price_max', rule.price_max)
        rule.locations_include = data.get('locations_include', rule.locations_include)
        rule.locations_exclude = data.get('locations_exclude', rule.locations_exclude)
        rule.seller_credit_min = data.get('seller_credit_min', rule.seller_credit_min)
        rule.notification_configs = json.dumps(data.get('notification_configs', []))
        rule.match_logic = data.get('match_logic', rule.match_logic)
        rule.description = data.get('description', rule.description)

        db.session.commit()

        return jsonify({
            'success': True,
            'message': '匹配规则更新成功'
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'更新匹配规则失败: {str(e)}'}), 500

@app.route('/api/product-match-rules/<int:rule_id>', methods=['DELETE'])
def api_delete_product_match_rule(rule_id):
    """API接口 - 删除产品匹配规则"""
    try:
        rule = ProductMatchRule.query.get_or_404(rule_id)
        db.session.delete(rule)
        db.session.commit()

        return jsonify({
            'success': True,
            'message': '匹配规则删除成功'
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'删除匹配规则失败: {str(e)}'}), 500

# ==================== 快速推送API ====================

# ==================== 通知服务模块 ====================
import json
import hmac
import hashlib
import base64
import time
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import Header

class NotificationService:
    """多渠道通知服务"""

    @staticmethod
    def send_dingtalk_notification(webhook_url, secret, title, content):
        """发送钉钉通知"""
        try:
            # 构建消息内容
            data = {
                "msgtype": "markdown",
                "markdown": {
                    "title": title,
                    "text": f"## {title}\n\n{content}"
                }
            }

            # 如果有密钥，添加签名
            if secret:
                timestamp = str(round(time.time() * 1000))
                secret_enc = secret.encode('utf-8')
                string_to_sign = f'{timestamp}\n{secret}'
                string_to_sign_enc = string_to_sign.encode('utf-8')
                hmac_code = hmac.new(secret_enc, string_to_sign_enc, digestmod=hashlib.sha256).digest()
                sign = urllib.parse.quote_plus(base64.b64encode(hmac_code))
                webhook_url = f"{webhook_url}&timestamp={timestamp}&sign={sign}"

            # 发送请求
            response = requests.post(webhook_url, json=data, timeout=10)
            return response.status_code == 200 and response.json().get('errcode') == 0

        except Exception as e:
            print(f"钉钉通知发送失败: {str(e)}")
            return False

    @staticmethod
    def send_feishu_notification(webhook_url, title, content):
        """发送飞书通知"""
        try:
            data = {
                "msg_type": "post",
                "content": {
                    "post": {
                        "zh_cn": {
                            "title": title,
                            "content": [
                                [{
                                    "tag": "text",
                                    "text": f"{title}\n\n{content}"
                                }]
                            ]
                        }
                    }
                }
            }

            response = requests.post(webhook_url, json=data, timeout=10)
            return response.status_code == 200 and response.json().get('code') == 0

        except Exception as e:
            print(f"飞书通知发送失败: {str(e)}")
            return False

    @staticmethod
    def send_wechat_work_notification(webhook_url, title, content):
        """发送企业微信通知"""
        try:
            data = {
                "msgtype": "markdown",
                "markdown": {
                    "content": f"### {title}\n\n{content}"
                }
            }

            response = requests.post(webhook_url, json=data, timeout=10)
            return response.status_code == 200 and response.json().get('errcode') == 0

        except Exception as e:
            print(f"企业微信通知发送失败: {str(e)}")
            return False

    @staticmethod
    def send_email_notification(email_address, smtp_config, subject, content):
        """发送邮件通知"""
        try:
            msg = MIMEMultipart()
            msg['From'] = smtp_config.get('from_email', email_address)
            msg['To'] = email_address
            msg['Subject'] = Header(subject, 'utf-8')

            # 添加HTML内容
            html_content = f"""
            <html>
            <body>
                <h2 style="color: #333;">{subject}</h2>
                <div style="color: #666; line-height: 1.6;">
                    {content.replace('\n', '<br>')}
                </div>
                <hr>
                <p style="color: #999; font-size: 12px;">
                    此邮件由闲鱼数据管理系统自动发送
                </p>
            </body>
            </html>
            """

            msg.attach(MIMEText(html_content, 'html', 'utf-8'))

            # 连接SMTP服务器并发送
            with smtplib.SMTP(smtp_config['smtp'], int(smtp_config.get('port', 587))) as server:
                server.starttls()
                server.login(smtp_config['username'], smtp_config['password'])
                server.send_message(msg)

            return True

        except Exception as e:
            print(f"邮件通知发送失败: {str(e)}")
            return False

    @staticmethod
    def trigger_notification(event_type, title, content):
        """触发通知"""
        try:
            # 获取所有启用的通知配置
            configs = NotificationConfig.query.filter_by(enabled=True).all()

            for config in configs:
                # 检查是否需要触发此事件
                events = json.loads(config.events or '{}')
                if not events.get(event_type, False):
                    continue

                # 根据平台发送通知
                if config.platform == 'dingtalk' and config.webhook_url:
                    NotificationService.send_dingtalk_notification(
                        config.webhook_url, config.secret, title, content
                    )
                elif config.platform == 'feishu' and config.webhook_url:
                    NotificationService.send_feishu_notification(
                        config.webhook_url, title, content
                    )
                elif config.platform == 'wechat_work' and config.webhook_url:
                    NotificationService.send_wechat_work_notification(
                        config.webhook_url, title, content
                    )
                elif config.platform == 'email' and config.email_address:
                    smtp_config = {
                        'smtp': config.email_smtp,
                        'username': config.email_address,
                        'password': config.email_password,
                        'from_email': config.email_address,
                        'port': int(config.get('port', 587))
                    }
                    NotificationService.send_email_notification(
                        config.email_address, smtp_config, title, content
                    )

            return True

        except Exception as e:
            print(f"通知触发失败: {str(e)}")
            return False

    @staticmethod
    def check_product_match(product_data, rule):
        """检查产品是否匹配规则"""
        if not rule.enabled:
            return False

        results = []

        # 检查包含关键词
        if rule.keywords_include:
            include_keywords = [k.strip() for k in rule.keywords_include.split(',') if k.strip()]
            title = product_data.get('title', '').lower()
            keyword_match = any(kw.lower() in title for kw in include_keywords)
            results.append(('keywords_include', keyword_match))

        # 检查排除关键词
        if rule.keywords_exclude:
            exclude_keywords = [k.strip() for k in rule.keywords_exclude.split(',') if k.strip()]
            title = product_data.get('title', '').lower()
            exclude_match = not any(kw.lower() in title for kw in exclude_keywords)
            results.append(('keywords_exclude', exclude_match))

        # 检查价格范围
        price_str = product_data.get('price', '').replace('¥', '').replace(',', '').strip()
        if price_str and rule.price_min is not None and rule.price_max is not None:
            try:
                price = float(price_str)
                price_match = rule.price_min <= price <= rule.price_max
                results.append(('price_range', price_match))
            except:
                results.append(('price_range', False))

        # 检查地区
        location = product_data.get('location', '')
        if rule.locations_include:
            include_locations = [l.strip() for l in rule.locations_include.split(',') if l.strip()]
            location_match = any(loc.lower() in location.lower() for loc in include_locations)
            results.append(('locations_include', location_match))

        if rule.locations_exclude:
            exclude_locations = [l.strip() for l in rule.locations_exclude.split(',') if l.strip()]
            location_exclude_match = not any(loc.lower() in location.lower() for loc in exclude_locations)
            results.append(('locations_exclude', location_exclude_match))

        # 检查卖家信用
        if rule.seller_credit_min:
            seller_credit = product_data.get('seller_credit', '')
            # 这里可以根据实际的信用评级进行比较
            credit_match = seller_credit >= rule.seller_credit_min
            results.append(('seller_credit', credit_match))

        # 根据匹配逻辑决定结果
        if not results:
            return False

        if rule.match_logic == 'AND':
            return all(result[1] for result in results)
        else:  # OR
            return any(result[1] for result in results)

    @staticmethod
    def trigger_product_notification(product_data, rule, notification_config_ids):
        """为匹配的产品发送通知"""
        try:
            # 获取通知配置
            notification_configs = []
            for config_id in notification_config_ids:
                config = NotificationConfig.query.get(config_id)
                if config and config.enabled:
                    notification_configs.append(config)

            if not notification_configs:
                print(f"没有找到有效的通知配置")
                return False

            # 构建产品通知内容
            title = f"🎯 发现符合规则的产品"

            # 构建基础信息
            content_parts = [
                "**产品信息：**",
                f"• 标题：{product_data.get('title', '未知')}",
                f"• 价格：{product_data.get('price', '未知')}",
                f"• 地区：{product_data.get('location', '未知')}",
                f"• 卖家信用：{product_data.get('seller_credit', '未知')}",
                f"• 关键词：{product_data.get('keyword', '未知')}"
            ]

            # 添加图片信息（如果有图片）
            if product_data.get('product_image') and product_data.get('product_image').strip():
                content_parts.append(f"• 📷 商品图片：{product_data.get('product_image')}")

            content_parts.extend([
                "",
                f"**匹配规则：**{rule.rule_name}",
                f"**规则描述：**{rule.description or '无'}",
                "",
                f"**产品链接：**{product_data.get('product_link', '无')}",
                "",
                "---",
                f"⏰ 发现时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            ])

            content = "\n".join(content_parts)

            # 发送通知到各个平台
            success_count = 0
            for config in notification_configs:
                try:
                    if config.platform == 'dingtalk' and config.webhook_url:
                        if NotificationService.send_dingtalk_notification(
                            config.webhook_url, config.secret, title, content
                        ):
                            success_count += 1

                    elif config.platform == 'feishu' and config.webhook_url:
                        if NotificationService.send_feishu_notification(
                            config.webhook_url, title, content
                        ):
                            success_count += 1

                    elif config.platform == 'wechat_work' and config.webhook_url:
                        if NotificationService.send_wechat_work_notification(
                            config.webhook_url, title, content
                        ):
                            success_count += 1

                    elif config.platform == 'email' and config.email_address:
                        smtp_config = {
                            'smtp': config.email_smtp,
                            'username': config.email_address,
                            'password': config.email_password,
                            'from_email': config.email_address,
                            'port': int(config.get('port', 587))
                        }
                        if NotificationService.send_email_notification(
                            config.email_address, smtp_config, title, content
                        ):
                            success_count += 1

                except Exception as e:
                    print(f"发送到 {config.platform} 通知失败: {str(e)}")
                    continue

            print(f"产品通知发送完成: {success_count}/{len(notification_configs)} 成功")
            return success_count > 0

        except Exception as e:
            print(f"触发产品通知失败: {str(e)}")
            return False

    @staticmethod
    def process_product_matching(product_data):
        """处理产品匹配和通知"""
        try:
            matched = False

            # 1. 检查快速推送配置
            quick_config = QuickPushConfig.get_config()
            if quick_config['enabled']:
                if NotificationService.check_quick_push_match(product_data, quick_config):
                    print(f"[快速推送] 产品 '{product_data.get('title', '')[:30]}...' 匹配快速推送规则")

                    # 创建快速推送规则对象
                    quick_rule = type('QuickRule', (), {
                        'rule_name': '快速推送',
                        'description': f"关键词: {quick_config['keywords'] or '不限'}"
                    })()

                    # 发送快速推送通知
                    if NotificationService.trigger_product_notification(
                        product_data, quick_rule, quick_config['notification_configs']
                    ):
                        matched = True

            # 2. 检查详细的匹配规则
            rules = ProductMatchRule.query.filter_by(enabled=True).all()
            for rule in rules:
                # 检查产品是否匹配规则
                if NotificationService.check_product_match(product_data, rule):
                    # 获取规则关联的通知配置
                    notification_config_ids = json.loads(rule.notification_configs or '[]')
                    if notification_config_ids:
                        print(f"[产品匹配] 产品 '{product_data.get('title', '')[:30]}...' 匹配规则 '{rule.rule_name}'")

                        # 发送通知
                        if NotificationService.trigger_product_notification(product_data, rule, notification_config_ids):
                            matched = True

            return matched

        except Exception as e:
            print(f"处理产品匹配失败: {str(e)}")
            return False

    @staticmethod
    def check_quick_push_match(product_data, config):
        """检查产品是否匹配快速推送配置"""
        if not config['enabled']:
            return False

        # 检查关键词
        if config['keywords']:
            keywords = [k.strip() for k in config['keywords'].split(',') if k.strip()]
            title = product_data.get('title', '').lower()
            if not any(kw.lower() in title for kw in keywords):
                return False

        # 检查价格范围
        if config['min_price'] is not None or config['max_price'] is not None:
            price_str = product_data.get('price', '').replace('¥', '').replace(',', '').strip()
            if price_str:
                try:
                    price = float(price_str)
                    if config['min_price'] is not None and price < config['min_price']:
                        return False
                    if config['max_price'] is not None and price > config['max_price']:
                        return False
                except:
                    return False

        # 检查地区
        if config['locations']:
            locations = [l.strip() for l in config['locations'].split(',') if l.strip()]
            product_location = product_data.get('location', '')
            if not any(loc.lower() in product_location.lower() for loc in locations):
                return False

        return True

    @staticmethod
    def get_latest_product_configs():
        """获取启用了最新商品推送的通知配置"""
        try:
            configs = NotificationConfig.query.filter_by(enabled=True).all()
            latest_product_configs = []

            for config in configs:
                # 检查是否启用了最新商品推送
                events = json.loads(config.events or '{}')
                if events.get('latest_product', False):
                    latest_product_configs.append(config)

            return latest_product_configs

        except Exception as e:
            print(f"获取最新商品推送配置失败: {str(e)}")
            return []

    @staticmethod
    def send_notification(config, title, content):
        """发送通知的通用方法"""
        try:
            if not config.webhook_url:
                print(f"通知配置 '{config.config_name}' 缺少webhook地址")
                return False

            success = False

            if config.platform == 'wechat_work':
                success = NotificationService.send_wechat_work_notification(
                    config.webhook_url, title, content
                )
            elif config.platform == 'dingtalk':
                success = NotificationService.send_dingtalk_notification(
                    config.webhook_url, config.secret or '', title, content
                )
            elif config.platform == 'feishu':
                success = NotificationService.send_feishu_notification(
                    config.webhook_url, title, content
                )
            elif config.platform == 'email':
                # 邮件通知需要额外的SMTP配置
                if hasattr(config, 'smtp_config') and config.smtp_config:
                    smtp_config = json.loads(config.smtp_config)
                    email_address = config.webhook_url  # 这里webhook_url存储的是邮箱地址
                    success = NotificationService.send_email_notification(
                        email_address, smtp_config, title, content
                    )
                else:
                    print(f"邮件通知配置 '{config.config_name}' 缺少SMTP配置")
                    return False
            else:
                print(f"不支持的通知类型: {config.platform}")
                return False

            return success

        except Exception as e:
            print(f"发送通知失败: {str(e)}")
            return False

# 短链接重定向路由
@app.route('/redirect/<short_code>')
def redirect_short_link(short_code):
    """处理短链接重定向到闲鱼商品"""
    try:
        # 这里需要根据short_code找到对应的商品ID
        # 由于我们没有存储映射关系，使用一个简单的解密算法

        import hashlib

        # 遍历可能的商品ID来找到匹配的短码
        # 在实际应用中，应该有数据库存储映射关系
        product = XianyuProduct.query.order_by(XianyuProduct.search_time.desc()).first()

        if product:
            # 重新生成短码验证
            hash_input = f"xianyu_{product.product_id}_{int(time.time())}"
            hash_obj = hashlib.md5(hash_input.encode())
            expected_short_code = hash_obj.hexdigest()[:8]

            # 由于时间戳不同，我们直接使用传入的短码
            # 构建移动端闲鱼链接
            target_url = f"https://m.2.taobao.com/item.htm?id={product.product_id}"

            # 也可以尝试Goofish链接
            # target_url = f"https://m.goofish.com/item?id={product.product_id}"

            return redirect(target_url)

        # 如果找不到商品，重定向到闲鱼首页
        return redirect("https://m.2.taobao.com")

    except Exception as e:
        print(f"重定向错误: {e}")
        return redirect("https://m.2.taobao.com")

# 导入requests库用于HTTP请求
import requests
import urllib.parse

if __name__ == '__main__':
    print("=" * 50)
    print("闲鱼数据管理系统启动")
    print("=" * 50)

    # 初始化数据库
    print("正在初始化数据库...")
    init_db()

    # 启动Web应用
    print("正在启动Web应用...")
    print("请访问: http://127.0.0.1:5000")
    print("=" * 50)

    app.run(debug=True, host='0.0.0.0', port=5000)