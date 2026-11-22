#!/usr/bin/env python3
"""Perform narrow hash-pinned SVG text/fill edits; not a scientific or layout validator."""
import argparse,hashlib,json,pathlib,re,sys,xml.etree.ElementTree as ET
H=lambda b:hashlib.sha256(b).hexdigest()
def snapshot(node,changes):
 ident=node.get('id'); attrs={k:v for k,v in node.attrib.items() if (ident,'fill') not in changes or k!='fill'};text=None if (ident,'text') in changes else node.text
 return (node.tag,tuple(sorted(attrs.items())),text,node.tail,tuple(snapshot(c,changes) for c in node))
def edit(source,plan,out):
 source=source.resolve();out=out.resolve()
 if out.exists():raise ValueError('Fresh output directory required')
 raw=source.read_bytes()
 if H(raw)!=plan.get('source_sha256'):raise ValueError('Stale source hash')
 if b'<!DOCTYPE' in raw.upper() or b'<!ENTITY' in raw.upper():raise ValueError('DTD/entities unsupported')
 root=ET.fromstring(raw)
 if not root.tag.endswith('}svg') and root.tag!='svg':raise ValueError('Source is not SVG')
 changes=plan.get('edits')
 if not isinstance(changes,list) or not changes:raise ValueError('No explicit edits')
 byid={}
 for n in root.iter():
  if n.get('id'):byid.setdefault(n.get('id'),[]).append(n)
 keys=[]
 for e in changes:
  key=(e.get('id'),e.get('kind'));ident,kind=key
  if key in keys or len(byid.get(ident,[]))!=1 or kind not in {'text','fill'} or not e.get('workorder_id') or not e.get('reason'):raise ValueError('Invalid/ambiguous target or attribution')
  keys.append(key);n=byid[ident][0];old=e.get('old');new=e.get('new')
  if not isinstance(old,str) or not isinstance(new,str) or old==new:raise ValueError('Invalid old/new value')
  if kind=='text':
   if not n.tag.endswith('}text') and n.tag!='text':raise ValueError('Text edit requires text node')
   if list(n) or n.text!=old:raise ValueError('Text must be simple and exactly match original')
  else:
   if n.get('fill')!=old or not re.fullmatch(r'#[0-9A-Fa-f]{6}',new):raise ValueError('Fill must exactly match original; new fill must be #RRGGBB')
 before=snapshot(root,set(keys))
 for e in changes:
  n=byid[e['id']][0]
  if e['kind']=='text':n.text=e['new']
  else:n.set('fill',e['new'])
 out.mkdir(parents=True);target=out/'edited.svg';ET.ElementTree(root).write(target,encoding='utf8',xml_declaration=True);after=ET.parse(target).getroot()
 if snapshot(after,set(keys))!=before:raise ValueError('Unchanged structure differs')
 if source.read_bytes()!=raw:raise ValueError('Original source changed during edit')
 report={'status':'edited_requires_visual_and_scientific_review','original_sha256':H(raw),'output_sha256':H(target.read_bytes()),'edits':changes,'limits':'Only simple text/fill edits checked. Scientific meaning, visual quality, font availability, references and general SVG feature preservation require inspection.'};(out/'svg-edit-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8');return report
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--source',required=True);p.add_argument('--plan',required=True);p.add_argument('--outdir',required=True);a=p.parse_args()
 try:r=edit(pathlib.Path(a.source),json.loads(pathlib.Path(a.plan).read_text(encoding='utf8')),pathlib.Path(a.outdir));print(json.dumps({'status':r['status'],'edits':len(r['edits'])}))
 except Exception as e:print(json.dumps({'status':'partial','error':str(e)}));sys.exit(2)
