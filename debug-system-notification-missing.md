# [OPEN] Debug Session: system-notification-missing

## 问题摘要
- 现象：当前应用“根本不显示系统通知”。
- 目标：定位 macOS 系统通知链路失败的具体环节，并在获得运行时证据后做最小修复。

## 当前假设
- H1：macOS 原生通知中心桥接对象创建成功，但 `deliverNotification:` 没有真正调用成功。
- H2：通知实际已提交，但因为 delegate / selector / type encoding 错误，前台场景被系统静默抑制。
- H3：通知对象字段设置不完整或对象生命周期异常，导致系统直接丢弃通知。
- H4：应用当前运行上下文或系统授权状态不允许通知显示。
- H5：问题只发生在 macOS 原生桥接路径，Qt 托盘消息或 Linux/Windows 路径未受影响。

## 调试计划
1. 阅读调试规范并确认日志采集方案。
2. 启动 Debug Server。
3. 仅添加通知链路插桩，不修改业务逻辑。
4. 复现并收集日志。
5. 基于证据判断根因，再实施最小修复。

## 证据分析（pre-fix）
| ID | 假设 | 状态 | 证据 |
|----|------|------|------|
| A | `deliverNotification:` 根本没成功执行 | ❌ 否定 | 日志 4 显示 `deliverNotification called` |
| B | delegate / type encoding 导致前台被抑制 | ⏳ 未定 | 日志 1 显示 delegate 已创建，但通知中心本身为 `None`，当前证据不足以单独确认 delegate 问题 |
| C | 通知对象创建失败 | ❌ 否定 | 日志 3 显示 `notification object created` 且 `is_null=false` |
| D | 通知中心对象为空导致通知未真正提交 | ✅ 确认 | 日志 1、4 中 `center` 都是 `None` |
| E | 事件没有走到 macOS 通知路径 | ❌ 否定 | 日志 2 已进入 `show_message` |

## 当前结论
- 当前根因是 macOS 原生通知桥接拿到的通知中心对象为空。
- 现有 `NSUserNotificationCenter` 路径不可靠，下一步改为 Apple 当前推荐的 `UNUserNotificationCenter` 本地通知链路，并补授权检查。

## 证据分析（post-fix）
| ID | 假设 | 状态 | 证据 |
|----|------|------|------|
| A | 通知调用未进入发送函数 | ❌ 否定 | post-fix 日志 2 显示 `show_message entered` |
| B | 当前运行环境不是有效 App Bundle | ✅ 确认 | post-fix 日志 1 显示 `bundle_id=""`，`bundle_path=.venv/bin`，`use_user_notifications=false` |
| C | 修复后仍在调用会崩溃的 `UNUserNotificationCenter` | ❌ 否定 | post-fix 日志 1 显示未进入该路径 |
| D | 开发态已切到系统通知 fallback | ✅ 确认 | post-fix 日志 3 显示 `osascript fallback used` |

## 修复结论
- macOS 在开发态没有有效 App Bundle 身份时，不再强行调用 `UNUserNotificationCenter`。
- 开发态自动回退到 `osascript display notification`，保证系统通知可显示且应用直接启动不报错。
- 打包为正式 `.app` 后，仍保留走 `UNUserNotificationCenter` 的能力。
