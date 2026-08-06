"""FX 特效贴图加载器（C02：fx-spec-v1.md 接入）。

来源：assets/effects/fx_*.png（从 design/art/ai-samples/fx-*/ 拷贝的定稿主选）。
- 全部 RGBA 单帧贴图，运行时按 radius/角度缩放旋转。
- 缺失时返回 None，各 draw 实现回退到程序化绘制（保证无素材也能运行）。
"""
import os
import sys
import pygame


def _resource_path(relative_path):
    base = getattr(sys, "_MEIPASS", os.path.abspath("."))
    return os.path.join(base, relative_path)


_FX_DIR = _resource_path(os.path.join("assets", "effects"))

# 主选（fx-spec-v1.md ⭐）：
#   fx_explosion_fire_01   爆炸（默认 exploder 死亡爆炸）
#   fx_explosion_purple_01 爆炸（魔法/暗影向）
#   fx_nova_runic_01       暗影新星冲击波
#   fx_lightning_bolt_01   连锁闪电链段（竖直 96×256，运行时旋转）
#   fx_muzzle_star_01      枪口火光
_CACHE = {}


def load_fx(name):
    """加载一张 FX 贴图；失败返回 None（调用方回退程序化绘制）。"""
    surf = _CACHE.get(name)
    if surf is not None:
        return surf
    path = os.path.join(_FX_DIR, name + ".png")
    if os.path.isfile(path):
        try:
            surf = pygame.image.load(path).convert_alpha()
        except Exception:
            surf = None
    else:
        surf = None
    _CACHE[name] = surf
    return surf


# 便捷引用（供各效果模块使用）
def get_explosion_fire():
    return load_fx("fx_explosion_fire_01")


def get_explosion_purple():
    return load_fx("fx_explosion_purple_01")


def get_nova_ring():
    return load_fx("fx_nova_runic_01")


def get_lightning_bolt():
    return load_fx("fx_lightning_bolt_01")


def get_muzzle_flash():
    return load_fx("fx_muzzle_star_01")
