---
name: close-out
description: 每日收尾仪式：读 journal 面包屑 + 当天 git 证据 + 场外结论，以编辑者姿态（合并/删除/毕业，而非追加）把当天知识压实进最小文档集（各 repo README+design.md、项目层 STUDY.md+decisions.md），更新 HANDOFF，清空 journal。Use when 用户说 /close-out、收尾、今天到这、sync docs、整理文档。附带 audit 手动档做规范体检。
---

# Skill: 每日收尾（Close-out）

> Fork 自 [KKKKhazix/khazix-skills](https://github.com/KKKKhazix/khazix-skills) 的 neat-freak，
> 按本 workspace 的最小文档集与"journal + 每日压实"架构改造。工具无关：Windsurf /
> Claude Code / Cursor / Codex 通用。

你是**知识库编辑，不是记录员**。记录员只会往后追加；编辑会审查全局、合并重复、修正过期、
删除废弃。你的目标：让文档永远反映**现状**，让下一个 agent（或下一个 session 的你）
基于正确前提工作。

## 架构定位（为什么是"每日"而不是"每会话"）

- **会话内**：journal rule（always_on）在每次实质性改码的会话里自动追加一行面包屑
  （改了什么 + 为什么）——零额外成本，小会话直接关，无需任何收尾动作。
- **每日一次**：本 skill 把当天所有面包屑 + git 证据 + 场外结论**压实**进权威文档，
  然后清空 journal。这是 write-ahead log + compaction：记录免费化，压实按天化。

## 输入源（三个，缺一不可地检查）

1. **Journal**：`projects/<study>/notes/journal.md` —— 当天各会话的 what + why 面包屑
2. **Git 证据**：对每个 `projects/<study>/repos/*/`：
   `git log --oneline --since="6am" --all` + `git status --short` + 必要时 `git diff --stat`
3. **场外结论**：用户在调用命令里带的内容（如 `/close-out 场外：客户同意 X 改软约束`）。
   **不要反问**——用户没带就视为"无"，直接开始。多问一轮 = 多花一次 credit。

## 维护对象：最小文档集（只有这些，不新增其他文档）

| 文档 | 内容 | 铁律 |
|---|---|---|
| 每个 repo 的 `README.md` | 怎么跑：环境、命令、入口 | 与代码一致，装不上跑不通就是 bug |
| 每个 repo 的 `docs/design.md` | 该 repo 核心设计的**现状**（DS repo = formulation 当前形态） | **只写现状不写历史**；历史归 decisions |
| 每个 repo 的 `docs/decisions.md` | 该 repo 的工程决策（append 后定期压实） | 已推翻/已完成的删 |
| 项目层 `STUDY.md` | 路由表、合规红线、工具备注 | 变了就改，不堆叙事 |
| 项目层 `docs/decisions.md` | **仅**跨 repo / formulation 级 / 客户拍板的决策 | repo 级决策不许进来 |
| 任务 `HANDOFF.md` | 在途任务的续工状态 | 只服务续工，保持短 |

## 执行流程

### 第一步：盘点（机械式，不许跳过）

1. 读 journal.md 全部未压实条目
2. 对每个 repo 跑 git 证据命令（只看**今天**的改动）
3. 读现有的六类文档 + 在途 HANDOFF.md
4. 内部列一张清单：每份文档标"要改 / 不用改"——漏一个不行

### 第二步：压实（编辑者四原则）

- **合并优于追加**：新信息是旧条目的更新就改旧条目；append 前先搜同关键字
- **删除优于保留**：已定稿的 option 探讨（只留胜者一行 + 为什么）、已完成的临时计划、
  被推翻的决策、单次 debug 流水账——删
- **毕业机制**：decisions 里反复出现的稳定机制说明 → 并进 design.md，原条目删；
  journal 里的 why → 归宿是 design.md（机制变化）或 decisions.md（决策），不留在 journal
- **现状优先**：design.md 读起来必须像"现在就是这样"，不像"我们曾经讨论过"

分流判据：

- 改动的**为什么**是数据/业务背景变化 → design.md 对应小节就地更新
- 是一次拍板（选了 A 放弃 B） → decisions.md（repo 级进 repo，跨 repo 级进项目层）追加一行：
  `- YYYY-MM-DD：<决策>（因为 <一句话>）`
- 是在途任务的进度 → HANDOFF.md 的 Current Status
- 是环境/命令变化 → README.md

### 第三步：更新 HANDOFF

对每个在途任务：按 task-handoff 模板刷新 Current Status / 下一步 / 卡点。
今天完结的任务：归档（见 task-handoff skill 的完成流程）。

### 第四步：清空 journal

已压实的行从 journal.md 删除（整个文件通常清空）。journal 里只允许留"今天没来得及
压实判断、明天再看"的行，且必须带日期。

### 第五步：自检清单（逐项过）

- [ ] 第一步清单里每份文档都判了"已改"或"不用改"
- [ ] design.md 无历史叙事残留（"当时我们考虑过…"→ 删或迁 decisions）
- [ ] decisions.md 无已死的 option 探讨、无 repo 级/项目级错位
- [ ] README 的命令与代码一致
- [ ] HANDOFF 的下一步可直接执行
- [ ] journal 已清空（或只剩带日期的存疑行）
- [ ] 无相对时间（grep 今天/昨天/最近/recently → 全部换绝对日期）
- [ ] 文档净增行数合理——收尾的正常结果经常是**净减**；连续多天只增不减 = 在当记录员

### 第六步：变更摘要（10 行以内）

```
## 收尾完成 YYYY-MM-DD
- <repo>/docs/design.md — <改了什么>
- 项目 decisions.md — 新增 N 条 / 删除 N 条（原因）
- HANDOFF <任务> — 下一步：<一句话>
- 待你拍板：<仅列无法自动判断的矛盾>
```

只列有变更的。没有"待你拍板"就不写这一节。

## 手动档：`/close-out audit`（不进日常）

用户明确要求时才做的规范体检：文档间矛盾、死引用（文档提到的路径/命令还存在吗）、
尺寸体检（design.md > ~800 行提示拆分；decisions.md > ~150 行提示压实）、
STUDY.md 与现实的漂移。破坏性修复（删文件、大重组）列"待你拍板"，不自动执行。

## 首次运行（bootstrap，一次性）

第一次在项目上运行时，现状是"文档基本不存在 + decisions.md 大杂烩"，流程改为：

1. **decisions 大清理**：通读现有 decisions.md → 已死的 option 探讨删掉（每个只留胜者
   一行）→ repo 级决策迁入各 repo `docs/decisions.md` → 项目层只留跨 repo/客户拍板的
2. **design.md 反向生成**：对每个用户 own 的 repo，从代码现状生成 `docs/design.md` 初稿
   （DS repo 以 formulation 为主体），提交用户人工过一遍
3. **README 补齐**：缺失的按"怎么跑"最小标准补
4. 建空 `notes/journal.md`，之后进入每日节奏

## 平台适配注记

- 本 skill 不依赖任何平台专有文件。"项目根 markdown"在本 workspace = `AGENTS.md` +
  `STUDY.md`；若平台另有约定（CLAUDE.md 等）按其现状处理，**不新建平台专有文件**。
- Agent 记忆系统（如 Claude Code 的 memory 目录）：**平台有才管**——过期记忆改、
  重复合并、稳定知识毕业进 docs；平台没有（如 Windsurf）整层跳过。
- 计费为按 prompt 的平台（Windsurf）：全流程必须在**一条 prompt**内完成，不反问用户。
