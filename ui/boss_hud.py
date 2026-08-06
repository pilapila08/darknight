"""Boss HP bar rendering."""
import math
import pygame
from settings import WHITE, GOLD, RED, DARK_GRAY

# 血条动画状态：登场展开 + 掉血延迟条
_state = {"boss_id": None, "reveal": 0.0, "ghost": 1.0, "last_ms": 0}


def draw_boss_hp_bar(screen, font, boss):
    """Draw boss name and HP bar at top center of screen.

    R7 P0 (C02 §4.1 U3/U4)：
    - 阶段刻度：50% / 30% 竖线
    - 血条底色按 Boss 主题色（config.color 深色版）
    - <30% 红色脉动
    - 狂暴横幅（boss.enraged 时显示，配合游戏层 audio.duck）
    """
    sw = screen.get_width()
    bar_width = 400
    bar_height = 22
    bar_x = (sw - bar_width) // 2
    bar_y = 55

    now = pygame.time.get_ticks()
    dt = min(0.1, (now - _state["last_ms"]) / 1000.0) if _state["last_ms"] else 0.016
    _state["last_ms"] = now

    # 新 Boss 登场：血条从 0 展开
    if _state["boss_id"] != id(boss):
        _state["boss_id"] = id(boss)
        _state["reveal"] = 0.0
        _state["ghost"] = 1.0
    _state["reveal"] = min(1.0, _state["reveal"] + dt / 0.8)

    name_text = font.render(boss.config["name"], True, GOLD)
    name_rect = name_text.get_rect(center=(sw // 2, bar_y - 18))
    screen.blit(name_text, name_rect)

    bg_rect = pygame.Rect(bar_x - 10, bar_y - 8, bar_width + 20, bar_height + 16)
    pygame.draw.rect(screen, (8, 10, 16), bg_rect, border_radius=8)
    pygame.draw.rect(screen, (74, 66, 78), bg_rect, 1, border_radius=8)
    bar_rect = pygame.Rect(bar_x, bar_y, bar_width, bar_height)

    # U3 血条底色按 Boss 主题色（深色版）
    theme = boss.config.get("color", (200, 60, 60))
    theme_dark = tuple(max(12, int(c * 0.28)) for c in theme)
    pygame.draw.rect(screen, theme_dark, bar_rect, border_radius=6)

    hp_ratio = max(0, boss.hp / boss.max_hp)
    # 登场展开动画：显示比例受 reveal 限制
    shown_ratio = min(hp_ratio, _state["reveal"])

    # 延迟条：掉血后白色残段缓慢缩短
    if _state["ghost"] < shown_ratio:
        _state["ghost"] = shown_ratio
    elif _state["ghost"] > shown_ratio:
        _state["ghost"] = max(shown_ratio, _state["ghost"] - 0.25 * dt)
    ghost_width = int(bar_width * _state["ghost"])
    if ghost_width > 0:
        ghost_rect = pygame.Rect(bar_x, bar_y, ghost_width, bar_height)
        pygame.draw.rect(screen, (225, 225, 232), ghost_rect, border_radius=6)

    fill_width = int(bar_width * shown_ratio)
    # U3 低血脉动：<30% 红色脉动
    hp_color = RED if hp_ratio < 0.3 else GOLD
    if hp_ratio < 0.3:
        pulse = 0.6 + 0.4 * math.sin(now * 0.012)
        hp_color = tuple(min(255, int(c * pulse)) for c in RED)
    if fill_width > 0:
        fill_rect = pygame.Rect(bar_x, bar_y, fill_width, bar_height)
        pygame.draw.rect(screen, hp_color, fill_rect, border_radius=6)
        shine = fill_rect.copy()
        shine.height = max(2, bar_height // 3)
        pygame.draw.rect(screen, (255, 255, 255, 34), shine, border_radius=5)

    pygame.draw.rect(screen, GOLD, bar_rect, 2, border_radius=6)

    # U3 阶段刻度：50% / 30% 竖线
    for pct in (0.5, 0.3):
        x = bar_x + int(bar_width * pct)
        pygame.draw.line(screen, (10, 10, 14), (x, bar_y), (x, bar_y + bar_height), 2)

    hp_text = font.render(str(max(0, int(boss.hp))) + "/" + str(int(boss.max_hp)), True, WHITE)
    hp_rect = hp_text.get_rect(center=(sw // 2, bar_y + bar_height // 2))
    screen.blit(hp_text, hp_rect)

    # U4 狂暴横幅：Boss 进入狂暴（尸王 <50%）时血条下方弹出
    if getattr(boss, "enraged", False):
        banner_text = f"{boss.config['name']}狂暴"
        banner = font.render(banner_text, True, (255, 90, 50))
        banner_rect = banner.get_rect(center=(sw // 2, bar_y + bar_height + 18))
        pad = 8
        bg = pygame.Rect(banner_rect.x - pad, banner_rect.y - 3, banner_rect.w + pad * 2, banner_rect.h + 6)
        pygame.draw.rect(screen, (40, 8, 6), bg, border_radius=6)
        pygame.draw.rect(screen, (255, 90, 50), bg, 1, border_radius=6)
        screen.blit(banner, banner_rect)
