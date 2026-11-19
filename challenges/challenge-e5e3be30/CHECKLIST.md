# Per-run check list — 文献证据溯源与事实核验

Channel: `challenge-e5e3be30`. One pass through this list per run; every line is a question with a
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

- [ ] 实际效果 / 任务完成度 (15): 是否把待核验的科研论断真正落到可判定的证据上，交付能直接使用的证据卡片或核验报告。
- [ ] 实际效果 / 结果正确性 (15): 是否把待核验的科研论断真正落到可判定的证据上，交付能直接使用的证据卡片或核验报告。
- [ ] 实际效果 / 结果完整性 (5): 是否把待核验的科研论断真正落到可判定的证据上，交付能直接使用的证据卡片或核验报告。
- [ ] 实际效果 / 结果可核验性 (5): 是否把待核验的科研论断真正落到可判定的证据上，交付能直接使用的证据卡片或核验报告。
- [ ] 使用增益 / 质量增益 (15): 在相同文献、相同论断、相同工具权限下，加载 Skill 后误支持（把主题相关当支持）与漏检（真支持未被识别）是否下降。
- [ ] 使用增益 / 效率增益 (5): 在相同文献、相同论断、相同工具权限下，加载 Skill 后误支持（把主题相关当支持）与漏检（真支持未被识别）是否下降。
- [ ] 使用增益 / 增益可验证性 (5): 在相同文献、相同论断、相同工具权限下，加载 Skill 后误支持（把主题相关当支持）与漏检（真支持未被识别）是否下降。
- [ ] 创新增益 / 新增能力 (5): 是否形成基础 Agent 或现有方案不具备、或难以稳定实现的段落级定位、四级支持度判定、冲突并列与不确定性表达能力。
- [ ] 创新增益 / 方法改进 (5): 是否形成基础 Agent 或现有方案不具备、或难以稳定实现的段落级定位、四级支持度判定、冲突并列与不确定性表达能力。
- [ ] 创新增益 / 创新证据 (5): 是否形成基础 Agent 或现有方案不具备、或难以稳定实现的段落级定位、四级支持度判定、冲突并列与不确定性表达能力。
- [ ] 可靠体验 / 调用与易用性 (3): Agent 能否在"帮我核验这句话"这类请求下正确触发，用户能否按说明完成一次从论断到证据卡片的核验，以及能否识别不属于本课题的请求。
- [ ] 可靠体验 / 运行稳定性 (4): Agent 能否在"帮我核验这句话"这类请求下正确触发，用户能否按说明完成一次从论断到证据卡片的核验，以及能否识别不属于本课题的请求。
- [ ] 可靠体验 / 异常处理 (3): Agent 能否在"帮我核验这句话"这类请求下正确触发，用户能否按说明完成一次从论断到证据卡片的核验，以及能否识别不属于本课题的请求。
- [ ] 生态贡献 / 文档完整性 (3): 使用说明、四级判定定义、输入输出字段、依赖、配置、示例、适用范围、限制和维护信息是否齐全。
- [ ] 生态贡献 / 资源可复用性 (4): 使用说明、四级判定定义、输入输出字段、依赖、配置、示例、适用范围、限制和维护信息是否齐全。
- [ ] 生态贡献 / 分享推广价值 (3): 使用说明、四级判定定义、输入输出字段、依赖、配置、示例、适用范围、限制和维护信息是否齐全。
