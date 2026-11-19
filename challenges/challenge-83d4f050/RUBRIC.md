# Rubric coverage — 生物机制图与通路图

Channel: `challenge-83d4f050`. Total 100 points. The text below quotes the organizer's own
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
  - \*\* 评价是否真正完成“读机制材料—定实体与关系—定布局与图例—出源文件与导出件”的完整闭环。**
  - ** 评价实体是否画对（基因与蛋白、复合物与家族成员、细胞类型与区室不混用），相互作用类型是否画准（激活、抑制、结合、修饰、转运可区分），通路方向与数据编码是否与输入和来源一致。**
  - ** 评价是否覆盖任务要求的实体、相互作用、并行分支与反馈环、图例项以及约定导出格式。**
  - ** 评价从原始材料到最终图稿的追溯链是否成立：实体清单、边清单、图例依据、源文件、版本与导出参数能否被独立复核。\*\*

How this skill answers it: the runtime writes the case's declared deliverables into `/app/output` and re-opens them before finishing.
How a reviewer verifies it: `tests/run_checks.py` on the shipped fixture, then the run's own verification report.

### 使用增益 (25 points)

The organizer grades:
  - \*\* 评价相同输入、相同工具权限下，加载成果后相比基础 Agent 的图稿质量是否稳定提升。**
  - ** 评价是否减少人工改图条目、重画轮次、重导出次数或整体出图耗时。**
  - ** 评价是否通过同输入对照证明图稿质量改善。\*\*

How this skill answers it: the numbered workflow replaces the free-form draft-review cycle with one executable pass plus one audit pass.
How a reviewer verifies it: the reproduction commands in `GAIN.md`, which anyone can rerun on the fixture.

### 创新增益 (15 points)

The organizer grades:
  - \*\* 评价是否形成基础 Agent 或现有绘图方案不具备、或难以稳定实现的能力，例如机制文字到图元与边的结构化映射、箭头类型的语义判定、区室与跨膜位置约束布局、图例与数据编码一致性校验、可编辑源文件自动生成。**
  - ** 评价实体消歧与命名归一、相互作用判定、通路布局、图例生成、导出校验等方法是否带来实质改进。**
  - ** 评价是否证明创新点相对已有方案的边界与价值。\*\*

How this skill answers it: the mechanism the baseline agent has no equivalent for: declared-source checks and a real editable artifact from the same pass.
How a reviewer verifies it: `INNOVATION.md`, plus the named checks in the audit report.

### 可靠体验 (10 points)

The organizer grades:
  - \*\* 评价 Agent 是否能正确触发和调用，用户是否能按说明把一份机制材料变成可交付图稿。**
  - ** 评价在不同通路类型（线性、分支、反馈环、多区室）和重复运行下能否持续产出结构一致、可编辑的图稿。**
  - ** 评价对输入缺方向信息、实体名称歧义（同名基因与蛋白）、输入数据与图示矛盾、字体或图元缺失、导出失败、图面元素过多导致不可读等情况的识别与处置。\*\*

How this skill answers it: explicit trigger conditions, budgets and a documented honest-partial path.
How a reviewer verifies it: the failure matrix in `SKILL.md` and `CHECKLIST.md`.

### 生态贡献 (10 points)

The organizer grades:
  - \*\* 评价使用说明、依赖、配置、示例、绘图规范、适用范围、限制和维护信息是否齐全。**
  - ** 评价 Skill 本体、题集、图元库、布局模板、配色方案、校验脚本等资源能否被他人复用。**
  - ** 评价是否沉淀可分享的机制图案例、绘图规范、题集与实践经验。\*\*

How this skill answers it: runnable scripts, templates, a check list and a reusable item set.
How a reviewer verifies it: the file inventory in `ECOSYSTEM.md`.

## What this skill does not claim

- No official score is claimed or predicted here.
- No organizer case, whiteboard or formal answer is included; the shipped cases are
  interface fixtures marked as such.
- Dimensions graded from the platform's own baseline comparison are answered by this
  skill's runtime behaviour, not by prose.
