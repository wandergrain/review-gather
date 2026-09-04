from PySide6.QtCore import QUrl, Qt
from PySide6.QtGui import QDesktopServices, QFont
from PySide6.QtWidgets import (
    QDialog, QFrame, QHBoxLayout, QLabel, QScrollArea,
    QVBoxLayout, QWidget,
)

from gui.widgets import make_button

APP_NAME = "拾评"
APP_VERSION = "1.0.0"
AUTHOR = "wandergrain"
GITHUB_URL = "https://github.com/wandergrain/review-gather"

_USER_AGREEMENT = [
    ("一、使用范围",
     "本程序为 Steam 评测数据抓取工具，仅用于个人学习、研究与数据分析！"
     "请勿将抓取数据用于商业牟利、批量传播或任何违反 Steam 用户协议的行为！"),
    ("二、实现方式",
     "程序通过 Steam 官方公开接口获取评测数据，"
     "不修改任何游戏文件、不注入进程、不影响游戏正常运行，"
     "请求频率与重试策略均可配置，默认节奏温和。"),
    ("三、风险说明",
     "请合理控制请求频率，过快的并发请求可能触发 Steam 限流（429）或临时封禁 IP，"
     "由此产生的任何账号限制或网络异常，由使用者自行承担！"),
    ("四、隐私声明",
     "程序不会上传任何数据到第三方服务器，"
     "仅在你主动填写并用于昵称获取的 API Key 会随请求发送至 Steam 官方接口，"
     "API Key 仅保存在本机配置文件中。"),
    ("五、数据用途",
     "导出数据（CSV / TXT）归使用者所有，可用于个人分析、学习展示等正当用途！"
     "请遵守当地法律法规与 Steam 服务条款，勿用于刷量、爬取再分发等违规场景！"),
]


def _agreement_sections():
    return list(_USER_AGREEMENT)


class AgreementDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("用户协议")
        self.setModal(True)
        self.setMinimumSize(620, 520)

        root = QVBoxLayout(self)
        root.setContentsMargins(28, 24, 28, 20)
        root.setSpacing(6)

        title = QLabel("用户协议")
        title.setProperty("role", "headline")
        title.setFont(QFont("Microsoft YaHei UI", 20, QFont.Bold))
        root.addWidget(title)
        subtitle = QLabel("查看程序使用范围、实现方式与风险提示")
        subtitle.setProperty("role", "subtitle")
        root.addWidget(subtitle)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        body = QWidget()
        L = QVBoxLayout(body)
        L.setContentsMargins(4, 8, 8, 8)
        L.setSpacing(14)
        for heading, text in _agreement_sections():
            sec = QLabel(heading)
            sec.setProperty("role", "section")
            sec.setWordWrap(True)
            L.addWidget(sec)
            par = QLabel(text)
            par.setProperty("role", "desc")
            par.setWordWrap(True)
            par.setTextInteractionFlags(Qt.TextSelectableByMouse)
            L.addWidget(par)
        scroll.setWidget(body)
        root.addWidget(scroll, 1)

        foot = QHBoxLayout()
        foot.addStretch()
        btn_close = make_button("已阅读，关闭", "primary")
        btn_close.setMinimumWidth(140)
        btn_close.clicked.connect(self.accept)
        foot.addWidget(btn_close)
        root.addLayout(foot)


class AboutPage(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setProperty("panel", "1")
        root = QVBoxLayout(self)
        root.setContentsMargins(20, 16, 20, 16)
        root.setSpacing(12)

        title = QLabel("关于此程序")
        title.setProperty("role", "headline")
        root.addWidget(title)
        subtitle = QLabel("详细了解本程序的用途、实现方式与使用协议")
        subtitle.setProperty("role", "subtitle")
        root.addWidget(subtitle)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        body = QWidget()
        L = QVBoxLayout(body)
        L.setContentsMargins(2, 0, 8, 0)
        L.setSpacing(10)
        scroll.setWidget(body)
        root.addWidget(scroll, 1)

        self._section(L, "程序介绍")
        self._desc(L, f"{APP_NAME} v{APP_VERSION} 是一款基于 Steam 官方公开接口的评测批量抓取工具，"
                      "它可以在你无需会编写代码的情况下，快速获取任意 Steam 游戏的用户评测数据，"
                      "支持按语言、好评/差评、购买来源、游戏时长等多个维度筛选，"
                      "并自动统计对比官方评测总数，一键导出 CSV / TXT 报告，方便二次分析。")

        self._section(L, "主要功能")
        for line in [
            "多语言抓取：11 种常用语言 + 全部语言",
            "多维度筛选：好评/差评、购买来源、最短游戏时长",
            "实时进度：原始数 → 有效数 → 好评数，含耗时统计",
            "官方对比：自动拉取官方总数，计算抓取完整率",
            "昵称富化：可选 Steam Web API Key，将 SteamID 换成昵称",
            "报告导出：CSV（UTF-8-SIG，Excel 直接打开）/ TXT",
            "界面个性化：深浅主题、强调色、背景图片毛玻璃",
        ]:
            self._desc(L, "· " + line, indent=True)

        self._section(L, "使用流程")
        for line in [
            "1. 在「爬取数据」页输入游戏 ID (AppID)，点击「查看游戏信息」",
            "2. 选择语言、评测类型、购买来源与时长过滤等参数",
            "3. 点击「开始爬取」，底部进度与摘要实时刷新",
            "4. 完成后自动导出 CSV / TXT 到指定目录（默认程序目录）",
        ]:
            self._desc(L, line, indent=True)

        self._section(L, "代码构成")
        self._desc(L, "程序采用模块化结构，代码清晰易维护：")
        for line in [
            "main.py              程序入口，启动 GUI",
            "core/scraper.py      爬虫核心：请求、翻页、统计、导出",
            "gui/theme.py         主题系统：预设背景色、强调色、全局样式",
            "gui/widgets.py       可复用组件：卡片、导航、下拉框、统计卡",
            "gui/app.py           主窗口：标题栏、侧边栏、页面堆叠",
            "gui/pages/           各功能区页面",
        ]:
            self._desc(L, line, indent=True)

        self._section(L, "所用技术")
        for line in [
            "Python 3 + PySide6 (Qt)：图形界面",
            "requests：访问 Steam 官方接口",
            "pandas：数据整理与 CSV 导出",
            "ThreadPoolExecutor：并行获取游戏信息",
        ]:
            self._desc(L, "· " + line, indent=True)

        self._section(L, "作者与项目")
        author_row = QHBoxLayout()
        author_row.setSpacing(10)
        author_label = QLabel(f"作者：{AUTHOR}")
        author_label.setProperty("role", "desc")
        author_label.setStyleSheet("font-size: 13px; font-weight: 700;")
        author_row.addWidget(author_label)
        author_row.addStretch()
        github_btn = make_button("打开 GitHub", "secondary")
        github_btn.clicked.connect(lambda: QDesktopServices.openUrl(QUrl(GITHUB_URL)))
        author_row.addWidget(github_btn)
        L.addLayout(author_row)
        url_label = QLabel(GITHUB_URL)
        url_label.setProperty("role", "desc")
        url_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        L.addWidget(url_label)

        self._section(L, "用户协议")
        self._desc(L, "使用本程序即表示同意以下条款！")
        agree_btn = make_button("查看用户协议", "secondary")
        agree_btn.clicked.connect(self._show_agreement)
        ag_row = QHBoxLayout()
        ag_row.addStretch()
        ag_row.addWidget(agree_btn)
        L.addLayout(ag_row)

        L.addStretch()

    def _show_agreement(self):
        dlg = AgreementDialog(self.window())
        dlg.exec()

    @staticmethod
    def _section(layout, text):
        label = QLabel(text)
        label.setProperty("role", "section")
        label.setContentsMargins(0, 6, 0, 0)
        layout.addWidget(label)

    @staticmethod
    def _desc(layout, text, indent=False):
        label = QLabel(text)
        label.setProperty("role", "desc")
        label.setWordWrap(True)
        label.setStyleSheet("line-height: 1.7;" if not indent else "padding-left: 14px; line-height: 1.7;")
        layout.addWidget(label)