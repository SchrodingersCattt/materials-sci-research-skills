# Rubric coverage — 学术格式与模板适配

Channel: `challenge-96263d10`. Total 100 points. The text below quotes the organizer's own
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
  - 是否真正把一份真实稿件按目标模板改到可交付，而不是只改了几处看得见的格式。
  - 格式规格与内容是否同时正确——字号、行距、页边距、栏数、题注位置、参考文献样式是否符合目标模板，同时正文、图表、公式、引用、批注是否被错误改动。
  - 模板要求的检查项与原稿的内容单元是否都被覆盖。
  - 他人能否按提交材料复现“从输入件到成品”的过程并核对每一项。

How this skill answers it: the runtime writes the case's declared deliverables into `/app/output` and re-opens them before finishing.
How a reviewer verifies it: `tests/run_checks.py` on the shipped fixture, then the run's own verification report.

### 使用增益 (25 points)

The organizer grades:
  - 在相同输入稿件、相同目标模板、相同工具权限下，加载 Skill、插件或工作流后相比不加载的基础 Agent 是否提升适配质量。
  - 是否减少逐项核对、重复排版、试错导出与人工返工。
  - 是否通过公平对照证明质量或效率改善。

How this skill answers it: the numbered workflow replaces the free-form draft-review cycle with one executable pass plus one audit pass.
How a reviewer verifies it: the reproduction commands in `GAIN.md`, which anyone can rerun on the fixture.

### 创新增益 (15 points)

The organizer grades:
  - 是否形成基础 Agent 或现有排版工具不具备、或难以稳定实现的能力，例如从模板文件反推检查项清单、图表题注与交叉引用联动更新、转换后自动比对保真度。
  - 模板解析、样式映射、内容锚定、转换与导出校验的方法是否带来实质改进。
  - 是否证明创新点相对已有方案的边界和价值。

How this skill answers it: the mechanism the baseline agent has no equivalent for: declared-source checks and a real editable artifact from the same pass.
How a reviewer verifies it: `INNOVATION.md`, plus the named checks in the audit report.

### 可靠体验 (10 points)

The organizer grades:
  - Agent 是否能正确触发和调用，用户是否能按说明完成一次完整适配。
  - 在不同模板类型、不同稿件长度、不同运行环境和重复运行下能否持续产出可用文件。
  - 对模板缺失或版本不明、字体缺失、样式冲突、转换失败、内容无法保真等情况的识别与处置能力。

How this skill answers it: explicit trigger conditions, budgets and a documented honest-partial path.
How a reviewer verifies it: the failure matrix in `SKILL.md` and `CHECKLIST.md`.

### 生态贡献 (10 points)

The organizer grades:
  - 使用说明、依赖环境、支持模板范围、示例、限制与维护信息是否齐全。
  - Skill 本体、检查项清单、样式映射脚本、样例输入输出能否被他人复用。
  - 是否沉淀可分享的模板检查清单、案例、实践经验和真实应用价值。

How this skill answers it: runnable scripts, templates, a check list and a reusable item set.
How a reviewer verifies it: the file inventory in `ECOSYSTEM.md`.

## What this skill does not claim

- No official score is claimed or predicted here.
- No organizer case, whiteboard or formal answer is included; the shipped cases are
  interface fixtures marked as such.
- Dimensions graded from the platform's own baseline comparison are answered by this
  skill's runtime behaviour, not by prose.
