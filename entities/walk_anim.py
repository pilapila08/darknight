"""L1 程序动画：正弦 bob + 水平挤压 + 朝向 flip + 脚底阴影联动。

设计依据：design/art/animation-params-v1.md（美术方向）。
叠加在现有 3 帧帧动画（entities/animation.py）之上，只做绘制期变换，
不改动 rect / 碰撞 / 玩法数值；攻击、受击状态不做特殊处理。

约定：
- bob 用 (1-cos)/2 半波：phase=0 触地（dy=0，脚贴阴影），phase=π 最高点（dy=-amp）。
- bob 返回世界 y 偏移，负 = 向上；屏幕 y 同样向下，draw 时直接 `dy=bob` 即可。
- 渲染顺序：flip → squash（pygame.transform.scale，nearest 保像素硬边）→ bob 偏移。
- 相位错开：同类实体以稳定整数 id 为种子（≈spawn%9 均匀分布，防全屏同步浮动）。
"""
import math

import pygame

from settings import (
    BOB_AMPLITUDE, BOB_FREQ, SQUASH_AMOUNT, BOB_PHASE_STEP, FLIP_DEADZONE,
    WALK_ANIM_PER_TYPE,
)

_TWO_PI = 2.0 * math.pi


class WalkFrame:
    """一次组合动画结果：变换后 surface + 绘制期需要的 bob/阴影信息。"""

    __slots__ = ("surface", "bob", "shadow_scale")

    def __init__(self, surface, bob, shadow_scale):
        self.surface = surface            # 已 flip + squash 的 surface
        self.bob = bob                    # 世界 y 偏移（负 = 向上）
        self.shadow_scale = shadow_scale  # 阴影缩放乘数（触地略大，最高点最小）


def resolve_params(entity_type):
    """按实体类型解析动画参数（fallback 到 settings 默认常量）。"""
    per = WALK_ANIM_PER_TYPE.get(entity_type, {})
    return {
        "amp": per.get("amp", BOB_AMPLITUDE),
        "freq": per.get("freq", BOB_FREQ),
        "squash": per.get("squash", SQUASH_AMOUNT),
        "shadow_fade": per.get("shadow_fade", 0.30),
    }


def bob_phase(entity_id):
    """同类实体相位错开：phase_offset = (id % 9) * BOB_PHASE_STEP。"""
    try:
        seed = int(entity_id)
    except (TypeError, ValueError):
        seed = hash(entity_id) & 0xFFFF
    return (seed % 9) * BOB_PHASE_STEP


def bob_offset(t, phase, amp, freq):
    """正弦垂直位移（世界 y 偏移，负 = 向上）。半波：触地 0 → 最高 -amp。"""
    c = math.cos(_TWO_PI * freq * t + phase)
    return -round(amp * (1.0 - c) / 2.0)


def squash(surface, t, phase, amount, freq=BOB_FREQ):
    """水平/垂直挤压（与 bob 同相位）：触地水平拉伸/垂直压缩，最高点反向。

    底边锚定由调用方保证（绘制一律 midbottom 定位，底部不浮动）；
    pygame.transform.scale 默认 nearest，保像素硬边。
    """
    c = math.cos(_TWO_PI * freq * t + phase)
    w, h = surface.get_size()
    nw = max(1, int(w * (1.0 + amount * c)))
    nh = max(1, int(h * (1.0 - amount * c)))
    if nw == w and nh == h:
        return surface
    return pygame.transform.scale(surface, (nw, nh))


def flip_for_direction(surface, vx):
    """按水平速度方向翻转：vx < -FLIP_DEADZONE 朝左 → 水平镜像；否则原样（零拷贝）。"""
    if vx < -FLIP_DEADZONE:
        return pygame.transform.flip(surface, True, False)
    return surface


def apply_walk_anim(surface, t, entity_id, vx, params):
    """组合入口：flip → squash（与 bob 同相位）。返回变换后 surface。

    bob 位移与阴影缩放请用 compute_walk_frame 一次性获取。
    """
    phase = bob_phase(entity_id)
    img = flip_for_direction(surface, vx)
    return squash(img, t, phase, params["squash"], params["freq"])


def compute_walk_frame(surface, t, entity_id, vx, params):
    """绘制期一次性拿到：变换后 surface + bob 位移 + 阴影缩放乘数。

    每实体每帧只算 1 次 cos：bob / squash / 阴影联动同相位。
    """
    phase = bob_phase(entity_id)
    freq = params["freq"]
    c = math.cos(_TWO_PI * freq * t + phase)
    bob = -round(params["amp"] * (1.0 - c) / 2.0)
    shadow_scale = 1.0 + params.get("shadow_fade", 0.30) * c
    img = flip_for_direction(surface, vx)
    img = squash(img, t, phase, params["squash"], freq)
    return WalkFrame(img, bob, shadow_scale)
