# 待回流清单（Dell 机上的改进 → core）

> 这些改进目前只活在 Dell 客户机的 workspace clone 里。回流方式：在 Dell 机上**读**，
> 剥掉一切客户名词后在个人/McKinsey 机上重写进 core，然后 push。客户机永不 push。
> 每完成一项就删掉对应条目。

- [ ] **一次性批量提问版 grill-me**：你在 Windsurf 上 customize 的版本（一次问完所有问题
      → 统一回答 → 最多再迭代一轮）。建议做成 `kernel/skills/grill-me-batch/`，
      与第三方多轮版 grill-me 并存：按 prompt 计费的工具用 batch 版，按 token 计费的用多轮版。
- [ ] **Windsurf 版 AGENTS.md 的硬规则**：你在 Dell 上加进 agents.md 的强制性措辞里，
      凡是与客户无关的（如工具行为约束），逐条评估进 `adapters/windsurf/rules/` 还是
      HANDBOOK。patch 工具那条已经预制（core-patch-tool.md），对照你的原版措辞校准。
- [ ] **摊平后的 skills 改动**：Dell 上被你改过的 skill 正文（相对 GitHub 原版的 diff），
      通用部分回流到 `kernel/skills/<对应名>/SKILL.md`。
- [ ] **Handoff skill 的 Windsurf 适配经验**：交接文档的实际格式/瘦身取舍如果和
      kernel 版有出入，以 Dell 实战版为准回流。
- [ ] **Windsurf 全局 skills 目录路径**：确认后回填 `install.sh` 的 `WINDSURF_SKILLS_DIR`
      与 `adapters/windsurf/HANDBOOK.md` §6。
- [ ] **`.git/info/exclude` 实验结果**：验证 Cascade 是否放行（HANDBOOK §4），
      结果无论正反都回流更新该小节。
- [ ] **Dell 机启用 journal + close-out**：把 core-journal.md 装进 .windsurf/rules/（重跑
      install.sh 即可），然后跑一次 `/close-out` 首次 bootstrap（decisions 大清理 +
      design.md 反向生成，挑 credit 富余的日子）。
- [ ] **EM 书面许可**：SharePoint bundle 通道的合规确认，拿到后在 Day-1 checklist §D 打勾模式固化。
