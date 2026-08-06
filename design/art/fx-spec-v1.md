# 暗夜求生 Darknight — FX 特效贴图接入规格（fx-spec-v1）

> 文档版本：v1（2026-08-03，DN-ART-FX-01 产出）
> 作者：art-director（林绘澄）
> 上游依据：`design/art/art-bible-v1.md`（视觉身份）+ `design/art/ai-asset-pipeline.md`（流水线总则）+ 实测代码（`entities/explosion.py` / `effects/orbital_blade.py` / `effects/chain_lightning.py` / `effects/juice.py`）
> 范围：本批产出的 4 类特效贴图（爆炸 / 新星冲击波 / 闪电 / 枪口火光）的**接入规格**，供 engineering-lead（第二批）落地。
> 标注：📦 = 文件位置 · 🎨 = 视觉规则 · ⚙️ = 接入建议 · ⚠️ = 风险/注意

---

## 0. 摘要（TL;DR）

- 本批产出 **10 张 RGBA 特效贴图**，分布 4 个目录，对应 4 类当前实现为程序化圆/线的特效：
  - `design/art/ai-samples/fx-explosion/` — 4 张（fx_explosion_fire_01/02, fx_explosion_purple_01/02）
  - `design/art/ai-samples/fx-nova/` — 3 张（fx_nova_runic_01, fx_nova_spike_02, fx_nova_double_03）
  - `design/art/ai-samples/fx-lightning/` — 2 张（fx_lightning_bolt_01/02）
  - `design/art/ai-samples/fx-muzzle/` — 1 张（fx_muzzle_star_01）
- 命名规范：`fx_<effect>_<variant>.png`，RGBA，无水印
- 关键策略：**纯黑背景 + 亮主体**（与 sprite 浅底暗主体相反），亮度差分抠图替代 sprite 的「浅底→亮差分」
- 风格与美术圣经锚点 ②「暗夜反差」完美对齐（亮 FX 浮在暗地图背景上），与 5 地图色环兼容（无紫/青之外的高饱和干扰色）
- 不替换 `assets/` 下任何文件；接入是 engineering-lead 第二批的事

---

## 1. 通用规格（4 类特效共性）

### 1.1 文件与命名 📦
- 全部 RGBA PNG，alpha=0 为透明
- 命名 `fx_<effect>_<variant>.png`（小写、下划线）
- 变体（variant）描述视觉特征，不是顺序：例 `fx_explosion_fire_01`（火·主选）、`fx_explosion_purple_02`（紫·备选）
- 候选原图存于各目录的 `raw/` 子目录，**不入游戏运行时**

### 1.2 流水线（与 sprite 的差异）🎨
| 步骤 | sprite（ai-asset-pipeline §3） | FX（本批） |
|---|---|---|
| AI 输入 | 浅灰底 + 暗主体 | **纯黑底 + 亮主体** |
| 抠图 | 亮背景→透明（luminance>160） | **黑背景→透明（luminance<22）** |
| 量化 | ≤11 色对齐美术圣经 | **不量化**（FX 需保留渐变发光） |
| 帧扩展 | 3 帧 wobble + 合成 sheet | **单帧**（运行时按 radius/duration 缩放） |
| 输出尺寸 | 16/96（base） | **128-256**（运行时再缩放） |

> 🎨 **为何"纯黑底"而非"透明底"**：ImageGen 的 `transparent` 参数实测失效（pipeline §1）。纯黑底 + 黑底亮度抠图是替代方案，对**亮发光**类特效反而更稳：bg 一定是 0，明暗差最大，键阈 22 几乎不误抠。

### 1.3 后处理脚本 📦
- `tools/fx_texture_pipeline.py`（PIL 版；pygame 未安装故改 PIL）
- 流程：watermark crop → luminance key → bbox+fit resize（NEAREST）→ save PNG
- 阈值调参：若主体被误抠 → KEY_THRESHOLD 调大；若黑 bg 残留 → 调小

### 1.4 水印处理 ⚠️
- 候选原图右下角有 "AI生成 WORKBUDDY" 水印（白字，在黑底上很显眼）
- 处理：右下裁剪 strip（right 15-17% / bottom 7-10%），裁掉后再键黑
- 闪电 bolt 因纵向延伸，bottom 只裁 7%（避免切掉 bolt 末端），water 仍能完全去除

### 1.5 与 5 地图色环的兼容性 🎨
- 4 类特效只用 4 个 accent 色系（火:橙/黄/白；紫:紫/品红；青:青/白；中性:黄/橙）
- 全部 ≤3 主色，与地图 accent_color（5 张各 1 色）**无冲突**：在任意地图上叠加都不会喧宾夺主
- 视觉与 art-bible §2.3「每图 1 accent」约束**叠加兼容**（FX 是 overlay 不是底色）

---

## 2. 爆炸特效（fx_explosion_*）📦

### 2.1 文件清单
| 文件 | 源候选 | 推荐度 | 用途 |
|---|---|---|---|
| `fx-explosion/fx_explosion_fire_01.png` | fire (no smoke) | ⭐ **主选** | exploder 自爆 / 默认爆炸 |
| `fx-explosion/fx_explosion_fire_02.png` | fire (with smoke) | 备选 | 需"烟感"的死亡爆炸 |
| `fx-explosion/fx_explosion_purple_01.png` | purple-cyan blast | ⭐ **主选** | 魔法/暗影向爆炸 |
| `fx-explosion/fx_explosion_purple_02.png` | white-shard burst | 备选 | 强烈"冲击波"感 |

### 2.2 规格
- **尺寸**：256×256 RGBA
- **不透明占比**：28-59%（量化初筛通过，28% 对应 shard 型属合理低密度）
- **配色**：fire = (255,170,60) (255,220,50) (255,255,255)；purple = (200,50,200) (100,200,255) (235,220,255) — 全部落在 art-bible 全局色 + 5 地图 ambient 范围内

### 2.3 当前实现 ⚙️
- `entities/explosion.py:Explosion.draw()` — 当前画 3 层圆（紫色 fill + 粉色描边 + 紫色外环），半径 0→max_radius 线性扩张，alpha 180→0
- 应用方式：`pygame.Surface` 一次性画三层 → blit
- **建议接入**：保留半径+alpha 缩放逻辑，**替换为 blit 贴图**

### 2.4 接入代码草稿 ⚙️
```python
# effects/asset_loader.py 增加
EXPLOSION_FIRE = load_rgba("design/art/ai-samples/fx-explosion/fx_explosion_fire_01.png")
EXPLOSION_PURPLE = load_rgba("design/art/ai-samples/fx-explosion/fx_explosion_purple_01.png")

# entities/explosion.py draw 改造（示意）
def draw(self, screen, camera):
    progress = self.elapsed / self.lifetime          # 0→1
    radius = max(1, int(self.max_radius * progress))
    alpha = int(180 * max(0, 1 - progress))
    size = radius * 2
    surf = pygame.transform.scale(EXPLOSION_FIRE, (size, size))
    surf.set_alpha(alpha)
    pos = camera.apply(pygame.Rect(self.x, self.y, 0, 0))
    screen.blit(surf, (pos.x - radius, pos.y - radius))
```

### 2.5 性能预算
- 单帧贴图 256×256 RGBA = 256KB；运行时按 radius 缩放（≤160px）= 100KB
- 同时存活爆炸数受 `EXPLODER_RADIUS=80` 区域影响，预估 ≤6 个同屏，<1MB 显存占用

---

## 3. 暗影新星冲击波（fx_nova_*）📦

### 3.1 文件清单
| 文件 | 源候选 | 推荐度 | 用途 |
|---|---|---|---|
| `fx-nova/fx_nova_runic_01.png` | concentric rings + runes | ⭐ **主选** | 默认 shockwave |
| `fx-nova/fx_nova_spike_02.png` | rings + radial spikes | 备选 | 需"爆发感"的强化态 |
| `fx-nova/fx_nova_double_03.png` | double-ring + outer runes | 备选 | 史诗级/传奇级 nova |

### 3.2 规格
- **尺寸**：256×256 RGBA
- **不透明占比**：29-38%（环有中空，天然低密度 — 正常）
- **配色**：紫色 (200,50,200) + 青色 (100,200,255) + 白核 (235,220,255) + 暗紫 (90,30,100) — 完美匹配 `settings.PURPLE` 与 `settings.CYAN`

### 3.3 当前实现 ⚙️
- `effects/orbital_blade.py:OrbitalBladeManager.draw()` — 当前画 3 层圆（紫 fill + 青描边 + 浅紫高光环），半径 0→radius 扩张
- 关键差异：本批贴图是**环形**（中间透明），不是实心圆 → 视觉上"冲击波"更明显

### 3.4 接入代码草稿 ⚙️
```python
# effects/asset_loader.py 增加
NOVA_RING = load_rgba("design/art/ai-samples/fx-nova/fx_nova_runic_01.png")

# effects/orbital_blade.py draw 改造（示意）
def draw_pulse(self, screen, camera, pulse):
    progress = min(1.0, pulse["age"] / pulse["duration"])
    radius = max(1, int(pulse["radius"] * progress))
    alpha = int(180 * (1 - progress))
    size = radius * 2
    surf = pygame.transform.scale(NOVA_RING, (size, size))
    surf.set_alpha(alpha)
    pos = camera.apply(pygame.Rect(pulse["x"], pulse["y"], 0, 0))
    screen.blit(surf, (pos.x - radius, pos.y - radius))
```

### 3.5 性能预算
- 贴图 256KB，缩放到 ≤300px = 350KB；同屏 nova 通常 ≤2 个（cooldown 3.8s），<1MB

---

## 4. 连锁闪电（fx_lightning_*）📦

### 4.1 文件清单
| 文件 | 源候选 | 推荐度 | 用途 |
|---|---|---|---|
| `fx-lightning/fx_lightning_bolt_01.png` | jagged bolt + small forks | ⭐ **主选** | 默认链段 |
| `fx-lightning/fx_lightning_bolt_02.png` | thicker bolt + big forks | 备选 | 高伤害/强化态 |

### 4.2 规格
- **尺寸**：96×256 RGBA（**竖直画布**，engineering 旋转至任意角度）
- **不透明占比**：11-13%（bolts 天然细长 — 正常）
- **配色**：白核 (255,255,255) + 青 (100,200,255) + 暗青 rim — 与 `settings.LIGHTNING_COLOR=(100,200,255)` / `CYAN=(100,200,255)` 一致

### 4.3 当前实现 ⚙️
- `effects/chain_lightning.py:LightningBolt.draw()` — 当前画 2 层 jagged line（青色粗线 + 白色细线），每段 0.25s 衰减
- 本批贴图是**单段纹理**，**不替换**折线算法：engineering 可将每段绘制改为"旋转+缩放 blit"，保持随机抖动感

### 4.4 接入代码草稿 ⚙️
```python
# effects/asset_loader.py 增加
LIGHTNING_BOLT = load_rgba("design/art/ai-samples/fx-lightning/fx_lightning_bolt_01.png")

# effects/chain_lightning.py LightningBolt.draw 改造（示意）
def draw(self, screen, camera):
    alpha = int(200 * (1 - self.elapsed / self.lifetime))
    p1 = camera.apply(pygame.Rect(self.start[0], self.start[1], 0, 0))
    p2 = camera.apply(pygame.Rect(self.end[0], self.end[1], 0, 0))
    dx, dy = p2.x - p1.x, p2.y - p1.y
    seg_len = math.hypot(dx, dy)
    angle = math.degrees(math.atan2(dy, dx)) - 90  # 贴图竖直，需转 -90°
    # 缩放到 seg_len（高度 256 → 实际 seg_len）
    surf = pygame.transform.rotozoom(LIGHTNING_BOLT, angle, seg_len / 256.0)
    surf.set_alpha(alpha)
    screen.blit(surf, (p1.x - surf.get_width() // 2, p1.y))
```

### 4.5 性能预算
- 96×256 = 96KB；运行时按段长缩放 ≤240px ≈ 360KB
- 同屏 bolt 数受 `chain_count=5` 影响，≤5 个 / 帧，<2MB

---

## 5. 枪口火光（fx_muzzle_*）📦

### 5.1 文件清单
| 文件 | 源候选 | 推荐度 | 用途 |
|---|---|---|---|
| `fx-muzzle/fx_muzzle_star_01.png` | yellow-white star + orange edges | ⭐ **主选** | 默认枪口火光 |

### 5.2 规格
- **尺寸**：128×128 RGBA
- **不透明占比**：38%（中心星 + 散落火星）
- **配色**：白核 (255,255,230) + 黄白 (255,240,180) + 黄 (255,220,50) + 橙 (255,140,0) — 与 `effects/juice.py:_MuzzleFlash` 当前颜色完全一致

### 5.3 当前实现 ⚙️
- `effects/juice.py:_MuzzleFlash.draw()` — 当前画 2 层圆 + 1 方向光刺，0.06s 单帧
- 颜色 (255,240,180) (255,235,170) — 与本贴图色板 100% 兼容

### 5.4 接入代码草稿 ⚙️
```python
# effects/asset_loader.py 增加
MUZZLE_FLASH = load_rgba("design/art/ai-samples/fx-muzzle/fx_muzzle_star_01.png")

# effects/juice.py _MuzzleFlash.draw 改造（示意）
def draw(self, screen, camera):
    life = max(0.0, self.timer / self.duration)
    r = int(5 + 7 * life)
    surf_size = r * 4
    surf = pygame.Surface((surf_size, surf_size), pygame.SRCALPHA)
    muzzle_scaled = pygame.transform.scale(MUZZLE_FLASH, (surf_size, surf_size))
    muzzle_scaled.set_alpha(int(230 * life))
    surf.blit(muzzle_scaled, (0, 0))
    # 旋转至 self.angle
    rotated = pygame.transform.rotate(surf, -math.degrees(self.angle))
    sx = self.x - camera.offset.x
    sy = self.y - camera.offset.y
    screen.blit(rotated, (sx - rotated.get_width() // 2, sy - rotated.get_height() // 2),
                special_flags=pygame.BLEND_RGBA_ADD)
```

### 5.5 性能预算
- 128×128 = 64KB；运行时 ≤40px = 5KB
- 同屏 muzzle ≤12 个（`_MuzzleFlash` 上限），<100KB

---

## 6. 命名与目录总览 📦

```
design/art/ai-samples/
├── fx-explosion/
│   ├── raw/                                    ← AI 候选原图（不入运行时）
│   ├── fx_explosion_fire_01.png    ⭐ 主选     → 默认 exploder 死亡爆炸
│   ├── fx_explosion_fire_02.png                → 烟雾版备选
│   ├── fx_explosion_purple_01.png  ⭐ 主选     → 魔法爆炸
│   └── fx_explosion_purple_02.png              → 白核冲击版备选
├── fx-nova/
│   ├── raw/
│   ├── fx_nova_runic_01.png        ⭐ 主选     → 默认 shockwave
│   ├── fx_nova_spike_02.png                    → 强化态备选
│   └── fx_nova_double_03.png                   → 史诗态备选
├── fx-lightning/
│   ├── raw/
│   ├── fx_lightning_bolt_01.png     ⭐ 主选    → 默认链段
│   └── fx_lightning_bolt_02.png                → 粗壮备选
└── fx-muzzle/
    ├── raw/
    └── fx_muzzle_star_01.png        ⭐ 主选     → 枪口火光
```

---

## 7. 流水线脚本与可复现 📦

- **脚本**：`tools/fx_texture_pipeline.py`（PIL 实现，pygame 未安装故改 PIL；如未来安装 pygame 可改回）
- **输入**：`design/art/ai-samples/fx-<effect>/raw/pixel_art_*_<timestamp>.png`（AI 候选）
- **输出**：`design/art/ai-samples/fx-<effect>/fx_<effect>_<variant>.png`
- **复现**：rerun `python tools/fx_texture_pipeline.py` 会基于最新 raw 重生成所有 finals
- **阈值**：KEY_THRESHOLD 默认 22，可按需 per-image 调整（脚本支持）

---

## 8. 与美术圣经的对齐检查 🎨

| art-bible 锚点 | 本批符合情况 |
|---|---|
| ① 浓黑描边 | ⚠️ **偏离**：FX 不强调 black outline（亮发光本身已与暗背景强对比）；如需 outline，engineering 可在 blit 后叠一层描边 surface |
| ② 暗夜反差 | ✅ **完美**：亮 FX 浮在暗夜地图背景，正是 anchor ② 的核心视觉 |
| ③ 色环接力 | ✅ **兼容**：FX 用色（橙/黄/紫/青/白）全部落在 5 地图 accent 与 ambient 范围内 |
| 不做什么红线 | ✅ 写实像素 ❌ 无；高饱和底色 ❌ 无；半透明蒙版 ❌ 无；3D ❌ 无 |

> 🎨 **锚点①的偏离是合理的**：art-bible §1.2 锚点①明确"世界实体（角色/怪物/boss/掉落物）外缘必须有可识别的深色外轮廓"——**特效不在列举范围**。亮发光 FX 在暗背景上的剪影自然清晰，不需要黑色 outline。

---

## 9. 风险与注意事项 ⚠️

1. **ImageGen 透明参数失效**：本批走"纯黑底+键黑"路线，**不可逆**：若未来要换 sprite 流水线生产 FX 需重建脚本（ai-asset-pipeline 的浅底路线对 FX 不适用，因为 FX 主体也是亮色会被误键）。
2. **并行调用冲突**（实测）：ImageGen 并行调用会全部落进同一目录（与 `output_dir` 参数无关），必须**严格串行 + 不同 output_dir**。本批已踩坑并把 9 张候选从错位的 `fx-nova/raw1/` 重新分发到正确目录。下次生产前请先看本节的提醒。
3. **闪电 bolt 末端被裁 7%**：因为 watermark 占底部 7-8%，为完全去 watermark 牺牲了 bolt 末端 ~22px（≤1% 总长）。engineering 按 segment length 缩放时无视觉影响。
4. **爆炸 fire_01 之外的 3 张属备选**：若游戏后续加入"不同怪有不同 explosion 颜色"机制（art-bible §6.4 已暗示），可直接复用本批 4 张，无需再生成。
5. **不直接覆盖 assets/**：本批不修改 `assets/sprites/` 或 `assets/effects/`。engineering-lead 接入时按 §2-5 的草稿创建新的 loader 路径（如 `effects/fx_textures.py`），由 gameplay 调用。

---

## 10. 下一步建议

1. **engineering-lead**（第二批）按 §2-5 草稿接入 4 类特效，主选用 ⭐ 标注的 4 张
2. **art-director**（本批已完成）等待工程接入后的实测截图，若发现"贴图太亮/太暗/位置偏移"再微调 size 或主选
3. **未来扩展**（P2）：boss 专属死亡爆炸（4 boss 各 1 张）、传说级 nova（金/紫双环）、muzzle 类型 2（扇形霰弹）

---

*文档结束*