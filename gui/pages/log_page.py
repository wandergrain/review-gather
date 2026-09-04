

from collections import deque
from datetime import datetime

from PySide6.QtWidgets import (
    QFileDialog, QFrame, QHBoxLayout, QLabel, QTextEdit, QVBoxLayout,
)

from gui.widgets import make_button

_MAX_LINES = 2000

class LogPage(QFrame):
    def __init__(self, get_config, parent=None):
        super().__init__(parent)
        self.get_config = get_config
        self._lines = deque(maxlen=_MAX_LINES)

        self.setProperty("panel", "1")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(14)

        title = QLabel("运行日记")
        title.setProperty("role", "headline")
        layout.addWidget(title)
        subtitle = QLabel("爬取进度、关键步骤与异常提示，同步更新")
        subtitle.setProperty("role", "subtitle")
        layout.addWidget(subtitle)

        toolbar = QHBoxLayout()
        toolbar.setSpacing(10)
        self.count_label = QLabel("0 行")
        self.count_label.setProperty("role", "desc")
        toolbar.addWidget(self.count_label)
        toolbar.addStretch()

        self.btn_clear = make_button("清空日志", "ghost")
        self.btn_clear.clicked.connect(self.clear_log)
        toolbar.addWidget(self.btn_clear)
        self.btn_export = make_button("导出日志", "secondary")
        self.btn_export.clicked.connect(self.export_log)
        toolbar.addWidget(self.btn_export)
        layout.addLayout(toolbar)

        self.textbox = QTextEdit()
        self.textbox.setReadOnly(True)
        self.textbox.setProperty("log", "1")
        self.textbox.setAcceptRichText(False)
        layout.addWidget(self.textbox, 1)

    def append_log(self, msg: str):
        cfg = self.get_config()
        max_lines = int(cfg.get("log_line_limit", 500) or 500)
        show_ts = bool(cfg.get("log_timestamp", True))

        text = str(msg)
        if show_ts:
            text = f"[{datetime.now().strftime('%H:%M:%S')}] {text}"
        self._lines.append(text)
        while len(self._lines) > max_lines:
            self._lines.popleft()

        self.textbox.setPlainText("\n".join(self._lines))
        self.count_label.setText(f"{len(self._lines)} 行")
        if bool(cfg.get("auto_scroll_log", True)):
            scrollbar = self.textbox.verticalScrollBar()
            scrollbar.setValue(scrollbar.maximum())

    def clear_log(self):
        self._lines.clear()
        self.textbox.clear()
        self.count_label.setText("0 行")

    def export_log(self):
        if not self._lines:
            return
        default_name = f"运行日志_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        path, _ = QFileDialog.getSaveFileName(self, "导出日志", default_name, "文本文件 (*.txt)")
        if not path:
            return
        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write("\n".join(self._lines))
            self.append_log(f"[日志] 已导出到 {path}")
        except Exception as exc:
            self.append_log(f"[日志] 导出失败: {exc}")

    def lines(self):
        return list(self._lines)