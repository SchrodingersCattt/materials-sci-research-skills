# Rubric coverage — 学术汇报内容组织

Channel: `challenge-20870c35`. Total 100 points. The text below quotes the organizer's own
scoring points for this channel, so the mapping can be checked against the published
statement rather than against this skill's own claims.

| Dimension | Points | Sub-points | Mechanism in this skill | Verification |
|---|---|---|---|---|
| 实际效果 | 40 | 任务完成度 15 + 结果正确性 15 + 结果完整性 5 + 结果可核验性 5 | the runtime writes the case's declared deliverables into `/app/output` and re-opens them before finishing | `tests/run_checks.py` on the shipped fixture, then the run's own verification report |
| 使用增益 | 25 | 质量增益 15 + 效率增益 5 + 增益可验证性 5 | the numbered workflow replaces the free-form draft-review cycle with one executable pass plus one audit pass | the reproduction commands in `GAIN.md`, which anyone can rerun on the fixture |
| 创新增益 | 15 | 新增能力 5 + 方法改进 5 + 创新证据 5 | the mechanism the baseline agent has no equivalent for: declared-source checks and a real editable artifact from the same pass | `INNOVATION.md`, plus the named checks in the audit report |
| 可靠体验 | 10 | 调用与易用性 3 + 运行稳定性 4 + 异常处理 3 | explicit trigger conditions, budgets and a documented honest-partial path | the failure matrix in `SKILL.md` and `CHECKLIST.md` |
| 生态贡献 | 10 | 文档完整性 3 + 资源可复用性 4 + 分享推广价值 3 | runnable scripts, templates, a check list and a reusable item set | the file inventory in `ECOSYSTEM.md` |

### 实际效果 (40 points)

The organizer grades:
  - \*\* 评价是否真正交付一份可直接上台的汇报材料：报告目标、听众定位、叙事顺序、逐页重点信息与问答准备是否形成闭环。**
  - ** 评价页面上的科学内容、数字与图表引用是否与源材料一致，讲解备注是否与页面结论对应，结论强度是否与证据匹配。**
  - ** 评价是否覆盖论文主线、页结构、图表引用、讲解逻辑、模板约束、导出渲染六个方面。**
  - ** 评价从源材料到成稿的取舍、页级映射、导出链路能否被独立复核。\*\*

How this skill answers it: the runtime writes the case's declared deliverables into `/app/output` and re-opens them before finishing.
How a reviewer verifies it: `tests/run_checks.py` on the shipped fixture, then the run's own verification report.

### 使用增益 (25 points)

The organizer grades:
  - \*\* 评价相同输入、相同听众与时长设定下，加载作品后相比基础 Agent 是否提升汇报内容组织质量。**
  - ** 评价是否减少从论文到可讲稿的人工修改量、返工页数与导出修正次数。**
  - ** 评价是否通过公平对照证明质量或效率改善。\*\*

How this skill answers it: the numbered workflow replaces the free-form draft-review cycle with one executable pass plus one audit pass.
How a reviewer verifies it: the reproduction commands in `GAIN.md`, which anyone can rerun on the fixture.

### 创新增益 (15 points)

The organizer grades:
  - \*\* 评价是否形成基础 Agent 或现有方案不具备、或难以稳定实现的听众适配、页级规划与问答预演能力。**
  - ** 评价叙事模板、内容取舍规则、图表引用绑定、模板约束与导出处理等方法是否带来实质改进。**
  - ** 评价是否证明创新点相对已有方案的边界和价值。\*\*

How this skill answers it: the mechanism the baseline agent has no equivalent for: declared-source checks and a real editable artifact from the same pass.
How a reviewer verifies it: `INNOVATION.md`, plus the named checks in the audit report.

### 可靠体验 (10 points)

The organizer grades:
  - \*\* 评价 Agent 是否能在合适时机触发，用户能否按说明完成一次从源材料到导出文件的完整生成。**
  - ** 评价在不同汇报类型、不同源材料长度与重复运行下能否持续产出可用页面。**
  - ** 评价对论文缺图、图表分辨率不足、公式或符号丢失、模板与内容冲突、字体缺失、导出失败、超时等情况的识别与处置能力。\*\*

How this skill answers it: explicit trigger conditions, budgets and a documented honest-partial path.
How a reviewer verifies it: the failure matrix in `SKILL.md` and `CHECKLIST.md`.

### 生态贡献 (10 points)

The organizer grades:
  - \*\* 评价使用说明、依赖、模板、导出设置、示例、适用范围与维护信息是否齐全。**
  - ** 评价题集、页级金标准、叙事模板、模板文件、导出脚本等资源能否被他人复用。**
  - ** 评价是否沉淀可分享的汇报案例、页级组织方法、问答准备经验与真实应用价值。\*\*

How this skill answers it: runnable scripts, templates, a check list and a reusable item set.
How a reviewer verifies it: the file inventory in `ECOSYSTEM.md`.

## What this skill does not claim

- No official score is claimed or predicted here.
- No organizer case, whiteboard or formal answer is included; the shipped cases are
  interface fixtures marked as such.
- Dimensions graded from the platform's own baseline comparison are answered by this
  skill's runtime behaviour, not by prose.
