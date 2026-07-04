---
name: video-reading-packet
description: 视频阅读包工作流：YouTube/Bilibili 链接 -> transcript + 深度分析阅读包（互链、时间戳、personal insights）。Use when 用户给视频链接并要求深读。
---

> 迁移注：本 skill 自 agentic-workspace `rules/skills/` 迁入。原文引用的 `tools/` 资源文件已移入本 skill 目录；`contexts/`、`rules/skills/` 等旧路径按 STUDY.md / 当前 workspace 路由理解。

# 视频阅读包工作流

## 元数据

- 类型: Workflow
- 适用场景: 从 YouTube / Bilibili 视频链接生成可长期阅读、可回看定位、可继续和 AI 深聊的 transcript + 深度分析阅读包
- 输出位置: `projects/media_reading_packets/artifacts/<packet_slug>/`
- 上游工具: `tools/yt_transcript.py`
- 相关 skill: `workflow_bilibili_whisper_transcription.md`, `semantic_search.md`
- 创建日期: 2026-05-09

## 目标

把一个长视频转成一个自洽的 reading packet。产物必须让用户在没有看过视频的情况下快速知道内容地图，也能在之后阅读 transcript、回跳原视频、继续和 AI 讨论高价值观点。

默认产物为同一文件夹下的两个 Markdown 文件：

```text
projects/media_reading_packets/artifacts/<packet_slug>/
├── transcript.md
└── analysis.md
```

旧结构 `artifacts/transcripts/` 和 `artifacts/deep_analysis/` 可继续读取；新任务默认使用 reading packet 结构。

## 输入范围

首版只把 YouTube / Bilibili 链接作为自动提取对象。播客链接暂不自动处理；如果用户已经提供播客 transcript，可以跳过提取步骤，直接按本 workflow 生成阅读包。

## 核心原则

1. **先保真，再分析**: transcript 是事实底座。分析必须能回到 transcript 和原始视频时间点。
2. **区分事实和推断**: 明确标注视频中直接表达的观点、基于多处 transcript 的综合判断，以及 AI 的延伸分析。
3. **先给地图，再给深度**: `analysis.md` 先提供时间顺序大纲，再进入高价值 insight。
4. **捕捉非共识观点**: 重点寻找行业专家、资深从业者、创始人、研究者的独特判断、反直觉经验和背后 reasoning。
5. **允许跳跃式综合**: deep insights 不受时间顺序限制。多个时间点共同指向同一观点时，合并成一个 insight，并保留各自时间证据。
6. **面向用户转化**: personal relevance 可以调用用户画像、memory、axioms、历史 notes，把一部分 insight 映射到用户的现实处境。

## 输出命名

`packet_slug` 使用稳定、可读、可排序的名字。中文视频优先保留中文短标题，让目录名一眼能看出这期内容；英文视频可以使用英文短标题。

```text
YYYYMMDD_<platform>_<video_id>_<short_readable_title>
```

示例：

```text
projects/media_reading_packets/artifacts/20260503_youtube_-Et3GJRSI_0_清华教授_应试教育_ai时代如何学习/
projects/media_reading_packets/artifacts/20260412_youtube_YE24Rpn3oD0_第一性原理思考_databricks_reynold_xin访谈/
```

如果 `tools/yt_transcript.py` 已生成旧式文件名，创建 packet 文件夹后把内容复制或移动为 `transcript.md`。不要删除旧文件，除非用户明确要求清理。

## 工作流程

### Phase 1: 生成或定位 transcript

如果用户提供的是 YouTube / Bilibili 链接，优先调用现有工具。转录阶段先输出到临时目录，避免在 `artifacts/` 根目录留下旧式 transcript 文件：

```bash
.venv/bin/python tools/yt_transcript.py "<url>" --output-dir tmp/media_reading_packets_transcript
```

可选参数：

```bash
.venv/bin/python tools/yt_transcript.py "<url>" --browser firefox --output-dir tmp/media_reading_packets_transcript
.venv/bin/python tools/yt_transcript.py "<url>" --no-cleanup --output-dir tmp/media_reading_packets_transcript
```

工具默认输出 Markdown transcript，保留 `[HH:MM:SS]` 时间戳。若平台无字幕，工具默认通过 OpenAI transcription API 转录。

如果用户已经提供 transcript 文件，直接使用该文件。先检查文件头部是否包含 source、duration、subtitle source 等元信息；缺失时在 packet 的 `transcript.md` 顶部补齐可获得的信息。

### Phase 2: 创建 reading packet

创建 packet 文件夹，把 transcript 标准化为：

```text
projects/media_reading_packets/artifacts/<packet_slug>/transcript.md
```

从临时目录移动唯一生成的 `.md` 文件到 `transcript.md`。如果临时目录中有多个候选文件，选择最新生成且标题/source 匹配当前视频的文件。移动完成后清理空临时目录。

`transcript.md` 顶部必须包含导航：

```markdown
# <Title>

## Navigation

- Source: <url>
- Analysis: [analysis.md](./analysis.md)
- Platform: <platform>
- Video ID: <video_id>
- Duration: <duration>
- Transcript status: raw / cleaned / user-provided
- Generated: <YYYY-MM-DD HH:MM>

## Reading Notes

- [ ] 

---
```

正文保留原始语言。中文视频保留中文 transcript；英文视频保留英文 transcript。不要为了分析便利把 transcript 全文翻译成中文。

### Phase 3: 增强时间戳导航

保留原有 `[HH:MM:SS]` 时间戳。分析引用时使用时间戳和 transcript 链接：

```markdown
[00:13:42](./transcript.md#001342)
```

如果 Markdown renderer 对自动 anchor 支持不稳定，可以在关键时间点前插入轻量 HTML anchor：

```markdown
<a id="001342"></a>
[00:13:42] ...
```

只需要给 analysis 引用到的关键时间点加 anchor。避免给每一行都插入 anchor，除非后续确实需要自动化跳转。

对于 YouTube 链接，在 `analysis.md` 的关键引用处同时提供原视频跳转链接：

```markdown
[00:13:42](./transcript.md#001342) | [video](https://www.youtube.com/watch?v=<id>&t=822s)
```

Bilibili 时间跳转支持不稳定时，保留 transcript 时间戳即可。

### Phase 4: 决定阅读策略

根据 transcript 长度选择策略：

1. **全量读入**: transcript 能完整进入上下文时，完整阅读后直接分析。
2. **分块提取 + 全局综合**: transcript 太长时，按时间顺序分块。每块提取章节、关键观点、reasoning、证据时间点、候选 personal insight。最后再做全局综合，去重、合并跨段落观点、识别隐含主线。
3. **主题优先补充**: 只有当用户指定主题时增加 topic-first pass。例如用户说重点看 AI 职业转型、data scientist 未来、agent workflow。

分块时不要只压缩摘要。每块至少保留：

- 时间范围
- 主要话题
- 关键原话或接近原话的 evidence
- 观点背后的 reasoning
- 值得回听的时间点
- 和用户相关的候选 insight

### Phase 5: 搜索用户知识体系

生成 `Personal Relevance` 前，主动检索用户相关背景。最低限度读取：

- `rules/USER.md`
- `contexts/memory/OBSERVATIONS.md`，如果存在
- `rules/axioms/INDEX.md`，如果主题涉及用户方法论、职业判断、AI 时代转型、学习系统

需要更深背景时使用 `semantic_search.md`。常用搜索路径：

- `contexts/daily_records/`
- `contexts/survey_sessions/`
- `contexts/thought_review/`
- `rules/axioms/`
- `rules/skills/`
- 相关 `projects/<project>/notes/`

搜索目标不是把用户历史观点硬套进视频，而是识别哪些 video insights 能映射到用户当前角色：data scientist、AI/agentic engineering 学习者、builder、知识系统构建者、深度研究和写作者。

### Phase 6: 生成 analysis.md

分析默认用中文写。视频为英文时，可以保留关键英文原话、术语和短引用。

`analysis.md` 使用以下结构：

```markdown
# <Title> - Deep Analysis

## Navigation

- Source: <url>
- Transcript: [transcript.md](./transcript.md)
- Generated: <YYYY-MM-DD HH:MM>
- Analysis language: Chinese
- Evidence policy: direct claims link to transcript timestamps; inferred claims are labeled.

## Executive Map

## Chronological Outline

## Deep Insights

## Personal Relevance

## Revisit Queue

## Open Questions
```

#### Executive Map

用 5 到 10 条说明这期内容的整体地图。不要写成泛泛摘要，要让用户知道这期节目最值得看的地方是什么。

#### Chronological Outline

按时间顺序列出章节。每个章节包含：

- 时间范围
- 主题
- 这一段讲了什么
- 关键人物或观点
- 值得回看时间点

#### Deep Insights

这是核心部分。每条 insight 可以使用自然段，但必须覆盖以下信息中的大部分：

- **观点**: 嘉宾或主持人真正提出了什么判断
- **为什么重要**: 为什么这不是普通聊天里常听到的浅层观点
- **Reasoning**: 观点背后的经验、逻辑、行业结构、约束条件或第一性原理
- **Evidence**: 链接到 transcript 时间点。多个时间点共同支撑同一 insight 时，全部列出
- **判断边界**: 这是视频中明确说的，还是基于 transcript 的综合推断
- **我的判断**: AI 的分析、质疑、延伸或和其他观点的连接

Deep insights 可以打破时间顺序。跨段落呼应应自然写在相关 insight 内，不单独建立固定章节。

#### Personal Relevance

结合用户个人背景写。重点关注：

- 对 data scientist 在 AI 时代的职业判断有什么启发
- 对 agentic engineering、AI-native workflow、个人知识系统有什么启发
- 哪些观点可以转化为用户下一步学习、实验、写作或工作方法
- 哪些观点值得保持怀疑，原因是什么

不要把所有 insight 都强行个人化。只挑真正有迁移价值的部分。

#### Revisit Queue

用表格列出值得回听或重读的片段：

```markdown
| Time | Why revisit | Suggested action |
|---|---|---|
| [00:13:42](./transcript.md#001342) | 核心非共识观点首次出现 | 回听并补个人笔记 |
```

#### Open Questions

列出读完后仍值得追问的问题。可以包括：

- 视频没有回答但很关键的问题
- 嘉宾观点的潜在反例
- 和用户当前项目或职业路径相关的后续问题

## 证据与推断标注规则

使用以下显式标签，避免混淆事实和分析：

- `视频明确说`: transcript 中直接出现的观点
- `综合推断`: 多个片段共同支持，但没有单句直接表达
- `AI 延伸`: 基于视频内容向外推演
- `我的疑问`: 对观点的保留、反例或需要继续验证的部分

每个重要论断至少给出一个时间戳。没有时间戳的论断只能作为 AI 延伸或个人化建议。

## 完成前检查

交付前检查：

1. `transcript.md` 顶部链接到 `analysis.md`
2. `analysis.md` 顶部链接到 `transcript.md`
3. 重要 insight 有 transcript 时间戳
4. 明确区分视频原意、综合推断和 AI 延伸
5. `Chronological Outline` 能让没看过视频的人理解节目结构
6. `Deep Insights` 包含 reasoning，而不是只罗列结论
7. `Personal Relevance` 结合了用户画像或相关记忆
8. `Revisit Queue` 至少包含 5 个高价值时间点，除非视频很短

## 常见错误

| 错误 | 修正 |
|---|---|
| 只写摘要，没有分析 | 增加 reasoning、行业结构、非共识观点和判断边界 |
| 把 AI 的推断写成嘉宾原话 | 加上 `综合推断` 或 `AI 延伸` 标签 |
| 时间戳只有文本，没有链接 | 至少在 analysis 的关键引用中链接回 transcript |
| 个人 relevance 太泛 | 回到用户角色：data scientist、AI 转型、agentic engineering、知识系统 |
| 分块后只拼接摘要 | 最后必须全局综合，合并跨段落观点并识别隐含主线 |
| 模板感太强 | 保留固定 section，但每个 insight 用自然段写，服务内容而不是填表 |
