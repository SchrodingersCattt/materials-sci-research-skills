# Rubric coverage — 写作12｜学术翻译与双语写作

Channel: `challenge-bb17a294`. Total 100 points. The text below quotes the organizer's own
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
  - 是否把给定原文整篇译出、按要求的输出形态（纯译文、双语对照或带修订标记）交付，并且可以直接进入作者的修改流程。
  - 术语、数字、单位、引用、否定与限定条件是否与原文一致，是否存在凭空补写或删改科学判断。
  - 是否覆盖原文章节、图表、公式、脚注与参考文献，以及任务要求的目标语言版本。
  - 能否按句段追溯原文、术语依据、数字与引用核对结果以及人工修改痕迹。

How this skill answers it: the runtime writes the case's declared deliverables into `/app/output` and re-opens them before finishing.
How a reviewer verifies it: `tests/run_checks.py` on the shipped fixture, then the run's own verification report.

### 使用增益 (25 points)

The organizer grades:
  - 相同原文与条件下加载 Skill、插件或工作流后，相比不加载的基础 Agent 是否稳定提升译文质量与可编辑性。
  - 是否真实减少后编辑工时、术语统一、对照排版、数字与引用核对的人工量。
  - 是否通过公平对照证明质量或效率改善。

How this skill answers it: the numbered workflow replaces the free-form draft-review cycle with one executable pass plus one audit pass.
How a reviewer verifies it: the reproduction commands in `GAIN.md`, which anyone can rerun on the fixture.

### 创新增益 (15 points)

The organizer grades:
  - 是否形成基础 Agent 或现有方案不具备、或难以稳定实现的翻译与双语写作能力。
  - 术语抽取、分块策略、对齐约束、二次校验、风格控制等方法是否带来实质改进。
  - 是否证明创新点相对已有方案（通用翻译工具、写作00 现有能力等）的边界和价值。

How this skill answers it: the mechanism the baseline agent has no equivalent for: declared-source checks and a real editable artifact from the same pass.
How a reviewer verifies it: `INNOVATION.md`, plus the named checks in the audit report.

### 可靠体验 (10 points)

The organizer grades:
  - Agent 是否能正确触发和调用，用户能否按说明完成一次整篇翻译或双语写作任务。
  - 在不同文体、不同长度、不同语向和重复运行下能否持续产出可用结果。
  - 对公式与表格、术语表冲突、超长文本、语向不支持、引用格式异常、输入编码错误等情况的识别与处置能力。

How this skill answers it: explicit trigger conditions, budgets and a documented honest-partial path.
How a reviewer verifies it: the failure matrix in `SKILL.md` and `CHECKLIST.md`.

### 生态贡献 (10 points)

The organizer grades:
  - 使用说明、依赖、配置、示例、适用范围、限制和维护信息是否齐全。
  - Skill 本体、脚本、术语表、对齐工具、题集和提示模板能否被他人复用。
  - 是否沉淀可分享的真实稿件案例、术语资产、双语写作经验和实际应用价值。

How this skill answers it: runnable scripts, templates, a check list and a reusable item set.
How a reviewer verifies it: the file inventory in `ECOSYSTEM.md`.

## What this skill does not claim

- No official score is claimed or predicted here.
- No organizer case, whiteboard or formal answer is included; the shipped cases are
  interface fixtures marked as such.
- Dimensions graded from the platform's own baseline comparison are answered by this
  skill's runtime behaviour, not by prose.
