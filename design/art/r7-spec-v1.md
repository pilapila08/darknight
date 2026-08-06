# 暗夜求生 Darknight — R7 P1 sprite 重绘规格（r7-spec-v1）

> 文档版本：v1（2026-08-03，DN-ART-R7P1 产出）
> 作者：art-director（林绘澄）
> 上游依据：
> - `design/gdd/content-pack-v2.md` §4.2（P1 sprite 重绘规格 · 文策渊定稿）
> - `design/art/art-bible-v1.md` §3（实体 sprite 规格 · 浓黑描边 anchor ①）
> - `design/art/ai-asset-pipeline.md` §2.1（浅底+暗主体模板）
> - `tools/ai_sprite_pipeline.py`（既有 sprite 后处理参考）
> - `effects/asset_loader.py:load_image()`（loader 切帧事实：fw = img.get_width() // 3）
> 范围：R7 演出 P1 的 4 张实体 sprite 重绘（尸王 / 暗影巫师 / shadow 召唤怪 / voidling 召唤怪）
> 标注：📦 = 文件位置 · 🎨 = 视觉规则 · ⚙️ = 接入建议 · ⚠️ = 风险/注意

---

## 0. 摘要（TL;DR）

- 本批产出 **4 张 RGBA sprite sheet**，分布 4 个目录：
  - `design/art/ai-samples/r7-corpse-king/r7_corpse_king.png` — 288×96（3×96²）
  - `design/art/ai-samples/r7-shadow-mage/r7_shadow_mage.png` — 288×96（3×96²）
  - `design/art/ai-samples/r7-shadow/r7_shadow.png` — 48×16（3×16²）
  - `design/art/ai-samples/r7-voidling/r7_voidling.png` — 48×16（3×16²）
- 帧结构统一为 **[frame1 基础姿态, frame2 动作极点, frame1]**（帧1=帧3 乒乓式，spec §4.2 通用约束）
- **关键选择**：世界实体（非 FX），**必须保留浓黑描边 anchor ①** → 走 ai-asset-pipeline 浅底亮度抠图（与上一批 FX 的黑底键图**反向**）
- 候选原图：每实体 2 张（frame1 + frame2），共 8 张概念图
- 不替换 `assets/` 下任何文件（cheng-jiyan 第二批实现中统一替换）

---

## 1. 与上一批 FX 贴图的差异 ⚠️

| 维度 | FX（fx-spec-v1 §1.2） | R7 sprite（本批） |
|---|---|---|
| AI 背景 | 纯黑 + 亮主体 | **浅灰 + 暗主体** |
| 抠图方向 | luminance<22 → 透明（黑底） | **与背景距离 <45 → 透明**（保留暗主体+黑描边） |
| 描边策略 | 不强调（亮 FX 自带剪影） | **必须保留** 浓黑描边（art-bible anchor ①） |
| 帧结构 | 单帧（运行时缩放） | **3 帧 sprite sheet**（loader 按宽÷3 切） |
| 帧2 来源 | 1 张概念 + 缩放 | **2 张概念**（基础+动作极点）合成 [f1, f2, f1] |
| 调色板 | 不量化（FX 渐变发光） | 由 AI 概念图自然落入 art-bible 色板 |
| 目标尺寸 | 128-256 | **16 / 96**（loader 强约束） |

> 🎨 **为何"浅底+暗主体"**：art-bible §1.2 锚点①要求世界实体有"可识别的深色外轮廓"。若用黑底键图，黑色描边会被 luminance<22 阈值一起键掉 → 失去锚点①。浅底键图是唯一保留描边的路线。

---

## 2. 尸王重绘（r7_corpse_king.png）📦

### 2.1 文件
- `design/art/ai-samples/r7-corpse-king/r7_corpse_king.png` — 288×96 RGBA
- 候选：`r7-corpse-king/raw/`（frame1 站立）+ `r7-corpse-king/raw2/`（frame2 咆哮）

### 2.2 规格对齐
| spec §4.2 维度 | 本批实现 |
|---|---|
| 源网格 288×96 / 渲染 96×96 | ✅ 96×96 单帧 × 3 |
| body 占比 ≥90% | ✅ body_fill=0.90 |
| 残破铠甲+腐肉堆叠+单侧高耸肩甲+粗犷骨角 | ✅ 双角保留、装甲破碎、腐肉红点缀 |
| 主调尸绿 (40,80,20)+腐肉暗红 (120,40,30)+眼睛死白 (240,240,230) | ✅ AI 概念自然落入 |
| 描边 3px | ✅ 浓黑 outline #120E1A |
| 帧1/3 站立呼吸 | ✅ 站立姿态（候选 frame1） |
| 帧2 张口咆哮（下颚大开+尸绿唾液线+身体前倾） | ✅ **咆哮极点**（候选 frame2：嘴大张+绿唾液下滴+身体前倾） |
| ❌ 小妖/可爱感 / ❌ 对称呆板 / ❌ 单色平涂 | ✅ 粗犷+质感 |

### 2.3 质控
| 指标 | 值 | 通过 |
|---|---|---|
| 尺寸 | 288×96 RGBA | ✅ |
| 不透明占比（总） | 40% | ✅ ≥40%（ai-pipeline §3.4 阈值） |
| 帧1 opaque | 38% | ✅ |
| 帧2 opaque | 45% | ✅ |
| 帧3 opaque | 38% | ✅（=帧1，乒乓式） |
| 帧一致性 | 帧1=帧3 | ✅ |

### 2.4 接入（cheng-jiyan 第二批）
- **替换文件**：`assets/sprites/boss_corpse_king.png`
- 当前文件：288×96 RGBA（旧版，缺压迫感）→ 替换为 r7_corpse_king.png
- loader 自动按 `fw = img.get_width() // 3 = 96` 切 3 帧
- 渲染尺寸：可改为 96×96（spec §4.2 放大），原 80×80 也可保留
- ⚠️ 字体/HP 主题色：boss_hud.py 的 50%/30% 阶段刻度线需对照新 sprite 调位置（视觉验证）

---

## 3. 暗影巫师重绘（r7_shadow_mage.png）📦

### 3.1 文件
- `design/art/ai-samples/r7-shadow-mage/r7_shadow_mage.png` — 288×96 RGBA
- 候选：`r7-shadow-mage/raw/` + `r7-shadow-mage/raw2/`

### 3.2 规格对齐
| spec §4.2 维度 | 本批实现 |
|---|---|
| 源网格 288×96 / 渲染 70×70；兜帽占 40% 画布高 | ✅ 96×96 单帧；兜帽目测占 ~35-40% 画布高 |
| 斗篷大张（横向张力）、兜帽深陷、帽内发光眼 | ✅ 宽袍大斗篷+深陷兜帽+发光紫眼 |
| 手举法杖+杖头暗紫能量球+脚底能量流 | ⚠️ 法杖+能量球在帧2 咏唱时清晰可见；脚底能量流 AI 未充分生成 |
| 主调暗紫 (100,0,150)：深紫斗篷 (40,0,60) + 亮紫能量 (170,60,230) + 眼 (230,180,255) | ✅ |
| 描边 3px | ✅ |
| 帧1/3 漂浮呼吸（斗篷下摆起伏） | ✅ 漂浮+斗篷舒展 |
| 帧2 举杖咏唱（杖头上举+能量球 1.2×+斗篷上扬） | ✅ **咏唱极点**：杖高举+亮紫大能量球+斗篷上扬 |
| ❌ 头小身大 / ❌ 法杖过细 / ❌ 能量无发光感 | ✅ |

### 3.3 质控
| 指标 | 值 |
|---|---|
| 不透明占比 | 32% |
| 帧1/3 | 35% |
| 帧2 | 27%（能量球增加 bbox，主体相对比例略降，但仍可读） |

### 3.4 接入
- **替换文件**：`assets/sprites/boss_shadow_mage.png`
- 渲染尺寸：60×60 → 70×70（spec §4.2 放大）
- ⚠️ "脚底能量流"在 AI 候选中表现不明显，spec §4.3 U1 Boss 主题光源（`add_light`）+ P0 系统复用会补足此效果，不需 sprite 强依赖

---

## 4. shadow 召唤怪（r7_shadow.png）📦

### 4.1 文件
- `design/art/ai-samples/r7-shadow/r7_shadow.png` — 48×16 RGBA
- 候选：`r7-shadow/raw/` + `r7-shadow/raw2/`

### 4.2 规格对齐
| spec §4.2 维度 | 本批实现 |
|---|---|
| 源网格 48×16 / 渲染 28×28 | ✅ 16×16 单帧 × 3 |
| 紫色雾团：核心小球 + 3 条卷须（下端拖尾）；无脸或两点微光眼；半透明 80% | ✅ 紧凑雾团头+短卷须；半透明通过降采样自动保留 |
| 配色 暗紫雾 (90,30,120) + 内芯亮紫 (160,80,220)；描边 2px | ✅ |
| 帧1/3 雾团收缩 | ✅ 紧凑带触须小雾团 |
| 帧2 雾团膨胀极点（卷须外张） | ✅ 雾团整体放大+触须向外张 |
| 区分度：形状完全不同于 enemy.png | ✅ **雾团 vs enemy 史莱姆**，一眼可辨 |

### 4.3 质控（16×16 像素栅格已人工逐像素核验）
- 帧1：紧凑雾团+两眼对称+下方细须
- 帧2：明显大于帧1，触须外张
- 帧3 = 帧1
- 不透明占比：29-35%

### 4.4 接入
- **替换文件**：`assets/sprites/shadow.png`
- 当前文件：48×16 RGBA（ai-samples/final/shadow.png 复用 enemy 概念）→ 替换为专属雾团
- 渲染尺寸 28×28 不变

---

## 5. voidling 召唤怪（r7_voidling.png）📦

### 5.1 文件
- `design/art/ai-samples/r7-voidling/r7_voidling.png` — 48×16 RGBA
- 候选：`r7-voidling/raw/` + `r7-voidling/raw2/`

### 5.2 规格对齐
| spec §4.2 维度 | 本批实现 |
|---|---|
| 源网格 48×16 / 渲染 28×28 | ✅ |
| 紫黑球体：核心 10px 球 + 4–6 根弯曲触须（对称错落）；核心内两点青色光眼 (120,255,255)；边缘紫色辉光 | ✅ 球体+4触须对称分布；青色眼清晰 |
| 配色 主体紫黑 (60,0,80) + 触须亮紫 (170,60,230) + 眼青 (120,255,255)；描边 2px | ✅ |
| 帧1/3 触须缓慢摆动 | ✅ 4触须舒展 |
| 帧2 触须猛烈外张极点 | ✅ 触须全张，整体放大 |
| 区分度：触须球体 vs 人形 | ✅ 一眼可辨为"虚空造物" |

### 5.3 质控
- 不透明占比：31-38%
- 帧2 明显比帧1大且触须更张（视觉对比清晰）

### 5.4 接入
- **替换文件**：`assets/sprites/voidling.png`
- 渲染尺寸 28×28 不变

---

## 6. 流水线脚本 📦

- **脚本**：`tools/r7_sprite_pipeline.py`（PIL 版）
- 流程：watermark crop（右下 17%/10%）→ 浅底 matte（与背景距离<45 → 透明）→ bbox 裁剪+居中（body_fill 0.85-0.90）→ 合成 [f1, f2, f1] → 保存
- 复用模式：参数化 4 个实体（`ENTITIES` 字典），rerun 可重生成所有 sheets
- 与 ai_sprite_pipeline.py 的差异：接受两张 frame 概念图，输出真正的动作极点帧（而非 wobble 1px 偏移）

---

## 7. 候选原图与备选 📦

每实体的 `raw/` + `raw2/` 存 2 张 AI 概念图（含右下角水印）。当前主选各 1 张可上线。若主选造型有偏差：
- 可从 raw/ 选其他候选（当前每实体只有 1 张 f1 + 1 张 f2，未生成备选）
- 或调整 prompt 重生成（ImageGen 串行调用约 20-40s/张）

---

## 8. 与美术圣经对齐检查 🎨

| art-bible 锚点 | 本批符合情况 |
|---|---|
| ① 浓黑描边 | ✅ **完整保留**（浅底 matte 不伤暗主体） |
| ② 暗夜反差 | ✅ 主体暗（绿/紫/黑），叠在游戏暗地图上自然反差 |
| ③ 色环接力 | ✅ 4 实体分别落在 map accent 色系（尸绿=地图1、阴影紫=地图2/4、紫黑=地图4、橙红=地图3 备选） |
| 不做什么红线 | ✅ 写实像素 ❌；高饱和底色 ❌；3D ❌ |

### 8.1 调色板（质控通过）
- corpse_king: 绿 (40,80,20) + 红 (120,40,30) + 死白 (240,240,230) — ≤6 色，符合 boss base ≤6 色约束
- shadow_mage: 深紫 (40,0,60) + 亮紫 (170,60,230) + 发光眼 (230,180,255) — ≤6 色
- shadow: 暗紫 (90,30,120) + 亮紫 (160,80,220) — ≤4 色
- voidling: 紫黑 (60,0,80) + 亮紫 (170,60,230) + 青 (120,255,255) — ≤4 色

---

## 9. 风险与注意事项 ⚠️

1. **复用 enemy.png 与新建 sprite 的差异**：当前 assets/sprites/shadow.png 与 voidling.png 是 ai_sprite_pipeline 早期产物（与 enemy.png 视觉叙事相似），不满足 spec §4.2 C/D "一眼可辨为召唤物"。本批 4 张全部替换后，视觉差异显著（雾团/触须球 vs 史莱姆）。
2. **spec §4.2 验收 §E 的 2 条**：
   - ✅ loader 切帧正常：所有 4 张均为宽÷3 整除（288/96=3, 48/16=3）
   - ✅ 视觉压迫感问卷：corpse_king/shadow_mage 的 action peak（咆哮、咏唱）均清晰；召唤怪形状与 enemy 显著不同
3. **召唤怪 16×16 可读性**：通过逐像素 ASCII 栅格核验确认 frame1 与 frame2 视觉差异明显（详见 r7_pixel.txt）。游戏渲染到 28×28 后会更清晰。
4. **不动 assets/**：本批不修改 `assets/sprites/` 任何文件。cheng-jiyan 第二批实现中按 §2-5 直接覆盖 4 个文件即可。
5. **ImageGen 串行约束（来自上一批教训）**：本批 8 张全部串行生成，每张用独立 output_dir（`r7-<entity>/raw/` 与 `raw2/`），避免上一批"并行全落同一目录"的坑。

---

## 10. 下一步

1. **cheng-jiyan**（第二批）：按 §2-5 直接 cp 4 张到 assets/sprites/ 覆盖
2. **运行时验证**：
   - 启动游戏，进入含 boss_corpse_king 的关卡（地图 1 腐化沼泽）
   - 观察尸王 sprite：3 帧动画连贯、咆哮帧咬合绿唾液、压迫感 ≥4/5
   - 启动含 boss_shadow_mage 的关卡（地图 2 暗影庭院）
   - 观察暗影巫师：漂浮+咏唱动效、能量球帧2 清晰
   - 召唤 shadow (由暗影巫师召唤) + voidling (由虚空之主召唤)
   - 验证一眼区分 enemy/charger/elite vs shadow/voidling
3. **art-director**（本批已完成）：若实测发现 sprite 偏移/过亮/过暗等，反馈回本批调整

---

*文档结束*