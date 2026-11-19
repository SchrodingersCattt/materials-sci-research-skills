# Rubric coverage — 写作05｜文献证据驱动写作

Channel: `challenge-b810ef56`. Total 100 points. The text below quotes the organizer's own
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
  - 是否把一段需要文献支撑的写作任务真正落到"论断清单—证据表—成稿"三段交付上。
  - 引用是否真实存在、是否真的支持该论断、著录信息与原文表述是否准确。
  - 论断、来源、证据强度标注、不确定性表述四类要素是否齐备。
  - 论断编号、原文摘录、定位信息与强度理由能否被独立复核。

How this skill answers it: the runtime writes the case's declared deliverables into `/app/output` and re-opens them before finishing.
How a reviewer verifies it: `tests/run_checks.py` on the shipped fixture, then the run's own verification report.

### 使用增益 (25 points)

The organizer grades:
  - 相同条件下加载 Skill、插件或工作流后，相比不加载的基础 Agent 是否改善证据支撑质量。
  - 是否减少回原文核对、补引用、改写过度推断段落等人工返工。
  - 是否通过公平对照证明证据支撑质量的改善。

How this skill answers it: the numbered workflow replaces the free-form draft-review cycle with one executable pass plus one audit pass.
How a reviewer verifies it: the reproduction commands in `GAIN.md`, which anyone can rerun on the fixture.

### 创新增益 (15 points)

The organizer grades:
  - 是否形成基础 Agent 或现有方案不具备、或难以稳定实现的论断切分、来源匹配与强度判定能力。
  - 证据抽取、匹配校验、强度分级和不确定性控制的方法是否带来实质改进。
  - 是否证明创新点相对已有方案的边界和价值。

How this skill answers it: the mechanism the baseline agent has no equivalent for: declared-source checks and a real editable artifact from the same pass.
How a reviewer verifies it: `INNOVATION.md`, plus the named checks in the audit report.

### 可靠体验 (10 points)

The organizer grades:
  - Agent 是否能正确触发和调用，用户是否能按说明完成一次从材料到成稿的完整流程。
  - 在不同学科、不同文献可得性和重复运行下能否持续产出可用的证据表与成稿。
  - 对文献不可得、仅有摘要、原文与摘要矛盾、证据相互冲突、格式不支持、权限不足等情况的识别与处置能力。

How this skill answers it: explicit trigger conditions, budgets and a documented honest-partial path.
How a reviewer verifies it: the failure matrix in `SKILL.md` and `CHECKLIST.md`.

### 生态贡献 (10 points)

The organizer grades:
  - 使用说明、依赖、配置、示例、适用范围、限制、强度分级口径和维护信息是否齐全。
  - Skill 本体、脚本、配置、论断切分模板、证据表结构和题集是否能被他人复用。
  - 是否沉淀可分享的案例、失败类型、核验方法和真实写作价值。

How this skill answers it: runnable scripts, templates, a check list and a reusable item set.
How a reviewer verifies it: the file inventory in `ECOSYSTEM.md`.

## What this skill does not claim

- No official score is claimed or predicted here.
- No organizer case, whiteboard or formal answer is included; the shipped cases are
  interface fixtures marked as such.
- Dimensions graded from the platform's own baseline comparison are answered by this
  skill's runtime behaviour, not by prose.
