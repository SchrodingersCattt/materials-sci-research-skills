# Rubric coverage — 学术 PPT 生成与编辑

Channel: `ppt-6ad93034`. Total 100 points. The text below quotes the organizer's own
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
  - \*\* 评价是否按任务要求交付一版可打开的学术演示稿，包括页数、页序、每页承担的叙事角色、演讲备注和导出件是否齐备。**
  - ** 评价页面上的数字、图表、图注、引用编号与论文原文、数据表是否一致，有无编造或按印象取整。**
  - ** 评价是否覆盖论文主线、页结构、图表引用、讲解逻辑、模板约束、导出渲染六类要素。**
  - ** 评价源文件、页级金标准、导出件、逐页 diff、运行日志和版本记录能否支撑他人独立复核并复跑。\*\*

How this skill answers it: the runtime writes the case's declared deliverables into `/app/output` and re-opens them before finishing.
How a reviewer verifies it: `tests/run_checks.py` on the shipped fixture, then the run's own verification report.

### 使用增益 (25 points)

The organizer grades:
  - \*\* 评价在相同论文输入、相同模板和相同运行条件下，加载成果后页面质量相比基础 Agent 是否提升。**
  - ** 评价是否减少返工页数、重排次数、导出复查轮次或整体人工修改量。**
  - ** 评价是否通过公平对照证明页面质量或制作效率的改善。\*\*

How this skill answers it: the numbered workflow replaces the free-form draft-review cycle with one executable pass plus one audit pass.
How a reviewer verifies it: the reproduction commands in `GAIN.md`, which anyone can rerun on the fixture.

### 创新增益 (15 points)

The organizer grades:
  - \*\* 评价是否形成基础 Agent 或现有方案不具备、或难以稳定实现的页序规划、模板槽位填充、图表数据绑定与局部编辑能力。**
  - ** 评价内容取舍、页序组织、槽位约束、图表重绘、编辑定位、导出校验等方法是否带来实质改进。**
  - ** 评价是否证明创新点相对科学空间现有能力、开源方案或商用插件的边界和价值。\*\*

How this skill answers it: the mechanism the baseline agent has no equivalent for: declared-source checks and a real editable artifact from the same pass.
How a reviewer verifies it: `INNOVATION.md`, plus the named checks in the audit report.

### 可靠体验 (10 points)

The organizer grades:
  - \*\* 评价 Agent 是否能正确触发和调用，用户是否能按说明用一篇论文生成一版可用稿。**
  - ** 评价在不同论文类型（综述、实验、理论）、不同模板和重复运行下能否持续产出不塌版的成稿。**
  - ** 评价对论文缺图、图片为位图无法取数、模板槽位不足、字体缺失、页数超限、导出失败等情况的识别与处置能力。\*\*

How this skill answers it: explicit trigger conditions, budgets and a documented honest-partial path.
How a reviewer verifies it: the failure matrix in `SKILL.md` and `CHECKLIST.md`.

### 生态贡献 (10 points)

The organizer grades:
  - \*\* 评价使用说明、模板与依赖、参数、示例、页数限制、导出要求和已知问题是否齐全。**
  - ** 评价作品本体、模板、页面骨架、图表重绘脚本、题集与页级金标准能否被他人直接复用。**
  - ** 评价是否沉淀可分享的案例、题集、页面骨架方法与真实应用价值。\*\*

How this skill answers it: runnable scripts, templates, a check list and a reusable item set.
How a reviewer verifies it: the file inventory in `ECOSYSTEM.md`.

## What this skill does not claim

- No official score is claimed or predicted here.
- No organizer case, whiteboard or formal answer is included; the shipped cases are
  interface fixtures marked as such.
- Dimensions graded from the platform's own baseline comparison are answered by this
  skill's runtime behaviour, not by prose.
