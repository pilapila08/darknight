# Display
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
FPS = 60

# World (larger than screen for camera scrolling)
MAP_WIDTH = 3000
MAP_HEIGHT = 2250
GRID_SIZE = 64

# Player
PLAYER_SIZE = 32
PLAYER_SPEED = 260  # pixels per second (was 200)
PLAYER_MAX_HP = 10
PLAYER_INVINCIBLE_TIME = 0.4  # seconds after taking damage

# Enemy
ENEMY_SIZE = 28
ENEMY_SPEED = 130  # pixels per second (was 100)
ENEMY_HP = 1
SPAWN_INTERVAL = 0.7  # seconds (was 1.0)

# Elite Enemy
ELITE_SIZE = 40
ELITE_SPEED = 75
ELITE_HP = 4
ELITE_CHANCE = 0.22
ELITE_ACTIVATION = 90    # seconds until elites appear (was 120)

# Charger
CHARGER_SPEED = 75
CHARGER_HP = 3
CHARGER_DASH_SPEED = 500
CHARGER_DASH_DURATION = 0.35
CHARGER_DASH_COOLDOWN = 2.5
CHARGER_COLOR = (255, 140, 0)

# Ranger
RANGER_SPEED = 85
RANGER_HP = 2
RANGER_RANGE = 200
RANGER_FIRE_INTERVAL = 1.6
RANGER_COLOR = (0, 200, 100)

# Exploder
EXPLODER_SPEED = 200
EXPLODER_HP = 1
EXPLODER_RADIUS = 90
EXPLODER_DAMAGE = 2
EXPLODER_COLOR = (200, 50, 200)

# Enemy Bullet
ENEMY_BULLET_RADIUS = 4
ENEMY_BULLET_SPEED = 180

# Difficulty Scaling
DIFFICULTY_INTERVAL = 25  # seconds per tier (was 30)
SPAWN_RATE_FACTOR = 0.83  # spawn interval multiplier per tier (was 0.85)
HP_BONUS_PER_TIER = 1

# Weapon
FIRE_INTERVAL = 0.6  # seconds (was 0.8)
BULLET_RADIUS = 5
BULLET_SPEED = 450  # pixels per second (was 400)

# XP / Level
ORB_RADIUS = 5
ORB_SPEED = 320       # magnetized flight speed (was 250)
PICKUP_RANGE = 90     # auto-attract radius (was 80)
XP_PER_ORB = 1
XP_PER_LEVEL = 6      # xp needed = level * 6 (was 8, -25%)

# Orbital Blades
BLADE_DAMAGE = 8        # DPS per blade
BLADE_ORBIT_RADIUS = 55
BLADE_ORBIT_SPEED = 3.0  # rad/s
BLADE_SIZE = 14
BLADE_COLOR = (180, 220, 255)

# Chain Lightning
LIGHTNING_COOLDOWN = 2.0
LIGHTNING_DAMAGE = 8
LIGHTNING_CHAINS = 3
LIGHTNING_CHAIN_RANGE = 150
LIGHTNING_DECAY = 0.7     # damage multiplier per bounce
LIGHTNING_COLOR = (100, 200, 255)

# Acid Trap
TRAP_INTERVAL = 2.0      # seconds between drops while moving
TRAP_DURATION = 8.0
TRAP_RADIUS = 28
TRAP_DOT_DURATION = 3.0  # total DoT time on enemy
TRAP_DOT_DAMAGE = 3      # damage per tick
TRAP_DOT_TICK = 1.0      # seconds between ticks
TRAP_COLOR = (100, 220, 80)

# New Skill Effects
CRIT_MULTIPLIER = 2.0
REGEN_KILLS = 50
FROSTBITE_SLOW = 0.8

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
