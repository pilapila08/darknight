"""游戏结束界面"""
import pygame
from settings import BLACK, DARK_GRAY, WHITE, RED, GOLD, GREEN


def draw_game_over_screen(screen, big_font, font, elapsed_time, score, level, high_score, is_new_record, is_victory=False):
    """绘制游戏结束界面，返回重新开始按钮区域
    is_victory: True=胜利(存活10分钟), False=失败(死亡)
    """
    sw, sh = screen.get_width(), screen.get_height()
    overlay = pygame.Surface((sw, sh))
    overlay.set_alpha(220)
    overlay.fill(BLACK)
    screen.blit(overlay, (0, 0))

    if is_victory:
        title = big_font.render("胜 利 ！", True, GOLD)
        subtitle = font.render("成功存活10分钟！", True, GREEN)
    else:
        title = big_font.render("游 戏 结 束", True, RED)
        subtitle = font.render("存活时间不足", True, (150, 150, 150))

    title_rect = title.get_rect(center=(sw // 2, sh // 6))
    screen.blit(title, title_rect)

    if is_victory:
        subtitle_rect = subtitle.get_rect(center=(sw // 2, sh // 6 + 50))
        screen.blit(subtitle, subtitle_rect)

    y = sh // 3 if is_victory else sh // 3
    gap = sh // 18

    if is_victory:
        lines = [
            f"存活时间：{elapsed_time:.0f} 秒 (10分钟)",
            f"击杀敌人：{score}",
            f"达到等级：Lv.{level}",
            f"历史最高分：{high_score}",
        ]
    else:
        lines = [
            f"存活时间：{elapsed_time:.0f} 秒",
            f"击杀敌人：{score}",
            f"达到等级：Lv.{level}",
            f"历史最高分：{high_score}",
        ]
    for line in lines:
        text = font.render(line, True, WHITE)
        rect = text.get_rect(center=(sw // 2, y))
        screen.blit(text, rect)
        y += gap

    if is_new_record:
        record_text = big_font.render("新 纪 录 ！", True, GOLD)
        record_rect = record_text.get_rect(center=(sw // 2, y))
        screen.blit(record_text, record_rect)
        y += 50

    # 重新开始按钮
    btn_w, btn_h = 240, 50
    btn_x = (sw - btn_w) // 2
    btn_y = sh - 120
    btn_rect = pygame.Rect(btn_x, btn_y, btn_w, btn_h)
    pygame.draw.rect(screen, DARK_GRAY, btn_rect)
    pygame.draw.rect(screen, WHITE, btn_rect, 2)
    btn_text = font.render("重 新 开 始", True, WHITE)
    btn_text_rect = btn_text.get_rect(center=btn_rect.center)
    screen.blit(btn_text, btn_text_rect)

    hint = font.render("按 SPACE 或点击按钮重新开始", True, (120, 120, 140))
    hint_rect = hint.get_rect(center=(sw // 2, btn_y + btn_h + 20))
    screen.blit(hint, hint_rect)

    return btn_rect
