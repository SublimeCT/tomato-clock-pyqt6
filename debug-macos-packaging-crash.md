# [OPEN] Debug Session: macos-packaging-crash

## 问题摘要
- 现象 1：macOS 打包出来的应用在调用通知时直接闪退。
- 现象 2：当前 macOS 打包产物是目录结构，包含 `_internal`，用户希望评估是否可改为单文件。
- 目标：先定位闪退根因，再审查现有 PyInstaller/macOS 打包配置，判断单文件方案与必要配置调整。

## 当前假设
- H1：打包后的通知闪退由 `UNUserNotificationCenter` / PyObjC 在 bundle 环境下的调用方式引起。
- H2：打包产物缺少 macOS 通知相关的 Info.plist / bundle / 签名元数据，导致通知框架运行时异常。
- H3：PyInstaller 当前使用的是 onedir 模式，因此 `_internal` 目录属于正常产物，不是异常。
- H4：改成 onefile 在 macOS 上虽可行，但会影响 `.app` 资源布局、启动性能和通知/资源访问方式。
- H5：当前 release workflow、spec、README 三处 macOS 构建路径不一致，导致发布配置存在偏差。

## 调试计划
1. 审查现有 spec / workflow / 入口代码和最近的通知实现。
2. 启动 Debug Server。
3. 只添加最小插桩，观察打包环境下通知调用链。
4. 构建并复现闪退，收集日志与 crash 线索。
5. 基于证据修复闪退，再单独给出单文件产物建议与配置方案。

## 证据分析（pre-fix）
| ID | 假设 | 状态 | 证据 |
|----|------|------|------|
| H1 | 闪退来自 `UNUserNotificationCenter` / PyObjC 调用链 | ✅ 确认 | 打包产物运行栈显示崩在 `show_message()` 内的通知内容赋值 |
| H2 | bundle / Info.plist / 授权缺失导致闪退 | ❌ 否定 | 日志显示 `bundle_id=com.sublimect.tomatoclock`，`granted=true`，通知中心初始化成功 |
| H3 | `_internal` 是 onedir 模式正常结果 | ✅ 确认 | 当前 spec 明确使用 `COLLECT(...)`，这是标准 onedir 结构 |
| H4 | 崩溃来自不合理的通知内容字段 | ✅ 确认 | 栈报错：`NSUnknownKeyException ... shouldAlwaysAlertWhileAppIsForeground` |
| H5 | 构建链路存在不一致 | ✅ 确认 | workflow / spec / README 的 macOS 路径近期已被改到 spec，但仍需继续审查 codesign / Info.plist / onefile 策略 |

## pre-fix 关键证据
- 打包态日志显示：
  - `bundle_id` 已存在
  - `use_user_notifications=true`
  - `granted=true`
  - 最后异常为 `UNMutableNotificationContent.setValue_forKey_(..., "shouldAlwaysAlertWhileAppIsForeground")`

## 已实施最小修复
- 移除对 `UNMutableNotificationContent` 不受支持的私有 KVC 字段 `shouldAlwaysAlertWhileAppIsForeground` 设置。

## 证据分析（post-fix）
- 打包产物再次启动后：
  - 应用未再因通知路径退出
  - `add request completion invoked` 且 `error=""`
- 说明闪退根因已被消除。

## onefile 评审结论
- 当前已把 spec 切到 onefile 风格：去掉 `COLLECT(...)`，改为 `BUNDLE(exe, ...)`。
- 构建结果表明：
  - 不再生成 `dist/TomatoClock/_internal` 这种 onedir 输出目录
  - `.app` 内部仍然是 bundle 目录，这是 macOS 正常形态，不可能变成真正的单一裸文件
  - 运行时 `sys._MEIPASS` 指向临时目录，说明 onefile 解包机制已生效
- 但 PyInstaller 已明确给出警告：
  - `Onefile mode in combination with macOS .app bundles ... clashes with macOS security`
  - `This will become an error in v7.0`

## 当前建议
- 如果你要“Finder 看起来只有一个 app”，当前配置已经达到目标。
- 如果你要“长期稳定发布”，应优先回到 onedir `.app`，并分发 zip 后的 `.app`，不要依赖 macOS onefile。
