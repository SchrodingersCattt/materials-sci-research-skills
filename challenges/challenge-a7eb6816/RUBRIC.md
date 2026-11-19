# Rubric coverage — 写作17｜科研成果转化写作

Channel: `challenge-a7eb6816`. Total 100 points. The text below quotes the organizer's own
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
  - 是否按给定源文、目标读者、体裁与篇幅完成一次可直接使用的成果转化改写，而不是只给写作建议、提纲或片段润色。
  - 改写稿中的事实、数据、单位、图表编号、引用与论断强度是否与源文一致，是否出现源文没有支持的新结论。
  - 是否保住源文的关键结论、数据、限定条件、方法要点与图表引用，同时删掉的是冗余而不是证据。
  - 改动能否被原作者按段复核，是否提供逐段对照、改动清单、删改理由和待确认问题。

How this skill answers it: the runtime writes the case's declared deliverables into `/app/output` and re-opens them before finishing.
How a reviewer verifies it: `tests/run_checks.py` on the shipped fixture, then the run's own verification report.

### 使用增益 (25 points)

The organizer grades:
  - 在相同源文、相同读者与体裁要求、相同篇幅上限下，加载 Skill、插件或工作流后是否比基础 Agent 更少出现事实漂移、受众错配和术语不一致。
  - 从拿到源文到形成可提交稿，人工编辑条目数、返工轮次与核对成本是否下降。
  - 是否通过公平对照证明质量或效率改善，包括同源文、同读者约束、同篇幅上限、同评分表或参考改写稿。

How this skill answers it: the numbered workflow replaces the free-form draft-review cycle with one executable pass plus one audit pass.
How a reviewer verifies it: the reproduction commands in `GAIN.md`, which anyone can rerun on the fixture.

### 创新增益 (15 points)

The organizer grades:
  - 是否形成基础 Agent 或通用写作工具不具备、或难以稳定实现的“受众画像→取舍策略→边界标注→多文体映射”链条。
  - 取舍规则、术语锁定、论断强度分级、逐段对照等方法是否带来实质改进。
  - 是否证明创新点相对基础 Agent、通用写作工具或人工改写流程的边界与价值。

How this skill answers it: the mechanism the baseline agent has no equivalent for: declared-source checks and a real editable artifact from the same pass.
How a reviewer verifies it: `INNOVATION.md`, plus the named checks in the audit report.

### 可靠体验 (10 points)

The organizer grades:
  - Agent 能否在“提供源文、说明读者与体裁”时正确触发，用户能否按说明完成一次完整改写。
  - 同一源文重复运行、长文分段处理、不同文体切换时能否持续产出可用结果。
  - 对源文缺引用、数据自相矛盾、体裁与篇幅冲突、材料涉密或未发表等情况的识别与处置能力。

How this skill answers it: explicit trigger conditions, budgets and a documented honest-partial path.
How a reviewer verifies it: the failure matrix in `SKILL.md` and `CHECKLIST.md`.

### 生态贡献 (10 points)

The organizer grades:
  - SKILL.md、体裁模板、术语表、验收口径、失败处理、版本与维护信息是否齐全。
  - 术语表、必须保留项清单、体裁模板、改动清单格式、题集等资源能否被他人直接复用。
  - 是否沉淀可分享的案例、题集、改写方法与真实应用价值。

How this skill answers it: runnable scripts, templates, a check list and a reusable item set.
How a reviewer verifies it: the file inventory in `ECOSYSTEM.md`.

## What this skill does not claim

- No official score is claimed or predicted here.
- No organizer case, whiteboard or formal answer is included; the shipped cases are
  interface fixtures marked as such.
- Dimensions graded from the platform's own baseline comparison are answered by this
  skill's runtime behaviour, not by prose.
