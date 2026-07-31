# 暗夜求生 Darknight · Playtest 计划 v1 + 冒烟扩展 + 发布质量门

> 阶段：发布硬化期测试基线（与工程 P0 修复并行）
> 编制：严守真（quality-lead / QA）
> 版本基线：v3.8（2026-07-31）
> 输入：设计评审 v1（design-review-v1.md）、冲刺计划 v1.1（sprint-plan-v1.md）、`_smoke_test.py`、`game/normal_game.py`、`settings.py`
> 约定：`[代码事实]` 本次已用代码核对 / 实际跑测；`[假设]` 设计评审推导、需人工 Playtest 验证

---

## 0. 测试基线状态（本次实测）

| 项 | 结果 | 说明 |
|----|------|------|
| 现有冒烟测试 `_smoke_test.py` | ✅ **SMOKE_ALL_PASS（11/11 OK）** | 无窗口 SDL dummy driver 实测通过：effects/juice、lighting、camera、get_font、audio_manager、hud、skill_select、boss_hud、game_over、start_screen、normal_game 10 帧模拟 |
| 运行环境 | venv + pygame 2.6.1 | `./venv/Scripts/python.exe _smoke_test.py` 可复跑，exit 0 |

**P0 三处断裂代码事实复核（本次 grep/读码确认，供测试用例设计定位）：**

| P0 | 代码事实 | 定位 |
|----|---------|------|
| P0-A 胜利判定缺失 | `is_victory` 仅两处赋值：L62 初始 False、L799 死亡时 False；`_check_game_end()`（L791）只判 `player_hp <= 0`，**无 `elapsed_time >= 600` 分支** | normal_game.py |
| P0-B 死亡后 ESC 被吞 | `_handle_events()` game_over 分支（L126-137）只响应 SPACE / 重开按钮，ESC 事件落入 `continue` 被吞 | normal_game.py |
| P0-C 经验球死代码 | 全仓库 `orbs.add` 0 处；`XpOrb` 仅 import 未实例化；`_update_orbs()`（L740）遍历空组；`pickup_range`/`ORB_SPEED` 无效；README 首句文案过期 | normal_game.py / entities/xp_orb.py |

**关键数值锚点（settings.py 复核）：** 难度档 34s/档×4 档（136s 冻结）；刷怪封顶 tf=5（~150s）；Boss 时间轴 120/240/360/480s；5 张地图（Boss 击杀后切换）；XP 几何增长 14×1.15^n；升级免费 +1 上限 +1 血。

---

## 1. Playtest 计划（验证点清单）

### 1.1 核心循环验证（击杀 → 升级 → 变强 → 10 分钟胜利闭环）

| # | 验证点 | 验证方法 | 通过标准 |
|---|--------|---------|---------|
| C1 | 击杀 → 经验直给：击杀普通怪 +1 XP、精英 +3、Boss +20，经验条即时推进 | 自动化（冒烟扩展 SMK-17）；人工观察 HUD | 击杀后 `experience` 增量符合 1/3/20；HUD 经验条无跳变无回退 |
| C2 | 升级 → 三选一暂停：经验达标触发 `paused=True` + 3 张技能卡 | 自动化（SMK-17） | 升级瞬间游戏逻辑冻结；`chosen_skills` 长度 = 3；选择后恢复运行 |
| C3 | 变强闭环：选技能后属性生效（如火力增强提升 `bullet_damage`） | 自动化（SMK-17）；人工验证手感 | 选择技能后 stats 对应字段变化；玩家伤害提升肉眼可感 |
| C4 | **10 分钟胜利判定（P0-A 修复后）**：`elapsed_time >= 600` → `game_over=True` + `is_victory=True` + 胜利结算 | 自动化（SMK-12/13） | 600s 时进入结算态；`is_victory` 为 True；胜利文案与死亡文案可区分 |
| C5 | 胜利结算可退出：结算界面 ESC/按钮 → 返回主菜单（非关窗） | 自动化（SMK-14）；人工验证 | 结算后 `run()` 返回 True，主菜单可见，无残留状态 |
| C6 | 死亡 → 重开：SPACE/按钮 → `_restart()` 状态重置干净 | 自动化（SMK-15） | 重开后 level=1、score=0、elapsed_time=0、enemies/orbs/drops 清空 |

### 1.2 数值手感验证（刷怪密度 / 难度曲线 / Boss 时间轴）

| # | 验证点 | 验证方法 | 通过标准 |
|---|--------|---------|---------|
| N1 | 刷怪密度曲线：0s≈1.25 只/s → 30s≈1.65 → 60s≈2.11 → 90s≈2.63 → 120s≈3.20 → 150s 封顶≈3.83 | 自动化（公式单测，读 `SPAWN_INTERVAL`/`time_factor`）；人工体感 | 公式输出与 settings 推导一致；**人工**：前 60s 可走位喘息、90-150s 压力明显上升、150s 后不再更密 |
| N2 | 难度档位 34s/档：0/34/68/102/136s 时敌人 HP/伤 +0/+1/+2/+3/+4 | 自动化（读 `DIFFICULTY_INTERVAL`/`_get_current_enemy_stats`） | 边界时间（34s、68s…）档位跳变正确；136s 后冻结不再增长 |
| N3 | **平台期体感（设计评审假设 #8）**：2.5 分钟后难度是否"麻木/无双割草" | **人工 Playtest（核心）** | 至少 2/3 测试员反馈"136s 后仍有关注点"（新敌人/Boss/走位压力）；若 2/3 反馈麻木 → 触发 P1-1 难度曲线重设计 |
| N4 | Boss 时间轴触发：120/240/360/480s 准时预警 → 清场 → Boss 入场 | 自动化（SMK-18）；人工验证 | 各 Boss 在对应 `spawn_time` 触发预警；预警期间暂停刷怪；清场后 Boss 生成 |
| N5 | **Boss 击杀时长校准（设计评审假设 #9）**：记录各 Boss 从入场到击杀时长 | **人工 Playtest + DPS 日志** | 目标击杀时长 8–20s/只；若尸王 <3s（过脆）或虚空之主 >40s（过肉）→ 反推调整 HP（当前 120/600/2400/8000 存疑） |
| N6 | 升级节奏：全流程升级 25–35 级估算 vs 实际 | 人工 Playtest 记录 | 首升约 14 XP（≤20s 内）；中盘升级间隔不出现 >60s 空窗 |
| N7 | 技能选择分布（设计评审假设 #7 主导策略） | **人工 Playtest 记录** | 火力增强/增加弹量/急速射击三件套出现率 >60% 且无脑选 → 记录为平衡风险项，交 design-strategist 出平衡表 |

### 1.3 UX 验证（升级三选一 / Boss 战反馈 / 死亡-胜利结算）

| # | 验证点 | 验证方法 | 通过标准 |
|---|--------|---------|---------|
| U1 | 升级三选一可用性：`1/2/3` 键 + 鼠标双通道选择 | 自动化（SMK-17 覆盖状态）；人工 | 两通道均可选；选后卡片消失、游戏恢复；稀有度色条可辨识 |
| U2 | Boss 预警仪式：黑边滑入 + 呼吸边框 + 大字横幅 + 清场 | 人工 Playtest | 预警 ≥3s 可读；Boss 名/颜色与 Boss 匹配；清场不卡顿 |
| U3 | Boss 战反馈：血条出现、攻击有前摇可躲、受击震屏/顿帧 | 人工 Playtest | 攻击可读性：测试员能说出"如何躲"；Boss 击杀顿帧 0.25s + 白闪 + 大残影明显 |
| U4 | 虚空之主 gravity 攻击（设计评审 P0-4：`pass` 未实现） | 人工 + 代码复核 | **当前 FAIL（代码事实）**：修复后验证黑洞有牵引/伤害表现 |
| U5 | 死亡结算：滑入面板 + 数字滚动 + 新纪录高亮 | 自动化（SMK-13 覆盖渲染）；人工 | 结算信息完整（时间/分数/等级/最高分）；新纪录有区分 |
| U6 | **死亡后 ESC 返回主菜单（P0-B 修复后）** | 自动化（SMK-14）；人工 | 死亡结算界面按 ESC → 主菜单；不残留游戏状态 |
| U7 | 胜利结算（P0-A 修复后）：胜利文案/演出与死亡可区分 | 人工 Playtest | 测试员能明确感知"我赢了"；通关后情绪峰值 ≥ 死亡 |
| U8 | 调试信息外露检查：标题栏 DPS/击杀/时间、FPS HUD（设计评审 P1-6/P2-3） | 人工目检 | 发布版应隐藏或收入调试开关；当前为外露（记录为发布前清理项） |

---

## 2. 冒烟测试扩展用例设计（基于 P0 修复，只给设计不改代码）

> 目标：把现有 11 例扩到 16–19 例，全部无窗口可跑（SDL dummy driver），覆盖 P0-A/B/C 修复后主路径与回归。用例编号接续现有 SMK 体系（新增 SMK-12 起）。

| ID | 名称 | 前置 | 步骤（概要） | 预期断言 | 覆盖 |
|----|------|------|-------------|---------|------|
| SMK-12 | 胜利判定触发 | NormalGame 实例化 + `_init_game()` | 手动置 `game_state.elapsed_time = 600` → `_update(0.016)` | `game_state.game_over is True`；`is_victory is True`；无异常 | P0-A |
| SMK-13 | 胜利结算渲染 | 同上，置胜利态 | `_render()` 多帧；`draw_game_over_screen(..., is_victory=True)` | 渲染不抛异常；胜利分支被调用（可注入探针或对比 is_victory 真假两路径渲染） | P0-A / U5 |
| SMK-14 | 死亡后 ESC 返回主菜单 | 置 `game_over=True` | 向事件队列注入 `pygame.KEYDOWN(K_ESCAPE)` → `_handle_events()` | `running is False`（run() 将返回 True 给主菜单）且不崩溃 | P0-B |
| SMK-15 | 死亡后 SPACE 重开重置 | 置 `game_over=True` + 造入敌人/分数 | 注入 `K_SPACE` → `_handle_events()` | `_restart()` 后 level=1、score=0、elapsed_time=0、enemies/orbs/drops 空、game_over=False | P0-B / C6 |
| SMK-16 | 击杀直给经验（经验球清理后） | `_init_game()` | 造 1 个 Enemy 并置 hp=0 → `_kill_enemy()`；确认 `orbs` 组为空 | `experience` 增量 ∈ {1,3,20}（按敌种）；`len(orbs)==0`（确认死代码已清） | P0-C |
| SMK-17 | 升级 → 三选一 → 选择恢复 | `_init_game()` | 置 `experience` 达到 L2 阈值 → `_check_level_up()` → 注入 `K_1` 选卡 | `level==2`；`paused` 先 True 后 False；`chosen_skills` 先 3 后 None；`acquired_skills` +1；选后 `_update` 恢复推进 | C2 / C3 / U1 |
| SMK-18 | Boss 时间轴四连触发 | `_init_game()` | 依次置 `elapsed_time = 120/240/360/480` → `_update` | 各时间点触发 `boss_warning_active`；预警结束后 `bosses` 出现对应 Boss；`boss_defeated_count` 递增（击杀后） | N4 / Boss 时间轴 |
| SMK-19 | 全流程 10 分钟模拟（回归总闸） | `_init_game()` | 循环 `_update(0.016)` × 625 帧（≈10s 逻辑时间放大或直接置时）+ 每帧 `_render()`，中途触发升级/Boss | 无异常、无内存级失控；结束时态合法；可作为"修复后全量回归"入口 | 全 P0 回归 |

**实现建议（交 engineering-lead，不改动本轮）：**
- SMK-12~19 沿用现有 `check(name, fn)` 骨架与 `SDL_VIDEODRIVER=dummy`；对事件注入用 `pygame.event.post()`。
- SMK-19 需确认修复后的 `_check_game_end()` 胜利分支可被 `elapsed_time` 直接驱动（不依赖真实时钟）。
- 建议新增"断言计数"统计：每个用例至少 2 条 assert，防空跑。

---

## 3. 发布质量门清单（Steam 发售前必须全绿，可勾选）

> 与商业化技术清单 P0-A~F 对齐；质量门为建议性门控，最终放行由用户决定。

### A. 自动化门（CI / 冒烟）
- [ ] A1 现有冒烟 11 例全绿（本次基线已 PASS，保持）
- [ ] A2 冒烟扩展 SMK-12~19 全绿（P0 修复后新增用例）
- [ ] A3 `_smoke_test.py` 退出码 0（`SMOKE_ALL_PASS`），无 flaky（连续跑 3 次全绿）
- [ ] A4 无 `SyntaxError`/import 断裂（`python -m compileall` 全仓通过）
- [ ] A5 无窗口环境（dummy driver）可完整跑通全量冒烟（发布环境可复现）

### B. P0 玩法修复门（工程修复后逐项验证）
- [ ] B1 10 分钟胜利判定：600s 触发胜利结算，`is_victory=True`（SMK-12/13）
- [ ] B2 死亡/胜利后 ESC 返回主菜单（SMK-14）；SPACE 重开状态干净（SMK-15）
- [ ] B3 经验球死代码清理：`orbs` 不再创建/遍历；击杀直给经验不受影响（SMK-16）
- [ ] B4 击杀/升级反馈动效（方案 B 已拍板）已落地且冒烟覆盖
- [ ] B5 虚空之主 gravity 攻击已实现（当前 `pass`，需 design/eng 确认修复）

### C. 素材门（art）
- [ ] C1 精英怪 sprite 修复（原 8% 空白像素）
- [ ] C2 冲锋怪 sprite 修复（原 23% 错图）
- [ ] C3 5 敌种 + 4 Boss 在 5 张地图均有可见素材（无空白/错位）

### D. 技术硬化门（release/eng）
- [ ] D1 存档路径改 `%APPDATA%/Darknight/`，不写游戏目录
- [ ] D2 内置字体（思源黑体/Noto）随包，`assets/fonts/` 非空
- [ ] D3 版本号统一 1.0（标题/打包/商店一致）
- [ ] D4 杀软误报检查通过（PyInstaller 产物）
- [ ] D5 标题栏调试信息/FPS HUD 发布版隐藏或入调试开关

### E. 本地化门（Steam 硬门槛）
- [ ] E1 字符串抽取完成（~400 行硬编码中文 → i18n/strings.py）
- [ ] E2 英文 UI 全量覆盖（菜单/HUD/选卡/Boss 名/结算/商店文案）
- [ ] E3 中英切换不丢字/不溢出（Boss 名长串、结算数字）

### F. 人工 Playtest 签收门（本计划 1.1–1.3 验证点）
- [ ] F1 核心循环签收：C1~C6 全过（胜利闭环可玩通）
- [ ] F2 数值手感签收：N1~N3 至少 2/3 测试员无"平台期麻木"；N5 Boss 击杀时长进入 8–20s 校准带
- [ ] F3 UX 签收：U1~U7 全过；U4（虚空之主）修复后复验
- [ ] F4 新玩家首局体验：3 名未玩过者能在无指导前提下 10 分钟内理解"走位→击杀→升级→打 Boss"并至少到第 2 Boss

### G. 发布稳定性门
- [ ] G1 全流程 10 分钟模拟无崩溃/无异常（SMK-19）
- [ ] G2 中高密度（MAX_ENEMIES=150 上限附近）FPS ≥ 50（dummy 无法测，需真机人工）
- [ ] G3 存档读写幂等：反复读写不损坏、最高分正确

---

## 4. 自动化 vs 人工 Playtest 边界（明确标注）

### 可自动化（QA 可无窗口跑，本计划已覆盖或可脚本化）
- 状态机逻辑：胜利判定、ESC 返回、SPACE 重开、升级暂停/恢复、Boss 时间轴触发、击杀经验增量、掉落
- 数值公式：刷怪间隔曲线、难度档位边界、XP 曲线、技能叠加后 stats 变化
- 渲染路径调用：胜利/死亡/选卡/Boss 血条/HUD 各分支不抛异常
- 回归总闸：SMK-19 全流程模拟

### 需人工 Playtest（QA 无法运行窗口游戏，必须真人/真机）
- **手感类**：刷怪密度体感、难度曲线平台期感受、走位/闪避压力
- **Boss 战体验**：攻击可读性（能否说清"怎么躲"）、压迫感、击杀时长体感
- **决策体验**：升级三选一的决策趣味、主导策略是否导致"无脑选"
- **情绪峰值**：胜利时刻的满足感、死亡挫败感是否可接受
- **真机性能**：FPS 稳定性、全屏/窗口切换、真机音频
- **新玩家首局**：无指导可理解性（需 3 名未玩过者）

**执行建议**：P0 修复合入后跑一轮自动化门（A+B 全绿）→ 人工 Playtest 一轮（F 门，5 人：3 新 + 2 老）→ 修数值/Boss 后复跑 → 进入 Steam 发售 gate。

---

## 5. 交付物清单

| 交付物 | 路径 | 状态 |
|--------|------|------|
| Playtest 计划 v1（本文件） | `design/review/playtest-plan-v1.md` | ✅ 已产出 |
| 冒烟测试基线实测 | `_smoke_test.py`（未改动） | ✅ 11/11 PASS |
| 冒烟扩展用例设计（SMK-12~19） | 本文件 §2（设计，未写代码） | ✅ 待 engineering-lead 实现 |
| 发布质量门清单 | 本文件 §3（可勾选） | ✅ 已产出 |

**回传主理人摘要**：见 SendMessage。

---

*本计划为 v1，随 P0 修复合入、首轮 Playtest 数据滚动更新。*
