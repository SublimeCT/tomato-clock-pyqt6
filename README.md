# 番茄专注

<p align="center">
  <img src="./src/assets/app-icon-256.png" width="96" height="96" alt="番茄专注" />
</p>

<p align="center">
  <a href="https://github.com/SublimeCT/tomato-clock-pyqt6/releases">
    <img alt="GitHub Release" src="https://img.shields.io/github/v/release/SublimeCT/tomato-clock-pyqt6?display_name=tag&sort=semver&style=flat-square" />
  </a>
  <a href="https://github.com/SublimeCT/tomato-clock-pyqt6/actions/workflows/release.yml">
    <img alt="Build" src="https://img.shields.io/github/actions/workflow/status/SublimeCT/tomato-clock-pyqt6/release.yml?style=flat-square" />
  </a>
  <img alt="Platform" src="https://img.shields.io/badge/platform-Windows%20%7C%20macOS%20%7C%20Linux-111827?style=flat-square" />
  <img alt="Offline" src="https://img.shields.io/badge/offline-available-059669?style=flat-square" />
  <img alt="Open Source" src="https://img.shields.io/badge/open--source-yes-2563eb?style=flat-square" />
</p>

| 页面 | 截图 | 说明 |
|--- |--- |--- |
| 专注 | `MacOS`: ![](./docs/focus_tab.png) `Ubuntu`: ![](./docs/focus_tab_ubuntu.png) `Windows`: ![](./docs/focus_tab_windows.png) | |
| 统计 | ![](./docs/statistics_tab.png) | |
| 统计(年) | ![](./docs/statistics_tab_year.png) | |
| 设置 | ![](./docs/settings_tab.png) | |
| 状态栏(MacOS 倒计时) | ![](./docs/tray_panel.png) | |

## 安装
可从 [github release](https://github.com/SublimeCT/tomato-clock-pyqt6/releases) 页面下载对应的安装包进行安装, 或自行 [打包](#打包)

### Windows
在 `zip` 格式的压缩包内, 直接运行 `TomatoClock.exe` 文件即可

### MacOS
在 `zip` 格式的压缩包内, 直接运行 `TomatoClock.app` 文件即可

### Linux
对于 `Ubuntu 22.04` 或更高版本, 通常执行 `TomatoClock` 文件即可, 目前并没有制作启动器文件, 以下是可能会遇到的报错:

#### 缺少 qt 依赖库
```bash
 ~/Downloads/dist/TomatoClock/TomatoClock 

qt.qpa.plugin: From 6.5.0, xcb-cursor0 or libxcb-cursor0 is needed to load the Qt xcb platform plugin.
qt.qpa.plugin: Could not load the Qt platform plugin "xcb" in "" even though it was found.
This application failed to start because no Qt platform plugin could be initialized. Reinstalling the application may fix this problem.

Available platform plugins are: wayland-brcm, wayland-egl, wayland, xcb, vnc, eglfs, minimal, minimalegl, offscreen, vkkhrdisplay, linuxfb.

Aborted
```

直接更新并安装缺少的依赖, 例如此处是 `libxcb-cursor0`:
```bash
sudo apt-add-repository universe
sudo apt update
sudo apt install -y libxcb-cursor0
```


## 技术栈
- [pyqt6](https://www.riverbankcomputing.com/static/Docs/PyQt6/): `qt` 的 `python` 绑定库
- [uv](https://docs.astral.sh/uv): 现代化的包管理工具

## 贡献
### 开发环境

```bash
# 安装依赖
uv sync
uv pip install -e .

# 运行应用(或点击 `src/main.py` 的 `Run Python File` 按钮)
uv run src/main.py
```

### QT Resource System
静态资源文件必须使用 [Qt Resource System](https://doc.qt.io/qt-6/zh/resources.html) 管理, 当资源文件更新时:

1. 将静态资源文件(图片 / 视频) 放到 `src/assets` 目录下
2. 打开 `resources.qrc` 文件, 添加资源文件
3. 运行 `rcc -g python resources.qrc -o src/assets/reources_rc.py` 生成 `src/assets/reources_rc.py` 文件
4. 在 `src/main.py` 中通过 `from src.assets import reources_rc` 引入(现在已经引入了)

`rcc` 命令来自 `qt` 工具链, 不包含在 `PyQt6` 包中

### 打包

```bash
# 对于 MacOS:
uv run pyinstaller \
  --name TomatoClock \
  --windowed \
  --clean \
  --noconfirm \
  --add-data "pyproject.toml:." \
  --icon icon.icns \
  src/main.py

# 对于 Windows:
uv run pyinstaller \
  --name TomatoClock \
  --windowed \
  --clean \
  --noconfirm \
  --add-data "pyproject.toml;." \
  --icon icon.ico \
  src/main.py
```

```bash
# [MacOS] 打开应用, 或直接在 finder 中双击运行
./dist/TomatoClock.app/Contents/MacOS/TomatoClock
```

本项目使用 `Github Actions` 进行构建, 具体构建命令在 `github/workflows/release.yml` 中

#### 制作应用图标
对于 `MacOS` 需要生成 `icon.iconset`:
```bash
mkdir icon.iconset

sips -z 16 16 src/assets/app-icon-256.png -o icon.iconset/icon_16x16.png
sips -z 32 32 src/assets/app-icon-256.png -o icon.iconset/icon_32x32.png
sips -z 128 128 src/assets/app-icon-256.png -o icon.iconset/icon_128x128.png
sips -z 256 256 src/assets/app-icon-256.png -o icon.iconset/icon_256x256.png
sips -z 512 512 src/assets/app-icon-512.png -o icon.iconset/icon_512x512.png

iconutil -c icns icon.iconset
```

对于 `Windows` 需要生成 `icon.ico`:
```bash
# uv add --dev pillow
uv run python -c "from PIL import Image; img = Image.open('src/assets/app-icon-512.
png'); img.save('icon.ico', format='ICO', sizes=[(16,16), (32,32), (48,48), (64,64), (128,128), (256,256)])"
```
