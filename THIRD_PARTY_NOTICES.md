# 第三方组件与许可

本仓库的原创代码、文档及界面示意图采用 GPL-3.0-only，见 LICENSE。仓库与源码发布 ZIP 不包含 Python、PyQt5、Qt、Codex CLI、OpenAI 客户端或它们的二进制文件；依赖由使用者另行安装。

| 组件 | 用途 | 许可与说明 |
| --- | --- | --- |
| Python | 运行解释器和标准库 | [PSF 许可及所带第三方通知](https://docs.python.org/3/license.html)；实际发行版还可能包含其他组件 |
| PyQt5 | Qt 的 Python 绑定 | [GPLv3 或 Riverbank 商业许可](https://www.riverbankcomputing.com/commercial/pyqt)；普通开源发行使用 GPLv3，本项目按 GPLv3 发布 |
| Qt | 窗口、字体和绘制 | [Qt 开源及商业许可说明](https://www.qt.io/licensing/)，取决于实际版本与模块；不能把所有 Qt 模块一概当作 LGPL |
| Codex 与桌面客户端 | 加载插件、产出会话日志 | 不属于本项目授权范围；须遵守 OpenAI 的相关条款 |
| Windows Script Host | 运行本机启动脚本 | 由 Windows 提供，不随项目分发 |

本项目的 GPL 不替代第三方许可。使用源码不需要向项目作者支付商用许可费。若制作包含 Python/PyQt5/Qt 的二进制产品，须自行随包提供适用版权、许可、对应源码或符合条款的源码提供方式，以及其他适用材料；只复制本项目的 LICENSE 不足以覆盖全部依赖。

PyQt 的商业许可与本项目 GPL 是两个不同授权。前者不自动授予闭源分发本项目衍生代码的权利。本项目没有承诺能够替第三方依赖提供商业授权。

本项目未使用 OpenAI 官方标识。文档中的产品名称仅用于说明兼容环境，不表示隶属、合作或官方认证。
