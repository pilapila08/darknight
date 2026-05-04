"""暂停菜单"""
import pygame
from settings import BLACK, WHITE, GOLD, DARK_GRAY


def draw_pause_menu(screen, big_font, font, mouse_pos):
    """绘制暂停菜单"""
    # 半透明遮罩
    overlay = pygame.Surface((screen.get_width(), screen.get_height()), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 150))
    screen.blit(overlay, (0, 0))

    # 暂停标题
    title = big_font.render("游戏暂停", True, GOLD)
    title_rect = title.get_rect(center=(screen.get_width() // 2, screen.get_height() // 2 - 80))
    screen.blit(title, title_rect)

    # 继续游戏按钮
    resume_rect = pygame.Rect(screen.get_width() // 2 - 100, screen.get_height() // 2, 200, 50)
    resume_color = GOLD if resume_rect.collidepoint(mouse_pos) else WHITE
    pygame.draw.rect(screen, DARK_GRAY, resume_rect, border_radius=8)
    pygame.draw.rect(screen, resume_color, resume_rect, 2, border_radius=8)
    resume_text = font.render("继续游戏 (1)", True, resume_color)
    resume_text_rect = resume_text.get_rect(center=resume_rect.center)
    screen.blit(resume_text, resume_text_rect)

    # 退出到主菜单按钮
    quit_rect = pygame.Rect(screen.get_width() // 2 - 100, screen.get_height() // 2 + 70, 200, 50)
    quit_color = GOLD if quit_rect.collidepoint(mouse_pos) else WHITE
    pygame.draw.rect(screen, DARK_GRAY, quit_rect, border_radius=8)
    pygame.draw.rect(screen, quit_color, quit_rect, 2, border_radius=8)
    quit_text = font.render("退出到主菜单", True, quit_color)
    quit_text_rect = quit_text.get_rect(center=quit_rect.center)
    screen.blit(quit_text, quit_text_rect)
