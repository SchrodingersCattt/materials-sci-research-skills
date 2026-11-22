# Per-run check list — 学术格式与模板适配

Channel: `challenge-96263d10`. One pass through this list per run; every line is a question with a
yes/no answer, so a run can be reviewed without reading the whole skill.

## Before writing

- [ ] the case's `output_contract` was read field by field and copied, not paraphrased
- [ ] every supplied material file was opened, not inferred from its name
- [ ] the deliverable paths the contract names are known

## While adapting

- [ ] each claim carries a source locator
- [ ] each number is either a declared source value or a declared compatible-unit
      calculation
- [ ] observation and interpretation are in different sentences
- [ ] missing material is written as "not reported" and kept out of the arithmetic
- [ ] every mapped template style has a definition in the output (no dangling `pStyle`)
- [ ] the template's own convention for caption placement and reference order was read, not assumed

## After writing

- [ ] the audit ran and exited 0, or its exit-2 report was repaired and rerun
- [ ] the artifact was built and then re-opened and verified against the source text
- [ ] the apparatus audit ran: every caption's declared number matches its position in the
      sequence of its family, every in-text reference resolves, and the reference list kept its
      entries (or the remaining defects are named with their locator)
- [ ] a renumber, if one was needed, carried the in-text references with the caption number and
      the renumbered file is the deliverable
- [ ] `result.json` keeps the original `case_id` and every original contract field
- [ ] the run's own limits are written down, including a missing renderer and every
      `observations` entry the template did not settle

## Rubric points covered by this list

- [ ] 实际效果 / 任务完成度 (15): 是否真正把一份真实稿件按目标模板改到可交付，而不是只改了几处看得见的格式。
- [ ] 实际效果 / 结果正确性 (15): 格式规格与内容是否同时正确——字号、行距、页边距、栏数、题注位置、参考文献样式是否符合目标模板，同时正文、图表、公式、引用、批注是否被错误改动。
- [ ] 实际效果 / 结果完整性 (5): 模板要求的检查项与原稿的内容单元是否都被覆盖。
- [ ] 实际效果 / 结果可核验性 (5): 他人能否按提交材料复现“从输入件到成品”的过程并核对每一项。
- [ ] 使用增益 / 质量增益 (15): 在相同输入稿件、相同目标模板、相同工具权限下，加载 Skill、插件或工作流后相比不加载的基础 Agent 是否提升适配质量。
- [ ] 使用增益 / 效率增益 (5): 是否减少逐项核对、重复排版、试错导出与人工返工。
- [ ] 使用增益 / 增益可验证性 (5): 是否通过公平对照证明质量或效率改善。
- [ ] 创新增益 / 新增能力 (5): 是否形成基础 Agent 或现有排版工具不具备、或难以稳定实现的能力，例如从模板文件反推检查项清单、图表题注与交叉引用联动更新、转换后自动比对保真度。
- [ ] 创新增益 / 方法改进 (5): 模板解析、样式映射、内容锚定、转换与导出校验的方法是否带来实质改进。
- [ ] 创新增益 / 创新证据 (5): 是否证明创新点相对已有方案的边界和价值。
- [ ] 可靠体验 / 调用与易用性 (3): Agent 是否能正确触发和调用，用户是否能按说明完成一次完整适配。
- [ ] 可靠体验 / 运行稳定性 (4): 在不同模板类型、不同稿件长度、不同运行环境和重复运行下能否持续产出可用文件。
- [ ] 可靠体验 / 异常处理 (3): 对模板缺失或版本不明、字体缺失、样式冲突、转换失败、内容无法保真等情况的识别与处置能力。
- [ ] 生态贡献 / 文档完整性 (3): 使用说明、依赖环境、支持模板范围、示例、限制与维护信息是否齐全。
- [ ] 生态贡献 / 资源可复用性 (4): Skill 本体、检查项清单、样式映射脚本、样例输入输出能否被他人复用。
- [ ] 生态贡献 / 分享推广价值 (3): 是否沉淀可分享的模板检查清单、案例、实践经验和真实应用价值。
