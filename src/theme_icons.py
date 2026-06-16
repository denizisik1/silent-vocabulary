from PySide6.QtCore import QPointF, Qt
from PySide6.QtGui import QColor, QIcon, QPainter, QPen, QPixmap

_SUN = QColor("#d4a017")
_MOON = QColor("#b0bcc8")
_DISK_LIGHT = QColor("#e8e8e8")
_DISK_DARK = QColor("#2a2a2a")

THEME_ORDER = ("white", "gray", "dark")
THEME_BUTTON = "toolButton_theme"

_TOOLTIPS = {
    "white": "Theme: White",
    "gray": "Theme: Gray",
    "dark": "Theme: Dark",
}


def _new_pixmap(size: int) -> tuple[QPixmap, QPainter]:
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    return pixmap, painter


def _draw_sun(painter: QPainter, size: int) -> None:
    center = size / 2
    radius = size * 0.22
    ray_inner = size * 0.32
    ray_outer = size * 0.46
    painter.setPen(
        QPen(_SUN, max(1.5, size * 0.08), Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
    )
    for index in range(8):
        angle = index * 45
        painter.save()
        painter.translate(center, center)
        painter.rotate(angle)
        painter.drawLine(QPointF(0, -ray_inner), QPointF(0, -ray_outer))
        painter.restore()
    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(_SUN)
    painter.drawEllipse(QPointF(center, center), radius, radius)


def _draw_moon(painter: QPainter, size: int) -> None:
    center = size / 2
    radius = size * 0.32
    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(_MOON)
    painter.drawEllipse(QPointF(center, center), radius, radius)
    painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_Clear)
    painter.drawEllipse(
        QPointF(center + size * 0.14, center - size * 0.08),
        radius * 0.88,
        radius * 0.88,
    )


def _draw_half(painter: QPainter, size: int) -> None:
    center = size / 2
    radius = size * 0.36
    painter.setPen(QPen(_MOON, max(1.0, size * 0.06)))
    painter.setBrush(_DISK_LIGHT)
    painter.drawEllipse(QPointF(center, center), radius, radius)
    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(_DISK_DARK)
    painter.drawChord(
        int(center - radius),
        int(center - radius),
        int(radius * 2),
        int(radius * 2),
        90 * 16,
        180 * 16,
    )


_DRAWERS = {
    "white": _draw_sun,
    "gray": _draw_half,
    "dark": _draw_moon,
}


def next_theme(theme_name: str) -> str:
    if theme_name not in THEME_ORDER:
        return THEME_ORDER[0]
    index = THEME_ORDER.index(theme_name)
    return THEME_ORDER[(index + 1) % len(THEME_ORDER)]


def theme_icon(theme_name: str, size: int = 18) -> QIcon:
    drawer = _DRAWERS.get(theme_name)
    if drawer is None:
        return QIcon()
    pixmap, painter = _new_pixmap(size)
    drawer(painter, size)
    painter.end()
    return QIcon(pixmap)


def theme_tooltip(theme_name: str) -> str:
    return _TOOLTIPS.get(theme_name, theme_name)
