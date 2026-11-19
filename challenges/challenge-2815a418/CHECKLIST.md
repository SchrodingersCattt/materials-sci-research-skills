# Per-run check list — 审稿回复与论文修改

Channel: `challenge-2815a418`. One pass through this list per run; every line is a question with a
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

- [ ] 实际效果 / 任务完成度 (15): 是否把一份真实的返修材料（审稿意见清单加指定版本稿件）处理成可直接提交给编辑部的修改稿与逐条回复。
- [ ] 实际效果 / 结果正确性 (15): 是否把一份真实的返修材料（审稿意见清单加指定版本稿件）处理成可直接提交给编辑部的修改稿与逐条回复。
- [ ] 实际效果 / 结果完整性 (5): 是否把一份真实的返修材料（审稿意见清单加指定版本稿件）处理成可直接提交给编辑部的修改稿与逐条回复。
- [ ] 实际效果 / 结果可核验性 (5): 是否把一份真实的返修材料（审稿意见清单加指定版本稿件）处理成可直接提交给编辑部的修改稿与逐条回复。
- [ ] 使用增益 / 质量增益 (15): 在相同稿件版本、相同意见清单、相同工具权限下，加载成果后返修交付质量是否稳定提升。
- [ ] 使用增益 / 效率增益 (5): 在相同稿件版本、相同意见清单、相同工具权限下，加载成果后返修交付质量是否稳定提升。
- [ ] 使用增益 / 增益可验证性 (5): 在相同稿件版本、相同意见清单、相同工具权限下，加载成果后返修交付质量是否稳定提升。
- [ ] 创新增益 / 新增能力 (5): 是否形成基础 Agent 不具备、或难以稳定实现的返修处理能力。
- [ ] 创新增益 / 方法改进 (5): 是否形成基础 Agent 不具备、或难以稳定实现的返修处理能力。
- [ ] 创新增益 / 创新证据 (5): 是否形成基础 Agent 不具备、或难以稳定实现的返修处理能力。
- [ ] 可靠体验 / 调用与易用性 (3): Agent 能否在真实返修场景中被正确触发，作者能否按说明完成一次完整返修。
- [ ] 可靠体验 / 运行稳定性 (4): Agent 能否在真实返修场景中被正确触发，作者能否按说明完成一次完整返修。
- [ ] 可靠体验 / 异常处理 (3): Agent 能否在真实返修场景中被正确触发，作者能否按说明完成一次完整返修。
- [ ] 生态贡献 / 文档完整性 (3): 使用说明、输入模板、依赖、示例、边界与维护信息是否齐全。
- [ ] 生态贡献 / 资源可复用性 (4): 使用说明、输入模板、依赖、示例、边界与维护信息是否齐全。
- [ ] 生态贡献 / 分享推广价值 (3): 使用说明、输入模板、依赖、示例、边界与维护信息是否齐全。
