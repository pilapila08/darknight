"""暗夜光照系统：全屏环境暗色 + 动态光源（乘法混合实现）。

原理：维护一张与屏幕等大的 darkness 表面，先填充环境色（偏暗偏冷），
再把径向渐变的光源贴图以加法混合画上去，最后把 darkness 以乘法混合
叠加到画面上——光源处画面保持原亮度，其余区域被压暗降温。

R5/QOL 调亮：提升各图环境光基准值（"暗但不黑"），保留 5 图色调差异；
LIGHT_AMBIENT_BRIGHTNESS 为全局亮度倍率（集中可调，默认 1.0 = 中性）。
"""
import pygame
from settings import SCREEN_WIDTH, SCREEN_HEIGHT

# 各地图的环境光颜色（值越低越暗；分量差异形成色调）。
# QOL 调亮：原 100-128 区间 → 140-180 区间（墓地最亮到虚空最暗的梯度仍保留）。
AMBIENT_BY_MAP = [
    (160, 168, 182),   # 荒芜墓地：冷灰蓝（最亮）
    (152, 172, 150),   # 腐化沼泽：阴绿
    (160, 146, 184),   # 暗影庭院：暗紫
    (176, 162, 148),   # 钢铁废墟：锈棕（最亮暖色）
    (148, 140, 168),   # 虚空裂缝：深紫（最暗，保留虚空压迫感）
]

# 全局环境光亮度倍率：>1 整体调亮，<1 整体调暗（集中可调，默认中性）
LIGHT_AMBIENT_BRIGHTNESS = 1.0

# 玩家光源基础半径（正常模式 _submit_lights 引用，便于集中调参）
PLAYER_LIGHT_RADIUS = 400
PLAYER_LIGHT_COLOR = (255, 238, 198)

_GRADIENT_SIZE = 256


def _build_gradient():
    """构建一张白色径向渐变贴图（中心亮，边缘透明衰减）。"""
    surf = pygame.Surface((_GRADIENT_SIZE, _GRADIENT_SIZE))
    center = _GRADIENT_SIZE // 2
    for r in range(center, 0, -2):
        t = r / center            # 1 -> 0
        value = int(255 * (1 - t) ** 2)
        pygame.draw.circle(surf, (value, value, value), (center, center), r)
    return surf


class LightingSystem:
    def __init__(self):
        self.darkness = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        self.ambient = AMBIENT_BY_MAP[0]
        self._gradient = _build_gradient()
        self._cache = {}      # (size_step, color) -> tinted scaled gradient
        self._lights = []
        self.enabled = True

    def set_map(self, map_index):
        self.ambient = AMBIENT_BY_MAP[map_index % len(AMBIENT_BY_MAP)]

    def add_light(self, world_x, world_y, radius, color=(255, 255, 255), intensity=1.0):
        """登记一个光源（世界坐标）。intensity 0~1 控制亮度。"""
        if len(self._lights) < 96:
            self._lights.append((world_x, world_y, radius, color, intensity))

    def _get_light_surf(self, radius, color):
        # 半径按 12px 分档，避免缓存爆炸
        step = max(24, int(radius / 12) * 12)
        key = (step, color)
        surf = self._cache.get(key)
        if surf is None:
            size = step * 2
            surf = pygame.transform.smoothscale(self._gradient, (size, size))
            if color != (255, 255, 255):
                tint = pygame.Surface((size, size))
                tint.fill(color)
                surf.blit(tint, (0, 0), special_flags=pygame.BLEND_RGB_MULT)
            if len(self._cache) > 64:
                self._cache.clear()
            self._cache[key] = surf
        return surf

    def render(self, screen, camera):
        """把光照结果叠加到画面上，并清空本帧光源列表。"""
        if not self.enabled:
            self._lights.clear()
            return
        ambient = self.ambient
        if LIGHT_AMBIENT_BRIGHTNESS != 1.0:
            ambient = tuple(
                max(0, min(255, int(c * LIGHT_AMBIENT_BRIGHTNESS))) for c in ambient)
        self.darkness.fill(ambient)
        for wx, wy, radius, color, intensity in self._lights:
            sx = wx - camera.offset.x
            sy = wy - camera.offset.y
            if not (-radius <= sx <= SCREEN_WIDTH + radius and
                    -radius <= sy <= SCREEN_HEIGHT + radius):
                continue
            surf = self._get_light_surf(radius, color)
            if intensity < 1.0:
                surf = surf.copy()
                fade = pygame.Surface(surf.get_size())
                v = int(255 * max(0.0, intensity))
                fade.fill((v, v, v))
                surf.blit(fade, (0, 0), special_flags=pygame.BLEND_RGB_MULT)
            half = surf.get_width() // 2
            self.darkness.blit(surf, (sx - half, sy - half),
                               special_flags=pygame.BLEND_RGB_ADD)
        self._lights.clear()
        screen.blit(self.darkness, (0, 0), special_flags=pygame.BLEND_RGB_MULT)
