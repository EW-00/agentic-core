---
name: bilibili-whisper-transcription
description: 视频字幕提取与云端转录：Bilibili/YouTube 字幕优先，无字幕用 OpenAI whisper-1。Use when 需要视频/音频转文字。
---

> 迁移注：本 skill 自 agentic-workspace `rules/skills/` 迁入。原文引用的 `tools/` 资源文件已移入本 skill 目录；`contexts/`、`rules/skills/` 等旧路径按 STUDY.md / 当前 workspace 路由理解。

# 视频字幕提取与云端转录工作流

## 元数据
- 类型: Workflow
- 适用场景: Bilibili/YouTube 视频字幕提取 + 云端语音识别
- 创建日期: 2025-02-12
- 最后更新: 2026-05-04
- 原项目已归档（不再保留在 workspace 中）

## 路径约定

- 临时下载与中间产物：`tmp/<task_name>/`
- 最终可长期保留的 transcript：`projects/media_reading_packets/artifacts/`
- 最终默认保留 Markdown transcript，并保留 `[HH:MM:SS]` 时间戳，便于回看定位
- 音频、`.srt`、`.vtt`、`.tsv`、`.json` 等中间产物在 transcript 落盘后清理到废纸篓

## 现成工具入口

单个 YouTube / Bilibili 视频优先使用仓库内工具：

```bash
.venv/bin/python tools/yt_transcript.py "https://www.youtube.com/watch?v=<video_id>"
.venv/bin/python tools/yt_transcript.py "https://www.bilibili.com/video/BV..."
```

默认输出到：

```text
projects/media_reading_packets/artifacts/
```

工具行为：

1. 优先用 `yt-dlp` 获取 YouTube / Bilibili 平台字幕，而不是直接下载音频转录
2. 优先语言：`zh-Hans` / `zh` / `zh-CN` / `en` / `ja` / `ko`
3. 下载 VTT/SRT/SRV/JSON3 字幕后转换成 `[HH:MM:SS] text` Markdown
4. 没有平台字幕时，下载音频并走 OpenAI 云端转录；默认模型为 `whisper-1`
5. 如需整理标点、分段和时间戳密度，优先通过 OpenCode 做 cleanup；只有在 OpenCode 不可用时，再考虑 raw `OPENAI_API_KEY` / `GEMINI_API_KEY`

## 核心流程

**三阶段工作流：**

1. **获取元数据与字幕列表** → 使用 `yt-dlp` 提取视频 ID、标题、时长和字幕信息
2. **优先保存平台字幕** → 有 CC / 自动字幕时，直接转换成带时间戳 Markdown
3. **无字幕走云端转录** → 下载临时音频，调用 OpenAI Transcription API，长音频自动分块并合并时间戳

## 关键决策

| 决策点 | 选择 | 原因 |
|--------|------|------|
| 下载并发 | 单线程 | 避免触发平台反爬机制 |
| 转录后端 | 默认 OpenAI API | 无字幕视频优先质量与速度，不再自动回退本地 CPU 转录 |
| 默认云端模型 | `whisper-1` | 当前工具默认，成本可接受，输出稳定 |
| 输出格式 | Markdown + `[HH:MM:SS]` 时间戳 | 便于检索、引用和回看定位 |

## 本地 Whisper 模型选择

本地 Whisper / faster-whisper 只作为显式测试或离线 fallback 使用；默认自动路径不再选择本地转录。

| 模型 | 参数量 | 速度（CPU） | 准确度 | 推荐场景 |
|------|--------|-------------|--------|----------|
| tiny | 39M | 1-2分钟/10分钟 | 较低 | 快速预览 |
| base | 74M | 2-5分钟/10分钟 | 中等 | 平衡选择 |
| small | 244M | 5-10分钟/10分钟 | 较高 | 日常使用 |
| medium | 769M | 10-20分钟/10分钟 | 高 | 高质量需求 |
| large-v3 | 1550M | 20-60分钟/10分钟 | 最高 | 最高质量要求 |

## LLM 后处理

语音转录原始输出通常需要后处理：

1. **转换为简体中文** — 识别可能为繁体
2. **添加标点符号** — 根据语义添加逗号、句号、问号
3. **合理分段** — 按主题划分段落，添加小标题
4. **纠正术语** — 专业名词识别错误（如"木质布"→"木质部"、"筛管细胞"）
5. **优化可读性** — 调整语序、补充缺失内容

## 踩坑记录

| 问题 | 现象 | 解决方案 |
|------|------|----------|
| **352错误** | 请求被B站拦截 | 添加User-Agent/Referer headers，增加延迟，或手动获取ID |
| **404错误** | 视频已删除或ID错误 | 验证ID有效性，跳过无效视频，记录失败ID |
| **本地转录资源不足** | 显式使用本地 Whisper / faster-whisper 时 CPU、内存或耗时不可接受 | 默认改用云端转录；只有离线或对照测试时才显式指定本地 backend |
| **下载不完整** | .m4a文件无法播放 | 检查文件大小，重新下载，添加完整性验证 |
| **云端转录失败** | API key 缺失、额度不足、网络失败或文件超过接口限制 | 检查 `.env` 中 `OPENAI_API_KEY`，长音频由工具自动分块；本地 backend 仅作显式 fallback |

## 最佳实践

**下载阶段：** 先只读取元数据和字幕；只有无平台字幕时才临时下载音频

**转录阶段：** 无平台字幕时默认 OpenAI API `whisper-1`；本地 `openai-whisper` / `faster-whisper` 仅在显式指定 backend 时使用

**落盘阶段：** 在 `tmp/` 完成下载和转录，整理出 Markdown transcript 后移入 `projects/media_reading_packets/artifacts/`

**清理阶段：** transcript 落盘后删除或回收音频、时间轴字幕和 sidecar 文件，只保留最终脚本

**质量优化：** 关键内容优先用云端模型；必要时人工校对，或显式对照本地 large-v3

**错误处理：** 实现重试机制，验证文件完整性，处理异常避免脚本中断
