# Per-run check list — 阅读02｜科研图表解析

Channel: `challenge-f35e4ca5`. One pass through this list per run; every line is a question with a
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

- [ ] 实际效果 / 任务完成度 (15): 是否真的把一张或一组科研图表读成可用的结构化结果，而不是给一段像总结的文字。
- [ ] 实际效果 / 结果正确性 (15): 是否真的把一张或一组科研图表读成可用的结构化结果，而不是给一段像总结的文字。
- [ ] 实际效果 / 结果完整性 (5): 是否真的把一张或一组科研图表读成可用的结构化结果，而不是给一段像总结的文字。
- [ ] 实际效果 / 结果可核验性 (5): 是否真的把一张或一组科研图表读成可用的结构化结果，而不是给一段像总结的文字。
- [ ] 使用增益 / 质量增益 (15): 相同图表、相同任务下，加载 Skill 后相比基础 Agent 在读数准确率、元素还原和解释可靠性上的提升。
- [ ] 使用增益 / 效率增益 (5): 相同图表、相同任务下，加载 Skill 后相比基础 Agent 在读数准确率、元素还原和解释可靠性上的提升。
- [ ] 使用增益 / 增益可验证性 (5): 相同图表、相同任务下，加载 Skill 后相比基础 Agent 在读数准确率、元素还原和解释可靠性上的提升。
- [ ] 创新增益 / 新增能力 (5): 是否形成基础 Agent 不具备的读图能力，例如坐标轴类型判别、像素到数据坐标的标定、图例与系列自动匹配、多子图关联、误差线语义识别。
- [ ] 创新增益 / 方法改进 (5): 是否形成基础 Agent 不具备的读图能力，例如坐标轴类型判别、像素到数据坐标的标定、图例与系列自动匹配、多子图关联、误差线语义识别。
- [ ] 创新增益 / 创新证据 (5): 是否形成基础 Agent 不具备的读图能力，例如坐标轴类型判别、像素到数据坐标的标定、图例与系列自动匹配、多子图关联、误差线语义识别。
- [ ] 可靠体验 / 调用与易用性 (3): Agent 能否正确触发，用户能否按说明完成一次从上传图表到拿到结构化数据的完整解析。
- [ ] 可靠体验 / 运行稳定性 (4): Agent 能否正确触发，用户能否按说明完成一次从上传图表到拿到结构化数据的完整解析。
- [ ] 可靠体验 / 异常处理 (3): Agent 能否正确触发，用户能否按说明完成一次从上传图表到拿到结构化数据的完整解析。
- [ ] 生态贡献 / 文档完整性 (3): 使用说明、依赖、输入要求、字段定义、误差口径、限制与维护信息是否齐全。
- [ ] 生态贡献 / 资源可复用性 (4): 使用说明、依赖、输入要求、字段定义、误差口径、限制与维护信息是否齐全。
- [ ] 生态贡献 / 分享推广价值 (3): 使用说明、依赖、输入要求、字段定义、误差口径、限制与维护信息是否齐全。
