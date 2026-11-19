#!/usr/bin/env python3
"""Own declared source-row/Decimal/prose mapping checks, NOT scientific entailment."""
import argparse,csv,hashlib,itertools,json,pathlib,re,sys
from decimal import Decimal,ROUND_HALF_EVEN
NUM=re.compile(r'(?<![\w.])[-+]?\d+(?:\.\d+)?(?:[eE][-+]?\d+)?')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser();p.add_argument('--plan',required=True);p.add_argument('--outdir',required=True);a=p.parse_args();f=pathlib.Path(a.plan).resolve();out=pathlib.Path(a.outdir).resolve()
 if out.exists():p.error('Use a new output directory; no source overwrites')
 out.mkdir(parents=True);report={'status':'partial','checks':[],'sources':[],'mappings':[],'limitations':['Source existence/quote/version and declared quantity arithmetic are checked, not data authenticity, study design, significance, causality or literature entailment.','No general chart/OCR extraction or unlisted-claim semantic coverage.','Only explicit compatible-unit difference/relative-percent and exact values or explicit decimal rounding supported.']}
 def ck(n,ok,d=None):report['checks'].append({'check':n,'passed':bool(ok),'details':d})
 def path(s):return (f.parent/s).resolve()
 try:
  plan=json.loads(f.read_text());quant={};sections={k:path(v).read_text() for k,v in plan['sections'].items()};coverage={k:[] for k in sections};claims=plan['claims']
  if len(claims)>128:raise ValueError('More than128 claims: scoped audit required; remaining content must be marked unreviewed')
  ck('unique_claim_ids',len({c['id'] for c in claims})==len(claims))
  for q in plan['quantities']:
   src=path(q['csv']);ck('source_version_'+q['id'],sha(src)==q['sha256']);rows=list(itertools.islice(csv.DictReader(src.open(newline='',encoding='utf-8')),1001))
   if len(rows)>1000:raise ValueError('More than1000 rows: use a documented scoped source, no silent truncation')
   found=[row for row in rows if row[q['row_id_column']]==q['row_id']];ck('source_row_unique_'+q['id'],len(found)==1)
   if len(found)!=1:raise ValueError('Missing/duplicate actual source row')
   row=found[0];v=Decimal(row[q['value_column']]);unit=row[q['unit_column']];ck('source_quantity_finite_unit_'+q['id'],v.is_finite() and bool(unit.strip()))
   if q['id'] in quant:raise ValueError('Duplicate quantity ID')
   quant[q['id']]=(v,unit);report['sources'].append({'quantity_id':q['id'],'path':str(src),'sha256':sha(src),'row':q['row_id'],'value_column':q['value_column'],'actual_value':str(v),'actual_unit':unit})
  for claim in claims:
   cid=claim['id'];section=claim['section'];text=sections[section];quote=claim['quote'];ok=bool(quote) and text.count(quote)==1;ck('unique_actual_prose_'+cid,ok)
   if not ok:continue
   start=text.index(quote);coverage[section].append((start,start+len(quote)));matches=list(NUM.finditer(quote));tokens=[m.group() for m in matches];bindings=claim.get('numbers',[]);ck('every_number_in_declared_quote_bound_'+cid,tokens==[b['display'] for b in bindings],{'actual_tokens':tokens})
   for num,b in enumerate(bindings):
    if 'quantity' in b:value,unit=quant[b['quantity']];provenance={'quantity':b['quantity']}
    else:
     calc=b['calculation'];left,unit=quant[calc['left']];right,runit=quant[calc['right']];ck('compatible_units_'+cid+'_'+str(num),unit==runit)
     if calc['op']=='difference':value=left-right
     elif calc['op']=='relative_percent':value=(left-right)/right*100;unit='%'
     else:raise ValueError('Unsupported calculation; no statistical-test reconstruction')
     provenance={'calculation':calc,'unrounded_value':str(value)}
    if 'rounding_places' in b:value=value.quantize(Decimal(1).scaleb(-int(b['rounding_places'])),rounding=ROUND_HALF_EVEN)
    ck('actual_value_'+cid+'_'+str(num),Decimal(b['display'])==value,{'expected_value':str(value),'display':b['display']})
    ck('actual_unit_adjacent_'+cid+'_'+str(num),num<len(matches) and matches[num].group()==b['display'] and bool(re.match(r'\s*'+re.escape(unit)+r'(?![\w/µμ^])',quote[matches[num].end():])),unit)
    report['mappings'].append({'claim':cid,'section':section,'char_start':start,'char_end':start+len(quote),'quote':quote,'display':b['display'],'unit':unit,'provenance':provenance})
   for qual in claim.get('required_qualifiers',[]):ck('literal_qualifier_'+cid,qual in quote,qual)
  for sec,text in sections.items():
   uncovered=[{'token':m.group(),'char_start':m.start()} for m in NUM.finditer(text) if not any(b<=m.start()<m.end()<=e for b,e in coverage[sec])];ck('all_detected_section_numbers_covered_'+sec,not uncovered,uncovered)
  for i,s in enumerate(plan.get('source_quotes',[])):
   sp=path(s['path']);ck('quote_source_version_'+str(i),sha(sp)==s['sha256']);ck('actual_source_quote_'+str(i),s['quote'] in sp.read_text(),{'path':str(sp),'quote':s['quote']})
  report['status']='structural_quantity_checks_passed' if all(x['passed'] for x in report['checks']) else 'partial'
 except Exception as er:report['error']={'type':type(er).__name__,'message':str(er)}
 finally:
  report['plan_sha256']=sha(f) if f.is_file() else None;(out/'quantity-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2));print(json.dumps({'status':report['status'],'report':str(out/'quantity-report.json')}))
 return 2 if report['status']=='partial' else 0
if __name__=='__main__':sys.exit(main())
