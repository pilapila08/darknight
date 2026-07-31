"""Game over screen."""
import math
import pygame
from settings import WHITE, RED, GOLD, GREEN

# 结算动画状态：面板滑入 + 数字滚动
_anim = {"key": None, "start_ms": 0}


def _ease_out_cubic(t):
    return 1 - (1 - t) ** 3


def draw_game_over_screen(screen, big_font, font, elapsed_time, score, level, high_score, is_new_record, is_victory=False):
    sw, sh = screen.get_width(), screen.get_height()
    overlay = pygame.Surface((sw, sh), pygame.SRCALPHA)
    overlay.fill((4, 5, 10, 226))
    screen.blit(overlay, (0, 0))

    # 本局结算动画计时（按数据组合识别新的一局）
    now = pygame.time.get_ticks()
    key = (round(elapsed_time, 1), score, level)
    if _anim["key"] != key:
        _anim["key"] = key
        _anim["start_ms"] = now
    elapsed = (now - _anim["start_ms"]) / 1000.0

    # 面板从上方滑入
    slide_t = _ease_out_cubic(min(1.0, elapsed / 0.4))
    panel_y = int(sh // 2 - 210 - (1 - slide_t) * 60)
    panel = pygame.Rect(sw // 2 - 250, panel_y, 500, 360)
    pygame.draw.rect(screen, (20, 23, 33), panel, border_radius=8)
    border_color = GREEN if is_victory else (150, 60, 60)
    pygame.draw.rect(screen, border_color, panel, 2, border_radius=8)
    # 顶部色条
    pygame.draw.rect(screen, border_color, (panel.x, panel.y, panel.width, 6),
                     border_top_left_radius=8, border_top_right_radius=8)

    title_text = "胜利" if is_victory else "游戏结束"
    title_color = GREEN if is_victory else RED
    title = big_font.render(title_text, True, title_color)
    screen.blit(title, title.get_rect(center=(sw // 2, panel.y + 58)))

    minutes = int(elapsed_time // 60)
    seconds = int(elapsed_time % 60)
    lines = [
        ("存活时间", f"{minutes:02d}:{seconds:02d}", None),
        ("击杀敌人", str(score), score),
        ("达到等级", f"Lv.{level}", level),
        ("最高分", str(high_score), high_score),
    ]
    y = panel.y + 112
    for i, (label, value, numeric) in enumerate(lines):
        # 行依次浮现
        row_t = min(1.0, max(0.0, (elapsed - 0.3 - i * 0.15) / 0.25))
        if row_t <= 0:
            y += 44
            continue
        row = pygame.Rect(panel.x + 58, y, panel.width - 116, 36)
        row_surf = pygame.Surface((row.width, row.height), pygame.SRCALPHA)
        pygame.draw.rect(row_surf, (29, 33, 46, int(255 * row_t)), row_surf.get_rect(), border_radius=6)
        screen.blit(row_surf, row.topleft)

        # 数字滚动：0.5秒内从0滚到目标值
        if numeric is not None:
            roll_t = min(1.0, max(0.0, (elapsed - 0.3 - i * 0.15) / 0.5))
            shown = int(numeric * _ease_out_cubic(roll_t))
            if label == "达到等级":
                value = f"Lv.{shown}"
            else:
                value = str(shown)

        label_text = font.render(label, True, (145, 158, 180))
        value_text = font.render(value, True, WHITE)
        label_text.set_alpha(int(255 * row_t))
        value_text.set_alpha(int(255 * row_t))
        screen.blit(label_text, (row.x + 14, row.y + 6))
        screen.blit(value_text, value_text.get_rect(midright=(row.right - 14, row.centery)))
        y += 44

    if is_new_record and elapsed > 1.2:
        # 新纪录呼吸金光
        pulse = 0.6 + 0.4 * math.sin(now * 0.008)
        record_font = font
        record_text = record_font.render("★ 新纪录 ★", True,
                                         (255, int(190 + 50 * pulse), int(60 * pulse)))
        screen.blit(record_text, record_text.get_rect(center=(sw // 2, y + 8)))

    btn_w, btn_h = 240, 50
    btn_rect = pygame.Rect((sw - btn_w) // 2, panel.bottom - 72, btn_w, btn_h)
    hovered = btn_rect.collidepoint(pygame.mouse.get_pos())
    pygame.draw.rect(screen, (48, 54, 74) if hovered else (35, 40, 55), btn_rect, border_radius=8)
    pygame.draw.rect(screen, GOLD, btn_rect, 3 if hovered else 2, border_radius=8)
    btn_text = font.render("重新开始", True, GOLD)
    screen.blit(btn_text, btn_text.get_rect(center=btn_rect.center))

    hint = font.render("按 SPACE 或点击按钮", True, (130, 140, 160))
    screen.blit(hint, hint.get_rect(center=(sw // 2, btn_rect.bottom + 22)))
    return btn_rect
