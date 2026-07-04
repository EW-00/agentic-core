# Git Boundaries（新架构版）

一句话：**唯一被 git 管理并跨机同步的是 `core/` 自己；workspace 是本地物化产物；
项目代码 repo 各自独立；三者永不嵌套污染。**

## 三层边界

| 层 | 位置 | git 状态 | 同步方式 |
|---|---|---|---|
| L0+L1 core | `workspace/core/` | 独立 repo（GitHub: EW-00/agentic-core） | git pull（客户机 pull-only）|
| L2 workspace | `workspace/` 根 | **哨兵 repo**：`.git/info/exclude='*'`，永不 commit，无 .gitignore | 不同步；STUDY.md 换 study 重写 |
| 项目代码 | `workspace/projects/<study>/repos/<repo>/` | 各自独立 repo（客户 GitLab 等） | 各自的 remote；应急走 scripts/bundle-out |

## 为什么根目录是"哨兵 repo"而不是普通 repo / 无 repo

- 普通 repo + `.gitignore: /projects/*`（旧方案）：Windsurf Cascade 拒改被 ignore 的文件（已知 bug，开关无效）。
- 完全无 repo：编辑器 SCM 失去锚定，多个嵌套 repo 的改动混排，review 困难（实测不适）。
- 哨兵 repo：`git init` + `.git/info/exclude` 写 `*`——git 眼里永远干净（badge 0），
  Cascade 找不到任何 `.gitignore` 文件，编辑器有锚定 repo。三方需求同时满足。
  ⚠️ 前提待 Dell 验证：Cascade 不解析 `info/exclude`（见 adapters/windsurf/HANDBOOK.md §4）。

## 内容路由（放哪一层）

- 换 study / 换工具仍成立 → `core/`（kernel 或对应 adapter），可回流 GitHub
- 只对本 study 成立 → `STUDY.md` / `projects/<study>/docs/`，只活在本机
- 单 repo 的工程语义 → repo 自己的 README/docs，跟 repo 的 git 走
- 笔记/草稿/待办 → Notion（跨四机的唯一笔记层），repo 只收蒸馏后的产物

## 子 code repo 的 .gitignore baseline

Python repo 至少包含：`.venv/`、`__pycache__/`、`.pytest_cache/`、`.mypy_cache/`、
`.ruff_cache/`、`.ipynb_checkpoints/`、`.env*`、`build/`、`dist/`、`*.egg-info/`、
`data/`、`outputs/`、`tmp/`、`logs/`（notebook/research repo 保留 notebook，按需白名单
`data/sample/`）。这些 ignore 在**子 repo 内部**，不影响 Cascade 对 workspace 其他文件的访问。
