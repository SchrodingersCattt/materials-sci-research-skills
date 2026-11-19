# Rubric coverage — 科研示意图生成与编辑

Channel: `challenge-98e5a474`. Total 100 points. The text below quotes the organizer's own
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
  - \*\* 评价是否从来源材料走通「材料→图稿→导出」，产出科学上成立、可继续编辑的示意图，而非套模板的插画。**
  - ** 评价实体、关系、方向、层级、相对比例与数值单位是否与来源或金标准一致。**
  - ** 评价是否覆盖三类示意图要素与图例、标注、单位、子图编号等必要图面元素。**
  - ** 评价图稿与来源材料、金标准的对应关系能否被独立复核。\*\*

How this skill answers it: the runtime writes the case's declared deliverables into `/app/output` and re-opens them before finishing.
How a reviewer verifies it: `tests/run_checks.py` on the shipped fixture, then the run's own verification report.

### 使用增益 (25 points)

The organizer grades:
  - \*\* 评价相同输入、画布与导出参数下，加载成果后图稿的科学正确性、图面规范与可编辑性是否稳定提升。**
  - ** 评价是否减少从材料到可投稿图稿的人工修改量、返工轮次与重复绘图动作。**
  - ** 评价是否通过公平对照证明质量或效率改善。\*\*

How this skill answers it: the numbered workflow replaces the free-form draft-review cycle with one executable pass plus one audit pass.
How a reviewer verifies it: the reproduction commands in `GAIN.md`, which anyone can rerun on the fixture.

### 创新增益 (15 points)

The organizer grades:
  - \*\* 评价是否形成基础 Agent 或现成绘图工具不具备的能力，如从文字描述解析实体关系、数据表驱动图例重绘、导出前合规检查。**
  - ** 评价实体抽取、关系建模、布局约束、图例映射与导出检查等方法是否有实质改进。**
  - ** 评价创新点相对已有方案与绘图工具的边界和价值是否被证明。\*\*

How this skill answers it: the mechanism the baseline agent has no equivalent for: declared-source checks and a real editable artifact from the same pass.
How a reviewer verifies it: `INNOVATION.md`, plus the named checks in the audit report.

### 可靠体验 (10 points)

The organizer grades:
  - \*\* 评价 Agent 能否正确触发，用户能否按说明完成一次从材料到源文件与导出件的出图。**
  - ** 评价不同图型、不同来源材料与重复运行下能否持续产出可用图稿。**
  - ** 评价来源缺失、描述矛盾、数据与图例不符、字体缺失、导出失败时能否识别并合理处置。\*\*

How this skill answers it: explicit trigger conditions, budgets and a documented honest-partial path.
How a reviewer verifies it: the failure matrix in `SKILL.md` and `CHECKLIST.md`.

### 生态贡献 (10 points)

The organizer grades:
  - \*\* 评价说明、依赖与字体安装、导出参数、示例、边界和维护信息是否齐全。**
  - ** 评价题集、金标准图稿、模板、配色与图例规范、导出预设能否被直接复用。**
  - ** 评价是否沉淀可分享的案例、题集、图例规范与实践经验。\*\*

How this skill answers it: runnable scripts, templates, a check list and a reusable item set.
How a reviewer verifies it: the file inventory in `ECOSYSTEM.md`.

## What this skill does not claim

- No official score is claimed or predicted here.
- No organizer case, whiteboard or formal answer is included; the shipped cases are
  interface fixtures marked as such.
- Dimensions graded from the platform's own baseline comparison are answered by this
  skill's runtime behaviour, not by prose.
