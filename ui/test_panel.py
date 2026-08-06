"""测试模式面板（DN-ENG-TEST-R1 重构：布局集中单一入口）。

- `build_test_layout(...)`：测试面板全部可点击区域的唯一计算入口，返回结构化 dict。
- 旧散落的 get_test_* 函数保留为兼容别名（全部委托 build_test_layout）。
- 渲染（draw_test_mode_panel）与点击分发共用同一份布局，杜绝手工 rect 散落/错位。
- 敌种名称/颜色来自 entities.enemy_types.ENEMY_TYPE_DEFS（单一来源，7 种）。
"""
import pygame
from skills import SKILL_POOL
from entities.boss import BOSS_CONFIGS
from entities.enemy_types import ENEMY_TYPE_DEFS, ENEMY_TYPE_BY_KEY
from .drawables import draw_skill_icon_shape, get_font, SKILL_ICONS

# 技能图标网格（左下 4×4）
_SKILL_ICON_SIZE = 38
_SKILL_PITCH = 46
_SKILL_COLS = 4
_SKILL_START = (15, 60)

# 左侧折叠区
_ENEMY_TOGGLE_RECT = pygame.Rect(15, 248, 80, 28)
_QUICK_SPAWN_START = (15, 286)
_QUICK_SPAWN_COLS = 4
_QUICK_SPAWN_PITCH = (60, 30)
_QUICK_BTN = (55, 28)
_AUTO_RECT_COLLAPSED = pygame.Rect(15, 286, 80, 28)
_AUTO_RECT_EXPANDED = pygame.Rect(15, 414, 80, 28)
_BOSS_TOGGLE_COLLAPSED = pygame.Rect(15, 324, 80, 28)
_BOSS_TOGGLE_EXPANDED = pygame.Rect(15, 452, 80, 28)
_BOSS_BTN = (75, 28)
_BOSS_PITCH = 33


def build_test_layout(sw, sh, enemy_panel_expanded=False, boss_panel_expanded=False):
    """测试面板单一布局入口：返回结构化 dict（全部可点击区域）。

    返回结构：
        player:       玩家控制区 {hp_*, max_hp_*, xp_*, full_hp, add_xp_100, add_xp_500}
        custom_enemy: 自定义敌生成区 {type_0..type_6, hp_*, damage_*, speed_*, spawn}
        enemy_toggle: 敌人生成面板展开/收起按钮
        enemy:        敌种快速生成按钮列表（7 种；收起时为空）
        auto_spawn:   自动生成开关
        boss_toggle:  Boss 面板展开/收起按钮
        boss:         Boss 按钮列表（4 Boss + 清屏；收起时为空）
        skill:        技能图标点击区列表（16 个）
        debug_stats:  调试数值显示开关
    """
    # ---- 技能区（左下 4×4，自上而下）----
    skill = []
    for i in range(len(SKILL_POOL)):
        row = i // _SKILL_COLS
        col = i % _SKILL_COLS
        skill.append(pygame.Rect(_SKILL_START[0] + col * _SKILL_PITCH,
                                 _SKILL_START[1] + row * _SKILL_PITCH,
                                 _SKILL_ICON_SIZE, _SKILL_ICON_SIZE))

    # ---- 左侧折叠区（敌人生成 / 自动生成 / Boss）----
    enemy_toggle = _ENEMY_TOGGLE_RECT
    auto_spawn = _AUTO_RECT_EXPANDED if enemy_panel_expanded else _AUTO_RECT_COLLAPSED
    boss_toggle = _BOSS_TOGGLE_EXPANDED if enemy_panel_expanded else _BOSS_TOGGLE_COLLAPSED

    enemy = []
    if enemy_panel_expanded:
        for i in range(len(ENEMY_TYPE_DEFS)):
            col = i // _QUICK_SPAWN_COLS
            row = i % _QUICK_SPAWN_COLS
            enemy.append(pygame.Rect(_QUICK_SPAWN_START[0] + col * _QUICK_SPAWN_PITCH[0],
                                     _QUICK_SPAWN_START[1] + row * _QUICK_SPAWN_PITCH[1],
                                     _QUICK_BTN[0], _QUICK_BTN[1]))

    boss = []
    if boss_panel_expanded:
        start_x = 15
        start_y = boss_toggle.bottom + 5  # 位置由布局统一计算（去掉 y hack）
        for i in range(len(BOSS_CONFIGS) + 1):  # 4 Boss + 独立"清屏"按钮
            boss.append(pygame.Rect(start_x, start_y + i * _BOSS_PITCH,
                                    _BOSS_BTN[0], _BOSS_BTN[1]))

    # ---- 玩家控制区（右）----
    panel_x = sw - 220
    panel_y = sh - 300
    player = {
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
        # DN-ENG-TEST-R2：沙盒控制（升级开关 / 重置）
        "upgrade_toggle": pygame.Rect(panel_x + 55, panel_y + 140, 90, 24),
        "reset": pygame.Rect(panel_x + 55, panel_y + 168, 90, 24),
    }

    # ---- 自定义敌生成区（右）----
    cpanel_x = sw - 220
    cpanel_y = sh - 520
    custom_enemy = {}
    for i in range(len(ENEMY_TYPE_DEFS)):
        col = i % 4
        row = i // 4
        custom_enemy[f"type_{i}"] = pygame.Rect(
            cpanel_x + 30 + col * 40, cpanel_y + 22 + row * 26, 38, 22)
    custom_enemy["hp_minus"] = pygame.Rect(cpanel_x + 30, cpanel_y + 74, 22, 22)
    custom_enemy["hp_plus"] = pygame.Rect(cpanel_x + 55, cpanel_y + 74, 22, 22)
    custom_enemy["hp_input"] = pygame.Rect(cpanel_x + 80, cpanel_y + 74, 65, 22)
    custom_enemy["damage_minus"] = pygame.Rect(cpanel_x + 30, cpanel_y + 102, 22, 22)
    custom_enemy["damage_plus"] = pygame.Rect(cpanel_x + 55, cpanel_y + 102, 22, 22)
    custom_enemy["damage_input"] = pygame.Rect(cpanel_x + 80, cpanel_y + 102, 65, 22)
    custom_enemy["speed_minus"] = pygame.Rect(cpanel_x + 30, cpanel_y + 130, 22, 22)
    custom_enemy["speed_plus"] = pygame.Rect(cpanel_x + 55, cpanel_y + 130, 22, 22)
    custom_enemy["speed_input"] = pygame.Rect(cpanel_x + 80, cpanel_y + 130, 65, 22)
    custom_enemy["spawn"] = pygame.Rect(cpanel_x + 60, cpanel_y + 158, 55, 28)

    # ---- 调试区（右，玩家面板下方）----
    debug_stats = pygame.Rect(sw - 220, sh - 90, 90, 26)

    return {
        "player": player,
        "custom_enemy": custom_enemy,
        "enemy_toggle": enemy_toggle,
        "enemy": enemy,
        "auto_spawn": auto_spawn,
        "boss_toggle": boss_toggle,
        "boss": boss,
        "skill": skill,
        "debug_stats": debug_stats,
    }


# ================================================================
# 兼容别名（旧散落函数全部委托 build_test_layout；对外行为不变）
# ================================================================

def get_test_control_rects(sw, sh, enemy_panel_expanded=False, boss_panel_expanded=False):
    """获取测试模式全部控制按钮区域（兼容入口）。"""
    return build_test_layout(sw, sh, enemy_panel_expanded, boss_panel_expanded)


def get_test_skill_rects(sw, sh):
    return build_test_layout(sw, sh)["skill"]


def get_test_player_controls_rect(sw, sh):
    return build_test_layout(sw, sh)["player"]


def get_test_custom_enemy_rects(sw, sh):
    return build_test_layout(sw, sh)["custom_enemy"]


def get_test_enemy_rects(sw, sh, expanded=False):
    return build_test_layout(sw, sh, enemy_panel_expanded=expanded)["enemy"]


def get_test_auto_spawn_rect(sw, sh, expanded=False):
    return build_test_layout(sw, sh, enemy_panel_expanded=expanded)["auto_spawn"]


def get_test_debug_rect(sw, sh):
    return build_test_layout(sw, sh)["debug_stats"]


def get_test_enemy_toggle_rect(sw, sh):
    return build_test_layout(sw, sh)["enemy_toggle"]


def get_test_boss_toggle_rect(sw, sh, enemy_panel_expanded=False):
    return build_test_layout(sw, sh, enemy_panel_expanded=enemy_panel_expanded)["boss_toggle"]


def get_test_boss_rects(sw, sh, boss_panel_expanded=False, enemy_panel_expanded=False):
    return build_test_layout(sw, sh, enemy_panel_expanded=enemy_panel_expanded,
                             boss_panel_expanded=boss_panel_expanded)["boss"]


def get_test_clear_enemies_rect(sw, sh):
    return build_test_layout(sw, sh, boss_panel_expanded=True)["boss"][-1]


# ================================================================
# 渲染
# ================================================================

def _draw_button(screen, font, rect, text, color, bg=(30, 25, 35),
                 hovered=False, border=1, border_radius=4):
    fill = (50, 45, 60) if hovered else bg
    pygame.draw.rect(screen, fill, rect, border_radius=border_radius)
    pygame.draw.rect(screen, color, rect, border if not hovered else border + 1,
                     border_radius=border_radius)
    surf = font.render(text, True, color)
    screen.blit(surf, surf.get_rect(center=rect.center))


def draw_test_mode_panel(screen, font, mouse_pos, state, enemy_stats=None):
    """绘制测试模式面板。

    state: TestPanelState（单一状态源；也可传任意同名字段对象）。
    enemy_stats: 敌人当前数值字典 {type: {hp, damage, explosion_damage}}。
    """
    sw, sh = screen.get_width(), screen.get_height()
    small_font = get_font(11)
    tiny_font = get_font(10)
    layout = build_test_layout(sw, sh,
                               state.enemy_panel_expanded,
                               state.boss_panel_expanded)

    # 测试模式标识
    test_label = font.render("[ 测试模式 ]", True, (100, 255, 100))
    screen.blit(test_label, (10, 10))

    # ============ 调试面板 ============
    debug_rect = layout["debug_stats"]
    debug_hovered = debug_rect.collidepoint(mouse_pos)
    debug_color = (80, 200, 80) if state.debug_stats_enabled else (150, 150, 150)
    debug_text = "数值 ON" if state.debug_stats_enabled else "数值 OFF"
    _draw_button(screen, tiny_font, debug_rect, debug_text, debug_color,
                 bg=(30, 30, 40), hovered=debug_hovered,
                 border=2 if not debug_hovered else 3)

    # ============ 敌人数值显示 ============
    if state.debug_stats_enabled and enemy_stats:
        stats_y = 45
        stats_x = sw - 220
        for enemy_type, stats in enemy_stats.items():
            definition = ENEMY_TYPE_BY_KEY.get(enemy_type)
            name = definition["name"] if definition else enemy_type
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
    panel_rect = pygame.Rect(panel_x - 5, panel_y - 5, 200, 200)  # 含沙盒控制两行（R2）
    pygame.draw.rect(screen, (25, 22, 30, 230), panel_rect, border_radius=6)
    pygame.draw.rect(screen, (60, 55, 70), panel_rect, 1, border_radius=6)
    title = small_font.render("玩家控制", True, (200, 180, 140))
    screen.blit(title, (panel_x, panel_y - 2))

    control_rects = layout["player"]

    # 当前血量
    hp_text = small_font.render(f"血量: {state.custom_hp}", True, (255, 100, 100))
    screen.blit(hp_text, (panel_x, panel_y + 18))
    pygame.draw.rect(screen, (50, 50, 60), control_rects["hp_minus"], border_radius=3)
    pygame.draw.rect(screen, (50, 50, 60), control_rects["hp_plus"], border_radius=3)
    pygame.draw.rect(screen, (60, 140, 80), control_rects["hp_apply"], border_radius=3)
    screen.blit(small_font.render("-", True, (255, 255, 255)),
                (control_rects["hp_minus"].centerx - 3, control_rects["hp_minus"].centery - 5))
    screen.blit(small_font.render("+", True, (255, 255, 255)),
                (control_rects["hp_plus"].centerx - 2, control_rects["hp_plus"].centery - 5))
    screen.blit(tiny_font.render("应用", True, (255, 255, 255)),
                (control_rects["hp_apply"].centerx - 9, control_rects["hp_apply"].centery - 4))

    # 血量上限
    max_hp_text = small_font.render(f"上限: {state.custom_max_hp}", True, (255, 180, 100))
    screen.blit(max_hp_text, (panel_x, panel_y + 48))
    pygame.draw.rect(screen, (50, 50, 60), control_rects["max_hp_minus"], border_radius=3)
    pygame.draw.rect(screen, (50, 50, 60), control_rects["max_hp_plus"], border_radius=3)
    pygame.draw.rect(screen, (60, 140, 80), control_rects["max_hp_apply"], border_radius=3)
    screen.blit(small_font.render("-", True, (255, 255, 255)),
                (control_rects["max_hp_minus"].centerx - 3, control_rects["max_hp_minus"].centery - 5))
    screen.blit(small_font.render("+", True, (255, 255, 255)),
                (control_rects["max_hp_plus"].centerx - 2, control_rects["max_hp_plus"].centery - 5))
    screen.blit(tiny_font.render("应用", True, (255, 255, 255)),
                (control_rects["max_hp_apply"].centerx - 9, control_rects["max_hp_apply"].centery - 4))

    # 经验倍率
    xp_text = small_font.render(f"经验x{state.xp_multiplier:.1f}", True, (180, 180, 255))
    screen.blit(xp_text, (panel_x, panel_y + 78))
    pygame.draw.rect(screen, (50, 50, 60), control_rects["xp_minus"], border_radius=3)
    pygame.draw.rect(screen, (50, 50, 60), control_rects["xp_plus"], border_radius=3)
    pygame.draw.rect(screen, (100, 80, 60), control_rects["xp_apply"], border_radius=3)
    screen.blit(small_font.render("-", True, (255, 255, 255)),
                (control_rects["xp_minus"].centerx - 3, control_rects["xp_minus"].centery - 5))
    screen.blit(small_font.render("+", True, (255, 255, 255)),
                (control_rects["xp_plus"].centerx - 2, control_rects["xp_plus"].centery - 5))
    screen.blit(tiny_font.render("应用", True, (255, 255, 255)),
                (control_rects["xp_apply"].centerx - 9, control_rects["xp_apply"].centery - 4))

    # 快捷按钮
    pygame.draw.rect(screen, (80, 50, 50), control_rects["full_hp"], border_radius=3)
    pygame.draw.rect(screen, (50, 80, 50), control_rects["add_xp_100"], border_radius=3)
    pygame.draw.rect(screen, (50, 80, 50), control_rects["add_xp_500"], border_radius=3)
    screen.blit(tiny_font.render("满血", True, (255, 255, 255)),
                (control_rects["full_hp"].centerx - 9, control_rects["full_hp"].centery - 4))
    screen.blit(tiny_font.render("+100", True, (255, 255, 255)),
                (control_rects["add_xp_100"].centerx - 11, control_rects["add_xp_100"].centery - 4))
    screen.blit(tiny_font.render("+500", True, (255, 255, 255)),
                (control_rects["add_xp_500"].centerx - 11, control_rects["add_xp_500"].centery - 4))

    # 沙盒控制（R2）：升级开关 / 重置
    up_label = small_font.render("升级:", True, (200, 200, 200))
    screen.blit(up_label, (panel_x, control_rects["upgrade_toggle"].y + 1))
    up_color = (80, 200, 80) if state.allow_level_up else (150, 150, 150)
    up_text = "开" if state.allow_level_up else "关"
    pygame.draw.rect(screen, (50, 50, 60), control_rects["upgrade_toggle"], border_radius=3)
    pygame.draw.rect(screen, up_color, control_rects["upgrade_toggle"],
                     2 if state.allow_level_up else 1, border_radius=3)
    screen.blit(tiny_font.render(up_text, True, up_color),
                (control_rects["upgrade_toggle"].centerx - 3,
                 control_rects["upgrade_toggle"].centery - 4))

    reset_label = small_font.render("重置:", True, (200, 200, 200))
    screen.blit(reset_label, (panel_x, control_rects["reset"].y + 1))
    reset_color = (220, 90, 70)
    pygame.draw.rect(screen, (60, 40, 40), control_rects["reset"], border_radius=3)
    pygame.draw.rect(screen, reset_color, control_rects["reset"], 1, border_radius=3)
    screen.blit(tiny_font.render("重置", True, reset_color),
                (control_rects["reset"].centerx - 9, control_rects["reset"].centery - 4))

    # ============ 自定义敌人生成面板 ============
    enemy_panel_x = sw - 220
    enemy_panel_y = sh - 520
    enemy_panel_rect = pygame.Rect(enemy_panel_x - 5, enemy_panel_y - 5, 200, 196)
    pygame.draw.rect(screen, (25, 22, 30, 230), enemy_panel_rect, border_radius=6)
    pygame.draw.rect(screen, (60, 55, 70), enemy_panel_rect, 1, border_radius=6)
    enemy_title = small_font.render("自定义敌人", True, (200, 180, 140))
    screen.blit(enemy_title, (enemy_panel_x, enemy_panel_y - 2))

    enemy_rects = layout["custom_enemy"]

    # 敌人类型选择（ENEMY_TYPE_DEFS 7 种，2 行）
    type_label = small_font.render("类型:", True, (200, 200, 200))
    screen.blit(type_label, (enemy_panel_x, enemy_rects["type_0"].y))
    for i, definition in enumerate(ENEMY_TYPE_DEFS):
        rect = enemy_rects[f"type_{i}"]
        hovered = rect.collidepoint(mouse_pos)
        is_selected = (state.custom_enemy_type == i)
        bg_color = (50, 80, 50) if is_selected else ((30, 25, 35) if not hovered else (50, 45, 60))
        border_color = definition["color"]
        pygame.draw.rect(screen, bg_color, rect, border_radius=3)
        pygame.draw.rect(screen, border_color, rect, 2 if is_selected else 1, border_radius=3)
        text = tiny_font.render(definition["name"], True, border_color)
        screen.blit(text, text.get_rect(center=rect.center))

    def draw_input_row(label, value, minus_rect, plus_rect, input_rect, field_name, active_field):
        label_surf = small_font.render(label, True, (200, 200, 200))
        screen.blit(label_surf, (enemy_panel_x, minus_rect.y))
        pygame.draw.rect(screen, (50, 50, 60), minus_rect, border_radius=3)
        pygame.draw.rect(screen, (50, 50, 60), plus_rect, border_radius=3)
        input_bg = (80, 80, 100) if active_field == field_name else (40, 40, 50)
        pygame.draw.rect(screen, input_bg, input_rect, border_radius=3)
        pygame.draw.rect(screen, (100, 100, 150), input_rect,
                         1 if active_field != field_name else 2, border_radius=3)
        screen.blit(small_font.render("-", True, (255, 255, 255)),
                    (minus_rect.centerx - 3, minus_rect.centery - 5))
        screen.blit(small_font.render("+", True, (255, 255, 255)),
                    (plus_rect.centerx - 2, plus_rect.centery - 5))
        val_str = str(value) if value is not None else "0"
        screen.blit(tiny_font.render(val_str, True, (255, 255, 255)),
                    (input_rect.x + 4, input_rect.centery - 4))

    draw_input_row("HP:", state.custom_hp,
                   enemy_rects["hp_minus"], enemy_rects["hp_plus"], enemy_rects["hp_input"],
                   "hp", state.active_input_field)
    draw_input_row("伤害:", state.custom_damage,
                   enemy_rects["damage_minus"], enemy_rects["damage_plus"],
                   enemy_rects["damage_input"], "damage", state.active_input_field)
    draw_input_row("SPD:", state.custom_speed,
                   enemy_rects["speed_minus"], enemy_rects["speed_plus"],
                   enemy_rects["speed_input"], "speed", state.active_input_field)

    # 生成按钮
    pygame.draw.rect(screen, (50, 150, 80), enemy_rects["spawn"], border_radius=4)
    pygame.draw.rect(screen, (100, 255, 150), enemy_rects["spawn"], 2, border_radius=4)
    screen.blit(small_font.render("生成", True, (255, 255, 255)),
                (enemy_rects["spawn"].centerx - 12, enemy_rects["spawn"].centery - 5))

    # ============ 技能面板 ============
    skill_title = font.render("技能 (点击添加):", True, (200, 180, 140))
    screen.blit(skill_title, (15, 35))

    for i, skill in enumerate(SKILL_POOL):
        rect = layout["skill"][i]
        hovered = rect.collidepoint(mouse_pos)
        icon_info = SKILL_ICONS.get(skill["name"], {
            "color": (100, 100, 100), "glow": (150, 150, 150),
            "shape": "crit", "border": (80, 80, 80)
        })
        bg_rect = pygame.Rect(rect.x, rect.y, _SKILL_ICON_SIZE, _SKILL_ICON_SIZE)
        pygame.draw.rect(screen, (20, 18, 25), bg_rect, border_radius=4)
        pygame.draw.rect(screen, icon_info["border"] if not hovered else icon_info["glow"],
                         bg_rect, 1, border_radius=4)
        draw_skill_icon_shape(screen, rect.x, rect.y, _SKILL_ICON_SIZE, icon_info)

    # ============ 敌人生成面板（左侧折叠式） ============
    toggle_rect = layout["enemy_toggle"]
    toggle_hovered = toggle_rect.collidepoint(mouse_pos)
    toggle_color = (80, 180, 80) if state.enemy_panel_expanded else (200, 180, 140)
    expand_text = "▼ 生成敌人" if state.enemy_panel_expanded else "▶ 生成敌人"
    _draw_button(screen, get_font(11), toggle_rect, expand_text, toggle_color,
                 hovered=toggle_hovered)

    if state.enemy_panel_expanded:
        for i, definition in enumerate(ENEMY_TYPE_DEFS):
            rect = layout["enemy"][i]
            _draw_button(screen, get_font(11), rect, definition["name"],
                         definition["color"], hovered=rect.collidepoint(mouse_pos))

    # 自动生成开关
    auto_rect = layout["auto_spawn"]
    auto_hovered = auto_rect.collidepoint(mouse_pos)
    auto_color = (80, 200, 80) if state.auto_spawn else (150, 150, 150)
    auto_text = "自动 ON" if state.auto_spawn else "自动 OFF"
    _draw_button(screen, get_font(11), auto_rect, auto_text, auto_color,
                 bg=(30, 30, 40), hovered=auto_hovered, border=2 if auto_hovered else 1)

    # ============ Boss 测试面板（折叠式） ============
    boss_toggle_rect = layout["boss_toggle"]
    boss_toggle_hovered = boss_toggle_rect.collidepoint(mouse_pos)
    toggle_color = (80, 180, 80) if state.boss_panel_expanded else (255, 180, 80)
    expand_text = "▼ Boss测试" if state.boss_panel_expanded else "▶ Boss测试"
    _draw_button(screen, get_font(11), boss_toggle_rect, expand_text, toggle_color,
                 hovered=boss_toggle_hovered)

    if state.boss_panel_expanded:
        boss_colors = [c["color"] for c in BOSS_CONFIGS] + [(200, 60, 60)]  # 清屏红
        boss_names = [c["name"] for c in BOSS_CONFIGS] + ["清屏"]
        for i, rect in enumerate(layout["boss"]):
            _draw_button(screen, get_font(11), rect, boss_names[i], boss_colors[i],
                         hovered=rect.collidepoint(mouse_pos))
