

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QColorDialog, QFrame, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QScrollArea, QVBoxLayout, QWidget,
)

from core.scraper import ScraperConfig
from gui.theme import (
    CUSTOM_ACCENT_FLAG, DEFAULT_DARK, accent_names,
    get_preset, is_hex_color, preset_accent_token, preset_names,
)
from gui.widgets import (
    Card, build_choice_block, build_slider_block, make_button,
)

class _SettingsPanel(QFrame):

    def __init__(self, engine, on_save, title, subtitle, parent=None):
        super().__init__(parent)
        self.engine = engine
        self.on_save = on_save
        self._widgets = {}
        self._dirty = False

        self.setProperty("panel", "1")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(10)

        title_label = QLabel(title)
        title_label.setProperty("role", "headline")
        layout.addWidget(title_label)
        sub_label = QLabel(subtitle)
        sub_label.setProperty("role", "subtitle")
        layout.addWidget(sub_label)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        content = QWidget()
        self.content_layout = QVBoxLayout(content)
        self.content_layout.setContentsMargins(0, 0, 6, 0)
        self.content_layout.setSpacing(10)
        scroll.setWidget(content)
        layout.addWidget(scroll, 1)

        action_bar = QFrame()
        action_bar.setProperty("card", "2")
        bar = QHBoxLayout(action_bar)
        bar.setContentsMargins(14, 10, 14, 10)
        bar.setSpacing(10)
        self.status_label = QLabel("当前设置已保存")
        self.status_label.setProperty("role", "desc")
        bar.addWidget(self.status_label, 1)
        self.btn_reset = make_button("恢复推荐值", "secondary")
        self.btn_reset.clicked.connect(self._restore_defaults)
        bar.addWidget(self.btn_reset)
        self.btn_save = make_button("保存并应用", "primary")
        self.btn_save.setEnabled(False)
        self.btn_save.clicked.connect(self._save)
        bar.addWidget(self.btn_save)
        layout.addWidget(action_bar)

        self._build()
        self._mark_dirty(False)

    def _build(self):
        raise NotImplementedError

    def _add_slider(self, key, title, note, minimum, maximum, on_change=None, **kwargs):
        handler = on_change or self._on_change
        self._widgets[key] = build_slider_block(
            self.content_layout, title, note, getattr(self.engine.config, key),
            minimum, maximum, key, handler, **kwargs)

    def _add_choice(self, key, title, note, options, current, on_change=None):
        handler = on_change or self._on_change
        self._widgets[key] = build_choice_block(
            self.content_layout, title, note, options, current, key, handler)

    def _on_change(self, key, value):
        setattr(self.engine.config, key, value)
        self._mark_dirty(True)

    def _mark_dirty(self, dirty):
        self._dirty = bool(dirty)
        self.btn_save.setEnabled(self._dirty)
        if dirty:
            self.status_label.setText("有未保存的更改")
            self.status_label.setProperty("role", "status-run")
        else:
            self.status_label.setText("当前设置已保存")
            self.status_label.setProperty("role", "desc")
        self.status_label.style().unpolish(self.status_label)
        self.status_label.style().polish(self.status_label)

    def _restore_defaults(self):
        defaults = ScraperConfig()
        for key, info in self._widgets.items():
            default = getattr(defaults, key, None)
            if info["type"] == "slider":
                slider = info["widget"]
                try:
                    sv = int(round(float(default) / float(info["value_scale"])))
                except (TypeError, ValueError, ZeroDivisionError):
                    continue
                slider.setValue(max(slider.minimum(), min(slider.maximum(), sv)))
            elif info["type"] == "choice":
                if default in info["values"]:
                    info["widget"].setCurrentIndex(info["values"].index(default))
        self._mark_dirty(True)

    def _save(self):
        self.on_save()
        self._mark_dirty(False)

    def reload(self):

        for key, info in self._widgets.items():
            value = getattr(self.engine.config, key, None)
            if info["type"] == "slider":
                try:
                    sv = int(round(float(value) / float(info["value_scale"])))
                except (TypeError, ValueError, ZeroDivisionError):
                    continue
                info["widget"].setValue(sv)
            elif info["type"] == "choice":
                if value in info["values"]:
                    info["widget"].setCurrentIndex(info["values"].index(value))
        self._mark_dirty(False)

class ColorTunerCard(Card):

    def __init__(self, title, desc, on_apply, on_reset, parent=None):
        super().__init__(title, desc, parent)
        self.on_apply = on_apply
        self.on_reset = on_reset
        self._debounce = QTimer(self)
        self._debounce.setSingleShot(True)
        self._debounce.setInterval(180)
        self._debounce.timeout.connect(self._flush)

        row = QHBoxLayout()
        row.setSpacing(8)
        self.swatch_btn = QPushButton()
        self.swatch_btn.setFixedSize(58, 34)
        self.swatch_btn.setCursor(Qt.PointingHandCursor)
        self.swatch_btn.setFocusPolicy(Qt.NoFocus)
        self.swatch_btn.setToolTip("点击打开颜色选择器")
        self.swatch_btn.clicked.connect(self._pick_color)
        row.addWidget(self.swatch_btn)

        self.hex_edit = QLineEdit()
        self.hex_edit.setProperty("field", "1")
        self.hex_edit.setFixedWidth(118)
        self.hex_edit.setMaxLength(7)
        self.hex_edit.setPlaceholderText("#RRGGBB")
        self.hex_edit.setToolTip("输入 #RRGGBB 十六进制颜色，输入即实时预览")
        self.hex_edit.textEdited.connect(lambda _t: self._debounce.start())
        self.hex_edit.editingFinished.connect(self._flush)
        row.addWidget(self.hex_edit)

        btn_pick = make_button("选色", "secondary")
        btn_pick.clicked.connect(self._pick_color)
        row.addWidget(btn_pick)
        btn_reset = make_button("恢复预设", "ghost")
        btn_reset.clicked.connect(self._on_reset_clicked)
        row.addWidget(btn_reset)
        row.addStretch()
        self.add_layout(row)

        self.set_color("#2DD4BF")

    def color(self) -> str:
        return self.hex_edit.text().strip()

    def set_color(self, hex_color: str):
        c = hex_color.upper() if is_hex_color(hex_color) else "#2DD4BF"
        self.hex_edit.setText(c)
        self._paint_swatch(c)

    def set_active(self, on: bool):
        self.setEnabled(bool(on))

    def _paint_swatch(self, color: str):
        self.swatch_btn.setStyleSheet(
            f"background: {color}; border: 1px solid rgba(0, 0, 0, 0.22); border-radius: 9px;")

    def _flush(self):
        h = self.color()
        if not is_hex_color(h):
            return
        self._paint_swatch(h.upper())
        if self.on_apply:
            self.on_apply(h.upper())

    def _pick_color(self):
        cur = QColor(self.color()) if is_hex_color(self.color()) else QColor("#2DD4BF")
        color = QColorDialog.getColor(cur, self, "选择颜色")
        if color.isValid():
            self.hex_edit.setText(color.name().upper())
            self._flush()

    def _on_reset_clicked(self):
        if self.on_reset:
            self.on_reset()

class NetworkPage(_SettingsPanel):
    def __init__(self, engine, on_save, parent=None):
        super().__init__(
            engine, on_save, "网络与请求",
            "调整请求超时、重试与翻页节奏，保存后立即生效",
            parent,
        )

    def _build(self):
        L = self.content_layout
        self._add_slider("timeout", "请求超时（秒）",
                         "调整单次 HTTP 请求超时时间",
                         1, 30, display_suffix=" 秒")
        self._add_slider("retries", "失败重试次数",
                         "调整请求失败最大重试次数",
                         0, 5, display_suffix=" 次")
        self._add_slider("backoff", "重试间隔系数（秒）",
                         "调整重试等待基础间隔",
                         1, 20, value_scale=0.1, display_suffix=" s", display_decimals=1)
        self._add_slider("page_size", "每页评测数量",
                         "调整单次请求抓取条数",
                         10, 100, display_suffix=" 条")
        self._add_slider("base_sleep", "翻页基础等待（秒）",
                         "调整翻页间隔，控制请求频率",
                         1, 20, value_scale=0.05, display_suffix=" s", display_decimals=2)
        self._add_slider("jitter", "随机抖动（秒）",
                         "调整叠加随机波动，节奏更自然",
                         1, 20, value_scale=0.01, display_suffix=" s", display_decimals=2)
        self._add_slider("game_name_timeout", "游戏信息请求超时（秒）",
                         "获取游戏名称的单请求超时",
                         1, 15, display_suffix=" 秒")
        self._add_slider("game_name_worker_timeout", "游戏信息线程超时（秒）",
                         "游戏名称并行请求的整体上限",
                         1, 20, display_suffix=" 秒")
        L.addStretch()

class InterfacePage(_SettingsPanel):
    def __init__(self, engine, on_save, on_theme_change, on_accent_change,
                 on_pick_bg, on_clear_bg, on_bg_change,
                 current_theme=DEFAULT_DARK, parent=None):
        self.on_theme_change = on_theme_change
        self.on_accent_change = on_accent_change
        self.on_pick_bg = on_pick_bg
        self.on_clear_bg = on_clear_bg
        self.on_bg_change = on_bg_change
        self.current_theme = current_theme
        self._theme_kind = get_preset(current_theme).kind
        super().__init__(
            engine, on_save, "界面与日志",
            "选择配色、背景图片，调整日志显示方式与跳转行为",
            parent,
        )
        self._bg_timer = QTimer(self)
        self._bg_timer.setSingleShot(True)
        self._bg_timer.setInterval(160)
        self._bg_timer.timeout.connect(self._flush_bg)

    def _build(self):
        L = self.content_layout
        self._add_choice(
            "theme", "背景颜色",
            "窗口整体配色预设，切换后立即生效",
            [(name, name) for name in preset_names()],
            self.current_theme,
            on_change=self._on_theme_change,
        )
        accent_options = [(name, name) for name in accent_names()] + [
            (CUSTOM_ACCENT_FLAG, CUSTOM_ACCENT_FLAG + "（手动调色）")]
        self._add_choice(
            "accent_color", "强调色",
            "按钮、选中态等元素的强调色",
            accent_options,
            self.engine.config.accent_color,
            on_change=self._on_accent_change,
        )
        self.accent_tuner = ColorTunerCard(
            "自定义强调色",
            "输入 #RRGGBB 或点击色块取色，实时预览",
            on_apply=self._on_accent_custom,
            on_reset=self._on_accent_reset,
        )
        self._sync_accent_tuner(self.engine.config.accent_color)
        L.addWidget(self.accent_tuner)

        bg_card = Card("自定义背景图片",
                       "作为窗口背景，通过卡片透明控制透出程度，清除后恢复预设配色")
        bg_row = QHBoxLayout()
        bg_row.setSpacing(8)
        self.bg_path_label = QLabel(self.engine.config.bg_image or "未设置图片")
        self.bg_path_label.setProperty("role", "desc")
        self.bg_path_label.setWordWrap(True)
        bg_row.addWidget(self.bg_path_label, 1)
        btn_pick = make_button("选择图片", "secondary")
        btn_pick.clicked.connect(self.on_pick_bg)
        bg_row.addWidget(btn_pick)
        btn_clear = make_button("清除", "ghost")
        btn_clear.clicked.connect(self.on_clear_bg)
        bg_row.addWidget(btn_clear)
        bg_card.add_layout(bg_row)
        L.addWidget(bg_card)

        self._add_slider(
            "card_transparency", "卡片透明百分比%",
            "卡片透出背景图片的程度，文字自动加投影保持可读",
            0, 100, display_suffix="%", on_change=self._on_bg_slider)
        self._add_slider(
            "bg_blur", "背景模糊（像素）",
            "背景图片模糊程度，0 为不模糊",
            0, 60, display_suffix=" px", on_change=self._on_bg_slider)

        self._add_slider("log_line_limit", "日志最大行数",
                         "运行日记最大保留行数，超出自动丢弃最旧记录",
                         100, 2000, display_suffix=" 行")
        self._add_choice("auto_scroll_log", "日志自动滚动",
                         "新日志出现时自动滚动到底部",
                         [(True, "开启"), (False, "关闭")],
                         bool(self.engine.config.auto_scroll_log))
        self._add_choice("log_timestamp", "日志显示时间戳",
                         "每条日志前显示 [时:分:秒]",
                         [(True, "开启"), (False, "关闭")],
                         bool(self.engine.config.log_timestamp))
        self._add_choice("auto_switch_to_log", "爬取完成自动跳转日志",
                         "爬取结束后自动切换到运行日记页",
                         [(True, "开启"), (False, "关闭")],
                         bool(self.engine.config.auto_switch_to_log))
        L.addStretch()

    def _sync_accent_tuner(self, accent):
        custom = is_hex_color(accent)
        self.accent_tuner.set_active(custom)
        self.accent_tuner.set_color(
            accent if custom else preset_accent_token(accent if accent else "青绿", self._theme_kind))

    def _on_accent_custom(self, hex_color):
        self.engine.config.accent_color = hex_color
        if self.on_accent_change:
            self.on_accent_change(hex_color)

    def _on_accent_reset(self):
        values = self._widgets["accent_color"]["values"]
        if values and values[0] != CUSTOM_ACCENT_FLAG:
            self._widgets["accent_color"]["widget"].setCurrentIndex(0)

    def _on_theme_change(self, key, name):
        if self.on_theme_change:
            self.on_theme_change(name)

    def _on_accent_change(self, key, name):
        if name == CUSTOM_ACCENT_FLAG:
            self.accent_tuner.set_active(True)
            if not is_hex_color(self.engine.config.accent_color):
                self.accent_tuner.set_color(preset_accent_token("青绿", self._theme_kind))
            else:
                self.accent_tuner.set_color(self.engine.config.accent_color)
        else:
            self._sync_accent_tuner(name)
            if self.on_accent_change:
                self.on_accent_change(name)

    def _on_bg_slider(self, key, value):
        setattr(self.engine.config, key, value)
        self._mark_dirty(True)
        self._bg_timer.start()

    def _flush_bg(self):
        if self.on_bg_change:
            self.on_bg_change()

    def sync_theme(self, name):
        self._theme_kind = get_preset(name).kind
        info = self._widgets.get("theme")
        if info and name in info["values"]:
            combo = info["widget"]
            blocked = combo.blockSignals(True)
            combo.setCurrentIndex(info["values"].index(name))
            combo.blockSignals(blocked)
        self._sync_accent_tuner(self.engine.config.accent_color)

    def sync_accent(self, name):
        info = self._widgets.get("accent_color")
        if info is None:
            return
        values = info["values"]
        combo = info["widget"]
        index = values.index(name) if name in values else \
            (values.index(CUSTOM_ACCENT_FLAG) if CUSTOM_ACCENT_FLAG in values else 0)
        blocked = combo.blockSignals(True)
        combo.setCurrentIndex(index)
        combo.blockSignals(blocked)
        self._sync_accent_tuner(name)

    def refresh_bg_path(self):
        if hasattr(self, "bg_path_label"):
            self.bg_path_label.setText(self.engine.config.bg_image or "未设置图片")

    def _restore_defaults(self):
        super()._restore_defaults()
        self._sync_accent_tuner("青绿")