# 原地收编：把已运转的旧 workspace 接入 agentic-core

> 适用场景：机器上已有一个跑了数周/数月的 workspace（旧 agentic-workspace clone +
> 本地魔改 + 在途项目），**mid-study 不能推倒重来**。本指引做的是无损收编：
> 只添不改，旧东西一个字节不动。全新机器请走 `templates/day1-checklist.md`。

## 原理

- 旧 workspace 的 origin 指向旧 repo（agentic-workspace）——**不要在那里 git pull**，
  拉不到新东西；新内核是独立 repo，单独 clone 进来。
- install.sh 的收编行为（均已实测）：手工改过的 AGENTS.md → 警告跳过；已存在的
  rules/ 真目录 → 警告跳过；repos/handoffs/decisions → 根本不在其操作范围。
  它净增的只有：`.windsurf/rules/core-*.md`、STUDY.md 模板、全局 skills、
  `.vscode/settings.json`（缺失时）。

## 步骤

0. **确认 workspace 位置**：WSL 文件系统内（`~/...`）→ 原样跑；
   Windows 侧（`/mnt/c/...`）→ 每条 install.sh 加 `--copy-mode`。

1. **clone 内核**（不动旧 workspace 任何东西）：

   ```bash
   cd <现有workspace路径>
   git clone https://github.com/EW-00/agentic-core core
   ```

2. **原地收编**：

   ```bash
   cd core && ./install.sh --workspace .. --profile client --no-third-party
   ```

   （`--no-third-party`：旧 workspace 里摊平的第三方 skills 原地可用，且客户机
   未必有 npx。）输出里的黄色警告=正确的绕行，逐条读一遍。

3. **填 STUDY.md**（10 分钟）：repo 路由表 + 合规红线先写，其他可留空。

4. **info/exclude 实验**（治 Cascade 拒改 gitignored 文件，2 分钟）：

   ```bash
   cd <workspace路径>
   grep -v '^/projects' .gitignore > .gitignore.tmp && mv .gitignore.tmp .gitignore
   printf '/projects/*\n!/projects/README.md\n' >> .git/info/exclude
   ```

   让 Cascade 改一个 projects 下的文件验证。失败则还原 .gitignore 并把结果
   回流 `adapters/windsurf/HANDBOOK.md` §4。

5. **确认 Windsurf 全局 skills 目录**：找到现有摊平 skills 被斜杠呼出的真实路径，
   回填 install.sh 的 `WINDSURF_SKILLS_DIR` 后重跑。找不到不阻塞——
   `@core/kernel/skills/<name>/SKILL.md` 照样可呼出。

6. **启动日常节奏**：journal rule 当天即生效（小会话直接关）；挑 credit 富余日
   跑 `/close-out` 首次 bootstrap（decisions 两层大清理 + design.md 反向生成）。

## 以后

- **收内核更新**：`cd core && git pull && ./install.sh --workspace .. --profile client`
- **回流改进**：客户机永不 push——Notion 记一行，回个人/McKinsey 机改 core。
- **彻底切换**到纯净新结构（AGENTS.md 由内核生成、rules 走 symlink）：
  留到本 study 结束、下个 study 的 Day-1 从零开始做，不要 mid-study 折腾。

## 不要做的事

- 不要删旧 workspace 的任何目录
- 不要动旧 workspace 的 git origin
- 不要在收编阶段合并/替换手工魔改的 AGENTS.md——它是实战版，等 study 结束再
  把其中的通用规则回流进 adapters
