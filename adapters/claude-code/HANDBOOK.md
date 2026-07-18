# Claude Code Handbook —— 接入机制与备忘

## 安装机制

- 全局 skills：`~/.claude/skills/<name>` → symlink → `~/.agents/skills/<name>`（install.sh 自动维护）。
- 第三方 skills：`core/skills.txt` 清单，经 `npx skills add <repo> --skill <name> -g -y` 安装（install.sh 自动执行）。
- workspace 入口：Claude Code 读 `CLAUDE.md`；install.sh 在 workspace 根放了 `CLAUDE.md → AGENTS.md` 的 symlink，单一入口不分叉。

## 备忘

- McKinsey 侧 Claude Code 于 2026-06 获批：MacBook Air 已装；McKinsey Dell (Windows) 未装，
  装好后跑一遍 core 的 install.sh 即可对齐全套 skills。
- Claude Code 对 AGENTS.md/skill 的遵循度是三个工具里最好的，keyword 触发基本可用，
  但确定性起见仍推荐斜杠显式呼出。

- **journal 面包屑 rule**：内容真身在 `adapters/windsurf/rules/core-journal.md`。
  Claude Code 侧等价实现：把同样内容放进 workspace 的 CLAUDE.md/AGENTS.md 约束段，
  或用 SessionEnd hook 提醒跑 /close-out。MBA 启用时顺手做。
