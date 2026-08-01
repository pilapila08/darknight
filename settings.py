# Display
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
FPS = 60

# Game (Victory condition)
GAME_DURATION_SECONDS = 600  # 存活满 10 分钟即为胜利（README 承诺）

# Debug
ENABLE_TEST_MODE = True  # 测试模式开关，True=开启，False=关闭

# World (larger than screen for camera scrolling)
MAP_WIDTH = 3000
MAP_HEIGHT = 2250
GRID_SIZE = 64

# Player
PLAYER_SIZE = 32
PLAYER_SPEED = 390  # pixels per second (was 260)
PLAYER_MAX_HP = 20  # 初始血量上限
PLAYER_INVINCIBLE_TIME = 0.4  # seconds after taking damage

# Enemy
ENEMY_SIZE = 28
ENEMY_SPEED = 195  # pixels per second (was 130)
ENEMY_HP = 1
SPAWN_INTERVAL = 0.80  # seconds (放缓初始刷怪间隔)
MAX_ENEMIES = 150  # 最多敌人数量（性能优化）

# Elite Enemy
ELITE_SIZE = 40
ELITE_SPEED = 113  # was 75
ELITE_HP = 4
ELITE_CHANCE = 0.22
ELITE_CHANCE_RAMP_PER_BOSS = 0.05  # R4: 精英概率斜坡 +0.05/击杀
ELITE_CHANCE_RAMP_PER_MIN = 0.01   # R4: 精英概率斜坡 +0.01/分钟
ELITE_CHANCE_MAX = 0.45            # R4: 精英概率封顶
ELITE_ACTIVATION = 90    # seconds until elites appear (was 120)

# Charger
CHARGER_SPEED = 113  # was 75
CHARGER_HP = 3
CHARGER_DASH_SPEED = 500
CHARGER_DASH_DURATION = 0.35
CHARGER_DASH_COOLDOWN = 2.5
CHARGER_COLOR = (255, 140, 0)

# Ranger
RANGER_SPEED = 128  # was 85
RANGER_HP = 2
RANGER_RANGE = 320  # was 200, 1.6x scale
RANGER_FIRE_INTERVAL = 1.6
RANGER_COLOR = (0, 200, 100)

# Exploder
EXPLODER_SPEED = 300  # was 200
EXPLODER_HP = 1
EXPLODER_RADIUS = 80   # 缩小自爆范围（原144过大）
EXPLODER_DAMAGE = 2
EXPLODER_COLOR = (200, 50, 200)

# Enemy Bullet
ENEMY_BULLET_RADIUS = 4
ENEMY_BULLET_SPEED = 180

# Difficulty Scaling (R4 方案A：线性档位 + 伤害封顶，无冻结段)
DIFFICULTY_INTERVAL = 34  # seconds per tier (45*0.75, 节奏加快25%)
DIFFICULTY_MAX_TIER = 17  # R4: 34×17=578s，接近终局仍缓涨（原4→136s冻结，已修复）
HP_BONUS_PER_TIER = 1     # 每档+1HP，持续线性涨至 17
DAMAGE_BONUS_PER_TIER = 1 # 每档+1伤害，由 DAMAGE_BONUS_MAX 封顶
DAMAGE_BONUS_MAX = 8      # R4: 普通怪接触伤上限 1+8=9（防终局一击死螺旋）
SPAWN_RATE_FACTOR = 0.90

# 刷怪密度（R4：tf_cap 随 Boss 击杀递增，修复 150s 刷怪封顶平台期）
SPAWN_RATE_CAP_BASE = 5      # tf 基础上限（原 SPAWN_RATE_CAP=5，已重命名）
SPAWN_CAP_PER_BOSS = 1.5     # 每击杀一个 Boss，tf_cap +1.5（终局 5+1.5×4=11 → 8.78 只/s）
# Boss 战节奏（R4 §2.4）
BOSS_FIGHT_SPAWN_SLOWDOWN = 1.5   # Boss 战期间普通刷怪间隔 ×1.5（速率 ×0.67）
BOSS_REINFORCE_DELAY = 45.0       # Boss 战超过 45s 后开始出增援波
BOSS_REINFORCE_INTERVAL = 15.0    # 增援波间隔
BOSS_REINFORCE_BASIC_COUNT = 4    # 增援波基础怪数量
BOSS_REINFORCE_CHARGER_COUNT = 1  # 增援波冲锋怪数量
# 终局冲锋（R4 §2.5：最后 60s）
FINAL_SURGE_INTERVAL_MULT = 0.8   # 刷怪间隔 ×0.8（速率 ×1.25）
FINAL_SURGE_ELITE_BONUS = 0.10    # 精英概率 +0.10
FINAL_SURGE_WAVE_INTERVAL = 20.0  # 包围波间隔
FINAL_SURGE_WAVE_COUNT = 8        # 包围波数量（环形入场）

# Time-based Growth
GROWTH_INTERVAL = 34     # 怪物成长时间间隔（与DIFFICULTY_INTERVAL一致）

# Elite Modifiers
ELITE_HP_MULT = 2.0       # 精英怪血量倍率
ELITE_DAMAGE_MULT = 2.0  # 精英怪伤害倍率

# Weapon
FIRE_INTERVAL = 0.6  # seconds (was 0.8)
BULLET_RADIUS = 5
BULLET_SPEED = 450  # pixels per second (was 400)
BULLET_BASE_DAMAGE = 2    # R3: 基础子弹伤害（替换 state.py 硬编码，C7）
BULLET_COUNT_BASE = 1     # R3: 基础弹量（替换 state.py 硬编码）
MAX_BULLET_SPEED_MULT = 10.0  # 子弹速度倍率上限
# 技能平衡（R3 §4.2 / §4.3）
BULLET_PENALTY_THRESHOLD = 3  # 第 4 发起（含）进入边际惩罚（0 基索引 ≥3）
BULLET_PENALTY_MULT = 0.55    # 第 4 发起每发伤害 ×0.55
BULLET_PIERCE_MAX = 3         # 穿透弹最多 3 层（达上限移出池）
BULLET_PIERCE_DAMAGE_MULT = 0.85  # 穿透弹伤害 ×0.85/发（首次选取，重复不再衰减）
# 联动技能（R3 §4.4）
STATIC_OVERLOAD_CD_REDUCTION = 0.15  # 静电过载：闪电每次命中使新星当前 CD -0.15s
DEATH_ECHO_RADIUS = 200              # 死亡回响：爆炸范围
DEATH_ECHO_DAMAGE = 12               # 死亡回响：伤害

# XP / Level
XP_BASE = 14          # 1→2级所需经验（放缓前期升级节奏）
XP_GROWTH = 1.15      # 每级经验×1.15 (几何增长，抬高中后期需求)

# Orbital Blades (deprecated block removed: BLADE_DAMAGE / BLADE_ORBIT_* 死常量已删，
# 暗影新星权威值见下方 SKILL_DEFS["nova"])

# Chain Lightning（伤害/跳数权威值见 SKILL_DEFS["lightning"]；此处保留冷却/范围/衰减）
LIGHTNING_COOLDOWN = 2.0
LIGHTNING_CHAIN_RANGE = 240  # was 150, 1.6x scale
LIGHTNING_DECAY = 0.7     # damage multiplier per bounce
LIGHTNING_COLOR = (100, 200, 255)

# Acid Trap（伤害权威值见 SKILL_DEFS["trap"]；TRAP_INTERVAL 已删，interval 唯一源=skills）
TRAP_DAMAGE_BASE = 4      # R3: 剧毒地雷伤害唯一源（每 tick，tick=1.0s）
TRAP_DURATION = 12.0       # 陷阱持续时间
TRAP_RADIUS = 45          # was 28, 1.6x scale
TRAP_DOT_DURATION = 3.0  # total DoT time on enemy
TRAP_DOT_TICK = 1.0      # seconds between ticks
TRAP_COLOR = (100, 220, 80)

# New Skill Effects
CRIT_MULTIPLIER = 2.0
REGEN_KILLS_INITIAL = 20  # 复苏之风初始需要击杀数
REGEN_KILLS_MIN = 5       # 复苏之风最小击杀数

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GRAY = (40, 40, 40)
DARK_GRAY = (60, 60, 60)
RED = (255, 50, 50)
BLUE = (50, 150, 255)
YELLOW = (255, 220, 50)
GOLD = (255, 200, 0)
GREEN = (0, 200, 100)
ORANGE = (255, 140, 0)
PURPLE = (200, 50, 200)
CYAN = (100, 200, 255)

# ---- Boss System ----
BOSS_WARNING_DURATION = 3.0
BOSS_CLEAR_DELAY = 1.5

# Boss 1: Corpse King (尸王)
BOSS_1_TIME = 120
CORPSE_KING_HP = 120
CORPSE_KING_DAMAGE = 5
CORPSE_KING_SIZE = 80
CORPSE_KING_COLOR = (40, 80, 20)
CORPSE_KING_SPEED = 100
CORPSE_KING_ATTACK_INTERVAL = 2.5
CORPSE_KING_POISON_DURATION = 5.0
CORPSE_KING_POISON_DAMAGE = 2
CORPSE_KING_MINION_COUNT = 3

# Boss 2: Shadow Mage (暗影巫师)
BOSS_2_TIME = 240
SHADOW_MAGE_HP = 600
SHADOW_MAGE_DAMAGE = 9
SHADOW_MAGE_SIZE = 60
SHADOW_MAGE_COLOR = (100, 0, 150)
SHADOW_MAGE_SPEED = 50
SHADOW_MAGE_ATTACK_INTERVAL = 2.5
SHADOW_MAGE_BOLT_COUNT = 5
SHADOW_MAGE_BOLT_DAMAGE = 6
SHADOW_MAGE_TELEPORT_INTERVAL = 4.0
SHADOW_MAGE_SHADOW_HP = 30
SHADOW_MAGE_SHADOW_DAMAGE = 6

# Boss 3: Iron Colossus (钢铁巨像)
BOSS_3_TIME = 360
IRON_COLOSSUS_HP = 2400
IRON_COLOSSUS_DAMAGE = 30
IRON_COLOSSUS_SIZE = 100
IRON_COLOSSUS_COLOR = (150, 150, 170)
IRON_COLOSSUS_SPEED = 80
IRON_COLOSSUS_ATTACK_INTERVAL = 3.5
IRON_COLOSSUS_POUND_DAMAGE = 48
IRON_COLOSSUS_ARMOR_REDUCTION = 0.5
IRON_COLOSSUS_ARMOR_DURATION = 4.0
IRON_COLOSSUS_FIST_SPEED = 250
IRON_COLOSSUS_FIST_DAMAGE = 24
IRON_COLOSSUS_FIST_RADIUS = 12

# Boss 4: Void Lord (虚空之主)
BOSS_4_TIME = 480
VOID_LORD_HP = 5500   # R4: 8000→5500（击杀窗口校准 20-30s，原推导 53-80s 过肉）
VOID_LORD_DAMAGE = 70
VOID_LORD_SIZE = 90
VOID_LORD_COLOR = (180, 0, 200)
VOID_LORD_SPEED = 120
VOID_LORD_ATTACK_INTERVAL = 2.0
VOID_LORD_VOID_RIFT_DAMAGE = 20
VOID_LORD_VOID_RIFT_RADIUS = 50
VOID_LORD_VOID_RIFT_DURATION = 8.0
VOID_LORD_GRAVITY_STRENGTH = 100  # 引力牵引速度（px/s，越靠近裂隙中心越强，最大=此值）
VOID_LORD_GRAVITY_RADIUS = 300    # 引力场牵引半径（px，裂隙核心伤害半径见 VOID_LORD_VOID_RIFT_RADIUS）
VOID_LORD_BARRAGE_COUNT = 12
VOID_LORD_BARRAGE_DAMAGE = 30
VOID_LORD_ENRAGE_THRESHOLD = 0.3
VOID_LORD_VOIDLING_HP = 150
VOID_LORD_VOIDLING_DAMAGE = 20

# ---- Map System ----
MAP_TRANSITION_DURATION = 2.0

# ---- 敌人可见性增强（DN-ENG-VIS-01）----
ENEMY_GLOW_COLOR = (255, 200, 80)   # 敌人轮廓光暖色
ENEMY_GLOW_WIDTH = 2                 # 轮廓光 mask 膨胀宽度（px）
ENEMY_GLOW_ALPHA = 70                # 轮廓光 alpha（建议 60-90）
ENEMY_RING_COLOR = (255, 80, 60)     # 脚底危险光圈红橙
ENEMY_RING_ALPHA = 55                # 脚底光圈 alpha（建议 40-70）
BOSS_RING_SCALE = 1.6                # Boss 光圈半径放大系数（更大更亮）
EXPLODER_RING_COLOR = (255, 60, 60)  # 自爆怪爆炸范围光圈（红）
EXPLODER_RING_ALPHA = 85             # 自爆怪光圈基础 alpha（脉冲增强）

# ---- L1 程序动画（正弦 bob + 水平挤压 + 朝向 flip + 脚底阴影联动）----
# 依据 design/art/animation-params-v1.md（美术方向）；bob 半波 (1-cos)/2：
# phase=0 触地（dy=0，脚贴阴影），phase=π 最高点（dy=-amp，负=向上）。
BOB_AMPLITUDE = 2.0   # 默认 bob 幅度（px，负=向上）
BOB_FREQ = 2.2        # 默认 bob 频率（Hz）
SQUASH_AMOUNT = 0.10  # 默认挤压系数（±10% 形变）
BOB_PHASE_STEP = 0.7  # 同类实体相位错开步长（rad，≈2π/9 均匀分布）
FLIP_DEADZONE = 5.0   # |vx| ≤ 5 px/s 视为静止，不翻转（防抖动）
# 按实体类型差异：玩家轻快小振幅 / 敌人中等软弹 / Boss 低频大振幅（沉重感）
WALK_ANIM_PER_TYPE = {
    # amp: bob 幅度(px) · freq: bob 频率(Hz) · squash: 挤压系数 · shadow_fade: 阴影联动乘数
    "player":   {"amp": 1.5, "freq": 3.0, "squash": 0.08, "shadow_fade": 0.30},
    "enemy":    {"amp": 2.0, "freq": 2.2, "squash": 0.10, "shadow_fade": 0.30},
    "exploder": {"amp": 2.5, "freq": 2.8, "squash": 0.12, "shadow_fade": 0.30},
    "charger":  {"amp": 2.0, "freq": 1.8, "squash": 0.10, "shadow_fade": 0.30},
    "ranger":   {"amp": 1.5, "freq": 1.6, "squash": 0.08, "shadow_fade": 0.30},
    "elite":    {"amp": 2.5, "freq": 1.5, "squash": 0.07, "shadow_fade": 0.30},
    "boss":     {"amp": 4.0, "freq": 0.9, "squash": 0.04, "shadow_fade": 0.30},
}

# ---- R3 权威技能定义块（settings.py 为唯一源，skills.py 等只引用）----
# 依据：design/gdd/playability-pack-v1.md §1.2。运行时真值为准。
SKILL_DEFS = {
    # 暗影新星（C3/C4 真值：12/+3/3.8s/150）
    "nova": {
        "base_count": 1,
        "base_damage": 12,
        "damage_per_stack": 3,
        "base_cooldown": 3.8,
        "cooldown_reduction": 0.25,
        "min_cooldown": 2.2,
        "base_radius": 150,
        "radius_per_stack": 12,
    },
    # 连锁闪电（C1 真值：5跳/7伤，+1跳+1伤/层）
    "lightning": {
        "base_chains": 5,
        "base_damage": 7,
        "chains_per_stack": 1,
        "damage_per_stack": 1,
    },
    # 剧毒地雷（C5/C6 真值：interval 唯一源 + 伤害 4/tick）
    "trap": {
        "base_interval": 2.0,
        "interval_reduction": 0.1,
        "min_interval": 1.2,
        "base_damage": 4,
        "damage_per_stack": 0.5,
        "base_radius_mult": 1.0,
        "radius_per_stack": 0.05,
    },
    # 穿透弹（R3 §4.3 B1：弹速×1.5 保留 + 穿透+1/层 + 伤害×0.85，3层封顶）
    "pierce": {
        "factor": 1.5,
        "damage_mult": 0.85,
        "max_pierce": 3,
    },
}
