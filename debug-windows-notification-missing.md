# [OPEN] Debug Session: windows-notification-missing

## 问题摘要
- 现象：Windows 上倒计时结束后没有显示系统通知弹窗。
- 目标：定位通知链路在 Windows 平台失败的具体环节，并在拿到运行时证据后实施最小修复。

## 当前假设
- H1：倒计时结束事件没有走到 `_show_system_notification()`。
- H2：Windows 平台进入了 `_show_system_notification()`，但 `QSystemTrayIcon` 实例为空或不可见。
- H3：`QSystemTrayIcon.supportsMessages()` 在当前运行环境返回了 `False`，导致通知没有真正发送。
- H4：通知已经调用了 `showMessage()`，但托盘初始化状态或图标/宿主窗口关系异常，导致系统未展示。
- H5：Windows 需要单独兜底系统通知实现，当前只依赖 Qt 托盘通知不够稳定。

## 调试计划
1. 阅读调试规范并确认日志采集方案。
2. 启动 Debug Server。
3. 仅为通知链路添加最小插桩，不修改业务逻辑。
4. 复现并收集日志。
5. 基于证据判断根因，再实施最小修复。

## 当前证据
- Qt 官方文档明确说明：`QSystemTrayIcon.showMessage()` 的显示依赖系统配置和用户偏好，消息“可能完全不出现”，不应作为关键通知的唯一通道。
- Windows 官方桌面 toast 文档要求非打包桌面应用使用稳定的 `AppUserModelID`，并将该 ID 关联到开始菜单快捷方式，才能走正式通知链路。
- 当前项目原先在 Windows 上仅依赖 `QSystemTrayIcon.showMessage()`，没有设置进程级 `AppUserModelID`，安装器快捷方式也没有声明 `AppUserModelID`。

## 当前修复
- 新增 Windows 原生 toast 发送逻辑，优先使用系统 toast。
- 应用启动时为 Windows 进程设置稳定 `AppUserModelID`。
- Windows 安装器生成的开始菜单 / 桌面快捷方式带上相同的 `AppUserModelID`。
- 若原生 toast 发送失败，则退回 Qt 托盘消息，避免开发态完全无通知。

## 待验证
- 需要在 Windows 安装包环境下复现一次倒计时结束，确认系统 toast 正常显示。
