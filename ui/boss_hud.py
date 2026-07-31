"""Boss HP bar rendering."""
import pygame
from settings import WHITE, GOLD, RED, DARK_GRAY

# 血条动画状态：登场展开 + 掉血延迟条
_state = {"boss_id": None, "reveal": 0.0, "ghost": 1.0, "last_ms": 0}


def draw_boss_hp_bar(screen, font, boss):
    """Draw boss name and HP bar at top center of screen."""
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
    pygame.draw.rect(screen, (35, 37, 46), bar_rect, border_radius=6)

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
    hp_color = RED if hp_ratio < 0.3 else GOLD
    if fill_width > 0:
        fill_rect = pygame.Rect(bar_x, bar_y, fill_width, bar_height)
        pygame.draw.rect(screen, hp_color, fill_rect, border_radius=6)
        shine = fill_rect.copy()
        shine.height = max(2, bar_height // 3)
        pygame.draw.rect(screen, (255, 255, 255, 34), shine, border_radius=5)

    pygame.draw.rect(screen, GOLD, bar_rect, 2, border_radius=6)

    hp_text = font.render(str(max(0, int(boss.hp))) + "/" + str(int(boss.max_hp)), True, WHITE)
    hp_rect = hp_text.get_rect(center=(sw // 2, bar_y + bar_height // 2))
    screen.blit(hp_text, hp_rect)
