# Rubric coverage — Graphical Abstract（图形摘要）

Channel: `graphical-abstract-7030fff2`. Total 100 points. The text below quotes the organizer's own
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
  - \*\* 评价是否真正产出“研究问题—方法—核心结果—结论”的单页图形摘要，并交付可继续编辑的源文件。**
  - ** 评价图中科学实体、实体间关系、数据编码与图例是否与来源材料一致。**
  - ** 评价四要素与图例、单位、比例尺等辅助信息的覆盖程度。**
  - ** 评价图稿、来源映射、版本与导出记录能否支持独立复核。\*\*

How this skill answers it: the runtime writes the case's declared deliverables into `/app/output` and re-opens them before finishing.
How a reviewer verifies it: `tests/run_checks.py` on the shipped fixture, then the run's own verification report.

### 使用增益 (25 points)

The organizer grades:
  - \*\* 评价相同输入下加载 Skill、插件或工作流后，相比不加载的基础 Agent 是否提升图稿质量。**
  - ** 评价是否减少重绘、重排版、跨软件搬运和人工返工。**
  - ** 评价是否通过公平对照证明质量或效率改善。\*\*

How this skill answers it: the numbered workflow replaces the free-form draft-review cycle with one executable pass plus one audit pass.
How a reviewer verifies it: the reproduction commands in `GAIN.md`, which anyone can rerun on the fixture.

### 创新增益 (15 points)

The organizer grades:
  - \*\* 评价是否形成基础 Agent 或现有方案不具备、或难以稳定实现的图谱式表达能力。**
  - ** 评价实体抽取规则、视觉通道映射、版面约束和导出检查等方法是否带来实质改进。**
  - ** 评价是否证明创新点相对已有绘图方案的边界和价值。\*\*

How this skill answers it: the mechanism the baseline agent has no equivalent for: declared-source checks and a real editable artifact from the same pass.
How a reviewer verifies it: `INNOVATION.md`, plus the named checks in the audit report.

### 可靠体验 (10 points)

The organizer grades:
  - \*\* 评价 Agent 是否能正确触发，用户是否能按说明完成从材料到成图并导出。**
  - ** 评价在不同图型、不同材料和重复运行下能否持续产出结构一致、可编辑的图稿。**
  - ** 评价对材料缺关键数值、实体歧义、文字溢出、字体缺失、画布超限和导出失败等情况的识别与处置能力。\*\*

How this skill answers it: explicit trigger conditions, budgets and a documented honest-partial path.
How a reviewer verifies it: the failure matrix in `SKILL.md` and `CHECKLIST.md`.

### 生态贡献 (10 points)

The organizer grades:
  - \*\* 评价使用说明、模板、依赖、导出参数、示例、限制和维护信息是否齐全。**
  - ** 评价图稿模板、图层结构与命名、图例样式、导出配置和题集能否被他人直接复用。**
  - ** 评价是否沉淀可分享的图稿案例、版式经验、Benchmark 和真实应用价值。\*\*

How this skill answers it: runnable scripts, templates, a check list and a reusable item set.
How a reviewer verifies it: the file inventory in `ECOSYSTEM.md`.

## What this skill does not claim

- No official score is claimed or predicted here.
- No organizer case, whiteboard or formal answer is included; the shipped cases are
  interface fixtures marked as such.
- Dimensions graded from the platform's own baseline comparison are answered by this
  skill's runtime behaviour, not by prose.
