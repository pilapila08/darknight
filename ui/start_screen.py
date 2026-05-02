"""开始界面"""
import pygame
from settings import GOLD, ENABLE_TEST_MODE


def draw_start_screen(screen, big_font, font, small_font):
    """绘制开始界面，返回按钮区域"""
    sw, sh = screen.get_width(), screen.get_height()
    screen.fill((10, 5, 20))

    # 标题
    title = big_font.render("暗 夜 求 生", True, GOLD)
    title_rect = title.get_rect(center=(sw // 2, sh // 6))
    screen.blit(title, title_rect)

    # 副标题
    sub = font.render("Darknight Survival", True, (150, 130, 180))
    sub_rect = sub.get_rect(center=(sw // 2, sh // 6 + 45))
    screen.blit(sub, sub_rect)

    # 说明文字
    lines = [
        "WASD / 方向键  移动",
        "自动瞄准最近敌人开火",
        "击杀敌人掉落经验球  →  升级  →  选择强化",
        "",
        "武器系统：",
        "  旋转利刃 — 环绕自身的刀刃",
        "  连锁闪电 — 弹跳打击多个敌人",
        "  剧毒地雷 — 移动时释放毒圈",
        "",
        "敌人类型会随时间逐渐解锁",
    ]
    y = sh // 3 + 20
    for line in lines:
        if line == "":
            y += 8
            continue
        color = GOLD if line.startswith("武器") or line.startswith("敌人") else (200, 200, 210)
        text = small_font.render(line, True, color)
        text_rect = text.get_rect(center=(sw // 2, y))
        screen.blit(text, text_rect)
        y += 22

    # 开始游戏按钮
    btn_w, btn_h = 220, 50
    btn_x = (sw - btn_w) // 2
    btn_y = sh - 100
    btn_rect = pygame.Rect(btn_x, btn_y, btn_w, btn_h)
    pygame.draw.rect(screen, (40, 20, 60), btn_rect)
    pygame.draw.rect(screen, GOLD, btn_rect, 2)
    btn_text = font.render("开 始 游 戏", True, GOLD)
    btn_text_rect = btn_text.get_rect(center=btn_rect.center)
    screen.blit(btn_text, btn_text_rect)

    hint = small_font.render("按 SPACE 或点击按钮开始", True, (120, 120, 140))
    hint_rect = hint.get_rect(center=(sw // 2, btn_y + btn_h + 22))
    screen.blit(hint, hint_rect)

    # 测试模式按钮（根据开关显示）
    if ENABLE_TEST_MODE:
        test_btn_w, test_btn_h = 220, 45
        test_btn_x = (sw - test_btn_w) // 2
        test_btn_y = btn_y - test_btn_h - 15
        test_btn_rect = pygame.Rect(test_btn_x, test_btn_y, test_btn_w, test_btn_h)
        pygame.draw.rect(screen, (30, 50, 30), test_btn_rect)
        pygame.draw.rect(screen, (100, 200, 100), test_btn_rect, 2)
        test_btn_text = font.render("测试模式", True, (150, 255, 150))
        test_btn_text_rect = test_btn_text.get_rect(center=test_btn_rect.center)
        screen.blit(test_btn_text, test_btn_text_rect)

        test_hint = small_font.render("T 键快速进入", True, (80, 150, 80))
        test_hint_rect = test_hint.get_rect(center=(sw // 2, test_btn_y + test_btn_h + 12))
        screen.blit(test_hint, test_hint_rect)

        return btn_rect, test_btn_rect

    return btn_rect, None
