

class Theme:

    def __init__(self, name: str, kind: str, **tokens):
        self.name = name
        self.kind = kind
        self.__dict__.update(tokens)

LIGHT = Theme(
    name="浅米白",
    kind="light",
    bg="#F2EEE4",
    panel="#FCFAF4",
    sidebar="#F8F5EC",
    titlebar="#FCFAF4",
    card="#FDFCF8",
    card_soft="#F5F1E7",
    input="#F1ECE1",
    border="#E0D9C8",
    border_soft="#EAE3D3",
    text="#29251C",
    text_dim="#4A4436",
    text_soft="#6E6755",
    accent="#0D9488",
    accent_soft="#14B8A6",
    accent_deep="#0F766E",
    grad_a="#2DD4BF",
    grad_b="#0D9488",
    on_accent="#FFFFFF",
    accent_tint="rgba(13, 148, 136, 0.10)",
    accent_tint_border="rgba(13, 148, 136, 0.30)",
    danger="#D6455D",
    danger_tint="rgba(214, 69, 93, 0.08)",
    warning="#B8721E",
    success="#0D9488",
    hover_bg="rgba(41, 37, 28, 0.05)",
    groove_bg="#E3DCCB",
    handle_bg="#FFFFFF",
    sel_bg="#E3F1EC",
    scroll_handle="#CFC7B4",
    scroll_handle_hover="#B4AA93",
    shadow="rgba(41, 37, 28, 0.08)",
)

DARK = Theme(
    name="深海蓝",
    kind="dark",
    bg="#0F1729",
    panel="#0F1B2B",
    sidebar="#0B1626",
    titlebar="#0F1B2B",
    card="#162032",
    card_soft="#1A2A40",
    input="#152236",
    border="#2A3B55",
    border_soft="#1E3249",
    text="#F3F8FF",
    text_dim="#9AB0CA",
    text_soft="#7187A3",
    accent="#2DD4BF",
    accent_soft="#5EEAD4",
    accent_deep="#0D9488",
    grad_a="#5EEAD4",
    grad_b="#0D9488",
    on_accent="#062E2B",
    accent_tint="rgba(45, 212, 191, 0.14)",
    accent_tint_border="rgba(45, 212, 191, 0.38)",
    danger="#FF667E",
    danger_tint="rgba(255, 102, 126, 0.10)",
    warning="#F1BE67",
    success="#6FE39A",
    hover_bg="rgba(255, 255, 255, 0.05)",
    groove_bg="#22334C",
    handle_bg="#B8FFFF",
    sel_bg="#134E4A",
    scroll_handle="#3B4E6B",
    scroll_handle_hover="#4E6787",
    shadow="rgba(0, 0, 0, 0.35)",
)

GRAPHITE = Theme(
    name="石墨灰",
    kind="dark",
    bg="#0F1115",
    panel="#16191E",
    sidebar="#12151A",
    titlebar="#16191E",
    card="#1A1E24",
    card_soft="#20242C",
    input="#191C22",
    border="#2A2F38",
    border_soft="#232830",
    text="#E8EAED",
    text_dim="#9AA2AC",
    text_soft="#6E7681",
    accent="#14B8A6",
    accent_soft="#2DD4BF",
    accent_deep="#0D9488",
    grad_a="#2DD4BF",
    grad_b="#0D9488",
    on_accent="#062E2B",
    accent_tint="rgba(20, 184, 166, 0.14)",
    accent_tint_border="rgba(20, 184, 166, 0.36)",
    danger="#F87171",
    danger_tint="rgba(248, 113, 113, 0.10)",
    warning="#FBBF24",
    success="#2DD4BF",
    hover_bg="rgba(255, 255, 255, 0.05)",
    groove_bg="#2A2F38",
    handle_bg="#EAF8F1",
    sel_bg="#0F3B34",
    scroll_handle="#3A404A",
    scroll_handle_hover="#4E5661",
    shadow="rgba(0, 0, 0, 0.35)",
)

PRESETS = {"深海蓝": DARK, "石墨灰": GRAPHITE}
DEFAULT_DARK = "深海蓝"
DEFAULT_ALT = "石墨灰"

def get_preset(name: str) -> Theme:
    return PRESETS.get(name, DARK)

def preset_names() -> list:
    return list(PRESETS.keys())

ACCENTS = {
    "青绿": {
        "light": {"accent": "#0D9488", "accent_soft": "#14B8A6", "accent_deep": "#0F766E",
                  "grad_a": "#2DD4BF", "grad_b": "#0D9488", "on_accent": "#FFFFFF",
                  "accent_tint": "rgba(13,148,136,0.10)", "accent_tint_border": "rgba(13,148,136,0.30)",
                  "sel_bg": "#E3F1EC", "success": "#0D9488"},
        "dark": {"accent": "#2DD4BF", "accent_soft": "#5EEAD4", "accent_deep": "#0D9488",
                 "grad_a": "#5EEAD4", "grad_b": "#0D9488", "on_accent": "#062E2B",
                 "accent_tint": "rgba(45,212,191,0.14)", "accent_tint_border": "rgba(45,212,191,0.38)",
                 "sel_bg": "#134E4A", "success": "#6FE39A"},
    },
    "蓝色": {
        "light": {"accent": "#2563EB", "accent_soft": "#3B82F6", "accent_deep": "#1D4ED8",
                  "grad_a": "#60A5FA", "grad_b": "#2563EB", "on_accent": "#FFFFFF",
                  "accent_tint": "rgba(37,99,235,0.10)", "accent_tint_border": "rgba(37,99,235,0.30)",
                  "sel_bg": "#E3EBFA", "success": "#2563EB"},
        "dark": {"accent": "#60A5FA", "accent_soft": "#93C5FD", "accent_deep": "#2563EB",
                 "grad_a": "#93C5FD", "grad_b": "#2563EB", "on_accent": "#0B1E45",
                 "accent_tint": "rgba(96,165,250,0.14)", "accent_tint_border": "rgba(96,165,250,0.38)",
                 "sel_bg": "#1E3A8A", "success": "#93C5FD"},
    },
}

CUSTOM_ACCENT_FLAG = "自定义"

def accent_names() -> list:
    return list(ACCENTS.keys())

def is_hex_color(value) -> bool:

    if not isinstance(value, str) or not value.startswith("#"):
        return False
    if len(value.lstrip("#")) not in (3, 6):
        return False
    try:
        _hex_to_rgb(value)
        return True
    except ValueError:
        return False

def is_custom_accent(name) -> bool:
    return is_hex_color(name)

def is_valid_accent(name) -> bool:

    if name in ACCENTS:
        return True
    if is_custom_accent(name):
        try:
            _hex_to_rgb(name)
            return True
        except ValueError:
            return False
    return False

def _hex_to_rgb(hex_color: str):
    h = hex_color.lstrip("#")
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    if len(h) != 6:
        raise ValueError(f"无效的十六进制颜色: {hex_color}")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    if not (0 <= r <= 255 and 0 <= g <= 255 and 0 <= b <= 255):
        raise ValueError(f"无效的十六进制颜色: {hex_color}")
    return r, g, b

def _rgb_to_hex(r, g, b) -> str:
    return f"#{int(round(r)):02X}{int(round(g)):02X}{int(round(b)):02X}"

def _mix_hex(hex1: str, hex2: str, t: float) -> str:

    r1, g1, b1 = _hex_to_rgb(hex1)
    r2, g2, b2 = _hex_to_rgb(hex2)
    k = max(0.0, min(1.0, float(t)))
    return _rgb_to_hex(r1 + (r2 - r1) * k,
                       g1 + (g2 - g1) * k,
                       b1 + (b2 - b1) * k)

def _luminance(hex_color: str) -> float:

    r, g, b = _hex_to_rgb(hex_color)
    return (0.2126 * r + 0.7152 * g + 0.0722 * b) / 255.0

def custom_accent(hex_color: str, kind: str, bg: str) -> dict:

    base = hex_color.upper()
    if kind == "dark":
        soft = _mix_hex(base, "#FFFFFF", 0.42)
        deep = _mix_hex(base, "#000000", 0.22)
        grad_a = _mix_hex(base, "#FFFFFF", 0.30)
        tint_a, tint_b = 0.16, 0.42
        sel_t = 0.24
    else:
        soft = _mix_hex(base, "#FFFFFF", 0.32)
        deep = _mix_hex(base, "#000000", 0.16)
        grad_a = _mix_hex(base, "#FFFFFF", 0.48)
        tint_a, tint_b = 0.12, 0.32
        sel_t = 0.10
    r, g, b = _hex_to_rgb(base)
    return {
        "accent": base,
        "accent_soft": soft,
        "accent_deep": deep,
        "grad_a": grad_a,
        "grad_b": base,
        "on_accent": "#FFFFFF" if _luminance(base) < 0.55 else "#0A2E2B",
        "accent_tint": f"rgba({r},{g},{b},{tint_a})",
        "accent_tint_border": f"rgba({r},{g},{b},{tint_b})",
        "sel_bg": _mix_hex(bg, base, sel_t),
        "success": base,
    }

def preset_accent_token(name: str, kind: str = "dark") -> str:

    accent = ACCENTS.get(name)
    if not accent:
        return "#0D9488"
    return accent.get(kind, accent["dark"]).get("accent", "#0D9488")

def apply_accent(theme: Theme, accent_name: str) -> Theme:

    if isinstance(accent_name, str) and is_valid_accent(accent_name):
        if is_custom_accent(accent_name):
            variant = custom_accent(accent_name, theme.kind, theme.bg)
        else:
            variant = ACCENTS.get(accent_name, ACCENTS["青绿"]).get(theme.kind,
                                                                    ACCENTS["青绿"]["dark"])
    else:
        variant = ACCENTS["青绿"].get(theme.kind, ACCENTS["青绿"]["dark"])
    result = Theme(theme.name, theme.kind, **{k: v for k, v in theme.__dict__.items()
                                              if k not in ("name", "kind")})
    for key, value in variant.items():
        setattr(result, key, value)
    return result

def _to_rgba(hex_color: str, alpha: float) -> str:

    h = hex_color.lstrip("#")
    if len(h) != 6:
        return hex_color
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return f"rgba({r},{g},{b},{alpha:.2f})"

def glass_theme(theme: Theme, alpha: float = 0.72) -> Theme:

    result = Theme(theme.name, theme.kind, **{k: v for k, v in theme.__dict__.items()
                                              if k not in ("name", "kind")})
    for key in ("bg", "panel", "sidebar", "titlebar"):
        setattr(result, key, _to_rgba(getattr(result, key), alpha))
    for key in ("card", "card_soft", "input"):
        setattr(result, key, _to_rgba(getattr(result, key), min(1.0, alpha + 0.10)))
    return result

def _dim_hex(hex_color: str, factor: float) -> str:

    h = hex_color.lstrip("#")
    if len(h) != 6:
        return hex_color
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    k = max(0.0, min(1.0, float(factor)))
    return f"#{int(r * (1 - k)):02X}{int(g * (1 - k)):02X}{int(b * (1 - k)):02X}"

def dim_accent(theme: Theme, factor: float) -> Theme:

    result = Theme(theme.name, theme.kind, **{k: v for k, v in theme.__dict__.items()
                                              if k not in ("name", "kind")})
    for key in ("accent", "accent_soft", "accent_deep", "grad_a", "grad_b", "success"):
        setattr(result, key, _dim_hex(getattr(result, key), factor))
    return result

def _lighten_hex(hex_color: str, factor: float) -> str:

    h = hex_color.lstrip("#")
    if len(h) != 6:
        return hex_color
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    k = max(0.0, min(1.0, float(factor)))
    r = int(r + (255 - r) * k)
    g = int(g + (255 - g) * k)
    b = int(b + (255 - b) * k)
    return f"#{r:02X}{g:02X}{b:02X}"

def brighten_text(theme: Theme, factor: float = 0.32) -> Theme:

    result = Theme(theme.name, theme.kind, **{k: v for k, v in theme.__dict__.items()
                                              if k not in ("name", "kind")})
    result.text_dim = _lighten_hex(result.text_dim, factor)
    result.text_soft = _lighten_hex(result.text_soft, factor)
    return result

def scrollbar_qss(theme: Theme, width: int = 10, radius: int = 5) -> str:
    return f"""
    QScrollBar:vertical {{
        border: none; background: transparent; width: {width}px;
        margin: 6px 2px 6px 0; border-radius: {radius}px;
    }}
    QScrollBar::handle:vertical {{
        background: {theme.scroll_handle}; min-height: 32px; border-radius: {radius}px;
    }}
    QScrollBar::handle:vertical:hover {{
        background: {theme.scroll_handle_hover};
    }}
    QScrollBar:horizontal {{
        border: none; background: transparent; height: {width}px;
        margin: 0 6px 2px 6px; border-radius: {radius}px;
    }}
    QScrollBar::handle:horizontal {{
        background: {theme.scroll_handle}; min-width: 32px; border-radius: {radius}px;
    }}
    QScrollBar::handle:horizontal:hover {{
        background: {theme.scroll_handle_hover};
    }}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical,
    QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
        width: 0px; height: 0px; border: none; background: transparent;
    }}
    QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical,
    QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal,
    QScrollBar::up-arrow:vertical, QScrollBar::down-arrow:vertical,
    QScrollBar::left-arrow:horizontal, QScrollBar::right-arrow:horizontal {{
        background: transparent; border: none; width: 0px; height: 0px;
    }}
    """

def build_stylesheet(theme: Theme) -> str:
    t = theme
    return f"""
    * {{
        font-family: 'Microsoft YaHei UI', 'Segoe UI', 'PingFang SC', sans-serif;
        font-size: 13px;
    }}
    QMainWindow, QWidget#appRoot {{
        background: transparent;
    }}
    QDialog {{
        background: {t.panel}; color: {t.text};
    }}
    QToolTip {{
        background: {t.panel}; color: {t.text};
        border: 1px solid {t.border}; border-radius: 8px; padding: 6px 10px; font-size: 12px;
    }}

    /* ---------- 容器 ---------- */
    QFrame[panel="1"] {{
        background: {t.panel}; border: 1px solid {t.border}; border-radius: 20px;
    }}
    QFrame[sidebar="1"] {{
        background: {t.sidebar}; border: 1px solid {t.border}; border-radius: 18px;
    }}
    QFrame[card="1"] {{
        background: {t.card}; border: 1px solid {t.border}; border-radius: 14px;
    }}
    QFrame[card="2"] {{
        background: {t.card_soft}; border: 1px solid {t.border_soft}; border-radius: 13px;
    }}
    QFrame[titlebar="1"] {{
        background: transparent; border: none;
    }}

    /* ---------- 标签 ---------- */
    QLabel[role="headline"] {{
        background: transparent; border: none; color: {t.text};
        font-size: 21px; font-weight: 800;
    }}
    QLabel[role="subtitle"] {{
        background: transparent; border: none; color: {t.text_dim}; font-size: 12px;
    }}
    QLabel[role="section"] {{
        background: transparent; border: none; color: {t.text};
        font-size: 15px; font-weight: 800;
    }}
    QLabel[role="stat"] {{
        background: transparent; border: none; color: {t.text};
        font-size: 23px; font-weight: 900;
    }}
    QLabel[role="desc"] {{
        background: transparent; border: none; color: {t.text_soft}; font-size: 12px;
    }}
    QLabel[role="pill"] {{
        background: {t.sel_bg}; color: {t.accent};
        border: 1px solid {t.accent_tint_border}; border-radius: 11px;
        padding: 3px 12px; font-size: 14px; font-weight: 800;
    }}
    QLabel[role="pill-big"] {{
        background: {t.sel_bg}; color: {t.accent};
        border: 1px solid {t.accent_tint_border}; border-radius: 12px;
        padding: 5px 14px; font-size: 18px; font-weight: 900;
    }}
    QLabel[role="tag"] {{
        background: {t.sel_bg}; color: {t.accent};
        border: 1px solid {t.accent_tint_border}; border-radius: 9px;
        padding: 2px 10px; font-size: 12px; font-weight: 700;
    }}
    QLabel[role="status-ok"] {{
        background: transparent; border: none; color: {t.success}; font-size: 13px; font-weight: 800;
    }}
    QLabel[role="status-err"] {{
        background: transparent; border: none; color: {t.danger}; font-size: 13px; font-weight: 800;
    }}
    QLabel[role="status-run"] {{
        background: transparent; border: none; color: {t.warning}; font-size: 13px; font-weight: 800;
    }}

    /* ---------- 按钮 ---------- */
    QPushButton[type="primary"] {{
        background: {t.accent}; color: {t.on_accent};
        border: none; border-radius: 12px; min-height: 40px; padding: 0 22px;
        font-size: 14px; font-weight: 800;
    }}
    QPushButton[type="primary"]:hover {{ background: {t.accent_soft}; }}
    QPushButton[type="primary"]:pressed {{ background: {t.accent_deep}; }}
    QPushButton[type="primary"]:disabled {{
        background: {t.groove_bg}; color: {t.text_soft};
    }}
    QPushButton[type="secondary"] {{
        background: transparent; color: {t.text_dim};
        border: 1px solid {t.border}; border-radius: 11px;
        min-height: 36px; padding: 0 16px; font-size: 13px; font-weight: 700;
    }}
    QPushButton[type="secondary"]:hover {{
        color: {t.text}; border: 1px solid {t.accent}; background: {t.hover_bg};
    }}
    QPushButton[type="secondary"]:pressed {{ background: {t.accent_tint}; }}
    QPushButton[type="secondary"]:disabled {{ color: {t.text_soft}; border-color: {t.border}; }}
    QPushButton[type="danger"] {{
        background: transparent; color: {t.danger};
        border: 1px solid {t.danger}; border-radius: 11px;
        min-height: 36px; padding: 0 16px; font-size: 13px; font-weight: 700;
    }}
    QPushButton[type="danger"]:hover {{ background: {t.danger_tint}; }}
    QPushButton[type="danger"]:disabled {{ color: {t.text_soft}; border-color: {t.border}; }}
    QPushButton[type="ghost"] {{
        background: transparent; color: {t.text_dim};
        border: 1px solid {t.border}; border-radius: 9px;
        min-height: 30px; padding: 0 12px; font-size: 12px; font-weight: 700;
    }}
    QPushButton[type="ghost"]:hover {{ color: {t.text}; border-color: {t.accent}; }}
    QPushButton[type="link"] {{
        background: transparent; color: {t.accent};
        border: none; text-align: left; padding: 0;
        font-size: 13px; font-weight: 800;
    }}
    QPushButton[type="link"]:hover {{ color: {t.accent_soft}; }}

    /* 侧边栏导航 */
    QPushButton[nav="1"] {{
        text-align: left; padding: 0 16px; min-height: 42px;
        border-radius: 12px; background: transparent;
        border: 1px solid transparent; color: {t.text_dim};
        font-size: 14px; font-weight: 700;
    }}
    QPushButton[nav="1"]:hover {{ background: {t.hover_bg}; color: {t.text}; }}
    QPushButton[nav="1"]:checked {{
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
            stop:0 {t.grad_a}, stop:1 {t.grad_b});
        color: {t.on_accent}; border: 1px solid {t.grad_b};
    }}

    /* ---------- 输入控件 ---------- */
    QLineEdit[field="1"], QSpinBox, QDoubleSpinBox, QComboBox[field="1"] {{
        background: {t.input}; color: {t.text};
        border: 1px solid {t.border}; border-radius: 10px;
        padding: 0 12px; min-height: 36px; font-size: 13px;
        selection-background-color: {t.accent}; selection-color: {t.on_accent};
    }}
    QLineEdit[field="1"]:focus, QSpinBox:focus, QDoubleSpinBox:focus,
    QComboBox[field="1"]:focus {{ border: 1px solid {t.accent}; }}
    QLineEdit[field="1"]:disabled, QSpinBox:disabled, QDoubleSpinBox:disabled {{
        color: {t.text_soft}; background: {t.card_soft};
    }}
    QLineEdit[field="1"]::placeholder {{ color: {t.text_soft}; }}
    /* 隐藏数字输入框原生的增减按钮（避免出现白色方块），数值直接键入 */
    QSpinBox::up-button, QDoubleSpinBox::up-button,
    QSpinBox::down-button, QDoubleSpinBox::down-button {{
        width: 0px; height: 0px; border: none; background: transparent;
    }}

    /* 下拉框：隐藏原生指示器，箭头由 FieldComboBox 自行绘制 */
    QComboBox[field="1"]::drop-down {{ border: none; width: 0px; }}
    QComboBox[field="1"]::down-arrow {{
        image: none; width: 0px; height: 0px; border: none;
    }}
    QComboBox[field="1"] QAbstractItemView {{
        background: {t.panel}; color: {t.text};
        border: 1px solid {t.border}; border-radius: 10px;
        selection-background-color: {t.accent_tint};
        selection-color: {t.text}; padding: 4px;
        outline: none;
    }}
    QComboBox[field="1"] QAbstractItemView::item {{
        min-height: 30px; padding: 0 10px; border-radius: 7px;
    }}
    QComboBox[field="1"] QAbstractItemView::item:selected {{
        background: {t.accent_tint}; color: {t.accent}; font-weight: 700;
    }}

    /* ---------- 滑块 ---------- */
    QSlider[slider="1"]::groove:horizontal {{
        height: 8px; border-radius: 4px; background: {t.groove_bg};
    }}
    QSlider[slider="1"]::sub-page:horizontal {{
        background: {t.accent}; border-radius: 4px;
    }}
    QSlider[slider="1"]::add-page:horizontal {{
        background: {t.groove_bg}; border-radius: 4px;
    }}
    QSlider[slider="1"]::handle:horizontal {{
        width: 18px; height: 18px; margin: -5px 0;
        border-radius: 9px; background: {t.handle_bg};
        border: 2px solid {t.accent};
    }}
    QSlider[slider="1"]::handle:horizontal:hover {{
        background: {t.accent_soft};
    }}

    /* ---------- 进度条 ---------- */
    QProgressBar[bar="1"] {{
        background: {t.groove_bg}; border: none; border-radius: 8px;
        min-height: 17px; text-align: center; color: {t.text}; font-size: 11px; font-weight: 700;
    }}
    QProgressBar[bar="1"]::chunk {{
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
            stop:0 {t.grad_a}, stop:1 {t.grad_b});
        border-radius: 8px;
    }}

    /* ---------- 日志文本框 ---------- */
    QTextEdit[log="1"] {{
        background: {t.input}; color: {t.text};
        border: 1px solid {t.border}; border-radius: 14px; padding: 12px;
        font-family: 'Consolas', 'Courier New', 'Microsoft YaHei UI', monospace;
        font-size: 12.5px;
        selection-background-color: {t.accent}; selection-color: {t.on_accent};
    }}

    /* ---------- 滚动区域 ---------- */
    QScrollArea {{ border: none; background: transparent; }}
    QScrollArea > QWidget > QWidget {{ background: transparent; }}
    {scrollbar_qss(t)}
    """