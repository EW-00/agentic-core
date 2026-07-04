# Day-1 Checklist — 新机器 / 新 study 从零到可工作

> 目标：两小时内完成。每次用完在末尾"本次经验"记一行，回流改进本清单。

## A. 终端环境（machine-setup，约 20 分钟）

- [ ] macOS：装 Homebrew → `brew install chezmoi` → `chezmoi init --apply EW-00/machine-setup` → `brew bundle --file ~/.local/share/chezmoi/Brewfile`
- [ ] Windows 客户机：先启用 WSL（`wsl --install`，需要时走客户 IT 流程）→ WSL 内跑
      `bash -c "$(curl -fsSL https://raw.githubusercontent.com/EW-00/machine-setup/main/bootstrap/wsl.sh)"`
- [ ] 验证：新开终端，starship 提示符 + `z`/`fzf`/`uv` 可用

## B. Workspace（agentic-core，约 10 分钟）

- [ ] `git clone https://github.com/EW-00/agentic-core ~/workspace/core`
- [ ] `cd ~/workspace/core && ./install.sh --profile client`（客户机；McKinsey 机用 `firm`。此 clone 永不 push）
- [ ] **手动放置 `USER.md`** 到 `~/workspace/core/kernel/rules/USER.md`（隐私文件不入库，已被 .gitignore 忽略；内容自己保管，如 Notion 私页）
- [ ] 填 `~/workspace/STUDY.md`（模板已就位；红线段落第一天就写，哪怕其他留空）
- [ ] 把项目 repos clone 进 `~/workspace/projects/<study>/repos/`

## C. 本机 AI 工具适配（约 20 分钟）

- [ ] 确认本机有哪些 AI 工具与额度，记入 STUDY.md
- [ ] 读对应的 `core/adapters/<tool>/HANDBOOK.md`（5 分钟，激活已付学费的坑）
- [ ] Windsurf：确认 `.windsurf/rules/core-*.md` 已就位；确认全局 skills 目录路径并回填 install.sh 变量；测一次斜杠呼出 task-handoff
- [ ] Claude Code / Cursor：测一次斜杠呼出
- [ ] 新工具（本 adapter 还没有的）：花一小时找到它的**确定性触发机制**（斜杠命令/rules 注入），建 `core/adapters/<新工具>/`，HANDBOOK 的第一条就记这个机制

## D. 合规与管道（第一周内完成）

- [ ] 问清本客户环境的**唯一合规出口管道**（SharePoint 或其他），记入 STUDY.md
- [ ] 如需月底 credits 耗尽的 fallback（在非客户机上编码），**向 EM 拿书面许可**再启用 `core/scripts/bundle-out.sh` 流程
- [ ] 确认个人 GitHub 在本机的读取是否通畅（决定 chezmoi update / core pull 是否可用）

## E. 收尾

- [ ] Notion 里建本 study 的 daily 页面（笔记层在 Notion，repo 只收蒸馏产物）
- [ ] 本清单走完后，把不顺的步骤记到下面

## 本次经验（append-only）

- <YYYY-MM-DD 机器/study：一句话>
