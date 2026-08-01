"""R5 角色系统：角色定义、数值覆盖、解锁条件、专属被动钩子。

依据：design/gdd/playability-pack-v1.md §3（R5 角色解锁设计）。
- stats_delta：对 GameState 默认 stats 的覆盖（绝对覆盖；护盾用 player_shield / player_max_shield 两个特殊键）。
- unlock_condition：回调读 meta 字典 → bool（None 表示默认解锁）。
- passive：apply_skill 的专属乘区钩子，key 见 skills.apply_skill 对应分支：
    bullet_damage_growth_mult  火力增强 等差成长 ×N（火枪手 1.5）
    damage_taken_factor_mult    钢铁意志 每层额外 ×N（坦克 0.97 → 0.9×0.97/层）
    fire_interval_factor        急速射击 乘区替换（游侠 0.78）
    player_speed_factor_mult    凌波微步 每层额外 ×N（游侠 1.03 → 1.25×1.03/层）
"""

CHARACTERS = {
    "default": {
        "name": "幸存者",
        "desc": ["均衡起点：", "20HP / 390移速 / 2伤 / 0.6s"],
        "stats_delta": {},
        "unlock_condition": None,
        "passive": {},
        "passive_text": "无专属被动",
        "unlock_text": "",
    },
    "gunslinger": {
        "name": "火枪手",
        "desc": ["玻璃大炮：", "12HP / 400移速 / 3伤 / 0.55s / 暴击+10%"],
        "stats_delta": {
            "max_hp": 12,
            "player_speed": 400,
            "bullet_damage": 3,
            "fire_interval": 0.55,
            "crit_chance": 0.10,
        },
        "unlock_condition": lambda meta: (
            meta.get("total_kills", 0) >= 500
            or meta.get("best_run_kills", 0) >= 250
        ),
        "passive": {"bullet_damage_growth_mult": 1.5},
        "passive_text": "被动·火药专家：火力增强成长 ×1.5",
        "unlock_text": "累计击杀500 或 单局击杀250",
    },
    "vanguard": {
        "name": "重装坦克",
        "desc": ["站桩生存：", "32HP / 330移速 / 0.65s / 护盾5(上限15) / 减伤15%"],
        "stats_delta": {
            "max_hp": 32,
            "player_speed": 330,
            "fire_interval": 0.65,
            "damage_taken": 0.85,
            "player_shield": 5,
            "player_max_shield": 15,
        },
        "unlock_condition": lambda meta: (
            meta.get("boss_kills", 0) >= 1
            or meta.get("best_time", 0.0) >= 360
        ),
        "passive": {"damage_taken_factor_mult": 0.97},
        "passive_text": "被动·钢铁壁垒：钢铁意志每层再-3%伤",
        "unlock_text": "累计击杀Boss 1 或 单局存活360s",
    },
    "wayfarer": {
        "name": "游侠",
        "desc": ["攻速压制：", "18HP / 430移速 / 0.45s"],
        "stats_delta": {
            "max_hp": 18,
            "player_speed": 430,
            "fire_interval": 0.45,
        },
        "unlock_condition": lambda meta: (
            meta.get("best_run_kills", 0) >= 200
            or meta.get("total_kills", 0) >= 2000
        ),
        "passive": {
            "fire_interval_factor": 0.78,
            "player_speed_factor_mult": 1.03,
        },
        "passive_text": "被动·疾风连射 ×0.78 + 灵动 +3%移速/层",
        "unlock_text": "单局击杀200 或 累计击杀2000",
    },
}

# 角色展示/导航顺序（default 恒在前）
CHARACTER_ORDER = ["default", "gunslinger", "vanguard", "wayfarer"]


def get_character(name):
    """按 key 取角色配置；未知 key 回退 default。"""
    return CHARACTERS.get(name, CHARACTERS["default"])


def is_default_unlocked(character):
    """default 恒解锁；其余由 unlock_condition 判定（只读 meta，不落盘）。"""
    if character == "default":
        return True
    cfg = CHARACTERS.get(character)
    if cfg is None or cfg.get("unlock_condition") is None:
        return True
    return False
