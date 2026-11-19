# Per-run check list — 学术格式与模板适配

Channel: `challenge-96263d10`. One pass through this list per run; every line is a question with a
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

- [ ] 实际效果 / 任务完成度 (15): 是否真正把一份真实稿件按目标模板改到可交付，而不是只改了几处看得见的格式。
- [ ] 实际效果 / 结果正确性 (15): 是否真正把一份真实稿件按目标模板改到可交付，而不是只改了几处看得见的格式。
- [ ] 实际效果 / 结果完整性 (5): 是否真正把一份真实稿件按目标模板改到可交付，而不是只改了几处看得见的格式。
- [ ] 实际效果 / 结果可核验性 (5): 是否真正把一份真实稿件按目标模板改到可交付，而不是只改了几处看得见的格式。
- [ ] 使用增益 / 质量增益 (15): 在相同输入稿件、相同目标模板、相同工具权限下，加载 Skill、插件或工作流后相比不加载的基础 Agent 是否提升适配质量。
- [ ] 使用增益 / 效率增益 (5): 在相同输入稿件、相同目标模板、相同工具权限下，加载 Skill、插件或工作流后相比不加载的基础 Agent 是否提升适配质量。
- [ ] 使用增益 / 增益可验证性 (5): 在相同输入稿件、相同目标模板、相同工具权限下，加载 Skill、插件或工作流后相比不加载的基础 Agent 是否提升适配质量。
- [ ] 创新增益 / 新增能力 (5): 是否形成基础 Agent 或现有排版工具不具备、或难以稳定实现的能力，例如从模板文件反推检查项清单、图表题注与交叉引用联动更新、转换后自动比对保真度。
- [ ] 创新增益 / 方法改进 (5): 是否形成基础 Agent 或现有排版工具不具备、或难以稳定实现的能力，例如从模板文件反推检查项清单、图表题注与交叉引用联动更新、转换后自动比对保真度。
- [ ] 创新增益 / 创新证据 (5): 是否形成基础 Agent 或现有排版工具不具备、或难以稳定实现的能力，例如从模板文件反推检查项清单、图表题注与交叉引用联动更新、转换后自动比对保真度。
- [ ] 可靠体验 / 调用与易用性 (3): Agent 是否能正确触发和调用，用户是否能按说明完成一次完整适配。
- [ ] 可靠体验 / 运行稳定性 (4): Agent 是否能正确触发和调用，用户是否能按说明完成一次完整适配。
- [ ] 可靠体验 / 异常处理 (3): Agent 是否能正确触发和调用，用户是否能按说明完成一次完整适配。
- [ ] 生态贡献 / 文档完整性 (3): 使用说明、依赖环境、支持模板范围、示例、限制与维护信息是否齐全。
- [ ] 生态贡献 / 资源可复用性 (4): 使用说明、依赖环境、支持模板范围、示例、限制与维护信息是否齐全。
- [ ] 生态贡献 / 分享推广价值 (3): 使用说明、依赖环境、支持模板范围、示例、限制与维护信息是否齐全。
