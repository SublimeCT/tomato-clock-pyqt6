# 番茄专注

## 技术栈
- [pyqt6](https://www.riverbankcomputing.com/static/Docs/PyQt6/)
- [uv](https://docs.astral.sh/uv): 现代化的包管理工具

## 贡献
### 开发环境

```bash
# 安装依赖
uv sync

# 运行应用
uv run src/main.py
```

### 打包

```bash
uv run pyinstaller --name TomatoClock --windowed --clean --noconfirm --collect-all PyQt6 --icon icon.icns src/main.py
```

```bash
# 打开应用, 或直接在 finder 中双击运行
./dist/TomatoClock.app/Contents/MacOS/TomatoClock
```

#### 制作应用图标
```bash
mkdir icon.iconset

sips -z 16 16 src/assets/app-icon-256.png -o icon.iconset/icon_16x16.png
sips -z 32 32 src/assets/app-icon-256.png -o icon.iconset/icon_32x32.png
sips -z 128 128 src/assets/app-icon-256.png -o icon.iconset/icon_128x128.png
sips -z 256 256 src/assets/app-icon-256.png -o icon.iconset/icon_256x256.png
sips -z 512 512 src/assets/app-icon-512.png -o icon.iconset/icon_512x512.png

iconutil -c icns icon.iconset
```