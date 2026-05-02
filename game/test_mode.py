"""测试模式处理器"""
import random
from settings import (
    MAP_WIDTH, MAP_HEIGHT, ELITE_HP, ELITE_SPEED,
    ELITE_SIZE, BLUE
)


class TestModeHandler:
    """测试模式逻辑处理器"""

    def __init__(self):
        self.auto_spawn = False

    def handle_skill_click(self, skill, stats, player, blade_mgr):
        """处理技能面板点击"""
        from skills import apply_skill
        apply_skill(stats, skill)
        player.speed = stats["player_speed"]
        if skill["key"] == "has_blades":
            blade_mgr.set_count(stats["bullet_count"] + stats["has_blades"])

    def spawn_enemy_near_player(self, enemy_type, enemies, player):
        """在玩家附近生成敌人"""
        from entities import Enemy, Charger, Ranger, Exploder

        spawn_x = player.rect.centerx + random.randint(-100, 100)
        spawn_y = player.rect.centery + random.randint(-100, 100)
        spawn_x = max(50, min(MAP_WIDTH - 50, spawn_x))
        spawn_y = max(50, min(MAP_HEIGHT - 50, spawn_y))

        if enemy_type == "basic":
            enemies.add(Enemy(spawn_x, spawn_y))
        elif enemy_type == "charger":
            enemies.add(Charger(spawn_x, spawn_y))
        elif enemy_type == "ranger":
            enemies.add(Ranger(spawn_x, spawn_y))
        elif enemy_type == "exploder":
            enemies.add(Exploder(spawn_x, spawn_y))
        elif enemy_type == "elite":
            enemies.add(Enemy(spawn_x, spawn_y, hp=ELITE_HP, speed=ELITE_SPEED,
                              size=ELITE_SIZE, color=BLUE, is_elite=True, sprite_name="elite"))

    def toggle_auto_spawn(self):
        """切换自动生成状态"""
        self.auto_spawn = not self.auto_spawn
        return self.auto_spawn

    def should_spawn_enemies(self, test_mode):
        """判断是否应该生成敌人"""
        return not test_mode or self.auto_spawn
