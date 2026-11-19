# Rubric coverage — 学术 PPT 模板与格式适配

Channel: `ppt-710fbc72`. Total 100 points. The text below quotes the organizer's own
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
  - \*\* 评价是否把源论文与图表真正套进指定模板，交付可打开、可继续编辑的 pptx 及导出件。**
  - ** 评价页内文字、数字、图号与源材料是否一致，图表是否与数据对应，母版与版式的继承关系是否真实发生，导出件是否与 pptx 渲染一致。**
  - ** 评价是否覆盖从封面到结论的主要页类型，以及论文主线、页结构、图表引用、讲解逻辑、模板约束、导出渲染六类要素。**
  - ** 评价源文件、模板、导出件与逐页偏差记录能否支撑他人独立复跑。\*\*

How this skill answers it: the runtime writes the case's declared deliverables into `/app/output` and re-opens them before finishing.
How a reviewer verifies it: `tests/run_checks.py` on the shipped fixture, then the run's own verification report.

### 使用增益 (25 points)

The organizer grades:
  - \*\* 评价在相同输入材料、相同模板和相同导出环境下，加载作品后相比基础 Agent 的交付质量是否提升。**
  - ** 评价是否减少单册排版耗时、批量返工页数和人工核对工作量。**
  - ** 评价是否通过公平对照证明质量或效率改善。\*\*

How this skill answers it: the numbered workflow replaces the free-form draft-review cycle with one executable pass plus one audit pass.
How a reviewer verifies it: the reproduction commands in `GAIN.md`, which anyone can rerun on the fixture.

### 创新增益 (15 points)

The organizer grades:
  - \*\* 评价是否形成基础 Agent 或现成模板工具不具备、或难以稳定实现的能力。**
  - ** 评价内容与版式的映射、字号与间距规则、图表缩放策略、批量一致性校验等方法是否带来实质改进。**
  - ** 评价是否证明创新点相对已有方案的边界与价值。\*\*

How this skill answers it: the mechanism the baseline agent has no equivalent for: declared-source checks and a real editable artifact from the same pass.
How a reviewer verifies it: `INNOVATION.md`, plus the named checks in the audit report.

### 可靠体验 (10 points)

The organizer grades:
  - \*\* 评价 Agent 能否正确触发，用户能否按说明完成一次“论文+模板→pptx+PDF”的完整流程。**
  - ** 评价在不同模板、不同页数、不同字体环境和重复运行下能否持续产出可用结果。**
  - ** 评价对模板缺版式、占位符缺失、文本框溢出、字体缺失、图表源文件失效、导出失败等情况的识别与处置。\*\*

How this skill answers it: explicit trigger conditions, budgets and a documented honest-partial path.
How a reviewer verifies it: the failure matrix in `SKILL.md` and `CHECKLIST.md`.

### 生态贡献 (10 points)

The organizer grades:
  - \*\* 评价模板准备规范、参数含义、导出设置、字体要求、限制与维护信息是否齐全。**
  - ** 评价作品本体、模板适配层、页级金标准、检查脚本等资源能否被他人直接复用。**
  - ** 评价是否沉淀可分享的案例、题集、规则与实践经验。\*\*

How this skill answers it: runnable scripts, templates, a check list and a reusable item set.
How a reviewer verifies it: the file inventory in `ECOSYSTEM.md`.

## What this skill does not claim

- No official score is claimed or predicted here.
- No organizer case, whiteboard or formal answer is included; the shipped cases are
  interface fixtures marked as such.
- Dimensions graded from the platform's own baseline comparison are answered by this
  skill's runtime behaviour, not by prose.
