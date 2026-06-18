import random
from settings import FIRE_INTERVAL, PLAYER_SPEED, PLAYER_MAX_HP, CRIT_MULTIPLIER, REGEN_KILLS_INITIAL, MAX_BULLET_SPEED_MULT

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
        "name": "急速子弹",
        "desc": "子弹飞行速度 ×1.5",
        "key": "bullet_speed",
        "factor": 1.5,
    },
    {
        "name": "增加弹量",
        "desc": "每次射击 +1 发子弹",
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
        "base_count": 1,
        "base_damage": 12,
        "damage_per_stack": 3,
        "base_cooldown": 3.8,
        "cooldown_reduction": 0.25,
        "min_cooldown": 2.2,
        "base_radius": 150,
        "radius_per_stack": 12,
    },
    {
        "name": "连锁闪电",
        "desc": "初始弹跳5次，伤害7（重复+1跳+1伤）",
        "key": "has_lightning",
        "delta": 1,
        "base_chains": 5,  # 初始弹跳次数
        "base_damage": 7,  # 初始伤害
        "chains_per_stack": 1,  # 每次叠加增加弹跳
        "damage_per_stack": 1,  # 每次叠加增加伤害
    },
    {
        "name": "剧毒地雷",
        "desc": "自动释放毒雷（间隔-0.1s至最低1.2s，伤害+0.5/s，范围×1.05）",
        "key": "has_traps",
        "delta": 1,
        "base_interval": 2.0,  # 基础释放间隔
        "interval_reduction": 0.1,  # 每次叠加减少间隔
        "min_interval": 1.2,
        "base_damage": 4,  # 基础伤害
        "damage_per_stack": 0.5,  # 每次叠加增加伤害
        "base_radius_mult": 1.0,  # 基础范围倍率
        "radius_per_stack": 0.05,  # 每次叠加增加范围
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
        # 如果已经选过，显示当前值和下次预期值
        if count > 0:
            # 等差数列累加：+1+1+2+2+3+3...
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
            next_val = max(skill.get("min_value", 0.18), current * skill.get("factor", 0.85))
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
        mult = stats.get(key, 1.0)
        if mult >= MAX_BULLET_SPEED_MULT:
            return f"速度 ×{mult:.2f}（已达上限）"
        if skill_count > 1:
            next_mult = min(mult * 1.5, MAX_BULLET_SPEED_MULT)
            return f"速度 ×{mult:.2f} → ×{next_mult:.2f}"
        return f"速度 ×{mult:.2f}"
    elif key == "bullet_count":
        current = stats.get(key, 1)
        next_val = current + 1
        if skill_count > 1:
            return f"弹量 {current} → {next_val}（+1）"
        return f"弹量 {current}"
    elif key == "crit_chance":
        crit = stats.get(key, 0)
        mult = stats.get("crit_multiplier", CRIT_MULTIPLIER)
        if skill_count > 1:
            next_crit = min(skill.get("max_value", 0.6), crit + skill.get("delta", 0.1))
            return f"暴击 {int(crit*100)}%→{int(next_crit*100)}% / {mult:.2f}x+0.25"
        return f"暴击 {int(crit*100)}% / {mult:.1f}x"
    elif key == "regen_kills":
        current = stats.get(key, 0)
        regen_hp = stats.get("regen_hp_amount", 1)
        min_kills = skill.get("min_kills", 5)
        if current > 0:
            # 达到最小值后显示回复血量
            if current <= min_kills:
                if skill_count > 1:
                    next_hp = regen_hp + skill.get("regen_hp_bonus", 0.5)
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
        cooldown = stats.get("nova_cooldown", skill.get("base_cooldown", 3.8))
        radius = stats.get("nova_radius", skill.get("base_radius", 150))
        blade_damage = stats.get("blade_damage", skill.get("base_damage", 8))
        if skill_count > 1:
            next_cd = max(skill.get("min_cooldown", 2.2), cooldown - skill.get("cooldown_reduction", 0.25))
            return f"伤{blade_damage}→{blade_damage+skill.get('damage_per_stack', 3)} / {cooldown:.1f}s→{next_cd:.1f}s"
        return f"伤{blade_damage} / 半径{radius} / {cooldown:.1f}s"
    elif key == "has_lightning":
        if stats.get(key, 0) == 0:
            return "未激活"
        chains = stats.get("lightning_chains", skill.get("base_chains", 5))
        dmg = stats.get("lightning_damage", skill.get("base_damage", 7))
        if skill_count > 1:
            return f"{chains}跳/{dmg}伤 → {chains+1}跳/{dmg+skill.get('damage_per_stack', 1)}伤"
        return f"{chains}跳 / 伤{dmg}"
    elif key == "has_traps":
        if stats.get(key, 0) == 0:
            return "未激活"
        interval = stats.get("trap_interval", 2.0)
        dmg = stats.get("trap_damage", 4)
        radius = stats.get("trap_radius_mult", 1.0)
        if skill_count > 1:
            next_interval = max(skill.get("min_interval", 1.2), interval - skill.get("interval_reduction", 0.1))
            return f"{interval:.1f}s/{dmg}伤 → {next_interval:.1f}s/{dmg+0.5}伤"
        return f"间隔{interval:.1f}s / 伤{dmg}"
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
            # 计算下次选择后的值和增量
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
        if is_first:
            next_val = max(skill.get("min_value", 0.18), current * skill.get("factor", 0.85))
            initial = f"下次选择: {next_val:.2f}s（-15%）"
        else:
            next_val = max(skill.get("min_value", 0.18), current * skill.get("factor", 0.85))
            initial = f"下次选择: {next_val:.2f}s（-15%）"
        return skill["desc"], current, initial

    elif key == "player_speed":
        base = PLAYER_SPEED
        current = stats.get(key, base)
        if is_first:
            next_val = int(current * 1.25)
            initial = f"下次选择: 速度{next_val}（+25%）"
        else:
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
        mult = stats.get(key, 1.0)
        if mult >= MAX_BULLET_SPEED_MULT:
            current = f"子弹速度×{mult:.2f}（已达上限）"
            initial = "已达上限，不再出现在升级选项中"
            return skill["desc"], current, initial
        next_mult = min(mult * 1.5, MAX_BULLET_SPEED_MULT)
        if is_first:
            initial = f"下次选择: 子弹速度×{next_mult:.2f}"
        else:
            initial = f"下次选择: 子弹速度×{next_mult:.2f}"
        current = f"子弹速度×{mult:.2f}"
        return skill["desc"], current, initial

    elif key == "bullet_count":
        base = 1
        current = stats.get(key, base)
        next_val = current + 1
        if is_first:
            initial = f"下次选择: +1发（{next_val}发）"
        else:
            initial = f"下次选择: +1发（{next_val}发）"
        return skill["desc"], current, initial

    elif key == "crit_chance":
        crit = stats.get(key, 0)
        mult = stats.get("crit_multiplier", CRIT_MULTIPLIER)
        if is_first:
            next_crit = min(skill.get("max_value", 0.6), crit + skill.get("delta", 0.1))
            next_mult = mult + skill.get("crit_multiplier_bonus", 0.25)
            initial = f"下次选择: 暴击{int(next_crit*100)}% / {next_mult:.1f}x"
        else:
            next_crit = min(skill.get("max_value", 0.6), crit + skill.get("delta", 0.1))
            next_mult = mult + skill.get("crit_multiplier_bonus", 0.25)
            initial = f"下次选择: 暴击{int(next_crit*100)}% / {next_mult:.1f}x"
        current_str = f"暴击 {int(crit*100)}% / {mult:.1f}x"
        return skill["desc"], current_str, initial

    elif key == "regen_kills":
        min_kills = skill.get("min_kills", 5)
        regen_hp = stats.get("regen_hp_amount", 1)
        current_val = stats.get(key, 0)
        if is_first:
            current_str = "未激活"
            initial = f"初始: 每击杀{REGEN_KILLS_INITIAL}只回1血（降至{min_kills}后+0.5血）"
        else:
            if current_val <= min_kills:
                next_hp = regen_hp + skill.get("regen_hp_bonus", 0.5)
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
        if is_first:
            next_val = current * 0.9
            next_reduction = (1 - next_val) * 100
            initial = f"下次选择: 减伤{int(next_reduction)}%（-10%）"
        else:
            next_val = current * 0.9
            next_reduction = (1 - next_val) * 100
            initial = f"下次选择: 减伤{int(next_reduction)}%（-10%）"
        current_str = f"减伤 {int(reduction)}%"
        return skill["desc"], current_str, initial

    elif key == "has_blades":
        base_dmg = skill.get("base_damage", 12)
        base_cd = skill.get("base_cooldown", 3.8)
        base_radius = skill.get("base_radius", 150)
        if is_first:
            initial = f"激活: 范围{base_radius} / 伤{base_dmg} / {base_cd:.1f}s"
        else:
            current_dmg = stats.get("blade_damage", base_dmg)
            current_cd = stats.get("nova_cooldown", base_cd)
            current_radius = stats.get("nova_radius", base_radius)
            next_dmg = current_dmg + skill.get("damage_per_stack", 3)
            next_cd = max(skill.get("min_cooldown", 2.2),
                          current_cd - skill.get("cooldown_reduction", 0.25))
            initial = f"下次: 伤{next_dmg} / {next_cd:.1f}s / 半径{current_radius+skill.get('radius_per_stack', 12)}"
        current_dmg = stats.get("blade_damage", base_dmg)
        current_str = f"范围{stats.get('nova_radius', base_radius)} / 伤{current_dmg}"
        return skill["desc"], current_str, initial

    elif key == "has_lightning":
        base_chains = skill.get("base_chains", 5)
        base_dmg = skill.get("base_damage", 7)
        if is_first:
            initial = f"激活: {base_chains}跳 / 伤{base_dmg}（重复+1跳+1伤）"
        else:
            current_chains = stats.get("lightning_chains", base_chains)
            current_dmg = stats.get("lightning_damage", base_dmg)
            initial = f"下次选择: {current_chains+1}跳 / 伤{current_dmg+skill.get('damage_per_stack', 1)}"
        chains = stats.get("lightning_chains", base_chains)
        dmg = stats.get("lightning_damage", base_dmg)
        current_str = f"{chains}跳 / 伤{dmg}"
        return skill["desc"], current_str, initial

    elif key == "has_traps":
        base_interval = skill.get("base_interval", 2.0)
        base_dmg = skill.get("base_damage", 4)
        base_radius = skill.get("base_radius_mult", 1.0)
        if is_first:
            initial = f"激活: 间隔{base_interval}s / 伤{base_dmg}/s / 范围×{base_radius}"
        else:
            current_interval = stats.get("trap_interval", base_interval)
            current_dmg = stats.get("trap_damage", base_dmg)
            current_radius = stats.get("trap_radius_mult", base_radius)
            next_interval = max(skill.get("min_interval", 1.2),
                                current_interval - skill.get("interval_reduction", 0.1))
            initial = f"下次: 间隔{next_interval:.1f}s / 伤{current_dmg+0.5}/s / 范围×{current_radius+skill.get('radius_per_stack', 0.05):.2f}"
        interval = stats.get("trap_interval", base_interval)
        dmg = stats.get("trap_damage", base_dmg)
        radius = stats.get("trap_radius_mult", base_radius)
        current_str = f"间隔{interval:.1f}s / 伤{dmg}/s / ×{radius:.1f}"
        return skill["desc"], current_str, initial

    return skill["desc"], "", ""


def _skill_available(skill, stats):
    if not stats:
        return True
    key = skill["key"]
    if key == "bullet_speed" and stats.get("bullet_speed", 1.0) >= MAX_BULLET_SPEED_MULT:
        return False
    if key == "fire_interval" and stats.get("fire_interval", FIRE_INTERVAL) <= skill.get("min_value", 0):
        return False
    if key == "crit_chance" and stats.get("crit_chance", 0.0) >= skill.get("max_value", 1.0):
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
        # 首次选择时记录基础值
        if count == 1:
            stats[f"{key}_base"] = stats.get(key, 2)
        base = stats.get(f"{key}_base", 2)
        # 等差数列成长：+1+1+2+2+3+3...（累加）
        # 前n项和：奇数n时为k²，偶数n时为k(k+1)，其中k=(n+1)//2
        k = (count + 1) // 2
        if count % 2 == 1:
            growth = k * k  # 奇数：1², 2², 3²...
        else:
            growth = k * (k + 1)  # 偶数：1×2, 2×3, 3×4...
        stats[key] = base + growth
    # 暗影新星（保留 has_blades 字段以兼容旧调用）
    elif key == "has_blades":
        current = stats.get(key, 0)
        stats[key] = current + 1
        if current == 0:
            stats["blade_count"] = skill.get("base_count", 3)
            stats["blade_damage"] = skill.get("base_damage", 10)
            stats["nova_cooldown"] = skill.get("base_cooldown", 3.8)
            stats["nova_radius"] = skill.get("base_radius", 150)
        else:
            stats["blade_damage"] += skill.get("damage_per_stack", 2)
            stats["nova_cooldown"] = max(
                skill.get("min_cooldown", 2.2),
                stats.get("nova_cooldown", skill.get("base_cooldown", 3.8)) -
                skill.get("cooldown_reduction", 0.25)
            )
            stats["nova_radius"] = stats.get("nova_radius", skill.get("base_radius", 150)) + skill.get("radius_per_stack", 12)
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
            stats["trap_interval"] = max(
                skill.get("min_interval", 1.2),
                stats["trap_interval"] - skill.get("interval_reduction", 0.1)
            )
            stats["trap_damage"] += skill.get("damage_per_stack", 0.5)
            stats["trap_radius_mult"] += skill.get("radius_per_stack", 0.1)
    # 致命节奏 - 暴击率和暴击伤害
    elif key == "crit_chance":
        before = stats[key]
        stats[key] = min(skill.get("max_value", 1.0), stats[key] + skill["delta"])
        if stats[key] > before and "crit_multiplier_bonus" in skill:
            current_crit_mult = stats.get("crit_multiplier", 2.0)
            stats["crit_multiplier"] = current_crit_mult + skill["crit_multiplier_bonus"]
    # 贪婪之魂 - 经验倍率计数
    elif key == "greedy_count":
        stats[key] = stats.get(key, 0) + 1
    # 急速子弹 - 子弹速度倍率
    elif key == "bullet_speed":
        current_speed = stats.get(key, 1.0)
        if current_speed < MAX_BULLET_SPEED_MULT:
            new_mult = current_speed * skill["factor"]
            stats[key] = min(new_mult, MAX_BULLET_SPEED_MULT)
    # 普通delta技能
    elif "delta" in skill:
        if "delta_factor" in skill:
            # 复苏之风特殊处理
            if key == "regen_kills":
                current = stats.get(key, 0)
                min_kills = skill.get("min_kills", 5)
                # 如果未获得（current=0），首次设置为delta值
                if current == 0:
                    stats[key] = skill["delta"]  # 20
                    stats["regen_hp_amount"] = skill.get("regen_hp_initial", 1)
                # 如果已达到最小值，增加回复血量
                elif current <= min_kills:
                    stats["regen_hp_amount"] = stats.get("regen_hp_amount", 1) + skill.get("regen_hp_bonus", 0.5)
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
