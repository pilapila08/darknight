"""暂停菜单"""
import pygame
from settings import BLACK, WHITE, GOLD, DARK_GRAY


def draw_pause_menu(screen, big_font, font, mouse_pos):
    """绘制暂停菜单"""
    overlay = pygame.Surface((screen.get_width(), screen.get_height()), pygame.SRCALPHA)
    overlay.fill((3, 5, 10, 185))
    screen.blit(overlay, (0, 0))

    panel = pygame.Rect(screen.get_width() // 2 - 170, screen.get_height() // 2 - 130, 340, 270)
    pygame.draw.rect(screen, (20, 23, 33), panel, border_radius=8)
    pygame.draw.rect(screen, (78, 88, 112), panel, 1, border_radius=8)

    title = big_font.render("游戏暂停", True, GOLD)
    title_rect = title.get_rect(center=(screen.get_width() // 2, panel.y + 58))
    screen.blit(title, title_rect)

    resume_rect = pygame.Rect(panel.x + 58, panel.y + 110, 224, 50)
    resume_color = GOLD if resume_rect.collidepoint(mouse_pos) else WHITE
    pygame.draw.rect(screen, (31, 35, 48), resume_rect, border_radius=8)
    pygame.draw.rect(screen, resume_color, resume_rect, 2, border_radius=8)
    resume_text = font.render("继续游戏 (1)", True, resume_color)
    resume_text_rect = resume_text.get_rect(center=resume_rect.center)
    screen.blit(resume_text, resume_text_rect)

    quit_rect = pygame.Rect(panel.x + 58, panel.y + 174, 224, 50)
    quit_color = GOLD if quit_rect.collidepoint(mouse_pos) else WHITE
    pygame.draw.rect(screen, (31, 35, 48), quit_rect, border_radius=8)
    pygame.draw.rect(screen, quit_color, quit_rect, 2, border_radius=8)
    quit_text = font.render("退出到主菜单", True, quit_color)
    quit_text_rect = quit_text.get_rect(center=quit_rect.center)
    screen.blit(quit_text, quit_text_rect)
