# Rubric coverage — 写作19｜思维导图

Channel: `challenge-9313ad0a`. Total 100 points. The text below quotes the organizer's own
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
  - 是否理解导图用途、目标读者、材料范围和交付要求，并交付可打开、可读、可继续编辑的导图及必要说明。
  - 节点内容是否忠于材料、关系方向是否正确、证据是否挂在对应节点上，有无材料中不存在的连接。
  - 是否覆盖任务要求的关键概念、问题、方法、证据、结论、任务和风险，以及必要的层级分支。
  - 关键节点与关系能否回到原始材料、页码、段落、引用或任务记录。

How this skill answers it: the runtime writes the case's declared deliverables into `/app/output` and re-opens them before finishing.
How a reviewer verifies it: `tests/run_checks.py` on the shipped fixture, then the run's own verification report.

### 使用增益 (25 points)

The organizer grades:
  - 相同材料、相同输出格式和相同预算下，加载 Skill、插件或工作流后相比基础 Agent 是否提升导图质量。
  - 是否减少整理、核对、改图、返工与沟通成本，包括运行耗时、人工修改量和重复操作。
  - 是否通过公平对照证明质量或效率改善。

How this skill answers it: the numbered workflow replaces the free-form draft-review cycle with one executable pass plus one audit pass.
How a reviewer verifies it: the reproduction commands in `GAIN.md`, which anyone can rerun on the fixture.

### 创新增益 (15 points)

The organizer grades:
  - 是否形成基础 Agent 或现有方案不具备、或难以稳定实现的能力。
  - 材料抽取、主题归并、层级设计、关系判定与布局策略是否带来实质改进。
  - 是否证明创新点相对已有方案的边界和价值。

How this skill answers it: the mechanism the baseline agent has no equivalent for: declared-source checks and a real editable artifact from the same pass.
How a reviewer verifies it: `INNOVATION.md`, plus the named checks in the audit report.

### 可靠体验 (10 points)

The organizer grades:
  - Agent 是否能正确触发和调用，用户是否能按说明完成一次从材料到导图的完整流程。
  - 在不同材料类型、不同长度和重复运行下能否持续产出可读可改的导图。
  - 对材料缺失、格式不支持、信息自相矛盾、节点规模爆炸、权限不足等情况的识别与处置能力。

How this skill answers it: explicit trigger conditions, budgets and a documented honest-partial path.
How a reviewer verifies it: the failure matrix in `SKILL.md` and `CHECKLIST.md`.

### 生态贡献 (10 points)

The organizer grades:
  - 使用说明、节点与关系定义、输出格式、依赖、配置、示例、适用范围、限制和维护信息是否齐全。
  - Skill 本体、脚本、题集、参考结构、导图模板和校验工具能否被他人直接复用。
  - 是否沉淀可分享的案例、Benchmark、整理方法和真实应用价值。

How this skill answers it: runnable scripts, templates, a check list and a reusable item set.
How a reviewer verifies it: the file inventory in `ECOSYSTEM.md`.

## What this skill does not claim

- No official score is claimed or predicted here.
- No organizer case, whiteboard or formal answer is included; the shipped cases are
  interface fixtures marked as such.
- Dimensions graded from the platform's own baseline comparison are answered by this
  skill's runtime behaviour, not by prose.
