# Per-run check list — 公式解析与数学推理

Channel: `challenge-7c37626c`. One pass through this list per run; every line is a question with a
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

- [ ] 实际效果 / 任务完成度 (15): 是否真的把给定的公式图像或 PDF 片段转成可用的结构化表达，并交付变量表与推导说明，而不是只贴一段 LaTeX。
- [ ] 实际效果 / 结果正确性 (15): 是否真的把给定的公式图像或 PDF 片段转成可用的结构化表达，并交付变量表与推导说明，而不是只贴一段 LaTeX。
- [ ] 实际效果 / 结果完整性 (5): 是否真的把给定的公式图像或 PDF 片段转成可用的结构化表达，并交付变量表与推导说明，而不是只贴一段 LaTeX。
- [ ] 实际效果 / 结果可核验性 (5): 是否真的把给定的公式图像或 PDF 片段转成可用的结构化表达，并交付变量表与推导说明，而不是只贴一段 LaTeX。
- [ ] 使用增益 / 质量增益 (15): 相同条件下加载 Skill、插件或工作流后，相比不加载的基础 Agent 是否改善公式解析与解释质量。
- [ ] 使用增益 / 效率增益 (5): 相同条件下加载 Skill、插件或工作流后，相比不加载的基础 Agent 是否改善公式解析与解释质量。
- [ ] 使用增益 / 增益可验证性 (5): 相同条件下加载 Skill、插件或工作流后，相比不加载的基础 Agent 是否改善公式解析与解释质量。
- [ ] 创新增益 / 新增能力 (5): 是否形成基础 Agent 或现有方案不具备、或难以稳定实现的公式解析与核验能力。
- [ ] 创新增益 / 方法改进 (5): 是否形成基础 Agent 或现有方案不具备、或难以稳定实现的公式解析与核验能力。
- [ ] 创新增益 / 创新证据 (5): 是否形成基础 Agent 或现有方案不具备、或难以稳定实现的公式解析与核验能力。
- [ ] 可靠体验 / 调用与易用性 (3): Agent 是否能正确触发和调用，用户是否能按说明看懂一次完整的公式解析。
- [ ] 可靠体验 / 运行稳定性 (4): Agent 是否能正确触发和调用，用户是否能按说明看懂一次完整的公式解析。
- [ ] 可靠体验 / 异常处理 (3): Agent 是否能正确触发和调用，用户是否能按说明看懂一次完整的公式解析。
- [ ] 生态贡献 / 文档完整性 (3): 使用说明、依赖、配置、示例、符号约定、适用范围、限制和维护信息是否齐全。
- [ ] 生态贡献 / 资源可复用性 (4): 使用说明、依赖、配置、示例、符号约定、适用范围、限制和维护信息是否齐全。
- [ ] 生态贡献 / 分享推广价值 (3): 使用说明、依赖、配置、示例、符号约定、适用范围、限制和维护信息是否齐全。
