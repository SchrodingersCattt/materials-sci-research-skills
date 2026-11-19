# Per-run check list — 科研数据图表生成与编辑

Channel: `challenge-1bd90d8a`. One pass through this list per run; every line is a question with a
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

- [ ] 实际效果 / 任务完成度 (15): \*\* 评价是否真正走通“读源数据—出图—按规范调样式—校验标注—交付可编辑文件”的链路，而不是只产出代码片段或示意图。**
- [ ] 实际效果 / 结果正确性 (15): \*\* 评价是否真正走通“读源数据—出图—按规范调样式—校验标注—交付可编辑文件”的链路，而不是只产出代码片段或示意图。**
- [ ] 实际效果 / 结果完整性 (5): \*\* 评价是否真正走通“读源数据—出图—按规范调样式—校验标注—交付可编辑文件”的链路，而不是只产出代码片段或示意图。**
- [ ] 实际效果 / 结果可核验性 (5): \*\* 评价是否真正走通“读源数据—出图—按规范调样式—校验标注—交付可编辑文件”的链路，而不是只产出代码片段或示意图。**
- [ ] 使用增益 / 质量增益 (15): \*\* 评价相同输入下加载作品后，相比不加载的基础 Agent，图的科学正确性、标注完整性与可编辑性是否提升。**
- [ ] 使用增益 / 效率增益 (5): \*\* 评价相同输入下加载作品后，相比不加载的基础 Agent，图的科学正确性、标注完整性与可编辑性是否提升。**
- [ ] 使用增益 / 增益可验证性 (5): \*\* 评价相同输入下加载作品后，相比不加载的基础 Agent，图的科学正确性、标注完整性与可编辑性是否提升。**
- [ ] 创新增益 / 新增能力 (5): \*\* 评价是否形成基础 Agent 或现有方案不具备、或难以稳定实现的能力，例如图元到源数据的双向映射校验、图例与系列自动对齐、中文标注与字体回退、可编辑矢量或演示文稿导出、期刊模板适配。**
- [ ] 创新增益 / 方法改进 (5): \*\* 评价是否形成基础 Agent 或现有方案不具备、或难以稳定实现的能力，例如图元到源数据的双向映射校验、图例与系列自动对齐、中文标注与字体回退、可编辑矢量或演示文稿导出、期刊模板适配。**
- [ ] 创新增益 / 创新证据 (5): \*\* 评价是否形成基础 Agent 或现有方案不具备、或难以稳定实现的能力，例如图元到源数据的双向映射校验、图例与系列自动对齐、中文标注与字体回退、可编辑矢量或演示文稿导出、期刊模板适配。**
- [ ] 可靠体验 / 调用与易用性 (3): \*\* 评价 Agent 是否能正确触发，用户是否能按说明从数据走到成图。**
- [ ] 可靠体验 / 运行稳定性 (4): \*\* 评价 Agent 是否能正确触发，用户是否能按说明从数据走到成图。**
- [ ] 可靠体验 / 异常处理 (3): \*\* 评价 Agent 是否能正确触发，用户是否能按说明从数据走到成图。**
- [ ] 生态贡献 / 文档完整性 (3): \*\* 评价使用说明、依赖、字体与模板来源、配置、示例、适用范围与限制是否齐全。**
- [ ] 生态贡献 / 资源可复用性 (4): \*\* 评价使用说明、依赖、字体与模板来源、配置、示例、适用范围与限制是否齐全。**
- [ ] 生态贡献 / 分享推广价值 (3): \*\* 评价使用说明、依赖、字体与模板来源、配置、示例、适用范围与限制是否齐全。**
