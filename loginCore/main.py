#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import os
import sys
import argparse
import logging
from datetime import datetime
from portal import ePortal
from notify import Notifier

# 配置日志系统
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger('AutoNet4AHU')

class AutoLogin:
    """校园网自动登录入口模块"""
    
    def __init__(self, config_file="config.json", log_level=logging.INFO):
        """
        初始化自动登录实例
        
        Args:
            config_file: 配置文件路径
            log_level: 日志级别
        """
        self.config_file = config_file
        self.config = self.load_config()
        
        # 设置日志级别
        logger.setLevel(log_level)
        logger.info("初始化自动登录模块")
    
    def load_config(self):
        """
        加载配置文件，如果不存在则返回空配置
        
        Returns:
            dict: 配置信息
        """
        default_config = {
            "student_id": "",
            "password": "",
            "webhook_urls": []
        }
        
        # 首先检查用户目录下的配置
        user_config_path = os.path.expanduser("~/Library/Application Support/AutoNet4AHU/config.json")
        app_config_path = self.config_file
        
        # 尝试从用户配置目录加载
        if os.path.exists(user_config_path):
            try:
                with open(user_config_path, "r", encoding="utf-8") as f:
                    config = json.load(f)
                logger.info(f"已从用户目录加载配置")
                return config
            except Exception as e:
                logger.error(f"从用户目录加载配置失败: {e}")
                # 继续尝试从应用目录加载
        
        # 尝试从应用目录加载
        if os.path.exists(app_config_path):
            try:
                with open(app_config_path, "r", encoding="utf-8") as f:
                    config = json.load(f)
                logger.info(f"已从应用目录加载配置")
                return config
            except Exception as e:
                logger.error(f"从应用目录加载配置失败: {e}")
                return default_config
        
        logger.warning("未找到配置文件，使用默认配置")
        return default_config
    
    def save_config(self):
        """
        保存配置到用户目录，确保配置持久化
        
        Returns:
            bool: 是否保存成功
        """
        user_config_dir = os.path.expanduser("~/Library/Application Support/AutoNet4AHU")
        user_config_path = os.path.join(user_config_dir, "config.json")
        
        try:
            # 确保目录存在
            os.makedirs(user_config_dir, exist_ok=True)
            
            with open(user_config_path, "w", encoding="utf-8") as f:
                json.dump(self.config, f, indent=4, ensure_ascii=False)
            
            logger.info(f"配置已保存到用户目录: {user_config_path}")
            return True
        except Exception as e:
            logger.error(f"保存配置到用户目录失败: {e}")
            
            # 尝试保存到应用目录作为备选
            try:
                with open(self.config_file, "w", encoding="utf-8") as f:
                    json.dump(self.config, f, indent=4, ensure_ascii=False)
                logger.info(f"配置已保存到应用目录: {self.config_file}")
                return True
            except Exception as e2:
                logger.error(f"保存配置到应用目录也失败: {e2}")
                return False
    
    def config_is_complete(self):
        """
        检查配置是否完整
        
        Returns:
            bool: 配置是否包含必要的信息
        """
        return bool(self.config.get("student_id")) and bool(self.config.get("password"))
    
    def login(self):
        """
        执行登录操作，如果配置不完整则直接退出
        
        Returns:
            bool: 登录是否成功
        """
        # 检查配置是否完整，不完整则直接退出
        if not self.config_is_complete():
            logger.error(f"配置不完整，请配置{self.config_file}文件设置学号和密码")
            return False
        
        student_id = self.config.get("student_id")
        password = self.config.get("password")
        
        # 使用ePortal进行登录
        try:
            portal = ePortal(student_id, password)
            success, message = portal.login()
            
            # 发送通知（如果配置了webhook URLs）
            if self.config.get("webhook_urls"):
                self.send_notification(success, message, portal.wlan_user_ip)
            
            if success:
                logger.info(f"登录成功: {message}")
            else:
                logger.error(f"登录失败: {message}")
            
            return success
        except Exception as e:
            error_msg = f"登录过程中发生异常: {str(e)}"
            logger.exception(error_msg)
            
            # 尝试发送错误通知
            if self.config.get("webhook_urls"):
                self.send_notification(False, error_msg, "未知")
            
            return False
    
    def send_notification(self, success, message, ip_address):
        """
        发送登录结果通知
        
        Args:
            success: 是否登录成功
            message: 登录结果消息
            ip_address: 当前IP地址
        """
        webhook_urls = self.config.get("webhook_urls", [])
        if not webhook_urls:
            return
        
        try:
            notifier = Notifier(webhook_urls)
            
            status = "成功" if success else "失败"
            content = f"校园网登录{status}通知\n\n" \
                    f"学号: {self.config.get('student_id')}\n" \
                    f"IP地址: {ip_address}\n" \
                    f"登录结果: {message}\n" \
                    f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n" \
                    f"设备: macOS {self.get_macos_version()}"
            
            sent = notifier.send_text(content)
            if sent:
                logger.info("通知发送成功")
            else:
                logger.warning("通知发送失败")
        except Exception as e:
            logger.error(f"发送通知时发生错误: {e}")
    
    def get_macos_version(self):
        """
        获取macOS系统版本
        
        Returns:
            str: macOS版本信息
        """
        try:
            import platform
            mac_ver = platform.mac_ver()[0]
            return mac_ver
        except Exception as e:
            logger.error(f"获取macOS版本失败: {e}")
            return "未知版本"


def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description="安徽大学校园网自动登录工具")
    parser.add_argument("-c", "--config", help="指定配置文件路径", default="config.json")
    parser.add_argument("-d", "--debug", help="启用调试模式", action="store_true")
    parser.add_argument("-s", "--silent", help="静默模式，不输出日志", action="store_true")
    parser.add_argument("command", nargs="?", default="login", help="执行的命令，目前支持: login")
    
    return parser.parse_args()


def main():
    """程序入口点"""
    args = parse_args()
    
    # 设置日志级别
    log_level = logging.DEBUG if args.debug else logging.WARNING if args.silent else logging.INFO
    logger.setLevel(log_level)
    
    # 使用指定的配置文件路径创建AutoLogin实例
    auto_login = AutoLogin(config_file=args.config, log_level=log_level)
    
    if args.command == "login":
        success = auto_login.login()
        if not success and not args.silent:
            sys.exit(1)
    else:
        logger.error(f"未知命令: {args.command}")
        logger.info("可用命令: login")
        if not args.silent:
            sys.exit(1)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("程序被用户中断")
        sys.exit(0)
    except Exception as e:
        logger.exception(f"程序运行时发生未处理的异常: {e}")
        sys.exit(1) 