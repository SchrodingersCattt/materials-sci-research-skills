# Rubric coverage — 写作14｜基金申请书写作

Channel: `challenge-d403dce6`. Total 100 points. The text below quotes the organizer's own
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
  - 是否针对给定材料交付"可直接进入申请书的章节稿＋要素对照说明"，而不是写作建议、提纲或整篇模板套用。
  - 事实性内容是否站得住——研究基础与前期成果、数据、引用文献、术语与政策口径是否准确，"已完成"与"拟开展"是否分清。
  - 七个要素是否齐全、厚度是否与任务要求匹配，要素之间是否衔接。
  - 段落、要素与证据之间能否构成可复核的三级对应，第三方能否判断某句话该不该这么写。

How this skill answers it: the runtime writes the case's declared deliverables into `/app/output` and re-opens them before finishing.
How a reviewer verifies it: `tests/run_checks.py` on the shipped fixture, then the run's own verification report.

### 使用增益 (25 points)

The organizer grades:
  - 在相同输入材料、相同相同可用资料下，加载 Skill 相比基础 Agent 是否在要素齐备、论断有据、目标与路线一致上稳定更好。
  - 是否减少从散乱材料到可提交初稿的时间、人工改写条目与往返轮次，且不把成本转移到事后校对。
  - 是否通过公平对照证明准确率、完整率或耗时的改善。

How this skill answers it: the numbered workflow replaces the free-form draft-review cycle with one executable pass plus one audit pass.
How a reviewer verifies it: the reproduction commands in `GAIN.md`, which anyone can rerun on the fixture.

### 创新增益 (15 points)

The organizer grades:
  - 是否形成基础 Agent、通用写作工具或现有模板不具备、或难以稳定实现的能力。
  - 材料抽取、要素映射、一致性回检、引用核验、评审人视角自检等方法是否带来实质改进。
  - 是否证明创新点相对已有方案的边界和价值。

How this skill answers it: the mechanism the baseline agent has no equivalent for: declared-source checks and a real editable artifact from the same pass.
How a reviewer verifies it: `INNOVATION.md`, plus the named checks in the audit report.

### 可靠体验 (10 points)

The organizer grades:
  - Agent 是否能正确识别基金申请书写作任务并调用，用户能否按说明完成一节稿。
  - 在长材料、多章节、不同学科和重复运行下能否持续产出口径一致的稿件。
  - 对材料缺失、指南不明、超长输入、引用无法核实、学科跨度过大、格式冲突等情况的识别与处置。

How this skill answers it: explicit trigger conditions, budgets and a documented honest-partial path.
How a reviewer verifies it: the failure matrix in `SKILL.md` and `CHECKLIST.md`.

### 生态贡献 (10 points)

The organizer grades:
  - SKILL.md、输入材料清单、模板映射、示例、适用范围、限制和维护信息是否齐全。
  - 要素清单、一致性检查表、题集、评分表、示例材料等资源能否被他人直接用于自己的申请。
  - 是否沉淀可分享的案例、Benchmark、写作方法与真实应用价值。

How this skill answers it: runnable scripts, templates, a check list and a reusable item set.
How a reviewer verifies it: the file inventory in `ECOSYSTEM.md`.

## What this skill does not claim

- No official score is claimed or predicted here.
- No organizer case, whiteboard or formal answer is included; the shipped cases are
  interface fixtures marked as such.
- Dimensions graded from the platform's own baseline comparison are answered by this
  skill's runtime behaviour, not by prose.
