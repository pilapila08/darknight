import random

SKILL_POOL = [
    # Combat stats
    {
        "name": "火力增强",
        "desc": "子弹伤害 +1",
        "key": "bullet_damage",
        "delta": 1,
    },
    {
        "name": "急速射击",
        "desc": "攻击间隔 -15%",
        "key": "fire_interval",
        "factor": 0.85,
    },
    {
        "name": "凌波微步",
        "desc": "移动速度 +15%",
        "key": "player_speed",
        "factor": 1.15,
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
        "desc": "击中敌人永久减速 20%",
        "key": "has_frostbite",
        "delta": 1,
    },
    {
        "name": "致命节奏",
        "desc": "+10% 暴击率（2倍伤害+击退）",
        "key": "crit_chance",
        "delta": 0.10,
    },
    {
        "name": "复苏之风",
        "desc": f"每击杀 50 个敌人回复 1 HP",
        "key": "has_regen",
        "delta": 1,
    },
    # Weapon unlocks (binary: picked once)
    {
        "name": "旋转利刃",
        "desc": "获得环绕刀刃（始终存在，触敌即伤）",
        "key": "has_blades",
        "delta": 1,
    },
    {
        "name": "连锁闪电",
        "desc": "获得弹跳闪电（自动打击多个敌人）",
        "key": "has_lightning",
        "delta": 1,
    },
    {
        "name": "剧毒地雷",
        "desc": "获得毒雷（移动时自动释放毒圈）",
        "key": "has_traps",
        "delta": 1,
    },
]


def get_random_skills(n=3):
    return random.sample(SKILL_POOL, min(n, len(SKILL_POOL)))


def apply_skill(stats, skill):
    if "delta" in skill:
        stats[skill["key"]] += skill["delta"]
    elif "factor" in skill:
        stats[skill["key"]] *= skill["factor"]

    if "side_effect" in skill:
        side_key, side_val, side_mode = skill["side_effect"]
        if side_mode == "factor":
            stats[side_key] *= side_val
        else:
            stats[side_key] += side_val
