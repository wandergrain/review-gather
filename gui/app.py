

import ctypes
import json
import os
import sys

from PySide6.QtCore import QEvent, QPoint, QRect, QRectF, Qt, QTimer
from PySide6.QtGui import QColor, QPainter, QPainterPath, QPixmap
from PySide6.QtWidgets import (
    QApplication, QFileDialog, QFrame, QGraphicsBlurEffect, QGraphicsDropShadowEffect,
    QGraphicsScene, QGraphicsPixmapItem, QHBoxLayout, QLabel, QMainWindow,
    QStackedWidget, QVBoxLayout, QWidget,
)

from core.scraper import ScraperConfig, ScraperEngine
from gui.theme import (
    DEFAULT_ALT, DEFAULT_DARK, PRESETS, apply_accent,
    brighten_text, build_stylesheet, dim_accent, get_preset, glass_theme,
    is_valid_accent,
)
from gui.widgets import (
    NavButton, TitleButton, TitleButtonGroup, make_button,
)
from gui.pages.scrape_page import ScrapePage, FuncWorker
from gui.pages.log_page import LogPage
from gui.pages.settings_page import NetworkPage, InterfacePage
from gui.pages.about_page import APP_NAME, APP_VERSION, AUTHOR, GITHUB_URL, AboutPage

if getattr(sys, "frozen", False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_PATH = os.path.join(BASE_DIR, "config.json")

NAV_ITEMS = [
    (0, "爬取数据"),
    (1, "运行日记"),
    (2, "网络与请求"),
    (3, "界面与日志"),
    (4, "关于此程序"),
]

class BackdropWidget(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)
        self._pixmap = None
        self._radius = 30
        self.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        self.setAttribute(Qt.WA_StyledBackground, False)

    def set_corner_radius(self, radius):
        self._radius = int(radius)
        self.update()

    def set_image(self, path, blur=0):
        try:
            src = QPixmap(path)
            pix = src
            if blur and blur > 0:
                scene = QGraphicsScene()
                item = QGraphicsPixmapItem(src)
                item.setGraphicsEffect(QGraphicsBlurEffect())
                item.graphicsEffect().setBlurRadius(int(blur))
                scene.addItem(item)
                target = QPixmap(src.size())
                target.fill(Qt.transparent)
                painter = QPainter(target)
                scene.render(painter)
                painter.end()
                pix = target
            self._pixmap = None if src.isNull() else pix
        except Exception:
            self._pixmap = None
        self.update()

    def clear_image(self):
        self._pixmap = None
        self.update()

    def paintEvent(self, _event):
        if self._pixmap is None:
            return
        painter = QPainter(self)
        painter.setRenderHint(QPainter.SmoothPixmapTransform)
        path = QPainterPath()
        path.addRoundedRect(QRectF(self.rect()), self._radius, self._radius)
        painter.setClipPath(path)
        rect = self.rect()
        scaled = self._pixmap.scaled(
            rect.size(), Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
        painter.drawPixmap((rect.width() - scaled.width()) // 2,
                           (rect.height() - scaled.height()) // 2, scaled)
        painter.end()

class TitleBar(QFrame):

    def __init__(self, window, parent=None):
        super().__init__(parent)
        self.window_ref = window
        self.drag_pos = QPoint()
        self.dragging = False
        self.setProperty("titlebar", "1")
        self.setFixedHeight(52)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 8, 10, 8)
        layout.setSpacing(8)

        brand = QHBoxLayout()
        brand.setSpacing(8)
        self.title_text = QLabel(APP_NAME)
        self.title_text.setStyleSheet("background: transparent; border: none; font-size: 14px; font-weight: 800;")
        brand.addWidget(self.title_text)
        self.version_tag = QLabel(f"v{APP_VERSION}")
        self.version_tag.setAlignment(Qt.AlignCenter)
        self.version_tag.setObjectName("versionTag")
        brand.addWidget(self.version_tag)
        layout.addLayout(brand)
        layout.addStretch()

        self.btn_group = TitleButtonGroup()
        buttons = [
            ("about", "关于此程序", lambda: window.switch_page(4)),
            ("theme", "切换深浅色主题", window.toggle_theme),
            ("min", "最小化", window.showMinimized),
            ("max", "最大化 / 还原", window.toggle_maximize_restore),
            ("close", "关闭", window.close),
        ]
        for kind, tip, slot in buttons:
            btn = TitleButton(kind)
            btn.setToolTip(tip)
            btn.clicked.connect(slot)
            setattr(self, f"btn_{kind}", btn)
            self.btn_group.add_button(btn)
        layout.addWidget(self.btn_group)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton and not self.window_ref.isMaximized():
            self.dragging = True
            self.drag_pos = event.globalPosition().toPoint() - self.window_ref.frameGeometry().topLeft()
            event.accept()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self.dragging and not self.window_ref.isMaximized():
            self.window_ref.move(event.globalPosition().toPoint() - self.drag_pos)
            event.accept()
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        self.dragging = False
        super().mouseReleaseEvent(event)

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.window_ref.toggle_maximize_restore()
        super().mouseDoubleClickEvent(event)

    def sync_state(self):
        self.btn_max.set_kind("restore" if self.window_ref.isMaximized() else "max")

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"{APP_NAME} v{APP_VERSION}")
        self.resize(1280, 820)
        self.setMinimumSize(1100, 700)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Window)
        self.setAttribute(Qt.WA_TranslucentBackground, True)

        self.engine = ScraperEngine()
        self.load_config()
        self.base_preset = self.engine.config.__dict__.get("_theme", DEFAULT_DARK)
        self.theme = apply_accent(get_preset(self.base_preset), self.engine.config.accent_color)

        self._build_ui()
        self.apply_theme(self.base_preset)
        self.refresh_backdrop()

    def apply_theme(self, name):
        self.base_preset = name
        self.engine.config._theme = name
        self._rebuild_theme()

    def _rebuild_theme(self):
        theme = apply_accent(get_preset(self.base_preset), self.engine.config.accent_color)
        self.theme = theme
        custom_bg_active = bool(self.engine.config.bg_image and os.path.exists(self.engine.config.bg_image))
        if custom_bg_active:
            alpha = max(0.08, 1.0 - self.engine.config.card_transparency / 100.0)
            theme = glass_theme(theme, alpha)
            theme = dim_accent(theme, (self.engine.config.card_transparency / 100.0) * 0.35)
            theme = brighten_text(theme)
        app = QApplication.instance()
        if app is not None:
            app.setStyleSheet(build_stylesheet(theme))
        self.title_bar.btn_theme.set_icon_color(self.theme.text_dim)
        self._style_title_text()
        self._set_text_shadow(custom_bg_active)

        try:
            from gui.widgets import FieldComboBox
            for combo in self.findChildren(FieldComboBox):
                combo.set_arrow_color(self.theme.text_dim)
            if hasattr(self, "page_interface"):
                self.page_interface.sync_theme(self.base_preset)
                self.page_interface.sync_accent(self.engine.config.accent_color)
        except Exception:
            pass

    def _set_text_shadow(self, enabled):

        if enabled == getattr(self, "_shadow_enabled", False):
            return
        self._shadow_enabled = enabled
        for label in self.findChildren(QLabel):
            if enabled:
                if not label.text():
                    continue
                effect = QGraphicsDropShadowEffect(label)
                effect.setBlurRadius(4)
                effect.setOffset(1, 1)
                effect.setColor(QColor(0, 0, 0, 150))
                label.setGraphicsEffect(effect)
            else:
                effect = label.graphicsEffect()
                if effect is not None:

                    label.setGraphicsEffect(None)

    def _style_title_text(self):
        t = self.theme
        self.title_bar.title_text.setStyleSheet(
            f"background: transparent; border: none; color: {t.text}; font-size: 14px; font-weight: 800;")
        self.title_bar.version_tag.setStyleSheet(
            f"background: transparent; border: 1px solid {t.border}; color: {t.text_dim};"
            f"border-radius: 10px; padding: 2px 8px; font-size: 11px;")

    def refresh_backdrop(self):
        cfg = self.engine.config
        if cfg.bg_image and os.path.exists(cfg.bg_image):
            self.backdrop.set_image(cfg.bg_image, cfg.bg_blur)
            self.backdrop.setVisible(True)
        else:
            self.backdrop.clear_image()
            self.backdrop.setVisible(False)
        self._sync_backdrop()
        self._rebuild_theme()

    def toggle_theme(self):
        target = DEFAULT_ALT if self.base_preset == DEFAULT_DARK else DEFAULT_DARK
        self.apply_theme(target)
        self.save_config()

    def _on_preset_selected(self, name):
        self.apply_theme(name)
        self.save_config()

    def _on_accent_selected(self, name):
        self.engine.config.accent_color = name
        self._rebuild_theme()
        self.save_config()

    def _on_pick_bg(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "选择背景图片", "", "图片文件 (*.png *.jpg *.jpeg *.bmp *.webp)")
        if path:
            self.engine.config.bg_image = path
            self.save_config()
            self.refresh_backdrop()
            self.page_interface.refresh_bg_path()

    def _on_clear_bg(self):
        self.engine.config.bg_image = ""
        self.save_config()
        self.refresh_backdrop()
        self.page_interface.refresh_bg_path()

    def _on_bg_change(self):
        self.save_config()
        self.refresh_backdrop()

    def _build_ui(self):
        central = QWidget()
        central.setObjectName("appRoot")
        self.setCentralWidget(central)
        self.root_layout = QVBoxLayout(central)
        self.root_layout.setContentsMargins(0, 0, 0, 0)
        self.root_layout.setSpacing(0)

        shell = QFrame()
        shell.setProperty("panel", "1")
        self.shell = shell
        shell_layout = QVBoxLayout(shell)
        shell_layout.setContentsMargins(0, 0, 0, 0)
        shell_layout.setSpacing(0)
        self.root_layout.addWidget(shell)

        self.backdrop = BackdropWidget(shell)
        self.backdrop.setVisible(False)
        self.backdrop.lower()
        shell.installEventFilter(self)

        self.title_bar = TitleBar(self)
        shell_layout.addWidget(self.title_bar)

        content = QHBoxLayout()
        content.setContentsMargins(14, 12, 14, 14)
        content.setSpacing(14)
        shell_layout.addLayout(content, 1)

        self._build_sidebar()
        content.addWidget(self.sidebar)

        self.stack = QStackedWidget()
        self.stack.setStyleSheet("QStackedWidget { background: transparent; }")

        self.page_log = LogPage(get_config=lambda: self.engine.config.to_dict())
        self.forward_log = self.page_log.append_log
        self.page_scrape = ScrapePage(
            self.engine, forward_log=self.forward_log,
            get_config=lambda: self.engine.config.to_dict(),
            on_switch_log=lambda: self.switch_page(1),
            on_busy_changed=self._on_scrape_busy,
        )
        self.page_settings = NetworkPage(self.engine, on_save=self.save_config)
        self.page_interface = InterfacePage(
            self.engine,
            on_save=self.save_config,
            on_theme_change=self._on_preset_selected,
            on_accent_change=self._on_accent_selected,
            on_pick_bg=self._on_pick_bg,
            on_clear_bg=self._on_clear_bg,
            on_bg_change=self._on_bg_change,
            current_theme=self.engine.config._theme,
        )
        self.page_about = AboutPage()

        for page in (self.page_scrape, self.page_log, self.page_settings,
                     self.page_interface, self.page_about):
            self.stack.addWidget(page)
        content.addWidget(self.stack, 1)
        self.switch_page(0)

    def _build_sidebar(self):
        self.sidebar = QFrame()
        self.sidebar.setProperty("sidebar", "1")
        self.sidebar.setFixedWidth(226)
        layout = QVBoxLayout(self.sidebar)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(12)

        nav_panel = QFrame()
        nav_panel.setProperty("card", "2")
        nav_layout = QVBoxLayout(nav_panel)
        nav_layout.setContentsMargins(8, 8, 8, 8)
        nav_layout.setSpacing(4)
        self.nav_buttons = {}
        for index, text in NAV_ITEMS:
            btn = NavButton(text)
            btn.clicked.connect(lambda _checked=False, i=index: self.switch_page(i))
            nav_layout.addWidget(btn)
            self.nav_buttons[index] = btn
        layout.addWidget(nav_panel)

        control_box = self._card("爬取控制")
        self.btn_sidebar_start = make_button("开始爬取", "primary")
        self.btn_sidebar_start.clicked.connect(self._sidebar_start)
        control_box.add_widget(self.btn_sidebar_start)
        self.btn_sidebar_stop = make_button("停止爬取", "danger")
        self.btn_sidebar_stop.setEnabled(False)
        self.btn_sidebar_stop.clicked.connect(self._sidebar_stop)
        control_box.add_widget(self.btn_sidebar_stop)
        layout.addWidget(control_box)

        status_box = self._card("连接状态")
        self.sidebar_status = QLabel("未测试")
        self.sidebar_status.setProperty("role", "desc")
        self.sidebar_status.setWordWrap(True)
        status_box.add_widget(self.sidebar_status)
        self.btn_sidebar_test = make_button("测试连接", "secondary")
        self.btn_sidebar_test.clicked.connect(self._test_sidebar_connection)
        status_box.add_widget(self.btn_sidebar_test)
        layout.addWidget(status_box)

        layout.addStretch()

        footer = self._card(None)
        author = QLabel(f"作者：{AUTHOR}")
        author.setProperty("role", "desc")
        author.setStyleSheet("background: transparent; border: none; font-size: 12px; font-weight: 700;")
        footer.add_widget(author)
        github = make_button("GitHub 项目地址", "link")
        github.clicked.connect(lambda: self._open_url(GITHUB_URL))
        footer.add_widget(github)
        layout.addWidget(footer)

    @staticmethod
    def _card(title=None):
        card = QFrame()
        card.setProperty("card", "2")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(6)
        if title:
            label = QLabel(title)
            label.setProperty("role", "section")
            layout.addWidget(label)
        card.add_widget = layout.addWidget
        return card

    def _test_sidebar_connection(self):
        self.btn_sidebar_test.setEnabled(False)
        self.sidebar_status.setProperty("role", "status-run")
        self.sidebar_status.setText("测试中 ...")
        self._repolish(self.sidebar_status)

        engine = ScraperEngine(config=self.engine.config, on_log=self.engine.on_log)
        worker = FuncWorker(engine.test_connection, self)
        self._sidebar_test_worker = worker
        worker.done.connect(self._on_sidebar_test_done)
        worker.start()

    def _on_sidebar_test_done(self, payload):
        self.btn_sidebar_test.setEnabled(True)
        if isinstance(payload, tuple) and payload and payload[0] == "error":
            text, role = f"测试失败：{payload[1]}", "status-err"
        else:
            ok, eng, _ = payload
            text, role = (f"连接正常：{eng}", "status-ok") if ok else \
                ("连接失败：请检查网络/代理", "status-err")
        self.sidebar_status.setText(text)
        self.sidebar_status.setProperty("role", role)
        self._repolish(self.sidebar_status)

    @staticmethod
    def _repolish(widget):
        widget.style().unpolish(widget)
        widget.style().polish(widget)

    def _open_url(self, url):
        from PySide6.QtCore import QUrl
        from PySide6.QtGui import QDesktopServices
        QDesktopServices.openUrl(QUrl(url))

    def _sidebar_start(self):
        self.switch_page(0)
        self.page_scrape.start_scrape()

    def _sidebar_stop(self):
        self.page_scrape.stop_scrape()

    def _on_scrape_busy(self, busy):
        self.btn_sidebar_start.setEnabled(not busy)
        self.btn_sidebar_stop.setEnabled(busy)

    def switch_page(self, index):
        if hasattr(self, "stack"):
            self.stack.setCurrentIndex(index)
        for i, btn in self.nav_buttons.items():
            btn.setChecked(i == index)

    def toggle_maximize_restore(self):
        if self.isMaximized():
            self.showNormal()
        else:
            self.showMaximized()
        self._update_frame_margins()
        self.title_bar.sync_state()

    def _update_frame_margins(self):
        margin = 0
        self.root_layout.setContentsMargins(margin, margin, margin, margin)
        if hasattr(self, "backdrop"):
            self.backdrop.set_corner_radius(margin + 18)

    def changeEvent(self, event):
        super().changeEvent(event)
        if hasattr(self, "title_bar"):
            self.title_bar.sync_state()
            self._update_frame_margins()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._sync_backdrop()

    def showEvent(self, event):
        super().showEvent(event)
        QTimer.singleShot(0, self._sync_backdrop)

    def eventFilter(self, obj, event):
        if obj is self.shell and event.type() == QEvent.Resize:
            self._sync_backdrop()
        return super().eventFilter(obj, event)

    def _sync_backdrop(self):
        if hasattr(self, "backdrop") and hasattr(self, "shell"):
            self.backdrop.setGeometry(QRect(0, 0, self.shell.width(), self.shell.height()))

    def closeEvent(self, event):
        try:
            self.page_scrape.shutdown()
        except Exception:
            pass
        super().closeEvent(event)

    def nativeEvent(self, event_type, message):
        try:
            if event_type == b"windows_generic_MSG":
                msg = ctypes.wintypes.MSG.from_address(int(message))
                if msg.message == 0x0084:
                    return True, 1
        except Exception:
            pass
        return super().nativeEvent(event_type, message)

    def load_config(self):
        data = {}
        if os.path.exists(CONFIG_PATH):
            try:
                with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                    data = json.load(f) or {}
            except Exception:
                data = {}
        theme_name = data.get("theme", DEFAULT_DARK)
        if theme_name not in PRESETS:
            theme_name = DEFAULT_DARK
        self.engine.config = ScraperConfig.from_dict(data.get("engine", {}))
        self.engine.config._theme = theme_name
        if not is_valid_accent(self.engine.config.accent_color):
            self.engine.config.accent_color = "青绿"

    def save_config(self):
        cfg = self.engine.config.to_dict()
        theme_name = cfg.pop("_theme", self.theme.name)
        try:
            with open(CONFIG_PATH, "w", encoding="utf-8") as f:
                json.dump({"theme": theme_name, "engine": cfg}, f,
                          ensure_ascii=False, indent=2)
            return True
        except Exception as exc:
            print(f"保存配置失败: {exc}")
            return False