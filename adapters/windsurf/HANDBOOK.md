# Windsurf Handbook —— 接入机制、计费特性与已知的坑

> 每条标注了出口：`[脚本自动修]` = install.sh 已处理；`[rule]` = 已物化为 rules 文件自动注入；
> `[人读]` = Day-1 时花五分钟重读本文件即可激活。

## 1. Credit 经济学 `[人读]`

按 **prompt 次数**计费（不是 token）："Hello" 和复杂请求同价。价目（high-thinking，2026-07 实测）：

| 模型 | credits/prompt | 定位 |
|---|---|---|
| GPT 5.4 | 4x | **日常默认**：探索、小改、机械重构 |
| Claude 4.6 | 6x | 正式实现、代码质量要求高的改动 |
| GPT 5.5 | 25x | 只给**已经收敛**的复杂多文件 plan 执行 |
| Claude 4.8 | 40x | 原则上不用（月预算只够 50 次） |

月度 2000 credits ≈ 每工作日 ~20 次好模型 prompt。纪律：
- 多轮讨论是最大的隐性杀手：15 轮对齐 = 90 credits。用**一次性批量提问版 grill**（让它把所有问题一次问完，统一回答，最多再迭代一轮）。
- plan 收敛前用 4x/6x 模型，收敛后才值得上 25x 执行。
- credits 见底的应急阀：把报错 + 已试修法贴进 ask.dell（免费 Claude 4.6，纯 chat）要一个新假设——不承担 plan/debug 主力，只做第二意见。
- 月底耗尽 → 走 `scripts/bundle-out.sh` SharePoint 流程流亡 McKinsey 机（见 core/scripts/）。

## 2. Rules 的硬预算 `[人读]`

单条 rule ≤ 6,000 字符；**所有生效 rules 合计 ≤ 12,000 字符**。
所以 always_on 只放最高价值的短规则；长内容走全局 skills 按需斜杠/@ 呼出。
AGENTS.md 塞得再满也不如三条精准的 always_on rule。

## 3. 编辑/patch 工具偶发失败 `[rule: core-patch-tool.md]`

Cascade 的 patch 工具偶发失败后，模型会以此为借口宣布改不了文件。
已由 always_on rule 强制其尝试替代手段（换工具 / 终端写入 / 输出全文）。

## 4. gitignore 文件拒改 `[脚本自动修 + 待验证]`

Cascade 拒绝读写被 `.gitignore` 覆盖的文件；官方开关 "Allow Cascade to access
.gitignore files" 和 `.codeiumignore` 的 `!` 例外均有已知失效 issue
（Exafunction/codeium #225、#133）。

**结构性解法（新架构下）**：workspace 根目录不再有带 `/projects/*` ignore 的 git repo。
install.sh 默认建"哨兵 root repo"（`git init` + `.git/info/exclude` 写 `*`，**不创建
.gitignore 文件**）：编辑器有锚定 repo、Cascade 找不到任何 .gitignore、哨兵 repo 永不 commit。

⚠️ 待 Dell 机验证：Cascade 是否也解析 `.git/info/exclude`（预期不会）。若失效，
fallback：删哨兵 repo + 用 `.vscode/settings.json` 的 `git.autoRepositoryDetection:
"openEditors"` 控制 SCM 面板噪音。

## 5. 多 repo 的 SCM 面板 `[人读]`

workspace 下多个真实 repo 时，Source Control 面板按 repo 分组显示、badge 是总数。
review 时按分组逐 repo 看；嫌乱可在面板里折叠/隐藏不相关 repo，或用上面的
`openEditors` 设置只显示碰过的 repo。

## 6. 全局 skills 目录 `[人读 + 待验证]`

个人 Mac 上的机制：skills 唯一真身在 `~/.agents/skills/`，各工具目录放 symlink。
Windsurf 的全局 skills 目录路径待在 Dell 机上确认一次（候选：`~/.codeium/windsurf/`
下的 skills/global_workflows 目录），确认后填进 install.sh 的 `WINDSURF_SKILLS_DIR`
变量并回流本文件。

## 7. 斜杠机制备忘 `[人读]`

全局安装 + 斜杠/@ 呼出是经过数月验证的可靠触发方式。若未来某个 Windsurf 版本
斜杠呼出变得不可靠，原生备选方案是 `.windsurf/workflows/*.md`（确定性 / 命令，
支持 `~/.codeium/windsurf/global_workflows/` 全局目录）——目前无需迁移。

## 8. AGENTS.md 遵循度 `[人读]`

Windsurf 对 AGENTS.md 的遵循弱于 Claude Code/Cursor：关键词触发 skill 基本不可靠
（index 间接层时代的教训），重要约束要么进 rules（强制注入）要么靠斜杠显式呼出，
不要指望它"自觉记得"markdown 里的恳求。
