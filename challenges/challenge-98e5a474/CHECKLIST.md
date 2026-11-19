# Per-run check list — 科研示意图生成与编辑

Channel: `challenge-98e5a474`. One pass through this list per run; every line is a question with a
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

- [ ] 实际效果 / 任务完成度 (15): \*\* 评价是否从来源材料走通「材料→图稿→导出」，产出科学上成立、可继续编辑的示意图，而非套模板的插画。**
- [ ] 实际效果 / 结果正确性 (15): \*\* 评价是否从来源材料走通「材料→图稿→导出」，产出科学上成立、可继续编辑的示意图，而非套模板的插画。**
- [ ] 实际效果 / 结果完整性 (5): \*\* 评价是否从来源材料走通「材料→图稿→导出」，产出科学上成立、可继续编辑的示意图，而非套模板的插画。**
- [ ] 实际效果 / 结果可核验性 (5): \*\* 评价是否从来源材料走通「材料→图稿→导出」，产出科学上成立、可继续编辑的示意图，而非套模板的插画。**
- [ ] 使用增益 / 质量增益 (15): \*\* 评价相同输入、画布与导出参数下，加载成果后图稿的科学正确性、图面规范与可编辑性是否稳定提升。**
- [ ] 使用增益 / 效率增益 (5): \*\* 评价相同输入、画布与导出参数下，加载成果后图稿的科学正确性、图面规范与可编辑性是否稳定提升。**
- [ ] 使用增益 / 增益可验证性 (5): \*\* 评价相同输入、画布与导出参数下，加载成果后图稿的科学正确性、图面规范与可编辑性是否稳定提升。**
- [ ] 创新增益 / 新增能力 (5): \*\* 评价是否形成基础 Agent 或现成绘图工具不具备的能力，如从文字描述解析实体关系、数据表驱动图例重绘、导出前合规检查。**
- [ ] 创新增益 / 方法改进 (5): \*\* 评价是否形成基础 Agent 或现成绘图工具不具备的能力，如从文字描述解析实体关系、数据表驱动图例重绘、导出前合规检查。**
- [ ] 创新增益 / 创新证据 (5): \*\* 评价是否形成基础 Agent 或现成绘图工具不具备的能力，如从文字描述解析实体关系、数据表驱动图例重绘、导出前合规检查。**
- [ ] 可靠体验 / 调用与易用性 (3): \*\* 评价 Agent 能否正确触发，用户能否按说明完成一次从材料到源文件与导出件的出图。**
- [ ] 可靠体验 / 运行稳定性 (4): \*\* 评价 Agent 能否正确触发，用户能否按说明完成一次从材料到源文件与导出件的出图。**
- [ ] 可靠体验 / 异常处理 (3): \*\* 评价 Agent 能否正确触发，用户能否按说明完成一次从材料到源文件与导出件的出图。**
- [ ] 生态贡献 / 文档完整性 (3): \*\* 评价说明、依赖与字体安装、导出参数、示例、边界和维护信息是否齐全。**
- [ ] 生态贡献 / 资源可复用性 (4): \*\* 评价说明、依赖与字体安装、导出参数、示例、边界和维护信息是否齐全。**
- [ ] 生态贡献 / 分享推广价值 (3): \*\* 评价说明、依赖与字体安装、导出参数、示例、边界和维护信息是否齐全。**
