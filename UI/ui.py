#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
import json
import subprocess
import shutil
from pathlib import Path
import logging

from PySide6.QtCore import Qt, QSize, QUrl, QTimer
from PySide6.QtGui import QDesktopServices, QIcon
from PySide6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                              QLineEdit, QSpacerItem, QSizePolicy, QMessageBox,
                              QPushButton, QMainWindow, QSystemTrayIcon, QMenu)

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('AutoNet4AHU.UI')

class StyledPushButton(QPushButton):
    """自定义按钮类，设置统一的样式"""
    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self.setMinimumHeight(32)
        font = self.font()
        font.setPointSize(12)
        self.setFont(font)

class LoginWidget(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('AHU校园网自动登录程序 (macOS)')
        self.resize(400, 320)
        self.setup_ui()
        self.load_config()
        self.bind_events()
        self.setup_tray()

    def setup_ui(self):
        """设置UI界面"""
        # 创建中央窗口部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 主布局
        self.main_layout = QVBoxLayout(central_widget)
        self.main_layout.setContentsMargins(20, 20, 20, 20)
        self.main_layout.setSpacing(15)
        
        # 学号输入框
        self.student_id_layout = QVBoxLayout()
        self.student_id_label = QLabel('学号')
        self.student_id_line_edit = QLineEdit(self)
        self.student_id_line_edit.setPlaceholderText('请输入学号')
        self.student_id_layout.addWidget(self.student_id_label)
        self.student_id_layout.addWidget(self.student_id_line_edit)
        
        # 密码输入框
        self.password_layout = QVBoxLayout()
        self.password_label = QLabel('密码')
        self.password_line_edit = QLineEdit(self)
        self.password_line_edit.setPlaceholderText('请输入密码')
        self.password_line_edit.setEchoMode(QLineEdit.Password)
        self.password_layout.addWidget(self.password_label)
        self.password_layout.addWidget(self.password_line_edit)
        
        # 企微webhook输入框
        self.webhook_layout = QVBoxLayout()
        self.webhook_label_layout = QHBoxLayout()
        self.webhook_label = QLabel('企微webhook')
        self.info_button = StyledPushButton("?", self)
        self.info_button.setFixedSize(24, 24)
        self.webhook_label_layout.addWidget(self.webhook_label)
        self.webhook_label_layout.addWidget(self.info_button)
        self.webhook_label_layout.addStretch(1)
        
        self.webhook_layout.addLayout(self.webhook_label_layout)
        self.webhook_line_edit = QLineEdit(self)
        self.webhook_line_edit.setPlaceholderText('请输入企微webhook（可不填）')
        self.webhook_layout.addWidget(self.webhook_line_edit)
        
        # 状态信息
        self.status_layout = QVBoxLayout()
        self.status_label = QLabel('当前状态: 未注册启动项')
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_layout.addWidget(self.status_label)
        
        # 按钮布局
        self.button_layout = QHBoxLayout()
        self.button_layout.setSpacing(10)
        
        # 注册按钮
        self.register_button = StyledPushButton('注册启动项', self)
        self.register_button.setStyleSheet("""
            QPushButton {
                background-color: #007aff;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
            }
            QPushButton:hover {
                background-color: #0069d9;
            }
            QPushButton:pressed {
                background-color: #005cbf;
            }
        """)
        
        # 卸载按钮
        self.uninstall_button = StyledPushButton('卸载启动项', self)
        self.uninstall_button.setStyleSheet("""
            QPushButton {
                background-color: #6c757d;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
            }
            QPushButton:hover {
                background-color: #5a6268;
            }
            QPushButton:pressed {
                background-color: #545b62;
            }
        """)
        
        # 立即登录按钮
        self.login_now_button = StyledPushButton('立即登录', self)
        self.login_now_button.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
            }
            QPushButton:hover {
                background-color: #218838;
            }
            QPushButton:pressed {
                background-color: #1e7e34;
            }
        """)
        
        self.button_layout.addWidget(self.register_button)
        self.button_layout.addWidget(self.uninstall_button)
        self.button_layout.addWidget(self.login_now_button)
        
        # 底部信息
        self.footer_layout = QHBoxLayout()
        self.footer_label = QLabel('由<a href="https://github.com/biubush">biubush</a>开发，开源于<a href="https://github.com/biubush/AutoNet4AHU-MacOS">github</a>')
        self.footer_label.setOpenExternalLinks(True)
        self.footer_label.setAlignment(Qt.AlignCenter)
        self.footer_layout.addWidget(self.footer_label)
        
        # 添加到主布局
        self.main_layout.addLayout(self.student_id_layout)
        self.main_layout.addLayout(self.password_layout)
        self.main_layout.addLayout(self.webhook_layout)
        self.main_layout.addSpacing(10)
        self.main_layout.addLayout(self.status_layout)
        self.main_layout.addSpacing(5)
        self.main_layout.addLayout(self.button_layout)
        self.main_layout.addStretch(1)
        self.main_layout.addLayout(self.footer_layout)
        
        # 设置macOS风格
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f8f9fa;
            }
            QWidget {
                font-family: 'SF Pro Display', 'Helvetica Neue', 'Segoe UI';
                font-size: 13px;
            }
            QLabel {
                font-size: 14px;
            }
            QLineEdit {
                padding: 8px;
                border: 1px solid #ced4da;
                border-radius: 4px;
                background-color: white;
            }
            QLineEdit:focus {
                border: 1px solid #007bff;
                outline: none;
            }
        """)
        
        # 检查当前启动项状态
        QTimer.singleShot(500, self.check_agent_status)

    def bind_events(self):
        """绑定事件处理函数"""
        self.register_button.clicked.connect(self.register_agent)
        self.uninstall_button.clicked.connect(self.uninstall_agent)
        self.login_now_button.clicked.connect(self.login_now)
        self.info_button.clicked.connect(self.open_webhook_help)

    def setup_tray(self):
        """设置系统托盘图标"""
        self.tray_icon = QSystemTrayIcon(self)
        
        # 尝试使用应用图标，如果找不到则使用默认图标
        icon_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "icon.png")
        if os.path.exists(icon_path):
            self.tray_icon.setIcon(QIcon(icon_path))
        else:
            self.tray_icon.setIcon(QIcon.fromTheme("network-wired"))
        
        # 创建托盘菜单
        tray_menu = QMenu()
        
        # 添加菜单项
        show_action = tray_menu.addAction("显示主窗口")
        show_action.triggered.connect(self.show)
        
        login_action = tray_menu.addAction("立即登录")
        login_action.triggered.connect(self.login_now)
        
        tray_menu.addSeparator()
        
        quit_action = tray_menu.addAction("退出")
        quit_action.triggered.connect(QApplication.quit)
        
        # 设置托盘菜单
        self.tray_icon.setContextMenu(tray_menu)
        
        # 托盘图标点击事件
        self.tray_icon.activated.connect(self.tray_icon_activated)
        
        # 显示托盘图标
        self.tray_icon.show()
    
    def tray_icon_activated(self, reason):
        """处理托盘图标的激活事件"""
        if reason == QSystemTrayIcon.Trigger:
            # 单击托盘图标，显示/隐藏主窗口
            if self.isVisible():
                self.hide()
            else:
                self.show()
                self.raise_()
                self.activateWindow()
    
    def closeEvent(self, event):
        """重写关闭事件，实现最小化到托盘"""
        if self.tray_icon.isVisible():
            QMessageBox.information(self, "提示", "程序将在后台运行，您可以通过系统托盘图标打开主界面。")
            self.hide()
            event.ignore()
        else:
            super().closeEvent(event)
    
    def open_webhook_help(self):
        """打开企业微信webhook帮助文档"""
        QDesktopServices.openUrl(QUrl("https://developer.work.weixin.qq.com/document/path/91770"))
    
    def check_agent_status(self):
        """检查启动项状态"""
        try:
            result = subprocess.run(
                ["launchctl", "list"], 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE,
                text=True
            )
            
            if "com.biubush.autonet4ahu" in result.stdout:
                self.status_label.setText("当前状态: 已注册启动项 ✅")
                self.status_label.setStyleSheet("color: #28a745;")
            else:
                self.status_label.setText("当前状态: 未注册启动项 ❌")
                self.status_label.setStyleSheet("color: #dc3545;")
                
        except Exception as e:
            logger.error(f"检查启动项状态失败: {e}")
            self.status_label.setText("当前状态: 检查失败 ⚠️")
            self.status_label.setStyleSheet("color: #ffc107;")
    
    def load_config(self):
        """加载配置文件"""
        try:
            # 尝试从用户目录读取配置
            user_config_path = os.path.expanduser("~/Library/Application Support/AutoNet4AHU/config.json")
            
            if os.path.exists(user_config_path):
                with open(user_config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    
                    self.student_id_line_edit.setText(config.get('student_id', ''))
                    self.password_line_edit.setText(config.get('password', ''))
                    
                    # 如果webhook_urls非空，则使用第一个URL
                    webhook_urls = config.get('webhook_urls', [])
                    if webhook_urls and len(webhook_urls) > 0:
                        self.webhook_line_edit.setText(webhook_urls[0])
                        
                logger.info("已从用户目录加载配置")
                return
            
            # 如果用户目录没有配置文件，尝试从应用目录读取
            app_config_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "config.json")
            
            if os.path.exists(app_config_path):
                with open(app_config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    
                    self.student_id_line_edit.setText(config.get('student_id', ''))
                    self.password_line_edit.setText(config.get('password', ''))
                    
                    # 如果webhook_urls非空，则使用第一个URL
                    webhook_urls = config.get('webhook_urls', [])
                    if webhook_urls and len(webhook_urls) > 0:
                        self.webhook_line_edit.setText(webhook_urls[0])
                
                logger.info("已从应用目录加载配置")
            else:
                logger.info("未找到配置文件")
        
        except Exception as e:
            logger.error(f"加载配置失败: {e}")
            QMessageBox.warning(self, "加载配置失败", f"无法加载配置文件: {str(e)}")
    
    def save_config(self):
        """保存配置文件"""
        student_id = self.student_id_line_edit.text().strip()
        password = self.password_line_edit.text().strip()
        webhook_url = self.webhook_line_edit.text().strip()
        
        webhook_urls = []
        if webhook_url:
            webhook_urls.append(webhook_url)
        
        config = {
            'student_id': student_id,
            'password': password,
            'webhook_urls': webhook_urls
        }
        
        try:
            # 保存到用户目录
            user_config_dir = os.path.expanduser("~/Library/Application Support/AutoNet4AHU")
            user_config_path = os.path.join(user_config_dir, "config.json")
            
            # 确保目录存在
            os.makedirs(user_config_dir, exist_ok=True)
            
            with open(user_config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=4, ensure_ascii=False)
            
            logger.info("配置已保存到用户目录")
            
            # 同时保存一份到应用目录
            app_config_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "config.json")
            
            with open(app_config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=4, ensure_ascii=False)
                
            logger.info("配置已保存到应用目录")
            return True
            
        except Exception as e:
            logger.error(f"保存配置失败: {e}")
            QMessageBox.critical(self, "保存配置失败", f"无法保存配置文件: {str(e)}")
            return False
    
    def validate_input(self):
        """验证输入"""
        student_id = self.student_id_line_edit.text().strip()
        password = self.password_line_edit.text().strip()
        
        if not student_id:
            QMessageBox.warning(self, "输入错误", "请输入学号")
            return False
            
        if not password:
            QMessageBox.warning(self, "输入错误", "请输入密码")
            return False
            
        return True
    
    def register_agent(self):
        """注册启动项"""
        # 检查输入
        if not self.validate_input():
            return
        
        # 保存配置
        if not self.save_config():
            return
            
        try:
            # 确认是否注册
            reply = QMessageBox.question(
                self, 
                '注册自启动服务', 
                '确定要注册自动登录服务吗？这将允许程序在系统启动和连接网络时自动登录校园网。',
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.Yes
            )
            
            if reply == QMessageBox.Yes:
                script_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "register_agent.sh")
                
                # 确保脚本有执行权限
                os.chmod(script_path, 0o755)
                
                # 执行注册脚本
                result = subprocess.run(
                    [script_path], 
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )
                
                logger.info(f"注册结果: {result.returncode}")
                logger.info(f"标准输出: {result.stdout}")
                logger.info(f"错误输出: {result.stderr}")
                
                if result.returncode == 0:
                    QMessageBox.information(self, "注册成功", "自动登录服务已成功注册！系统将在启动和网络状态变化时自动登录校园网。")
                    self.check_agent_status()
                else:
                    QMessageBox.critical(self, "注册失败", f"自动登录服务注册失败，错误信息:\n{result.stderr}")
        
        except Exception as e:
            logger.exception(f"注册启动项失败: {e}")
            QMessageBox.critical(self, "注册失败", f"发生异常: {str(e)}")
    
    def uninstall_agent(self):
        """卸载启动项"""
        try:
            # 确认是否卸载
            reply = QMessageBox.question(
                self, 
                '卸载自启动服务', 
                '确定要卸载自动登录服务吗？卸载后将不再自动登录校园网。',
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                script_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "unregister_agent.sh")
                
                # 确保脚本有执行权限
                os.chmod(script_path, 0o755)
                
                # 执行卸载脚本
                result = subprocess.run(
                    [script_path], 
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )
                
                logger.info(f"卸载结果: {result.returncode}")
                logger.info(f"标准输出: {result.stdout}")
                logger.info(f"错误输出: {result.stderr}")
                
                if result.returncode == 0:
                    QMessageBox.information(self, "卸载成功", "自动登录服务已成功卸载！系统将不再自动登录校园网。")
                    self.check_agent_status()
                else:
                    QMessageBox.critical(self, "卸载失败", f"自动登录服务卸载失败，错误信息:\n{result.stderr}")
        
        except Exception as e:
            logger.exception(f"卸载启动项失败: {e}")
            QMessageBox.critical(self, "卸载失败", f"发生异常: {str(e)}")
    
    def login_now(self):
        """立即执行登录"""
        # 检查输入
        if not self.validate_input():
            return
        
        # 保存配置
        if not self.save_config():
            return
            
        try:
            # 获取登录程序路径
            login_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "login")
            
            # 检查登录程序是否存在
            if not os.path.exists(login_path):
                QMessageBox.critical(self, "错误", f"登录程序不存在: {login_path}")
                return
            
            # 确保登录程序有执行权限
            os.chmod(login_path, 0o755)
            
            # 显示正在登录提示
            self.login_now_button.setEnabled(False)
            self.login_now_button.setText("登录中...")
            QApplication.processEvents()
            
            # 执行登录程序
            result = subprocess.run(
                [login_path], 
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            logger.info(f"登录结果: {result.returncode}")
            logger.info(f"标准输出: {result.stdout}")
            logger.info(f"错误输出: {result.stderr}")
            
            # 恢复按钮状态
            self.login_now_button.setEnabled(True)
            self.login_now_button.setText("立即登录")
            
            if result.returncode == 0:
                QMessageBox.information(self, "登录成功", "校园网登录成功！")
            else:
                QMessageBox.warning(self, "登录失败", f"校园网登录失败，错误信息:\n{result.stderr}")
        
        except Exception as e:
            logger.exception(f"执行登录失败: {e}")
            QMessageBox.critical(self, "登录失败", f"发生异常: {str(e)}")
            
            # 恢复按钮状态
            self.login_now_button.setEnabled(True)
            self.login_now_button.setText("立即登录")


if __name__ == '__main__':
    try:
        # 处理高分辨率屏幕
        if hasattr(Qt, 'AA_EnableHighDpiScaling'):
            QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
        if hasattr(Qt, 'AA_UseHighDpiPixmaps'):
            QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
        
        app = QApplication(sys.argv)
        app.setStyle('Fusion')  # 使用Fusion风格，在macOS上看起来更原生
        
        # 设置应用图标
        icon_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "icon.png")
        if os.path.exists(icon_path):
            app.setWindowIcon(QIcon(icon_path))
        
        # 创建并显示窗口
        widget = LoginWidget()
        widget.show()
        
        sys.exit(app.exec())
    
    except Exception as e:
        logger.exception(f"程序运行时发生未处理的异常: {e}")
        # 显示错误对话框
        err_msg = QMessageBox()
        err_msg.setIcon(QMessageBox.Critical)
        err_msg.setText("程序发生严重错误")
        err_msg.setInformativeText(str(e))
        err_msg.setWindowTitle("错误")
        err_msg.exec()
        sys.exit(1) 