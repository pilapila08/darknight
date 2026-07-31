"""游戏实体模块"""
from .player import Player
from .enemy import Enemy
from .enemy_types import Charger, Ranger, Exploder
from .bullet import Bullet
from .enemy_bullet import EnemyBullet
# XpOrb 已废弃：经验改为击杀直给（见 entities/xp_orb.py，保留文件待 ORB_* 常量清理后删除）
from .particle import Particle
from .damage_number import DamageNumber
from .explosion import Explosion
from .animation import Animation
from .acid_trap import TrapManager
from .drop_item import HealthPack, ShieldPickup, DropItem
from .boss import Boss, BossProjectile, AreaEffect, BOSS_CONFIGS, BoomerangFist
