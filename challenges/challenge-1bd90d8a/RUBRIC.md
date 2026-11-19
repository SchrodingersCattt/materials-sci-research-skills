# Rubric coverage — 科研数据图表生成与编辑

Channel: `challenge-1bd90d8a`. Total 100 points. The text below quotes the organizer's own
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
  - \*\* 评价是否真正走通“读源数据—出图—按规范调样式—校验标注—交付可编辑文件”的链路，而不是只产出代码片段或示意图。**
  - ** 评价图中呈现的科学内容是否与源数据一致，包括数值与图元高度、坐标轴刻度与单位量级、误差线含义、显著性标记、图例与系列对应，以及基因、蛋白、物种、化合物等科学实体的命名。**
  - ** 评价任务要求的图表要素与六类检查点是否齐备：科学实体、空间关系、数据编码、图例标注、可编辑源文件、导出格式。**
  - ** 评价源数据版本、字段映射、绘图脚本或操作步骤、导出参数、人工修改是否能让他人独立重跑并得到同一张图。\*\*

How this skill answers it: the runtime writes the case's declared deliverables into `/app/output` and re-opens them before finishing.
How a reviewer verifies it: `tests/run_checks.py` on the shipped fixture, then the run's own verification report.

### 使用增益 (25 points)

The organizer grades:
  - \*\* 评价相同输入下加载作品后，相比不加载的基础 Agent，图的科学正确性、标注完整性与可编辑性是否提升。**
  - ** 评价从输入数据到可交付图表的耗时、人工改图条目与重绘轮次是否下降。**
  - ** 评价是否通过同输入、同数据版本与导出参数的公平对照证明改善。\*\*

How this skill answers it: the numbered workflow replaces the free-form draft-review cycle with one executable pass plus one audit pass.
How a reviewer verifies it: the reproduction commands in `GAIN.md`, which anyone can rerun on the fixture.

### 创新增益 (15 points)

The organizer grades:
  - \*\* 评价是否形成基础 Agent 或现有方案不具备、或难以稳定实现的能力，例如图元到源数据的双向映射校验、图例与系列自动对齐、中文标注与字体回退、可编辑矢量或演示文稿导出、期刊模板适配。**
  - ** 评价数据到图元的映射建模、样式规则化、标注校验策略是否带来实质改进。**
  - ** 评价是否证明新增能力相对已有方案（科学空间现有能力、通用绘图库、现成模板）的边界与价值。\*\*

How this skill answers it: the mechanism the baseline agent has no equivalent for: declared-source checks and a real editable artifact from the same pass.
How a reviewer verifies it: `INNOVATION.md`, plus the named checks in the audit report.

### 可靠体验 (10 points)

The organizer grades:
  - \*\* 评价 Agent 是否能正确触发，用户是否能按说明从数据走到成图。**
  - ** 评价在不同数据规模、不同图型和不同字体环境下重复运行能否持续产出可用图。**
  - ** 评价对数据缺列、空值、量级异常、标签过长、字体缺失、导出失败、标注遮挡等情况的识别与处置能力。\*\*

How this skill answers it: explicit trigger conditions, budgets and a documented honest-partial path.
How a reviewer verifies it: the failure matrix in `SKILL.md` and `CHECKLIST.md`.

### 生态贡献 (10 points)

The organizer grades:
  - \*\* 评价使用说明、依赖、字体与模板来源、配置、示例、适用范围与限制是否齐全。**
  - ** 评价题集、金标准图、绘图脚本、样式模板、校验清单与导出预设能否被他人直接复用。**
  - ** 评价是否沉淀可分享的图型案例、样式规范、校验经验与真实应用价值。\*\*

How this skill answers it: runnable scripts, templates, a check list and a reusable item set.
How a reviewer verifies it: the file inventory in `ECOSYSTEM.md`.

## What this skill does not claim

- No official score is claimed or predicted here.
- No organizer case, whiteboard or formal answer is included; the shipped cases are
  interface fixtures marked as such.
- Dimensions graded from the platform's own baseline comparison are answered by this
  skill's runtime behaviour, not by prose.
