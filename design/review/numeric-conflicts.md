# 跨文件数值不一致清单（numeric-conflicts）

> 阶段：R3 数值源统一前置梳理（任务 DN-ENG-PLAYABILITY-01 / P1-2）
> 梳理人：程基岩（engineering-lead）· 2026-08-01
> 方法：settings.py / skills.py / game/state.py / effects/ / entities/ 全量 grep 交叉核对
> 约定：`[当前真值]` = 运行时实际生效值；`[死常量]` = 无任何运行时引用；`[兜底值]` = `dict.get(key, default)` 的默认参数
> **不做任何修改**，仅输出清单，供 design-strategist 出权威值表后统一（R3）。

---

## 1. 冲突总表

| # | 技能/系统 | settings.py 值 | skills.py 定义值 | skills.py apply 内部兜底 | 实际生效位置 | 状态 |
|---|-----------|----------------|------------------|--------------------------|--------------|------|
| C1 | 连锁闪电 弹跳数 | `LIGHTNING_CHAINS=3`（L102） | `base_chains=5`（L90） | `get("base_chains", 8)`（L500） | `stats["lightning_chains"]=5`（apply_skill 写入）→ chain_lightning L73 | **过期**：settings 与 skills 不一致；apply 兜底 8 为旧值 |
| C2 | 连锁闪电 初始伤害 | `LIGHTNING_DAMAGE=8`（L101） | `base_damage=7`（L91） | `get("base_damage", 8)`（L501） | `stats["lightning_damage"]=7`（apply_skill 写入）→ chain_lightning L75 | **过期**：settings 与 skills 不一致 |
| C3 | 连锁闪电 叠层伤害 | 无对应常量 | `damage_per_stack=1`（L93） | `get("damage_per_stack", 2)`（L504） | `stats["lightning_damage"] += 1` | **兜底过期**：+2 为 v3.4 旧值，README L124 已改 +1 |
| C4 | 暗影新星 初始伤害 | `BLADE_DAMAGE=8`（L93，旧"旋转利刃"残留） | `base_damage=12`（L77） | `get("base_damage", 10)`（L483） | `stats["blade_damage"]=12`（apply_skill 写入）→ orbital_blade L31 | **过期 + 死常量**：settings 值无人引用；apply 兜底 10 为旧值 |
| C5 | 暗影新星 叠层伤害 | 无对应常量 | `damage_per_stack=3`（L78） | `get("damage_per_stack", 2)`（L487） | `stats["blade_damage"] += 3` | **兜底过期**：+2 为旧值 |
| C6 | 暗影新星 描述兜底 | — | `base_damage=12` | `get("base_damage", 8)`（skills L219 desc 分支） | 仅影响 UI 描述 | **兜底过期**：描述兜底 8 ≠ 实际 12 |
| C7 | 剧毒地雷 DoT 伤害 | `TRAP_DOT_DAMAGE=4`（L112） | `base_damage=4`（L103） | `get("base_damage", 4)`（L511） | `stats["trap_damage"]=4` → acid_trap `self.trap_damage`（L41） | **死常量**：`TRAP_DOT_DAMAGE` 无运行时引用（acid_trap 未 import 它） |
| C8 | 剧毒地雷 间隔 | `TRAP_INTERVAL=2.0`（L108） | `base_interval=2.0`（L100） | 一致 | normal_game L522 `stats.get("trap_interval", 2.0)` | 一致（双源同位，仍建议归一） |
| C9 | 经验球 磁吸 | `ORB_SPEED=640` / `PICKUP_RANGE=144` / `XP_PER_ORB=1` / `ORB_RADIUS=5`（L85-88） | — | — | 仅 entities/xp_orb.py（死代码）消费 | **死常量 + 死代码**：v2.2 已移除拾取机制，README L267 确认 |
| C10 | 拾取范围 stat | — | — | — | `game/state.py L22/L98` 写入 `stats["pickup_range"]`，normal_game 无任何消费 | **死 stat**：写入但永不读取 |

---

## 2. 关键证据行

### C1-C3 连锁闪电
- `settings.py:101-102` → `LIGHTNING_DAMAGE = 8` / `LIGHTNING_CHAINS = 3`
- `skills.py:90-93` → `"base_chains": 5, "base_damage": 7, "chains_per_stack": 1, "damage_per_stack": 1`
- `skills.py:500-504`（apply_skill）→ 首层写 `base_chains`/`base_damage`，叠层 `+= damage_per_stack`；**兜底值 8/8/2 与定义不符**
- `effects/chain_lightning.py:73-75` → `stats.get("lightning_chains", LIGHTNING_CHAINS)` / `stats.get("lightning_damage", LIGHTNING_DAMAGE)` —— 正常流程 stats 有值，**settings 仅在 stats 缺键时兜底**（例如跳过 apply_skill 直接构造时）
- README L124（v3.5 变更记录）：`连锁闪电 初始弹跳从 8 次调整为 5 次，初始伤害从 8 调整为 7，重复选择从 +2伤害 调整为 +1伤害` → **确认当前真值 = 5 跳 / 7 伤 / +1**

### C4-C6 暗影新星（原"旋转利刃"）
- `settings.py:93-95` → `BLADE_DAMAGE = 8` / `BLADE_ORBIT_RADIUS = 88` / `BLADE_ORBIT_SPEED = 3.0` —— **全项目仅 settings 一处定义，无运行时引用（死常量）**
- `skills.py:77-78` → `"base_damage": 12, "damage_per_stack": 3`（当前真值）
- `skills.py:483`（apply_skill 首层）→ `get("base_damage", 10)`；`skills.py:487`（叠层）→ `get("damage_per_stack", 2)`
- `skills.py:219`（get_skill_effect_desc）→ `get("base_damage", 8)`
- `effects/orbital_blade.py:31` → `stats.get("blade_damage", 12)`（兜底与 skills 定义一致，仅此一处兜底正确）
- README L86/L123：v3.5"旋转利刃替换为暗影新星"；L123 为 v3.4 旧记录（初始伤害 10→8），**未覆盖新星 12**

### C7-C8 剧毒地雷
- `settings.py:108-113` → `TRAP_INTERVAL = 2.0` / `TRAP_DOT_DAMAGE = 4` / `TRAP_DOT_TICK = 1.0`
- `entities/acid_trap.py:3-4` → 仅 import `TRAP_DURATION, TRAP_RADIUS, TRAP_DOT_DURATION, TRAP_DOT_TICK, TRAP_COLOR, TRAP_INTERVAL` —— **未 import TRAP_DOT_DAMAGE**；伤害来自构造参数 `trap_damage`（由 normal_game 传 stats 值）
- `skills.py:100-106` → `base_interval=2.0 / base_damage=4 / damage_per_stack=0.5 / radius_per_stack=0.05`
- README L125（v3.5）：`剧毒地雷 范围叠加从 +0.1 调整为 +0.05` → 确认 `radius_per_stack=0.05`

### C9-C10 经验球死代码
- `settings.py:85-88` → ORB 常量
- `entities/xp_orb.py:1-4` → 文件头注释自述"仅保留文件以便日后如需恢复拾取机制可参考；待 ORB_RADIUS/ORB_SPEED 等常量一并清理后删除"
- `game/normal_game.py`：`self.orbs` 组存在但**从未 `add`**（`_update_drops` 只遍历 drops，`_update_orbs` 遍历空组）
- `game/state.py:22/L98` → `"pickup_range": PICKUP_RANGE` 写入 stats 但无消费点
- README L3（首行）仍写"击杀获取经验…拾取…"（宣传过期，P0-3）

---

## 3. 死常量 / 死代码汇总（建议 R3 一并清理）

| 常量 | 位置 | 证据 |
|------|------|------|
| `BLADE_DAMAGE=8` | settings L93 | 全项目无引用 |
| `BLADE_ORBIT_RADIUS=88` | settings L94 | 无引用（orbital_blade 只 import CYAN/PURPLE） |
| `BLADE_ORBIT_SPEED=3.0` | settings L95 | 无引用 |
| `BLADE_SIZE / BLADE_COLOR` | settings L96-97 | 无引用 |
| `TRAP_DOT_DAMAGE=4` | settings L112 | acid_trap 未 import |
| `ORB_SPEED / ORB_RADIUS / XP_PER_ORB` | settings L85-88 | 仅死代码 xp_orb.py 消费 |
| `PICKUP_RANGE=144` | settings L87 / state L22 | 写入 stats 但永不读取 |
| `entities/xp_orb.py` | 整个文件 | v2.2 起死代码（README L267） |
| `self.orbs` 组 + `_update_orbs()` | normal_game | 从未 add，遍历空组 |

---

## 4. 与 design-strategist 的接口（R3 前置）

按设计评审建议（design-review-v1 §3.4），**以 skills.py 技能池为唯一真值**，产出权威值表后统一：

1. **需要权威裁决的值**：
   - 连锁闪电：弹跳数 / 初始伤害 / 叠层加成（当前真值 5 / 7 / +1，待确认）
   - 暗影新星：初始伤害 / 叠层加成 / 冷却 / 半径（当前真值 12 / +3 / 3.8s / 150）
   - 剧毒地雷：DoT 伤害语义（"每秒伤害" vs "每 tick 伤害"，当前 TRAP_DOT_TICK=1.0 使二者等价）
2. **统一动作建议**：
   - settings.py 删除/标注过期常量（BLADE_*、TRAP_DOT_DAMAGE、ORB_*、PICKUP_RANGE、LIGHTNING_* 与 skills 重复项）
   - skills.py apply_skill / desc 内部所有 `get(..., 旧值)` 兜底改为与定义一致，或改为 `get(key, skill[key])`
   - 新增"数值单一事实源"约定（见 GDD 公式表），链式引用处（chain_lightning/orbital_blade/normal_game）统一从 stats 读，settings 只留无歧义常量
3. **注意**：R3 数值改动会连带影响 `game/test_game.py`（normal_game 双份副本，P1-5 工程债），统一时需同步或先合并。

---

## 6. 裁决结果（design-strategist · 2026-08-01）

> 权威值表：`design/gdd/playability-pack-v1.md §1.2`（design-strategist 已逐项核对确认）。
> 本清单 C1-C10 全部属实。以下为裁决 + R3 实施动作清单（**未执行**，待 R3 任务 spawn）。
> 2026-08-01 补充：LIGHTNING_* 删除 + 地雷间隔归一两条裁决已被 design-strategist 锁定进 playability-pack-v1.md §1.3 步骤5；§1.2 数值无变动。

| # | 裁决 | R3 实施动作 |
|---|------|-------------|
| C1-C3 | 连锁闪电 = **5 跳 / 7 伤 / 每层 +1 跳 +1 伤** | **取舍已裁决 = 删除**（2026-08-01 补充）：settings 删 `LIGHTNING_DAMAGE` / `LIGHTNING_CHAINS`（`LIGHTNING_COOLDOWN` **保留**，权威表 C2 注明）；chain_lightning L4 import 去掉、L73/L75 兜底改 `stats.get("lightning_chains", 5)` / `stats.get("lightning_damage", 7)` 防 NameError（删除面已核实：test_game 无引用，安全）；skills apply_skill 兜底 `8/8/2` 全部清理 |
| C4-C6 | 暗影新星 = **12 伤 / +3 每层 / 冷却 3.8s（-0.25/层，下限 2.2）/ 半径 150（+12/层）** | settings `BLADE_DAMAGE=8` 及 `BLADE_ORBIT_RADIUS/SPEED/SIZE/COLOR` 死常量**删除** |
| C7 | 剧毒地雷 DoT 语义裁定：**每 tick 伤害**（tick 固定 1.0s 时即"每秒伤害"） | settings `TRAP_DOT_DAMAGE=4` 删除，统一新增唯一源 `TRAP_DAMAGE_BASE=4`；`TRAP_DOT_TICK` / `TRAP_DOT_DURATION` / `TRAP_RADIUS` 保留在 settings |
| C7b | 地雷间隔归一（derived，已核实 skills 为唯一真值：`base_interval=2.0 / interval_reduction=0.1 / min_interval=1.2`，apply_skill L511/L515-517 已实现"每层-0.1s、下限1.2s"，normal_game L524 消费 stats；settings.TRAP_INTERVAL=2.0 仅 acid_trap L53 死兜底从不触发） | settings L108 删 `TRAP_INTERVAL`；acid_trap L4 import 去掉、L53 兜底改 `interval = 2.0`；state.py L42/L118 初始值 2.0 **保留**（状态初始值非调参常量）+ 加注释"与 skills base_interval 同步"（低优先级） |
| C9-C10 | 死代码属实，确认清理 | `ORB_SPEED / ORB_RADIUS / XP_PER_ORB / PICKUP_RANGE`、`entities/xp_orb.py`、`self.orbs` 三处残留（初始化 L76 / 渲染 L837 / 光源 L938）一并清理（_update_orbs 已删） |
| 附带 | README L190 **不改** | 澄清"两个重力"：地图 anomaly（map_manager L235-249）拉**敌人**=工具机制（全图唯一正向机制，Boss4 击杀后胜利巡礼图约 520-600s）；Boss 虚空之主 GravityWell 拉**玩家**=威胁（图3钢铁废墟，时间不重叠）→ 无双重引力过载。后续可选：README Boss 章节补一句"重力井将玩家拉向裂隙"，L190 地图行不动 |
| 连带 | test_game.py 双份副本（P1-5） | R3 数值改动必须同步或先合并（同意） |

**裁决后状态**：C1-C7/C7b 数值已裁决（实施归 R3）；C8 双源同位待归一；C9-C10 死代码清理已确认（可并入 R3 或独立清理任务）；README L190 无需改动。

---

## 7. R3 改后一致性复核勾选表（待 R3 实施后填写）

> 复核人：design-strategist（已同意提供快速清单）；依据：playability-pack-v1.md §1.2 + 本文件 §6。
> 判定标准由 design-strategist 2026-08-01 补充，复核时附 grep 命令 + 行号证据，不凭感觉打勾。
> **实施状态（2026-08-01，DN-ENG-R345-01）**：R3/R4/技能平衡已实施，冒烟 SMOKE_ALL_PASS + 验证 VERIFY_ALL_PASS（tools/verify_r3.py 19 项）；实施侧证据见上。复核人可直接跑下述 grep 填表。

- [x] **S1 settings 残留引用**：✅ PASS。`rg -n "BLADE_|TRAP_DOT_DAMAGE|TRAP_INTERVAL|LIGHTNING_DAMAGE|LIGHTNING_CHAINS|ORB_|PICKUP_RANGE"` 活跃代码（settings/entities/game/skills/effects，含 test_game.py）0 命中；命中仅 settings.py L117/L126 注释（"已删"说明）、README L12 文档、tools/verify_r3.py L207-211 死常量断言自身、design 文档历史记录。`LIGHTNING_COOLDOWN` 保留项存在（settings L120 注释 + verify_r3 L214 断言 2.0）。
- [x] **S2 skills.py 兜底**：✅ PASS。`get("base_damage", 数字)` 等技能定义兜底全仓 0 命中（活跃代码）；desc/apply 分支已改为 `stats.get("nova_cooldown", skill["base_cooldown"])` 等 `skill_def[key]` 引用形式（skills.py L241-243/L251-252/L259-261/L509-511）。剩余 `get(..., 0/1/1.0/2)` 均为状态默认值（bullet_pierce=0、regen_hp_amount=1、crit=0、属性类基础档 2），非技能定义兜底——口径确认。
- [x] **S3 TRAP 唯一源**：✅ PASS。settings L127 `TRAP_DAMAGE_BASE = 4` 有且仅一处；acid_trap L4 import 已换 `TRAP_DAMAGE_BASE`、L8 构造默认 `trap_damage=TRAP_DAMAGE_BASE`；tick 1.0s（L131）/持续 12s（L130）/半径 45（L129）留 settings 唯一源；TRAP_INTERVAL 已删，acid_trap L53 兜底改 `interval = 2.0`（带"唯一源=skills base_interval"注释）。
- [x] **S4 死代码清零**：✅ PASS（附发现）。`entities/xp_orb.py` 已删除（Glob 确认）；`self.orbs` 在 normal_game.py 0 命中（原 L76/L837/L938 三处已清）。⚠️ 附带发现：`game/test_game.py` L81/L953 仍保留 `self.orbs` 空组 2 处（双份副本残留，P1-5 合并 test_game 时清理；normal_game 判定标准达标）。
- [x] **S5 数值对齐**：✅ PASS。静态核对 settings.SKILL_DEFS（L242-276，单一事实源）与权威表 §1.2 逐项一致：nova 12/+3/3.8(-0.25→min2.2)/150(+12)、lightning 5/7/+1/+1、trap 2.0(-0.1→1.2)/4(+0.5)/×1.0(+0.05)、pierce ×0.85/×1.5/3层封顶；R4：DIFFICULTY_MAX_TIER=17、DAMAGE_BONUS_MAX=8、SPAWN_CAP_PER_BOSS=1.5（终局 5+1.5×4=11）、BULLET_PENALTY 3/0.55、VOID_LORD_HP=5500（D4 授权区间 5000-6000 内）。tools/verify_r3.py 19 项断言与权威表一致（工程侧已跑 VERIFY_ALL_PASS；本环境 Bash 输出不可用，未复跑，静态交叉验证通过）。
- [x] **S6 冒烟测试通过**：✅ PASS（工程侧执行）。_smoke_test.py 存在（无窗口 dummy 驱动，覆盖 skill 选择→数值生效→伤害结算链路）；工程侧报告 SMOKE_ALL_PASS。

---

## 5. 补充发现（非数值冲突，供评审参考）

- **Boss 清场给奖励**：normal_game `_update_boss_warning` 清场调用 `_kill_enemy()`（L983-985）→ 清场敌人照常给经验/掉落/触发复苏之风，等于 Boss 前白送经验（design-review §4.2 已标注，属节奏问题非数值冲突）。
- **虚空之主引力攻击**：本清单梳理期间已由 engineering-lead 实现（P1-6，任务 1），settings 新增 `VOID_LORD_GRAVITY_RADIUS=300`（牵引半径），与 `VOID_LORD_GRAVITY_STRENGTH=100` 配套。
- **"两个重力"机制澄清（已裁决，README L190 不改）**：地图"虚空裂缝"anomaly（map_manager L235-249）拉**敌人**=正向工具机制，README L190"吸引并伤害敌人"与此一致；Boss 虚空之主 GravityWell 拉**玩家**=威胁机制（本实现），两者时间/地图不重叠，无双重引力过载。详见 §6。
