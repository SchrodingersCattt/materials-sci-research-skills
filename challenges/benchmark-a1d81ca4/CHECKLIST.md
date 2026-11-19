# Per-run check list — 文献阅读 Benchmark 与评测工具

Channel: `benchmark-a1d81ca4`. One pass through this list per run; every line is a question with a
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

- [ ] 实际效果 / 任务完成度 (15): 是否真正建成可判分、可复跑的题集与评测流程，而不是交出一份题单加几张截图。
- [ ] 实际效果 / 结果正确性 (15): 是否真正建成可判分、可复跑的题集与评测流程，而不是交出一份题单加几张截图。
- [ ] 实际效果 / 结果完整性 (5): 是否真正建成可判分、可复跑的题集与评测流程，而不是交出一份题单加几张截图。
- [ ] 实际效果 / 结果可核验性 (5): 是否真正建成可判分、可复跑的题集与评测流程，而不是交出一份题单加几张截图。
- [ ] 使用增益 / 质量增益 (15): 在同一题集快照与同一 Agent 版本下，加载成果相比不加载是否提升评测质量。
- [ ] 使用增益 / 效率增益 (5): 在同一题集快照与同一 Agent 版本下，加载成果相比不加载是否提升评测质量。
- [ ] 使用增益 / 增益可验证性 (5): 在同一题集快照与同一 Agent 版本下，加载成果相比不加载是否提升评测质量。
- [ ] 创新增益 / 新增能力 (5): 是否形成基础 Agent 或现有方案不具备、或难以稳定实现的评测基础设施能力。
- [ ] 创新增益 / 方法改进 (5): 是否形成基础 Agent 或现有方案不具备、或难以稳定实现的评测基础设施能力。
- [ ] 创新增益 / 创新证据 (5): 是否形成基础 Agent 或现有方案不具备、或难以稳定实现的评测基础设施能力。
- [ ] 可靠体验 / 调用与易用性 (3): 用户能否按说明跑完一轮评测。
- [ ] 可靠体验 / 运行稳定性 (4): 用户能否按说明跑完一轮评测。
- [ ] 可靠体验 / 异常处理 (3): 用户能否按说明跑完一轮评测。
- [ ] 生态贡献 / 文档完整性 (3): 题卡规范、运行方法、依赖、示例、结果字段与维护信息是否齐全。
- [ ] 生态贡献 / 资源可复用性 (4): 题卡规范、运行方法、依赖、示例、结果字段与维护信息是否齐全。
- [ ] 生态贡献 / 分享推广价值 (3): 题卡规范、运行方法、依赖、示例、结果字段与维护信息是否齐全。
