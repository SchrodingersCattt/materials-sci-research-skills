# Rubric coverage — 文献证据溯源与事实核验

Channel: `challenge-e5e3be30`. Total 100 points. The text below quotes the organizer's own
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
  - 是否把待核验的科研论断真正落到可判定的证据上，交付能直接使用的证据卡片或核验报告。
  - 证据片段是否真实存在于所标位置、支持度判定是否站得住、文献元数据是否准确，尤其要区分"主题相关"与"真正支持"。
  - 是否覆盖论断拆解出的全部子判断（事实、比较、因果、范围）、正反证据、冲突来源与限制条件。
  - "论断→证据片段→原文定位→支持度判定→判定理由"这条链能否被他人独立复核。

How this skill answers it: the runtime writes the case's declared deliverables into `/app/output` and re-opens them before finishing.
How a reviewer verifies it: `tests/run_checks.py` on the shipped fixture, then the run's own verification report.

### 使用增益 (25 points)

The organizer grades:
  - 在相同文献、相同论断、相同工具权限下，加载 Skill 后误支持（把主题相关当支持）与漏检（真支持未被识别）是否下降。
  - 单条论断从"打开原文人工找段落"到"核对证据卡片"的耗时、人工回原文的条数以及返工轮次是否下降。
  - 是否通过同输入、同文献版本、同同工具权限的加载与不加载对照，证明质量或效率改善。

How this skill answers it: the numbered workflow replaces the free-form draft-review cycle with one executable pass plus one audit pass.
How a reviewer verifies it: the reproduction commands in `GAIN.md`, which anyone can rerun on the fixture.

### 创新增益 (15 points)

The organizer grades:
  - 是否形成基础 Agent 或现有方案不具备、或难以稳定实现的段落级定位、四级支持度判定、冲突并列与不确定性表达能力。
  - 论断拆解粒度、证据检索与重排、支持度判定规则、双人标注与仲裁流程是否带来实质改进。
  - 是否证明创新点相对已有方案的边界和价值。

How this skill answers it: the mechanism the baseline agent has no equivalent for: declared-source checks and a real editable artifact from the same pass.
How a reviewer verifies it: `INNOVATION.md`, plus the named checks in the audit report.

### 可靠体验 (10 points)

The organizer grades:
  - Agent 能否在"帮我核验这句话"这类请求下正确触发，用户能否按说明完成一次从论断到证据卡片的核验，以及能否识别不属于本课题的请求。
  - 长论文、跨页证据、扫描件、多语言文献和重复运行下能否持续产出可核验结果。
  - 对原文无法访问、PDF 无文本层、定位失败、证据互相冲突、论断含多个子判断却只找到部分证据等情况下的识别与处置能力。

How this skill answers it: explicit trigger conditions, budgets and a documented honest-partial path.
How a reviewer verifies it: the failure matrix in `SKILL.md` and `CHECKLIST.md`.

### 生态贡献 (10 points)

The organizer grades:
  - 使用说明、四级判定定义、输入输出字段、依赖、配置、示例、适用范围、限制和维护信息是否齐全。
  - Skill 本体、脚本、证据卡片模板、论断拆解题集、标注规范与评分表能否被他人复用复跑。
  - 是否沉淀可分享的核验案例、标注经验、Benchmark 与真实应用价值。

How this skill answers it: runnable scripts, templates, a check list and a reusable item set.
How a reviewer verifies it: the file inventory in `ECOSYSTEM.md`.

## What this skill does not claim

- No official score is claimed or predicted here.
- No organizer case, whiteboard or formal answer is included; the shipped cases are
  interface fixtures marked as such.
- Dimensions graded from the platform's own baseline comparison are answered by this
  skill's runtime behaviour, not by prose.
