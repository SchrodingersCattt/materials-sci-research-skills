#!/usr/bin/env python3
"""Check normalized multi-document coverage, exact quotes and explicit context; not semantic proof."""
import decimal,json,sys
from pathlib import Path
KEYS=('task','metric','unit','material','pollutant','budget')
def check(target,sources,result):
 errors=[]; docs=target.get('document_ids'); fields=target.get('field_ids'); records=result.get('records'); src=sources.get('documents')
 if not isinstance(docs,list) or not docs or len(docs)!=len(set(docs)):return ['invalid document IDs'],[]
 if not isinstance(fields,list) or not fields or len(fields)!=len(set(fields)):return ['invalid field IDs'],[]
 if not isinstance(records,list) or not isinstance(src,dict):return ['unsupported records/source schema'],[]
 expected={(a,b) for a in docs for b in fields};actual=[];by={}
 for r in records:
  if not isinstance(r,dict):errors.append('invalid record');continue
  key=(r.get('document_id'),r.get('field_id'));actual.append(key);by[key]=r;status=r.get('status')
  if status not in {'reported','not_reported','source_conflict','extraction_failed'}:errors.append(str(key)+': invalid status');continue
  if status in {'not_reported','extraction_failed'}:
   if r.get('value') is not None or not r.get('reason'):errors.append(str(key)+': missing/failure value or reason invalid')
   continue
  if status=='reported' and r.get('value') is None:errors.append(str(key)+': reported value missing')
  ev=r.get('evidence');
  if not isinstance(ev,list) or not ev:errors.append(str(key)+': missing evidence');continue
  if status=='source_conflict' and len(ev)<2:errors.append(str(key)+': conflict needs multiple sources')
  for x in ev:
   if not isinstance(x,dict):errors.append(str(key)+': malformed evidence');continue
   doc=x.get('document_id');pid=x.get('paragraph_id');quote=x.get('quote');text=src.get(doc,{}).get(pid) if isinstance(src.get(doc),dict) else None
   if doc!=key[0] or not isinstance(text,str) or not isinstance(quote,str) or not quote or quote not in text:errors.append(str(key)+': quote/source mismatch')
   elif status=='reported' and r.get('value') is not None and str(r['value']) not in quote:errors.append(str(key)+': value not in exact quote')
 if len(actual)!=len(set(actual)) or set(actual)!=expected:errors.append('matrix coverage mismatch/duplicates')
 comparisons=[]
 for f in fields:
  for i,a in enumerate(docs):
   for b in docs[i+1:]:
    x=by.get((a,f),{});y=by.get((b,f),{});cx=x.get('context') or {};cy=y.get('context') or {};missing=[k for k in KEYS if cx.get(k) in (None,'') or cy.get(k) in (None,'')];diff=[k for k in KEYS if k not in missing and cx[k]!=cy[k]]
    status='blocked_by_validation_error' if errors else ('comparable_subject_to_scientific_review' if not missing and not diff and x.get('status')=='reported' and y.get('status')=='reported' else 'not_comparable_or_unavailable')
    row={'field_id':f,'documents':[a,b],'status':status,'missing_context':missing,'differing_context':diff}
    if status.startswith('comparable'):
     try:
      av=decimal.Decimal(str(x['value']));bv=decimal.Decimal(str(y['value']));
      if av.is_finite() and bv.is_finite():row['difference_second_minus_first']=str(bv-av)
     except (decimal.InvalidOperation,KeyError,TypeError):pass
    comparisons.append(row)
 return errors,comparisons
if __name__=='__main__':
 try:
  a=[json.loads(Path(p).read_text(encoding='utf8')) for p in sys.argv[1:]]
  if len(a)!=3:raise ValueError('expected target, sources, results JSON')
  e,c=check(*a)
 except Exception as x:print(json.dumps({'status':'input_error','error':str(x)}));raise SystemExit(2)
 print(json.dumps({'status':'fail' if e else 'pass','errors':e,'comparisons':c,'limits':'Exact label/quote checks only; source relevance, methodology and genuine comparability require scientific review.'},ensure_ascii=False));raise SystemExit(bool(e))
