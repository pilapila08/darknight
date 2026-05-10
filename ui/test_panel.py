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


def get_test_enemy_toggle_rect(sw, sh):
    """获取敌人生成折叠面板的展开/收起按钮"""
    return pygame.Rect(15, 180, 80, 28)


def get_test_boss_toggle_rect(sw, sh, enemy_panel_expanded=False):
    """获取Boss测试折叠面板的展开/收起按钮"""
    if enemy_panel_expanded:
        return pygame.Rect(15, 430, 80, 28)
    return pygame.Rect(15, 215, 80, 28)


def get_test_enemy_rects(sw, sh, expanded=False):
    """获取测试模式敌人生成面板的点击区域"""
    if not expanded:
        return []
    rects = []
    btn_w, btn_h = 55, 28
    start_x = 15
    start_y = 215  # 展开后第一个按钮的y位置
    for i in range(5):
        rects.append(pygame.Rect(start_x, start_y + i * (btn_h + 4), btn_w, btn_h))
    return rects


def get_test_auto_spawn_rect(sw, sh, expanded=False):
    """获取测试模式自动生成开关的点击区域"""
    if not expanded:
        return pygame.Rect(15, 215, 80, 28)
    return pygame.Rect(15, 400, 80, 28)


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
    panel_y = sh - 520
    rects = {
        # 类型选择（5个按钮横排）
        "type_0": pygame.Rect(panel_x, panel_y + 22, 38, 22),  # 基础
        "type_1": pygame.Rect(panel_x + 40, panel_y + 22, 38, 22),  # 冲锋
        "type_2": pygame.Rect(panel_x + 80, panel_y + 22, 38, 22),  # 射手
        "type_3": pygame.Rect(panel_x + 120, panel_y + 22, 38, 22),  # 自爆
        "type_4": pygame.Rect(panel_x + 160, panel_y + 22, 38, 22),  # 精英
        # 自定义数值
        "hp_minus": pygame.Rect(panel_x + 30, panel_y + 52, 22, 22),
        "hp_plus": pygame.Rect(panel_x + 55, panel_y + 52, 22, 22),
        "hp_input": pygame.Rect(panel_x + 80, panel_y + 52, 65, 22),
        "damage_minus": pygame.Rect(panel_x + 30, panel_y + 80, 22, 22),
        "damage_plus": pygame.Rect(panel_x + 55, panel_y + 80, 22, 22),
        "damage_input": pygame.Rect(panel_x + 80, panel_y + 80, 65, 22),
        "speed_minus": pygame.Rect(panel_x + 30, panel_y + 108, 22, 22),
        "speed_plus": pygame.Rect(panel_x + 55, panel_y + 108, 22, 22),
        "speed_input": pygame.Rect(panel_x + 80, panel_y + 108, 65, 22),
        "spawn": pygame.Rect(panel_x + 60, panel_y + 138, 55, 28),
    }
    return rects


def get_test_debug_rect(sw, sh):
    """获取调试显示开关的点击区域"""
    return pygame.Rect(sw - 220, sh - 430, 90, 26)


def get_test_boss_rects(sw, sh, boss_panel_expanded=False, enemy_panel_expanded=False):
    """获取Boss测试按钮的点击区域"""
    if not boss_panel_expanded:
        return []
    from entities.boss import BOSS_CONFIGS
    rects = []
    btn_w, btn_h = 75, 28
    start_x = 15
    start_y = 28 + 5  # Boss折叠按钮高度28 + 间距5，紧跟在按钮下方
    for i, config in enumerate(BOSS_CONFIGS):
        rects.append(pygame.Rect(start_x, start_y + i * (btn_h + 5), btn_w, btn_h))
    # 清屏按钮
    rects.append(pygame.Rect(start_x, start_y + len(BOSS_CONFIGS) * (btn_h + 5), btn_w, btn_h))
    return rects


def get_test_clear_enemies_rect(sw, sh):
    """获取清屏按钮的点击区域"""
    boss_rects = get_test_boss_rects(sw, sh)
    return boss_rects[-1]  # 最后一个就是清屏按钮


def draw_test_mode_panel(screen, font, mouse_pos, auto_spawn_enabled,
                         player_hp, player_max_hp, xp_multiplier,
                         custom_hp, custom_speed, custom_damage=None,
                         debug_stats_enabled=False,
                         enemy_stats=None,
                         enemy_panel_expanded=False,
                         boss_panel_expanded=False,
                         active_input_field=None,
                         custom_enemy_type=0):
    """绘制测试模式面板
    debug_stats_enabled: 是否显示敌人数值
    enemy_stats: 敌人当前数值字典 {type: {hp, damage, explosion_damage}}
    enemy_panel_expanded: 敌人生成面板是否展开
    boss_panel_expanded: Boss测试面板是否展开
    active_input_field: 当前激活的输入框名称 (None, "hp", "damage", "speed")
    custom_enemy_type: 自定义敌人类型索引 (0-4)
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
    enemy_panel_y = sh - 520

    # 面板背景（高度增加以容纳类型选择）
    enemy_panel_rect = pygame.Rect(enemy_panel_x - 5, enemy_panel_y - 5, 200, 185)
    pygame.draw.rect(screen, (25, 22, 30, 230), enemy_panel_rect, border_radius=6)
    pygame.draw.rect(screen, (60, 55, 70), enemy_panel_rect, 1, border_radius=6)

    enemy_title = small_font.render("自定义敌人", True, (200, 180, 140))
    screen.blit(enemy_title, (enemy_panel_x, enemy_panel_y - 2))

    enemy_rects = get_test_custom_enemy_rects(sw, sh)

    # 敌人类型选择
    enemy_type_info = [
        ("基础", (255, 80, 80)),
        ("冲锋", (255, 140, 0)),
        ("射手", (0, 200, 100)),
        ("自爆", (200, 50, 200)),
        ("精英", (50, 150, 255)),
    ]
    type_label = small_font.render("类型:", True, (200, 200, 200))
    screen.blit(type_label, (enemy_panel_x, enemy_rects["type_0"].y))
    for i, (name, color) in enumerate(enemy_type_info):
        rect = enemy_rects[f"type_{i}"]
        hovered = rect.collidepoint(mouse_pos)
        is_selected = (custom_enemy_type == i)
        bg_color = (50, 80, 50) if is_selected else ((30, 25, 35) if not hovered else (50, 45, 60))
        border_color = color
        pygame.draw.rect(screen, bg_color, rect, border_radius=3)
        pygame.draw.rect(screen, border_color, rect, 2 if is_selected else 1, border_radius=3)
        text = tiny_font.render(name, True, color)
        text_rect = text.get_rect(center=rect.center)
        screen.blit(text, text_rect)

    def draw_input_row(label, value, minus_rect, plus_rect, input_rect, field_name, active_field):
        """绘制一行输入控件"""
        label_surf = small_font.render(label, True, (200, 200, 200))
        screen.blit(label_surf, (enemy_panel_x, minus_rect.y))
        pygame.draw.rect(screen, (50, 50, 60), minus_rect, border_radius=3)
        pygame.draw.rect(screen, (50, 50, 60), plus_rect, border_radius=3)
        # 输入框背景色
        input_bg = (80, 80, 100) if active_field == field_name else (40, 40, 50)
        pygame.draw.rect(screen, input_bg, input_rect, border_radius=3)
        pygame.draw.rect(screen, (100, 100, 150), input_rect, 1 if active_field != field_name else 2, border_radius=3)
        screen.blit(small_font.render("-", True, (255, 255, 255)), (minus_rect.centerx - 3, minus_rect.centery - 5))
        screen.blit(small_font.render("+", True, (255, 255, 255)), (plus_rect.centerx - 2, plus_rect.centery - 5))
        val_str = str(value) if value is not None else "0"
        screen.blit(tiny_font.render(val_str, True, (255, 255, 255)), (input_rect.x + 4, input_rect.centery - 4))

    draw_input_row("HP:", custom_hp, enemy_rects["hp_minus"], enemy_rects["hp_plus"], enemy_rects["hp_input"], "hp", active_input_field)
    draw_input_row("伤害:", custom_damage if custom_damage is not None else 1, enemy_rects["damage_minus"], enemy_rects["damage_plus"], enemy_rects["damage_input"], "damage", active_input_field)
    draw_input_row("SPD:", custom_speed, enemy_rects["speed_minus"], enemy_rects["speed_plus"], enemy_rects["speed_input"], "speed", active_input_field)

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

    # ============ 敌人生成面板（左侧折叠式） ============
    # 折叠/展开按钮
    toggle_rect = get_test_enemy_toggle_rect(sw, sh)
    toggle_hovered = toggle_rect.collidepoint(mouse_pos)
    toggle_color = (80, 180, 80) if enemy_panel_expanded else (200, 180, 140)
    pygame.draw.rect(screen, (30, 25, 35) if not toggle_hovered else (50, 45, 60), toggle_rect, border_radius=4)
    pygame.draw.rect(screen, toggle_color, toggle_rect, 1 if not toggle_hovered else 2, border_radius=4)
    expand_text = "▼ 生成敌人" if enemy_panel_expanded else "▶ 生成敌人"
    text = get_font(11).render(expand_text, True, toggle_color)
    text_rect = text.get_rect(center=toggle_rect.center)
    screen.blit(text, text_rect)

    # 如果展开，显示敌人类型选择按钮
    if enemy_panel_expanded:
        # 敌人生成按钮
        enemy_btn_rects = get_test_enemy_rects(sw, sh, expanded=True)
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
            text = get_font(11).render(name, True, color)
            text_rect = text.get_rect(center=rect.center)
            screen.blit(text, text_rect)

        # 自动生成开关（在敌人生成按钮下方）
        auto_rect = get_test_auto_spawn_rect(sw, sh, expanded=True)
        auto_hovered = auto_rect.collidepoint(mouse_pos)
        auto_color = (80, 200, 80) if auto_spawn_enabled else (150, 150, 150)
        pygame.draw.rect(screen, (30, 30, 40), auto_rect, border_radius=4)
        pygame.draw.rect(screen, auto_color, auto_rect, 2 if not auto_hovered else 3, border_radius=4)
        auto_text = "自动 ON" if auto_spawn_enabled else "自动 OFF"
        text = get_font(11).render(auto_text, True, auto_color)
        text_rect = text.get_rect(center=auto_rect.center)
        screen.blit(text, text_rect)
    else:
        # 收起状态下显示自动生成开关
        auto_rect = get_test_auto_spawn_rect(sw, sh, expanded=False)
        auto_hovered = auto_rect.collidepoint(mouse_pos)
        auto_color = (80, 200, 80) if auto_spawn_enabled else (150, 150, 150)
        pygame.draw.rect(screen, (30, 30, 40), auto_rect, border_radius=4)
        pygame.draw.rect(screen, auto_color, auto_rect, 2 if not auto_hovered else 3, border_radius=4)
        auto_text = "自动 ON" if auto_spawn_enabled else "自动 OFF"
        text = get_font(11).render(auto_text, True, auto_color)
        text_rect = text.get_rect(center=auto_rect.center)
        screen.blit(text, text_rect)

    # ============ Boss 测试面板（折叠式） ============
    from entities.boss import BOSS_CONFIGS

    # Boss折叠/展开按钮
    boss_toggle_rect = get_test_boss_toggle_rect(sw, sh, enemy_panel_expanded)
    boss_toggle_hovered = boss_toggle_rect.collidepoint(mouse_pos)
    toggle_color = (80, 180, 80) if boss_panel_expanded else (255, 180, 80)
    pygame.draw.rect(screen, (30, 25, 35) if not boss_toggle_hovered else (50, 45, 60), boss_toggle_rect, border_radius=4)
    pygame.draw.rect(screen, toggle_color, boss_toggle_rect, 1 if not boss_toggle_hovered else 2, border_radius=4)
    expand_text = "▼ Boss测试" if boss_panel_expanded else "▶ Boss测试"
    text = get_font(11).render(expand_text, True, toggle_color)
    text_rect = text.get_rect(center=boss_toggle_rect.center)
    screen.blit(text, text_rect)

    # 如果展开，显示Boss选择按钮（紧跟在折叠按钮下方）
    if boss_panel_expanded:
        boss_toggle_rect = get_test_boss_toggle_rect(sw, sh, enemy_panel_expanded)
        boss_btn_rects = get_test_boss_rects(sw, sh, boss_panel_expanded=True, enemy_panel_expanded=enemy_panel_expanded)
        boss_colors = [
            (40, 80, 20),     # 尸王 - dark green
            (100, 0, 150),    # 暗影巫师 - purple
            (150, 150, 170),  # 钢铁巨像 - gray
            (180, 0, 200),    # 虚空之主 - bright purple
            (200, 60, 60),    # 清屏 - red
        ]
        boss_names = [c["name"] for c in BOSS_CONFIGS] + ["清屏"]
        for i, (name, color) in enumerate(zip(boss_names, boss_colors)):
            if i < len(boss_btn_rects):
                rect = boss_btn_rects[i]
                # 计算相对于折叠按钮的位置
                rect.y = boss_toggle_rect.bottom + 5 + i * 33
                hovered = rect.collidepoint(mouse_pos)
                bg_color = (30, 25, 35) if not hovered else (50, 45, 60)
                pygame.draw.rect(screen, bg_color, rect, border_radius=4)
                pygame.draw.rect(screen, color, rect, 1 if not hovered else 2, border_radius=4)
                text = get_font(11).render(name, True, color)
                text_rect = text.get_rect(center=rect.center)
                screen.blit(text, text_rect)


def get_test_control_rects(sw, sh, enemy_panel_expanded=False, boss_panel_expanded=False):
    """获取测试模式控制按钮的区域（供main.py事件处理使用）"""
    return {
        "player": get_test_player_controls_rect(sw, sh),
        "custom_enemy": get_test_custom_enemy_rects(sw, sh),
        "enemy_toggle": get_test_enemy_toggle_rect(sw, sh),
        "enemy": get_test_enemy_rects(sw, sh, expanded=enemy_panel_expanded),
        "auto_spawn": get_test_auto_spawn_rect(sw, sh, expanded=enemy_panel_expanded),
        "debug_stats": get_test_debug_rect(sw, sh),
        "skill": get_test_skill_rects(sw, sh),
        "boss_toggle": get_test_boss_toggle_rect(sw, sh, enemy_panel_expanded),
        "boss": get_test_boss_rects(sw, sh, boss_panel_expanded=boss_panel_expanded, enemy_panel_expanded=enemy_panel_expanded),
    }
