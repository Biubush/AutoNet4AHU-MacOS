#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import requests
import os
import logging
import subprocess
import sys
from urllib.parse import urlparse

# 获取logger
logger = logging.getLogger('AutoNet4AHU.notify')

class Notifier:
    """通知模块，用于发送消息通知"""
    
    def __init__(self, webhook_urls, timeout=10):
        """
        初始化通知器实例
        
        Args:
            webhook_urls: webhook URL的列表或字符串
            timeout: 请求超时时间(秒)
        """
        if isinstance(webhook_urls, str):
            self.webhook_urls = [webhook_urls]
        else:
            self.webhook_urls = webhook_urls
        
        self.timeout = timeout
        
        # 获取系统代理设置
        self.proxies = self._get_system_proxies()
        
        # 创建会话对象，提高连接复用效率
        self.session = requests.Session()
    
    def _get_system_proxies(self):
        """
        获取macOS系统代理设置
        
        Returns:
            dict: 包含http和https代理的字典，如果没有代理则返回空字典
        """
        proxies = {}
        
        try:
            # 首先检查环境变量中的代理设置（通用方法）
            http_proxy = os.environ.get('HTTP_PROXY') or os.environ.get('http_proxy')
            https_proxy = os.environ.get('HTTPS_PROXY') or os.environ.get('https_proxy')
            
            if http_proxy:
                proxies['http'] = http_proxy
            if https_proxy:
                proxies['https'] = https_proxy
            
            # 如果环境变量中没有代理设置，则尝试获取macOS系统代理
            if not proxies:
                mac_proxies = self._get_macos_proxies()
                if mac_proxies:
                    proxies.update(mac_proxies)
            
            # 记录代理设置
            if proxies:
                logger.info(f"使用系统代理: {proxies}")
            else:
                logger.info("未使用代理")
                
        except Exception as e:
            logger.error(f"获取系统代理时发生错误: {str(e)}")
            
        return proxies
    
    def _get_macos_proxies(self):
        """
        获取macOS特定的系统代理设置
        
        Returns:
            dict: 包含http和https代理的字典，如果没有代理则返回空字典
        """
        try:
            # 使用macOS特有的命令获取代理设置
            # 检查HTTP代理
            http_proxy_cmd = "networksetup -getwebproxy Wi-Fi"
            http_proxy_enabled = subprocess.run(f"{http_proxy_cmd} | grep 'Enabled' | awk '{{print $2}}'", 
                                             shell=True, capture_output=True, text=True).stdout.strip()
            
            # 检查HTTPS代理
            https_proxy_cmd = "networksetup -getsecurewebproxy Wi-Fi"
            https_proxy_enabled = subprocess.run(f"{https_proxy_cmd} | grep 'Enabled' | awk '{{print $2}}'", 
                                              shell=True, capture_output=True, text=True).stdout.strip()
            
            proxies = {}
            
            # 如果HTTP代理已启用
            if http_proxy_enabled.lower() == "yes":
                http_proxy_server = subprocess.run(f"{http_proxy_cmd} | grep 'Server' | awk '{{print $2}}'", 
                                               shell=True, capture_output=True, text=True).stdout.strip()
                http_proxy_port = subprocess.run(f"{http_proxy_cmd} | grep 'Port' | awk '{{print $2}}'", 
                                              shell=True, capture_output=True, text=True).stdout.strip()
                
                if http_proxy_server and http_proxy_port:
                    proxies['http'] = f"http://{http_proxy_server}:{http_proxy_port}"
            
            # 如果HTTPS代理已启用
            if https_proxy_enabled.lower() == "yes":
                https_proxy_server = subprocess.run(f"{https_proxy_cmd} | grep 'Server' | awk '{{print $2}}'", 
                                                shell=True, capture_output=True, text=True).stdout.strip()
                https_proxy_port = subprocess.run(f"{https_proxy_cmd} | grep 'Port' | awk '{{print $2}}'", 
                                               shell=True, capture_output=True, text=True).stdout.strip()
                
                if https_proxy_server and https_proxy_port:
                    proxies['https'] = f"https://{https_proxy_server}:{https_proxy_port}"
            
            return proxies
        except Exception as e:
            logger.error(f"获取macOS代理设置时发生错误: {str(e)}")
            return {}
    
    def validate_webhook_url(self, url):
        """
        验证webhook URL是否有效
        
        Args:
            url: 要验证的URL
            
        Returns:
            bool: URL是否有效
        """
        try:
            # 简单验证URL格式
            result = urlparse(url)
            if not all([result.scheme, result.netloc]):
                return False
                
            # 验证是否是企业微信webhook地址
            if "qyapi.weixin.qq.com" not in result.netloc:
                logger.warning(f"URL不是企业微信域名: {url}")
                # 不强制要求必须是企业微信域名
            
            return True
        except Exception as e:
            logger.error(f"验证webhook URL时发生错误: {str(e)}")
            return False
    
    def send_text(self, content, mentioned_list=None, mentioned_mobile_list=None):
        """
        发送文本消息
        
        Args:
            content: 消息内容
            mentioned_list: 要@的成员ID列表
            mentioned_mobile_list: 要@的成员手机号列表
            
        Returns:
            bool: 是否发送成功
        """
        data = {
            "msgtype": "text",
            "text": {
                "content": content,
                "mentioned_list": mentioned_list or [],
                "mentioned_mobile_list": mentioned_mobile_list or [],
            },
        }
        return self._send(data)
    
    def send_markdown(self, content):
        """
        发送markdown消息
        
        Args:
            content: markdown格式的消息内容
            
        Returns:
            bool: 是否发送成功
        """
        data = {
            "msgtype": "markdown",
            "markdown": {
                "content": content
            }
        }
        return self._send(data)
    
    def _send(self, data, webhook_url=None):
        """
        发送消息到指定的webhook URL
        
        Args:
            data: 要发送的消息数据
            webhook_url: 要发送的webhook URL，如果不指定，则发送到所有webhook URLs
            
        Returns:
            bool: 是否发送成功
        """
        if webhook_url is None:
            webhooks = self.webhook_urls
        else:
            webhooks = [webhook_url]
        
        all_success = True
        
        for webhook in webhooks:
            # 验证webhook URL
            if not self.validate_webhook_url(webhook):
                logger.error(f"无效的webhook URL: {webhook}")
                all_success = False
                continue
                
            try:
                headers = {"Content-Type": "application/json"}
                
                # 使用requests会话和系统代理发送请求
                response = self.session.post(
                    webhook, 
                    headers=headers, 
                    data=json.dumps(data, ensure_ascii=False).encode('utf-8'),
                    proxies=self.proxies if self.proxies else None,
                    timeout=self.timeout
                )
                
                # 处理响应
                if response.status_code != 200:
                    logger.error(f"发送消息失败，HTTP状态码: {response.status_code}")
                    all_success = False
                    continue
                
                # 解析响应JSON
                try:
                    result = response.json()
                    if result.get("errcode") != 0:
                        error_msg = result.get("errmsg", "未知错误")
                        logger.error(f"发送消息失败，错误码: {result.get('errcode')}, 错误信息: {error_msg}")
                        all_success = False
                    else:
                        logger.info(f"消息发送成功: {webhook}")
                except json.JSONDecodeError:
                    logger.error(f"解析响应JSON失败: {response.text}")
                    all_success = False
                    
            except requests.exceptions.Timeout:
                logger.error(f"发送消息超时: {webhook}")
                all_success = False
            except requests.exceptions.ConnectionError:
                logger.error(f"连接错误: {webhook}")
                all_success = False
            except Exception as e:
                logger.exception(f"发送消息过程中发生错误: {str(e)}")
                all_success = False
        
        return all_success


# 使用示例
if __name__ == "__main__":
    # 设置日志
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    if len(sys.argv) > 1:
        webhook_url = sys.argv[1]
    else:
        webhook_url = input("请输入企业微信webhook URL: ")
    
    # 初始化通知器
    notifier = Notifier(webhook_urls=webhook_url)
    
    # 发送测试消息
    success = notifier.send_text("这是一条来自AutoNet4AHU-MacOS的测试消息")
    print(f"消息发送{'成功' if success else '失败'}")
    
    # 发送markdown消息
    markdown_content = """
# 测试markdown消息
- 项目: **AutoNet4AHU-MacOS**
- 状态: <font color="info">正常</font>
- 时间: {0}
    """.format(__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    
    success = notifier.send_markdown(markdown_content)
    print(f"Markdown消息发送{'成功' if success else '失败'}")
    
    # 打印当前使用的代理
    print(f"当前系统代理设置: {notifier.proxies}") 