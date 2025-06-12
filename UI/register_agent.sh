#!/bin/bash

# 设置UTF-8编码
export LANG=en_US.UTF-8

# 获取当前目录
CURRENT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
PLIST_TEMPLATE="${CURRENT_DIR}/com.biubush.autonet4ahu.plist"
SCRIPT_PATH="${CURRENT_DIR}/ahu_eportal.py"
LAUNCH_AGENTS_DIR="${HOME}/Library/LaunchAgents"
TARGET_PLIST="${LAUNCH_AGENTS_DIR}/com.biubush.autonet4ahu.plist"
LOG_DIR="${HOME}/Library/Logs/AutoNet4AHU"

echo "开始注册AutoNet4AHU自动登录服务..."

# 检查python3是否安装
if ! command -v python3 &> /dev/null; then
    echo "错误: 未找到python3命令，请确保已安装Python 3" >&2
    exit 1
fi

# 获取python3路径
PYTHON_PATH=$(which python3)
echo "找到Python路径: ${PYTHON_PATH}"

# 确保脚本可执行
chmod +x "${SCRIPT_PATH}"
echo "已设置脚本可执行权限"

# 确保目录存在
mkdir -p "${LAUNCH_AGENTS_DIR}"
mkdir -p "${LOG_DIR}"
echo "已创建必要目录"

# 处理模板文件，替换占位符
if [ -f "${PLIST_TEMPLATE}" ]; then
    echo "使用模板文件: ${PLIST_TEMPLATE}"
    
    # 替换占位符并生成最终的plist文件
    sed -e "s|%PYTHON_PATH%|${PYTHON_PATH}|g" \
        -e "s|%SCRIPT_PATH%|${SCRIPT_PATH}|g" \
        -e "s|%LOG_PATH%|${LOG_DIR}|g" \
        -e "s|%WORKING_DIR%|${CURRENT_DIR}|g" \
        "${PLIST_TEMPLATE}" > "${TARGET_PLIST}"
    
    echo "已生成启动项配置文件: ${TARGET_PLIST}"
    
    # 卸载可能已存在的启动项
    if launchctl list | grep com.biubush.autonet4ahu &> /dev/null; then
        echo "卸载已存在的启动项..."
        launchctl unload "${TARGET_PLIST}" 2>/dev/null
    fi
    
    # 加载新的启动项
    echo "正在加载启动项..."
    launchctl load "${TARGET_PLIST}"
    
    # 检查是否成功加载
    if launchctl list | grep com.biubush.autonet4ahu &> /dev/null; then
        echo "启动项注册成功！"
        echo "系统已启用AutoNet4AHU自动登录服务。"
        echo "服务将在系统启动和网络状态变化时自动运行。"
        exit 0
    else
        echo "错误: 启动项注册失败，请检查日志获取更多信息" >&2
        exit 1
    fi
else
    echo "错误: 未找到模板文件: ${PLIST_TEMPLATE}" >&2
    exit 1
fi 