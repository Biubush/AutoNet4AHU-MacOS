#!/bin/bash

# 设置UTF-8编码
export LANG=en_US.UTF-8

# 获取启动项文件路径
LAUNCH_AGENTS_DIR="${HOME}/Library/LaunchAgents"
TARGET_PLIST="${LAUNCH_AGENTS_DIR}/com.biubush.autonet4ahu.plist"

echo "开始卸载AutoNet4AHU自动登录服务..."

# 检查启动项是否已加载
if launchctl list | grep com.biubush.autonet4ahu &> /dev/null; then
    echo "正在卸载启动项..."
    
    # 尝试卸载启动项
    if launchctl unload "${TARGET_PLIST}" 2>/dev/null; then
        echo "已成功卸载启动项"
    else
        echo "警告: 卸载启动项失败，可能需要手动操作" >&2
    fi
else
    echo "启动项未加载，无需卸载"
fi

# 删除启动项文件
if [ -f "${TARGET_PLIST}" ]; then
    echo "正在删除启动项配置文件..."
    rm -f "${TARGET_PLIST}"
    echo "已删除: ${TARGET_PLIST}"
else
    echo "启动项配置文件不存在，无需删除"
fi

# 检查是否成功完成
if launchctl list | grep com.biubush.autonet4ahu &> /dev/null; then
    echo "警告: 启动项似乎仍然存在，可能需要重启系统或手动卸载" >&2
    exit 1
else
    echo "AutoNet4AHU自动登录服务已成功卸载！"
    echo "系统将不再自动执行登录操作。"
    exit 0
fi 