"""游戏状态管理"""
from settings import (
    FIRE_INTERVAL, PLAYER_SPEED, BULLET_BASE_DAMAGE, BULLET_COUNT_BASE,
    CRIT_MULTIPLIER, PLAYER_MAX_HP, REGEN_KILLS_INITIAL,
    ENEMY_HP, ENEMY_SPEED, ENEMY_SIZE, RED
)
from characters import CHARACTERS


class GameState:
    """游戏状态类，管理所有游戏数据"""

    def __init__(self, character="default"):
        self.character = character
        self.reset(character)

    def reset(self, character="default"):
        """重置所有游戏状态；character 应用角色 stats 覆盖（R5）"""
        self.character = character
        char = CHARACTERS.get(character, CHARACTERS["default"])
        delta = char["stats_delta"]

        self.stats = self.get_default_stats()
        # 角色数值覆盖：stats_delta 中的键绝对覆盖默认值
        for k, v in delta.items():
            if k in self.stats:
                self.stats[k] = v
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
        self.player_hp = self.stats["max_hp"]
        # R5：护盾为角色专属字段（基准 0/10；坦克 5/15）
        self.player_shield = delta.get("player_shield", 0)
        self.player_max_shield = delta.get("player_max_shield", 10)
        self.invincible_timer = 1.5
        self.menu = True
        self.game_over = False
        self.escaped = False  # ESC 暂停状态
        self.test_mode = False
        self.test_auto_spawn = False
        # Boss state
        self.boss_active = False
        self.boss_defeated_count = 0
        self.boss_warning_active = False
        self.boss_warning_timer = 0.0
        # 测试模式控制
        self.test_xp_multiplier = 1.0  # 经验倍率（设为0可禁止经验获取）
        self.test_custom_hp = self.stats["max_hp"]      # 测试血量设置
        self.test_custom_max_hp = self.stats["max_hp"]   # 测试血量上限设置

    def apply_skill_update(self, skill, player, blade_mgr=None):
        """应用技能后更新相关状态"""
        self.acquired_skills.append(skill["name"])
        player.speed = self.stats["player_speed"]
        
        # 血量上限变化时更新玩家血量
        if skill["key"] == "max_hp":
            player.max_hp = self.stats["max_hp"]
        
        # 复苏之风首次获得时初始化击杀进度
        if skill["key"] == "regen_kills" and self.stats["regen_kills_progress"] == 0:
            self.stats["regen_kills_progress"] = 0
        
        if skill["key"] == "has_blades" and blade_mgr:
            blade_mgr.set_count(self.stats.get("blade_count", 3))

    def get_default_stats(self):
        """获取默认属性字典"""
        return {
            "fire_interval": FIRE_INTERVAL,
            "bullet_damage": BULLET_BASE_DAMAGE,
            "player_speed": PLAYER_SPEED,
            "bullet_count": BULLET_COUNT_BASE,
            "damage_taken": 1.0,
            "crit_chance": 0.0,
            "crit_multiplier": CRIT_MULTIPLIER,
            "greedy_count": 0,
            "bullet_speed": 1.0,
            "bullet_pierce": 0,
            "bullet_damage_mult": 1.0,
            "bullet_speed_damage_mult": 1.0,
            "regen_kills": 0,
            "regen_kills_progress": 0,
            "regen_hp_amount": 1,
            "max_hp": PLAYER_MAX_HP,
            "has_blades": 0,
            "blade_count": 0,
            "blade_damage": 0,
            "nova_cooldown": 3.8,
            "nova_radius": 150,
            "has_lightning": 0,
            "lightning_chains": 0,
            "lightning_damage": 0,
            "has_traps": 0,
            "trap_interval": 2.0,
            "trap_damage": 4,
            "trap_radius_mult": 1.0,
            "static_overload": 0,
            "death_echo": 0,
            # C02 新武器（content-pack-v2.md §1）
            "has_frost": 0,
            "frost_radius": 100,
            "frost_damage": 2,
            "frost_slow": 0.20,
            "has_flame": 0,
            "flame_interval": 0.28,
            "flame_damage": 2,
            "flame_burn": 1,
        }
