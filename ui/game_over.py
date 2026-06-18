"""Game over screen."""
import pygame
from settings import WHITE, RED, GOLD, GREEN


def draw_game_over_screen(screen, big_font, font, elapsed_time, score, level, high_score, is_new_record, is_victory=False):
    sw, sh = screen.get_width(), screen.get_height()
    overlay = pygame.Surface((sw, sh), pygame.SRCALPHA)
    overlay.fill((4, 5, 10, 226))
    screen.blit(overlay, (0, 0))

    panel = pygame.Rect(sw // 2 - 250, sh // 2 - 210, 500, 360)
    pygame.draw.rect(screen, (20, 23, 33), panel, border_radius=8)
    pygame.draw.rect(screen, (80, 88, 112), panel, 1, border_radius=8)

    title_text = "胜利" if is_victory else "游戏结束"
    title_color = GREEN if is_victory else RED
    title = big_font.render(title_text, True, title_color)
    screen.blit(title, title.get_rect(center=(sw // 2, panel.y + 58)))

    minutes = int(elapsed_time // 60)
    seconds = int(elapsed_time % 60)
    lines = [
        ("存活时间", f"{minutes:02d}:{seconds:02d}"),
        ("击杀敌人", str(score)),
        ("达到等级", f"Lv.{level}"),
        ("最高分", str(high_score)),
    ]
    y = panel.y + 112
    for label, value in lines:
        row = pygame.Rect(panel.x + 58, y, panel.width - 116, 36)
        pygame.draw.rect(screen, (29, 33, 46), row, border_radius=6)
        label_text = font.render(label, True, (145, 158, 180))
        value_text = font.render(value, True, WHITE)
        screen.blit(label_text, (row.x + 14, row.y + 6))
        screen.blit(value_text, value_text.get_rect(midright=(row.right - 14, row.centery)))
        y += 44

    if is_new_record:
        record_text = font.render("新纪录", True, GOLD)
        screen.blit(record_text, record_text.get_rect(center=(sw // 2, y + 8)))

    btn_w, btn_h = 240, 50
    btn_rect = pygame.Rect((sw - btn_w) // 2, panel.bottom - 72, btn_w, btn_h)
    pygame.draw.rect(screen, (35, 40, 55), btn_rect, border_radius=8)
    pygame.draw.rect(screen, GOLD, btn_rect, 2, border_radius=8)
    btn_text = font.render("重新开始", True, GOLD)
    screen.blit(btn_text, btn_text.get_rect(center=btn_rect.center))

    hint = font.render("按 SPACE 或点击按钮", True, (130, 140, 160))
    screen.blit(hint, hint.get_rect(center=(sw // 2, btn_rect.bottom + 22)))
    return btn_rect
