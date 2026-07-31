"""游戏HUD（经验条和生命条）"""
import math
import pygame
from settings import DARK_GRAY, GOLD, WHITE, RED, GREEN

# HUD 动效状态（延迟血条 / 升级闪光）
_state = {
    "ghost_hp": None,      # 延迟血条比例（掉血后慢慢追上当前值）
    "last_ms": 0,
    "prev_level": None,
    "xp_flash": 0.0,       # 升级时经验条闪光
}


def _draw_status_bar(screen, rect, fill_ratio, fill_color, border_color, ghost_ratio=None):
    fill_ratio = max(0.0, min(1.0, fill_ratio))
    pygame.draw.rect(screen, (10, 10, 14), rect.inflate(8, 8), border_radius=8)
    pygame.draw.rect(screen, DARK_GRAY, rect, border_radius=6)
    # 延迟条（白色残段，表现"刚掉了多少血"）
    if ghost_ratio is not None and ghost_ratio > fill_ratio:
        ghost_rect = rect.copy()
        ghost_rect.width = int(rect.width * min(1.0, ghost_ratio))
        pygame.draw.rect(screen, (235, 235, 240), ghost_rect, border_radius=6)
    if fill_ratio > 0:
        fill_rect = rect.copy()
        fill_rect.width = int(rect.width * fill_ratio)
        pygame.draw.rect(screen, fill_color, fill_rect, border_radius=6)
        shine = fill_rect.copy()
        shine.height = max(2, rect.height // 3)
        pygame.draw.rect(screen, (255, 255, 255, 36), shine, border_radius=5)
    pygame.draw.rect(screen, border_color, rect, 2, border_radius=6)


def draw_hud(screen, font, level, experience, xp_to_next, player_hp, player_max_hp,
             elapsed_time=0, player_shield=0, player_max_shield=0):
    """绘制游戏HUD（经验条和生命条）"""
    sw = screen.get_width()
    bar_width = sw // 2
    bar_height = 16
    bar_x = (sw - bar_width) // 2

    # 帧间隔（HUD 内部动效使用真实时间）
    now = pygame.time.get_ticks()
    dt = min(0.1, (now - _state["last_ms"]) / 1000.0) if _state["last_ms"] else 0.016
    _state["last_ms"] = now

    # 经验条
    xp_y = 8
    xp_rect = pygame.Rect(bar_x, xp_y, bar_width, bar_height)
    level_text = font.render(f"Lv {level}", True, GOLD)
    screen.blit(level_text, (bar_x - 66, xp_y - 3))
    _draw_status_bar(screen, xp_rect, experience / max(1, xp_to_next), GOLD, (170, 130, 45))

    # 升级闪光
    if _state["prev_level"] is None:
        _state["prev_level"] = level
    if level > _state["prev_level"]:
        _state["xp_flash"] = 1.0
        _state["ghost_hp"] = None  # 升级回血，重置延迟条
    _state["prev_level"] = level
    if _state["xp_flash"] > 0:
        flash = pygame.Surface((xp_rect.width + 8, xp_rect.height + 8), pygame.SRCALPHA)
        flash.fill((255, 245, 200, int(160 * _state["xp_flash"])))
        screen.blit(flash, (xp_rect.x - 4, xp_rect.y - 4))
        _state["xp_flash"] = max(0.0, _state["xp_flash"] - 2.5 * dt)

    # 显示当前/总经验
    xp_needed = xp_to_next - experience
    xp_info_text = font.render(f"{max(0, xp_needed):.0f}", True, WHITE)
    screen.blit(xp_info_text, (bar_x + bar_width + 8, xp_y - 2))

    # 生命条（带延迟条）
    hp_y = xp_y + bar_height + 7
    hp_rect = pygame.Rect(bar_x, hp_y, bar_width, bar_height)
    hp_text = font.render(f"HP {player_hp:.0f}/{player_max_hp:.0f}", True, WHITE)
    screen.blit(hp_text, (bar_x - 92, hp_y - 3))

    hp_ratio = max(0.0, player_hp / max(1, player_max_hp))
    if _state["ghost_hp"] is None or _state["ghost_hp"] < hp_ratio:
        _state["ghost_hp"] = hp_ratio
    elif _state["ghost_hp"] > hp_ratio:
        # 短暂停留后加速追上当前血量
        _state["ghost_hp"] = max(hp_ratio, _state["ghost_hp"] - 0.55 * dt)

    low_hp = player_hp <= player_max_hp * 0.3
    hp_color = RED if low_hp else GREEN
    if low_hp:
        # 低血量呼吸提亮
        pulse = 0.5 + 0.5 * math.sin(now * 0.012)
        hp_color = (255, int(50 + 70 * pulse), int(50 + 40 * pulse))
    _draw_status_bar(screen, hp_rect, hp_ratio, hp_color,
                     (130, 45, 45) if low_hp else (45, 130, 80),
                     ghost_ratio=_state["ghost_hp"])

    if player_max_shield > 0 and player_shield > 0:
        shield_y = hp_y + bar_height + 7
        shield_rect = pygame.Rect(bar_x, shield_y, bar_width, 10)
        shield_label = font.render(f"SH {player_shield:.0f}", True, (150, 225, 255))
        screen.blit(shield_label, (bar_x - 72, shield_y - 7))
        _draw_status_bar(screen, shield_rect, player_shield / max(1, player_max_shield),
                         (65, 185, 245), (55, 115, 165))

    # 右上角显示游戏时间（向左偏移以避免与FPS重叠）
    minutes = int(elapsed_time // 60)
    seconds = int(elapsed_time % 60)
    time_text = font.render(f"{minutes:02d}:{seconds:02d}", True, WHITE)
    time_rect = time_text.get_rect(topright=(sw - 54, 8))
    bg_rect = time_rect.inflate(16, 8)
    pygame.draw.rect(screen, (10, 10, 14), bg_rect, border_radius=6)
    pygame.draw.rect(screen, (90, 85, 105), bg_rect, 1, border_radius=6)
    screen.blit(time_text, time_rect)
