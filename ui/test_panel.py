"""测试模式面板"""
import pygame
from skills import SKILL_POOL
from .drawables import draw_skill_icon_shape, get_font, SKILL_ICONS


def get_test_skill_rects(sw, sh):
    """获取测试模式技能面板的点击区域"""
    rects = []
    icon_size = 38
    padding = 8
    cols = 6
    start_x = 15
    start_y = sh - 60 - 38
    for i, skill in enumerate(SKILL_POOL):
        row = i // cols
        col = i % cols
        x = start_x + col * (icon_size + padding)
        y = start_y - row * (icon_size + padding + 16)
        rects.append(pygame.Rect(x, y, icon_size, icon_size))
    return rects


def get_test_enemy_rects(sw, sh):
    """获取测试模式敌人生成面板的点击区域"""
    rects = []
    btn_w, btn_h = 70, 35
    start_x = sw - 80
    start_y = sh - 60
    for i in range(5):
        rects.append(pygame.Rect(start_x, start_y - i * (btn_h + 8), btn_w, btn_h))
    return rects


def get_test_auto_spawn_rect(sw, sh):
    """获取测试模式自动生成开关的点击区域"""
    return pygame.Rect(sw - 80, sh - 50 - 5 * 40, 70, 35)


def draw_test_mode_panel(screen, font, acquired_skills, mouse_pos, auto_spawn_enabled):
    """绘制测试模式面板"""
    sw, sh = screen.get_width(), screen.get_height()

    # 测试模式标识
    test_label = font.render("[ 测试模式 ]", True, (100, 255, 100))
    screen.blit(test_label, (10, 10))

    # 技能面板标题
    skill_title = font.render("技能 (点击添加):", True, (200, 180, 140))
    screen.blit(skill_title, (15, 35))

    # 绘制所有可添加的技能
    skill_rects = get_test_skill_rects(sw, sh)
    icon_size = 38
    cols = 6
    for i, skill in enumerate(SKILL_POOL):
        rect = skill_rects[i]
        hovered = rect.collidepoint(mouse_pos)
        icon_info = SKILL_ICONS.get(skill["name"], {
            "color": (100, 100, 100), "glow": (150, 150, 150), "border": (80, 80, 80)
        })

        bg_rect = pygame.Rect(rect.x, rect.y, icon_size, icon_size)
        pygame.draw.rect(screen, (20, 18, 25), bg_rect, border_radius=4)
        pygame.draw.rect(screen, icon_info["border"] if not hovered else icon_info["glow"],
                        bg_rect, 1, border_radius=4)
        draw_skill_icon_shape(screen, rect.x, rect.y, icon_size, icon_info)

    # 敌人生成面板标题
    enemy_title = font.render("生成敌人:", True, (200, 180, 140))
    screen.blit(enemy_title, (sw - 90, sh - 250))

    # 敌人生成按钮
    enemy_rects = get_test_enemy_rects(sw, sh)
    enemy_info = [
        ("基础", (255, 80, 80)),
        ("冲锋", (255, 140, 0)),
        ("射手", (0, 200, 100)),
        ("自爆", (200, 50, 200)),
        ("精英", (50, 150, 255)),
    ]
    for i, (name, color) in enumerate(enemy_info):
        rect = enemy_rects[i]
        hovered = rect.collidepoint(mouse_pos)
        bg_color = (30, 25, 35) if not hovered else (50, 45, 60)
        pygame.draw.rect(screen, bg_color, rect, border_radius=4)
        pygame.draw.rect(screen, color, rect, 1, border_radius=4)
        text = get_font(12).render(name, True, color)
        text_rect = text.get_rect(center=rect.center)
        screen.blit(text, text_rect)

    # 自动生成开关
    auto_rect = get_test_auto_spawn_rect(sw, sh)
    auto_hovered = auto_rect.collidepoint(mouse_pos)
    auto_color = (80, 200, 80) if auto_spawn_enabled else (150, 150, 150)
    pygame.draw.rect(screen, (30, 30, 40), auto_rect, border_radius=4)
    pygame.draw.rect(screen, auto_color, auto_rect, 2 if not auto_hovered else 3, border_radius=4)
    auto_text = "自动生成 ON" if auto_spawn_enabled else "自动生成 OFF"
    text = get_font(11).render(auto_text[:6], True, auto_color)
    text_rect = text.get_rect(center=auto_rect.center)
    screen.blit(text, text_rect)
