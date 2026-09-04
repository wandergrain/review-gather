

from typing import Callable, List, Tuple

from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QColor, QFont, QPainter, QPainterPath, QPen
from PySide6.QtWidgets import (
    QComboBox, QDoubleSpinBox, QFrame, QHBoxLayout, QLabel,
    QPushButton, QSlider, QSpinBox, QVBoxLayout,
)

FONT_FAMILY = "Microsoft YaHei UI"

def make_button(text: str, kind: str = "secondary", parent=None) -> QPushButton:
    btn = QPushButton(text, parent)
    btn.setProperty("type", kind)
    btn.setFocusPolicy(Qt.NoFocus)
    btn.setCursor(Qt.PointingHandCursor)
    return btn

class NoWheelSpinBox(QSpinBox):
    def wheelEvent(self, event):
        event.ignore()

class NoWheelDoubleSpinBox(QDoubleSpinBox):
    def wheelEvent(self, event):
        event.ignore()

class NoWheelSlider(QSlider):
    def wheelEvent(self, event):
        event.ignore()

class FieldComboBox(QComboBox):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setProperty("field", "1")
        self._arrow_color = QColor("#9AB0CA")
        self.setFocusPolicy(Qt.NoFocus)

    def wheelEvent(self, event):
        event.ignore()

    def set_arrow_color(self, color):
        self._arrow_color = QColor(color)
        self.update()

    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        pen = QPen(self._arrow_color, 1.7)
        pen.setCapStyle(Qt.RoundCap)
        pen.setJoinStyle(Qt.RoundJoin)
        painter.setPen(pen)
        cx = self.width() - 17
        cy = self.height() / 2.0
        painter.drawLine(int(cx - 3), int(cy - 2), int(cx), int(cy + 1))
        painter.drawLine(int(cx + 3), int(cy - 2), int(cx), int(cy + 1))
        painter.end()

class TitleButtonGroup(QFrame):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setProperty("titleGroup", "1")
        self.setFixedHeight(32)
        self._layout = QHBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(0)
        self.setStyleSheet("QFrame[titleGroup=\"1\"] { background: transparent; border: none; }")
        self.setAttribute(Qt.WA_Hover, True)

    def add_button(self, btn):
        self._layout.addWidget(btn)

    def paintEvent(self, _event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        rect = QRectF(self.rect())
        if self._is_dark():
            base, border = QColor(255, 255, 255, 10), QColor(255, 255, 255, 24)
        else:
            base, border = QColor(0, 0, 0, 16), QColor(0, 0, 0, 30)
        painter.setPen(Qt.NoPen)
        painter.setBrush(base)
        painter.drawRoundedRect(rect, 12, 12)
        painter.setPen(QPen(border, 1))
        painter.setBrush(Qt.NoBrush)
        painter.drawRoundedRect(rect.adjusted(0.5, 0.5, -0.5, -0.5), 12, 12)
        painter.end()

    def _is_dark(self) -> bool:
        try:
            window = self.window()
            if hasattr(window, "theme"):
                return getattr(window.theme, "kind", "dark") == "dark"
        except Exception:
            pass
        return True

def _button_position(btn) -> Tuple[bool, bool]:

    parent = btn.parent()
    if isinstance(parent, TitleButtonGroup):
        idx = parent.layout().indexOf(btn)
        return idx == 0, idx == parent.layout().count() - 1
    return True, True

class TitleButton(QPushButton):

    def __init__(self, kind: str, parent=None):
        super().__init__(parent)
        self.kind = kind
        self._icon_color = QColor("#5B6B82")
        self.setFixedSize(40, 32)
        self.setCursor(Qt.PointingHandCursor)
        self.setFocusPolicy(Qt.NoFocus)
        self.setAttribute(Qt.WA_Hover, True)
        self.setStyleSheet("QPushButton { background: transparent; border: none; outline: none; }")

    def set_kind(self, kind: str):
        if self.kind != kind:
            self.kind = kind
            self.update()

    def set_icon_color(self, color):
        self._icon_color = QColor(color)
        self.update()

    def enterEvent(self, event):
        self.update()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.update()
        super().leaveEvent(event)

    def paintEvent(self, _event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        is_first, is_last = _button_position(self)
        is_close = self.kind == "close"
        is_dark = self._is_dark()
        hovered = self.underMouse()

        if self.isDown():
            bg = QColor(0, 0, 0, 55) if is_dark else QColor(0, 0, 0, 28)
        elif hovered:
            bg = QColor(239, 68, 68, 220) if is_close else (
                QColor(255, 255, 255, 26) if is_dark else QColor(0, 0, 0, 20))
        else:
            bg = QColor(0, 0, 0, 0)

        if bg.alpha() > 0:
            painter.setPen(Qt.NoPen)
            painter.setBrush(bg)
            rect = QRectF(self.rect()).adjusted(1, 1, -1, -1)
            path = QPainterPath()
            if is_first and is_last:
                path.addRoundedRect(rect, 11, 11)
            elif is_first:
                path.addRoundedRect(rect, 11, 11)
                path = path.united(self._right_patch(rect))
            elif is_last:
                path.addRoundedRect(rect, 11, 11)
                path = path.united(self._left_patch(rect))
            else:
                path.addRect(rect)
            painter.drawPath(path)

        icon_color = QColor(255, 255, 255) if (is_close and hovered) else QColor(self._icon_color)
        pen = QPen(icon_color, 1.5)
        pen.setCapStyle(Qt.RoundCap)
        pen.setJoinStyle(Qt.RoundJoin)
        painter.setPen(pen)

        cx, cy = self.width() / 2.0, self.height() / 2.0
        if self.kind == "min":
            painter.drawLine(int(cx - 5), int(cy + 1), int(cx + 5), int(cy + 1))
        elif self.kind == "max":
            painter.setBrush(Qt.NoBrush)
            painter.drawRoundedRect(int(cx - 5), int(cy - 4), 10, 10, 2, 2)
        elif self.kind == "restore":
            painter.setBrush(Qt.NoBrush)
            painter.drawRoundedRect(int(cx - 6), int(cy - 1), 8, 8, 1, 1)
            painter.drawRoundedRect(int(cx - 1), int(cy - 6), 8, 8, 1, 1)
        elif self.kind == "close":
            painter.drawLine(int(cx - 5), int(cy - 5), int(cx + 5), int(cy + 5))
            painter.drawLine(int(cx + 5), int(cy - 5), int(cx - 5), int(cy + 5))
        elif self.kind == "theme":
            painter.setBrush(Qt.NoBrush)
            painter.drawEllipse(int(cx - 4), int(cy - 4), 9, 9)
            painter.drawEllipse(int(cx - 2), int(cy - 6), 5, 5)
        elif self.kind == "about":
            painter.setBrush(Qt.NoBrush)
            painter.drawEllipse(int(cx - 4), int(cy - 4), 9, 9)
            painter.setBrush(icon_color)
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(int(cx) - 1, int(cy) - 4, 2, 2)
            pen2 = QPen(icon_color, 1.7)
            pen2.setCapStyle(Qt.RoundCap)
            painter.setPen(pen2)
            painter.setBrush(Qt.NoBrush)
            painter.drawLine(int(cx), int(cy - 1), int(cx), int(cy + 3))
        painter.end()

    @staticmethod
    def _right_patch(rect: QRectF) -> "QPainterPath":
        fill = QPainterPath()
        fill.addRect(QRectF(rect.right() - 11, rect.top(), 12, rect.height()))
        return fill

    @staticmethod
    def _left_patch(rect: QRectF) -> "QPainterPath":
        fill = QPainterPath()
        fill.addRect(QRectF(rect.left(), rect.top(), 11, rect.height()))
        return fill

    def _is_dark(self) -> bool:
        try:
            window = self.window()
            if hasattr(window, "theme"):
                return getattr(window.theme, "kind", "dark") == "dark"
        except Exception:
            pass
        return True

class NavButton(QPushButton):
    def __init__(self, text: str, parent=None):
        super().__init__(text, parent)
        self.setProperty("nav", "1")
        self.setCheckable(True)
        self.setCursor(Qt.PointingHandCursor)
        self.setFocusPolicy(Qt.NoFocus)
        self.setFont(QFont(FONT_FAMILY, 11, QFont.DemiBold))

class Card(QFrame):

    def __init__(self, title: str = "", desc: str = "", level: int = 1, parent=None):
        super().__init__(parent)
        self.setProperty("card", str(level))
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(16, 14, 16, 14)
        self._layout.setSpacing(8)
        if title:
            label = QLabel(title)
            label.setProperty("role", "section")
            self._layout.addWidget(label)
        if desc:
            label = QLabel(desc)
            label.setProperty("role", "desc")
            label.setWordWrap(True)
            self._layout.addWidget(label)

    def add_widget(self, widget, stretch: int = 0, align=None):
        if align is not None:
            self._layout.addWidget(widget, stretch, align)
        else:
            self._layout.addWidget(widget, stretch)

    def add_layout(self, layout, stretch: int = 0):
        self._layout.addLayout(layout, stretch)

    def add_stretch(self):
        self._layout.addStretch()

def make_row(spacing: int = 12) -> QHBoxLayout:

    layout = QHBoxLayout()
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(spacing)
    return layout

class StatCard(QFrame):
    def __init__(self, label: str, accent: str = "#0D9488", parent=None):
        super().__init__(parent)
        self.setProperty("card", "1")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 11, 14, 9)
        layout.setSpacing(2)

        self.label_label = QLabel(label)
        self.label_label.setProperty("role", "desc")
        layout.addWidget(self.label_label)
        self.value_label = QLabel("--")
        self.value_label.setProperty("role", "stat")
        layout.addWidget(self.value_label)
        self.sub_label = QLabel("")
        self.sub_label.setProperty("role", "desc")
        layout.addWidget(self.sub_label)
        self.line = QFrame()
        self.line.setFixedHeight(4)
        layout.addWidget(self.line)
        self.set_accent(accent)

    def set_data(self, value, sub: str = ""):
        self.value_label.setText(str(value))
        self.sub_label.setText(str(sub))

    def set_accent(self, accent: str):
        self.value_label.setStyleSheet(
            f"background: transparent; border: none; color: {accent}; font-size: 23px; font-weight: 900;")
        self.line.setStyleSheet(
            f"background: {accent}; border: none; border-radius: 2px; margin: 4px 0 0 0;")

def _config_from_slider(value: int, value_scale: float, config_decimals=None):
    scaled = float(value) * float(value_scale)
    if config_decimals is not None:
        return round(scaled, int(config_decimals))
    if abs(float(value_scale) - 1.0) < 0.000001:
        return int(round(scaled))
    return scaled

def _format_slider(value: int, display_scale: float, display_suffix: str, display_decimals: int):
    disp = float(value) * float(display_scale)
    text = str(int(round(disp))) if int(display_decimals) <= 0 else \
        f"{disp:.{int(display_decimals)}f}".rstrip("0").rstrip(".")
    return f"{text}{display_suffix}"

def build_slider_block(parent_layout, title, note, value, minimum, maximum,
                       key: str, on_change: Callable,
                       value_scale=1.0, display_scale=None, display_suffix="",
                       display_decimals=0, config_decimals=None) -> dict:

    display_scale = value_scale if display_scale is None else display_scale
    try:
        slider_value = int(round(float(value) / float(value_scale)))
    except (TypeError, ValueError, ZeroDivisionError):
        slider_value = int(minimum)
    slider_value = max(int(minimum), min(int(maximum), slider_value))

    block = QFrame()
    block.setProperty("card", "2")
    layout = QVBoxLayout(block)
    layout.setContentsMargins(14, 10, 14, 10)
    layout.setSpacing(6)

    top = QHBoxLayout()
    title_label = QLabel(title)
    title_label.setProperty("role", "section")
    top.addWidget(title_label)
    top.addStretch()
    value_label = QLabel(_format_slider(slider_value, display_scale, display_suffix, display_decimals))
    value_label.setProperty("role", "pill")
    value_label.setAlignment(Qt.AlignCenter)
    top.addWidget(value_label)
    layout.addLayout(top)

    note_label = QLabel(note)
    note_label.setProperty("role", "desc")
    note_label.setWordWrap(True)
    layout.addWidget(note_label)

    slider = NoWheelSlider(Qt.Horizontal)
    slider.setProperty("slider", "1")
    slider.setRange(int(minimum), int(maximum))
    slider.setValue(slider_value)
    slider.setFocusPolicy(Qt.NoFocus)

    def _on_change(new_value):
        value_label.setText(_format_slider(new_value, display_scale, display_suffix, display_decimals))
        try:
            on_change(key, _config_from_slider(new_value, value_scale, config_decimals))
        except Exception:
            pass

    slider.valueChanged.connect(_on_change)
    layout.addWidget(slider)
    parent_layout.addWidget(block)
    return {
        "type": "slider", "widget": slider, "value_label": value_label,
        "value_scale": value_scale, "config_decimals": config_decimals,
        "default": value,
    }

def build_choice_block(parent_layout, title, note, options: List[Tuple], current,
                       key: str, on_change: Callable) -> dict:

    block = QFrame()
    block.setProperty("card", "2")
    layout = QVBoxLayout(block)
    layout.setContentsMargins(14, 10, 14, 10)
    layout.setSpacing(6)

    title_label = QLabel(title)
    title_label.setProperty("role", "section")
    layout.addWidget(title_label)
    note_label = QLabel(note)
    note_label.setProperty("role", "desc")
    note_label.setWordWrap(True)
    layout.addWidget(note_label)

    combo = FieldComboBox()
    values = []
    index = 0
    for i, (value, label) in enumerate(options):
        combo.addItem(label)
        values.append(value)
        if value == current:
            index = i
    combo.setCurrentIndex(index)
    combo.currentIndexChanged.connect(
        lambda i: on_change(key, values[i]) if 0 <= i < len(values) else None)
    layout.addWidget(combo)

    parent_layout.addWidget(block)
    return {"type": "choice", "widget": combo, "values": values, "default": current}