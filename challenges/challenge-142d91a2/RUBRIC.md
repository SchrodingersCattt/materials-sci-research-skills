# Rubric coverage — 写作15｜开题报告与研究计划书

Channel: `challenge-142d91a2`. Total 100 points. The text below quotes the organizer's own
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
  - 是否真正交付一份研究背景、问题定义、目标、技术路线、阶段计划、风险、预期成果七要素齐全、且与给定周期和资源相容的开题方案。
  - 事实、数据、引用、专业判断和计划口径是否准确，尤其看论断与引用是否一一对应、指标阈值是否有依据。
  - 七要素、风险类型和预期成果考核方式是否齐全，边界是否写明。
  - 每个论断能否定位到输入材料、引用与版本，评分人能否按记录复跑。

How this skill answers it: the runtime writes the case's declared deliverables into `/app/output` and re-opens them before finishing.
How a reviewer verifies it: `tests/run_checks.py` on the shipped fixture, then the run's own verification report.

### 使用增益 (25 points)

The organizer grades:
  - 相同条件下加载 Skill、插件或工作流后，相比不加载的基础 Agent 是否提升开题方案质量。
  - 是否减少大纲搭建、章节重写、往返修改和材料核对的工作量。
  - 是否通过公平对照证明质量或效率改善。

How this skill answers it: the numbered workflow replaces the free-form draft-review cycle with one executable pass plus one audit pass.
How a reviewer verifies it: the reproduction commands in `GAIN.md`, which anyone can rerun on the fixture.

### 创新增益 (15 points)

The organizer grades:
  - 是否形成基础 Agent 不具备、或难以稳定实现的开题方案生成与自检能力。
  - 约束抽取、要素对齐、计划可行性校验等方法是否带来实质改进，而非包装。
  - 是否证明创新点相对已有方案的边界和价值。

How this skill answers it: the mechanism the baseline agent has no equivalent for: declared-source checks and a real editable artifact from the same pass.
How a reviewer verifies it: `INNOVATION.md`, plus the named checks in the audit report.

### 可靠体验 (10 points)

The organizer grades:
  - Agent 能否正确触发，模糊请求下是否先索要课题指南、周期、经费与数据条件，用户能否按说明完成一次完整撰写。
  - 在不同学科、不同篇幅和重复运行下，要素是否不漂移、目标数量与周期经费是否前后一致。
  - 遇到材料缺失、周期过短、指标不可达、学科规范冲突、引用无法获取时的识别与处置能力。

How this skill answers it: explicit trigger conditions, budgets and a documented honest-partial path.
How a reviewer verifies it: the failure matrix in `SKILL.md` and `CHECKLIST.md`.

### 生态贡献 (10 points)

The organizer grades:
  - 使用说明、依赖、要素清单、示例、适用边界和维护信息是否齐全。
  - Skill 本体、脚本、题集、任务卡、要素检查表、计划模板和评分锚点能否被他人复用。
  - 是否沉淀可分享的开题案例、Benchmark、写作方法和真实应用价值。

How this skill answers it: runnable scripts, templates, a check list and a reusable item set.
How a reviewer verifies it: the file inventory in `ECOSYSTEM.md`.

## What this skill does not claim

- No official score is claimed or predicted here.
- No organizer case, whiteboard or formal answer is included; the shipped cases are
  interface fixtures marked as such.
- Dimensions graded from the platform's own baseline comparison are answered by this
  skill's runtime behaviour, not by prose.
