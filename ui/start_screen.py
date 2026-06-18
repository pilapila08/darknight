"""开始界面"""
import pygame
from settings import GOLD, ENABLE_TEST_MODE


def draw_start_screen(screen, big_font, font, small_font, test_activated=False):
    """绘制开始界面，返回按钮区域和游戏模式选择
    test_activated: 测试模式是否已通过密码激活
    """
    sw, sh = screen.get_width(), screen.get_height()
    screen.fill((10, 5, 20))

    # 标题（放大）
    title = big_font.render("暗 夜 求 生", True, GOLD)
    title_rect = title.get_rect(center=(sw // 2, sh // 5))
    screen.blit(title, title_rect)

    # 副标题
    sub = font.render("Darknight Survival", True, (150, 130, 180))
    sub_rect = sub.get_rect(center=(sw // 2, sh // 5 + 55))
    screen.blit(sub, sub_rect)

    # 说明文字（使用 font 代替 small_font 使其更大）
    lines = [
        "WASD / 方向键  移动",
        "自动瞄准最近敌人开火",
        "击杀敌人掉落经验球  →  升级  →  选择强化",
        "",
        "武器系统：",
        "  暗影新星 — 周期性释放范围冲击波",
        "  连锁闪电 — 弹跳打击多个敌人",
        "  剧毒地雷 — 自动释放毒圈",
        "",
        "敌人类型会随时间逐渐解锁",
    ]
    y = sh // 3 + 30
    for line in lines:
        if line == "":
            y += 12
            continue
        color = GOLD if line.startswith("武器") or line.startswith("敌人") else (200, 200, 210)
        text = font.render(line, True, color)
        text_rect = text.get_rect(center=(sw // 2, y))
        screen.blit(text, text_rect)
        y += 28

    # 按钮区域
    btn_w, btn_h = 220, 55
    btn_x = (sw - btn_w) // 2
    btn_y = sh - 120
    btn_rect = pygame.Rect(btn_x, btn_y, btn_w, btn_h)

    # 绘制开始游戏按钮
    pygame.draw.rect(screen, (50, 40, 80), btn_rect, border_radius=8)
    pygame.draw.rect(screen, GOLD, btn_rect, 2, border_radius=8)
    start_text = font.render("开 始 游 戏", True, GOLD)
    start_text_rect = start_text.get_rect(center=btn_rect.center)
    screen.blit(start_text, start_text_rect)

    # 开始游戏提示（用 font 替代 small_font）
    start_hint = font.render("按 空格键 开始游戏", True, (150, 150, 150))
    start_hint_rect = start_hint.get_rect(center=(sw // 2, btn_y + btn_h + 30))
    screen.blit(start_hint, start_hint_rect)

    # 测试模式按钮（仅在密码激活后显示）
    test_btn_rect = None
    if test_activated and ENABLE_TEST_MODE:
        test_btn_w, test_btn_h = 220, 45
        test_btn_x = (sw - test_btn_w) // 2
        test_btn_y = btn_y - test_btn_h - 15
        test_btn_rect = pygame.Rect(test_btn_x, test_btn_y, test_btn_w, test_btn_h)
        pygame.draw.rect(screen, (30, 30, 50), test_btn_rect, border_radius=6)
        pygame.draw.rect(screen, (100, 100, 140), test_btn_rect, 1, border_radius=6)
        test_text = small_font.render("测试模式 (T)", True, (150, 150, 200))
        test_text_rect = test_text.get_rect(center=test_btn_rect.center)
        screen.blit(test_text, test_text_rect)

    return btn_rect, test_btn_rect


def handle_start_screen_input(event, btn_rect, test_btn_rect, test_activated=False):
    """处理开始界面的输入，返回选择的游戏模式 ('normal', 'test', None)
    test_activated: 测试模式是否已通过密码激活
    """
    if event.type == pygame.KEYDOWN:
        if event.key == pygame.K_SPACE:
            return "normal"
        if event.key == pygame.K_t and test_activated and test_btn_rect is not None:
            return "test"

    if event.type == pygame.MOUSEBUTTONDOWN:
        if btn_rect is not None and btn_rect.collidepoint(event.pos):
            return "normal"
        if test_btn_rect is not None and test_btn_rect.collidepoint(event.pos):
            return "test"

    return None
