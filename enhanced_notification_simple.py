#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简化增强通知系统
包含多渠道通知、队列处理和模板系统
"""

import json
import time
import threading
import queue
import sqlite3
import logging
from datetime import datetime
from enum import Enum
from dataclasses import dataclass
from typing import Dict, Any, Optional, List

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class NotificationChannel(Enum):
    """通知渠道"""
    DINGTALK = "dingtalk"
    FEISHU = "feishu"
    WECHAT_WORK = "wechat_work"
    EMAIL = "email"
    WEBHOOK = "webhook"
    BROWSER = "browser"
    DESKTOP = "desktop"

@dataclass
class NotificationMessage:
    """通知消息"""
    title: str
    content: str
    timestamp: datetime
    priority: str = "normal"
    data: Optional[Dict[str, Any]] = None

@dataclass
class NotificationConfig:
    """通知配置"""
    id: int
    name: str
    notification_type: str
    enabled: bool = True
    webhook_url: Optional[str] = None
    secret: Optional[str] = None
    email_address: Optional[str] = None
    smtp_config: Optional[Dict[str, Any]] = None
    config: Optional[Dict[str, Any]] = None

class SimpleEnhancedNotificationManager:
    """简化的增强通知管理器"""

    def __init__(self, db_path: str = "xianyu_data.db"):
        self.db_path = db_path
        self.queue = queue.Queue()
        self.worker_thread = None
        self.running = False
        self.stats = {
            'total_sent': 0,
            'total_failed': 0,
            'queue_size': 0,
            'last_sent': None
        }
        self.templates = self._load_templates()

    def _load_templates(self) -> Dict[str, str]:
        """加载通知模板"""
        return {
            'scraping_start': """🚀 爬取任务开始

关键词: {keyword}
目标页数: {max_pages}
延迟策略: {delay}秒

开始时间: {timestamp}""",

            'scraping_complete': """✅ 爬取任务完成

关键词: {keyword}
统计详情:
• 爬取商品: {total_scraped} 个
• 新增商品: {saved_count} 个
• 重复商品: {duplicate_count} 个

完成时间: {timestamp}""",

            'scraping_error': """❌ 爬取任务失败

关键词: {keyword}
错误信息: {error_message}

失败时间: {timestamp}""",

            'product_match': """🎯 找到匹配商品

商品标题: {title}
价格: {price}
发布时间: {publish_time}
匹配规则: {rule_name}

查看链接: {link}"""
        }

    def start_background_processor(self):
        """启动后台处理线程"""
        if self.worker_thread and self.worker_thread.is_alive():
            return

        self.running = True
        self.worker_thread = threading.Thread(target=self._process_queue, daemon=True)
        self.worker_thread.start()
        logger.info("增强通知系统已启动")

    def stop_background_processor(self):
        """停止后台处理线程"""
        self.running = False
        if self.worker_thread:
            self.worker_thread.join(timeout=5)
        logger.info("增强通知系统已停止")

    def _process_queue(self):
        """处理通知队列"""
        while self.running:
            try:
                # 等待消息，超时1秒
                message_data = self.queue.get(timeout=1)
                self._send_notification(message_data)
                self.queue.task_done()
            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"处理通知队列时出错: {e}")

    def send_notification(self, notification_type: str, title: str, content: str,
                         config: Optional[Dict[str, Any]] = None, priority: str = 'normal') -> bool:
        """发送通知"""
        try:
            message = NotificationMessage(
                title=title,
                content=content,
                timestamp=datetime.now(),
                priority=priority,
                data=config
            )

            message_data = {
                'type': notification_type,
                'message': message,
                'config': config or {}
            }

            # 添加到队列
            self.queue.put(message_data)
            self.stats['queue_size'] = self.queue.qsize()

            return True

        except Exception as e:
            logger.error(f"发送通知失败: {e}")
            self.stats['total_failed'] += 1
            return False

    def send_from_template(self, template_name: str, data: Dict[str, Any],
                          priority: str = 'normal') -> bool:
        """从模板发送通知"""
        try:
            template = self.templates.get(template_name, self.templates['scraping_complete'])

            # 添加时间戳
            data['timestamp'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

            # 填充模板
            content = template.format(**data)

            # 提取标题
            lines = content.split('\n')
            title = lines[0] if lines else "通知"

            return self.send_notification('browser', title, content, data, priority)

        except Exception as e:
            logger.error(f"发送模板通知失败: {e}")
            return False

    def _send_notification(self, message_data: Dict[str, Any]):
        """实际发送通知"""
        try:
            notification_type = message_data['type']
            message = message_data['message']
            config = message_data['config']

            # 根据类型发送通知
            if notification_type == NotificationChannel.BROWSER.value:
                self._send_browser_notification(message)
            elif notification_type == NotificationChannel.DESKTOP.value:
                self._send_desktop_notification(message)
            elif notification_type == NotificationChannel.WEBHOOK.value:
                self._send_webhook_notification(message, config)
            else:
                # 默认使用浏览器通知
                self._send_browser_notification(message)

            self.stats['total_sent'] += 1
            self.stats['last_sent'] = datetime.now().isoformat()

        except Exception as e:
            logger.error(f"发送通知时出错: {e}")
            self.stats['total_failed'] += 1

    def _send_browser_notification(self, message: NotificationMessage):
        """发送浏览器通知"""
        try:
            print(f"[浏览器通知] {message.title}")
            print(f"内容: {message.content}")
            # 这里可以集成实际的浏览器通知库
        except Exception as e:
            logger.error(f"浏览器通知发送失败: {e}")

    def _send_desktop_notification(self, message: NotificationMessage):
        """发送桌面通知"""
        try:
            print(f"[桌面通知] {message.title}")
            print(f"内容: {message.content}")
            # 这里可以集成实际的桌面通知库
        except Exception as e:
            logger.error(f"桌面通知发送失败: {e}")

    def _send_webhook_notification(self, message: NotificationMessage, config: Dict[str, Any]):
        """发送webhook通知"""
        try:
            import requests

            webhook_url = config.get('webhook_url')
            if not webhook_url:
                return

            payload = {
                'title': message.title,
                'content': message.content,
                'timestamp': message.timestamp.isoformat(),
                'priority': message.priority
            }

            response = requests.post(webhook_url, json=payload, timeout=10)
            response.raise_for_status()

        except Exception as e:
            logger.error(f"Webhook通知发送失败: {e}")

    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        self.stats['queue_size'] = self.queue.qsize()
        return self.stats.copy()

    def get_configs(self) -> List[Dict[str, Any]]:
        """获取配置列表"""
        # 简化版本，返回默认配置
        return [
            {
                'id': 1,
                'name': '浏览器通知',
                'type': 'browser',
                'enabled': True
            },
            {
                'id': 2,
                'name': '桌面通知',
                'type': 'desktop',
                'enabled': True
            }
        ]

    def add_config(self, name: str, notification_type: str,
                   config: Optional[Dict[str, Any]] = None, enabled: bool = True) -> bool:
        """添加配置"""
        try:
            # 简化版本，总是返回True
            logger.info(f"添加通知配置: {name} ({notification_type})")
            return True
        except Exception as e:
            logger.error(f"添加配置失败: {e}")
            return False

# 向后兼容的别名
EnhancedNotificationManager = SimpleEnhancedNotificationManager