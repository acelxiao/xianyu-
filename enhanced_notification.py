#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
增强版通知推送系统
支持多种通知渠道、模板化消息、队列处理和智能重试
"""

import asyncio
import json
import time
import hashlib
import hmac
import base64
import requests
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field
from enum import Enum
import sqlite3
import threading
from pathlib import Path

# 配置日志
logger = logging.getLogger(__name__)

class NotificationChannel(Enum):
    """通知渠道"""
    DINGTALK = "dingtalk"
    FEISHU = "feishu"
    WECHAT_WORK = "wechat_work"
    EMAIL = "email"
    WEBHOOK = "webhook"
    BROWSER = "browser"  # 浏览器推送
    DESKTOP = "desktop"  # 桌面通知

class NotificationPriority(Enum):
    """通知优先级"""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"

@dataclass
class NotificationMessage:
    """通知消息"""
    title: str
    content: str
    channel: NotificationChannel
    priority: NotificationPriority = NotificationPriority.NORMAL
    timestamp: datetime = field(default_factory=datetime.now)
    extra_data: Dict[str, Any] = field(default_factory=dict)
    retry_count: int = 0
    max_retries: int = 3
    delay_seconds: int = 5

@dataclass
class NotificationConfig:
    """通知配置"""
    channel: NotificationChannel
    webhook_url: Optional[str] = None
    secret: Optional[str] = None
    access_token: Optional[str] = None
    chat_id: Optional[str] = None
    email_address: Optional[str] = None
    smtp_config: Optional[Dict] = None
    template: Optional[str] = None
    enabled: bool = True
    priority: NotificationPriority = NotificationPriority.NORMAL
    rate_limit: int = 10  # 每分钟最多发送数量
    batch_size: int = 100  # 批量发送大小

@dataclass
class NotificationTemplate:
    """通知模板"""
    name: str
    title_template: str
    content_template: str
    variables: List[str] = field(default_factory=list)
    channel: NotificationChannel = NotificationChannel.DINGTALK
    priority: NotificationPriority = NotificationPriority.NORMAL

class NotificationQueue:
    """通知队列"""
    def __init__(self, max_size=1000):
        self.queue = []
        self.max_size = max_size
        self.lock = threading.Lock()
        self.processing = False

    def add(self, message: NotificationMessage) -> bool:
        """添加消息到队列"""
        with self.lock:
            if len(self.queue) >= self.max_size:
                logger.warning("通知队列已满，丢弃消息")
                return False
            self.queue.append(message)
            logger.info(f"消息已添加到队列: {message.title}")
            return True

    def get(self) -> Optional[NotificationMessage]:
        """从队列获取消息"""
        with self.lock:
            if self.queue:
                return self.queue.pop(0)
        return None

    def size(self) -> int:
        """获取队列大小"""
        with self.lock:
            return len(self.queue)

class EnhancedNotificationManager:
    """增强版通知管理器"""

    def __init__(self, db_path: str = "xianyu_data.db"):
        self.db_path = db_path
        self.queue = NotificationQueue()
        self.rate_limits = {}  # 频率限制记录
        self.templates = self._load_templates()
        self.configs = self._load_configs()
        self.stats = {
            'total_sent': 0,
            'total_failed': 0,
            'by_channel': {},
            'last_sent': None
        }

        # 注册通知渠道处理器
        self.channel_handlers = {
            NotificationChannel.DINGTALK: self._send_dingtalk_notification,
            NotificationChannel.FEISHU: self._send_feishu_notification,
            NotificationChannel.WECHAT_WORK: self._send_wechat_work_notification,
            NotificationChannel.EMAIL: self._send_email_notification,
            NotificationChannel.WEBHOOK: self._send_webhook_notification,
            NotificationChannel.BROWSER: self._send_browser_notification,
            NotificationChannel.DESKTOP: self._send_desktop_notification
        }

    def _load_templates(self) -> Dict[str, NotificationTemplate]:
        """加载通知模板"""
        templates = {}

        # 内置模板
        builtin_templates = [
            {
                "name": "爬取开始",
                "title_template": "🚀 爬取任务开始",
                "content_template": "关键词: {keyword}\n目标页数: {max_pages}\n延迟策略: {delay}秒\n显示模式: {display_mode}",
                "variables": ["keyword", "max_pages", "delay", "display_mode"],
                "channel": NotificationChannel.DINGTALK,
                "priority": NotificationPriority.NORMAL
            },
            {
                "name": "爬取成功",
                "title_template": "✅ 爬取任务完成",
                "content_template": "成功爬取 {product_count} 个商品\n关键词: {keyword}\n用时: {duration}秒\n文件: {filename}",
                "variables": ["product_count", "keyword", "duration", "filename"],
                "channel": NotificationChannel.DINGTALK,
                "priority": NotificationPriority.NORMAL
            },
            {
                "name": "爬取失败",
                "title_template": "❌ 爬取任务失败",
                "content_template": "失败原因: {error}\n关键词: {keyword}\n建议: {suggestion}",
                "variables": ["error", "keyword", "suggestion"],
                "channel": NotificationChannel.DINGTALK,
                "priority": NotificationPriority.HIGH
            },
            {
                "name": "定时任务创建",
                "title_template": "⏰ 定时任务已创建",
                "content_template": "任务名称: {task_name}\n执行时间: {start_time}\n关键词: {keyword}\n排序方式: {sort_type}",
                "variables": ["task_name", "start_time", "keyword", "sort_type"],
                "channel": NotificationChannel.DINGTALK,
                "priority": NotificationPriority.NORMAL
            },
            {
                "name": "定时任务执行",
                "title_template": "🔄 定时任务执行中",
                "content_template": "任务名称: {task_name}\n开始时间: {start_time}\n关键词: {keyword}\n已处理: {processed_count} 个商品",
                "variables": ["task_name", "start_time", "keyword", "processed_count"],
                "channel": NotificationChannel.DINGTALK,
                "priority": NotificationPriority.NORMAL
            },
            {
                "name": "定时任务完成",
                "title_template": "🎉 定时任务完成",
                "content_template": "任务名称: {task_name}\n关键词: {keyword}\n成功提取: {success_count} 个商品\n耗时: {duration}",
                "variables": ["task_name", "keyword", "success_count", "duration"],
                "channel": NotificationChannel.DINGTALK,
                "priority": NotificationPriority.NORMAL
            }
        ]

        for template_data in builtin_templates:
            template = NotificationTemplate(**template_data)
            templates[template.name] = template

        return templates

    def _load_configs(self) -> Dict[str, NotificationConfig]:
        """加载通知配置"""
        configs = {}

        try:
            # 从数据库加载配置
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("SELECT * FROM notification_configs WHERE enabled = 1")
            rows = cursor.fetchall()

            for row in rows:
                config = NotificationConfig(
                    channel=NotificationChannel(row[1]),
                    webhook_url=row[2],
                    secret=row[3],
                    access_token=row[4],
                    chat_id=row[5],
                    email_address=row[6],
                    smtp_config=json.loads(row[7]) if row[7] else None,
                    template=row[8],
                    enabled=bool(row[9]),
                    priority=NotificationPriority(row[10]),
                    rate_limit=row[11],
                    batch_size=row[12]
                )
                configs[f"{row[0]}_{config.channel.value}"] = config

            conn.close()
        except Exception as e:
            logger.error(f"加载通知配置失败: {str(e)}")

        return configs

    async def send_notification(self,
                            channel: NotificationChannel,
                            title: str,
                            content: str,
                            config_name: str = None,
                            template_name: str = None,
                            variables: Dict[str, Any] = None,
                            priority: NotificationPriority = NotificationPriority.NORMAL,
                            extra_data: Optional[Dict[str, Any]] = None,
                            **kwargs) -> bool:
        """发送通知"""

        # 获取配置
        config = None
        if config_name:
            config = self.configs.get(f"{config_name}_{channel.value}")
        else:
            # 使用该渠道的第一个可用配置
            for key, cfg in self.configs.items():
                if cfg.channel == channel and cfg.enabled:
                    config = cfg
                    break

        if not config:
            logger.warning(f"未找到 {channel.value} 的配置")
            return False

        # 检查频率限制
        if not self._check_rate_limit(config):
            logger.warning(f"触发频率限制，跳过发送: {title}")
            return False

        # 使用模板
        if template_name and template_name in self.templates:
            template = self.templates[template_name]
            if variables:
                # 渲染模板
                title = template.title_template.format(**variables)
                content = template.content_template.format(**variables)
            priority = template.priority

        # 创建消息对象
        message = NotificationMessage(
            title=title,
            content=content,
            channel=channel,
            priority=priority,
            extra_data=extra_data or {},
            max_retries=3 if priority == NotificationPriority.URGENT else 2
        )

        # 添加到队列
        if not self.queue.add(message):
            return False

        # 处理队列
        await self._process_queue()

        return True

    def _check_rate_limit(self, config: NotificationConfig) -> bool:
        """检查频率限制"""
        now = time.time()
        key = f"{config.channel.value}_{config.webhook_url or config.chat_id}"

        # 清理过期的限制记录
        if key in self.rate_limits:
            self.rate_limits = {k: v for k, v in self.rate_limits.items() if now - v < 60}

        # 检查当前限制
        current_count = self.rate_limits.get(key, 0)
        if current_count >= config.rate_limit:
            return False

        # 增加计数
        self.rate_limits[key] = current_count + 1
        return True

    async def _process_queue(self) -> None:
        """处理通知队列"""
        if self.queue.processing:
            return

        self.queue.processing = True

        while self.queue.size() > 0:
            message = self.queue.get()
            if not message:
                break

            try:
                # 获取配置
                config = None
                for cfg in self.configs.values():
                    if cfg.channel == message.channel and cfg.enabled:
                        config = cfg
                        break

                if config:
                    # 发送通知
                    success = await self._send_to_channel(message, config)

                    # 更新统计
                    if success:
                        self._update_stats(message.channel, True)
                    else:
                        self._update_stats(message.channel, False, message.retry_count)
                        # 重试逻辑
                        if message.retry_count < message.max_retries:
                            message.retry_count += 1
                            await asyncio.sleep(message.delay_seconds * (2 ** message.retry_count))
                            self.queue.add(message)
                else:
                    logger.warning(f"未找到 {message.channel.value} 的配置，跳过发送")

            except Exception as e:
                logger.error(f"处理通知消息失败: {str(e)}")
                # 继续处理下一条

        self.queue.processing = False

    async def _send_to_channel(self, message: NotificationMessage, config: NotificationConfig) -> bool:
        """发送到指定渠道"""
        try:
            handler = self.channel_handlers.get(message.channel)
            if handler:
                return await handler(message, config)
            else:
                logger.warning(f"不支持的通知渠道: {message.channel.value}")
                return False
        except Exception as e:
            logger.error(f"发送通知失败: {str(e)}")
            return False

    async def _send_dingtalk_notification(self, message: NotificationMessage, config: NotificationConfig) -> bool:
        """发送钉钉通知"""
        if not config.webhook_url:
            return False

        try:
            # 构建消息内容
            data = {
                "msgtype": "markdown",
                "markdown": {
                    "title": message.title,
                    "text": f"## {message.title}\n\n{message.content}"
                }
            }

            # 添加签名
            if config.secret:
                timestamp = str(int(time.time() * 1000))
                string_to_sign = f'{timestamp}\n{config.secret}'
                hmac_code = hmac.new(
                    config.secret.encode('utf-8'),
                    string_to_sign.encode('utf-8'),
                    digestmod=hashlib.sha256
                ).digest()
                sign = base64.b64encode(hmac_code).decode()
                data['timestamp'] = timestamp
                data['sign'] = sign

            # 发送请求
            response = requests.post(
                config.webhook_url,
                json=data,
                timeout=10,
                headers={'Content-Type': 'application/json'}
            )

            return response.status_code == 200 and response.json().get('errcode') == 0

        except Exception as e:
            logger.error(f"钉钉通知发送失败: {str(e)}")
            return False

    async def _send_feishu_notification(self, message: NotificationMessage, config: NotificationConfig) -> bool:
        """发送飞书通知"""
        if not config.webhook_url:
            return False

        try:
            data = {
                "msg_type": "post",
                "content": {
                    "post": {
                        "zh_cn": {
                            "title": message.title,
                            "content": [
                                {
                                    "tag": "text",
                                    "text": f"{message.title}\n\n{message.content}"
                                }
                            ]
                        }
                    }
                }
            }

            response = requests.post(
                config.webhook_url,
                json=data,
                timeout=10,
                headers={'Content-Type': 'application/json'}
            )

            return response.status_code == 200

        except Exception as e:
            logger.error(f"飞书通知发送失败: {str(e)}")
            return False

    async def _send_wechat_work_notification(self, message: NotificationMessage, config: NotificationConfig) -> bool:
        """发送企业微信通知"""
        if not config.access_token or not config.chat_id:
            return False

        try:
            url = f"https://qyapi.weixin.qq.com/cgi-bin/message/send?access_token={config.access_token}"

            data = {
                "touser": config.chat_id,
                "msgtype": "markdown",
                "markdown": {
                    "content": f"## {message.title}\n\n{message.content}"
                }
            }

            response = requests.post(url, json=data, timeout=10)

            return response.status_code == 200 and response.json().get('errcode') == 0

        except Exception as e:
            logger.error(f"企业微信通知发送失败: {str(e)}")
            return False

    async def _send_email_notification(self, message: NotificationMessage, config: NotificationConfig) -> bool:
        """发送邮件通知"""
        if not config.email_address or not config.smtp_config:
            return False

        try:
            import smtplib
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart

            smtp_config = config.smtp_config
            msg = MIMEMultipart()

            msg['From'] = smtp_config.get('from_email')
            msg['To'] = config.email_address
            msg['Subject'] = message.title

            # 添加文本内容
            text_part = MIMEText(message.content, 'plain', 'utf-8')
            msg.attach(text_part)

            # 发送邮件
            with smtplib.SMTP(
                smtp_config.get('host'),
                smtp_config.get('port', 587),
                timeout=10
            ) as server:
                server.starttls()
                server.login(
                    smtp_config.get('username'),
                    smtp_config.get('password')
                )
                server.send_message(msg)

            return True

        except Exception as e:
            logger.error(f"邮件通知发送失败: {str(e)}")
            return False

    async def _send_webhook_notification(self, message: NotificationMessage, config: NotificationConfig) -> bool:
        """发送通用Webhook通知"""
        if not config.webhook_url:
            return False

        try:
            payload = {
                "title": message.title,
                "content": message.content,
                "timestamp": message.timestamp.isoformat(),
                "priority": message.priority.value,
                **message.extra_data
            }

            headers = {}
            if config.secret:
                # 添加签名头
                timestamp = str(int(time.time() * 1000))
                message_content = '{"title": "' + message.title + '", "content": "' + message.content + '"}'
                string_to_sign = timestamp + message_content + config.secret
                hmac_code = hmac.new(
                    config.secret.encode('utf-8'),
                    string_to_sign.encode('utf-8'),
                    digestmod=hashlib.sha256
                ).digest()
                headers['X-Signature'] = base64.b64encode(hmac_code).decode()
                headers['X-Timestamp'] = timestamp

            response = requests.post(
                config.webhook_url,
                json=payload,
                headers=headers,
                timeout=10
            )

            return response.status_code == 200

        except Exception as e:
            logger.error(f"Webhook通知发送失败: {str(e)}")
            return False

    async def _send_browser_notification(self, message: NotificationMessage, config: NotificationConfig) -> None:
        """浏览器推送（暂时实现为日志）"""
        # 在实际应用中，这里可以集成WebSocket或SSE实现实时推送
        logger.info(f"浏览器通知: {message.title} - {message.content}")

    async def _send_desktop_notification(self, message: NotificationMessage, config: NotificationConfig) -> None:
        """桌面通知（暂时实现为日志）"""
        # 在实际应用中，这里可以集成系统通知库
        logger.info(f"桌面通知: {message.title} - {message.content}")

    def _update_stats(self, channel: NotificationChannel, success: bool, retry_count: int = 0):
        """更新统计信息"""
        channel_name = channel.value
        if channel_name not in self.stats['by_channel']:
            self.stats['by_channel'][channel_name] = {
                'success': 0, 'failed': 0
            }

        if success:
            self.stats['by_channel'][channel_name]['success'] += 1
            self.stats['total_sent'] += 1
            self.stats['last_sent'] = datetime.now()
        else:
            self.stats['by_channel'][channel_name]['failed'] += 1
            self.stats['total_failed'] += 1

    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return self.stats.copy()

    def get_queue_status(self) -> Dict[str, Any]:
        """获取队列状态"""
        return {
            'queue_size': self.queue.size(),
            'processing': self.queue.processing,
            'max_size': self.queue.max_size
        }

    def create_notification_template(self,
                                   name: str,
                                   title_template: str,
                                   content_template: str,
                                   channel: NotificationChannel = NotificationChannel.DINGTALK,
                                   variables: List[str] = None,
                                   priority: NotificationPriority = NotificationPriority.NORMAL) -> bool:
        """创建通知模板"""
        try:
            template = NotificationTemplate(
                name=name,
                title_template=title_template,
                content_template=content_template,
                variables=variables or [],
                channel=channel,
                priority=priority
            )

            # 保存到数据库
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute('''
                INSERT OR REPLACE INTO notification_templates
                (name, title_template, content_template, variables, channel, priority)
                VALUES (?, ?, ?, ?, ?, ?)
            '', (name, title_template, content_template,
                  json.dumps(variables or []), channel.value, priority.value))

            conn.commit()
            conn.close()

            self.templates[name] = template
            logger.info(f"创建通知模板: {name}")
            return True

        except Exception as e:
            logger.error(f"创建通知模板失败: {str(e)}")
            return False

    def update_notification_config(self, config_name: str, config: NotificationConfig) -> bool:
        """更新通知配置"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute('''
                INSERT OR REPLACE INTO notification_configs
                (name, channel, webhook_url, secret, access_token, chat_id,
                 email_address, smtp_config, template, enabled, priority, rate_limit, batch_size)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            '', (config_name, config.channel.value, config.webhook_url, config.secret,
                  config.access_token, config.chat_id, config.email_address,
                  json.dumps(config.smtp_config) if config.smtp_config else None,
                  config.template, config.enabled, config.priority.value,
                  config.rate_limit, config.batch_size))

            conn.commit()
            conn.close()

            # 更新内存中的配置
            self.configs[f"{config_name}_{config.channel.value}"] = config
            logger.info(f"更新通知配置: {config_name}")
            return True

        except Exception as e:
            logger.error(f"更新通知配置失败: {str(e)}")
            return False

# 创建全局通知管理器实例
notification_manager = EnhancedNotificationManager()

# 便捷函数
async def send_notification(channel: NotificationChannel,
                            title: str,
                            content: str,
                            **kwargs) -> bool:
    """发送通知的便捷函数"""
    return await notification_manager.send_notification(channel, title, content, **kwargs)

async def trigger_notification(event_type: str,
                             title: str,
                             content: str,
                             **kwargs) -> bool:
    """触发类型化通知"""
    return await notification_manager.send_notification(
        channel=NotificationChannel.DINGTALK,
        title=f"[{event_type}] {title}",
        content=content,
        **kwargs
    )

if __name__ == "__main__":
    # 测试代码
    asyncio.run(send_notification(
        channel=NotificationChannel.DINGTALK,
        title="测试通知",
        content="这是一条测试通知消息"
    ))