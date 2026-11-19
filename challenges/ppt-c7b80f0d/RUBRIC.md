# Rubric coverage — 论文转学术 PPT

Channel: `ppt-c7b80f0d`. Total 100 points. The text below quotes the organizer's own
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
  - \*\* 评价是否真正把一篇论文变成主线成立、页序可讲、可在目标模板中交付的学术 PPT，而不是把段落切块贴进页面。**
  - ** 评价页面上的数字、单位、方法名称、结论表述与论文是否一致，图表编号与正文引用是否对得上，是否存在把示意图当实验数据、把他人结果当本文结果的情况。**
  - ** 评价论文主线必需页是否齐全，以及论文主线、页结构、图表引用、讲解逻辑、模板约束、导出渲染六类要素的覆盖程度。**
  - ** 评价每页内容能否回溯到论文的具体图、表、章节或页码，是否提供页级金标准、源文件与导出文件。\*\*

How this skill answers it: the runtime writes the case's declared deliverables into `/app/output` and re-opens them before finishing.
How a reviewer verifies it: `tests/run_checks.py` on the shipped fixture, then the run's own verification report.

### 使用增益 (25 points)

The organizer grades:
  - \*\* 评价在相同论文、相同模板、相同软件版本与页数上限下，加载成果后页级正确性、主线清晰度与版面合规是否稳定优于不加载的基础 Agent。**
  - ** 评价从拿到论文到形成可讲 PPT 的端到端耗时，以及人工修改页数是否下降。**
  - ** 评价是否通过同输入、同模板、同版本的公平对照证明质量或效率改善。\*\*

How this skill answers it: the numbered workflow replaces the free-form draft-review cycle with one executable pass plus one audit pass.
How a reviewer verifies it: the reproduction commands in `GAIN.md`, which anyone can rerun on the fixture.

### 创新增益 (15 points)

The organizer grades:
  - \*\* 评价是否形成基础 Agent 或现有方案不具备、或难以稳定实现的能力，例如论文图表定位与页级引用、按模板占位符约束排版、讲解备注与页面内容分离生成。**
  - ** 评价主线抽取、页结构映射、图表对齐、备注生成等方法是否带来实质改进，而非包装。**
  - ** 评价是否证明创新点相对已有方案（通用 PPT 生成工具、手工排版流程、其他课题产出）的边界与价值。\*\*

How this skill answers it: the mechanism the baseline agent has no equivalent for: declared-source checks and a real editable artifact from the same pass.
How a reviewer verifies it: `INNOVATION.md`, plus the named checks in the audit report.

### 可靠体验 (10 points)

The organizer grades:
  - \*\* 评价 Agent 是否能被正确触发，用户是否能按说明用一篇论文跑出可打开、可编辑的 PPT。**
  - ** 评价在不同论文类型、不同模板和重复运行下，能否持续产出可打开、不崩版、可编辑的成果。**
  - ** 评价对图表无法提取、公式为图片、PDF 加密、模板占位符不足、字体缺失、页数超限等情况的识别与处置能力。\*\*

How this skill answers it: explicit trigger conditions, budgets and a documented honest-partial path.
How a reviewer verifies it: the failure matrix in `SKILL.md` and `CHECKLIST.md`.

### 生态贡献 (10 points)

The organizer grades:
  - \*\* 评价使用说明、依赖、模板要求、示例、适用范围、限制和维护信息是否齐全。**
  - ** 评价 Skill 本体、模板、页级大纲模板、证据映射表、题集与金标准等资源能否被他人复用。**
  - ** 评价是否沉淀可分享的论文转 PPT 案例、模板方法、实践经验和真实汇报价值。\*\*

How this skill answers it: runnable scripts, templates, a check list and a reusable item set.
How a reviewer verifies it: the file inventory in `ECOSYSTEM.md`.

## What this skill does not claim

- No official score is claimed or predicted here.
- No organizer case, whiteboard or formal answer is included; the shipped cases are
  interface fixtures marked as such.
- Dimensions graded from the platform's own baseline comparison are answered by this
  skill's runtime behaviour, not by prose.
