"""测试模式处理器（DN-ENG-TEST-R1 重构）。

设计（单一状态源）：
- `TestPanelState`：测试面板全部状态的唯一存放处（自定义数值/经验倍率/自动生成开关/
  面板展开/激活输入框/调试开关/自定义敌种索引），TestGame 不再散落实例属性。
- `TestModeHandler`：状态 + 生成/技能/输入逻辑；生成统一走 `ENEMY_TYPE_DEFS`，
  wraith/warlock 复用 BaseGame._spawn_enemy（C02 已实现路径，避免重复实现）。
- TestGame 只持有 handler 一个引用；game_state.test_xp_multiplier /
  game_state.test_auto_spawn 保留为镜像键（BaseGame 钩子与旧代码兼容，勿删）。
"""
import math
import random
from dataclasses import dataclass

from settings import (
    MAP_WIDTH, MAP_HEIGHT, ENEMY_SPEED, ENEMY_SIZE,
    ELITE_HP, ELITE_SPEED, ELITE_SIZE, BLUE, GREEN, RED,
    PLAYER_MAX_HP,
)
from entities import Enemy, Exploder
from entities.enemy_types import ENEMY_TYPE_DEFS, ENEMY_TYPE_BY_KEY
from entities.boss import BOSS_CLASSES
from skills import apply_skill


class TestInputField:
    """输入框标识（替代魔法字符串 "hp"/"damage"/"speed"）。"""

    HP = "hp"
    DAMAGE = "damage"
    SPEED = "speed"


# wraith/warlock 复用 base_game._spawn_enemy（C02 已实现构造路径），不走自定义表 cls 分支
_C02_REUSE_TYPES = ("wraith", "warlock")


@dataclass
class TestPanelState:
    """测试面板全部状态的单一来源。"""

    custom_hp: int = PLAYER_MAX_HP            # 自定义敌人 HP
    custom_max_hp: int = PLAYER_MAX_HP        # 玩家血量上限设置
    custom_speed: int = ENEMY_SPEED           # 自定义敌人速度
    custom_damage: int = 1                    # 自定义敌人伤害
    xp_multiplier: float = 1.0                # 经验倍率（game_state.test_xp_multiplier 镜像）
    auto_spawn: bool = False                  # 自动生成开关（game_state.test_auto_spawn 镜像）
    enemy_panel_expanded: bool = False        # 敌人生成面板展开
    boss_panel_expanded: bool = False         # Boss 测试面板展开
    active_input_field: object = None         # TestInputField 或 None
    debug_stats_enabled: bool = False         # 调试数值显示开关
    custom_enemy_type: int = 0                # 自定义敌种索引（ENEMY_TYPE_DEFS 下标）
    allow_level_up: bool = False              # 升级开关（默认关：击杀不触发升级弹窗/冻结）


class TestModeHandler:
    """测试模式逻辑处理器（状态 + 生成/技能/输入逻辑）。"""

    def __init__(self):
        self.state = TestPanelState()

    # ------------------------------------------------------------ 状态

    def toggle_auto_spawn(self):
        self.state.auto_spawn = not self.state.auto_spawn
        return self.state.auto_spawn

    def should_spawn_enemies(self, test_mode):
        """是否允许自动刷怪（test 模式受 auto_spawn 开关控制）。"""
        return not test_mode or self.state.auto_spawn

    def toggle_enemy_panel(self):
        self.state.enemy_panel_expanded = not self.state.enemy_panel_expanded

    def toggle_boss_panel(self):
        self.state.boss_panel_expanded = not self.state.boss_panel_expanded

    def toggle_debug_stats(self):
        self.state.debug_stats_enabled = not self.state.debug_stats_enabled

    def toggle_level_up(self):
        """切换升级开关（默认关：测试模式不触发升级弹窗，移动不冻结）。"""
        self.state.allow_level_up = not self.state.allow_level_up
        return self.state.allow_level_up

    def set_custom_enemy_type(self, index):
        if 0 <= index < len(ENEMY_TYPE_DEFS):
            self.state.custom_enemy_type = index

    def activate_input(self, field):
        self.state.active_input_field = field

    def deactivate_input(self):
        self.state.active_input_field = None

    # ------------------------------------------------------------ 输入（TEXTINPUT）

    def apply_text_input(self, text):
        """输入框激活时收集 TEXTINPUT 文本（与主菜单一致）；忽略非数字。"""
        field = self.state.active_input_field
        if field is None:
            return
        for ch in text:
            if ch.isdigit():
                value = int(ch)
                if field == TestInputField.HP:
                    self.state.custom_hp = min(99999, self.state.custom_hp * 10 + value)
                elif field == TestInputField.DAMAGE:
                    self.state.custom_damage = min(99999, self.state.custom_damage * 10 + value)
                elif field == TestInputField.SPEED:
                    self.state.custom_speed = min(9999, self.state.custom_speed * 10 + value)

    def backspace_input(self):
        field = self.state.active_input_field
        if field == TestInputField.HP:
            self.state.custom_hp = max(1, self.state.custom_hp // 10)
        elif field == TestInputField.DAMAGE:
            self.state.custom_damage = max(1, self.state.custom_damage // 10)
        elif field == TestInputField.SPEED:
            self.state.custom_speed = max(10, self.state.custom_speed // 10)

    # ------------------------------------------------------------ 技能

    def handle_skill_click(self, skill, stats, player, blade_mgr, character=None):
        """处理技能面板点击（character 用于 R5 专属被动）。"""
        apply_skill(stats, skill, character)
        player.speed = stats["player_speed"]
        if skill["key"] == "has_blades":
            blade_mgr.set_count(stats.get("blade_count", 3))

    # ------------------------------------------------------------ 生成

    def _clamp_spawn(self, player):
        x = player.rect.centerx + random.randint(-100, 100)
        y = player.rect.centery + random.randint(-100, 100)
        return max(50, min(MAP_WIDTH - 50, x)), max(50, min(MAP_HEIGHT - 50, y))

    def _build_enemy(self, game, enemy_type, x, y,
                     hp=None, speed=None, damage=None, color=None):
        """按 ENEMY_TYPE_DEFS 生成敌人。

        wraith/warlock 复用 game._spawn_enemy（C02 已实现路径，避免重复实现）；
        其余类型走定义表生成类；自定义数值（hp/speed/damage）在构造后统一覆写。
        """
        definition = ENEMY_TYPE_BY_KEY.get(enemy_type, ENEMY_TYPE_BY_KEY["basic"])
        if enemy_type in _C02_REUSE_TYPES and game is not None:
            enemy = game._spawn_enemy(enemy_type_override=enemy_type, tier_override=0, pos=(x, y))
        elif enemy_type == "exploder":
            enemy = Exploder(x, y, hp=hp if hp is not None else definition["default_hp"],
                             explosion_damage=(damage if damage is not None else 1) * 2)
        elif enemy_type == "elite":
            enemy = Enemy(x, y, hp=hp if hp is not None else ELITE_HP,
                          speed=speed if speed is not None else ELITE_SPEED,
                          size=ELITE_SIZE, color=BLUE, is_elite=True, sprite_name="elite",
                          contact_damage=damage if damage is not None else 1)
        elif enemy_type == "basic":
            enemy = Enemy(x, y, hp=hp if hp is not None else definition["default_hp"],
                          speed=speed if speed is not None else definition["default_speed"],
                          size=ENEMY_SIZE, color=color if color is not None else RED,
                          is_elite=False, contact_damage=damage if damage is not None else 1)
        else:
            cls = definition["cls"]
            enemy = cls(x, y, hp=hp if hp is not None else definition["default_hp"],
                        damage=damage if damage is not None else 1)
        # 自定义数值覆写（构造后统一，兼容 wraith/warlock 固定速度类）
        if speed is not None:
            enemy.speed = speed
            if hasattr(enemy, "_base_speed"):
                enemy._base_speed = speed
        if hp is not None:
            enemy.hp = hp
            enemy.max_hp = hp
        if damage is not None and enemy_type != "exploder":
            # exploder 保持旧行为：无接触伤害（仅爆炸），爆炸伤害已在构造时按 damage×2 设置
            enemy.contact_damage = damage
        return enemy

    def spawn_enemy_near_player(self, enemy_type, enemies, player, game=None):
        """在玩家附近生成默认参数敌人（快速生成按钮）。"""
        x, y = self._clamp_spawn(player)
        enemies.add(self._build_enemy(game, enemy_type, x, y))

    def spawn_custom_enemy_with_type(self, enemies, player, enemy_type,
                                     hp, speed, damage=None, game=None):
        """在玩家附近生成指定类型的自定义敌人（HP/伤害/速度可调）。"""
        x, y = self._clamp_spawn(player)
        color = GREEN if enemy_type == "basic" else None  # 保留旧视觉：基础自定义怪绿色
        enemies.add(self._build_enemy(game, enemy_type, x, y,
                                      hp=hp, speed=speed, damage=damage, color=color))

    def spawn_boss_near_player(self, boss_index, player):
        """在玩家附近生成指定 Boss（BOSS_CLASSES 枚举）。"""
        if boss_index >= len(BOSS_CLASSES):
            return None
        angle = random.uniform(0, math.pi * 2)
        dist = random.randint(200, 400)
        bx = player.rect.centerx + int(math.cos(angle) * dist)
        by = player.rect.centery + int(math.sin(angle) * dist)
        bx = max(50, min(MAP_WIDTH - 50, bx))
        by = max(50, min(MAP_HEIGHT - 50, by))
        return BOSS_CLASSES[boss_index](bx, by)
