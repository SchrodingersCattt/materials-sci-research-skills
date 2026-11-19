# Rubric coverage — 审稿回复与论文修改

Channel: `challenge-2815a418`. Total 100 points. The text below quotes the organizer's own
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
  - 是否把一份真实的返修材料（审稿意见清单加指定版本稿件）处理成可直接提交给编辑部的修改稿与逐条回复。
  - 回应中的事实、数据、引用和专业判断是否准确，以及"已修改"的声明是否与稿件真实状态一致。
  - 是否覆盖意见条目、一条意见内的多个子要求，以及回复信与修订稿的格式要求。
  - 回复信中的每一处定位能否在指定版本稿件中被独立核对。

How this skill answers it: the runtime writes the case's declared deliverables into `/app/output` and re-opens them before finishing.
How a reviewer verifies it: `tests/run_checks.py` on the shipped fixture, then the run's own verification report.

### 使用增益 (25 points)

The organizer grades:
  - 在相同稿件版本、相同意见清单、相同工具权限下，加载成果后返修交付质量是否稳定提升。
  - 是否减少逐条比对意见、人工查找行号、重写语气和补齐证据清单的时间。
  - "有改善"的结论是否有公平对照与逐条证据支撑。

How this skill answers it: the numbered workflow replaces the free-form draft-review cycle with one executable pass plus one audit pass.
How a reviewer verifies it: the reproduction commands in `GAIN.md`, which anyone can rerun on the fixture.

### 创新增益 (15 points)

The organizer grades:
  - 是否形成基础 Agent 不具备、或难以稳定实现的返修处理能力。
  - 意见拆解、定位方式、证据组织与语气控制的方法是否带来实质改进。
  - 创新点相对已有返修工具或通用写作 Agent 的边界与价值是否被证明。

How this skill answers it: the mechanism the baseline agent has no equivalent for: declared-source checks and a real editable artifact from the same pass.
How a reviewer verifies it: `INNOVATION.md`, plus the named checks in the audit report.

### 可靠体验 (10 points)

The organizer grades:
  - Agent 能否在真实返修场景中被正确触发，作者能否按说明完成一次完整返修。
  - 长稿件、多意见、多轮返修与重复运行下能否持续产出可用结果。
  - 对意见互相冲突、意见本身有误、稿件缺章节、无法补实验、版本不匹配、权限不足等情况的识别与处置能力。

How this skill answers it: explicit trigger conditions, budgets and a documented honest-partial path.
How a reviewer verifies it: the failure matrix in `SKILL.md` and `CHECKLIST.md`.

### 生态贡献 (10 points)

The organizer grades:
  - 使用说明、输入模板、依赖、示例、边界与维护信息是否齐全。
  - 题集、意见分类法、回复信模板、定位脚手架与评分表能否被他人直接复用。
  - 是否沉淀可分享的返修案例、意见分类经验与真实应用价值。

How this skill answers it: runnable scripts, templates, a check list and a reusable item set.
How a reviewer verifies it: the file inventory in `ECOSYSTEM.md`.

## What this skill does not claim

- No official score is claimed or predicted here.
- No organizer case, whiteboard or formal answer is included; the shipped cases are
  interface fixtures marked as such.
- Dimensions graded from the platform's own baseline comparison are answered by this
  skill's runtime behaviour, not by prose.
