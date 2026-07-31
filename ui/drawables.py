"""基础绘制工具和技能图标"""
import math
import os
import sys
import pygame


def _resource_path(relative_path):
    base = getattr(sys, "_MEIPASS", os.path.abspath("."))
    return os.path.join(base, relative_path)


_FONT_CACHE = {}
_CUSTOM_FONT_PATH = None
_CUSTOM_FONT_CHECKED = False


def _find_custom_font():
    """查找 assets/fonts 下的自定义字体（放入 ttf/otf 即自动生效）"""
    global _CUSTOM_FONT_PATH, _CUSTOM_FONT_CHECKED
    if _CUSTOM_FONT_CHECKED:
        return _CUSTOM_FONT_PATH
    _CUSTOM_FONT_CHECKED = True
    fonts_dir = _resource_path(os.path.join("assets", "fonts"))
    if os.path.isdir(fonts_dir):
        for name in sorted(os.listdir(fonts_dir)):
            if name.lower().endswith((".ttf", ".otf", ".ttc")):
                _CUSTOM_FONT_PATH = os.path.join(fonts_dir, name)
                break
    return _CUSTOM_FONT_PATH


def get_font(size, bold=False):
    """获取支持中文的字体（带缓存；优先 assets/fonts 自定义字体）"""
    key = (size, bold)
    font = _FONT_CACHE.get(key)
    if font is not None:
        return font

    custom = _find_custom_font()
    if custom:
        try:
            font = pygame.font.Font(custom, size)
            font.set_bold(bold)
        except Exception:
            font = None
    if font is None:
        for name in ("microsoft yahei", "simhei", "simsun", "noto sans cjk sc",
                     "wenquanyi micro hei", "arial unicode ms", "ms gothic"):
            try:
                font = pygame.font.SysFont(name, size, bold=bold)
                break
            except Exception:
                continue
    if font is None:
        font = pygame.font.Font(None, size)
    _FONT_CACHE[key] = font
    return font


def draw_skill_icon_shape(screen, x, y, size, icon_info):
    """绘制技能图标的形状"""
    cx, cy = x + size // 2, y + size // 2
    color = icon_info["color"]
    glow = icon_info["glow"]
    shape = icon_info["shape"]

    if shape == "arrow_up":
        points = [(cx, y + 6), (x + size - 6, y + size - 8), (cx, y + size - 14), (x + 6, y + size - 8)]
        pygame.draw.polygon(screen, color, points)
        pygame.draw.rect(screen, color, (x + 8, y + size - 12, size - 16, 5), border_radius=2)

    elif shape == "lightning":
        points = [(cx + 4, y + 4), (cx - 6, cy), (cx + 2, cy), (cx - 4, y + size - 4), (cx + 6, cy - 4), (cx, cy - 4)]
        pygame.draw.polygon(screen, color, points)

    elif shape == "speed":
        for i in range(3):
            offset = i * 5
            pygame.draw.line(screen, color, (x + 8 + offset, y + 10 + i * 8), (x + size - 8 - offset, y + 10 + i * 8), 3)

    elif shape == "triple":
        for i in range(3):
            y_pos = y + 10 + i * 7
            pygame.draw.ellipse(screen, color, (x + 8, y_pos, size - 16, 5))

    elif shape == "magnet":
        pygame.draw.arc(screen, color, (x + 6, y + 6, size - 12, size - 12), 3.14, 0, 4)
        pygame.draw.rect(screen, color, (x + 6, cy - 2, 8, size // 3))
        pygame.draw.rect(screen, glow, (x + size - 14, cy - 2, 8, size // 3))

    elif shape == "snowflake":
        for i in range(6):
            angle = i * 1.047
            end_x = cx + int((size // 2 - 5) * math.sin(angle))
            end_y = cy - int((size // 2 - 5) * math.cos(angle))
            pygame.draw.line(screen, color, (cx, cy), (end_x, end_y), 2)
            ex1 = cx + int(4 * math.sin(angle + 0.5))
            ey1 = cy - int(4 * math.cos(angle + 0.5))
            ex2 = cx + int(4 * math.sin(angle - 0.5))
            ey2 = cy - int(4 * math.cos(angle - 0.5))
            pygame.draw.line(screen, color, (end_x, end_y), (ex1, ey1), 1)
            pygame.draw.line(screen, color, (end_x, end_y), (ex2, ey2), 1)

    elif shape == "crit":
        points = []
        for i in range(5):
            outer_angle = i * 2 * math.pi / 5 - math.pi / 2
            inner_angle = outer_angle + math.pi / 5
            outer_x = cx + int(12 * math.cos(outer_angle))
            outer_y = cy + int(12 * math.sin(outer_angle))
            inner_x = cx + int(5 * math.cos(inner_angle))
            inner_y = cy + int(5 * math.sin(inner_angle))
            if i == 0:
                points.append((outer_x, outer_y))
            else:
                points.append((inner_x, inner_y))
            points.append((outer_x, outer_y))
        points.append(points[0])
        if len(points) >= 3:
            pygame.draw.polygon(screen, color, points[:-1])

    elif shape == "heart":
        for i in range(size // 2 - 6):
            w = size - 12 - i * 2
            h = 6 + i
            pygame.draw.ellipse(screen, color, (cx - w // 2, y + 6 + i, w, h))

    elif shape == "blade":
        points = [(cx, y + 6), (x + size - 8, cy), (cx, y + size - 6), (x + 8, cy)]
        pygame.draw.polygon(screen, color, points)
        pygame.draw.line(screen, glow, (cx, y + 10), (cx, y + size - 10), 1)

    elif shape == "chain":
        for i in range(2):
            oy = y + 10 + i * 12
            pygame.draw.ellipse(screen, color, (cx - 8, oy, 16, 8), 3)
        pygame.draw.line(screen, color, (cx, y + 14), (cx, y + size - 14), 2)

    elif shape == "trap":
        pygame.draw.circle(screen, color, (cx, cy), size // 3, 3)
        pygame.draw.circle(screen, glow, (cx, cy), size // 5)
        pygame.draw.circle(screen, color, (cx, cy), 3)

    elif shape == "shield":
        points = [
            (cx, y + 6),
            (x + size - 8, y + 12),
            (x + size - 8, y + size // 2),
            (cx, y + size - 6),
            (x + 8, y + size // 2),
            (x + 8, y + 12),
        ]
        pygame.draw.polygon(screen, color, points)
        pygame.draw.polygon(screen, glow, [
            (cx, y + 10),
            (x + size - 12, y + 14),
            (x + size - 12, y + size // 2 - 2),
            (cx, y + size - 10),
            (x + 12, y + size // 2 - 2),
            (x + 12, y + 14),
        ])

    elif shape == "coin":
        pygame.draw.circle(screen, color, (cx, cy), size // 3)
        pygame.draw.circle(screen, glow, (cx, cy), size // 4)
        pygame.draw.circle(screen, color, (cx, cy), 3)

    elif shape == "arrow_right":
        points = [(x + 6, cy), (x + size - 10, cy), (x + size - 10, y + 8), (x + size - 4, cy), (x + size - 10, y + size - 8), (x + size - 10, cy)]
        pygame.draw.polygon(screen, color, points)


# 技能图标配置
SKILL_ICONS = {
    "火力增强": {
        "color": (220, 60, 60), "glow": (255, 100, 100),
        "shape": "arrow_up", "border": (180, 40, 40),
    },
    "急速射击": {
        "color": (255, 180, 50), "glow": (255, 220, 100),
        "shape": "lightning", "border": (200, 140, 30),
    },
    "凌波微步": {
        "color": (60, 180, 255), "glow": (120, 210, 255),
        "shape": "speed", "border": (40, 140, 200),
    },
    "贪婪之魂": {
        "color": (255, 215, 0), "glow": (255, 245, 150),
        "shape": "coin", "border": (200, 170, 0),
    },
    "急速子弹": {
        "color": (100, 255, 200), "glow": (180, 255, 230),
        "shape": "arrow_right", "border": (70, 200, 150),
    },
    "增加弹量": {
        "color": (255, 130, 50), "glow": (255, 180, 100),
        "shape": "triple", "border": (200, 100, 30),
    },
    "致命节奏": {
        "color": (255, 80, 140), "glow": (255, 150, 180),
        "shape": "crit", "border": (200, 50, 100),
    },
    "复苏之风": {
        "color": (80, 220, 120), "glow": (140, 255, 170),
        "shape": "heart", "border": (50, 180, 90),
    },
    "暗影新星": {
        "color": (150, 110, 255), "glow": (220, 205, 255),
        "shape": "trap", "border": (110, 80, 190),
    },
    "连锁闪电": {
        "color": (80, 180, 255), "glow": (150, 220, 255),
        "shape": "chain", "border": (50, 140, 200),
    },
    "剧毒地雷": {
        "color": (80, 200, 100), "glow": (140, 240, 150),
        "shape": "trap", "border": (50, 160, 70),
    },
    "钢铁意志": {
        "color": (150, 150, 180), "glow": (200, 200, 220),
        "shape": "shield", "border": (100, 100, 130),
    },
}
