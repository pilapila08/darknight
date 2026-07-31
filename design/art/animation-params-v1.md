# 暗夜求生 Darknight — L1 程序动画参数规范 v1（animation-params-v1）

> 文档版本：v1（2026-07-31）
> 作者：art-director（林绘澄）· 美术方向
> 上游依据：`design/art/art-bible-v1.md`（视觉身份唯一权威）+ `settings.py`（尺寸/速度事实）+ `entities/*`（现有帧动画/倾斜实现事实）+ `ui/render_helpers.py`（脚底阴影事实）
> 用途：为工程 L1 程序动画（DN-ENG-L1ANIM-01：正弦 bob + 水平挤压 + 朝向 flip + 脚底阴影联动）提供可执行参数。**只约束渲染表现，不触碰碰撞 rect 与玩法数值。**
> 标注约定：✅ = 基于代码事实 · 🔬 = 需 Playtest 手感验证（给推荐默认值）· ⚠️ = 实现约束/风险
> 基线事实：60 FPS，屏幕 1280×720；现有帧动画 玩家 0.1s/帧、敌人 0.15s/帧（`entities/animation.py`）；玩家已有 `_tilt` 旋转倾斜（`-dx*8.0°`，lerp 12/s）；脚底阴影 `draw_ground_shadow(rect, scale, alpha)` 宽=rect.w×0.9×scale、高=rect.h×0.24×scale。

---

## 0. TL;DR（参数总表）

| 实体 | 渲染尺寸 | 移速(px/s) | **bob 幅度** | **bob 频率** | **squash 系数 s** | **flip** | 相位错开 |
|---|---|---|---|---|---|---|---|
| 玩家 | 32 | 390 | 1.5px | 3.0Hz（静止 0.9Hz） | 0.08 | 按 vx | 单体不适用 |
| 普通敌人 | 28 | 195 | 2.0px | 2.2Hz | 0.10 | 朝玩家 | spawn%9 |
| exploder | 28 | 300 | 2.5px | 2.8Hz | 0.12 | 朝玩家 | spawn%9 |
| charger | 28 | 113 / 冲刺500 | 2.0px / 冲刺1.0px(压低) | 1.8Hz / 冲刺3.3Hz | 0.10 / 冲刺前倾0.06 | 朝玩家(冲刺锁朝向) | spawn%9 |
| ranger | 28 | 128 | 1.5px | 1.6Hz | 0.08 | 朝玩家 | spawn%9 |
| 精英 | 40 | 113 | 2.5px | 1.5Hz | 0.07 | 朝玩家 | spawn%9 |
| Boss 60px (暗影巫师) | 60 | 50 | 3.0px | 1.0Hz | 0.04 | **不 flip**（悬浮） | 固定随机 |
| Boss 80px (尸王) | 80 | 100 | 3.5px | 0.9Hz | 0.04 | 低频可（0.5s 缓动） | 固定随机 |
| Boss 90px (虚空之主) | 90 | 120 | 4.0px | 1.0Hz | 0.03 | **不 flip**（悬浮） | 固定随机 |
| Boss 100px (钢铁巨像) | 100 | 80 | 4.5px | 0.8Hz | 0.03 | 低频可（0.5s 缓动） | 固定随机 |

> ✅ 幅度依据：玩家/小怪 ≈ 渲染高度的 4.7%-8.9%（小实体轻快弹性）；Boss ≈ 4.4%-5%（96px 帧实体按渲染尺寸取 3-4.5px，幅度更大但频率低+squash 小 → 视觉沉重）。频率依据：`freq = 0.8 + min(speed,500)/200` Hz（移动时激活，静止退化 0.9Hz 呼吸），表中按类型微调。

---

## 1. 波形与相位约定（公式，工程直接套用）

- 相位：`phase = t * 2π * freq + phase_offset`
- **bob（y 偏移，负=向上，整数化）**：`dy = -round(amp * (1 - cos(phase)) / 2)`
  - 用 `(1-cos)/2` 半波而非 `sin` 全波：`phase=0` 触地（dy=0，脚贴阴影），`phase=π` 最高点（dy=amp）。实体不会低于地面。
- **squash（与 bob 同相位，触底同步）**：`sx = 1 + s*cos(phase)`，`sy = 1 - s*cos(phase)`
  - `phase=0` 触地 → sx>1 水平拉伸 / sy<1 垂直压缩；`phase=π` 最高点 → sx<1 / sy>1（跳跃拉伸）。
- **渲染顺序**：先 flip → 再 squash（`pygame.transform.scale`，nearest 保像素硬边）→ 最后加 bob 的 y 偏移 blit。
- ⚠️ **只改渲染偏移，不改 `rect`**：bob/squash/flip 全部作用于 draw 时的变换，碰撞与逻辑位置零影响（现有 `_tilt` 已是此模式）。

## 2. squash 细节

- 系数范围：玩家 0.06-0.10、普通敌人 0.08-0.12（软体怪更弹）、精英 0.06-0.09、**Boss 0.03-0.05（质量越大 squash 越小，物理直觉：沉重）**。
- 触底时刻（`phase=0`）水平拉伸、垂直压缩；最高点反向。squash 与 bob 必须同相位、同频率。
- charger 冲刺：bob 幅度压到 1.0px（低身前倾）、squash 降到 0.06（冲刺蓄力收身），冲刺方向锁 flip。🔬
- 🔬 可选扩展（非 L1 必须）：受击/命中瞬间注入一次性 hit-squash 脉冲（sx 1.15 / sy 0.85，0.12s ease-out 回弹），与 `effects/juice.py` 受击闪白叠加。建议纳入后续 juice 层，不阻塞 L1。

## 3. flip 规则

- **朝向判定**：`vx > 5` 朝右，`vx < -5` 朝左，`|vx| ≤ 5` 保持上次朝向（5px/s 防抖，避免静止抖动）。🔬 阈值可调。
- **应用对象**：
  - 玩家：朝移动方向（水平速度分量 vx；纯上下移动时保持上次朝向）。
  - 普通敌人/精英/charger/ranger：**朝玩家**（即朝移动方向 vx——它们始终追玩家，等价于按 vx）。
  - Boss：默认**不 flip**（Shadow Mage / Void Lord 悬浮型严格不翻）；Corpse King / Iron Colossus 有明确正面的低频 flip：vx 反向且持续 ≥0.3s 后，用 0.5s 缓动翻转（不瞬翻，避免大体积跳变）。🔬
- ⚠️ 与玩家 `_tilt` 叠加时：先 rotate 后 flip 会镜像倾斜方向，实现时固定顺序（flip 后 rotate，或 rotate 后 flip 时倾斜角取反）。

## 4. 相位错开（防全屏同步浮动）

- 同类型实体：`phase_offset = (spawn_index % 9) * (2π/9)` —— 最多 1/9 同步。🔬 N=9 可调（8-12）。
- 备选（可脚本）：按世界格 hash `phase_offset = hash((x//64, y//64)) % (2π)`，相邻实体天然错开。
- 精英/Boss 单体：`phase_offset = random.uniform(0, 2π)` 固定于生成时，不每帧重滚。
- 错开只作用于 bob/squash 相位，不影响 flip。

## 5. 动画语言基调（对齐美术圣经"土豆兄弟式"）

- **移动轻快**：玩家/exploder 高频率小幅度 → 急促、灵活；敌人中等 → 软弹；ranger 站桩射击为主 → 低频微浮。
- **Boss 沉重**：低频（0.8-1.0Hz）+ 大 bob 幅度（3-4.5px）+ 极小 squash（0.03-0.04）+ 不/低频 flip → 体积感与压迫感；与玩家轻快形成节奏反差。
- **打击感配合**：受击闪白（0.1s）已有；bob 频率不打断受击反馈（hit-squash 后置）；死亡残影/火光沿用 juice 层，动画层不抢戏。

## 6. 实现约束（供工程对齐）

- ⚠️ 每帧最多 150 敌人 + 4 Boss：squash 每帧 `transform.scale` 150 次可接受（nearest 便宜），但**不要 smoothscale**（贵且破坏像素硬边）。可预烘焙 5 档 sx 缓存或按实体缓存缩放结果。
- ✅ flip 结果可缓存（每实体每朝向一份），bob 偏移整数化（round）避免亚像素抖动。
- ✅ 脚底阴影联动：阴影**保持在地面不动**（不随 bob），阴影宽随 squash 微调 `shadow_scale *= 1 + 0.3*cos(phase)`（触地时略宽）、alpha 在最高点降 10-15%（可选）。玩家现有 shadow `scale=1.2, alpha=115` 保持不变。
- ✅ 新参数建议放 `settings.py` 或独立 `animation_params.py`，与现有 `Animation` 帧动画共存（帧动画管造型摆动，程序动画管位移挤压，互不覆盖）。

## 7. Playtest 验证清单（🔬 全部需手感验证）

| # | 项 | 推荐默认 | 验证问题 |
|---|---|---|---|
| 1 | 玩家 bob 幅度/频率 | 1.5px / 3.0Hz | 是否"太飘/太跳"？静止 0.9Hz 呼吸是否自然 |
| 2 | Boss 沉重感 | 0.8-1.0Hz / 0.03-0.04 | 幅度 3-4.5px 是否够"压场"，频率是否过慢致"卡顿感" |
| 3 | 敌人 squash 0.10-0.12 | 软弹 | 是否过度形变/破描边感 |
| 4 | 相位错开 N=9 | 9 | 满屏 150 敌是否仍有可感知同步 |
| 5 | flip 阈值 5px/s | 5 | 静止是否抖动；Boss 低频 flip 0.5s 缓动是否自然 |
| 6 | hit-squash 脉冲 | 后置 | 是否纳入 L1 或留 juice 层 |
| 7 | 阴影 alpha 联动 | 可选 | 是否值得做（成本 vs 质感） |

---

*文档结束*
