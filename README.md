# agentic-core

可移植 AI 工作流内核。设计目标只有一个：**每 3-4 个月换一个 study（新客户、
新电脑、新 AI 工具）时，Day-1 两条命令恢复全部工作方式。**

前身是 [agentic-workspace](https://github.com/EW-00/agentic-workspace)（fork 自
grapeot/context-infrastructure），2026-07 按"分层内核 + 工具适配器"重构。
终端环境（zsh/starship/brew）由姊妹仓库 [machine-setup](https://github.com/EW-00/machine-setup)
（chezmoi）独立管理。

## 使用

```bash
git clone https://github.com/EW-00/agentic-core ~/workspace/core
cd ~/workspace/core && ./install.sh --profile <client|firm|personal>   # 幂等，可反复重跑
```

`--profile` 决定装哪些 skills（默认 `personal` = 全量）：客户机 `client` 只装工作必需的
最小集，McKinsey 机 `firm` 居中。清单在 `kernel/skills/PROFILES.txt` 和 `skills.txt`
第三列，一行一个 skill，改标签即改安装范围。

跑完得到 `~/workspace/`：AGENTS.md（生成）、rules/（symlink 到 kernel）、STUDY.md
（模板，你填写）、.windsurf/rules/core-*.md、全局 skills（~/.agents/skills + 各工具
symlink）、哨兵 root repo。收更新：`cd ~/workspace/core && git pull && ./install.sh`。

## 分层（放哪儿的唯一判据："换了项目/工具还成立吗？"）

| 层 | 内容 | 位置 | 流动 |
|---|---|---|---|
| **L0 kernel** | 身份规则、43 axioms、17 自研 skills | `kernel/` | GitHub 同步全机器 |
| **L1 adapters** | 每工具的 rules 壳、HANDBOOK（手册：接入机制+坑）、安装逻辑 | `adapters/<tool>/` | GitHub 同步全机器 |
| **L2 study** | 项目路由、客户约定、合规红线 | 本机 `STUDY.md` 等 | **永不离开客户机** |

回流规则：客户机对 GitHub **pull-only**；在客户机发现的通用改进 → Notion 记一行 →
回个人/McKinsey 机剥掉客户名词后改 core 并 push。

## 目录

```
kernel/rules/        SOUL / COMMUNICATION + axioms/（43 条，按需 @）；USER.md 不入库，每机手动放置
kernel/skills/       17 个自研 skill（SKILL.md 标准，全局安装唯一真身的源头）
skills.txt           第三方 skill 清单（npx skills add -g）
adapters/{windsurf,claude-code,cursor}/   rules 模板 + HANDBOOK.md（接入机制、计费特性、付过学费的坑）
templates/           AGENTS.md / STUDY.md / Day-1 checklist / vscode 设置
scripts/             bundle-out.sh / apply-in.sh（credits 耗尽时的 SharePoint 双向流程）
docs/                git-boundaries（三层 git 边界）/ BACKFLOW-TODO（待回流清单）
install.sh           幂等物化脚本（见文件头注释）
```

## 维护原则

- 不需要的 skill 直接删，避免噪声；新 skill 建 `kernel/skills/<name>/SKILL.md`
- 每个工具的新坑先记本机 STUDY.md，确认通用后回流对应 adapter 的 HANDBOOK
- 笔记层在 Notion；本 repo 只收蒸馏后的可复用资产

## License

MIT（继承自原仓库）
