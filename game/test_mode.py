"""测试模式处理器"""
import random
from settings import (
    MAP_WIDTH, MAP_HEIGHT, ELITE_HP, ELITE_SPEED,
    ELITE_SIZE, BLUE, ENEMY_HP, ENEMY_SPEED,
    ENEMY_SIZE, RED, GREEN
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
            blade_mgr.set_count(stats.get("blade_count", 3))

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

    def spawn_custom_enemy(self, enemies, player, hp, speed, size=None, color=None):
        """在玩家附近生成自定义属性的敌人"""
        from entities import Enemy

        spawn_x = player.rect.centerx + random.randint(-100, 100)
        spawn_y = player.rect.centery + random.randint(-100, 100)
        spawn_x = max(50, min(MAP_WIDTH - 50, spawn_x))
        spawn_y = max(50, min(MAP_HEIGHT - 50, spawn_y))

        # 使用提供的值或默认值
        hp = hp if hp > 0 else ENEMY_HP
        speed = speed if speed > 0 else ENEMY_SPEED
        size = size if size else ENEMY_SIZE
        color = color if color else GREEN  # 绿色表示自定义敌人

        enemies.add(Enemy(spawn_x, spawn_y, hp=hp, speed=speed,
                          size=size, color=color, is_elite=False))

    def toggle_auto_spawn(self):
        """切换自动生成状态"""
        self.auto_spawn = not self.auto_spawn
        return self.auto_spawn

    def should_spawn_enemies(self, test_mode):
        """判断是否应该生成敌人"""
        return not test_mode or self.auto_spawn
