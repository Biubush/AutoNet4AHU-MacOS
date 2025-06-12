#!/bin/bash

# 设置UTF-8编码
export LANG=en_US.UTF-8

echo "开始编译UI模块..."

# 获取当前目录和项目根目录
CURRENT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
ROOT_DIR="$(dirname "$CURRENT_DIR")"
APP_NAME="AutoNet4AHU"

# 检查PyInstaller是否已安装
if ! pip show pyinstaller > /dev/null; then
    echo "PyInstaller未安装，正在安装..."
    pip install pyinstaller
fi

# 检查login程序是否存在
if [ ! -f "$CURRENT_DIR/login" ]; then
    echo "错误: login程序不存在，请先编译登录核心模块"
    exit 1
fi

# 确保login程序有执行权限
chmod +x "$CURRENT_DIR/login"

# 生成macOS应用图标
if [ ! -f "$CURRENT_DIR/icon.icns" ] && [ -f "$CURRENT_DIR/icon.png" ]; then
    echo "正在生成macOS应用图标..."
    
    # 创建临时图标目录
    mkdir -p "$CURRENT_DIR/icon.iconset"
    
    # 生成不同尺寸的图标
    sips -z 16 16 "$CURRENT_DIR/icon.png" --out "$CURRENT_DIR/icon.iconset/icon_16x16.png"
    sips -z 32 32 "$CURRENT_DIR/icon.png" --out "$CURRENT_DIR/icon.iconset/icon_16x16@2x.png"
    sips -z 32 32 "$CURRENT_DIR/icon.png" --out "$CURRENT_DIR/icon.iconset/icon_32x32.png"
    sips -z 64 64 "$CURRENT_DIR/icon.png" --out "$CURRENT_DIR/icon.iconset/icon_32x32@2x.png"
    sips -z 128 128 "$CURRENT_DIR/icon.png" --out "$CURRENT_DIR/icon.iconset/icon_128x128.png"
    sips -z 256 256 "$CURRENT_DIR/icon.png" --out "$CURRENT_DIR/icon.iconset/icon_128x128@2x.png"
    sips -z 256 256 "$CURRENT_DIR/icon.png" --out "$CURRENT_DIR/icon.iconset/icon_256x256.png"
    sips -z 512 512 "$CURRENT_DIR/icon.png" --out "$CURRENT_DIR/icon.iconset/icon_256x256@2x.png"
    sips -z 512 512 "$CURRENT_DIR/icon.png" --out "$CURRENT_DIR/icon.iconset/icon_512x512.png"
    
    # 使用iconutil创建.icns文件
    iconutil -c icns "$CURRENT_DIR/icon.iconset"
    
    # 清理临时目录
    rm -rf "$CURRENT_DIR/icon.iconset"
    
    echo "图标生成完成: $CURRENT_DIR/icon.icns"
fi

# 使用PyInstaller编译
echo "使用PyInstaller编译应用..."
pyinstaller \
  --name="${APP_NAME}" \
  --icon="${CURRENT_DIR}/icon.icns" \
  --windowed \
  --add-data="${CURRENT_DIR}/login:." \
  --add-data="${CURRENT_DIR}/register_agent.sh:." \
  --add-data="${CURRENT_DIR}/unregister_agent.sh:." \
  --add-data="${CURRENT_DIR}/com.biubush.autonet4ahu.plist:." \
  --add-data="${CURRENT_DIR}/ahu_eportal.py:." \
  --add-data="${CURRENT_DIR}/icon.png:." \
  --noconfirm \
  --clean \
  "${CURRENT_DIR}/ui.py"

# 确保脚本有执行权限
echo "设置可执行权限..."
chmod +x "dist/${APP_NAME}.app/Contents/MacOS/${APP_NAME}"
chmod +x "dist/${APP_NAME}.app/Contents/MacOS/register_agent.sh"
chmod +x "dist/${APP_NAME}.app/Contents/MacOS/unregister_agent.sh"
chmod +x "dist/${APP_NAME}.app/Contents/MacOS/ahu_eportal.py"
chmod +x "dist/${APP_NAME}.app/Contents/MacOS/login"

# 移动应用程序到项目根目录
echo "移动应用到项目根目录..."
mv "dist/${APP_NAME}.app" "${ROOT_DIR}/"

# 创建DMG镜像
echo "创建DMG镜像..."

# 检查create-dmg命令是否存在
if command -v create-dmg &> /dev/null; then
    create-dmg \
      --volname "${APP_NAME}" \
      --volicon "${CURRENT_DIR}/icon.icns" \
      --window-pos 200 120 \
      --window-size 800 400 \
      --icon-size 100 \
      --icon "${APP_NAME}.app" 200 190 \
      --app-drop-link 600 185 \
      "${ROOT_DIR}/${APP_NAME}.dmg" \
      "${ROOT_DIR}/${APP_NAME}.app"
else
    # 如果没有create-dmg，使用hdiutil创建基本DMG
    hdiutil create -volname "${APP_NAME}" -srcfolder "${ROOT_DIR}/${APP_NAME}.app" -ov -format UDZO "${ROOT_DIR}/${APP_NAME}.dmg"
fi

# 清理临时文件
echo "清理临时文件..."
rm -rf build dist *.spec

echo "UI模块编译完成！"
echo "应用程序: ${ROOT_DIR}/${APP_NAME}.app"
echo "镜像文件: ${ROOT_DIR}/${APP_NAME}.dmg" 