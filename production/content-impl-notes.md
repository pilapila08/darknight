# C02 内容扩充实现说明（DN-ENG-C02）

- 负责人：程基岩（engineering-lead）
- 规格源：`design/gdd/content-pack-v2.md`（§1 新武器 / §2 新敌人 / §4 R7）/ `design/art/fx-spec-v1.md`
- 分支：dev/1.0-hardening（依赖 R6 BaseGame 已合入）
- 约束遵守：meta（每日挑战/日榜）暂缓不实现；不 commit/push

---

## 1. 交付项总览

| 批次 | 交付 | 文件 | 状态 |
|---|---|---|---|
| 0 | 数据 | `settings.py`：SKILL_DEFS["frost"]/["flame"]、Wraith/Warlock 常量、R7 常量 | ✅ |
| 1 | 技能 | `skills.py` 池 14→16 + apply_skill/desc 分支；`game/state.py` +8 键 | ✅ |
| 1 | 新武器 | `entities/frost_aura.py`（FrostAuraManager）、`entities/flame_spitter.py`（FlameSpitterManager） | ✅ |
| 1 | 新敌人 | `entities/enemy_types.py`：Wraith / Warlock / HomingOrb | ✅ |
| 1 | R7 Boss | `entities/boss.py`：尸王 C1 冲锋前摇 + C2 狂暴、暗影巫师 S1 传送提示 + S2 弹幕尾迹 | ✅ |
| 1 | R7 血条 | `ui/boss_hud.py`：U3 阶段刻度/主题色/低血脉动 + U4 狂暴横幅 | ✅ |
| 1 | FX 接入 | `assets/effects/`（5 张贴图）+ `effects/fx_textures.py` 加载器 + 4 处 draw 接入（explosion/nova/lightning/muzzle） | ✅ |
| 2 | BaseGame 钩子 | `game/base_game.py`（见 §2）；`game/normal_game.py`（R7 覆写）；`game/test_game.py`（HP 键） | ✅ |
| 3 | 验收 | `tools/verify_content.py`（21 条断言全绿）+ 全量回归 | ✅ |

## 2. BaseGame 单点改动（R6 后 single-point）

全部新运行时逻辑落在 `BaseGame`，Normal/Test 仅覆写钩子：

- `_init_game`：新增 `frost_mgr` / `flame_mgr`
- `_update_weapons`：`has_frost` / `has_flame` 两个分支（独立伤害键，不读 bullet_damage/fire_interval）
- `_spawn_enemy`：敌种 5→7（wraith tier4 / warlock tier6），Boss 战过滤 warlock（保留 wraith）
- 敌人更新循环：drain 非 Boss 事件（`_process_enemy_event`：唤魔师召唤/追踪弹）+ `_disperse_at` 主从消散（无奖励）
- `_kill_enemy`：`hasattr(enemy, "on_death")` 钩子（唤魔师死亡 → 仆从标记消散）
- `_process_boss_attacks`：新增 `telegraph_shake` / `teleport_telegraph_shake` / `teleport_land_shake` / `boss_enrage` 事件 + projectile `trail_color`
- `_update_boss_warning`：Boss 生成后调用 `_on_boss_arrive(boss)`
- 渲染：`frost_mgr.draw` / `flame_mgr.draw`
- 新增策略钩子：`_on_boss_arrive`（基类：震动+粒子；Normal：+白闪/顿帧/主题光源）、`_add_projectile_trail`（Normal：火花）、`_on_boss_enrage`（Normal：红闪）

## 3. 关键实现决策

1. **新武器独立伤害键**（content-pack-v2.md §1.1 红线）：frost/flame 均不读 `bullet_damage`/`fire_interval`，火力/急速不放大新武器。
2. **火焰间隔公式**：`interval = max(0.18, 0.28 − 0.02×(层数−1))`。第 5 次选取 = 0.20、第 6 次触底 0.18（权威表 "5 层达下限" 解读为 6 次选取触底；公式以 SKILL_DEFS 为准，验收脚本按公式断言）。
3. **唤魔师主从绑定**：游戏层在 `_process_enemy_event("summon")` 给仆从打 `_master_id`；唤魔师 `on_death(game)` 扫描 `_master_id == id(self)` 的存活仆从，标记 `_disperse_at = elapsed+2.0`；`_update` 每帧检查到期 → `enemy.kill()`（无经验/掉落/复苏）。
4. **追踪弹**：新增轻量 `HomingOrb(EnemyBullet)`（每帧重瞄准玩家，速度 WARLOCK_ORB_SPEED=140），走 enemy_bullets 通道（命中即伤玩家）；未改 `BossProjectile.update`（避免影响既有 Boss 弹）。
5. **FX 贴图回退**：`effects/fx_textures.py` 加载 assets/effects/ 下的 5 张主选贴图；缺失返回 None，各 draw 回退原程序化绘制 → 无素材也能运行（对打包/裁剪安全）。
6. **技能池 14→16**：这是 C02 设计包 §1.4/§1.5 的**明确要求**，故 `tools/verify_r3.py` / `verify_r5.py` 中硬编码 `len(SKILL_POOL) == 14` 的两处断言已更新为 16（预期验收更新，非回归）。
7. **R6 行为等价 harness 保持全绿**：其 boss 阶段仅覆盖 3s 预警窗口（120 帧 ≈ 2s < 3s），未触达新敌种生成/Boss 降临路径 → C02 新增行为不影响 R6 等价性结论（C02 新增路径由 verify_content.py 单独覆盖）。

## 4. 验证结果（全绿）

| 验证 | 命令 | 结果 |
|---|---|---|
| C02 内容验收 | `venv/Scripts/python.exe tools/verify_content.py` | `CONTENT_VERIFY_ALL_PASS`（21 条，写 tools/verify_content_out.txt） |
| 冒烟 | `venv/Scripts/python.exe _smoke_test.py` | `SMOKE_ALL_PASS` |
| R3 | `venv/Scripts/python.exe tools/verify_r3.py` | `VERIFY_ALL_PASS` |
| R5 | `venv/Scripts/python.exe tools/verify_r5.py` | `VERIFY_ALL_PASS` |
| R6 行为等价 | `venv/Scripts/python.exe tools/verify_r6_behavior_diff.py` | `BEHAVIOR_ALL_MATCH`（544 快照） |

## 5. 风险点 / 待 Playtest- `[待 Playtest]` 火焰 DPS（首取 ~11）与凛冬减速 0.15/层是否过强 → 降档参数见 content-pack-v2.md §1.2/§1.3。
- `[待 Playtest]` 怨灵 136–240s 窗口的威胁节奏；唤魔师“先杀召唤师”优先级是否成立。
- 新敌种/新武器未接入 TestGame 测试面板的类型列表（面板 UI 布局未扩展，Boss 战/auto_spawn 已可自然生成）。
- `design/art/ai-samples` 为源素材目录；运行时副本在 `assets/effects/`（打包需包含）。

## 6. 改动文件清单

新增：`entities/frost_aura.py`、`entities/flame_spitter.py`、`effects/fx_textures.py`、`assets/effects/*.png`（5 张）、`tools/verify_content.py`、`tools/verify_fix_bug001.py`、`production/content-impl-notes.md`
修改：`settings.py`、`skills.py`、`game/state.py`、`game/base_game.py`、`game/normal_game.py`、`game/test_game.py`、`entities/enemy_types.py`、`entities/boss.py`、`entities/explosion.py`、`effects/orbital_blade.py`、`effects/chain_lightning.py`、`effects/juice.py`、`ui/boss_hud.py`、`tools/verify_r3.py`（池 16 断言+标签）、`tools/verify_r5.py`（池 16 断言+标签）、`tools/smoke_content_extra.py`（SMK-24/28 游戏循环级断言恢复 + 新增 SMK-30）

---

## 7. BUG-001 修复（DN-ENG-FIX-BUG001）

### 根因
Boss 同时加入 `self.enemies` 与 `self.bosses` 两组：
- `_update` 旧 :381 `self.enemies.update(dt, player_rect)` 先驱动 `boss.update()`（attack_timer 到阈值触发 `_do_attacks` 并把 attack_timer 清零）→ 返回 attacks 列表 → **pygame Group.update 丢弃返回值**
- 随后 `_update_bosses` 再调 `boss.update()` → 计时器已清零 → attacks 空 → `_process_boss_attacks` 收不到
- 实测：CorpseKing 120 帧 0 条攻击、ShadowMage 120 帧仅 1 次（应约 48）

### 修复（方案 A，Boss 保留在 enemies 组）
```python
# _update 中替换 self.enemies.update(dt, self.player.rect)
for enemy in list(self.enemies):
    if not isinstance(enemy, Boss):
        enemy.update(dt, self.player.rect)
```
Boss 仅由 `_update_bosses` 驱动一次；enemies 组保留（子弹 groupcollide、武器管理器、陷阱均依赖它打 Boss，B 方案需动 8+ 处）。

### 验证（tools/verify_fix_bug001.py → tools/verify_out_fix_bug001.txt）
- CorpseKing 500 帧送达 **4** 条攻击（阈值 ≥3；修复前 0）✓
- ShadowMage 120 帧 **5** 条（修复前 1）、IronColossus 120 帧 **1**、VoidLord 120 帧 **3** ✓
- 绘制无重复（enemies 绘制排除 Boss、bosses 单独绘制）✓
- Boss 移动/动画/受击闪白正常 ✓
- `tools/smoke_content_extra.py` SMK-24（狂暴红闪经游戏循环送达）/SMK-28（弹幕尾迹经游戏循环送达）恢复游戏循环级断言 + 新增 SMK-30（四 Boss 攻击送达计数）→ SMOKE_CONTENT_EXTRA_ALL_PASS ✓
- 全量回归：_smoke_test / verify_content / verify_r3 / verify_r5 / verify_r6_behavior_diff 全绿 ✓
