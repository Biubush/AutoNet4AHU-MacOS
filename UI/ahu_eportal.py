#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
AHU ePortal 自动登录后台脚本
此脚本用于macOS LaunchAgent服务，在网络状态变化时自动执行
"""

import os
import sys
import subprocess
import logging
from datetime import datetime
import time

# 配置日志系统
log_dir = os.path.expanduser("~/Library/Logs/AutoNet4AHU")
os.makedirs(log_dir, exist_ok=True)

log_file = os.path.join(log_dir, "autonet4ahu.log")
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file, encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger('AutoNet4AHU.agent')

def get_script_path():
    """获取当前脚本的路径"""
    return os.path.dirname(os.path.realpath(__file__))

def run_login():
    """运行登录程序"""
    try:
        # 获取login程序路径
        script_dir = get_script_path()
        login_path = os.path.join(script_dir, "login")
        
        # 检查login程序是否存在
        if not os.path.exists(login_path):
            logger.error(f"登录程序不存在: {login_path}")
            return False
        
        # 确保登录程序有执行权限
        os.chmod(login_path, 0o755)
        
        logger.info(f"开始执行登录程序: {login_path}")
        
        # 使用subprocess执行登录程序
        result = subprocess.run(
            [login_path], 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE,
            text=True
        )
        
        # 记录执行结果
        logger.info(f"登录程序执行完成，返回码: {result.returncode}")
        
        if result.stdout:
            logger.info(f"标准输出:\n{result.stdout}")
        if result.stderr:
            logger.error(f"错误输出:\n{result.stderr}")
            
        return result.returncode == 0
    
    except Exception as e:
        logger.exception(f"执行登录程序时发生异常: {e}")
        return False

def main():
    """主函数"""
    logger.info("=" * 50)
    logger.info(f"AHU ePortal 自动登录服务启动 - {datetime.now()}")
    
    # 延迟几秒，确保网络连接已经建立
    time.sleep(3)
    
    # 运行登录程序
    success = run_login()
    logger.info(f"自动登录{'成功' if success else '失败'}")
    
    return 0 if success else 1

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        logger.info("程序被用户中断")
        sys.exit(0)
    except Exception as e:
        logger.exception(f"程序运行时发生未处理的异常: {e}")
        sys.exit(1) 