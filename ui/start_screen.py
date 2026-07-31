"""开始界面"""
import math
import random
import pygame
from settings import GOLD, ENABLE_TEST_MODE

# 标题画面氛围粒子（缓慢上浮的暗紫色光点）
_particles = []
_last_ms = 0


def _update_particles(sw, sh):
    global _last_ms
    now = pygame.time.get_ticks()
    dt = min(0.1, (now - _last_ms) / 1000.0) if _last_ms else 0.016
    _last_ms = now

    # 补充粒子
    while len(_particles) < 46:
        _particles.append({
            "x": random.uniform(0, sw),
            "y": random.uniform(0, sh + 60),
            "size": random.uniform(1.5, 4.5),
            "speed": random.uniform(8, 30),
            "drift": random.uniform(-6, 6),
            "phase": random.uniform(0, math.pi * 2),
            "alpha": random.uniform(40, 110),
        })
    for p in _particles:
        p["y"] -= p["speed"] * dt
        p["x"] += (p["drift"] + math.sin(now * 0.001 + p["phase"]) * 6) * dt
        if p["y"] < -10:
            p["y"] = sh + random.uniform(0, 40)
            p["x"] = random.uniform(0, sw)
    return now


def draw_start_screen(screen, big_font, font, small_font, test_activated=False):
    """绘制开始界面，返回按钮区域和游戏模式选择
    test_activated: 测试模式是否已通过密码激活
    """
    sw, sh = screen.get_width(), screen.get_height()
    now = _update_particles(sw, sh)

    # 背景：垂直渐变（深紫到近黑）
    screen.fill((10, 5, 20))
    grad = pygame.Surface((sw, sh // 2), pygame.SRCALPHA)
    for i in range(0, sh // 2, 4):
        alpha = int(70 * (1 - i / (sh // 2)))
        pygame.draw.rect(grad, (60, 30, 90, alpha), (0, i, sw, 4))
    screen.blit(grad, (0, 0))

    # 氛围粒子
    for p in _particles:
        r = int(p["size"])
        surf = pygame.Surface((r * 6, r * 6), pygame.SRCALPHA)
        pygame.draw.circle(surf, (150, 110, 210, int(p["alpha"] * 0.35)),
                           (r * 3, r * 3), r * 3)
        pygame.draw.circle(surf, (200, 170, 255, int(p["alpha"])),
                           (r * 3, r * 3), r)
        screen.blit(surf, (int(p["x"]) - r * 3, int(p["y"]) - r * 3))

    # 标题（带呼吸光晕和阴影）
    title_cx, title_cy = sw // 2, sh // 5
    pulse = 0.6 + 0.4 * math.sin(now * 0.0015)
    title = big_font.render("暗 夜 求 生", True, GOLD)
    glow = big_font.render("暗 夜 求 生", True, (120, 80, 30))
    glow.set_alpha(int(140 * pulse))
    title_rect = title.get_rect(center=(title_cx, title_cy))
    shadow = big_font.render("暗 夜 求 生", True, (40, 20, 10))
    screen.blit(shadow, title_rect.move(4, 4))
    for dx, dy in ((-2, 0), (2, 0), (0, -2), (0, 2)):
        screen.blit(glow, title_rect.move(dx, dy))
    screen.blit(title, title_rect)

    # 标题下方装饰线
    line_w = int(200 + 26 * pulse)
    pygame.draw.line(screen, (150, 120, 60), (title_cx - line_w, title_cy + 38),
                     (title_cx + line_w, title_cy + 38), 1)

    # 副标题
    sub = font.render("Darknight Survival", True, (150, 130, 180))
    sub_rect = sub.get_rect(center=(sw // 2, sh // 5 + 55))
    screen.blit(sub, sub_rect)

    # 说明文字
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
    mouse_pos = pygame.mouse.get_pos()
    hovered = btn_rect.collidepoint(mouse_pos)

    # 绘制开始游戏按钮（悬停提亮 + 呼吸边框）
    bg_color = (70, 55, 110) if hovered else (50, 40, 80)
    pygame.draw.rect(screen, bg_color, btn_rect, border_radius=8)
    border_pulse = int(200 + 55 * math.sin(now * 0.004))
    pygame.draw.rect(screen, (border_pulse, int(border_pulse * 0.8), 0),
                     btn_rect, 3 if hovered else 2, border_radius=8)
    start_text = font.render("开 始 游 戏", True, GOLD)
    start_text_rect = start_text.get_rect(center=btn_rect.center)
    screen.blit(start_text, start_text_rect)

    # 开始游戏提示（呼吸闪烁）
    hint_alpha = int(120 + 100 * (0.5 + 0.5 * math.sin(now * 0.003)))
    start_hint = font.render("按 空格键 开始游戏", True, (170, 170, 185))
    start_hint.set_alpha(hint_alpha)
    start_hint_rect = start_hint.get_rect(center=(sw // 2, btn_y + btn_h + 30))
    screen.blit(start_hint, start_hint_rect)

    # 测试模式按钮（仅在密码激活后显示）
    test_btn_rect = None
    if test_activated and ENABLE_TEST_MODE:
        test_btn_w, test_btn_h = 220, 45
        test_btn_x = (sw - test_btn_w) // 2
        test_btn_y = btn_y - test_btn_h - 15
        test_btn_rect = pygame.Rect(test_btn_x, test_btn_y, test_btn_w, test_btn_h)
        test_hovered = test_btn_rect.collidepoint(mouse_pos)
        pygame.draw.rect(screen, (42, 42, 66) if test_hovered else (30, 30, 50),
                         test_btn_rect, border_radius=6)
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
