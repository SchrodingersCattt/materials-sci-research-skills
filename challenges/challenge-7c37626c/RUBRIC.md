# Rubric coverage — 公式解析与数学推理

Channel: `challenge-7c37626c`. Total 100 points. The text below quotes the organizer's own
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
  - 是否真的把给定的公式图像或 PDF 片段转成可用的结构化表达，并交付变量表与推导说明，而不是只贴一段 LaTeX。
  - 还原的 LaTeX 与原文符号、上下标、括号层级、希腊字母和单位是否一一对应，变量解释是否符合原文定义，数值代入是否算得对。
  - 是否覆盖所声明公式的变量表、推导步骤、边界条件与核验结论，而不是只给首行公式。
  - 每个符号定义能否指回原文位置，每步推导与数值代入能否按记录复跑。

How this skill answers it: the runtime writes the case's declared deliverables into `/app/output` and re-opens them before finishing.
How a reviewer verifies it: `tests/run_checks.py` on the shipped fixture, then the run's own verification report.

### 使用增益 (25 points)

The organizer grades:
  - 相同条件下加载 Skill、插件或工作流后，相比不加载的基础 Agent 是否改善公式解析与解释质量。
  - 是否减少回原文找定义、手工比对符号、重复代入与人工返工。
  - 是否通过公平对照证明质量或效率改善。

How this skill answers it: the numbered workflow replaces the free-form draft-review cycle with one executable pass plus one audit pass.
How a reviewer verifies it: the reproduction commands in `GAIN.md`, which anyone can rerun on the fixture.

### 创新增益 (15 points)

The organizer grades:
  - 是否形成基础 Agent 或现有方案不具备、或难以稳定实现的公式解析与核验能力。
  - 识别、对齐、核验的流程设计或符号约束策略是否带来实质改进。
  - 是否证明创新点相对已有方案的边界和价值。

How this skill answers it: the mechanism the baseline agent has no equivalent for: declared-source checks and a real editable artifact from the same pass.
How a reviewer verifies it: `INNOVATION.md`, plus the named checks in the audit report.

### 可靠体验 (10 points)

The organizer grades:
  - Agent 是否能正确触发和调用，用户是否能按说明看懂一次完整的公式解析。
  - 在不同版式、不同公式类型和重复运行下能否持续产出可用结果。
  - 对图像模糊、公式截断、符号严重歧义、单位缺失、代入无解、权限不足等情况的识别与处置能力。

How this skill answers it: explicit trigger conditions, budgets and a documented honest-partial path.
How a reviewer verifies it: the failure matrix in `SKILL.md` and `CHECKLIST.md`.

### 生态贡献 (10 points)

The organizer grades:
  - 使用说明、依赖、配置、示例、符号约定、适用范围、限制和维护信息是否齐全。
  - Skill 本体、脚本、题集、公式图像、LaTeX 参考答案、变量表模板与核验脚本能否被他人复用。
  - 是否沉淀可分享的公式案例、Benchmark、解析方法与真实应用价值。

How this skill answers it: runnable scripts, templates, a check list and a reusable item set.
How a reviewer verifies it: the file inventory in `ECOSYSTEM.md`.

## What this skill does not claim

- No official score is claimed or predicted here.
- No organizer case, whiteboard or formal answer is included; the shipped cases are
  interface fixtures marked as such.
- Dimensions graded from the platform's own baseline comparison are answered by this
  skill's runtime behaviour, not by prose.
