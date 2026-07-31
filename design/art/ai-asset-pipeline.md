# 暗夜求生 Darknight — AI 辅助美术生产流水线（ai-asset-pipeline）

> 文档版本：v1.1（2026-07-31，含 P0 实测反馈修订）
> 作者：art-director（林绘澄）· 美术方向
> 上游依据：`design/art/art-bible-v1.md`（视觉规范唯一权威）+ `effects/asset_loader.py`（资产生成/加载事实）+ `assets/sprites/` 实测尺寸 + ImageGen 实测样例 + P0 候选量化分析（`design/art/candidate-analysis-p0.txt`）
> 用途：把 AI 生图纳入可复现、可质控的美术生产流程，产出可直接喂给后续"人工微调 + 入库"的资产。
> 标注约定：🤖 = 可自动化（主理人可跑 ImageGen / 脚本）· 👁 = 必须人工判定 · ⚠️ = 风险/必须注意
>
> **v1.1 修订要点**：① 实测确认 ImageGen `transparent background` 参数**不生效**（6/6 候选全为 1024×1024 不透明、背景复杂渐变、色键不可行）；② 抠图策略从"bbox 透明裁剪"改为**亮度差分抠图**（利用"浅底深主体"事实，5/6 候选可直接用）；③ 新增 P0 候选量化初筛表与重生成准则。

---

## 0. 摘要（TL;DR）

- **AI 定位**：AI 只做"上游概念与参考"，**永远不直接产出最终游戏 sprite sheet**。
- **关键纪律**：最终入库 sprite 必须是 48×16（3 帧 × 16px）/ 288×96（boss 3 帧 × 96px）/ 24×24（pickup），RGBA，经"降采样 → 调色板对齐 → 切帧 → 人工质控"后由脚本合成为 sheet。
- **本轮 P0-D**：`elite.png`（空 8%）、`charger.png`（错图 23%）用 AI 概念 + 流水线重绘；`ranger`、两个 boss、shadow/voidling 召唤怪按 P1 排入。
- **⚠️ 已知限制（实测）**：ImageGen 的 `transparent background` 参数不生效，输出全为不透明 1024×1024、背景复杂渐变（962-1886 色）。因此**入库前必须抠图**，方案 = "生成时要求浅色/纯色背景 + 深色主体" → 亮度差分生成 alpha（见 §3.2）。
- **水印纪律**：所有商业化出口（商店 Key Art / 封面）必须无水印；sprite 概念图经"浅底亮度抠图 + 裁剪"后水印大部分落在背景区被抠掉，但入库前仍要目检（§5）。
- **产出目录**：AI 候选放 `design/art/ai-candidates/`（不入游戏运行时），终稿才写入 `assets/sprites/`。

---

## 1. 总则：AI 能做什么 / 不能做什么（边界，实测确认）

| 能力 | 结论 | 说明 |
|---|---|---|
| 概念参考图（角色/怪物/Boss 造型） | ✅ AI 胜任 | 产出"造型方向"供选型，再走降采样流水线 |
| 商店 Key Art / 封面 / Library Hero | ✅ AI 胜任 | 构图氛围强；但文字/Logo 必须后期合成，AI 出字不可靠 |
| UI 图标（透明底、线性/扁平） | ✅ AI 胜任（需抠图） | 适合单色 + 高光 + 描边的图标；复杂渐变图标降级为参考。**透明参数不生效，需浅底亮度抠图** |
| 背景氛围图（5 地图主题） | ✅ AI 胜任 | 每张给 accent 色 + 关键词即可；作商店底图不要求透明 |
| **透明背景（transparent background 参数）** | ❌ **AI 做不了（实测）** | 6/6 候选输出 1024×1024 不透明、背景复杂渐变（962-1886 色、非纯色），无法色键直抠 → 必须"浅底亮度差分抠图"（§3.2） |
| **精确像素 sprite sheet（48×16 三帧对齐）** | ❌ **AI 做不了** | 帧间一致性、16px 内可读性、网格对齐都不可靠。必须走"概念 → 降采样 → 切帧 → 人工"流水线 |
| 中文文字 / Logo 字型 | ❌ AI 做不了 | 一律后期合成（见 §2.3） |
| 16px 小尺寸下的"形状可读性" | ❌ AI 做不了 | AI 放大看很美，缩到 16px 会糊成一团；可读性靠人工终审 |

> ⚠️ **核心原则：AI 产"大"，人工收"小"。** AI 出 1024 级概念，流水线负责收成 16/96px，人工负责"小尺寸还认不认得出来"这一关。
> ⚠️ **透明不可用的应对**：所有 sprite/图标 prompt 改为"**浅灰/纯白背景 + 深色主体 + 高对比**"，让亮度差分抠图可用（实测 5/6 候选背景亮度 ≥ 主体亮度，可直接差分；1 张深灰底候选建议重生成）。

---

## 2. Prompt 规范（模板库）

### 2.0 通用风格锚点段落（所有 prompt 必带）

把这段作为每个 prompt 的**前缀或后缀**，确保风格与美术圣经锚点 ①②③ 对齐：

```
dark fantasy pixel art, thick black outline (Brotato style), flat cartoon pixel, dark moody subject,
high saturation accent highlights, single centered subject, plain light gray background, high contrast,
16x16 low-res pixel sprite aesthetic, no text, no watermark, no border, bottom right empty margin
```

中文对照（ImageGen 支持中文 prompt，可任选一种语言，推荐英文为主）：
```
暗黑幻想像素艺术，浓黑粗描边（土豆兄弟风格），扁平卡通像素，暗色主体，高饱和强调色高光，
单一居中主体，纯浅灰背景，高对比，16x16 低分辨率像素精灵质感，无文字，无水印，无边框，右下角留空
```

**关键元素**：
- `plain light gray background` + `high contrast`（**替代已失效的 transparent**——浅底深主体 → 亮度差分抠图可用，见 §3.2）
- `bottom right empty margin`（水印规避，见 §5）
- `no text`（商店素材除外）
- ⚠️ **不要再用 `transparent background`**（实测无效）；若某个候选背景过深（亮度接近主体），判定为"不可差分"，弃用或重生成。

---

### 2.1 像素 sprite 概念参考（角色/怪物/Boss）

> 目标：拿到 1 个"造型对、描边对、配色对"的角色概念图，不是 sprite sheet。
> 每个候选出 1 张单帧概念 → 后处理时由脚本/人工扩展为 3 帧（见 §3.3）。

**模板 A（通用小怪 / 精英）**

```
pixel art monster concept, {描述}, dark fantasy pixel art, thick black outline (Brotato style),
flat cartoon pixel, single centered subject, plain light gray background, high contrast,
16x16 sprite aesthetic, palette: dark base (#0F1217), accent {ACCENT_HEX}, glow highlight {GLOW_HEX}, outline #120E1A,
no text, no watermark, bottom right empty margin
```

中文：
```
像素怪概念图，{描述}，暗黑幻想像素艺术，浓黑粗描边（土豆兄弟风格），扁平卡通像素，
单个居中主体，纯浅灰背景，高对比，16x16 精灵质感，配色：暗底 #0F1217，强调色 {ACCENT_HEX}，高光 {GLOW_HEX}，描边 #120E1A，
无文字，无水印，右下角留空
```

**模板 B（Boss，要求压迫感）**

```
pixel art boss monster concept, imposing menacing {描述}, massive silhouette, glowing eyes,
dark fantasy pixel art, thick black outline (Brotato style), flat cartoon pixel, single centered subject,
plain light gray background, high contrast, 96x96 sprite aesthetic, palette: dark base #0F1217, accent {ACCENT_HEX},
glow highlight {GLOW_HEX}, outline #120E1A, no text, no watermark, bottom right empty margin
```

**按资产填的描述与配色**（直接抄用）：

| 资产 | 描述（中文 / English） | ACCENT_HEX | GLOW_HEX | 参考基线 |
|---|---|---|---|---|
| elite（P0） | 精英冠军怪：大身躯、金色边饰、大角、发光眼 / elite champion monster, bulky body, gold trim, big horns, glowing eyes | #FFC800（金） | #FFE066 | art-bible §6.4 elite 升级路径 |
| charger（P0） | 冲锋角兽：低身前倾、大角、速度感 / charging ram beast, lowered head, big horns, forward momentum | #6E695F（锈棕） | #FF9A3C | art-bible §6.4 charger 建议 |
| ranger（P1） | 持弓/弩的人形怪、兜帽 / hooded archer monster with bow | #5F3782（暗紫） | #7AE0FF | art-bible §6.4 ranger 建议 |
| shadow 召唤怪（P1） | 暗影幽灵：半透明斗篷、飘忽 / shadow wraith, tattered cloak, floating | #640096 | #B44CFF | 色 = 暗影巫师 (100,0,150) |
| voidling 召唤怪（P1） | 虚空幼体：裂隙浮体、紫色虚空 / void spawn, cracked floating orb, void tendrils | #B400C8 | #FF5CF0 | 色 = 虚空 (180,0,200) |
| boss_corpse_king（P1） | 尸王：骨刺、腐肉、王冠、压迫感 / corpse king, bone spikes, rotten flesh, crown, imposing | #3C822D（阴绿） | #7AE07A | art-bible §6.4 |
| boss_shadow_mage（P1） | 暗影巫师：飘动斗篷、大头、魔法光 / shadow mage, flowing cloak, big hooded head, arcane glow | #5F3782（暗紫） | #B44CFF | art-bible §6.4 |

> 👁 **选型判断标准**（每个资产从 N 张候选里挑 1 张主选 + 1 张备选）：
> ① 描边是否"浓黑清晰"（缩到 16px 后仍是完整剪影）；
> ② 造型叙事是否对（elite 要"精英"，charger 要"冲锋"，不是小山/弯曲生物）；
> ③ 配色是否贴 ACCENT_HEX（偏离即降级）；
> ④ 主体是否居中、有无大块透明边距（便于 bbox 裁剪）。

---

### 2.2 商店 Key Art（Steam 主图 / Library Hero / itch cover）

> 目标：横版构图氛围图。**文字/Logo 全部后期合成**，AI 只出"底图 + 构图"。

**模板 C（Steam 胶囊主图 616×353 横版）**

```
dark atmospheric game key art, landscape 16:9 composition, lone hooded survivor with glowing staff
facing a horde of monsters on the right, dark fantasy pixel art, thick black outline (Brotato style),
flat cartoon pixel, moody fog, palette: deep night blue base, golden accent highlights (#FFC800),
embers and particles, cinematic lighting, high contrast, no text, no logo, no watermark,
empty area on right side for title placement
```

中文：
```
暗黑氛围游戏主视觉，横版 16:9 构图，左侧孤身兜帽幸存者手持发光法杖，右侧一群怪物逼近，
暗黑幻想像素艺术，浓黑粗描边（土豆兄弟风格），扁平卡通像素，雾气弥漫，
配色：深夜蓝暗底，金色强调高光 #FFC800，余烬与粒子，电影级光照，高对比，无文字，无Logo，无水印，
右侧留空用于放标题
```

**模板 D（Steam Library Hero 3840×1240 超宽）**

```
ultrawide atmospheric game key art, 3:1 composition, epic dark fantasy landscape, tiny lone hero
silhouette in lower left, massive boss silhouette looming on the right, dark fantasy pixel art,
thick black outline, flat cartoon pixel, fog and floating embers, deep violet and gold palette,
cinematic, no text, no logo, no watermark, large empty dark area on left for title
```

**模板 E（itch cover 630×500 竖版方形）**

```
square game cover art, 1:1 composition, hero in center facing boss, dark fantasy pixel art,
thick black outline (Brotato style), flat cartoon pixel, dramatic lighting, deep blue + gold palette,
no text, no logo, no watermark, margin around subject for cropping
```

> 👁 **构图检查**：主视觉必须含"玩家可见角色 + 至少 1 个 boss/怪群"（art-bible §7.3），禁止出现游戏内没有的元素。
> ⚠️ **尺寸策略**：ImageGen 不一定精确出 616×353 / 3840×1240 / 630×500。做法：先生成近似比例大图（如 1:1 或 16:9），再用 §3 的"中心裁剪到目标宽高比"处理。

---

### 2.3 UI 图标（浅底 + 亮度抠图 → 透明）

> 目标：44px 正方形技能图标，风格与现有 13 种程序化 shape 图标（`ui/drawables.py:SKILL_ICONS`）一致：**单色 + 高光 + 厚描边 + 居中**。
> ⚠️ 透明参数失效 → 图标 prompt 同样用"浅色背景 + 深色主体"，入库前亮度差分抠图（§3.2）。

**模板 F（UI 图标）**

```
flat pixel UI icon, {图标描述}, single primary color with golden highlight, thick dark outline,
centered, plain light gray background, high contrast, simple readable silhouette, 44x44 icon, dark fantasy style,
no text, no watermark, no border, bottom right empty margin
```

中文：
```
扁平像素 UI 图标，{图标描述}，单一主色 + 金色高光，浓黑描边，居中，纯浅灰背景，高对比，简洁可读剪影，44x44 图标，
暗黑幻想风格，无文字，无水印，无边框，右下角留空
```

**直接可复用清单**（对应现有 13 种，若要做 PNG 版）：arrow_up / arrow_right / lightning / speed / triple / magnet / snowflake / crit / heart / blade / chain / trap / shield / coin

> 👁 选型：图标在 44px 下必须一眼可读；复杂图标（chain/trap）优先保留现有程序化 shape，AI 只做参考。

---

### 2.4 背景氛围图（5 地图主题各 1 张）

> 目标：氛围背景（商店截图背景 / 主视觉底图 / 可能用作 Library Hero 元素）。每张只允许 1 个 accent 主色（art-bible §5.3 主题色规则）。

**模板 G（背景氛围图）**

```
dark atmospheric background art, {地图关键词}, {地图英文名}, dark fantasy pixel art,
thick black outline accents, flat cartoon pixel, no characters, wide landscape,
palette: base {BG_HEX}, accent {ACCENT_HEX}, ambient {AMBIENT_HEX}, subtle vignette,
no text, no watermark
```

**5 张地图填表**（色值取自 art-bible §2.3）：

| # | 地图 | 关键词（中/英） | BG_HEX | ACCENT_HEX | AMBIENT_HEX |
|---|---|---|---|---|---|
| 0 | 荒芜墓地 | 苔藓、夜露、墓碑 / moss, night dew, gravestones | #0F120C | #505F37 | #6E7684 冷灰蓝 |
| 1 | 腐化沼泽 | 腐水、毒气、菌丝 / toxic water, gas, mycelium | #141E0A | #3C822D | #687C66 阴绿 |
| 2 | 暗影庭院 | 哥特、回廊、咒印 / gothic, corridors, runes | #0F0519 | #5F3782 | #706086 暗紫 |
| 3 | 钢铁废墟 | 铁锈、废铁、机械 / rust, scrap, machinery | #19120C | #6E695F | #807264 锈棕 |
| 4 | 虚空裂缝 | 裂隙、虚空、引力 / rift, void, gravity | #08000F | #782D9B | #64547E 深紫 |

---

## 3. 后处理流水线

### 3.1 总流程（每个 sprite 资产必经）

```
AI 候选图（1024级，浅底深主体）
  → ① 水印裁剪（§5，可脚本）
  → ② 亮度差分抠图：背景（亮）→ alpha=0，主体（暗）→ alpha=255（可脚本 + 👁 阈值复核）
  → ③ bbox 主体裁剪 + 方形化（可脚本）
  → ④ 降采样到目标像素尺寸（16×16 / 96×96；可脚本，nearest/box）
  → ⑤ 调色板对齐美术圣经色板（可脚本 + 👁 复核）
  → ⑥ 3 帧扩展与合成 48×16 / 288×96（脚本生成 wobble 帧 + 👁 帧2微调）
  → ⑦ 人工质控清单（§3.4，👁 必须）
  → ⑧ 写入 assets/sprites/{name}.png（最终入库）
```

> ⚠️ **抠图是新增关键步骤（v1.1）**：因 transparent 参数失效，所有 sprite/图标必须走"浅底亮度差分抠图"。若某候选背景亮度接近主体（差分阈值调不动），判定"不可差分"→ 弃用或按 §4 重生成。

### 3.2 降采样、抠图与像素化算法（Python/PIL 思路）

```python
from PIL import Image

TARGET = 16          # 普通怪/玩家/精英；boss 用 96
OUTLINE = (18, 14, 26)

def luminance(px):
    """感知亮度（0-255）"""
    return 0.299 * px[0] + 0.587 * px[1] + 0.114 * px[2]

def matte_by_luminance(img, threshold=160):
    """② 亮度差分抠图：背景（亮）→ 透明，主体（暗）→ 保留。
    前提：prompt 已要求 'plain light gray background, high contrast'。
    实测候选背景亮度约 140-250，主体中心亮度约 25-80，阈值默认 160 可分离。"""
    img = img.convert("RGBA")
    px = img.load()
    w, h = img.size
    for y in range(h):
        for x in range(w):
            r, g, b, a = px[x, y]
            if luminance((r, g, b)) > threshold:
                px[x, y] = (0, 0, 0, 0)       # 背景→透明
    return img

def bbox_crop_square(img):
    """③ 裁主体 bbox 并方形化（透明底）"""
    bbox = img.getbbox()
    if bbox:
        img = img.crop(bbox)
    w, h = img.size
    side = max(w, h)
    canvas = Image.new("RGBA", (side, side), (0, 0, 0, 0))
    canvas.paste(img, ((side - w) // 2, (side - h) // 2))
    return canvas

def downsample_to_pixel(img, target=TARGET, method=Image.NEAREST):
    """④ 降采样：nearest/box 到 target×target"""
    return img.resize((target, target), method)

def quantize_to_palette(img, palette):
    """⑤ 调色板对齐：把每个像素映射到美术圣经色板最近色"""
    img = img.convert("RGBA")
    px = img.load()
    w, h = img.size
    for y in range(h):
        for x in range(w):
            r, g, b, a = px[x, y]
            if a < 128:                        # 半透明→全透明（去AI抗锯齿毛边）
                px[x, y] = (0, 0, 0, 0)
                continue
            px[x, y] = (*nearest_color((r, g, b), palette), 255)
    return img

def nearest_color(c, palette):
    return min(palette, key=lambda p: sum((p[i]-c[i])**2 for i in range(3)))
```

> 👁 **阈值复核（必须人工）**：`matte_by_luminance` 的阈值需要按候选图微调。自动跑完后，用"透明化预览图"（把 alpha=0 像素染成洋红，见下）检查：① 背景是否全抠掉；② 主体边缘有没有被误抠（深色描边不能丢）。这一步 👁 必须人工目检。
> 🤖 辅助预览脚本：`out = img.copy(); out.putalpha(Image.eval(img.getchannel('A'), lambda a: 255)); 把 alpha=0 处染 (255,0,255)` 另存 PNG 供目检。
> ⚠️ **调色板规则**：sprite base 颜色数 ≤ 11（player.png 当前上限，boss ≤ 6，art-bible §9.2）。调色板 = OUTLINE + ACCENT 主色系（明/暗/高光 3 档）+ 少量通用色（眼睛/皮肤）。超出上限时 👁 人工合并近似色。
> 💡 若系统无 PIL：pygame 用 `pygame.transform.scale` + `pygame.surfarray` 逐像素映射，逻辑等价；推荐 PIL 做批量脚本，pygame 做入库前预览。

### 3.3 3 帧切帧规则

现有 loader（`asset_loader.py:load_image`）按 `width // 3` 切帧，强约束 3 帧。**帧规则（art-bible §3.2）**：

| 帧 | 角色（玩家/小怪/精英） | Boss |
|---|---|---|
| 帧1 | 待机/基础姿态 | 待机/悬浮 |
| 帧2 | **动作极点**（武器挥下、冲锋前倾、跃起中点） | 施法/咆哮极点 |
| 帧3 | = 帧1（或镜像） | = 帧1（或轻微镜像） |

**帧扩展方法（推荐顺序）**：
1. **脚本 wobble 帧**（可自动化）：帧1 → 帧3 直接复制；帧2 用 `y 偏移 ±1px` + 可选 `x 缩放 1.05` 制造动作感（对齐 loader 中 `int(math.sin(i*2.1)*2)` 的 wobble 语义）。
2. **镜像帧**（可脚本）：帧3 = 帧1 水平翻转（适合左右对称怪）。
3. **👁 帧2 人工微调**：若资产有明确"动作叙事"（charger 冲锋、elite 压迫 wobble），由人工在 16px 网格上手绘/微调帧2（移动 1-2 像素改变肢体角度即可），不许 AI 直接出 3 帧。

> ⚠️ **禁止**：让 AI 直接出"3 帧对齐 sheet"——实测帧间会跳变，loader 切帧后动画会闪。

**合成 sheet**：

```python
def compose_sheet(frames, fw=16, fh=16):
    sheet = Image.new("RGBA", (fw * 3, fh), (0, 0, 0, 0))
    for i, f in enumerate(frames):
        sheet.paste(f.resize((fw, fh), Image.NEAREST), (i * fw, 0))
    return sheet
# 玩家/小怪/精英: 48×16；boss: 288×96；pickup: 24×24 单帧
```

### 3.4 人工质控清单（👁 每个 sprite 入库前必过）

| # | 检查项 | 通过标准 |
|---|---|---|
| 1 | **帧一致性** | 三帧主体位置差 ≤1px，无跳变；帧3=帧1 或明确镜像 |
| 2 | **轮廓清晰** | 16px 缩放下剪影完整、可读（"这是角兽/这是精英"一眼可辨） |
| 3 | **抠图干净** | 背景全透明（alpha=0），主体深色描边未被误抠；无背景残留斑块/渐变色晕；主体外预留 1-2px 透明外缘（loader 会补 2px 描边） |
| 4 | **信息密度** | 非透明像素占比 ≥ 40%（对照审计：elite 8% 太空 / charger 23% 太弱） |
| 5 | **调色板合规** | 颜色数 ≤11（boss ≤6），全部落在美术圣经色板/ACCENT 系内 |
| 6 | **命名与格式** | 文件名 = `assets/sprites/{name}.png`，RGBA，尺寸 = 48×16 / 288×96 / 24×24 |
| 7 | **水印残留** | 右下角 400% 放大无"AI生成"字样（§5） |

> 👁 任何一条不通过 → 回到对应环节（换候选 / 重跑降采样 / 人工微调），**不许带病入库**。

---

## 4. 批量生产计划（对照审计 P0-D / P1）

> 排期原则：先 P0（elite/charger），后 P1（ranger/boss/召唤怪），商店素材与 sprite 并行但独立。

| 序 | 资产 | 优先级 | 候选数 | 选型标准（👁） | 后处理步骤 | 质控点 | 预估 |
|---|---|---|---|---|---|---|---|
| 1 | elite.png | **P0** | 6-8 | 金色边饰+大角+发光眼；16px 可读；信息密度≥40% | 模板A(浅底) → 亮度抠图 → 降采样16 → 调色板 → 3帧wobble+帧2微调 → 48×16 | 1,2,3,4,5,6,7 | 0.5 天 |
| 2 | charger.png | **P0** | 6-8 | 低身前倾+大角+速度感；**不再是"小山"** | 模板A(浅底) → 亮度抠图 → 降采样16 → 调色板 → 3帧；帧2 体现"冲锋极点" | 1,2,3,4,5,6,7 | 0.5 天 |
| 3 | ranger.png | P1 | 4-6 | 持弓/弩 + 兜帽；不再是"戴帽农夫" | 模板A(浅底) → 亮度抠图 → 降采样16 → 调色板 → 3帧 → 48×16 | 1,2,3,4,5,6,7 | 0.5 天 |
| 4 | boss_corpse_king | P1 | 4-6 | 骨刺+腐肉+王冠；**压迫感 > 萌感** | 模板B(浅底,96) → 亮度抠图 → 降采样96 → 调色板 → 3帧 → 288×96 | 1,2,3,5,6,7 | 0.5 天 |
| 5 | boss_shadow_mage | P1 | 4-6 | 飘动斗篷+大头+魔法光 | 模板B(浅底,96) → 亮度抠图 → 降采样96 → 调色板 → 3帧 → 288×96 | 1,2,3,5,6,7 | 0.5 天 |
| 6 | shadow 召唤怪 | P1 | 3-4 | 半透明幽灵、暗紫 (100,0,150) 系；**与 enemy.png 视觉区分** | 模板A(浅底) → 亮度抠图 → 降采样16 → 调色板 → 48×16 | 2,3,4,5,6,7 | 0.5 天 |
| 7 | voidling 召唤怪 | P1 | 3-4 | 虚空浮体、深紫 (180,0,200) 系；区分于 enemy.png | 模板A(浅底) → 亮度抠图 → 降采样16 → 调色板 → 48×16 | 2,3,4,5,6,7 | 0.5 天 |
| 8 | Steam 胶囊主图 | 商店 | 5-8 | 含英雄+boss、构图张力、右侧留白放标题 | 模板C → 中心裁剪 616×353 → **人工合成文字/Logo** | 无水印、无游戏外元素 | 1 天 |
| 9 | Library Hero | 商店 | 3-5 | 超宽氛围、左侧留白放标题 | 模板D → 裁剪 3840×1240 → 合成标题 | 无水印 | 0.5 天 |
| 10 | itch cover | 商店 | 3-5 | 竖版/方形、居中主体 | 模板E → 裁剪 630×500 → 合成标题 | 无水印 | 0.5 天 |
| 11 | 背景氛围图 ×5 | 商店/截图 | 每图 3-5 | 单 accent 色、无角色、氛围到位 | 模板G → 裁剪 1920×1080 | 色环正确、无水印 | 1 天 |
| 12 | UI 图标（可选 PNG 版） | P2 | 每图标 2-3 | 44px 可读、单色+描边 | 模板F(浅底) → 亮度抠图 → 44×44 | 2,3,6,7 | 0.5 天 |

> ⚠️ **透明参数已失效**：上述所有 sprite/图标行均含"亮度抠图"步骤（§3.2 `matte_by_luminance`），取代旧的"透明底 bbox 裁剪"。

> 📦 **总 ImageGen 调用预算**：约 45-65 次候选生成（P0+P1 sprite 约 25-35 次，商店素材约 20-30 次）。建议**每批次生成后先人工选型，再进流水线**，避免浪费后处理时间。

---

## 5. 水印处理规范

实测：生成图右下角带 **"AI生成 WORKBUDDY"** 水印。商业化素材必须清除。

| 素材类型 | 规避策略 | 可脚本？ |
|---|---|---|
| **sprite 概念（浅底）** | 亮度抠图（§3.2）把亮背景→透明，水印文字（高亮白字）随背景被抠掉；随后 bbox 裁剪进一步去掉右下角 | 🤖 脚本 + 👁 目检 |
| **UI 图标（浅底）** | 同上，亮度抠图 + bbox 裁剪 | 🤖 脚本 + 👁 目检 |
| **背景氛围图** | prompt 要求"右下角留空"→ 生成后裁剪右下 10-15% 区域，或中心裁剪到目标比例时水印落在裁切区 | 🤖 脚本 + 👁 目检 |
| **Key Art / 封面（不透明）** | ① prompt 要求右侧/底部留空 → ② 中心裁剪到目标宽高比时水印落裁切区 → ③ 用合成标题/Logo 覆盖右下区域 | 🤖 裁剪 + 👁 合成 |
| **最终商店素材** | **必须人工 400% 放大右下角确认无残留**，或脚本做水印文本像素检测（检测右下角区域是否含高对比文本团） | 👁 必须 + 🤖 辅助检测 |

> ⚠️ **v1.1 提示**：若水印文字颜色与主体相近（深色水印落在浅底上），亮度抠图可能把水印误留为"主体残片"——质控清单第 3 项（抠图干净）需专门检查右下角有无文字形残片。

> ⚠️ **红线**：任何进入 `assets/sprites/` 或商店发布目录的图片，水印残留 = 不合格，直接退回。
> ⚠️ 合规提示：AI 生成素材用于商业发布，需确认所用 ImageGen 服务的商用条款；本流水线仅处理视觉水印，不构成法律意见。

---

## 6. 自动化 vs 人工判定清单

### 🤖 可自动化（主理人可跑）
1. ImageGen 候选批量生成（按 §2 模板，一次一批）
2. 水印裁剪（右下 strip / bbox）
3. **亮度差分抠图**（§3.2 `matte_by_luminance`，阈值默认 160，需人工复核）
4. bbox 裁剪 + 方形化
5. 降采样到 target（nearest/box）
6. 调色板量化（映射到美术圣经色板）
7. 3 帧 wobble/镜像扩展 + 48×16 / 288×96 sheet 合成
8. 尺寸/格式/命名校验（48×16、RGBA、颜色数、信息密度 ≥40%）
9. 水印残留像素检测（辅助）
10. **候选量化初筛**（主体占比/背景亮度/颜色数统计，辅助选型，见 §7）

### 👁 必须人工判定（art-director / 用户拍板）
1. **候选选型**（哪个造型进流水线）——视觉叙事判断
2. **帧2 动作极点微调**——运动语义
3. **16px 可读性终审**（§3.4 质控 1-2）
4. 调色板超限时的合并取舍
5. **商店素材的文字/Logo 合成**（AI 不做字）
6. 最终商店素材水印目检
7. 任何偏离美术圣经的标注（visual consistency 红线）

---

## 7. P0 候选量化初筛与选型方法（v1.1 实测反馈）

> 背景：主理人已按模板 A 生成 6 张 P0 候选（elite 3 + charger 3），全部 1024×1024 不透明。art-director 当前模型无视觉能力，因此**先用脚本做客观量化初筛，再交人工/有视觉能力的角色做造型终审**。量化数据见 `design/art/candidate-analysis-p0.txt`。

### 7.1 量化指标与判读

| 指标 | 含义 | 判读标准 |
|---|---|---|
| 背景亮度（四角平均） | 抠图可行性 | ≥ 140 且明显高于主体 → 亮度差分可用；接近主体亮度 → 不可差分 |
| 主体中心亮度 | 主体明暗 | 越低越利于与浅底分离 |
| body_ratio（主体像素占比） | 主体是否够大 | sprite 目标 ≥ 40%；概念图参考值 20-80%，过低说明主体太小 |
| 颜色数（64×64 降采样） | 背景复杂程度 | 越高背景渐变越复杂 → 色键不可行（印证亮度差分必要性） |

### 7.2 P0 候选初筛结果（基于量化，非视觉）

| 候选 | 四角背景亮度 | 中心亮度 | body_ratio | 抠图可行性 | 初筛结论 |
|---|---|---|---|---|---|
| elite 15-52-41 | 深灰 ~70 | 65,45,23（暗） | 25.5% | ⚠️ 背景暗，阈值难定 | **备选**（背景偏暗，差分需低阈值，有误抠风险） |
| elite 15-53-27 | 浅灰 ~165-197 | 53,39,29（暗） | 25.5% | ✅ 亮底暗主体 | **主选候选** |
| elite 15-53-51 | 近白 ~237-253 | 54,39,24（暗） | 32.8% | ✅ 最易差分 | **主选候选（优先）** |
| charger 15-52-41 | 中灰 ~130-155 | 47,41,42（暗） | 20.5% | ⚠️ 中灰，可试 | 备选 |
| charger 15-54-16 | 浅灰 ~172-216 | 48,42,45（暗） | 56.7% | ✅ 亮底暗主体，占比大 | **主选候选** |
| charger 15-54-40 | 亮底 ~131-253 不均匀 | 80,49,36 | 79.3% | ⚠️ 背景不均匀 | 备选（占比大但背景非均匀，差分可能残留） |

> 👁 **结论（需视觉终审）**：量化只能证明"哪些候选抠图可行、主体够大"，**无法判断造型叙事**（这是不是精英怪？有没有金饰大角？）。视觉终审必须由**能看图的人/模型**执行：
> - 优先：用户或主理人目检 6 张，对照 §2.1 选型 4 标准（描边/叙事/配色/居中）；
> - 或：主理人换一个有视觉能力的模型/工具做"图像描述"再回传给我判定；
> - 脚本无法替代造型判断——这是 👁 硬边界。

### 7.3 已确认的 P0 行动建议

1. **6 张候选不浪费**：elite 15-53-51、charger 15-54-16 直接进亮度抠图流水线（背景亮、主体暗、占比达标）。
2. **⚠️ 若视觉终审否决造型**（如"这不是角兽/这是小山"）→ 按 §2.1 新模板（浅底）**重新生成**该资产候选，不再等透明。
3. **批量生产其余资产**（ranger/boss/召唤怪）一律用**新模板（浅灰底+高对比）**生成，避免再踩透明失效。

---

## 8. 附录

### 8.1 目录与命名规范
- AI 候选：`design/art/ai-candidates/{category}/{asset}_v{n}.png`（不入运行时）
  - category：`sprites/` `keyart/` `icons/` `bg/`
- 终稿：`assets/sprites/{name}.png`（唯一入库路径，命名必须与 loader 引用一致）
- 商店素材：`design/release/`（与 `commercialization-plan-v1.md` 同目录）
- 已存在样例：`design/art/ai-samples/`（2 张实测，仅参考）

### 8.2 目标尺寸速查
| 资产 | sheet | 单帧 base | 渲染 | 备注 |
|---|---|---|---|---|
| 玩家 | 48×16 | 16×16 | 32×32 | 3 帧 |
| 普通敌人 | 48×16 | 16×16 | 28×28 | 3 帧 |
| 精英 | 48×16 | 16×16 | 40×40 | 3 帧 |
| Boss | 288×96 | 96×96 | 60-100px | 3 帧 |
| pickup (orb/pack/shield) | 24×24 | 24×24 | 24×24 | 单帧 |

### 8.3 与引擎/管线的风险（供主理人转程基岩）
- ⚠️ `entities/player.py` 反向依赖 `ui/render_helpers.py`（技术债）：若替换 sprite 涉及 render_helpers 改动，需同步重构，避免主循环回归。
- ⚠️ loader 有"PNG 缺失 → 程序化 fallback"双路径：重做 sprite 期间**保留原 PNG 或 fallback**，避免黑屏。
- ✅ 新 sprite 只要满足 3 帧 + 尺寸，loader 无需改代码即可加载。

### 8.4 下一步建议（供主理人排期）
1. **P0 候选已生成**：elite 15-53-51 / charger 15-54-16 为主选，进入亮度抠图流水线（需先人工/视觉终审造型叙事）。
2. 流水线脚本（§3.2/§3.3）建议由程基岩按此文档实现为 `tools/ai_sprite_pipeline.py`（纯 PIL，不入游戏运行时），含 `matte_by_luminance` 亮度抠图 + 透明化预览（洋红底）辅助阈值复核。
3. 商店 Key Art 的标题/Logo 字型待用户拍板（思源宋体 SemiBold / Sans CJK SC Bold）。
4. 若 6 张候选视觉终审全部不达标 → 按新模板（浅灰底）重生成 elite/charger 各 6-8 张。

---

*文档结束*
