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
    btn_w, btn_h = 55, 32
    # 位于顶部技能图标和底部技能栏之间（y=250起）
    start_x = 15
    start_y = 250  # 第一个按钮的y位置
    for i in range(5):
        rects.append(pygame.Rect(start_x, start_y + i * (btn_h + 5), btn_w, btn_h))
    return rects


def get_test_auto_spawn_rect(sw, sh):
    """获取测试模式自动生成开关的点击区域（在生成敌人按钮上方）"""
    return pygame.Rect(15, 215, 90, 28)


def get_test_player_controls_rect(sw, sh):
    """获取测试模式玩家控制面板的点击区域"""
    panel_x = sw - 220
    panel_y = sh - 300
    rects = {
        "hp_minus": pygame.Rect(panel_x + 60, panel_y + 20, 28, 24),
        "hp_plus": pygame.Rect(panel_x + 95, panel_y + 20, 28, 24),
        "hp_apply": pygame.Rect(panel_x + 128, panel_y + 20, 45, 24),
        "max_hp_minus": pygame.Rect(panel_x + 60, panel_y + 50, 28, 24),
        "max_hp_plus": pygame.Rect(panel_x + 95, panel_y + 50, 28, 24),
        "max_hp_apply": pygame.Rect(panel_x + 128, panel_y + 50, 45, 24),
        "xp_minus": pygame.Rect(panel_x + 60, panel_y + 80, 28, 24),
        "xp_plus": pygame.Rect(panel_x + 95, panel_y + 80, 28, 24),
        "xp_apply": pygame.Rect(panel_x + 128, panel_y + 80, 45, 24),
        "full_hp": pygame.Rect(panel_x, panel_y + 110, 55, 24),
        "add_xp_100": pygame.Rect(panel_x + 58, panel_y + 110, 60, 24),
        "add_xp_500": pygame.Rect(panel_x + 121, panel_y + 110, 60, 24),
    }
    return rects


def get_test_custom_enemy_rects(sw, sh):
    """获取自定义敌人生成面板的点击区域"""
    panel_x = sw - 220
    panel_y = sh - 470
    rects = {
        "hp_minus": pygame.Rect(panel_x + 60, panel_y + 20, 25, 22),
        "hp_plus": pygame.Rect(panel_x + 95, panel_y + 20, 25, 22),
        "hp_input": pygame.Rect(panel_x + 125, panel_y + 20, 50, 22),
        "speed_minus": pygame.Rect(panel_x + 60, panel_y + 48, 25, 22),
        "speed_plus": pygame.Rect(panel_x + 95, panel_y + 48, 25, 22),
        "speed_input": pygame.Rect(panel_x + 125, panel_y + 48, 50, 22),
        "spawn": pygame.Rect(panel_x + 70, panel_y + 76, 55, 28),
    }
    return rects


def get_test_debug_rect(sw, sh):
    """获取调试显示开关的点击区域"""
    return pygame.Rect(sw - 220, sh - 430, 90, 26)


def draw_test_mode_panel(screen, font, mouse_pos, auto_spawn_enabled,
                         player_hp, player_max_hp, xp_multiplier,
                         custom_hp, custom_speed, debug_stats_enabled=False,
                         enemy_stats=None):
    """绘制测试模式面板
    debug_stats_enabled: 是否显示敌人数值
    enemy_stats: 敌人当前数值字典 {type: {hp, damage, explosion_damage}}
    """
    sw, sh = screen.get_width(), screen.get_height()
    small_font = get_font(11)
    tiny_font = get_font(10)

    # 测试模式标识
    test_label = font.render("[ 测试模式 ]", True, (100, 255, 100))
    screen.blit(test_label, (10, 10))

    # ============ 调试面板 ============
    debug_rect = get_test_debug_rect(sw, sh)
    debug_hovered = debug_rect.collidepoint(mouse_pos)
    debug_color = (80, 200, 80) if debug_stats_enabled else (150, 150, 150)
    pygame.draw.rect(screen, (30, 30, 40), debug_rect, border_radius=4)
    pygame.draw.rect(screen, debug_color, debug_rect, 2 if not debug_hovered else 3, border_radius=4)
    debug_text = "数值 ON" if debug_stats_enabled else "数值 OFF"
    text = get_font(10).render(debug_text, True, debug_color)
    text_rect = text.get_rect(center=debug_rect.center)
    screen.blit(text, text_rect)

    # ============ 敌人数值显示 ============
    if debug_stats_enabled and enemy_stats:
        stats_y = 45
        stats_x = sw - 220
        for enemy_type, stats in enemy_stats.items():
            type_names = {
                "basic": "基础",
                "charger": "冲锋",
                "ranger": "射手",
                "exploder": "自爆",
                "elite": "精英"
            }
            name = type_names.get(enemy_type, enemy_type)
            hp_str = f"{name}: HP{stats['hp']}"
            if enemy_type == "exploder":
                dmg_str = f" 爆炸{stats['explosion_damage']}"
            elif enemy_type == "ranger":
                dmg_str = f" 弹{stats['damage']}"
            else:
                dmg_str = f" 伤{stats['damage']}"
            stat_text = tiny_font.render(hp_str + dmg_str, True, (200, 200, 200))
            screen.blit(stat_text, (stats_x, stats_y))
            stats_y += 14

    # ============ 玩家控制面板 ============
    panel_x = sw - 220
    panel_y = sh - 300

    # 面板背景
    panel_rect = pygame.Rect(panel_x - 5, panel_y - 5, 200, 150)
    pygame.draw.rect(screen, (25, 22, 30, 230), panel_rect, border_radius=6)
    pygame.draw.rect(screen, (60, 55, 70), panel_rect, 1, border_radius=6)

    title = small_font.render("玩家控制", True, (200, 180, 140))
    screen.blit(title, (panel_x, panel_y - 2))

    control_rects = get_test_player_controls_rect(sw, sh)

    # 当前血量
    hp_text = small_font.render(f"血量: {player_hp}", True, (255, 100, 100))
    screen.blit(hp_text, (panel_x, panel_y + 18))
    pygame.draw.rect(screen, (50, 50, 60), control_rects["hp_minus"], border_radius=3)
    pygame.draw.rect(screen, (50, 50, 60), control_rects["hp_plus"], border_radius=3)
    pygame.draw.rect(screen, (60, 140, 80), control_rects["hp_apply"], border_radius=3)
    screen.blit(small_font.render("-", True, (255, 255, 255)), (control_rects["hp_minus"].centerx - 3, control_rects["hp_minus"].centery - 5))
    screen.blit(small_font.render("+", True, (255, 255, 255)), (control_rects["hp_plus"].centerx - 2, control_rects["hp_plus"].centery - 5))
    screen.blit(tiny_font.render("应用", True, (255, 255, 255)), (control_rects["hp_apply"].centerx - 9, control_rects["hp_apply"].centery - 4))

    # 血量上限
    max_hp_text = small_font.render(f"上限: {player_max_hp}", True, (255, 180, 100))
    screen.blit(max_hp_text, (panel_x, panel_y + 48))
    pygame.draw.rect(screen, (50, 50, 60), control_rects["max_hp_minus"], border_radius=3)
    pygame.draw.rect(screen, (50, 50, 60), control_rects["max_hp_plus"], border_radius=3)
    pygame.draw.rect(screen, (60, 140, 80), control_rects["max_hp_apply"], border_radius=3)
    screen.blit(small_font.render("-", True, (255, 255, 255)), (control_rects["max_hp_minus"].centerx - 3, control_rects["max_hp_minus"].centery - 5))
    screen.blit(small_font.render("+", True, (255, 255, 255)), (control_rects["max_hp_plus"].centerx - 2, control_rects["max_hp_plus"].centery - 5))
    screen.blit(tiny_font.render("应用", True, (255, 255, 255)), (control_rects["max_hp_apply"].centerx - 9, control_rects["max_hp_apply"].centery - 4))

    # 经验倍率
    xp_text = small_font.render(f"经验x{xp_multiplier:.1f}", True, (180, 180, 255))
    screen.blit(xp_text, (panel_x, panel_y + 78))
    pygame.draw.rect(screen, (50, 50, 60), control_rects["xp_minus"], border_radius=3)
    pygame.draw.rect(screen, (50, 50, 60), control_rects["xp_plus"], border_radius=3)
    pygame.draw.rect(screen, (100, 80, 60), control_rects["xp_apply"], border_radius=3)
    screen.blit(small_font.render("-", True, (255, 255, 255)), (control_rects["xp_minus"].centerx - 3, control_rects["xp_minus"].centery - 5))
    screen.blit(small_font.render("+", True, (255, 255, 255)), (control_rects["xp_plus"].centerx - 2, control_rects["xp_plus"].centery - 5))
    screen.blit(tiny_font.render("x0禁止", True, (255, 255, 255)), (control_rects["xp_apply"].centerx - 12, control_rects["xp_apply"].centery - 4))

    # 快捷按钮
    pygame.draw.rect(screen, (80, 50, 50), control_rects["full_hp"], border_radius=3)
    pygame.draw.rect(screen, (50, 80, 50), control_rects["add_xp_100"], border_radius=3)
    pygame.draw.rect(screen, (50, 80, 50), control_rects["add_xp_500"], border_radius=3)
    screen.blit(tiny_font.render("满血", True, (255, 255, 255)), (control_rects["full_hp"].centerx - 9, control_rects["full_hp"].centery - 4))
    screen.blit(tiny_font.render("+100", True, (255, 255, 255)), (control_rects["add_xp_100"].centerx - 11, control_rects["add_xp_100"].centery - 4))
    screen.blit(tiny_font.render("+500", True, (255, 255, 255)), (control_rects["add_xp_500"].centerx - 11, control_rects["add_xp_500"].centery - 4))

    # ============ 自定义敌人生成面板 ============
    enemy_panel_x = sw - 220
    enemy_panel_y = sh - 470

    # 面板背景
    enemy_panel_rect = pygame.Rect(enemy_panel_x - 5, enemy_panel_y - 5, 200, 120)
    pygame.draw.rect(screen, (25, 22, 30, 230), enemy_panel_rect, border_radius=6)
    pygame.draw.rect(screen, (60, 55, 70), enemy_panel_rect, 1, border_radius=6)

    enemy_title = small_font.render("自定义敌人", True, (200, 180, 140))
    screen.blit(enemy_title, (enemy_panel_x, enemy_panel_y - 2))

    enemy_rects = get_test_custom_enemy_rects(sw, sh)

    # HP设置
    hp_label = small_font.render("HP:", True, (200, 200, 200))
    screen.blit(hp_label, (enemy_panel_x, enemy_panel_y + 18))
    pygame.draw.rect(screen, (50, 50, 60), enemy_rects["hp_minus"], border_radius=3)
    pygame.draw.rect(screen, (50, 50, 60), enemy_rects["hp_plus"], border_radius=3)
    pygame.draw.rect(screen, (40, 40, 50), enemy_rects["hp_input"], border_radius=3)
    screen.blit(small_font.render("-", True, (255, 255, 255)), (enemy_rects["hp_minus"].centerx - 3, enemy_rects["hp_minus"].centery - 5))
    screen.blit(small_font.render("+", True, (255, 255, 255)), (enemy_rects["hp_plus"].centerx - 2, enemy_rects["hp_plus"].centery - 5))
    screen.blit(tiny_font.render(str(custom_hp), True, (255, 255, 255)), (enemy_rects["hp_input"].centerx - 8, enemy_rects["hp_input"].centery - 4))

    # 速度设置
    speed_label = small_font.render("SPD:", True, (200, 200, 200))
    screen.blit(speed_label, (enemy_panel_x, enemy_panel_y + 46))
    pygame.draw.rect(screen, (50, 50, 60), enemy_rects["speed_minus"], border_radius=3)
    pygame.draw.rect(screen, (50, 50, 60), enemy_rects["speed_plus"], border_radius=3)
    pygame.draw.rect(screen, (40, 40, 50), enemy_rects["speed_input"], border_radius=3)
    screen.blit(small_font.render("-", True, (255, 255, 255)), (enemy_rects["speed_minus"].centerx - 3, enemy_rects["speed_minus"].centery - 5))
    screen.blit(small_font.render("+", True, (255, 255, 255)), (enemy_rects["speed_plus"].centerx - 2, enemy_rects["speed_plus"].centery - 5))
    screen.blit(tiny_font.render(str(custom_speed), True, (255, 255, 255)), (enemy_rects["speed_input"].centerx - 8, enemy_rects["speed_input"].centery - 4))

    # 生成按钮
    pygame.draw.rect(screen, (50, 150, 80), enemy_rects["spawn"], border_radius=4)
    pygame.draw.rect(screen, (100, 255, 150), enemy_rects["spawn"], 2, border_radius=4)
    screen.blit(small_font.render("生成", True, (255, 255, 255)), (enemy_rects["spawn"].centerx - 12, enemy_rects["spawn"].centery - 5))

    # ============ 技能面板 ============
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

    # ============ 敌人生成面板（左侧） ============
    enemy_title = font.render("生成敌人:", True, (200, 180, 140))
    screen.blit(enemy_title, (15, 180))

    # 敌人生成按钮
    enemy_btn_rects = get_test_enemy_rects(sw, sh)
    enemy_info = [
        ("基础", (255, 80, 80)),
        ("冲锋", (255, 140, 0)),
        ("射手", (0, 200, 100)),
        ("自爆", (200, 50, 200)),
        ("精英", (50, 150, 255)),
    ]
    for i, (name, color) in enumerate(enemy_info):
        rect = enemy_btn_rects[i]
        hovered = rect.collidepoint(mouse_pos)
        bg_color = (30, 25, 35) if not hovered else (50, 45, 60)
        pygame.draw.rect(screen, bg_color, rect, border_radius=4)
        pygame.draw.rect(screen, color, rect, 1, border_radius=4)
        text = get_font(12).render(name, True, color)
        text_rect = text.get_rect(center=rect.center)
        screen.blit(text, text_rect)

    # ============ 自动生成开关（生成敌人按钮上方） ============
    auto_rect = get_test_auto_spawn_rect(sw, sh)
    auto_hovered = auto_rect.collidepoint(mouse_pos)
    auto_color = (80, 200, 80) if auto_spawn_enabled else (150, 150, 150)
    pygame.draw.rect(screen, (30, 30, 40), auto_rect, border_radius=4)
    pygame.draw.rect(screen, auto_color, auto_rect, 2 if not auto_hovered else 3, border_radius=4)
    auto_text = "自动 ON" if auto_spawn_enabled else "自动 OFF"
    text = get_font(11).render(auto_text, True, auto_color)
    text_rect = text.get_rect(center=auto_rect.center)
    screen.blit(text, text_rect)


def get_test_control_rects(sw, sh):
    """获取测试模式控制按钮的区域（供main.py事件处理使用）"""
    return {
        "player": get_test_player_controls_rect(sw, sh),
        "custom_enemy": get_test_custom_enemy_rects(sw, sh),
        "enemy": get_test_enemy_rects(sw, sh),
        "auto_spawn": get_test_auto_spawn_rect(sw, sh),
        "debug_stats": get_test_debug_rect(sw, sh),
        "skill": get_test_skill_rects(sw, sh),
    }
