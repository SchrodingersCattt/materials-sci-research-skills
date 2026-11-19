# Per-run check list — 论文结构与逻辑优化

Channel: `challenge-8021aacb`. One pass through this list per run; every line is a question with a
yes/no answer, so a run can be reviewed without reading the whole skill.

## Before writing

- [ ] the case's `output_contract` was read field by field and copied, not paraphrased
- [ ] every supplied material file was opened, not inferred from its name
- [ ] the deliverable paths the contract names are known

## While writing

- [ ] each claim carries a source locator
- [ ] each number is either a declared source value or a declared compatible-unit
      calculation
- [ ] observation and interpretation are in different sentences
- [ ] missing material is written as "not reported" and kept out of the arithmetic

## After writing

- [ ] the audit ran and exited 0, or its exit-2 report was repaired and rerun
- [ ] the artifact was built and then re-opened and verified against the source text
- [ ] `result.json` keeps the original `case_id` and every original contract field
- [ ] the run's own limits are written down, including a missing renderer

## Rubric points covered by this list

- [ ] 实际效果 / 任务完成度 (15): 是否真的对一篇完整稿件完成结构诊断，并交付作者可直接执行的修改方案。
- [ ] 实际效果 / 结果正确性 (15): 是否真的对一篇完整稿件完成结构诊断，并交付作者可直接执行的修改方案。
- [ ] 实际效果 / 结果完整性 (5): 是否真的对一篇完整稿件完成结构诊断，并交付作者可直接执行的修改方案。
- [ ] 实际效果 / 结果可核验性 (5): 是否真的对一篇完整稿件完成结构诊断，并交付作者可直接执行的修改方案。
- [ ] 使用增益 / 质量增益 (15): 在相同稿件、相同任务要求下，加载成果后结构诊断与修改方案是否优于基础 Agent。
- [ ] 使用增益 / 效率增益 (5): 在相同稿件、相同任务要求下，加载成果后结构诊断与修改方案是否优于基础 Agent。
- [ ] 使用增益 / 增益可验证性 (5): 在相同稿件、相同任务要求下，加载成果后结构诊断与修改方案是否优于基础 Agent。
- [ ] 创新增益 / 新增能力 (5): 是否形成基础 Agent 或现有写作工具不具备的结构级能力，例如论点—论据映射、跨章节冗余检测、结论与数据范围的边界比对。
- [ ] 创新增益 / 方法改进 (5): 是否形成基础 Agent 或现有写作工具不具备的结构级能力，例如论点—论据映射、跨章节冗余检测、结论与数据范围的边界比对。
- [ ] 创新增益 / 创新证据 (5): 是否形成基础 Agent 或现有写作工具不具备的结构级能力，例如论点—论据映射、跨章节冗余检测、结论与数据范围的边界比对。
- [ ] 可靠体验 / 调用与易用性 (3): Agent 是否能正确触发，作者是否能按说明完成一次完整结构诊断。
- [ ] 可靠体验 / 运行稳定性 (4): Agent 是否能正确触发，作者是否能按说明完成一次完整结构诊断。
- [ ] 可靠体验 / 异常处理 (3): Agent 是否能正确触发，作者是否能按说明完成一次完整结构诊断。
- [ ] 生态贡献 / 文档完整性 (3): 使用说明、依赖、配置、示例、适用范围、限制和维护信息是否齐全。
- [ ] 生态贡献 / 资源可复用性 (4): 使用说明、依赖、配置、示例、适用范围、限制和维护信息是否齐全。
- [ ] 生态贡献 / 分享推广价值 (3): 使用说明、依赖、配置、示例、适用范围、限制和维护信息是否齐全。
