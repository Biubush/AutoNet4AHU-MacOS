#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import socket
import re
import json
import logging
import time
import subprocess
from urllib.parse import urlencode

# 获取logger
logger = logging.getLogger('AutoNet4AHU.portal')

class ePortal:
    """安徽大学校园网自动登录类"""
    
    def __init__(self, user_account, user_password, max_retries=3, retry_interval=2):
        """
        初始化ePortal实例
        
        Args:
            user_account: 学号
            user_password: 密码
            max_retries: 最大重试次数
            retry_interval: 重试间隔(秒)
        """
        self.user_account = user_account
        self.user_password = user_password
        self.max_retries = max_retries
        self.retry_interval = retry_interval
        self.base_url = "http://172.16.253.3:801/eportal/"
        self.login_url = f"{self.base_url}?c=Portal&a=login&callback=dr1003&login_method=1&jsVersion=3.3.2&v=1117"
        self.campus_check_url = "http://172.16.253.3/a79.htm"
        self.headers = {
            "Accept": "*/*",
            "Accept-Language": "zh-CN,zh;q=0.9",
            "Cache-Control": "no-cache",
            "Pragma": "no-cache",
            "Referer": "http://172.16.253.3/",
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Safari/605.1.15"
        }
        self.wlan_user_ip = self.get_local_ip()
        self.session = requests.Session()
        
        # 应对macOS网络环境可能的变化
        self.session.trust_env = True  # 允许从环境变量读取代理配置
    
    def get_local_ip(self):
        """
        获取本机IP地址，针对macOS系统优化
        
        Returns:
            str: 本机IP地址
        """
        try:
            # 首先尝试使用原生macOS命令获取网络接口信息
            result = self._get_mac_active_ip()
            if result:
                logger.info(f"通过macOS命令获取到IP地址: {result}")
                return result
            
            # 如果macOS命令失败，尝试通过socket连接获取
            logger.info("尝试通过socket连接获取IP地址")
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.settimeout(1.0)  # 设置较短的超时时间
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            logger.info(f"通过socket连接获取到IP地址: {ip}")
            return ip
        except Exception as e:
            # 如果上述方法失败，尝试其他方法
            logger.warning(f"通过socket连接获取IP地址失败: {e}")
            try:
                hostname = socket.gethostname()
                ip = socket.gethostbyname(hostname)
                logger.info(f"通过hostname获取到IP地址: {ip}")
                return ip
            except Exception as e:
                logger.error(f"获取IP地址失败: {e}")
                # 在macOS上，优先返回一个可能的局域网IP范围
                return "10.0.0.1"  # macOS常用局域网IP
    
    def _get_mac_active_ip(self):
        """
        使用macOS特有命令获取活动网络接口的IP地址
        
        Returns:
            str: 活动网络接口的IP地址，失败返回None
        """
        try:
            # 使用ifconfig和grep查找活动接口
            cmd = "ifconfig | grep 'inet ' | grep -v 127.0.0.1 | awk '{print $2}' | head -n 1"
            ip = subprocess.check_output(cmd, shell=True, universal_newlines=True).strip()
            if ip:
                return ip
            return None
        except Exception as e:
            logger.warning(f"通过macOS命令获取IP地址失败: {e}")
            return None
    
    def check_network_connectivity(self):
        """
        检查网络连接是否可用
        
        Returns:
            bool: 网络是否可用
        """
        try:
            # 首先尝试访问校园网
            if self.is_connected_to_campus_network():
                return True
            
            # 如果校园网不可访问，检查互联网连接
            response = requests.get("https://www.baidu.com", timeout=5)
            return response.status_code == 200
        except Exception as e:
            logger.warning(f"网络连接检查失败: {e}")
            return False
    
    def is_connected_to_campus_network(self):
        """
        检查是否已连接到校园网（但可能尚未认证）
        
        Returns:
            bool: 是否已连接到校园网
        """
        try:
            response = self.session.get(self.campus_check_url, timeout=5, headers=self.headers)
            return response.status_code == 200
        except Exception as e:
            logger.warning(f"校园网连接检查失败: {e}")
            return False
    
    def is_already_logged_in(self):
        """
        检查是否已经登录校园网
        
        Returns:
            bool: 是否已登录
        """
        try:
            # 尝试访问外网
            response = requests.get("https://www.baidu.com", timeout=5)
            return response.status_code == 200
        except Exception:
            return False
    
    def login(self):
        """
        执行登录操作，支持重试机制
        
        Returns:
            tuple: (bool, str) 登录是否成功，登录结果信息
        """
        # 检查是否已登录
        if self.is_already_logged_in():
            logger.info("已经登录校园网，无需再次登录")
            return True, "已经登录校园网"
        
        # 检查网络连接状态
        if not self.check_network_connectivity():
            logger.error("网络连接不可用")
            return False, "网络连接不可用"
        
        # 检查是否已连接到校园网
        if not self.is_connected_to_campus_network():
            logger.error("尚未连接校园网")
            return False, "尚未连接校园网"
            
        # 支持重试机制
        for attempt in range(1, self.max_retries + 1):
            try:
                logger.info(f"尝试登录 (第 {attempt}/{self.max_retries} 次)")
                # 更新IP地址，因为可能已经变化
                if attempt > 1:
                    self.wlan_user_ip = self.get_local_ip()
                    logger.info(f"更新IP地址: {self.wlan_user_ip}")
                
                # 构建登录参数
                params = {
                    "c": "Portal",
                    "a": "login",
                    "callback": "dr1003",
                    "login_method": "1",
                    "user_account": self.user_account,
                    "user_password": self.user_password,
                    "wlan_user_ip": self.wlan_user_ip,
                    "wlan_user_ipv6": "",
                    "wlan_user_mac": "000000000000",
                    "wlan_ac_ip": "",
                    "wlan_ac_name": "",
                    "jsVersion": "3.3.2",
                    "v": "1117"
                }
                
                # 发送登录请求
                response = self.session.get(
                    self.login_url, 
                    params=params,
                    headers=self.headers,
                    timeout=10  # 增加超时时间
                )
                
                # 处理返回结果
                if response.status_code == 200:
                    # 提取JSON数据 (通常在dr1003()中)
                    json_str = re.search(r'dr1003\((.*)\)', response.text)
                    if json_str:
                        result = json.loads(json_str.group(1))
                        if result.get("result") == "1":
                            logger.info("登录成功")
                            return True, "登录成功"
                        else:
                            error_msg = result.get("msg", "登录失败，未知原因")
                            logger.error(f"登录失败: {error_msg}")
                            
                            # 检查是否是密码错误，如果是则不再重试
                            if "密码错误" in error_msg or "用户不存在" in error_msg:
                                return False, error_msg
                            
                            # 其他错误继续重试
                    else:
                        logger.warning(f"无法解析返回数据: {response.text[:100]}...")
                else:
                    logger.error(f"HTTP请求失败，状态码: {response.status_code}")
            
            except requests.exceptions.Timeout:
                logger.warning("登录请求超时")
            except requests.exceptions.ConnectionError:
                logger.warning("连接错误，可能是网络不稳定")
            except Exception as e:
                logger.exception(f"登录过程中发生异常: {str(e)}")
            
            # 如果不是最后一次尝试，等待后重试
            if attempt < self.max_retries:
                logger.info(f"等待 {self.retry_interval} 秒后重试...")
                time.sleep(self.retry_interval)
        
        return False, f"登录失败，已尝试 {self.max_retries} 次"


# 使用示例
if __name__ == "__main__":
    import getpass
    import sys
    
    # 设置日志
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    user_account = input("请输入学号: ")
    user_password = getpass.getpass("请输入密码: ")
    
    portal = ePortal(user_account, user_password)
    success, message = portal.login()
    
    print(message)
    if not success:
        sys.exit(1) 