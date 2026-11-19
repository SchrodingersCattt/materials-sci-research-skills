# Rubric coverage — 写作01｜学术论文写作

Channel: `challenge-308a6fdc`. Total 100 points. The text below quotes the organizer's own
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
  - 是否在给定研究材料、实验记录、图表与文献的基础上，真正产出一份结构完整、可进入修改环节的章节稿，而不是提纲、写作建议或素材堆叠。
  - 稿件中的事实性内容是否与原始材料和文献一致，包括数值、单位、样本量、统计显著性、图注、作者、年份、期刊与 DOI。
  - 是否覆盖学科模板与任务要求的关键章节、图表、参考文献和声明字段。
  - 每条事实性论断能否指回具体材料位置和具体文献条目，稿件改动是否留痕。

How this skill answers it: the runtime writes the case's declared deliverables into `/app/output` and re-opens them before finishing.
How a reviewer verifies it: `tests/run_checks.py` on the shipped fixture, then the run's own verification report.

### 使用增益 (25 points)

The organizer grades:
  - 相同材料、相同章节要求、相同运行条件下，加载 Skill、插件或工作流后稿件的可用程度是否提升。
  - 从拿到材料到形成可修改初稿的时间、人工返工条目与重写轮次是否下降。
  - 对照是否公平：材料、章节模板、字数范围、引用格式、工具权限是否一致。

How this skill answers it: the numbered workflow replaces the free-form draft-review cycle with one executable pass plus one audit pass.
How a reviewer verifies it: the reproduction commands in `GAIN.md`, which anyone can rerun on the fixture.

### 创新增益 (15 points)

The organizer grades:
  - 是否形成基础 Agent 不具备的能力，例如材料、图表与正文三向对齐，论断与引用绑定，章节缺项检测，术语与缩写统一。
  - 材料索引、证据映射表、章节约束、引用核验回路、一致性检查等方法是否带来实质改进。
  - 相对通用大模型直接写作、模板填充、文献管理工具等已有方案的新增价值是否有证据。

How this skill answers it: the mechanism the baseline agent has no equivalent for: declared-source checks and a real editable artifact from the same pass.
How a reviewer verifies it: `INNOVATION.md`, plus the named checks in the audit report.

### 可靠体验 (10 points)

The organizer grades:
  - Agent 能否被正确触发，用户能否按说明把 docx、pdf、csv、图片等常见材料喂进去并拿到可编辑稿件。
  - 换学科、换篇幅、换材料完整度以及重复运行时能否稳定产出可用稿件。
  - 材料缺图注、图表与正文冲突、文献取不到全文、材料超长、引用格式不认识等情况下的识别与处置能力。

How this skill answers it: explicit trigger conditions, budgets and a documented honest-partial path.
How a reviewer verifies it: the failure matrix in `SKILL.md` and `CHECKLIST.md`.

### 生态贡献 (10 points)

The organizer grades:
  - SKILL.md、章节模板、输入材料格式、依赖、示例、适用范围与维护信息是否齐全。
  - 题集、材料包、章节模板、评分表、一致性检查脚本能否被他人直接复用。
  - 是否沉淀可分享的案例、题集、学科适配经验和真实应用价值。

How this skill answers it: runnable scripts, templates, a check list and a reusable item set.
How a reviewer verifies it: the file inventory in `ECOSYSTEM.md`.

## What this skill does not claim

- No official score is claimed or predicted here.
- No organizer case, whiteboard or formal answer is included; the shipped cases are
  interface fixtures marked as such.
- Dimensions graded from the platform's own baseline comparison are answered by this
  skill's runtime behaviour, not by prose.
