# Rubric coverage — 论文结构与逻辑优化

Channel: `challenge-8021aacb`. Total 100 points. The text below quotes the organizer's own
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
  - 是否真的对一篇完整稿件完成结构诊断，并交付作者可直接执行的修改方案。
  - 结构判断是否与稿件实际内容相符，是否虚构不存在的缺陷、是否漏掉真实断裂、是否把风格偏好当成结构错误。
  - 是否覆盖研究问题、章节结构、论证链、段落关系、重复内容、结论边界六类，且缺项不是稿件的主要问题所在。
  - 诊断与修改建议能否指回原文位置、判断过程能否被独立复核。

How this skill answers it: the runtime writes the case's declared deliverables into `/app/output` and re-opens them before finishing.
How a reviewer verifies it: `tests/run_checks.py` on the shipped fixture, then the run's own verification report.

### 使用增益 (25 points)

The organizer grades:
  - 在相同稿件、相同任务要求下，加载成果后结构诊断与修改方案是否优于基础 Agent。
  - 作者从拿到诊断到完成结构定稿所需的时间、轮次与返工是否下降。
  - 是否用同稿、同版本、同评分口径的对照证明改善。

How this skill answers it: the numbered workflow replaces the free-form draft-review cycle with one executable pass plus one audit pass.
How a reviewer verifies it: the reproduction commands in `GAIN.md`, which anyone can rerun on the fixture.

### 创新增益 (15 points)

The organizer grades:
  - 是否形成基础 Agent 或现有写作工具不具备的结构级能力，例如论点—论据映射、跨章节冗余检测、结论与数据范围的边界比对。
  - 章节功能拆解、论点与论据抽取、重复内容识别、结论边界检查等方法本身是否带来实质改进。
  - 是否证明结构优化相对已有方案（尤其是语言润色类工具）的边界与增量。

How this skill answers it: the mechanism the baseline agent has no equivalent for: declared-source checks and a real editable artifact from the same pass.
How a reviewer verifies it: `INNOVATION.md`, plus the named checks in the audit report.

### 可靠体验 (10 points)

The organizer grades:
  - Agent 是否能正确触发，作者是否能按说明完成一次完整结构诊断。
  - 在不同学科、不同稿件类型、不同篇幅与重复运行下能否持续产出可用的结构诊断。
  - 对缺章节、无参考文献、图表与公式缺失、格式混乱、稿件被截断等情况的识别与处置。

How this skill answers it: explicit trigger conditions, budgets and a documented honest-partial path.
How a reviewer verifies it: the failure matrix in `SKILL.md` and `CHECKLIST.md`.

### 生态贡献 (10 points)

The organizer grades:
  - 使用说明、依赖、配置、示例、适用范围、限制和维护信息是否齐全。
  - Skill 本体、脚本、题集、结构问题标注模板、论点—论据映射表等资源能否被他人复用。
  - 是否沉淀可分享的结构问题分类、典型案例、改稿前后对照与真实应用价值。

How this skill answers it: runnable scripts, templates, a check list and a reusable item set.
How a reviewer verifies it: the file inventory in `ECOSYSTEM.md`.

## What this skill does not claim

- No official score is claimed or predicted here.
- No organizer case, whiteboard or formal answer is included; the shipped cases are
  interface fixtures marked as such.
- Dimensions graded from the platform's own baseline comparison are answered by this
  skill's runtime behaviour, not by prose.
