"""游戏状态管理"""
from settings import (
    FIRE_INTERVAL, PLAYER_SPEED, PICKUP_RANGE,
    CRIT_MULTIPLIER, PLAYER_MAX_HP
)


class GameState:
    """游戏状态类，管理所有游戏数据"""

    def __init__(self):
        self.reset()

    def reset(self):
        """重置所有游戏状态"""
        self.stats = {
            "fire_interval": FIRE_INTERVAL,
            "bullet_damage": 1,
            "player_speed": PLAYER_SPEED,
            "bullet_count": 1,
            "pickup_range": PICKUP_RANGE,
            "damage_taken": 1.0,
            "has_frostbite": 0,
            "crit_chance": 0.0,
            "crit_multiplier": CRIT_MULTIPLIER,
            "has_regen": 0,
            "regen_kills": 0,
            "has_blades": 0,
            "has_lightning": 0,
            "has_traps": 0,
        }
        self.acquired_skills = []
        self.spawn_timer = 0.0
        self.fire_timer = 0.0
        self.score = 0
        self.experience = 0
        self.level = 1
        self.paused = False
        self.chosen_skills = None
        self.elapsed_time = 0.0
        self.difficulty_level = 0
        self.player_hp = PLAYER_MAX_HP
        self.invincible_timer = 1.5
        self.menu = True
        self.game_over = False
        self.test_mode = False
        self.test_auto_spawn = False

    def apply_skill_update(self, skill, player, blade_mgr=None):
        """应用技能后更新相关状态"""
        self.acquired_skills.append(skill["name"])
        player.speed = self.stats["player_speed"]
        if skill["key"] == "has_blades" and blade_mgr:
            blade_mgr.set_count(self.stats["bullet_count"] + self.stats["has_blades"])

    def get_default_stats(self):
        """获取默认属性字典"""
        return {
            "fire_interval": FIRE_INTERVAL,
            "bullet_damage": 1,
            "player_speed": PLAYER_SPEED,
            "bullet_count": 1,
            "pickup_range": PICKUP_RANGE,
            "damage_taken": 1.0,
            "has_frostbite": 0,
            "crit_chance": 0.0,
            "crit_multiplier": CRIT_MULTIPLIER,
            "has_regen": 0,
            "regen_kills": 0,
            "has_blades": 0,
            "has_lightning": 0,
            "has_traps": 0,
        }
