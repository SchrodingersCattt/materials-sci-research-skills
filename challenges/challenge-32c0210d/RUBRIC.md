# Rubric coverage — 学位论文与长文档写作

Channel: `challenge-32c0210d`. Total 100 points. The text below quotes the organizer's own
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
  - 是否按提纲和任务要求真正写出可用章节，并交付配套的术语、引用或改动说明，而不是给一段通用写作建议。
  - 每条论断是否与所引文献对得上，数据、术语、符号、章节与图表编号是否与原文或给定材料一致。
  - 提纲要求的章节、必要论证要素（研究问题、方法、结果、讨论、局限）和著录项（图表、参考文献、附录）是否齐全。
  - 章节文字能否追溯到大纲条目、原始材料、具体文献和版本记录。

How this skill answers it: the runtime writes the case's declared deliverables into `/app/output` and re-opens them before finishing.
How a reviewer verifies it: `tests/run_checks.py` on the shipped fixture, then the run's own verification report.

### 使用增益 (25 points)

The organizer grades:
  - 在相同材料、工具权限下，加载成果后长文档写作质量是否稳定提升，重点看跨章节一致性与可编辑性。
  - 是否减少反复通读全文、手工统一术语、逐条补引用、重排编号与交叉引用的人工成本。
  - 是否通过公平对照证明质量或效率改善。

How this skill answers it: the numbered workflow replaces the free-form draft-review cycle with one executable pass plus one audit pass.
How a reviewer verifies it: the reproduction commands in `GAIN.md`, which anyone can rerun on the fixture.

### 创新增益 (15 points)

The organizer grades:
  - 是否形成基础 Agent 或现有写作工具不具备、或难以稳定实现的长文档能力。
  - 章节规划、一致性检查、引用处理、版本合并等方法是否带来实质改进。
  - 是否证明创新点相对已有方案（基础 Agent、通用写作工具、人工模板）的边界和价值。

How this skill answers it: the mechanism the baseline agent has no equivalent for: declared-source checks and a real editable artifact from the same pass.
How a reviewer verifies it: `INNOVATION.md`, plus the named checks in the audit report.

### 可靠体验 (10 points)

The organizer grades:
  - Agent 是否能正确触发，作者是否能按说明完成一轮“给定材料—生成或改写章节—检查一致性”的完整流程。
  - 在不同章节类型（综述、方法、结果、讨论）、不同篇幅和重复运行下能否持续产出可用文本。
  - 对材料缺失、引用找不到原文、章节间结论冲突、编号不连续、文档格式不支持、超长截断等情况的识别与处置能力。

How this skill answers it: explicit trigger conditions, budgets and a documented honest-partial path.
How a reviewer verifies it: the failure matrix in `SKILL.md` and `CHECKLIST.md`.

### 生态贡献 (10 points)

The organizer grades:
  - 使用说明、依赖、配置、示例、适用范围、篇幅上限、已知失败模式和维护信息是否齐全。
  - Skill 本体、脚本、术语表与引用表模板、章节检查清单、测试题集能否被他人直接复用。
  - 是否沉淀可分享的长文档写作案例、一致性检查清单、改稿经验与真实应用价值。

How this skill answers it: runnable scripts, templates, a check list and a reusable item set.
How a reviewer verifies it: the file inventory in `ECOSYSTEM.md`.

## What this skill does not claim

- No official score is claimed or predicted here.
- No organizer case, whiteboard or formal answer is included; the shipped cases are
  interface fixtures marked as such.
- Dimensions graded from the platform's own baseline comparison are answered by this
  skill's runtime behaviour, not by prose.
