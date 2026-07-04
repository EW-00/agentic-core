---
name: session-distillation
description: 聊天会话蒸馏：将长聊天中的高价值内容分流到 handoff、decisions 与后续 candidate。Use when 一段长对话结束后需要沉淀结论，或用户说 蒸馏 / distill。
---

> 迁移注：本 skill 自 agentic-workspace `rules/skills/` 迁入。原文引用的 `tools/` 资源文件已移入本 skill 目录；`contexts/`、`rules/skills/` 等旧路径按 STUDY.md / 当前 workspace 路由理解。

# Skill: Chat Session Distillation

## When to Use

- 一轮长聊天即将结束
- 聊天中产生了较多设计权衡、实现取舍或质量判断
- 用户说"distill this session"、"提炼"、"蒸馏"
- 需要把 chat 中的高价值内容转成文件系统里的长期可读资产

## Purpose

这个 skill 的作用不是保存完整聊天记录，而是把本轮聊天里的高价值内容结构化，并分流到正确的位置：

- task continuation → `handoffs/`
- stable project decisions → `docs/decisions.md`
- reusable patterns / preferences → 保留在 session distillation file 中，后续再判断是否值得进入 candidate

## Output Location

按项目域组织，存放在：

- `projects/<project>/chat_session_distillations/`

文件名建议：

- `YYYY-MM-DD_HHMM__<topic>.md`

## Session Distillation Template

```markdown
# Chat Session Distillation: <title>
Updated: YYYY-MM-DD HH:MM

## Session Objective
一句话说明本轮聊天想解决什么。

## What Was Resolved
- 本轮明确解决的事项

## Stable Decisions
- 决策 1：选择了什么，为什么
- 决策 2：...

## Task Continuation
- 当前做到哪
- 下一步是什么
- 当前 blocker / 风险

## Reusable Patterns
- 这次暴露出的稳定 workflow / 方法模式

## Preferences Revealed
- 这次聊天中暴露出的用户偏好 / 判断风格

## Suggested Routing
- to_handoff:
  - 需要写入 handoff 的内容
- to_decisions:
  - 需要写入 decisions.md 的内容
- to_candidates:
  - 可能值得后续进入 skill / axiom candidate 的内容
```

## Routing Rule

不要让 `chat_session_distillation` 和 `handoff` 各自完整写一遍同样的内容。

正确顺序：

1. 先做 session distillation
2. 再把 `Task Continuation` 写入当前任务的 `HANDOFF.md`
3. 再把 `Stable Decisions` 追加到 `projects/<project>/docs/decisions.md`

避免的情况：

- 先完整写一次 distillation
- 再完整写一次 handoff
- 两边重复记录同样的决策和状态

## Recommended Workflow

### A. End-of-Chat Flow

1. 定位当前项目
2. 在 `projects/<project>/chat_session_distillations/` 下创建或更新本轮 distillation file
3. 提炼本轮的：
   - 解决了什么
   - 形成了哪些稳定决策
   - 当前任务如何续工
   - 暴露了哪些可复用模式或偏好
4. 将 `Task Continuation` 写入当前任务的 `HANDOFF.md`
5. 将 `Stable Decisions` 追加到 `projects/<project>/docs/decisions.md`
6. 保留 `Reusable Patterns / Preferences Revealed` 在 distillation file 中，后续交给 human 或 reflector 判断

### B. Resume Flow

当用户说"继续这个任务"时：

1. 优先读 `HANDOFF.md`
2. 如需理解为什么这样做，再读 `docs/decisions.md`
3. 如仍需还原更细的 chat reasoning，再读最近的 `chat_session_distillations/`

## Principles

- **不保存整段聊天记录**——只提炼高价值内容
- **先分流，再落盘**——续工信息和长期决策不要混在一起
- **handoff 保持短**——让下一个 agent 能立刻继续干活
- **decisions 保持稳**——让项目级设计判断长期可维护
- **distillation 作为桥**——承接 chat 中产生但还没进入正式结构的内容
