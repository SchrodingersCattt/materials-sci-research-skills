# Rubric coverage — reading engine (question-shaped and field-shaped cases)

Total 100 points. The text below quotes the organizer's own scoring points **for each channel this
engine serves**, so the mapping can be checked against the published statement rather than against
this skill's own claims. The header used to name a single channel; the engine is shared, so the
per-channel sections below are the authority.

| Dimension | Points | Sub-points | Mechanism in this skill | Verification |
|---|---|---|---|---|
| 实际效果 | 40 | 任务完成度 15 + 结果正确性 15 + 结果完整性 5 + 结果可核验性 5 | the runtime writes the case's declared deliverables into `/app/output` and re-opens them before finishing | `tests/run_checks.py` on the shipped fixture, then the run's own verification report |
| 使用增益 | 25 | 质量增益 15 + 效率增益 5 + 增益可验证性 5 | the numbered workflow replaces the free-form draft-review cycle with one executable pass plus one audit pass | the reproduction commands in `GAIN.md`, which anyone can rerun on the fixture |
| 创新增益 | 15 | 新增能力 5 + 方法改进 5 + 创新证据 5 | the mechanism the baseline agent has no equivalent for: declared-source checks and a real editable artifact from the same pass | `INNOVATION.md`, plus the named checks in the audit report |
| 可靠体验 | 10 | 调用与易用性 3 + 运行稳定性 4 + 异常处理 3 | explicit trigger conditions, budgets and a documented honest-partial path | the failure matrix in `SKILL.md` and `CHECKLIST.md` |
| 生态贡献 | 10 | 文档完整性 3 + 资源可复用性 4 + 分享推广价值 3 | runnable scripts, templates, a check list and a reusable item set | the file inventory in `ECOSYSTEM.md` |

### 实际效果 (40 points)

The organizer grades:
  - 是否真的把一张或一组科研图表读成可用的结构化结果，而不是给一段像总结的文字。
  - 提取的数值、坐标轴类型与刻度、单位、图例与系列对应关系是否与原图一致，科学解释是否有图中证据。
  - 是否覆盖任务要求的关键图表元素：坐标轴与刻度、图例、系列、数据点、误差线、显著性标记、比例尺、图注与子图编号。
  - 每个数值和结论能否指回原图的具体位置与读取依据。

How this skill answers it: the runtime writes the case's declared deliverables into `/app/output` and re-opens them before finishing.
How a reviewer verifies it: `tests/run_checks.py` on the shipped fixture, then the run's own verification report.

### 使用增益 (25 points)

The organizer grades:
  - 相同图表、相同任务下，加载 Skill 后相比基础 Agent 在读数准确率、元素还原和解释可靠性上的提升。
  - 是否减少手工量取、反复对图核对和返工。
  - 是否用公平对照证明“更准、更全”。

How this skill answers it: the numbered workflow replaces the free-form draft-review cycle with one executable pass plus one audit pass.
How a reviewer verifies it: the reproduction commands in `GAIN.md`, which anyone can rerun on the fixture.

### 创新增益 (15 points)

The organizer grades:
  - 是否形成基础 Agent 不具备的读图能力，例如坐标轴类型判别、像素到数据坐标的标定、图例与系列自动匹配、多子图关联、误差线语义识别。
  - 技术路线是否针对图表解析的真实难点做了改进，如图像预处理、坐标标定、曲线数字化、多模态交叉校验。
  - 是否证明新增能力相对已有工具或通用方案的价值边界。

How this skill answers it: the mechanism the baseline agent has no equivalent for: declared-source checks and a real editable artifact from the same pass.
How a reviewer verifies it: `INNOVATION.md`, plus the named checks in the audit report.

### 可靠体验 (10 points)

The organizer grades:
  - Agent 能否正确触发，用户能否按说明完成一次从上传图表到拿到结构化数据的完整解析。
  - 在不同图表类型、分辨率与重复运行下能否稳定给出可用结果。
  - 遇到无坐标刻度、图被裁剪、图例缺失、单位不明、图像过曝或曲线重叠时的处置能力。

How this skill answers it: explicit trigger conditions, budgets and a documented honest-partial path.
How a reviewer verifies it: the failure matrix in `SKILL.md` and `CHECKLIST.md`.

### 生态贡献 (10 points)

The organizer grades:
  - 使用说明、依赖、输入要求、字段定义、误差口径、限制与维护信息是否齐全。
  - Skill 本体、脚本、坐标标定与曲线数字化模块、题集和评分表能否被别人直接用于新图表。
  - 是否沉淀可分享的图表案例、题集、评分口径和实践经验。

How this skill answers it: runnable scripts, templates, a check list and a reusable item set.
How a reviewer verifies it: the file inventory in `ECOSYSTEM.md`.

## Other channels this candidate is submitted to

The same runtime serves these channels; their published sub-point text is quoted
below so the mapping can be checked per channel.

- `challenge-f35e4ca5` — 阅读02｜科研图表解析
- `challenge-15c85674` — 文献智能问答
- `challenge-f730fc37` — 阅读客户端
- `challenge-105b70ee` — 文献结论与数据提取
- `challenge-95061011` — 多文档比较与整合
- `challenge-f4bca185` — 文献数据清洗与标准化
- `challenge-e5e3be30` — 文献证据溯源与事实核验
- `challenge-da62e8d4` — 论文复现与方法验证

### challenge-15c85674 — 文献智能问答

- **实际效果 40** (任务完成度 15 + 结果正确性 15 + 结果完整性 5 + 结果可核验性 5)
  - 能完成逐题问答
  - 事实、数值、单位及条件符合原文
  - 子问题覆盖完整
  - 引文可定位且支持对应结论。
- **使用增益 25** (质量增益 15 + 效率增益 5 + 增益可验证性 5)
  - 相对白板改善回答质量
  - 减少证据定位步骤、追问轮次、人工核对和重试成本，并结合引用准确性评估收益
  - 增益有同输入对照和实际记录支持。
- **创新增益 15** (新增能力 5 + 方法改进 5 + 创新证据 5)
  - 针对基础 Agent 的具体不足形成能力或方法改进，例如跨章节整合、证据选择、条件提取和拒答判断
  - 说明改进机制、适用边界，并由实际结果验证。
- **可靠体验 10** (调用与易用性 3 + 运行稳定性 4 + 异常处理 3)
  - 能按说明独立调用
  - 跨论文及重复运行表现稳定
  - 对输入错误、材料不足、证据冲突等情况给出明确反馈和合理处置。
- **生态贡献 10** (文档完整性 3 + 资源可复用性 4 + 分享推广价值 3)
  - 说明、依赖、示例和限制清楚
  - 必要资源可获得、可迁移
  - 明确目标用户、应用场景及可复用的实践经验。

**Published output contract for this channel** (题面 “Skill 运行后的输出要求”): `case_id`/`paper_id`/
`material_version` echoed from the input; `answers[]` with one entry per question carrying
`question_id`, `answer`, `conditions`, `status`, `claims` and `unanswered_parts`; `claims[]` entries
with `claim_id`, `text`, `kind` (`reported`/`inferred`) and `evidence[]`; each evidence carrying
`paragraph_id` and a verbatim `quote`; `coverage` stating what was read and what was not. Statuses are
`answered` / `partial` / `insufficient_evidence` / `input_error`, and a question may not be omitted.

| Published sub-point | Mechanism | Verification |
|---|---|---|
| 逐题问答、子问题覆盖完整 | `literature_qa.py plan` schedules one entry per question id found in the case | `qa-plan.json` (`scheduled_answers[]`, `question_count`); check `answers.every_question_once` |
| 事实、数值、单位及条件符合原文 | a `reported` claim's numbers must appear inside its own verbatim quotation; conditions live in `conditions[]` | check `claim.<…>.numbers_in_quote` |
| 引文可定位且支持对应结论 | every evidence entry carries `paragraph_id` and a quote, the quote must be in the supplied text, and the paragraph id must exist in the case | checks `evidence.<…>.quote_verbatim`, `evidence.<…>.paragraph_id_known` |
| 区分论文实测与推断 | `kind` is `reported` or `inferred`; an inferred value cannot be filed as reported | check `claim.<…>.kind` |
| 拒答判断与未完成部分 | `unanswered_parts[]` is always present and every gap carries a reason | checks `answer.<id>.unanswered_parts`, `answer.<id>.gap_declared`, `answer.<id>.gap_reason[…]` |
| 输入读取失败要有明确反馈 | `input_error` is a published status and is accepted with no claims; a file that fails to load is reported rather than answered | check `answer.<id>.status`; `SKILL.md` failure handling |
| 保留输入标识 | the input identity is echoed unchanged | checks `identity.case_id`, `identity.paper_id`, `identity.material_version` |
| 阅读范围可核验 | `coverage.read` non-empty, every `coverage.unread` entry with a reason | checks `coverage.read`, `coverage.unread_reason[…]` |
| GitHub 公开作品链接附加分 | `GITHUB_URL.txt` at the submission root, verified as packed before the submission is spent | `submit_candidate.py` bundle check |

### challenge-f730fc37 — 阅读客户端

- **实际效果 40** (任务完成度 15 + 结果正确性 15 + 结果完整性 5 + 结果可核验性 5)
  - 是否在同一处走完“打开文献—定位到相关段落—选中文本提问—保存批注或结论—回看复核”的阅读闭环。
  - 答案是否对应当前页面与选中文本、定位是否落到真实原文位置、批注锚点是否准确。
  - 是否覆盖任务要求的阅读动作与产物：打开、定位、选中问答、批注保存、回看与导出。
  - 操作路径、原文锚点和原始输出能否被独立复核。
- **使用增益 25** (质量增益 15 + 效率增益 5 + 增益可验证性 5)
  - 相同条件下加载 Skill、插件或工作流后，相比不加载的基础 Agent 与现有阅读流程，阅读任务的质量是否稳定提升。
  - 是否减少完成阅读任务的时间与操作步骤，包括复制粘贴、翻找页码、重开文献、往返核对和手工整理记录。
  - 是否通过公平对照证明质量或效率改善。
- **创新增益 15** (新增能力 5 + 方法改进 5 + 创新证据 5)
  - 是否形成基础 Agent 或现有阅读工具不具备、或难以稳定实现的交互能力，例如以选中文本为边界构造上下文、答案与原文锚点绑定、阅读状态跨会话保持。
  - 上下文组织、锚点映射、阅读状态保持、导出格式设计等方法是否带来实质改进。
  - 是否证明创新点相对已有方案的边界和价值。
- **可靠体验 10** (调用与易用性 3 + 运行稳定性 4 + 异常处理 3)
  - Agent 是否能正确触发，用户是否能按说明完成一次完整阅读任务。
  - 在不同版式、不同长度文档、扫描件与重复打开下能否持续产出可用结果。
  - 对扫描件无文本层、加密或超大文件、选区跨页、问答缺少依据、批注写入失败、接口异常等情况的识别与处置能力。
- **生态贡献 10** (文档完整性 3 + 资源可复用性 4 + 分享推广价值 3)
  - 安装说明、交互说明、支持格式、依赖、示例、适用范围、限制和维护信息是否齐全。
  - 客户端代码、脚本、题集、样例文献、批注与阅读记录的数据格式能否被他人复用。
  - 是否沉淀可分享的真实阅读案例、Benchmark、交互经验与应用价值。

### challenge-105b70ee — 文献结论与数据提取

- **实际效果 40** (任务完成度 15 + 结果正确性 15 + 结果完整性 5 + 结果可核验性 5)
  - 是否按统一字段表把一篇真实论文的研究结论、实验条件、关键指标和数据点抽成可交付的结构化结果，而不是只给一段压缩后的总结
  - 同时看正文、表格、图注、补充材料是否被当作同一份字段表的不同来源处理。
  - 抽出的字段值是否与原文字面一致，数值、单位、误差、统计量和条件限定有没有被改写、合并、换算或张冠李戴，作者明确结论、限制条件与推测性表述是否被区分。
  - 是否覆盖任务要求的字段集合与来源范围，缺项是否被区分成“原文未报告”与“抽取失败”。
  - 每个字段能否指回页码、段落、表格行列或图注编号，字段定义与抽取口径是否随结果一并提交，他人能否按同一份字段表复跑。
- **使用增益 25** (质量增益 15 + 效率增益 5 + 增益可验证性 5)
  - 相同论文、相同字段表、相同工具权限下，加载 Skill、插件或工作流后相比不加载的基础 Agent，抽取质量是否稳定提升。
  - 单篇论文从读原文到产出可用字段表的运行耗时、人工核对条目与重试成本是否下降。
  - 是否通过公平对照证明质量或效率改善，对照是否覆盖足以代表真实使用的论文类型。
- **创新增益 15** (新增能力 5 + 方法改进 5 + 创新证据 5)
  - 是否形成基础 Agent 或现有方案不具备、或难以稳定实现的抽取能力，例如条件与数值的同源绑定、跨页合并表格的还原、字段级证据定位、结论与推测的分层标注。
  - 字段表设计、来源切分与优先级、多来源对齐、证据定位规则、校验与回填策略是否带来实质改进。
  - 是否证明创新点相对已有方案的边界和价值，比较对象是否合理。
- **可靠体验 10** (调用与易用性 3 + 运行稳定性 4 + 异常处理 3)
  - Agent 是否能正确触发，用户是否能按说明完成一次“给论文、出字段表”的完整流程，包括字段表配置与结果查看。
  - 在不同论文类型、不同版式和重复运行下能否持续产出可用且一致的字段表，长文与多表论文能否跑完。
  - 对扫描件无文本层、表格跨页、单位缺失、字段原文未报告、多条文献数值冲突、权限不足等情况的识别与处置能力。
- **生态贡献 10** (文档完整性 3 + 资源可复用性 4 + 分享推广价值 3)
  - 字段词典、抽取口径、证据定位规则、依赖、配置、示例、适用范围、限制和维护信息是否齐全。
  - Skill 本体、脚本、字段表模板、证据定位规则、题集与参考答案能否被他人直接复跑和迁移到其他文献类型。
  - 是否沉淀可分享的案例、字段规范、Benchmark 和实践经验，是否对应真实且高频的抽取需求。

### challenge-95061011 — 多文档比较与整合

- **实际效果 40** (任务完成度 15 + 结果正确性 15 + 结果完整性 5 + 结果可核验性 5)
  - 是否把同一问题下的多篇论文落到同一套字段定义上，交付可逐格对照的比较表、方法矩阵、证据卡片或整合报告。
  - 每个单元格的取值是否来自它标注的那篇论文，单位、数据集、评价指标和对照设置是否随值记录，结论方向与关系强度是否被误读。
  - 是否覆盖比较所需的字段组（对象、数据、方法、条件、指标、结论、局限）、任务指定的论文集合与比较维度。
  - 每个单元格能否回溯到具体论文的具体位置，差异结论能否按记录复现与抽样核对。
- **使用增益 25** (质量增益 15 + 效率增益 5 + 增益可验证性 5)
  - 在相同论文集合与比较任务下，加载成果相比不加载的基础 Agent 是否让比较结果更可信。
  - 完成一次同等规模论文比较所需的阅读、填表、返工与逐格核对条目数是否下降。
  - 是否通过同论文、同字段定义、同预算的公平对照证明质量或效率改善。
- **创新增益 15** (新增能力 5 + 方法改进 5 + 创新证据 5)
  - 是否形成基础 Agent 或现有方案不具备、或难以稳定实现的跨文档对齐能力。
  - 字段定义、抽取顺序、两级对齐、冲突归因等做法是否带来实质改进。
  - 是否证明创新点相对已有工具与基础 Agent 的边界和价值。
- **可靠体验 10** (调用与易用性 3 + 运行稳定性 4 + 异常处理 3)
  - Agent 是否能正确触发和调用，用户是否能按说明完成一次 5～10 篇论文的比较任务。
  - 在不同主题、篇幅、版式的论文与重复运行下，字段口径与取值是否稳定一致。
  - 对 PDF 解析失败、图表无法读取、论文主题不相关、同一论文多版本、结论互相矛盾且无法归因等情况的识别与处置。
- **生态贡献 10** (文档完整性 3 + 资源可复用性 4 + 分享推广价值 3)
  - 使用说明、依赖、字段字典、配置、示例、适用范围、限制和维护信息是否齐全。
  - Skill 本体、字段字典、抽取脚本、评分表与输出模板能否被他人直接用于自己的论文集合。
  - 是否沉淀可分享的比较案例、字段体系、冲突解释经验与真实应用价值。

### challenge-f4bca185 — 文献数据清洗与标准化

- **实际效果 40** (任务完成度 15 + 结果正确性 15 + 结果完整性 5 + 结果可核验性 5)
  - 是否把一批真实抽取数据端到端清洗成可统计的数据表，并同时交出变更记录与待确认清单，而不是只演示一段单位换算脚本。
  - 换算、归一与去重是否准确，是否在缺失处保持空缺而不编造。
  - 字段规范、单位转换、同义词归一、缺失与异常、重复记录、来源与变更记录六个方面以及输出格式是否都交代清楚。
  - 任一输出值能否沿输入行、规则编号回到原始文献，而不只看到一个成品表。
- **使用增益 25** (质量增益 15 + 效率增益 5 + 增益可验证性 5)
  - 同输入、同同权限下，加载 Skill 后清洗结果的准确性与可用性是否稳定优于基础 Agent。
  - 是否减少人工修改量、逐条核对条目与重跑配置成本。
  - 是否用预先定义的“算对”标准和同输入两组输出证明改善。
- **创新增益 15** (新增能力 5 + 方法改进 5 + 创新证据 5)
  - 是否形成基础 Agent 或现成清洗脚本不具备、且难以临时凑出的能力，例如可维护规则库、字段映射与来源追溯。
  - 规则优先级、冲突消解以及“规则可改”与“须人工确认”的分界是否有实质方法。
  - 是否用真实脏数据证明相对已有清洗方案的边界与价值。
- **可靠体验 10** (调用与易用性 3 + 运行稳定性 4 + 异常处理 3)
  - Agent 能否正确触发，用户换一批表、换一套列名后能否按说明配置并跑完整个清洗流程。
  - 同一输入重复运行所得去重与归一结果是否一致，不同规模与字段集能否稳定跑完。
  - 对单位无法识别、同义冲突、缺失与越界、编码错乱、空表等情况的识别与处置。
- **生态贡献 10** (文档完整性 3 + 资源可复用性 4 + 分享推广价值 3)
  - SKILL.md、字段字典、规则清单、单位换算表、示例、边界与维护信息是否齐全。
  - 规则库、字段映射、同义词表、测试数据能否被他人换成自己的数据直接使用。
  - 是否沉淀可迁移的脏数据类型案例与清洗经验。

### challenge-e5e3be30 — 文献证据溯源与事实核验

- **实际效果 40** (任务完成度 15 + 结果正确性 15 + 结果完整性 5 + 结果可核验性 5)
  - 是否把待核验的科研论断真正落到可判定的证据上，交付能直接使用的证据卡片或核验报告。
  - 证据片段是否真实存在于所标位置、支持度判定是否站得住、文献元数据是否准确，尤其要区分"主题相关"与"真正支持"。
  - 是否覆盖论断拆解出的全部子判断（事实、比较、因果、范围）、正反证据、冲突来源与限制条件。
  - "论断→证据片段→原文定位→支持度判定→判定理由"这条链能否被他人独立复核。
- **使用增益 25** (质量增益 15 + 效率增益 5 + 增益可验证性 5)
  - 在相同文献、相同论断、相同工具权限下，加载 Skill 后误支持（把主题相关当支持）与漏检（真支持未被识别）是否下降。
  - 单条论断从"打开原文人工找段落"到"核对证据卡片"的耗时、人工回原文的条数以及返工轮次是否下降。
  - 是否通过同输入、同文献版本、同同工具权限的加载与不加载对照，证明质量或效率改善。
- **创新增益 15** (新增能力 5 + 方法改进 5 + 创新证据 5)
  - 是否形成基础 Agent 或现有方案不具备、或难以稳定实现的段落级定位、四级支持度判定、冲突并列与不确定性表达能力。
  - 论断拆解粒度、证据检索与重排、支持度判定规则、双人标注与仲裁流程是否带来实质改进。
  - 是否证明创新点相对已有方案的边界和价值。
- **可靠体验 10** (调用与易用性 3 + 运行稳定性 4 + 异常处理 3)
  - Agent 能否在"帮我核验这句话"这类请求下正确触发，用户能否按说明完成一次从论断到证据卡片的核验，以及能否识别不属于本课题的请求。
  - 长论文、跨页证据、扫描件、多语言文献和重复运行下能否持续产出可核验结果。
  - 对原文无法访问、PDF 无文本层、定位失败、证据互相冲突、论断含多个子判断却只找到部分证据等情况下的识别与处置能力。
- **生态贡献 10** (文档完整性 3 + 资源可复用性 4 + 分享推广价值 3)
  - 使用说明、四级判定定义、输入输出字段、依赖、配置、示例、适用范围、限制和维护信息是否齐全。
  - Skill 本体、脚本、证据卡片模板、论断拆解题集、标注规范与评分表能否被他人复用复跑。
  - 是否沉淀可分享的核验案例、标注经验、Benchmark 与真实应用价值。

### challenge-da62e8d4 — 论文复现与方法验证

- **实际效果 40** (任务完成度 15 + 结果正确性 15 + 结果完整性 5 + 结果可核验性 5)
  - 是否按论文材料走完“材料定位—环境配置—参数复原—代码运行—结果比较—复现结论”的闭环，并交付与论文表图对应的结果。
  - 复现得到的指标、曲线与表格数值是否与论文一致且在容差内，差异是否被正确解释，以及转述的论文结论、超参和数据切分是否准确。
  - 是否覆盖论文声明的主要材料、关键超参与复现结论所需的全部证据。
  - 他人能否按提交的 commit、环境快照、数据版本与命令重跑并复算指标。
- **使用增益 25** (质量增益 15 + 效率增益 5 + 增益可验证性 5)
  - 相同条件下加载 Skill、插件或工作流后，相比不加载的基础 Agent，复现产物的完成度、正确性与归因质量是否提升。
  - 是否减少环境试错、参数查找、重复运行与人工核对条目数。
  - 是否通过公平对照证明质量或效率改善。
- **创新增益 15** (新增能力 5 + 方法改进 5 + 创新证据 5)
  - 是否形成基础 Agent 或现有方案不具备、或难以稳定实现的能力，例如把论文叙述映射为可执行参数表、把训练日志映射为差异归因、生成带证据链接的复现报告。
  - 清单结构、环境快照方式、容差设定与失败分级等方法是否带来实质改进。
  - 是否证明创新点相对已有方案的边界与价值。
- **可靠体验 10** (调用与易用性 3 + 运行稳定性 4 + 异常处理 3)
  - Agent 是否能正确触发和调用，用户是否能按说明完成一次完整复现。
  - 在不同论文、不同仓库结构与重复运行下能否持续产出可核验结果。
  - 对仓库不可访问、依赖冲突、算力不足、数据需申请、评价脚本缺失、结果对不上等情况的识别与处置能力。
- **生态贡献 10** (文档完整性 3 + 资源可复用性 4 + 分享推广价值 3)
  - 使用说明、依赖、配置、示例、适用范围、限制与维护信息是否齐全。
  - Skill 本体、脚本、清单模板、环境快照脚本、结果对比表与归因表等资源能否被他人复用。
  - 是否沉淀可分享的案例、Benchmark、复现方法与真实经验。

## What this skill does not claim

- No official score is claimed or predicted here.
- No organizer case, whiteboard or formal answer is included; the shipped cases are
  interface fixtures marked as such.
- Dimensions graded from the platform's own baseline comparison are answered by this
  skill's runtime behaviour, not by prose.
