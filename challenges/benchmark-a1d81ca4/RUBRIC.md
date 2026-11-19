# Rubric coverage — 文献阅读 Benchmark 与评测工具

Channel: `benchmark-a1d81ca4`. Total 100 points. The text below quotes the organizer's own
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
  - 是否真正建成可判分、可复跑的题集与评测流程，而不是交出一份题单加几张截图。
  - 参考答案、判分结果和汇总指标是否准确一致，自动得分是否与人工结论对得上。
  - 是否覆盖任务定义、数据与答案管理、评分维度、原始输出留存、误差分析、版本迭代六个方面。
  - 每个分数能否顺着题目 ID 追到原始输出、运行配置和评分记录。

How this skill answers it: the runtime writes the case's declared deliverables into `/app/output` and re-opens them before finishing.
How a reviewer verifies it: `tests/run_checks.py` on the shipped fixture, then the run's own verification report.

### 使用增益 (25 points)

The organizer grades:
  - 在同一题集快照与同一 Agent 版本下，加载成果相比不加载是否提升评测质量。
  - 建题、跑评测、汇总与复核的人工修改量是否下降。
  - 是否通过公平对照证明质量或效率改善。

How this skill answers it: the numbered workflow replaces the free-form draft-review cycle with one executable pass plus one audit pass.
How a reviewer verifies it: the reproduction commands in `GAIN.md`, which anyone can rerun on the fixture.

### 创新增益 (15 points)

The organizer grades:
  - 是否形成基础 Agent 或现有方案不具备、或难以稳定实现的评测基础设施能力。
  - 题集设计、评分档位、运行与失败归因方法是否带来实质改进。
  - 是否用同批题目证明新做法相对旧口径的边界与价值。

How this skill answers it: the mechanism the baseline agent has no equivalent for: declared-source checks and a real editable artifact from the same pass.
How a reviewer verifies it: `INNOVATION.md`, plus the named checks in the audit report.

### 可靠体验 (10 points)

The organizer grades:
  - 用户能否按说明跑完一轮评测。
  - 同一题集在不同环境与重复运行下能否持续产出可用结果。
  - 对题目缺参考答案、输出为空或超长、格式不合规、文件损坏、权限不足等情况的识别与处置。

How this skill answers it: explicit trigger conditions, budgets and a documented honest-partial path.
How a reviewer verifies it: the failure matrix in `SKILL.md` and `CHECKLIST.md`.

### 生态贡献 (10 points)

The organizer grades:
  - 题卡规范、运行方法、依赖、示例、结果字段与维护信息是否齐全。
  - 题集、评分表、运行器、结果模板能否被他人直接复用。
  - 是否沉淀可分享的建题经验、失败样例与真实应用价值。

How this skill answers it: runnable scripts, templates, a check list and a reusable item set.
How a reviewer verifies it: the file inventory in `ECOSYSTEM.md`.

## Other channels this candidate is submitted to

The same runtime serves these channels; their published sub-point text is quoted
below so the mapping can be checked per channel.

- `benchmark-a1d81ca4` — 文献阅读 Benchmark 与评测工具
- `benchmark-d57ad64a` — 学术写作 Benchmark 与评测工具

### benchmark-d57ad64a — 学术写作 Benchmark 与评测工具

- **实际效果 40** (任务完成度 15 + 结果正确性 15 + 结果完整性 5 + 结果可核验性 5)
  - 是否真的形成“题面—参考答案—评分锚点—逐题评分—评测报告”的可判定闭环，而不是只交一份范文、一张总分表或一段演示。
  - 评测结论本身是否成立，包括参考答案是否真的可接受、锚点是否与题面要求一致、得分是否与稿子实际质量对得上、报告中的题号分数引用是否准确。
  - 是否覆盖承诺的题量与题型结构、是否覆盖六个方向、报告是否给全逐题结果。
  - 别人能否拿题集、锚点版本、原始输出和评分记录复算出同一批分数。
- **使用增益 25** (质量增益 15 + 效率增益 5 + 增益可验证性 5)
  - 相同条件下加载工具后，相比人工手写题集与评分表，产出质量（题面完备度、锚点可操作性、评分一致性、报告可用性）是否稳定提升。
  - 建题、评稿、汇总报告的时间、人工步骤、返工轮次或综合成本是否下降。
  - 是否通过公平对照证明质量或效率改善，而不是靠精选案例。
- **创新增益 15** (新增能力 5 + 方法改进 5 + 创新证据 5)
  - 是否形成基础 Agent 或通用 rubric 不具备、或难以稳定实现的能力，例如把写作要求转成可观察判据、从评分分歧反推锚点缺陷、按题型自动分层出题。
  - 任务集设计方法、参考答案构造、锚点分层、一致性校准与复现流程是否带来实质改进。
  - 是否证明新做法相对通用 rubric 或纯人工经验更可靠，边界在哪里。
- **可靠体验 10** (调用与易用性 3 + 运行稳定性 4 + 异常处理 3)
  - Agent 是否能正确触发和调用，一名新评分员能否只按文档完成出题、打分和出报告。
  - 在不同写作类型、不同运行条件和重复运行下能否持续产出可用结果。
  - 对题面歧义、参考答案缺失、双评分歧超过一档、材料超长或格式错乱、模型拒答等情况的识别与处置。
- **生态贡献 10** (文档完整性 3 + 资源可复用性 4 + 分享推广价值 3)
  - SKILL.md、使用说明、题目编写规范、锚点写法、评分表字段、版本与限制信息是否齐全。
  - 题集、锚点库、评分表模板、复现脚本能否被他人直接拿去建自己的学科题集。
  - 是否沉淀可分享的建题方法、锚点库、失败分析和真实应用价值。

## What this skill does not claim

- No official score is claimed or predicted here.
- No organizer case, whiteboard or formal answer is included; the shipped cases are
  interface fixtures marked as such.
- Dimensions graded from the platform's own baseline comparison are answered by this
  skill's runtime behaviour, not by prose.
