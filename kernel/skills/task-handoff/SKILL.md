---
name: task-handoff
description: 任务交接协议：checkpoint / handoff / resume 的标准流程，含 handoff 瘦身原则。Use when 对话太长需要新开 session 并保留 context，或用户说 交接 / handoff / checkpoint。
---

> 迁移注：本 skill 自 agentic-workspace `rules/skills/` 迁入。原文引用的 `tools/` 资源文件已移入本 skill 目录；`contexts/`、`rules/skills/` 等旧路径按 STUDY.md / 当前 workspace 路由理解。

# Skill: 任务交接协议（Task Handoff Protocol）

## When to Use

- 用户说"checkpoint"、"存档"、"写交接"、"handoff"
- 用户说"继续 XX 任务"、"resume XX"
- Context window 消耗较大，主动提议做一次 checkpoint
- 任务到达阶段性节点

## 定位项目

Handoff 按项目域组织，存放在 `projects/<project>/handoffs/`。

1. 如果当前对话已在某个项目上下文中工作，直接使用该项目
2. 如果用户指定了项目名，用 WORKSPACE.md 快速查询定位
3. 如果不确定，扫描 `projects/*/handoffs/INDEX.md` 找到匹配的任务

## 创建新任务

1. 确定目标项目（见"定位项目"）
2. 在 `projects/<project>/handoffs/` 下创建目录（snake_case）
3. 创建 `HANDOFF.md`，填写下方模板
4. 更新 `projects/<project>/handoffs/INDEX.md`

## 写交接（Checkpoint / Handoff）

更新 `HANDOFF.md`，确保覆盖以下所有区块：

```markdown
# Task: <任务名>
Updated: YYYY-MM-DD HH:MM

## Objective
一句话：最终要达成什么。

## Task-Critical Decisions
- 只记录仍然影响下一步执行的关键决策摘要
- 如果某个决策已经是长期项目决策，转写到 `projects/<project>/docs/decisions.md`

## Current Status
- [x] 已完成的步骤
- [ ] 🔵 当前进行中（卡点/进展）
- [ ] 待做的步骤

## Important Context
- 关键文件与作用
- 已知坑和绕过方式
- 外部依赖（API、服务、数据）

## Open Questions
- 待确认事项
- 需要用户决策的问题
```

### 写交接的原则

- **写给下一个完全没有上下文的 AI**，不要假设它知道任何之前的对话
- **handoff 只服务续工**——优先写"现在做到哪、下一步是什么、卡在哪"
- **决策只保留当前仍影响续工的摘要**——长期有效的项目决策转去 `docs/decisions.md`
- **文件路径要具体**——写 `projects/<project>/repos/repo-name/path/to/file.py` 的 `ClassName.method()`，不要写"那个文件"
- **状态要可执行**——下一步能直接动手，不需要再问"从哪开始"

### 不要让 handoff 变成决策档案

以下内容不应该长期堆在 `HANDOFF.md`：

- 完整设计推理过程
- 历史上所有 decision log
- 已经稳定、不再影响当前续工的选择理由

如果这些内容很重要，应转写到：

- `projects/<project>/docs/decisions.md`

如果这些内容来自刚结束的一轮长聊天，优先运行：

- `rules/skills/chat_session_distillation.md`

## 恢复任务（Resume）

用户说"继续 XX"时：

1. 定位项目（见"定位项目"）
2. 读 `projects/<project>/handoffs/INDEX.md` 找到任务目录
3. 读该任务的 `HANDOFF.md`
4. 向用户确认当前状态是否准确，有无新变化
5. 从 Current Status 中第一个未完成项开始工作

## 完成任务

1. 更新 `HANDOFF.md`，所有步骤标记完成
2. 在 `INDEX.md` 中将任务从"任务列表"移到"归档"
3. 如有长期有效的项目决策，补写到 `projects/<project>/docs/decisions.md`
4. 如有跨任务通用的经验教训，再考虑是否值得进入后续 reflection / candidate 流程

## 主动提醒时机

当以下条件成立时，主动建议用户做 checkpoint：
- 对话已经很长，且完成了一个阶段性目标
- 即将开始一个可能出错需要回退的操作
- 用户明确说"今天先到这"或类似结束信号

如果这一轮聊天里产生了较多设计权衡、偏好暴露或可复用模式，优先建议：

- 先做 `chat_session_distillation`
- 再把其中的 task continuation 写入 `HANDOFF.md`
