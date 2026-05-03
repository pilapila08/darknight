# Display
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
FPS = 60

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
SPAWN_INTERVAL = 0.65  # seconds (放缓初始刷怪间隔)
MAX_ENEMIES = 150  # 最多敌人数量（性能优化）

# Elite Enemy
ELITE_SIZE = 40
ELITE_SPEED = 113  # was 75
ELITE_HP = 4
ELITE_CHANCE = 0.22
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
EXPLODER_RADIUS = 144  # was 90, 1.6x scale
EXPLODER_DAMAGE = 2
EXPLODER_COLOR = (200, 50, 200)

# Enemy Bullet
ENEMY_BULLET_RADIUS = 4
ENEMY_BULLET_SPEED = 180

# Difficulty Scaling
DIFFICULTY_INTERVAL = 40  # seconds per tier (放缓难度提升)
SPAWN_RATE_FACTOR = 0.90  # spawn interval multiplier per tier (放缓刷新加速)
HP_BONUS_PER_TIER = 1
DAMAGE_BONUS_PER_TIER = 1  # 等差数列增长，每40秒触发：+1, +2, +3... (累计: 0, 1, 3, 6, 10...)

# Time-based Growth
GROWTH_INTERVAL = 40     # 怪物成长时间间隔（秒，拉长节奏）
XP_GROWTH_INTERVAL = 80   # 经验成长时间间隔（秒，拉长节奏）
XP_BONUS_PER_GROWTH = 0.3  # 每次经验成长+0.3 (降低)

# Game Duration
GAME_DURATION = 600  # 10分钟游戏时长上限（秒）

# Elite Modifiers
ELITE_HP_MULT = 2.0       # 精英怪血量倍率
ELITE_DAMAGE_MULT = 2.0  # 精英怪伤害倍率

# Weapon
FIRE_INTERVAL = 0.6  # seconds (was 0.8)
BULLET_RADIUS = 5
BULLET_SPEED = 450  # pixels per second (was 400)

# XP / Level
ORB_RADIUS = 5
ORB_SPEED = 640       # magnetized flight speed (was 320, 2x)
PICKUP_RANGE = 144    # was 90, 1.6x scale
XP_PER_ORB = 1
XP_BASE = 6           # 初始升级经验 (1→2级需要6)
XP_DIFF_INCREMENT = 4  # 经验增量等差数列的差值 (1→10级增量1, 11→20级增量5, 21→30级增量9...)

# Orbital Blades
BLADE_DAMAGE = 8        # DPS per blade
BLADE_ORBIT_RADIUS = 88  # was 55, 1.6x scale
BLADE_ORBIT_SPEED = 3.0  # rad/s
BLADE_SIZE = 14
BLADE_COLOR = (180, 220, 255)

# Chain Lightning
LIGHTNING_COOLDOWN = 2.0
LIGHTNING_DAMAGE = 8
LIGHTNING_CHAINS = 3
LIGHTNING_CHAIN_RANGE = 240  # was 150, 1.6x scale
LIGHTNING_DECAY = 0.7     # damage multiplier per bounce
LIGHTNING_COLOR = (100, 200, 255)

# Acid Trap
TRAP_INTERVAL = 2.0      # seconds between drops while moving
TRAP_DURATION = 12.0       # 陷阱持续时间
TRAP_RADIUS = 45          # was 28, 1.6x scale
TRAP_DOT_DURATION = 3.0  # total DoT time on enemy
TRAP_DOT_DAMAGE = 4      # damage per tick
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
