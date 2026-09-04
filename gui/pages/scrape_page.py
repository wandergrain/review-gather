

import time
from datetime import datetime

from PySide6.QtCore import QObject, QThread, QTimer, QUrl, Signal
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QAbstractSpinBox, QFileDialog, QFrame, QHBoxLayout, QLabel,
    QLineEdit, QProgressBar, QScrollArea, QVBoxLayout, QWidget,
)

from core.scraper import (
    EXPORT_FORMATS, LANG_CODE_TO_CN, LANGUAGE_MENU, PURCHASE_DISPLAY,
    PURCHASE_TYPES, REVIEW_FILTERS, ScraperEngine, TIME_FIELDS, run_scrape,
    validate_api_key,
)
from gui.widgets import (
    Card, FieldComboBox, NoWheelDoubleSpinBox, NoWheelSpinBox, StatCard,
    make_button, make_row,
)

class LogBridge(QObject):

    emitted = Signal(str)

    def __call__(self, msg):
        self.emitted.emit(str(msg))

class ScrapeWorker(QThread):

    progress = Signal(int, int, int)
    official = Signal(object)
    stage = Signal(str)
    nickname = Signal(int, int)
    done = Signal(bool, str, object)

    def __init__(self, engine, params, parent=None):
        super().__init__(parent)
        self.engine = engine
        self.params = params

    def run(self):
        try:
            p = self.params
            result = run_scrape(
                self.engine,
                appid=p["appid"],
                language=p["language"],
                max_reviews=p["max_reviews"],
                review_filter=p["review_filter"],
                purchase_type=p["purchase_type"],
                min_hours=p["min_hours"],
                time_filter_field=p["time_filter_field"],
                api_key=p["api_key"],
                export_dir=p["export_dir"],
                export_format=p["export_format"],
                progress_cb=lambda raw, valid, pos: self.progress.emit(raw, valid, pos),
                on_stage=self.stage.emit,
                on_official=self.official.emit,
                on_nickname_progress=lambda done, total: self.nickname.emit(done, total),
            )
            self.done.emit(bool(result.get("success")), str(result.get("reason", "")), result)
        except Exception as exc:
            self.done.emit(False, f"程序异常: {exc}", {})

class FuncWorker(QThread):

    done = Signal(object)

    def __init__(self, fn, parent=None):
        super().__init__(parent)
        self.fn = fn

    def run(self):
        try:
            result = self.fn()
        except Exception as exc:
            result = ("error", str(exc))
        self.done.emit(result)

class ScrapePage(QFrame):
    def __init__(self, engine, forward_log, get_config, on_switch_log,
                 on_busy_changed=None, parent=None):
        super().__init__(parent)
        self.engine = engine
        self.forward_log = forward_log
        self.get_config = get_config
        self.on_switch_log = on_switch_log
        self.on_busy_changed = on_busy_changed

        self._worker = None
        self._running = False
        self._start_ts = None
        self._official_total = 0
        self._current_target = 0

        self._bridge = LogBridge()
        self._bridge.emitted.connect(self.forward_log)
        self.engine.on_log = self._bridge

        self._elapsed_timer = QTimer(self)
        self._elapsed_timer.setInterval(500)
        self._elapsed_timer.timeout.connect(self._tick_elapsed)

        self.setProperty("panel", "1")
        self.root = QVBoxLayout(self)
        self.root.setContentsMargins(20, 16, 20, 16)
        self.root.setSpacing(10)

        title = QLabel("爬取数据")
        title.setProperty("role", "headline")
        self.root.addWidget(title)
        subtitle = QLabel("请填入游戏 AppID 查询信息，不知道ID可以前往游戏商店页面查看，复制粘贴选择参数后开始爬取")
        subtitle.setProperty("role", "subtitle")
        self.root.addWidget(subtitle)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        body = QWidget()
        self.body_layout = QVBoxLayout(body)
        self.body_layout.setContentsMargins(0, 0, 6, 0)
        self.body_layout.setSpacing(10)
        scroll.setWidget(body)
        self.root.addWidget(scroll, 1)

        self._build_config_rows()
        self._build_bottom()

    def _build_config_rows(self):
        L = self.body_layout

        row1 = make_row()
        card_appid = Card("游戏 AppID )", "填写完成，将要查询的信息请确认无误！")
        appid_row = QHBoxLayout()
        appid_row.setSpacing(8)
        self.appid_edit = QLineEdit()
        self.appid_edit.setProperty("field", "1")
        self.appid_edit.setPlaceholderText("例如 730 / 1245620")
        self.btn_view_info = make_button("查看游戏信息", "secondary")
        self.btn_view_info.clicked.connect(self.view_game_info)
        appid_row.addWidget(self.appid_edit, 1)
        appid_row.addWidget(self.btn_view_info)
        card_appid.add_layout(appid_row)
        row1.addWidget(card_appid, 2)

        self.info_card = Card("游戏信息", "查询后将显示游戏名称与官方评测统计")
        self.info_title = QLabel("尚未查询")
        self.info_title.setProperty("role", "section")
        self.info_title.setWordWrap(True)
        self.info_card.add_widget(self.info_title)
        self.info_sub = QLabel("输入 AppID 后点击查看游戏信息！")
        self.info_sub.setProperty("role", "desc")
        self.info_sub.setWordWrap(True)
        self.info_card.add_widget(self.info_sub)
        self.info_tags = QLabel("")
        self.info_tags.setProperty("role", "desc")
        self.info_tags.setWordWrap(True)
        self.info_card.add_widget(self.info_tags)
        row1.addWidget(self.info_card, 3)
        L.addLayout(row1)

        row2 = make_row()
        card_lang = Card("评测语言", "选择评测显示语言")
        self.lang_combo = self._make_combo(LANGUAGE_MENU, "schinese")
        card_lang.add_widget(self.lang_combo)
        row2.addWidget(card_lang)

        card_filter = Card("评测类型", "全部 / 仅好评 / 仅差评")
        self.filter_combo = self._make_combo(REVIEW_FILTERS, "recent")
        card_filter.add_widget(self.filter_combo)
        row2.addWidget(card_filter)

        card_purchase = Card("购买来源", "所有 / 仅Steam商店 / 仅非Steam")
        self.purchase_combo = self._make_combo(PURCHASE_TYPES, "all")
        card_purchase.add_widget(self.purchase_combo)
        row2.addWidget(card_purchase)
        L.addLayout(row2)

        row3 = make_row()
        card_max = Card("获取数量", "0 = 无上限")
        self.max_spin = NoWheelSpinBox()
        self.max_spin.setProperty("field", "1")
        self.max_spin.setButtonSymbols(QAbstractSpinBox.NoButtons)
        self.max_spin.setRange(0, 100000)
        self.max_spin.setValue(0)
        self.max_spin.setSuffix(" 条")
        card_max.add_widget(self.max_spin)
        row3.addWidget(card_max)

        card_hours = Card("最少游戏时长", "0 = 不过滤")
        self.min_hours_spin = NoWheelDoubleSpinBox()
        self.min_hours_spin.setProperty("field", "1")
        self.min_hours_spin.setButtonSymbols(QAbstractSpinBox.NoButtons)
        self.min_hours_spin.setRange(0.0, 99999.0)
        self.min_hours_spin.setDecimals(1)
        self.min_hours_spin.setValue(0.0)
        self.min_hours_spin.setSuffix(" 小时")
        card_hours.add_widget(self.min_hours_spin)
        row3.addWidget(card_hours)

        card_time = Card("时长基准", "时长筛选依据的字段")
        self.time_combo = self._make_combo(TIME_FIELDS, "playtime_forever")
        card_time.add_widget(self.time_combo)
        row3.addWidget(card_time)
        L.addLayout(row3)

        row4 = make_row()
        card_key = Card("Steam Web API Key", "可选，用于获取用户昵称。")
        key_row = QHBoxLayout()
        key_row.setSpacing(8)
        self.api_key_edit = QLineEdit()
        self.api_key_edit.setProperty("field", "1")
        self.api_key_edit.setPlaceholderText("留空则使用 SteamID 代替昵称")
        self.api_key_edit.setEchoMode(QLineEdit.Password)
        self.api_key_edit.setText(self.engine.config.steam_api_key)
        self.api_key_edit.textEdited.connect(self._on_key_edited)
        key_row.addWidget(self.api_key_edit, 1)
        self.btn_show_key = make_button("显示", "ghost")
        self.btn_show_key.setToolTip("显示 / 隐藏密钥")
        self.btn_show_key.clicked.connect(self.toggle_key_visible)
        key_row.addWidget(self.btn_show_key)
        self.btn_validate_key = make_button("验证 Key", "ghost")
        self.btn_validate_key.clicked.connect(self.validate_key)
        key_row.addWidget(self.btn_validate_key)
        self.btn_get_key = make_button("获取 API Key", "ghost")
        self.btn_get_key.setToolTip("打开 Steam 官方页面申请 API Key")
        self.btn_get_key.clicked.connect(self.open_api_key_page)
        key_row.addWidget(self.btn_get_key)
        card_key.add_layout(key_row)

        self.key_status = QLabel("")
        self.key_status.setProperty("role", "desc")
        card_key.add_widget(self.key_status)
        row4.addWidget(card_key, 3)

        card_dir = Card("导出设置", "选择导出格式与保存位置，目录留空 = 程序目录")
        fmt_row = QHBoxLayout()
        fmt_row.setSpacing(8)
        self.export_fmt_combo = self._make_combo(EXPORT_FORMATS, "all")
        fmt_row.addWidget(self.export_fmt_combo, 1)
        card_dir.add_layout(fmt_row)
        dir_row = QHBoxLayout()
        dir_row.setSpacing(8)
        self.export_dir_edit = QLineEdit()
        self.export_dir_edit.setProperty("field", "1")
        self.export_dir_edit.setPlaceholderText("留空使用程序目录")
        self.btn_browse = make_button("浏览", "ghost")
        self.btn_browse.clicked.connect(self.browse_dir)
        dir_row.addWidget(self.export_dir_edit, 1)
        dir_row.addWidget(self.btn_browse)
        card_dir.add_layout(dir_row)
        row4.addWidget(card_dir, 2)
        L.addLayout(row4)

        self.detail_card = QFrame()
        self.detail_card.setProperty("card", "2")
        detail_layout = QVBoxLayout(self.detail_card)
        detail_layout.setContentsMargins(14, 10, 14, 10)
        detail_layout.setSpacing(6)
        detail_title = QLabel("详细分布")
        detail_title.setProperty("role", "section")
        detail_layout.addWidget(detail_title)
        self.detail_text = QLabel("")
        self.detail_text.setProperty("role", "desc")
        self.detail_text.setWordWrap(True)
        detail_layout.addWidget(self.detail_text)
        self.detail_card.setVisible(False)
        L.addWidget(self.detail_card)

        L.addStretch()

    def _build_bottom(self):
        R = self.root

        self.progress_card = Card("爬取进度", "")
        self.stage_label = QLabel("待机中")
        self.stage_label.setProperty("role", "status-ok")
        self.progress_card.add_widget(self.stage_label)
        self.progress_bar = QProgressBar()
        self.progress_bar.setProperty("bar", "1")
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setFormat("0%")
        self.progress_card.add_widget(self.progress_bar)
        self.progress_detail = QLabel("无数据")
        self.progress_detail.setProperty("role", "desc")
        self.progress_card.add_widget(self.progress_detail)
        R.addWidget(self.progress_card)

        summary_header = QHBoxLayout()
        summary_title = QLabel("爬取摘要")
        summary_title.setProperty("role", "section")
        summary_header.addWidget(summary_title)
        summary_header.addStretch()
        self.summary_sub = QLabel("")
        self.summary_sub.setProperty("role", "desc")
        summary_header.addWidget(self.summary_sub)
        R.addLayout(summary_header)

        stat_row = make_row(10)
        self.stats = {
            "official": StatCard("官方总数", "#3B82F6"),
            "scraped": StatCard("本次爬取", "#2DD4BF"),
            "complete": StatCard("抓取完整数", "#22C55E"),
            "positive": StatCard("推荐数", "#22C55E"),
            "negative": StatCard("差评数", "#F43F5E"),
            "time": StatCard("耗时", "#A855F7"),
        }
        for card in self.stats.values():
            stat_row.addWidget(card, 1)
        R.addLayout(stat_row)

        self._reset_summary()

    def _make_combo(self, items, current_key):
        combo = FieldComboBox()
        codes = []
        index = 0
        for i, (code, label) in enumerate(items):
            combo.addItem(label)
            codes.append(code)
            if code == current_key:
                index = i
        combo.setCurrentIndex(index)
        combo._codes = codes
        return combo

    def _combo_current(self, combo):
        codes = getattr(combo, "_codes", [])
        idx = combo.currentIndex()
        return codes[idx] if 0 <= idx < len(codes) else codes[0]

    def _collect_params(self):

        try:
            appid = int(self.appid_edit.text().strip() or 0)
        except ValueError:
            appid = 0
        return {
            "appid": appid,
            "language": self._combo_current(self.lang_combo),
            "max_reviews": int(self.max_spin.value()),
            "review_filter": self._combo_current(self.filter_combo),
            "purchase_type": self._combo_current(self.purchase_combo),
            "min_hours": float(self.min_hours_spin.value()),
            "time_filter_field": self._combo_current(self.time_combo),
            "api_key": self.api_key_edit.text().strip(),
            "export_dir": self.export_dir_edit.text().strip() or self.engine.config.export_dir or "",
            "export_format": self._combo_current(self.export_fmt_combo),
        }

    def _on_key_edited(self):
        self.engine.config.steam_api_key = self.api_key_edit.text().strip()
        try:
            save = getattr(self.engine, "save_config", None)
            if save is None:
                window = self.window()
                save = getattr(window, "save_config", None)
            if callable(save):
                save()
        except Exception:
            pass

    def toggle_key_visible(self):
        hidden = self.api_key_edit.echoMode() == QLineEdit.Password
        self.api_key_edit.setEchoMode(QLineEdit.Normal if hidden else QLineEdit.Password)
        self.btn_show_key.setText("隐藏" if hidden else "显示")

    def open_api_key_page(self):
        QDesktopServices.openUrl(QUrl("https://steamcommunity.com/dev/apikey"))

    def _set_status(self, text, err=False, run=False):
        self.stage_label.setProperty(
            "role", "status-err" if err else ("status-run" if run else "status-ok"))
        self.stage_label.setText(text)
        self.stage_label.style().unpolish(self.stage_label)
        self.stage_label.style().polish(self.stage_label)

    def _set_busy(self, busy):
        self._running = busy
        if self.on_busy_changed:
            self.on_busy_changed(busy)
        for widget in (self.appid_edit, self.btn_view_info,
                       self.lang_combo, self.filter_combo, self.purchase_combo,
                       self.max_spin, self.min_hours_spin, self.time_combo,
                       self.export_fmt_combo, self.export_dir_edit, self.btn_browse):
            widget.setEnabled(not busy)

    def view_game_info(self):
        try:
            appid = int(self.appid_edit.text().strip())
        except ValueError:
            self.info_sub.setText("错误：游戏 ID 必须为数字！")
            return
        if appid <= 0:
            self.info_sub.setText("错误：请输入有效的游戏 AppID！")
            return
        self.btn_view_info.setEnabled(False)
        self.info_title.setText("正在查询 ...")
        self.info_sub.setText("")
        self.info_tags.setText("")
        self.forward_log(f"[信息] 正在查询 AppID {appid} 的游戏信息 ...")

        engine = ScraperEngine(config=self.engine.config, on_log=self.engine.on_log)
        worker = FuncWorker(lambda: engine.fetch_game_info(appid), self)
        self._info_worker = worker
        worker.done.connect(self._on_info_done)
        worker.start()

    def _on_info_done(self, payload):
        self.btn_view_info.setEnabled(True)
        if isinstance(payload, tuple) and payload and payload[0] == "error":
            self.info_title.setText("查询失败")
            self.info_sub.setText(f"查询失败：{payload[1]}")
            return
        try:
            eng, chn, summary = payload
        except Exception:
            self.info_title.setText("查询失败")
            self.info_sub.setText("返回数据异常！")
            return
        if not eng:
            self.info_title.setText("查询失败")
            self.info_sub.setText("无法获取游戏信息，请检查网络/代理后重试！")
            return
        self.info_title.setText(f"{eng} / {chn or eng}")
        if summary and summary.get("total_reviews", 0) > 0:
            total = summary["total_reviews"]
            pos = summary.get("total_positive", 0)
            self.info_sub.setText("官方评测统计：")
            self.info_tags.setText(f"总评测 {total:,} 条  ·  好评 {pos:,} 条  ·  "
                                   f"好评率 {pos / total * 100:.1f}%")
        else:
            self.info_sub.setText("官方评测统计：无法获取")
            self.info_tags.setText("")
        self.forward_log(f"[信息] 查询完成：{eng} / {chn or eng}")

    def validate_key(self):
        key = self.api_key_edit.text().strip()
        if not key:
            self.key_status.setText("请先输入 API Key")
            return
        self.btn_validate_key.setEnabled(False)
        self.key_status.setText("验证中 ...")
        worker = FuncWorker(lambda: ("ok" if validate_api_key(key) else "bad"), self)
        self._key_worker = worker
        worker.done.connect(self._on_key_done)
        worker.start()

    def _on_key_done(self, payload):
        self.btn_validate_key.setEnabled(True)
        if isinstance(payload, tuple) and payload and payload[0] == "error":
            self.key_status.setText(f"验证出错：{payload[1]}")
            return
        ok = payload == "ok"
        self.key_status.setText("API Key 有效，将获取用户昵称！" if ok else "API Key 无效，将只显示 SteamID！")
        self.key_status.setProperty("role", "status-ok" if ok else "status-err")
        self.key_status.style().unpolish(self.key_status)
        self.key_status.style().polish(self.key_status)

    def browse_dir(self):
        path = QFileDialog.getExistingDirectory(self, "选择导出目录",
                                                self.export_dir_edit.text().strip() or ".")
        if path:
            self.export_dir_edit.setText(path)

    def _reset_summary(self):
        self._official_total = 0
        self.stats["scraped"]._last_value = None
        for key, (value, sub) in {
            "official": ("--", "Steam 官方"),
            "scraped": ("--", "有效评测"),
            "complete": ("--", "占官方比例"),
            "positive": ("--", "好评"),
            "negative": ("--", "不推荐"),
            "time": ("--", "爬取耗时"),
        }.items():
            self.stats[key].set_data(value, sub)
        self.summary_sub.setText("")
        self.detail_card.setVisible(False)
        self.detail_text.setText("")

    def _on_official(self, total):
        self._official_total = int(total or 0)
        self.stats["official"].set_data(
            f"{self._official_total:,} 条" if self._official_total > 0 else "--",
            "Steam 官方" if self._official_total > 0 else "未获取官方总数")
        self._refresh_completeness()

    def _refresh_completeness(self):
        valid = getattr(self.stats["scraped"], "_last_value", None)
        if valid is None or self._official_total <= 0:
            self.stats["complete"].set_data("--", "占官方比例")
            return
        self.stats["complete"].set_data(f"{valid / self._official_total * 100:.1f}%", "占官方比例")

    def _on_progress(self, raw, valid, positive):
        self.progress_detail.setText(f"原始 {raw} → 有效 {valid}")
        goal = self._current_target if self._current_target > 0 else self._official_total
        if goal and goal > 0:
            pct = valid / goal * 100
            self.progress_bar.setValue(int(round(pct)))
            self.progress_bar.setFormat(f"{pct:.1f}%")
        else:
            self.progress_bar.setValue(0)
            self.progress_bar.setFormat(f"已抓取 {valid} 条")
        self.stats["scraped"].set_data(f"{valid:,} 条", "有效评测")
        self.stats["scraped"]._last_value = valid
        self.stats["positive"].set_data(f"{positive:,}", "好评")
        self.stats["negative"].set_data(f"{valid - positive:,}", "不推荐")
        self._refresh_completeness()

    def _tick_elapsed(self):
        if self._start_ts:
            self.stats["time"].set_data(self._fmt_elapsed(time.time() - self._start_ts), "爬取耗时")

    @staticmethod
    def _fmt_elapsed(seconds):
        if seconds < 60:
            return f"{seconds:.1f}s"
        return f"{int(seconds // 60)}分{int(seconds % 60)}秒"

    def start_scrape(self):
        if self._running:
            return
        params = self._collect_params()
        if params["appid"] <= 0:
            self._set_status("请先输入有效的游戏 ID (AppID)", err=True)
            return
        self._current_target = params["max_reviews"]
        self._set_busy(True)
        self._set_status("准备中 ...", run=True)
        self.progress_bar.setValue(0)
        self.progress_bar.setFormat("0%")
        self.progress_detail.setText("原始 0 → 有效 0")
        self._reset_summary()

        self._start_ts = time.time()
        self._elapsed_timer.start()
        self._tick_elapsed()

        worker = ScrapeWorker(self.engine, params, self)
        self._worker = worker
        worker.progress.connect(self._on_progress)
        worker.official.connect(self._on_official)
        worker.stage.connect(lambda msg: self._set_status(msg, run=True))
        worker.nickname.connect(self._on_nickname_progress)
        worker.done.connect(self._on_scrape_done)
        worker.start()

    def _on_nickname_progress(self, done, total):
        if not total:
            return
        pct = min(100.0, done / total * 100)
        self.progress_bar.setValue(int(pct))
        self.progress_bar.setFormat(f"昵称 {done}/{total}")
        self.progress_detail.setText(f"正在获取用户昵称，已完成 {done}/{total}")

    def stop_scrape(self):
        if self._worker is not None and self._worker.isRunning():
            self.engine.request_stop()
            self._set_status("正在停止 ...", run=True)
            self.forward_log("[抓取] 收到停止请求，将在当前页结束后停止！")

    def _on_scrape_done(self, success, reason, result):
        self._set_busy(False)
        self._elapsed_timer.stop()
        stats = (result or {}).get("stats")
        if success and stats:
            self.progress_bar.setValue(100)
            self.progress_bar.setFormat("100%")
            self._set_status("爬取完成")
            self._finalize_summary(stats, result)
            if self.get_config().get("auto_switch_to_log", True):
                self.on_switch_log()
        else:
            self.progress_bar.setValue(0)
            self._set_status(f"未完成：{reason or '未知原因'}", err=True)
            self.detail_card.setVisible(False)

    def _finalize_summary(self, stats, result):
        total = stats["total"]
        positive = stats["positive"]
        official = stats.get("official_total") or 0
        self.stats["official"].set_data(f"{official:,} 条" if official else "--", "Steam 官方")
        self.stats["scraped"].set_data(f"{total:,} 条", "有效评测")
        completeness = stats.get("completeness")
        self.stats["complete"].set_data(
            f"{completeness:.1f}%" if completeness is not None else "--", "占官方比例")
        self.stats["positive"].set_data(f"{positive:,}", "好评")
        self.stats["negative"].set_data(f"{stats['negative']:,}", "不推荐")
        self.stats["time"].set_data(self._fmt_elapsed(stats["elapsed"]), "爬取耗时")

        if result.get("game_eng"):
            start = datetime.fromtimestamp(stats["start_time"]).strftime("%H:%M:%S")
            end = datetime.fromtimestamp(stats["end_time"]).strftime("%H:%M:%S")
            self.summary_sub.setText(
                f"{result['game_eng']} / {result.get('game_chn', '')}  ·  {start} → {end}")

        lines = []
        if stats.get("purchase_dist"):
            lines.append("购买来源统计（来源 / 数量 / 好评 / 差评 / 好评率）：")
            for key, cnt, pos in stats["purchase_dist"]:
                neg = cnt - pos
                rate = pos / cnt * 100 if cnt else 0
                lines.append(f"  {PURCHASE_DISPLAY.get(key, key)}：{cnt} 条  "
                             f"好评 {pos} / 差评 {neg}  好评率 {rate:.1f}%")
        if stats.get("lang_dist"):
            lines.append("")
            lines.append("语言分布（语言 / 数量 / 占比 / 好评率）：")
            for lang, cnt, pos in stats["lang_dist"]:
                rate = pos / cnt * 100 if cnt else 0
                name = LANG_CODE_TO_CN.get(lang, lang)
                lines.append(f"  {name}：{cnt} 条 ({cnt / total * 100:.1f}%)  好评率 {rate:.1f}%")
        if lines:
            self.detail_text.setText("\n".join(lines))
            self.detail_card.setVisible(True)

    def shutdown(self):
        if self._worker is not None and self._worker.isRunning():
            self.engine.request_stop()
            self._worker.wait(2000)