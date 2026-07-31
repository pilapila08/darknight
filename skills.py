import random
from settings import (
    FIRE_INTERVAL, PLAYER_SPEED, PLAYER_MAX_HP, CRIT_MULTIPLIER,
    REGEN_KILLS_INITIAL, MAX_BULLET_SPEED_MULT, SKILL_DEFS,
    STATIC_OVERLOAD_CD_REDUCTION, DEATH_ECHO_RADIUS, DEATH_ECHO_DAMAGE,
)

# R3：技能数值唯一源 = settings.SKILL_DEFS（playability-pack-v1.md §1.2）
_NOVA = SKILL_DEFS["nova"]
_LIGHTNING = SKILL_DEFS["lightning"]
_TRAP = SKILL_DEFS["trap"]
_PIERCE = SKILL_DEFS["pierce"]

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
        "desc": "攻击间隔 -15%（最低0.18s）",
        "key": "fire_interval",
        "factor": 0.85,
        "min_value": 0.18,
    },
    {
        "name": "凌波微步",
        "desc": "移动速度 +25%",
        "key": "player_speed",
        "factor": 1.25,
    },
    {
        "name": "贪婪之魂",
        "desc": "经验获取 +15%（线性叠加）",
        "key": "greedy_count",
        "factor": 0.15,
        "is_xp_mult": True,  # 标记为经验倍率技能
    },
    {
        "name": "穿透弹",
        "desc": "子弹穿透+1目标，伤害×0.85，弹速×1.5（最多3层）",
        "key": "bullet_speed",
        "factor": _PIERCE["factor"],
        "damage_mult": _PIERCE["damage_mult"],
        "max_pierce": _PIERCE["max_pierce"],
    },
    {
        "name": "增加弹量",
        "desc": "每次射击 +1 发子弹（第4发起每发伤害×0.55）",
        "key": "bullet_count",
        "delta": 1,
    },
    # Functional modifiers
    {
        "name": "致命节奏",
        "desc": "+10% 暴击率，+0.25 暴击伤害（暴击率最高60%）",
        "key": "crit_chance",
        "delta": 0.10,
        "max_value": 0.60,
        "crit_multiplier_bonus": 0.25,  # 额外暴击伤害
    },
    {
        "name": "复苏之风",
        "desc": "每击杀 N 敌回复 HP（击杀要求×0.8降至最小后，重复+0.5回复）",
        "key": "regen_kills",
        "delta": 20,
        "delta_factor": 0.8,
        "min_kills": 5,
        "regen_hp_initial": 1,
        "regen_hp_bonus": 0.5,
    },
    {
        "name": "钢铁意志",
        "desc": "受伤 -10%（重复选取乘算）",
        "key": "damage_taken",
        "factor": 0.9,
    },
    # Weapon unlocks (with stacking)
    {
        "name": "暗影新星",
        "desc": "周期性释放范围冲击波，击退并伤害周围敌人",
        "key": "has_blades",
        "delta": 1,
        "base_count": _NOVA["base_count"],
        "base_damage": _NOVA["base_damage"],
        "damage_per_stack": _NOVA["damage_per_stack"],
        "base_cooldown": _NOVA["base_cooldown"],
        "cooldown_reduction": _NOVA["cooldown_reduction"],
        "min_cooldown": _NOVA["min_cooldown"],
        "base_radius": _NOVA["base_radius"],
        "radius_per_stack": _NOVA["radius_per_stack"],
    },
    {
        "name": "连锁闪电",
        "desc": "初始弹跳5次，伤害7（重复+1跳+1伤）",
        "key": "has_lightning",
        "delta": 1,
        "base_chains": _LIGHTNING["base_chains"],
        "base_damage": _LIGHTNING["base_damage"],
        "chains_per_stack": _LIGHTNING["chains_per_stack"],
        "damage_per_stack": _LIGHTNING["damage_per_stack"],
    },
    {
        "name": "剧毒地雷",
        "desc": "自动释放毒雷（间隔-0.1s至最低1.2s，伤害+0.5/s，范围×1.05）",
        "key": "has_traps",
        "delta": 1,
        "base_interval": _TRAP["base_interval"],
        "interval_reduction": _TRAP["interval_reduction"],
        "min_interval": _TRAP["min_interval"],
        "base_damage": _TRAP["base_damage"],
        "damage_per_stack": _TRAP["damage_per_stack"],
        "base_radius_mult": _TRAP["base_radius_mult"],
        "radius_per_stack": _TRAP["radius_per_stack"],
    },
    # 联动技能（R3 §4.4，池 12→14）
    {
        "name": "静电过载",
        "desc": "连锁闪电每次命中使暗影新星CD-0.15s；未拥有新星时获得+1层",
        "key": "static_overload",
        "delta": 1,
    },
    {
        "name": "死亡回响",
        "desc": "击杀精英/Boss时，周围200px敌人受12伤害并击退",
        "key": "death_echo",
        "delta": 1,
    },
]


def get_skill_by_name(name):
    """根据名称获取技能定义"""
    for skill in SKILL_POOL:
        if skill["name"] == name:
            return skill
    return None


def get_skill_effect_desc(skill_name, stats, skill_count=1):
    """获取技能当前效果的简洁描述
    skill_count: 该技能被选取的次数（用于显示加成）
    """
    skill = get_skill_by_name(skill_name)
    if not skill:
        return ""

    key = skill["key"]

    # 特殊处理：基于选择次数显示预期效果
    if key == "bullet_damage":
        count_key = f"{key}_count"
        count = stats.get(count_key, 0)
        current = stats.get(key, 2)
        base = stats.get(f"{key}_base", 2)
        if count > 0:
            next_k = (count + 2) // 2
            if (count + 1) % 2 == 1:
                next_growth = next_k * next_k
            else:
                next_growth = next_k * (next_k + 1)
            next_val = base + next_growth
            inc = next_val - current
            return f"伤害 {current} → {next_val}（+{inc}）"
        return f"伤害 {current}"
    elif key == "fire_interval":
        current = stats.get(key, FIRE_INTERVAL)
        if skill_count > 1:
            next_val = max(skill["min_value"], current * skill["factor"])
            return f"间隔 {current:.2f}s → {next_val:.2f}s"
        return f"间隔 {current:.2f}s"
    elif key == "player_speed":
        current = stats.get(key, PLAYER_SPEED)
        if skill_count > 1:
            next_val = int(current * 1.25)
            return f"速度 {current} → {next_val}"
        return f"速度 {current}"
    elif key == "greedy_count":
        count = stats.get(key, 0)
        if count > 0:
            mult = 1.0 + 0.15 * count
            next_mult = 1.0 + 0.15 * (count + 1)
            return f"经验 ×{mult:.2f} → ×{next_mult:.2f}"
        return "未激活"
    elif key == "bullet_speed":
        # 穿透弹（R3 B1）：显示穿透层数与弹速
        mult = stats.get(key, 1.0)
        pierce = stats.get("bullet_pierce", 0)
        if pierce >= skill["max_pierce"]:
            return f"穿透{pierce} / 速度×{mult:.2f}（已达上限）"
        if skill_count > 1:
            next_mult = min(mult * skill["factor"], MAX_BULLET_SPEED_MULT)
            return f"穿透{pierce}→{pierce+1} / 速度×{mult:.2f}→×{next_mult:.2f}"
        return f"穿透{pierce} / 速度×{mult:.2f}"
    elif key == "bullet_count":
        current = stats.get(key, 1)
        next_val = current + 1
        if skill_count > 1:
            return f"弹量 {current} → {next_val}（+1，第4发起×0.55）"
        return f"弹量 {current}"
    elif key == "crit_chance":
        crit = stats.get(key, 0)
        mult = stats.get("crit_multiplier", CRIT_MULTIPLIER)
        if skill_count > 1:
            next_crit = min(skill["max_value"], crit + skill["delta"])
            return f"暴击 {int(crit*100)}%→{int(next_crit*100)}% / {mult:.2f}x+0.25"
        return f"暴击 {int(crit*100)}% / {mult:.1f}x"
    elif key == "regen_kills":
        current = stats.get(key, 0)
        regen_hp = stats.get("regen_hp_amount", 1)
        min_kills = skill["min_kills"]
        if current > 0:
            if current <= min_kills:
                if skill_count > 1:
                    next_hp = regen_hp + skill["regen_hp_bonus"]
                    return f"击杀 {current} 只回 {regen_hp} → {next_hp} HP"
                return f"击杀 {current} 只回 {regen_hp} HP"
            else:
                next_val = int(current * 0.8)
                if next_val < min_kills:
                    next_val = min_kills
                if skill_count > 1:
                    return f"击杀 {current} → {next_val} 只回 {regen_hp} HP"
                return f"击杀 {current} 只回 {regen_hp} HP"
        return "未激活"
    elif key == "damage_taken":
        current = stats.get(key, 1.0)
        reduction = (1 - current) * 100
        if skill_count > 1:
            next_val = current * 0.9
            next_reduction = (1 - next_val) * 100
            return f"减伤 {int(reduction)}% → {int(next_reduction)}%"
        return f"减伤 {int(reduction)}%"
    elif key == "has_blades":
        if stats.get(key, 0) == 0:
            return "未激活"
        cooldown = stats.get("nova_cooldown", skill["base_cooldown"])
        radius = stats.get("nova_radius", skill["base_radius"])
        blade_damage = stats.get("blade_damage", skill["base_damage"])
        if skill_count > 1:
            next_cd = max(skill["min_cooldown"], cooldown - skill["cooldown_reduction"])
            return f"伤{blade_damage}→{blade_damage+skill['damage_per_stack']} / {cooldown:.1f}s→{next_cd:.1f}s"
        return f"伤{blade_damage} / 半径{radius} / {cooldown:.1f}s"
    elif key == "has_lightning":
        if stats.get(key, 0) == 0:
            return "未激活"
        chains = stats.get("lightning_chains", skill["base_chains"])
        dmg = stats.get("lightning_damage", skill["base_damage"])
        if skill_count > 1:
            return f"{chains}跳/{dmg}伤 → {chains+1}跳/{dmg+skill['damage_per_stack']}伤"
        return f"{chains}跳 / 伤{dmg}"
    elif key == "has_traps":
        if stats.get(key, 0) == 0:
            return "未激活"
        interval = stats.get("trap_interval", skill["base_interval"])
        dmg = stats.get("trap_damage", skill["base_damage"])
        radius = stats.get("trap_radius_mult", skill["base_radius_mult"])
        if skill_count > 1:
            next_interval = max(skill["min_interval"], interval - skill["interval_reduction"])
            return f"{interval:.1f}s/{dmg}伤 → {next_interval:.1f}s/{dmg+skill['damage_per_stack']}伤"
        return f"间隔{interval:.1f}s / 伤{dmg}"
    elif key == "static_overload":
        if stats.get(key, 0) == 0:
            return "未激活"
        if stats.get("has_blades", 0) > 0:
            return f"闪电命中减新星CD {STATIC_OVERLOAD_CD_REDUCTION:.2f}s"
        return "获得暗影新星 +1 层"
    elif key == "death_echo":
        if stats.get(key, 0) == 0:
            return "未激活"
        return f"精英/Boss击杀引爆 {DEATH_ECHO_DAMAGE} 伤 / {DEATH_ECHO_RADIUS}px"
    return ""


def get_skill_detail_desc(skill_name, stats, acquired_count):
    """获取技能详细描述，包含初始效果、当前效果和下次选择加成
    acquired_count: 该技能已被选择的次数
    """
    skill = get_skill_by_name(skill_name)
    if not skill:
        return "", "", ""

    key = skill["key"]
    is_first = acquired_count == 0

    # 首次选择的初始效果
    if key == "bullet_damage":
        base = stats.get(f"{key}_base", stats.get(key, 2))
        if is_first:
            initial = f"初始伤害 {base}+1，之后+1+2+2+3..."
        else:
            count_key = f"{key}_count"
            count = stats.get(count_key, 0)
            current = stats.get(key, base)
            next_k = (count + 2) // 2
            if (count + 1) % 2 == 1:
                next_growth = next_k * next_k
            else:
                next_growth = next_k * (next_k + 1)
            next_val = base + next_growth
            inc = next_val - current
            initial = f"下次选择变为 {next_val}（+{inc}）"
        current = get_skill_effect_desc(skill_name, stats, acquired_count)
        return skill["desc"], current, initial

    elif key == "fire_interval":
        base = FIRE_INTERVAL
        current = stats.get(key, base)
        next_val = max(skill["min_value"], current * skill["factor"])
        initial = f"下次选择: {next_val:.2f}s（-15%）"
        return skill["desc"], current, initial

    elif key == "player_speed":
        base = PLAYER_SPEED
        current = stats.get(key, base)
        next_val = int(current * 1.25)
        initial = f"下次选择: 速度{next_val}（+25%）"
        return skill["desc"], current, initial

    elif key == "greedy_count":
        count = stats.get(key, 0)
        if is_first:
            current_mult = 1.0
            next_mult = 1.15
            initial = f"下次选择: 经验×{next_mult:.2f}"
        else:
            current_mult = 1.0 + 0.15 * count
            next_mult = 1.0 + 0.15 * (count + 1)
            initial = f"下次选择: 经验×{next_mult:.2f}"
        current_str = f"经验×{current_mult:.2f}" if count > 0 else "未激活"
        return skill["desc"], current_str, initial

    elif key == "bullet_speed":
        # 穿透弹（R3 B1）
        mult = stats.get(key, 1.0)
        pierce = stats.get("bullet_pierce", 0)
        if pierce >= skill["max_pierce"]:
            current = f"穿透{pierce}（已达上限）/ 速度×{mult:.2f}"
            initial = "已达上限，不再出现在升级选项中"
            return skill["desc"], current, initial
        next_mult = min(mult * skill["factor"], MAX_BULLET_SPEED_MULT)
        initial = f"下次选择: 穿透{pierce+1} / 速度×{next_mult:.2f}"
        current = f"穿透{pierce} / 速度×{mult:.2f}"
        return skill["desc"], current, initial

    elif key == "bullet_count":
        base = 1
        current = stats.get(key, base)
        next_val = current + 1
        initial = f"下次选择: +1发（{next_val}发，第4发起每发×0.55）"
        return skill["desc"], current, initial

    elif key == "crit_chance":
        crit = stats.get(key, 0)
        mult = stats.get("crit_multiplier", CRIT_MULTIPLIER)
        next_crit = min(skill["max_value"], crit + skill["delta"])
        next_mult = mult + skill["crit_multiplier_bonus"]
        initial = f"下次选择: 暴击{int(next_crit*100)}% / {next_mult:.1f}x"
        current_str = f"暴击 {int(crit*100)}% / {mult:.1f}x"
        return skill["desc"], current_str, initial

    elif key == "regen_kills":
        min_kills = skill["min_kills"]
        regen_hp = stats.get("regen_hp_amount", 1)
        current_val = stats.get(key, 0)
        if is_first:
            current_str = "未激活"
            initial = f"初始: 每击杀{REGEN_KILLS_INITIAL}只回1血（降至{min_kills}后+0.5血）"
        else:
            if current_val <= min_kills:
                next_hp = regen_hp + skill["regen_hp_bonus"]
                initial = f"下次选择: 每击杀{current_val}只回{next_hp} HP（+0.5）"
            else:
                next_val = int(current_val * 0.8)
                if next_val < min_kills:
                    next_val = min_kills
                initial = f"下次选择: 每击杀{next_val}只回{regen_hp} HP"
            current_str = f"每击杀{current_val}只回{regen_hp}血"
        return skill["desc"], current_str, initial

    elif key == "damage_taken":
        current = stats.get(key, 1.0)
        reduction = (1 - current) * 100
        next_val = current * 0.9
        next_reduction = (1 - next_val) * 100
        initial = f"下次选择: 减伤{int(next_reduction)}%（-10%）"
        current_str = f"减伤 {int(reduction)}%"
        return skill["desc"], current_str, initial

    elif key == "has_blades":
        base_dmg = skill["base_damage"]
        base_cd = skill["base_cooldown"]
        base_radius = skill["base_radius"]
        if is_first:
            initial = f"激活: 范围{base_radius} / 伤{base_dmg} / {base_cd:.1f}s"
        else:
            current_dmg = stats.get("blade_damage", base_dmg)
            current_cd = stats.get("nova_cooldown", base_cd)
            current_radius = stats.get("nova_radius", base_radius)
            next_dmg = current_dmg + skill["damage_per_stack"]
            next_cd = max(skill["min_cooldown"], current_cd - skill["cooldown_reduction"])
            initial = f"下次: 伤{next_dmg} / {next_cd:.1f}s / 半径{current_radius+skill['radius_per_stack']}"
        current_dmg = stats.get("blade_damage", base_dmg)
        current_str = f"范围{stats.get('nova_radius', base_radius)} / 伤{current_dmg}"
        return skill["desc"], current_str, initial

    elif key == "has_lightning":
        base_chains = skill["base_chains"]
        base_dmg = skill["base_damage"]
        if is_first:
            initial = f"激活: {base_chains}跳 / 伤{base_dmg}（重复+1跳+1伤）"
        else:
            current_chains = stats.get("lightning_chains", base_chains)
            current_dmg = stats.get("lightning_damage", base_dmg)
            initial = f"下次选择: {current_chains+1}跳 / 伤{current_dmg+skill['damage_per_stack']}"
        chains = stats.get("lightning_chains", base_chains)
        dmg = stats.get("lightning_damage", base_dmg)
        current_str = f"{chains}跳 / 伤{dmg}"
        return skill["desc"], current_str, initial

    elif key == "has_traps":
        base_interval = skill["base_interval"]
        base_dmg = skill["base_damage"]
        base_radius = skill["base_radius_mult"]
        if is_first:
            initial = f"激活: 间隔{base_interval}s / 伤{base_dmg}/s / 范围×{base_radius}"
        else:
            current_interval = stats.get("trap_interval", base_interval)
            current_dmg = stats.get("trap_damage", base_dmg)
            current_radius = stats.get("trap_radius_mult", base_radius)
            next_interval = max(skill["min_interval"], current_interval - skill["interval_reduction"])
            initial = f"下次: 间隔{next_interval:.1f}s / 伤{current_dmg+skill['damage_per_stack']}/s / 范围×{current_radius+skill['radius_per_stack']:.2f}"
        interval = stats.get("trap_interval", base_interval)
        dmg = stats.get("trap_damage", base_dmg)
        radius = stats.get("trap_radius_mult", base_radius)
        current_str = f"间隔{interval:.1f}s / 伤{dmg}/s / ×{radius:.1f}"
        return skill["desc"], current_str, initial

    elif key == "static_overload":
        current_str = "闪电命中减新星CD 0.15s" if stats.get(key, 0) > 0 else "未激活"
        initial = "下次: 强化联动（闪电→新星CD）"
        return skill["desc"], current_str, initial

    elif key == "death_echo":
        current_str = "精英/Boss击杀引爆" if stats.get(key, 0) > 0 else "未激活"
        initial = "下次: 强化回响"
        return skill["desc"], current_str, initial

    return skill["desc"], "", ""


def _skill_available(skill, stats):
    if not stats:
        return True
    key = skill["key"]
    if key == "bullet_speed":
        if stats.get("bullet_pierce", 0) >= skill["max_pierce"]:
            return False
        if stats.get("bullet_speed", 1.0) >= MAX_BULLET_SPEED_MULT:
            return False
    if key == "fire_interval" and stats.get("fire_interval", FIRE_INTERVAL) <= skill["min_value"]:
        return False
    if key == "crit_chance" and stats.get("crit_chance", 0.0) >= skill["max_value"]:
        return False
    return True


def get_random_skills(n=3, stats=None):
    available = [skill for skill in SKILL_POOL if _skill_available(skill, stats)]
    if not available:
        available = SKILL_POOL[:]
    return random.sample(available, min(n, len(available)))


def apply_skill(stats, skill):
    key = skill["key"]

    # 等差数列技能（子弹伤害）
    if skill.get("is_arithmetic"):
        count_key = f"{key}_count"
        count = stats.get(count_key, 0) + 1
        stats[count_key] = count
        if count == 1:
            stats[f"{key}_base"] = stats.get(key, 2)
        base = stats.get(f"{key}_base", 2)
        k = (count + 1) // 2
        if count % 2 == 1:
            growth = k * k
        else:
            growth = k * (k + 1)
        stats[key] = base + growth
    # 暗影新星
    elif key == "has_blades":
        current = stats.get(key, 0)
        stats[key] = current + 1
        if current == 0:
            stats["blade_count"] = skill["base_count"]
            stats["blade_damage"] = skill["base_damage"]
            stats["nova_cooldown"] = skill["base_cooldown"]
            stats["nova_radius"] = skill["base_radius"]
        else:
            stats["blade_damage"] += skill["damage_per_stack"]
            stats["nova_cooldown"] = max(
                skill["min_cooldown"],
                stats.get("nova_cooldown", skill["base_cooldown"]) - skill["cooldown_reduction"]
            )
            stats["nova_radius"] = stats.get("nova_radius", skill["base_radius"]) + skill["radius_per_stack"]
    # 连锁闪电
    elif key == "has_lightning":
        current = stats.get(key, 0)
        stats[key] = current + 1
        if current == 0:
            stats["lightning_chains"] = skill["base_chains"]
            stats["lightning_damage"] = skill["base_damage"]
        else:
            stats["lightning_chains"] += skill["chains_per_stack"]
            stats["lightning_damage"] += skill["damage_per_stack"]
    # 剧毒地雷
    elif key == "has_traps":
        current = stats.get(key, 0)
        stats[key] = current + 1
        if current == 0:
            stats["trap_interval"] = skill["base_interval"]
            stats["trap_damage"] = skill["base_damage"]
            stats["trap_radius_mult"] = skill["base_radius_mult"]
        else:
            stats["trap_interval"] = max(
                skill["min_interval"],
                stats["trap_interval"] - skill["interval_reduction"]
            )
            stats["trap_damage"] += skill["damage_per_stack"]
            stats["trap_radius_mult"] += skill["radius_per_stack"]
    # 穿透弹（R3 §4.3 B1 重做）
    elif key == "bullet_speed":
        current_speed = stats.get(key, 1.0)
        if current_speed < MAX_BULLET_SPEED_MULT:
            stats[key] = min(current_speed * skill["factor"], MAX_BULLET_SPEED_MULT)
        if stats.get("bullet_pierce", 0) < skill["max_pierce"]:
            stats["bullet_pierce"] = stats.get("bullet_pierce", 0) + 1
            if stats["bullet_pierce"] >= 1:
                stats["bullet_damage_mult"] = skill["damage_mult"]
    # 静电过载（R3 §4.4 C1）
    elif key == "static_overload":
        if stats.get("has_blades", 0) == 0:
            # 首次选取：获得暗影新星 +1 层
            stats["has_blades"] = 1
            stats["blade_count"] = _NOVA["base_count"]
            stats["blade_damage"] = _NOVA["base_damage"]
            stats["nova_cooldown"] = _NOVA["base_cooldown"]
            stats["nova_radius"] = _NOVA["base_radius"]
        stats["static_overload"] = stats.get("static_overload", 0) + 1
    # 死亡回响（R3 §4.4 C2）
    elif key == "death_echo":
        stats["death_echo"] = stats.get("death_echo", 0) + 1
    # 致命节奏 - 暴击率和暴击伤害
    elif key == "crit_chance":
        before = stats[key]
        stats[key] = min(skill["max_value"], stats[key] + skill["delta"])
        if stats[key] > before and "crit_multiplier_bonus" in skill:
            current_crit_mult = stats.get("crit_multiplier", 2.0)
            stats["crit_multiplier"] = current_crit_mult + skill["crit_multiplier_bonus"]
    # 贪婪之魂 - 经验倍率计数
    elif key == "greedy_count":
        stats[key] = stats.get(key, 0) + 1
    # 普通delta技能
    elif "delta" in skill:
        if "delta_factor" in skill:
            # 复苏之风特殊处理
            if key == "regen_kills":
                current = stats.get(key, 0)
                min_kills = skill["min_kills"]
                if current == 0:
                    stats[key] = skill["delta"]
                    stats["regen_hp_amount"] = skill["regen_hp_initial"]
                elif current <= min_kills:
                    stats["regen_hp_amount"] = stats.get("regen_hp_amount", 1) + skill["regen_hp_bonus"]
                else:
                    stats[key] = int(current * skill["delta_factor"])
                    if stats[key] < min_kills:
                        stats[key] = min_kills
            else:
                current = stats.get(key, skill["delta"])
                stats[key] = int(current * skill["delta_factor"])
                if "min_kills" in skill and stats[key] < skill["min_kills"]:
                    stats[key] = skill["min_kills"]
        else:
            stats[key] += skill["delta"]
    # factor技能
    elif "factor" in skill:
        stats[key] *= skill["factor"]
        if "min_value" in skill:
            stats[key] = max(skill["min_value"], stats[key])

    if "side_effect" in skill:
        side_key, side_val, side_mode = skill["side_effect"]
        if side_mode == "factor":
            stats[side_key] *= side_val
        else:
            stats[side_key] += side_val
