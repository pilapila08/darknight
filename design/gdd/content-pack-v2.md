# 暗夜求生 Darknight · 内容扩充设计包 v2

> 任务：DN-DES-C01（design-strategist / 文策渊）
> 基线：v1.0-hardening（R3 数值源已统一、R4 难度曲线方案A 已落地、R5 四角色已实现）
> 前置文档：
> - `design/gdd/playability-pack-v1.md`（R3 权威数值表 / R4 难度曲线 / R5 角色设计）
> - `design/review/design-review-v1.md`（P1-5：尸王/暗影巫师缺压迫感、ranger 强化；P2-2 内容量偏小）
> - `production/sprint-plan-v1.md` v1.2（方向：完整性 + 可玩性优先）
> - `settings.py`（R3 后唯一数值源，所有新数值必须入 settings）
> 本包覆盖：新武器×2 / 新敌人×2 / meta MVP（暂缓）/ R7 Boss 压迫感演出 / 依赖排序
> **定稿状态（2026-08-01 拍板）**：新武器×2 ✅ / 新敌人×2 ✅ / R7 P0+P1 ✅ / meta MVP ⏸ 暂缓（§3 设计保留，待后续立项）
> 标注约定（沿用 v1）：
> - `[代码事实]` 基于当前代码可直接验证，改代码前不得违背
> - `[设计决策]` 本文提出的新方案，供用户拍板；未批准前不改代码
> - `[待 Playtest]` 数值推导合理但需实机验证，验证后回填
> - 影响面说明：本文件**不修改任何代码**，仅提供工程实现规格

---

## 0. 执行摘要

| # | 交付项 | 结论 | 状态 |
|---|--------|------|------|
| 1 | 新武器×2 | **凛冬之环**（贴身减速 AOE，复用死钩子 `apply_frostbite`）+ **圣焰喷射器**（短程锥形喷吐 + 燃烧，可暴击）；技能池 14→16；数值进 `SKILL_DEFS` | 表已给，待批准后程基岩落码 |
| 2 | 新敌人×2 | **怨灵**（tier4/136s 闪现逼近）+ **唤魔师**（tier6/204s 召唤 + 追踪弹），均有专属行为而非数值换皮 | 表已给，含 sprite 规格供美术 |
| 3 | meta MVP | **已拍板暂缓**：每日挑战 + 本地日榜设计完整保留（全离线）；本批不扩展存档 schema、不做入口/结算写入 | ⏸ 暂缓，设计保留待后续立项 |
| 4 | R7 演出 | 尸王/暗影巫师压迫感：P0 全复用现有 systems（juice/lighting/audio/camera/boss_hud）；P1 需美术 sprite 重绘 | 方案已给，P1 依赖林绘澄 |
| 5 | 依赖排序 | 数值/单份模块可立即做；normal_game 钩子依赖 R6 合并结果 | 见 §5 |

**一句话结论**：新武器走"独立输出通道"（不与火力+弹量+急速 DPS 三件套相乘）避免制造新的主导策略；新敌人填补 Boss1→Boss2 窗口（120–240s）的种类空白；meta（每日挑战+本地日榜）设计保留但本批暂缓；R7 靠复用已成熟的打击感/光照/音频系统把尸王与暗影巫师从"偏弱 sprite"救成"压迫感 Boss"。

---

## 1. 新武器 ×2（技能池 14 → 16）

### 1.1 设计原则（防主导策略）

`[代码事实]` 火力增强（等差 ≈(n+1)²/4）+ 增加弹量（线性 +1 发）+ 急速射击（×0.85）三者互乘构成纯 DPS 主导策略（v1 §4.1）。

**新武器红线：不得与 DPS 三件套形成乘法循环。**

- 新武器伤害使用**独立伤害键**（`flame_damage` / `frost_damage`），**不读** `bullet_damage` → 火力增强不放大新武器。
- 新武器间隔**不读** `fire_interval` → 急速射击不同时提速自动枪与新武器（防双吃）。
- 新武器与角色被动联动通过**暴击**（火枪手）与**站桩/控制**（坦克）等**维度**实现，而非数值耦合。

### 1.2 武器一：凛冬之环 Frost Aura（贴身减速 AOE · 防御/控场向）

**机制描述**：以玩家为中心持续释放冰霜光环。光环内敌人每 0.5s 受 1 次冰伤，并被减速（减速按层数叠加，离开光环立即恢复）。这是全武器池中**唯一**的控制/减速维度（现有 4 武器：单点 / 脉冲 AOE / 链式 / 放置 DoT，均无减速）。

`[代码事实]` `Enemy.apply_frostbite(slow_factor)` 已存在但**从未被任何技能调用**（死钩子）——本武器直接激活它，工程成本极低。

**角色联动**：
- **重装坦克**：贴身站桩 + 钢铁意志 → 光环全程覆盖价值最大化；减速让坦克少风筝多输出，是坦克最契合的武器。
- **火枪手/游侠**：低血角色把光环当"保命兜底"（替代复苏之风），贴脸怪被减速后逃生窗口拉大。

**SKILL_DEFS 权威数值表（新增 `SKILL_DEFS["frost"]`，单位标全）**

| 常量 | 值 | 单位 | 说明 |
|------|-----|------|------|
| FROST_BASE_RADIUS | 100 | px | 光环半径 |
| FROST_RADIUS_PER_STACK | 12 | px/层 | |
| FROST_TICK_INTERVAL | 0.5 | s | 每 tick 一次伤害+减速判定 |
| FROST_BASE_DAMAGE | 2 | 伤害/tick | 不参与暴击（控制武器，伤害从简） |
| FROST_DAMAGE_PER_STACK | 1 | 伤害/层 | |
| FROST_SLOW_BASE | 0.20 | — | 基础减速 20% |
| FROST_SLOW_PER_STACK | 0.15 | +/层 | 第 N 层总减速 = 0.20 + 0.15×(N−1) |
| FROST_SLOW_MAX | 0.65 | — | 减速上限 65% |

**首取 DPS 推导**：2 / 0.5s = **4.0 DPS（半径 100px 全场 AOE）+ 20% 减速**。对照 v1 权威表：新星 3.16（AOE+击退）、闪电 9.7（链）、地雷 ~6（放置）。控制本身就是收益，4 DPS + 减速定价合理；满层（如 4 层）≈ 10 DPS + 65% 减速，需实机验证（`[待 Playtest]` 若出现"无脑站撸"，`FROST_SLOW_PER_STACK` 0.15 → 0.10）。

**stats 键**（进 `state.py get_default_stats`）：
```python
"has_frost": 0, "frost_radius": 100, "frost_damage": 2, "frost_slow": 0.20,
```

**apply_skill 分支**（key `has_frost`）：
- 首次：`frost_radius=100 / frost_damage=2 / frost_slow=0.20`
- 重复：`frost_radius += 12`、`frost_damage += 1`、`frost_slow = min(0.65, frost_slow + 0.15)`

**实现要点**：
- 新增 `entities/frost_aura.py`：`FrostAuraManager`（参照 `orbital_blade.py` 结构），每 tick 遍历光环内敌人：`enemy.speed = enemy._base_speed * (1 - frost_slow)`（直接覆盖而非叠加乘算，避免多次乘法累积），并 `take_damage(frost_damage)`；离开光环的敌人恢复 `_base_speed`。
- 与冲锋怪交互（设计决策）：光环内**包括冲锋中的 Charger** 也减速——"冰克制冲锋"是爽点，保留（`[待 Playtest]` 若冲锋怪 dash 被完全废掉导致无威胁，则加"dash 期间免疫减速"）。
- 绘制：半透明冰蓝光环（`pygame.draw.circle` 程序化，风格同 nova 脉冲），随 tick 做脉冲收缩反馈。

### 1.3 武器二：圣焰喷射器 Flame Spitter（短程锥形喷吐 · 清群/持续输出向）

**机制描述**：每 0.28s 向最近敌人方向喷出一段锥形火焰（长 170px、半角 30°），锥内全部敌人受直接伤害并附加 2.0s 燃烧 DoT（每 0.5s 一跳）。火焰是"持续喷吐"型——现有 4 武器均无此动词（自动枪单点、新星脉冲、闪电链式、地雷放置）。

**角色联动**：
- **火枪手**：火焰每 tick **可暴击**（复用 `crit_chance/crit_multiplier`，参照 `chain_lightning.py` L84-86 的暴击判定）→ 火枪手 +10% 初始暴击与致命节奏自然收益，形成清晰联动。
- **游侠**：攻速流双通道输出（自动枪单点 + 火焰清群补刀），不依赖急速射击机制耦合，靠玩法搭配。
- **重装坦克**：火焰短程需要贴近 → 契合坦克站桩；补坦克偏低的 DPS。

**SKILL_DEFS 权威数值表（新增 `SKILL_DEFS["flame"]`）**

| 常量 | 值 | 单位 | 说明 |
|------|-----|------|------|
| FLAME_BASE_INTERVAL | 0.28 | s | 喷吐间隔 |
| FLAME_INTERVAL_REDUCTION | 0.02 | s/层 | |
| FLAME_MIN_INTERVAL | 0.18 | s | 5 层达下限（与急速射击下限一致） |
| FLAME_BASE_DAMAGE | 2 | 伤害/tick | 直接伤害，可暴击 |
| FLAME_DAMAGE_PER_STACK | 0.6 | 伤害/层 | |
| FLAME_BURN_DAMAGE | 1 | 伤害/燃烧tick | 燃烧不可暴击 |
| FLAME_BURN_DURATION | 2.0 | s | 燃烧总时长（4 跳） |
| FLAME_BURN_TICK | 0.5 | s | 燃烧 tick 间隔 |
| FLAME_CONE_LENGTH | 170 | px | |
| FLAME_CONE_HALF_ANGLE | 30 | 度 | 全锥角 60° |

**首取 DPS 推导**：直接 2/0.28s ≈ **7.1 + 燃烧 4（2s 内）= ~11 DPS（锥内每目标）**。对照闪电首取 9.7——火焰略高但代价是**短程锥形必须贴近**（闪电 240px 自动链），定价合理（`[待 Playtest]` 若火焰清群过强，`FLAME_BASE_DAMAGE` 2→1.5 或半角 30°→25°）。

**stats 键**（进 `state.py get_default_stats`）：
```python
"has_flame": 0, "flame_interval": 0.28, "flame_damage": 2, "flame_burn": 1,
```

**apply_skill 分支**（key `has_flame`）：
- 首次：`flame_interval=0.28 / flame_damage=2 / flame_burn=1`
- 重复：`flame_interval = max(0.18, flame_interval - 0.02)`、`flame_damage += 0.6`

**实现要点**：
- 新增 `entities/flame_spitter.py`：`FlameSpitterManager`（参照 `chain_lightning.py` 结构）。
- 命中判定：以玩家为顶点、最近敌人方向为中心轴，对每个敌人计算 `dist ≤ 170` 且 `夹角 ≤ 30°`（点积法），命中即直接伤害 + `enemy.apply_dot(2.0, 0.5, flame_burn)`（复用现有 DoT 机制）。
- 暴击：`random.random() < crit_chance` → `dmg *= crit_multiplier`（与闪电一致）。
- 绘制：程序化火焰粒子（扇形内短橙色线条 + 抖动，参照 `_Spark`），喷吐时轻微震屏（`camera.shake(0.05, 2)`）。

### 1.4 技能池集成方式（与现有 14 技能池机制完全兼容）

| 层 | 改动 | 文件 |
|----|------|------|
| 定义 | `SKILL_POOL` 追加 2 条（`has_frost` / `has_flame`，含 desc 与全部成长字段） | skills.py |
| 应用 | `apply_skill` 增加 2 个分支（见 1.2/1.3） | skills.py |
| 描述 | `get_skill_effect_desc` / `get_skill_detail_desc` 各增加 2 个分支（显示当前/下次效果） | skills.py |
| 默认值 | `get_default_stats` 增加 8 个键 | game/state.py |
| 运行时 | `_update_weapons` 增加 2 个分支（`if stats.get("has_frost")...` / `if stats.get("has_flame")...`） | game/normal_game.py + game/test_game.py（若 R6 未合并则双份同步） |
| 可用性 | 无上限类技能，`_skill_available` 无需改（始终可选取，可无限叠层——与闪电/地雷一致） | skills.py |

### 1.5 验收标准（怎么算做完）

- [ ] `SKILL_POOL` 长度 16；升级三选一仍保证 3 个不重复（`get_random_skills` 回归）。
- [ ] 选取凛冬之环 1/3 次：光环半径 100/124、伤害 2/4、减速 20%/50% 与权威表一致（调试面板可验证）。
- [ ] 选取圣焰喷射器 1/5 次：间隔 0.28/0.18、伤害 2/4.4 与权威表一致；第 5 次后间隔封底不再降。
- [ ] 凛冬之环：光环内敌人减速生效（进入前 vs 进入后 `enemy.speed` 可测）、离开恢复；tick 伤害正确。
- [ ] 圣焰喷射器：仅锥内敌人受伤（锥外不受伤）；燃烧 DoT 生效（敌人 2s 内 4 跳）；火焰暴击触发（伤害数字放大 + 暴击色）。
- [ ] 回归：暗影新星/连锁闪电/剧毒地雷行为不回归；smoke test 全绿。
- [ ] `[待 Playtest]` 新武器 pick 率进入"选择日志"统计；确认火焰/光环未取代闪电成为新必选（pick 率 ≤ 45%）。

---

## 2. 新敌人 ×2（5 敌种 → 7 敌种，不含 Boss）

### 2.1 解锁时间线设计（对齐 R4 档位 34s/档、17 档）

`[代码事实]` 现敌种解锁：basic=0（0s）、charger=1（34s）、ranger=2（68s）、exploder=3（102s）、精英=90s 时间判定。

`[推导]` 136s（tier4，旧平台期起点）到 240s（Boss2）之间是当前**敌种最单一**的窗口——只有前 4 种的数量变化，无新威胁模式。新敌种应填这里，且不与 Boss 战节奏冲突。

| 新敌种 | 解锁 tier | 解锁时间 | 落点 |
|--------|-----------|----------|------|
| 怨灵 Wraith | 4 | 136s | 旧平台期起点 = 新威胁登场点 |
| 唤魔师 Warlock | 6 | 204s | Boss1(120s) 击杀后 → Boss2(240s) 前 |

### 2.2 新敌人一：怨灵 Wraith（闪现逼近 · 相位型）

**专属行为（非数值换皮）**：不直线追逐，而是**周期性向玩家闪现**——每 1.2s 朝玩家方向瞬移 150–220px，闪现前 0.4s 在落点生成淡紫残影提示（可被预判击杀），落地后停顿 0.5s 再行动；非闪现期以低速（60px/s）飘向玩家。制造"必须保持移动"的间歇性压力，契合暗影庭院（图 2）主题。

**数值表（settings.py 新增常量块）**

| 常量 | 值 | 单位 | 说明 |
|------|-----|------|------|
| WRATH_SPEED | 60 | px/s | 非闪现期飘移速度 |
| WRATH_HP | 3 | HP | 基础（+tier×HP_BONUS_PER_TIER） |
| WRATH_BLINK_INTERVAL | 1.2 | s | 闪现间隔 |
| WRATH_BLINK_DIST_MIN / MAX | 150 / 220 | px | 闪现距离 |
| WRATH_TELEGRAPH | 0.4 | s | 落点残影提示期（提示期内为实体，可被打） |
| WRATH_LAND_PAUSE | 0.5 | s | 落地停顿 |
| WRATH_SIZE | 30 | px | 渲染尺寸 |
| WRATH_COLOR | (160, 140, 255) | — | 青紫幽魂 |

**交互规则**：
- 残影提示期 = 实体期（0.4s 内可被子弹命中并击杀）——预判打提示位是高手爽点，无虚影无敌机制（避免 auto-aim 游戏"打空"挫败感）。
- 接触伤害 = 1 + damage_bonus（普通怪公式）。
- Boss 战期间**允许**刷怨灵（其行为独立不召唤，不会叠加召唤压力）。

### 2.3 新敌人二：唤魔师 Warlock（召唤 · 法师型）

**专属行为（非数值换皮）**：**站桩施法者**，与玩家保持 240px 距离（过近则后退），每 2.5s 召唤 1 只基础小怪（tier0 弱化版），每 5s 释放一颗**慢速追踪弹**（缓速弯曲飞向玩家当前位置）。核心差异化：**普通怪里第一个召唤者**——击杀它让全场小怪失去"主心骨"，形成"先杀召唤师"的目标优先级决策（Boss 战防卡关增援已用同类思路，R4 §2.4）。

**数值表（settings.py 新增常量块）**

| 常量 | 值 | 单位 | 说明 |
|------|-----|------|------|
| WARLOCK_SPEED | 85 | px/s | 移动速度 |
| WARLOCK_HP | 2 | HP | 脆皮（+tier×HP_BONUS_PER_TIER） |
| WARLOCK_KEEP_DIST | 240 | px | 与玩家保持距离（比 ranger 的 320 更近，但只退不进） |
| WARLOCK_SUMMON_INTERVAL | 2.5 | s | 召唤间隔 |
| WARLOCK_SUMMON_COUNT | 1 | 只 | 每波召唤数 |
| WARLOCK_ORB_INTERVAL | 5.0 | s | 追踪弹间隔 |
| WARLOCK_ORB_SPEED | 140 | px/s | 慢速追踪（ranger 弹 180 直线） |
| WARLOCK_ORB_DAMAGE | 1+bonus | 伤害 | 追踪弹伤害（低，威胁在"必须躲"） |
| WARLOCK_SIZE | 30 | px | 渲染尺寸 |
| WARLOCK_COLOR | (200, 80, 60) | — | 暗红斗篷 |

**主从绑定（设计决策，实现小）**：Warlock 记录 `minion_ids`；死亡时其存活仆从 2s 内消散（无奖励清除，同 R4 Boss 清场规则——避免"白送经验"破坏节奏）。
**Boss 战期间不刷 Warlock**（召唤 + Boss 召唤双重压力过载，与"Boss 战不刷精英"同一精神，R4 §2.4）。
**召唤物规格**：tier0 基础怪（HP1/伤 1），与 Boss 召唤一致，防滚雪球。

### 2.4 刷怪权重与实现（normal_game._spawn_enemy 扩展）

```python
enemy_types = ["basic", "charger", "ranger", "exploder", "wraith", "warlock"]
enemy_unlock = {"basic": 0, "charger": 1, "ranger": 2, "exploder": 3,
                "wraith": 4, "warlock": 6}
enemy_weights = {"basic": 1.0, "charger": 0.4, "ranger": 0.35, "exploder": 0.2,
                 "wraith": 0.25, "warlock": 0.18}
# Boss 战期间：available 过滤掉 warlock（防召唤过载）；wraith 保留
```

**实现要点**：
- `entities/enemy_types.py` 新增 `Wraith(Enemy)` / `Warlock(Enemy)`，构造签名与 Charger/Ranger 一致（`hp/damage` 覆盖），各自重写 `update(dt, player_rect)`。
- 追踪弹：复用 `BossProjectile`（`entities/boss.py` 已有 `self.homing = False` 字段，启用 homing 即弯曲追踪；或新增轻量 `HomingOrb`，二选一由工程定，成本同级）。
- **非 Boss 事件钩子（小扩展）**：normal_game 敌人生成后，在敌人更新循环里 drain 非 Boss 敌人的事件（召唤/消散标记）：`for ev in enemy.drain_events(): self._process_enemy_event(ev)`。约 10 行，替代"敌人直接访问游戏对象"的耦合方案。
- Warlock 死亡消散：`_kill_enemy` 增加 `if hasattr(enemy, "on_death"): enemy.on_death(self)` 钩子（Warlock 在 on_death 里标记 minion_ids 无奖励清除）。

### 2.5 sprite 规格需求（供林绘澄）

| 资产 | 源网格 | 渲染 | 帧数 | 视觉要求 |
|------|--------|------|------|----------|
| wraith.png | 48×16（3×16²） | 30×30 | 3 帧 | 半透明幽魂、飘动衣袂、青紫冷色调、浓黑描边 2px；帧 2 为"显形张牙"极点 |
| warlock.png | 48×16 | 30×30 | 3 帧 | 披斗篷法师、持杖、暗红+暗金、兜帽内两点亮光；帧 2 为"举杖施法"极点 |

> 素材路径约定：`assets/sprites/wraith.png` / `warlock.png`，loader 自动按"宽÷3"切 3 帧（`[代码事实]` art-bible §3.1）。

### 2.6 验收标准（怎么算做完）

- [ ] 136s 后怨灵出现；行为正确：闪现 → 0.4s 落点残影 → 落地停顿 → 再闪现；残影期可被命中击杀。
- [ ] 204s 后唤魔师出现；行为正确：保持 240px、每 2.5s 召唤 1 只 tier0 基础怪、每 5s 放追踪弹。
- [ ] 主从绑定：Warlock 死亡后其仆从 2s 内消散且**不触发**经验/掉落/复苏之风。
- [ ] Boss 战期间不刷 Warlock；Wraith 正常刷新。
- [ ] 追踪弹弯曲追踪玩家；命中伤害 1+bonus。
- [ ] 难度模拟脚本（`tools/difficulty_sim.py`）确认新敌种在时间线解锁点出现，不破坏 R4 密度曲线。
- [ ] `[待 Playtest]` 3 局实机：136–240s 窗口不再"敌种单一"，怨灵/唤魔师出场带来可感知的威胁模式变化（问卷 ≥4/5）。

---

## 3. meta MVP：每日挑战 + 本地日榜（已拍板暂缓 · 设计保留）

> ⚠️ **拍板结果（2026-08-01）**：本批**暂缓**——每日挑战/本地日榜本批**不做**：不扩展存档 schema、不加主菜单入口、不加结算写入、不涉及任何代码改动。
> 以下 §3.1–3.5 设计**完整保留**，作为后续立项时的直接规格源；届时按本节落地即可，无需重新设计。D6（跨日清零语义）已按推荐值冻结（§5.4）。

### 3.1 方案对比与选择

| 方案 | 工程成本 | 单人离线 | 留存价值 | 存档兼容 | 结论 |
|------|---------|----------|----------|----------|------|
| A 每日挑战 | 低（种子 + 入口 + 记录） | ✅ | 高（每日回访钩子） | ✅ 低扩展 | **核心** |
| B 在线排行榜 | 中–高（需后端） | ❌ | 中（依赖网络） | 复杂 | **排除**（违反"单人离线可玩"硬要求） |
| C 解锁树 | 高（多内容 + UI + 数据） | ✅ | 中（一次性） | ✅ 成本大 | **延后**（R5 角色解锁已是解锁树第一层；新武器/新敌人已通过技能池/时间线落地，无需再绑 meta） |

**推荐：A + 本地日榜（最小组合）**——每日固定种子制造"今天这一局"的仪式感与回访动机；本地日榜记录当日 Top5，纯离线自我比较。**不引入在线排行榜、不做奖励/成就**（防进度系统膨胀，MVP 边界清晰）。

### 3.2 每日种子（离线确定性）

```python
seed = int(hashlib.md5(date_str.encode()).hexdigest()[:8], 16)  # date_str = "2026-08-01"
```
- 进每日挑战局时 `random.seed(seed)` → 技能三选一 / 刷怪 / Boss 位置全部确定化：**同一天所有玩家玩同一局**，正是每日挑战的卖点。
- `[工程注意]` 退出挑战局后 `random.seed()`（系统熵）恢复随机，避免污染主菜单/普通局；普通模式不改（不 seed）。

### 3.3 存档 schema 扩展（souls_save.json，向后兼容）

在 R5 schema（`unlocks`/`meta`/`settings` 顶层块）旁新增顶层 `daily` 块：

```json
"daily": {
  "date": "2026-08-01",
  "seed": 12345678,
  "best_score": 0,
  "best_time": 0.0,
  "victory": false,
  "runs": 0,
  "top_scores": []
}
```
`top_scores` 元素：`{"score": 0, "time": 0.0, "victory": false, "character": "default", "ts": 0}`（MVP 存 Top5）。

- `systems/save_data.py`：`_default_data()` 增加 daily 块；`_merge_defaults()` 增加 daily 合并逻辑（旧档无此块按默认值，不报错）。
- 语义：进入每日挑战时检查 `daily.date != today` → 重置 daily 块（`runs` 归零、`top_scores` 清空；`best_*` 保留为"历史最佳"或清零由 UI 文案定，建议清零+文案"新的一天"）。
- 写入点：挑战局结算 `record_run_result` 旁新增 `record_daily_result(...)`（或并入 `_trigger_game_over` 的一处分流）。

### 3.4 MVP 范围（明确 IN / OUT）

**IN**：
- 主菜单新增"每日挑战"按钮（显示今日日期；当日已通关显示"✓ 已通关"）。
- 每日挑战局：seed 固定、结算写入 daily。
- 本地日榜：结算页显示"今日最佳 + 今日 Top5"。
- 存档 schema 扩展 + 向后兼容。

**OUT（明确不做，防膨胀）**：
- 在线排行榜 / 云同步 / 每日挑战奖励（里程碑/成就）。
- 解锁树 UI（角色解锁沿用 R5；武器/敌人解锁后续立项）。
- 多日期历史回看。

### 3.5 验收标准（怎么算做完）

- [ ] 同一天两次进入每日挑战：技能三选一序列、Boss 位置可复现（种子一致）；不同日期种子不同。
- [ ] 挑战结算写入 daily：`best_score / best_time / victory / runs` 正确；Top5 更新且只保留 5 条。
- [ ] 旧存档（无 `daily` 字段）读取不报错，`daily` 按默认初始化。
- [ ] 离线（断网）状态每日挑战完全可玩。
- [ ] 普通模式不受每日挑战 seed 影响（普通局随机正常）。
- [ ] 主菜单入口展示今日日期 + 通关状态。

---

## 4. R7 演出设计：Boss 压迫感强化（尸王 / 暗影巫师）

> 背景：`[代码事实]` review P1-5 与 art-bible 审计——`boss_corpse_king.png`（绿色小妖戴角，过可爱）与 `boss_shadow_mage.png`（头部小，压迫感不足）为两个"缺压迫感"的 Boss；`iron_colossus` / `void_lord` 已达标。本方案聚焦这两个 Boss，分 P0（工程可做，全复用现有系统）/ P1（需美术素材）。

### 4.1 P0（低工程 · 全复用现有 systems：juice / lighting / audio / camera / boss_hud）

**通用（两 Boss 共用）**

| # | 演出 | 具体做法 | 复用系统 / API |
|---|------|----------|----------------|
| U1 | 降临入场 | Boss 生成瞬间：全屏震动 + 白闪 + 长顿帧 + 粒子爆发 + Boss 位置主题色光源 | `camera.shake(0.4, 10)` / `effects.screen_flash((255,255,255),120)` / `effects.trigger_hitstop(0.12)` / 粒子（30 个主题色）/ `lighting.add_light(bx, by, 220, boss_color, 1.0)` |
| U2 | 降临音 | 新增"降临音"（audio 侧复用 boss_warning 变体或低频 sub 鼓） | `audio_manager`（新增 `play_boss_arrive()`，或临时复用 `play_boss_warning()`） |
| U3 | Boss 血条增强 | 血条加入阶段刻度（50%/30% 竖线）；血条底色按 Boss 主题色；<30% 红色脉动 | `ui/boss_hud.py draw_boss_hp_bar` 扩展（现有 reveal/ghost 动画保留） |
| U4 | 狂暴横幅 | Boss 进入狂暴（尸王 <50%）时血条下方弹出"尸王狂暴"横幅 + 音乐 duck | `boss_hud` + `audio_manager.duck(0.6, 1.2)` |

**尸王专属（召唤系 · 压迫感来自"越打越多"）**

| # | 演出 | 具体做法 |
|---|------|----------|
| C1 | 冲锋蓄力提示 | 冲锋前 0.3s 前摇：脚下黄圈收缩 + 抖动（复用 enemy 脚底光圈机制 + `camera.shake(0.15, 4)`）→ 让"冲锋"从偷袭变为可读威胁 |
| C2 | 狂暴（<50%）| 召唤波次 3→5；召唤物从"基础怪"升级为"基础+冲锋混合"（复用现有 summon 机制扩展）；触发 U4 横幅 |

**暗影巫师专属（位移系 · 压迫感来自"不确定性"）**

| # | 演出 | 具体做法 |
|---|------|----------|
| S1 | 传送落点提示 | 传送前 0.4s 在落点生成紫色残影 + 落点提示圈（复用 `AreaEffect` 绘制风格 + `lighting.add_light(紫光)`）；传送瞬间小震屏 |
| S2 | 弹幕尾迹 | 暗影弹幕加紫色粒子尾迹（复用 `effects.add_sparks`，每帧少量，低开销） |
| S3 | 镜像标记（可选） | 传送升级为"3 选 1 落点"（2 个幻影 + 1 真身，落点提示后真身出现）——若工程余量允许；否则 S1 已达标 |

### 4.2 P1（需美术 · sprite 重绘规格，供林绘澄直接排期）

**通用约束（`[代码事实]` art-bible §3，所有新/改 sprite 必须遵守）**：
- 3 帧横向 sprite sheet，loader 按"宽÷3"切帧（`effects/asset_loader.py` `fw = img.get_width() // 3`）；帧 1 与帧 3 相同或镜像（乒乓式），帧 2 为"动作极点"。
- 所有世界实体外缘预留 1–2px 透明外缘 → 应用 2px 浓黑描边 `OUTLINE_COLOR=(18,14,26)`；Boss 可特权加粗至 3px。
- Boss 源网格 288×96（3×96²）；小怪源网格 48×16（3×16²）。

**A. boss_corpse_king.png（尸王重绘）**

| 维度 | 规格 |
|------|------|
| 源网格 / 渲染 | 288×96（3 帧 × 96²）/ 渲染 80×80 → **96×96（压迫感放大）**，body 占比 ≥90% 画布 |
| 构图 | 正面 3/4 视角、重心下沉（巨物感）；残破铠甲 + 腐肉堆叠 + 单侧高耸肩甲；粗犷骨角（保留双角但去可爱化）；身周 2–4 只小尸蝇/腐肉碎片点缀 |
| 配色 | 主调尸绿加深（保留主题 `(40,80,20)`）；腐肉暗红点缀 `(120,40,30)`；眼睛两点死白 `(240,240,230)`；描边 3px |
| 帧要求 | 帧1/帧3：站立呼吸（胸甲起伏）；帧2：**张口咆哮极点**（下颚大开 + 尸绿唾液线 + 身体前倾 2–3px） |
| 负面清单 | ❌ 小妖/可爱感（圆头大眼）；❌ 对称呆板；❌ 单色平涂无质感 |

**B. boss_shadow_mage.png（暗影巫师重绘）**

| 维度 | 规格 |
|------|------|
| 源网格 / 渲染 | 288×96（3 帧 × 96²）/ 渲染 60×60 → **70×70**；头部占比从"偏小"改为"兜帽占 40% 画布高" |
| 构图 | 斗篷大张（横向张力）、兜帽深陷、帽内两只发光眼（能量）；手举法杖，杖头悬浮暗紫能量球；脚底半透明能量流 |
| 配色 | 主调暗紫（保留主题 `(100,0,150)`）分层：深紫斗篷 `(40,0,60)` + 亮紫能量 `(170,60,230)`；眼睛 `(230,180,255)` 发光；描边 3px |
| 帧要求 | 帧1/帧3：漂浮呼吸（斗篷下摆起伏）；帧2：**举杖咏唱极点**（杖头上举 + 能量球放大 1.2× + 斗篷上扬） |
| 负面清单 | ❌ 头小身大失衡；❌ 法杖过细不可读；❌ 能量无发光感 |

**C. shadow.png（暗影巫师召唤怪专属，修复 art-bible 缺口 #23）**

| 维度 | 规格 |
|------|------|
| 源网格 / 渲染 | 48×16（3 帧 × 16²）/ 渲染 28×28（与普通怪同级，靠视觉叙事区分） |
| 构图 | 紫色雾团：核心小球 + 3 条卷须（下端拖尾）；无脸或两点微光眼；半透明 80% |
| 配色 | 暗紫雾 `(90,30,120)` 为主，内芯亮紫 `(160,80,220)`；描边 2px |
| 帧要求 | 帧1/帧3：雾团收缩；帧2：**雾团膨胀极点**（卷须外张） |
| 区分度 | 形状完全不同于 enemy.png（雾团 vs 人形），一眼可辨为"召唤物" |

**D. voidling.png（虚空之主召唤怪专属，修复 art-bible 缺口 #23）**

| 维度 | 规格 |
|------|------|
| 源网格 / 渲染 | 48×16（3 帧 × 16²）/ 渲染 28×28 |
| 构图 | 带触须的紫黑球体：核心 10px 球 + 4–6 根弯曲触须（对称错落）；核心内两点青色光眼 `(120,255,255)`；边缘紫色辉光 |
| 配色 | 主体紫黑 `(60,0,80)` + 触须亮紫 `(170,60,230)` + 眼青 `(120,255,255)`；描边 2px |
| 帧要求 | 帧1/帧3：触须缓慢摆动；帧2：**触须猛烈外张极点** |
| 区分度 | 触须球体 vs 人形，一眼可辨为"虚空造物" |

**E. P1 美术侧验收**
- [ ] 4 张 sprite（boss_corpse_king / boss_shadow_mage / shadow / voidling）入库 `assets/sprites/`，loader 切帧正常（宽÷3）。
- [ ] 视觉压迫感问卷：尸王/暗影巫师 ≥4/5；召唤怪与普通怪一眼可辨。

### 4.3 复用系统映射表（P0 全部可复用，无新增引擎依赖）

| 系统 | 现有 API | R7 复用点 |
|------|----------|-----------|
| effects/juice.py | `trigger_hitstop` / `screen_flash` / `add_death_ghost` / `add_sparks` | U1 顿帧+闪光、C1 蓄力抖动、S2 弹幕尾迹 |
| systems/lighting.py | `add_light(wx, wy, radius, color, intensity)` | U1 Boss 主题光源、S1 传送落点紫光 |
| systems/audio_manager.py | `play_boss_warning` / `play_boss_death` / `duck` | U2 降临音、U4 狂暴 duck |
| systems/camera.py | `shake(duration, magnitude)` | U1 入场震动、C1 冲锋震动 |
| ui/boss_hud.py | `draw_boss_hp_bar` | U3 阶段刻度/主题色/低血脉动、U4 横幅 |
| entities/boss.py | `AreaEffect` / `BossProjectile` / summon 机制 | C2 召唤波扩展、S1 落点提示圈、S3 幻影标记 |

### 4.4 验收标准（怎么算做完）

- [ ] 尸王/暗影巫师入场：震动 + 白闪 + 顿帧 + Boss 主题光源全部触发（肉眼 + 调试日志可验）。
- [ ] Boss 血条：阶段刻度线（50%/30%）显示；<30% 红色脉动。
- [ ] 尸王 <50% 狂暴：召唤 3→5、混合召唤、狂暴横幅 + 音乐 duck。
- [ ] 暗影巫师传送：0.4s 落点提示 + 紫色残影；弹幕有尾迹粒子。
- [ ] 全部复用现有 systems，无新增引擎/依赖；smoke test 全绿。
- [ ] P1（需美术）：4 张 sprite（boss_corpse_king / boss_shadow_mage / shadow / voidling）入库 `assets/sprites/`，loader 按宽÷3 切帧正常；视觉压迫感问卷 ≥4/5、召唤怪与普通怪一眼可辨。

---

## 5. 依赖与排序（最终实施版）

### 5.1 依赖 R6 重构结果（engineering-lead cheng-jiyan 并行中）

R6 = normal_game.py 与 test_game.py 双份合并（review P1-5 工程债）。以下改动**若 R6 未完成则需双份同步，成本 ×2**，建议排在 R6 合入之后：

| 改动 | 位置 |
|------|------|
| 新武器运行时钩子（`_update_weapons` 2 分支） | game/normal_game.py + test_game.py |
| 新敌种生成（`_spawn_enemy` 扩展 + 非 Boss 事件钩子 + `_kill_enemy` on_death 钩子） | 同上 |
| R7 入场/狂暴/传送演出（boss 生成段、`_process_boss_attacks`） | game/normal_game.py + test_game.py + entities/boss.py |

> meta（每日挑战）已拍板暂缓，**不进入任何依赖链**。

### 5.2 可独立（不依赖 R6，可立即做）

| 改动 | 位置 | 说明 |
|------|------|------|
| `SKILL_DEFS` 新增 `frost` / `flame` + 敌人常量块 | settings.py | 纯数据，无依赖 |
| 技能池 2 条 + apply_skill / desc 分支 | skills.py | 单份模块，不受 R6 影响 |
| stats 默认键 8 个 | game/state.py | 单份 |
| 新武器管理器 FrostAuraManager / FlameSpitterManager | entities/frost_aura.py / flame_spitter.py | 新文件，无依赖 |
| 新敌种 Wraith / Warlock 类 | entities/enemy_types.py | 单份 |
| Boss 机制扩展（C1/C2/S1/S2/S3、狂暴阈值） | entities/boss.py | 单份 |
| Boss 血条增强（U3/U4） | ui/boss_hud.py | 单份 |
| R7 P1 sprite 重绘 + 新敌种 sprite | assets/sprites/ | 美术线，与工程并行 |

### 5.3 排序建议（最终实施版）

```
批次 0（数据，可立即启动）: settings.py —— SKILL_DEFS 新增 frost/flame 权威表 + 怨灵/唤魔师常量块
批次 1（单份模块，与批次 0 并行）: skills.py 新技能分支 / state.py 新键 /
        新武器管理器（entities/frost_aura.py + flame_spitter.py）/
        新敌种 class（entities/enemy_types.py）/ boss.py 机制扩展 / ui/boss_hud.py 增强 /
        R7 P1 sprite（美术线并行：尸王/暗影巫师/shadow/voidling + wraith/warlock）
批次 2（依赖 R6 合入，engineering-lead）: game/normal_game.py（+test_game.py）运行时钩子：
        _update_weapons 2 分支 / _spawn_enemy 扩展 + 非 Boss 事件钩子 / _kill_enemy on_death /
        R7 入场/狂暴/传送演出
批次 3（验收）: 难度模拟脚本扩展 + 选择日志 + smoke test + 2 轮 Playtest（严守真）
```

### 5.4 拍板记录（2026-08-01 定稿）

| # | 决策点 | 拍板结果 |
|---|--------|----------|
| D1 | 新武器选型 | 凛冬之环 + 圣焰喷射器 **两个都上**（技能池 14→16，SKILL_DEFS 权威表保留） |
| D2 | 新敌人选型 | 怨灵 + 唤魔师 **两个都上**（tier4/136s + tier6/204s 解锁线保留） |
| D3 | meta MVP | **暂缓**（§3 设计保留，待后续立项；本批不扩存档、不做入口） |
| D4 | R7 范围 | **P0 + P1 全做**（P1 sprite 规格见 §4.2，供林绘澄直接排期） |
| D5 | 火焰 DPS | 首取 ~11 DPS **保留**，标注 `[待 Playtest]` 校准（降档参数见 §1.3） |
| D6 | 每日跨日清零 | 按推荐值冻结（暂缓，随 D3 一并冻结） |

---

## 附录 A：settings.py 新增键清单（实现用）

```python
# ---- 新武器（§1，SKILL_DEFS 新增两块）----
SKILL_DEFS["frost"] = {...}   # 见 §1.2 表
SKILL_DEFS["flame"] = {...}   # 见 §1.3 表

# ---- 新敌人（§2）----
WRATH_SPEED / WRATH_HP / WRATH_BLINK_INTERVAL / WRATH_BLINK_DIST_MIN / WRATH_BLINK_DIST_MAX /
WRATH_TELEGRAPH / WRATH_LAND_PAUSE / WRATH_SIZE / WRATH_COLOR
WARLOCK_SPEED / WARLOCK_HP / WARLOCK_KEEP_DIST / WARLOCK_SUMMON_INTERVAL /
WARLOCK_SUMMON_COUNT / WARLOCK_ORB_INTERVAL / WARLOCK_ORB_SPEED / WARLOCK_ORB_DAMAGE /
WARLOCK_SIZE / WARLOCK_COLOR

# meta 每日挑战常量（§3 已拍板暂缓，不进入本批 settings；设计保留于 §3 文档内）
```

## 附录 B：涉及文件索引（实现影响面）

| 文件 | 本包影响 |
|------|----------|
| settings.py | SKILL_DEFS 新增 2 块 + 敌人常量块 |
| skills.py | SKILL_POOL 16 条 + apply_skill/desc 各 2 分支 |
| game/state.py | get_default_stats 新键 8 个 |
| entities/frost_aura.py（新）/ flame_spitter.py（新） | 新武器管理器 |
| entities/enemy_types.py | Wraith / Warlock 类 |
| entities/boss.py | C1/C2/S1/S2/S3 机制、狂暴阈值 |
| game/normal_game.py + test_game.py | 运行时钩子（依赖 R6） |
| ui/boss_hud.py | 阶段刻度/主题色/低血脉动/横幅 |
| assets/sprites/ | wraith.png / warlock.png + R7 P1 重绘（boss_corpse_king / boss_shadow_mage / shadow / voidling） |
| tools/difficulty_sim.py | 新敌种解锁点校验 |
| README.md | 武器表/敌人表同步 |

## 附录 C：公式速查

```
凛冬之环：DPS = FROST_BASE_DAMAGE / FROST_TICK_INTERVAL = 4（半径内全场）
          减速 N 层 = min(0.65, 0.20 + 0.15×(N−1))
圣焰喷射器：DPS(锥内单目标) ≈ FLAME_BASE_DAMAGE/FLAME_BASE_INTERVAL + FLAME_BURN_DAMAGE×4
          = 2/0.28 + 4 ≈ 11
怨灵闪现距离 = uniform(WRATH_BLINK_DIST_MIN, WRATH_BLINK_DIST_MAX)
唤魔师召唤 = tier0 基础怪；追踪弹 = BossProjectile(homing=True)
每日种子 = int(hashlib.md5(date_str).hexdigest()[:8], 16)
```

---

*本文档为设计规格，不修改任何代码。本定稿将作为第二批实现的唯一规格源。批准后由 team-lead 分派：批次0/1 数据与单份模块 → 程基岩（可立即）；批次2 normal_game 钩子 → 程基岩（R6 合入后）；sprite（R7 P1 + 新敌种）→ 林绘澄；批次3 验收 → 严守真。*
