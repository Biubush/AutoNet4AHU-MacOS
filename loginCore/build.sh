#!/bin/bash

# 设置UTF-8编码
export LANG=en_US.UTF-8

echo "开始编译登录核心模块..."

# 设置输出目录和文件名
OUTPUT_DIR="../UI"
OUTPUT_FILE="login"

# 检查PyInstaller是否已安装
if ! pip show pyinstaller > /dev/null; then
    echo "PyInstaller未安装，正在安装..."
    pip install pyinstaller
fi

# 使用PyInstaller编译
pyinstaller \
  --onefile \
  --name="${OUTPUT_FILE}" \
  --hidden-import=requests \
  --add-data="$(python -c 'import certifi; print(certifi.where())'):certifi" \
  --noconfirm \
  --clean \
  --noconsole \
  main.py

# 移动编译后的文件到指定目录
echo "移动编译后的文件到UI目录..."
mkdir -p ${OUTPUT_DIR}

if [ -f "dist/${OUTPUT_FILE}" ]; then
    cp "dist/${OUTPUT_FILE}" ${OUTPUT_DIR}/
    echo "已复制 ${OUTPUT_FILE} 到 ${OUTPUT_DIR} 目录"
    
    # 设置可执行权限
    chmod +x "${OUTPUT_DIR}/${OUTPUT_FILE}"
    echo "已设置可执行权限"
else
    echo "错误: 编译失败，未找到输出文件: dist/${OUTPUT_FILE}"
    exit 1
fi

# 清理临时文件
echo "清理临时文件..."
rm -rf build dist *.spec

echo "登录核心模块编译完成！输出文件: ${OUTPUT_DIR}/${OUTPUT_FILE}" 