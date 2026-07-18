---
name: task-handoff
description: 任务交接协议：resume / 手动 checkpoint 的标准流程，含 handoff 瘦身原则。Use when 用户说 继续 XX / resume / checkpoint / 交接，或即将执行有风险需回退的操作。日常的 handoff 刷新由每日 close-out 顺带完成。
---

# Skill: 任务交接协议（Task Handoff Protocol）

## 与 close-out 的分工

- **日常刷新**：每日 `/close-out` 会顺带更新在途任务的 HANDOFF——你不需要为此手动跑本 skill
- **本 skill 出场的两个时机**：
  1. **Resume**：新 session 要继续某个任务
  2. **手动 checkpoint**：即将执行可能出错需要回退的操作，或对话中途要立即换 session

## 定位项目

Handoff 按项目域组织，存放在 `projects/<study>/handoffs/`。

1. 当前对话已在某项目上下文中 → 直接用该项目
2. 用户指定了项目名 → 按 STUDY.md 路由定位
3. 不确定 → 扫 `projects/*/handoffs/INDEX.md` 找匹配任务

## 创建新任务

1. 在 `projects/<study>/handoffs/` 下创建目录（snake_case）
2. 创建 `HANDOFF.md`，填写下方模板
3. 更新 `projects/<study>/handoffs/INDEX.md`

## HANDOFF.md 模板

```markdown
# Task: <任务名>
Updated: YYYY-MM-DD HH:MM

## Objective
一句话：最终要达成什么。

## Task-Critical Decisions
- 只记录仍然影响下一步执行的关键决策摘要
- 长期项目决策不放这里 → repo 或项目层的 docs/decisions.md

## Current Status
- [x] 已完成的步骤
- [ ] 🔵 当前进行中（卡点/进展）
- [ ] 待做的步骤

## Important Context
- 关键文件与作用（写具体路径 + ClassName.method()，不写"那个文件"）
- 已知坑和绕过方式
- 外部依赖（API、服务、数据）

## Open Questions
- 待确认事项 / 需要用户决策的问题
```

## 写交接的原则

- **写给下一个完全没有上下文的 AI**——不假设它知道任何之前的对话
- **只服务续工**——现在做到哪、下一步是什么、卡在哪；下一步必须能直接动手
- **保持短**——设计推理、历史决策、稳定机制说明都不属于这里：
  机制现状 → repo 的 `docs/design.md`；决策 → 对应层的 `docs/decisions.md`。
  这些分流由每日 close-out 执行，checkpoint 时也照此办理

## Resume 流程

用户说"继续 XX"时：

1. 定位项目 → 读 `handoffs/INDEX.md` 找到任务目录 → 读 `HANDOFF.md`
2. 需要理解"为什么这样设计" → 再读对应 repo 的 `docs/design.md` 与 `docs/decisions.md`
3. 向用户确认状态是否有新变化
4. 从 Current Status 第一个未完成项开始干活

## 完成任务

1. `HANDOFF.md` 全部步骤标完成
2. `INDEX.md` 中把任务移入"归档"
3. 长期有效的决策确认已在 decisions.md（通常 close-out 已做，这里核对）

## 主动提醒时机

- 即将开始可能出错需要回退的操作 → 建议先 checkpoint
- 用户说"今天先到这" → 建议跑 `/close-out`（不是本 skill）
