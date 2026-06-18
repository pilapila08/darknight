"""游戏HUD（经验条和生命条）"""
import pygame
from settings import DARK_GRAY, GOLD, WHITE, RED, GREEN


def _draw_status_bar(screen, rect, fill_ratio, fill_color, border_color):
    fill_ratio = max(0.0, min(1.0, fill_ratio))
    pygame.draw.rect(screen, (10, 10, 14), rect.inflate(8, 8), border_radius=8)
    pygame.draw.rect(screen, DARK_GRAY, rect, border_radius=6)
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

    # 经验条
    xp_y = 8
    xp_rect = pygame.Rect(bar_x, xp_y, bar_width, bar_height)
    level_text = font.render(f"Lv {level}", True, GOLD)
    screen.blit(level_text, (bar_x - 66, xp_y - 3))
    _draw_status_bar(screen, xp_rect, experience / max(1, xp_to_next), GOLD, (170, 130, 45))
    # 显示当前/总经验
    xp_needed = xp_to_next - experience
    xp_info_text = font.render(f"{max(0, xp_needed):.0f}", True, WHITE)
    screen.blit(xp_info_text, (bar_x + bar_width + 8, xp_y - 2))

    # 生命条
    hp_y = xp_y + bar_height + 7
    hp_rect = pygame.Rect(bar_x, hp_y, bar_width, bar_height)
    hp_text = font.render(f"HP {player_hp:.0f}/{player_max_hp:.0f}", True, WHITE)
    screen.blit(hp_text, (bar_x - 92, hp_y - 3))
    hp_color = RED if player_hp <= player_max_hp * 0.3 else GREEN
    _draw_status_bar(screen, hp_rect, player_hp / max(1, player_max_hp), hp_color,
                     (130, 45, 45) if hp_color == RED else (45, 130, 80))

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
