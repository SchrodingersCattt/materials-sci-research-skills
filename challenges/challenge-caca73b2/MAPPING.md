# Auxiliary quantity interface; NOT the original case result contract
Plan has sections {results: PATH, discussion: PATH}; quantities with unique id,csv,sha256,row_id_column,row_id,value_column,unit_column; claims with unique id,section,quote and ordered numbers bindings. Each binding has display and either quantity or calculation {op: difference|relative_percent,left,right}; right is the declared comparison baseline. Optional rounding_places applies Decimal ROUND_HALF_EVEN, not a significance/precision inference. The display with exact source/derived unit must be adjacent in the quote. Literal required_qualifiers are optional. source_quotes list path,sha256,quote existence checks. Relative paths use the plan's parent. All scientific/claim/evidence relation interpretation still requires reading and judgment, not this structural check.

Numbers are detected by a narrow ASCII decimal/exponent pattern. Detected numeric occurrences outside declared prose quotes are reported, but there is no universal numeric/semantic coverage claim. Every actual quote's detected numeric token sequence must exactly equal its bindings' displays. Input plots/images are NOT converted to precise data by these scripts. CSV extraction, when appropriate, must preserve genuine original locators and uncertainty, never invent values. Missing/ambiguous figures or tests must remain partial, not be fabricated.

## Minimal synthetic setup (not official source, score or result)
Run this code from a new writable work directory, outside the candidate. It creates toy source and prose from explicitly specified toy values, not scientific data. Source qualifier exists, but the helper only verifies actual quote existence and arithmetic; the host must still assess proper discussion boundaries.
```python
from pathlib import Path
import json,hashlib
p=Path('toy');p.mkdir()
(p/'data.csv').write_text('group,mean,unit\ncontrol,8,a.u.\ntreated,9,a.u.\n')
(p/'caption.txt').write_text('Synthetic only. Error bars denote SD; n and significance testing were not supplied.')
q='Control was 8 a.u.; treatment was 9 a.u.; the difference was 1 a.u. (12.5%).'
(p/'results.md').write_text('# Results\n\n'+q+'\n')
(p/'discussion.md').write_text('# Discussion\n\nThis descriptive comparison does not establish causality. Sample size and significance testing were not supplied.\n')
def h(n):return hashlib.sha256((p/n).read_bytes()).hexdigest()
qs=[{'id':i,'csv':'data.csv','sha256':h('data.csv'),'row_id_column':'group','row_id':i,'value_column':'mean','unit_column':'unit'} for i in ['control','treated']]
nums=[{'display':'8','quantity':'control'},{'display':'9','quantity':'treated'},{'display':'1','calculation':{'op':'difference','left':'treated','right':'control'}},{'display':'12.5','calculation':{'op':'relative_percent','left':'treated','right':'control'}}]
plan={'sections':{'results':'results.md','discussion':'discussion.md'},'quantities':qs,'claims':[{'id':'Q1','section':'results','quote':q,'numbers':nums}],'source_quotes':[{'path':'caption.txt','sha256':h('caption.txt'),'quote':'Error bars denote SD; n and significance testing were not supplied.'}]}
(p/'plan.json').write_text(json.dumps(plan))
```
Resolve SKILL_DIR from the ACTUAL loaded SKILL.md. Invoke `python "$SKILL_DIR/scripts/quantity_audit.py" --plan toy/plan.json --outdir toy-audit-new`. Expected interface (not an asserted past run): actual quantity-report.json with real row source/hash and independently recomputed difference/percent. To export if genuine verified tools/font exist, use that environment's Python with `"$SKILL_DIR/scripts/render_sections.py" --section toy/results.md --section toy/discussion.md --outdir toy-render-new --font "Liberation Serif"`, then open actual PNGs. Output files are genuine sections.docx/PDF/PNG and actual render-report, not renamed text.

A strong numerical negative changes ONLY actual prose 12.5% to25%, updates actual quote and display accordingly, while genuine table values and original mapping formula remain unchanged. Hashes/locators/prose existence stay valid, but actual_value_Q1_3 must fail. Do not call this a benchmark score or general scientific-validation result. Runtime official cases/schemas/materials are not bundled; original output_contract and case_id must be read and fulfilled separately.
