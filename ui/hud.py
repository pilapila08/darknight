"""游戏HUD（经验条和生命条）"""
import pygame
from settings import DARK_GRAY, GOLD, WHITE, RED, GREEN


def draw_hud(screen, font, level, experience, xp_to_next, player_hp, player_max_hp, elapsed_time=0):
    """绘制游戏HUD（经验条和生命条）"""
    sw = screen.get_width()
    bar_width = sw // 2
    bar_height = 14
    bar_x = (sw - bar_width) // 2

    # 经验条
    xp_y = 8
    level_text = font.render(f"Lv.{level}", True, WHITE)
    screen.blit(level_text, (bar_x - 60, xp_y - 2))
    pygame.draw.rect(screen, DARK_GRAY, (bar_x, xp_y, bar_width, bar_height))
    fill_width = int(bar_width * (experience / max(1, xp_to_next)))
    if fill_width > 0:
        pygame.draw.rect(screen, GOLD, (bar_x, xp_y, fill_width, bar_height))
    # 显示当前/总经验
    xp_needed = xp_to_next - experience
    xp_info_text = font.render(f"{xp_needed}", True, WHITE)
    screen.blit(xp_info_text, (bar_x + bar_width + 8, xp_y - 2))

    # 生命条
    hp_y = xp_y + bar_height + 4
    hp_text = font.render("生命", True, WHITE)
    screen.blit(hp_text, (bar_x - 40, hp_y - 2))
    pygame.draw.rect(screen, DARK_GRAY, (bar_x, hp_y, bar_width, bar_height))
    hp_fill = int(bar_width * (player_hp / player_max_hp))
    if hp_fill > 0:
        hp_color = RED if player_hp <= player_max_hp * 0.3 else GREEN
        pygame.draw.rect(screen, hp_color, (bar_x, hp_y, hp_fill, bar_height))

    # 右上角显示游戏时间
    minutes = int(elapsed_time // 60)
    seconds = int(elapsed_time % 60)
    time_text = font.render(f"{minutes:02d}:{seconds:02d}", True, WHITE)
    screen.blit(time_text, (sw - 60, 8))
