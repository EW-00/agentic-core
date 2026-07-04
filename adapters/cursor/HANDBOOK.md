# Cursor Handbook —— 接入机制与备忘

## 安装机制

- 全局 skills：与 Claude Code 相同的 symlink 模式（唯一真身 `~/.agents/skills/`）。
  Cursor 的全局规则/命令目录在下次实际使用 Cursor 时确认一次并回流到这里
  （install.sh 的 `CURSOR_RULES_DIR` 变量预留）。
- workspace rules：`.cursor/rules/*.mdc`（带 frontmatter 的 MDC 格式）。
  目前 core 未生成 Cursor 版规则——回归 Cursor 工作流（McKinsey 机月底 fallback 或
  下个 study）时，把 `adapters/windsurf/rules/` 的三条内容翻译成 .mdc 即可，
  内容一字不变，只换壳。

## 备忘

- Cursor 按 token 计费（对比 Windsurf 按 prompt 计费）：多轮讨论无惩罚，
  grill/追问式工作流可全功率使用，无需一次性批量提问的阉割版。
