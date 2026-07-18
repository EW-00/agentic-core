---
trigger: always_on
---

# Doc-with-code（文档与代码同一次变更）

任何改动 optimization formulation、数据契约（schema/接口字段）、或核心业务逻辑的实现，
必须在**同一次修改**中同步更新对应 repo 的 `docs/design.md` 对应小节（现状描述），
否则该任务视为未完成。文档更新和代码改动必须出现在同一个 diff 里。

如果本次改动没有对应文档，先在回复末尾提示一句"该模块暂无文档，是否建立"，不要擅自新建长文档。
