---
trigger: model_decision
description: 当用户的 prompt 中提到客户/团队已确认或已同意的决策（feature、formulation 变化、数据口径、约束调整等）时应用本规则
---

# Decision log（append-only 决策日志）

当 prompt 中出现"客户同意了 X""我们决定 Y"这类**已拍板**的决策时：

1. 在完成主任务后，向对应层的 decisions.md **追加一行**（repo 级决策 → 该 repo 的 `docs/decisions.md`；跨 repo / 客户拍板 → `projects/<study>/docs/decisions.md`）：
   `- YYYY-MM-DD：<一句话决策内容>（来源：会议/用户口述）`
2. 只 append，不重写、不整理、不总结历史条目。
3. 如果该文件不存在，先创建（只含标题行）再追加。
4. 拿不准是否算"决策"时，问一句，不要擅自记录。
