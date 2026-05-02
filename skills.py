import random

SKILL_POOL = [
    # Combat stats
    {
        "name": "火力增强",
        "desc": "子弹伤害按等差数列增加",
        "key": "bullet_damage",
        "delta": 1,
        "is_arithmetic": True,  # 标记为等差数列技能
    },
    {
        "name": "急速射击",
        "desc": "攻击间隔 -25%",
        "key": "fire_interval",
        "factor": 0.75,
    },
    {
        "name": "凌波微步",
        "desc": "移动速度 +25%",
        "key": "player_speed",
        "factor": 1.25,
    },
    {
        "name": "增加弹量",
        "desc": "每次射击 +1 发子弹",
        "key": "bullet_count",
        "delta": 1,
    },
    # Functional modifiers
    {
        "name": "贪婪之魂",
        "desc": "拾取范围 +50%，受伤 +10%",
        "key": "pickup_range",
        "factor": 1.5,
        "side_effect": ("damage_taken", 1.1, "factor"),
    },
    {
        "name": "冰霜光环",
        "desc": "周围敌人永久减速 20%",
        "key": "has_frostbite",
        "delta": 1,
        "aura": True,  # 标记为光环技能
    },
    {
        "name": "致命节奏",
        "desc": "+15% 暴击率，+0.5 暴击伤害（可叠加）",
        "key": "crit_chance",
        "delta": 0.15,
        "crit_multiplier_bonus": 0.5,  # 额外暴击伤害
    },
    {
        "name": "复苏之风",
        "desc": "每击杀 20 敌回复 1 HP（可叠加，需敌量×0.8）",
        "key": "regen_kills",
        "delta": 20,
        "delta_factor": 0.8,
        "min_kills": 5,
    },
    {
        "name": "钢铁意志",
        "desc": "受伤 -10%（重复选取乘算）",
        "key": "damage_taken",
        "factor": 0.9,
    },
    # Weapon unlocks (with stacking)
    {
        "name": "旋转利刃",
        "desc": "初始3个刀刃，伤害10（重复+1刀+2伤）",
        "key": "has_blades",
        "delta": 1,
        "base_count": 3,  # 初始数量
        "base_damage": 10,  # 初始伤害
        "damage_per_stack": 2,  # 每次叠加增加伤害
    },
    {
        "name": "连锁闪电",
        "desc": "初始弹跳8次，伤害8（重复+1跳+2伤）",
        "key": "has_lightning",
        "delta": 1,
        "base_chains": 8,  # 初始弹跳次数
        "base_damage": 8,  # 初始伤害
        "chains_per_stack": 1,  # 每次叠加增加弹跳
        "damage_per_stack": 2,  # 每次叠加增加伤害
    },
    {
        "name": "剧毒地雷",
        "desc": "移动时释放毒雷（间隔-0.1s，伤害+0.5/s，范围×1.1）",
        "key": "has_traps",
        "delta": 1,
        "base_interval": 2.0,  # 基础释放间隔
        "interval_reduction": 0.1,  # 每次叠加减少间隔
        "base_damage": 4,  # 基础伤害
        "damage_per_stack": 0.5,  # 每次叠加增加伤害
        "base_radius_mult": 1.0,  # 基础范围倍率
        "radius_per_stack": 0.1,  # 每次叠加增加范围
    },
]


def get_random_skills(n=3):
    return random.sample(SKILL_POOL, min(n, len(SKILL_POOL)))


def apply_skill(stats, skill):
    key = skill["key"]

    # 等差数列技能（增加弹量）
    if skill.get("is_arithmetic"):
        current = stats.get(key, 1)
        # 等差数列: 1,1,2,2,3,3... 即每两次选择增加1
        if current == 1:
            stats[key] = 1
        else:
            stats[key] = current + 1
    # 旋转利刃
    elif key == "has_blades":
        current = stats.get(key, 0)
        stats[key] = current + 1
        # 第一个时设置初始数量
        if current == 0:
            stats["blade_count"] = skill.get("base_count", 3)
            stats["blade_damage"] = skill.get("base_damage", 10)
        else:
            stats["blade_damage"] += skill.get("damage_per_stack", 2)
    # 连锁闪电
    elif key == "has_lightning":
        current = stats.get(key, 0)
        stats[key] = current + 1
        # 第一个时设置初始值
        if current == 0:
            stats["lightning_chains"] = skill.get("base_chains", 8)
            stats["lightning_damage"] = skill.get("base_damage", 8)
        else:
            stats["lightning_chains"] += skill.get("chains_per_stack", 1)
            stats["lightning_damage"] += skill.get("damage_per_stack", 2)
    # 剧毒地雷
    elif key == "has_traps":
        current = stats.get(key, 0)
        stats[key] = current + 1
        # 第一个时设置初始值
        if current == 0:
            stats["trap_interval"] = skill.get("base_interval", 2.0)
            stats["trap_damage"] = skill.get("base_damage", 4)
            stats["trap_radius_mult"] = skill.get("base_radius_mult", 1.0)
        else:
            stats["trap_interval"] -= skill.get("interval_reduction", 0.1)
            stats["trap_damage"] += skill.get("damage_per_stack", 0.5)
            stats["trap_radius_mult"] += skill.get("radius_per_stack", 0.1)
    # 致命节奏 - 暴击率和暴击伤害
    elif key == "crit_chance":
        stats[key] += skill["delta"]
        if "crit_multiplier_bonus" in skill:
            current_crit_mult = stats.get("crit_multiplier", 2.0)
            stats["crit_multiplier"] = current_crit_mult + skill["crit_multiplier_bonus"]
    # 普通delta技能
    elif "delta" in skill:
        if "delta_factor" in skill:
            current = stats.get(key, skill["delta"])
            stats[key] = int(current * skill["delta_factor"])
            if "min_kills" in skill and stats[key] < skill["min_kills"]:
                stats[key] = skill["min_kills"]
        else:
            stats[key] += skill["delta"]
    # factor技能
    elif "factor" in skill:
        stats[key] *= skill["factor"]

    if "side_effect" in skill:
        side_key, side_val, side_mode = skill["side_effect"]
        if side_mode == "factor":
            stats[side_key] *= side_val
        else:
            stats[side_key] += side_val
