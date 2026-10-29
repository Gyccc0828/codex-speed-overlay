# Codex Speed Overlay · 本地速度悬浮窗

Windows 上的小型置顶悬浮窗，显示本地 Codex 会话的模型、思考强度、本轮有效吞吐和运行时长。通过本地插件的 `SessionStart` 钩子自动启动，无需 API Key，也不额外调用模型。

![界面效果示例](docs/preview.png)

*图片由实际界面程序渲染，使用示例数据，不代表某个模型的测速成绩。*

```text
gpt-6.1-sol / xhigh             ×
本轮有效吞吐 28.9tokens/s
本轮已完成 03分15秒
```

## 效果与适用范围

- 282 × 90 像素的小窗，浅灰半透明背景、圆角、无边框；三行正文统一字体、字号和颜色。
- 显示当前模型与思考强度；会话运行时计时，完成或中止后停止计时。
- 拖动文字或空白处移动；点击右上角 **×** 关闭，也可右键关闭或按 Esc。
- 同一 Windows 登录会话内只保留一个窗口；跟随日志中**最近开始的一轮主会话**，忽略子代理日志。它不识别当前前台标签页。
- 支持产出本地 `CODEX_HOME/sessions` 日志的 Codex CLI，以及具备本地 Codex 会话支持的桌面版。**不承诺普通云端 ChatGPT 聊天、浏览器版或云端执行的 Work 会话可用。**
- 当前仅支持 Windows。不要将本项目当作 macOS/Linux 通用插件。

插件机制和生命周期钩子来自 [OpenAI 官方插件文档](https://developers.openai.com/plugins/build/plugins) 与 [Hooks 文档](https://learn.chatgpt.com/docs/hooks)。**本项目是第三方自制项目，没有获得 OpenAI 官方认证或背书。**

## 安装

### 1. 准备环境

- Windows，以及可正常运行的本地 Codex 环境。
- Python 3.9 或以上版本，包含 `pythonw.exe`。
- 支持 `codex plugin marketplace add`、`codex plugin add` 和 `/hooks` 的 Codex CLI。可先执行 `codex plugin --help` 检查；安装 Codex CLI 并不自动保证所有桌面版本都支持这些钩子。
- PyQt5。推荐为插件创建独立环境，不修改现有 Python 依赖。

下载本仓库 ZIP 并解压，或执行：

```powershell
git clone https://github.com/Gyccc0828/codex-speed-overlay.git
cd codex-speed-overlay
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\install.ps1 -PythonPath "$PWD\.venv\Scripts\python.exe"
```

没有 `py` 命令时，用你安装的 `python.exe` 完整路径替代。若 Codex 不在 PATH 中，同时指定：

```powershell
.\install.ps1 -PythonPath '你的 python.exe 完整路径' -CodexPath '你的 codex.exe 完整路径'
```

如果 PowerShell 策略禁止运行脚本，请按设备管理策略允许该脚本；安装器不会自行修改系统执行策略。**安装后须保留所选 Python 环境**，包括示例中的 `.venv`；删除或移动它会导致启动失败，需重新安装并记录新路径。

### 2. 审查并允许钩子

在 Codex CLI 中运行 `/hooks`，或打开支持钩子管理的桌面设置，找到本项目的 `SessionStart` 钩子，检查后允许所选项。

安装器不代替你授予信任，也不绕过信任检查。更改钩子定义后，官方机制可能要求重新审查。

### 3. 验证自动启动

开始或恢复一个本地 Codex 会话，再发送消息，观察小窗是否出现、计时是否递增、结束后是否显示“本轮已完成”。

**会话开始/恢复，不等于桌面软件进程启动。** 只打开软件、没有进入本地会话时，小窗不一定出现。手动关闭后，也不会在同一会话的每条消息都自动重开；下一次匹配的会话开始/恢复才会触发启动。

需要手动查看时，可在仓库根目录运行：

```powershell
.\.venv\Scripts\pythonw.exe .\plugins\codex-speed-overlay\app\overlay.pyw
```

## 计算口径与更新时间

```text
本轮有效吞吐 = Σ 已完成模型请求的 output_tokens / Σ 对应的模型响应时段（秒）
```

`output_tokens` 按日志口径包含推理 tokens，不再次加上 reasoning tokens。通过日志中的工具返回与模型输出时间边界估计响应时段，排除可识别的工具执行区间；仍可能包含等待、网络及调度时间。它是**日志估算值**，不是服务端精确解码速度，也不是整轮墙钟时间的倒数。

后台每次读取后约等待 **0.8 秒**，界面每 **0.4 秒**处理新数据，另有文件扫描与读取耗时。token 用量通常在一次模型响应结束后才写入，因此数值按已完成请求更新，长时间思考时可能保持不变。运行时长则覆盖整轮任务，包括工具执行时间。

日志格式属于上游实现细节，未来版本变化可能影响统计。没有样本时显示 `--tokens/s`。多会话并行时跟随最近开始的一轮，不能保证与当前正在看的标签页一致。

## 运行方式与隐私

```text
本地会话开始 / 恢复
  → 已获信任的 SessionStart 钩子（异步，超时 3 秒）
  → Windows Script Host 启动 pythonw 后立即返回
  → 独立 PyQt5 悬浮窗只读本机 sessions/*.jsonl
```

悬浮窗和启动脚本不联网，不上传聊天内容，不读取 `auth.json`、API Key 或账号令牌。日志解析会接触本地会话文件，其中可能包含聊天内容；数据仅在本机处理，不另存副本。安装器会调用 Codex CLI 注册本地插件，依赖安装和 Codex 自身可能访问网络。

安装位置为 Windows 当前账号的 `LocalApplicationData/CodexSpeedOverlay/marketplace`（部分桌面打包环境会重定向实际目录）。`runtime-path.txt` 仅记录该主机的 `pythonw.exe` 路径，不加入仓库或发布 ZIP。

GUI 在独立进程运行，后台钩子立即返回；缺少启动文件或运行环境时安静退出。此设计降低对聊天启动的影响，**不保证零故障**。没有 Windows 登录启动项，不修改 ChatGPT/Codex 程序文件，也不依赖 `debug-codex-requests` skill。

## 跨主机、更新和停用

- **另一台 Windows 主机：** 下载本仓库，重新准备 Python/PyQt5 和 Codex，运行安装器，再由该主机用户审查允许钩子。无需复制登录凭据、会话日志或整份 `.codex`。
- **更新：** 关闭旧悬浮窗，更新代码后重新运行安装器；确认插件管理中为新版本。若钩子要求重新审查，检查后再次允许。发布版更改了单实例名称，首次从私人旧版迁移时尤其应先关闭旧窗。
- **停用：** 在插件管理中禁用本插件或钩子，关闭已打开的小窗。禁用不会主动结束已有的悬浮窗进程。
- **卸载：** 执行 `codex plugin remove codex-speed-overlay@speed-overlay-local`。安装目录和 Python 环境可在关闭程序后按需手动清理；卸载器不删除聊天日志或 Python 环境。

没有弹窗时，依次检查钩子是否允许、是否为本地会话、Python 环境是否仍存在，以及 PyQt5 是否安装在同一个环境中。可用 `python.exe` 代替手动启动命令中的 `pythonw.exe` 查看异常信息；不要公开粘贴含聊天内容的完整日志。

## 开源、分发与商用

本项目采用 **GNU GPL v3.0 only（GPL-3.0-only）**，完整条款见 [LICENSE](LICENSE)。下面是使用说明，许可正文优先。

| 场景 | 原则 |
| --- | --- |
| 个人、研究或企业内部使用 | 允许，包括营利用途；仅使用、不向外分发，不要求公开你自己的内部修改 |
| Fork、修改、免费分享 | 允许；分发本项目或其衍生作品时保留版权与许可，标明修改，并按 GPLv3 向接收者提供相应源码 |
| 收费分发、售卖安装或支持服务 | 允许；收费不免除 GPLv3 的源码和接收者权利要求 |
| 分发 exe 或安装包 | 需同时满足 GPLv3 相应源码提供方式，并遵守所有随包第三方组件的许可；不能只发布二进制却不给合规源码途径 |
| 把本项目衍生版本闭源分发 | 本仓库的 GPLv3 不授予这种许可；不能通过附加协议剥夺接收者的 GPL 权利 |

开源不等于禁止商用，也不等于放弃版权。这里没有“商用须另付费”或“禁止转售”的附加限制。GPLv3 不授予 OpenAI、ChatGPT、Codex、Qt 等名称或标识的商标使用权，也不替代相关服务的使用条款。项目按许可约定不提供担保。

**PyQt5 是选择 GPLv3 的重要原因。** Riverbank 说明其免费版本采用 GPLv3，与 GPL 不兼容的用途需要商业许可；购买 PyQt 商业许可也不会自动改变本项目源码的 GPLv3 授权。Python、PyQt5 和 Qt 不随本仓库打包；如果自行打包这些组件，须另外核对实际版本、模块及其分发义务。详见 [第三方依赖说明](THIRD_PARTY_NOTICES.md)。

参考：[GPLv3 正文](https://www.gnu.org/licenses/gpl-3.0.html)、[GNU 许可 FAQ](https://www.gnu.org/licenses/gpl-faq.html)、[Riverbank 许可说明](https://www.riverbankcomputing.com/commercial/pyqt)。

## 开发与验证

```powershell
python -m unittest discover -s tests -v
```

测试使用合成日志，不需要真实账号、网络或聊天记录。覆盖统计去重、推理 token 口径、工具时段排除、任务重置、截断日志、子代理过滤和启动器失败退出。GUI 测试在 Windows 上检查颜色、字号、关闭按钮及计时器停止。

本机曾验证会话钩子自动启动和界面运行；不代表已覆盖其他 Windows 主机、所有桌面版本、所有 Python/PyQt5 版本或不同 DPI 配置。提交改动时请描述行为变化和验证方式；贡献内容按本项目相同许可提供。

```text
.agents/plugins/marketplace.json        本地 marketplace
plugins/codex-speed-overlay/
  .codex-plugin/plugin.json             插件清单
  hooks/hooks.json                     异步 SessionStart 定义
  scripts/start-overlay.vbs            独立窗口启动器
  app/overlay.pyw                      PyQt5 界面
  app/meter.py                         只读日志统计
install.ps1                           本机安装器
tests/                                合成数据与界面检查
```
