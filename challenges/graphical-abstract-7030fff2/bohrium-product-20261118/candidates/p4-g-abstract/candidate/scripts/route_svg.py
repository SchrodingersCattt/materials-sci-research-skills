#!/usr/bin/env python3
"""Source-locator-bearing orthogonal SVG diagrams; geometry only, not scientific validation."""
import json,math,pathlib,re,sys,unicodedata,xml.etree.ElementTree as E
SVG='http://www.w3.org/2000/svg';E.register_namespace('',SVG);NS=lambda x:'{'+SVG+'}'+x
COLORS={'material_flow':'#006D77','data_flow':'#355C7D','sequence':'#333333','control':'#BC6C25'}
DASH={'material_flow':'','data_flow':'7,4','sequence':'','control':'2,4'}
def num(v):return isinstance(v,(int,float)) and not isinstance(v,bool) and math.isfinite(v)
def evidence(v):return isinstance(v,list) and bool(v) and all(isinstance(x,dict) and bool(x.get('source')) and bool(x.get('locator')) for x in v)
def boundary(p,n):
 x,y=p; nx,ny,w,h=(n[k] for k in ('x','y','w','h'));eps=0.01
 return ((abs(x-nx)<eps or abs(x-(nx+w))<eps) and ny-eps<=y<=ny+h+eps) or ((abs(y-ny)<eps or abs(y-(ny+h))<eps) and nx-eps<=x<=nx+w+eps)
def crosses(a,b,n):
 x,y=a;u,v=b;nx,ny,w,h=(n[k] for k in ('x','y','w','h'))
 if y==v:return ny<y<ny+h and max(min(x,u),nx)<min(max(x,u),nx+w)
 return nx<x<nx+w and max(min(y,v),ny)<min(max(y,v),ny+h)
def generate(plan,out):
 width=plan.get('width');height=plan.get('height');nodes=plan.get('nodes');edges=plan.get('edges')
 if not num(width) or not num(height) or width<=0 or height<=0:raise ValueError('Invalid canvas')
 fontsize=plan.get('font_size',16);font=plan.get('font_family','sans-serif')
 if not num(fontsize) or not 8<=fontsize<=36 or not isinstance(font,str) or not font.strip():raise ValueError('Invalid font configuration')
 if not isinstance(nodes,list) or not nodes or len(nodes)>100 or not isinstance(edges,list) or len(edges)>200:raise ValueError('Invalid graph size')
 by={}
 for n in nodes:
  if not isinstance(n,dict):raise ValueError('Invalid node')
  ident=n.get('id');label=n.get('label')
  if not isinstance(ident,str) or not re.fullmatch(r'[A-Za-z_][A-Za-z0-9_.-]*',ident) or ident in by:raise ValueError('Invalid/duplicate node ID')
  if not isinstance(label,str) or not label.strip() or not evidence(n.get('evidence')):raise ValueError('Node label/source locator required')
  if any(not num(n.get(k)) for k in ('x','y','w','h')) or n['x']<0 or n['y']<0 or n['w']<40 or n['h']<35 or n['x']+n['w']>width or n['y']+n['h']>height:raise ValueError('Node outside canvas or too small')
  if len(label)>40:raise ValueError('Node label too long for narrow helper; use another editor')
  estimate=sum(1.0 if unicodedata.east_asian_width(c) in {'W','F'} else 0.6 for c in label)*fontsize
  if estimate>n['w']-12 or fontsize>n['h']-10:raise ValueError('Node label exceeds conservative size estimate')
  by[ident]=n
 for i,a in enumerate(nodes):
  for b in nodes[i+1:]:
   if max(a['x'],b['x'])<min(a['x']+a['w'],b['x']+b['w']) and max(a['y'],b['y'])<min(a['y']+a['h'],b['y']+b['h']):raise ValueError('Overlapping nodes')
 legend=plan.get('legend');kinds=sorted({e.get('kind') for e in edges if isinstance(e,dict) and e.get('kind') in COLORS})
 if edges:
  if not isinstance(legend,dict) or any(not num(legend.get(k)) for k in ('x','y','w','h')) or legend['x']<0 or legend['y']<0 or legend['w']<180 or legend['h']<20+24*len(kinds) or legend['x']+legend['w']>width or legend['y']+legend['h']>height:raise ValueError('Adequate legend box required')
  if any(max(n['x'],legend['x'])<min(n['x']+n['w'],legend['x']+legend['w']) and max(n['y'],legend['y'])<min(n['y']+n['h'],legend['y']+legend['h']) for n in nodes):raise ValueError('Legend overlaps node')
 used=set()
 for e in edges:
  if not isinstance(e,dict):raise ValueError('Invalid edge')
  ident=e.get('id');src=e.get('source');dst=e.get('target');kind=e.get('kind');pts=e.get('points')
  if not isinstance(ident,str) or not re.fullmatch(r'[A-Za-z_][A-Za-z0-9_.-]*',ident) or ident in used or ident in by:raise ValueError('Invalid/duplicate edge ID')
  used.add(ident)
  if src not in by or dst not in by or src==dst or kind not in COLORS or not evidence(e.get('evidence')):raise ValueError('Invalid edge/source/target/kind/evidence')
  if e.get('label') is not None:
   label=e['label'];lx=e.get('label_x');ly=e.get('label_y')
   if not isinstance(label,str) or not label.strip() or len(label)>40 or not num(lx) or not num(ly):raise ValueError('Invalid edge label')
   estimated=sum(1.0 if unicodedata.east_asian_width(c) in {'W','F'} else 0.6 for c in label)*13;box={'x':lx-estimated/2,'y':ly-13,'w':estimated,'h':17}
   if box['x']<0 or box['y']<0 or box['x']+box['w']>width or box['y']+box['h']>height:raise ValueError('Edge label outside canvas')
   for obstacle in nodes+([legend] if legend else []):
    if max(box['x'],obstacle['x'])<min(box['x']+box['w'],obstacle['x']+obstacle['w']) and max(box['y'],obstacle['y'])<min(box['y']+box['h'],obstacle['y']+obstacle['h']):raise ValueError('Edge label overlaps node or legend')
  if not isinstance(pts,list) or not 2<=len(pts)<=30 or any(not isinstance(p,list) or len(p)!=2 or not all(num(v) for v in p) or not 0<=p[0]<=width or not 0<=p[1]<=height for p in pts):raise ValueError('Invalid routed points')
  if not boundary(pts[0],by[src]) or not boundary(pts[-1],by[dst]):raise ValueError('Directed route must start/end on source/target boundary')
  for a,b in zip(pts,pts[1:]):
   if a==b or (a[0]!=b[0] and a[1]!=b[1]):raise ValueError('Only nonzero orthogonal segments supported')
   if any(crosses(a,b,n) for n in nodes):raise ValueError('Route crosses a node interior')
   if legend and crosses(a,b,legend):raise ValueError('Route crosses legend interior')
 out=pathlib.Path(out).resolve()
 if out.exists():raise ValueError('Fresh output directory required')
 out.mkdir(parents=True);root=E.Element(NS('svg'),{'width':str(width),'height':str(height),'viewBox':f'0 0 {width} {height}','role':'img'});defs=E.SubElement(root,NS('defs'))
 for kind,color in COLORS.items():
  mark=E.SubElement(defs,NS('marker'),{'id':'arrow-'+kind,'viewBox':'0 0 10 10','refX':'9','refY':'5','markerWidth':'7','markerHeight':'7','orient':'auto-start-reverse'});E.SubElement(mark,NS('path'),{'d':'M 0 0 L 10 5 L 0 10 z','fill':color})
 for e in edges:
  kind=e['kind'];attrs={'id':e['id'],'points':' '.join(f'{p[0]},{p[1]}' for p in e['points']),'fill':'none','stroke':COLORS[kind],'stroke-width':'2.5','marker-end':'url(#arrow-'+kind+')'}
  if DASH[kind]:attrs['stroke-dasharray']=DASH[kind]
  E.SubElement(root,NS('polyline'),attrs)
  if e.get('label') is not None:
   t=E.SubElement(root,NS('text'),{'x':str(e['label_x']),'y':str(e['label_y']),'text-anchor':'middle','font-family':font,'font-size':'13','fill':COLORS[kind]});t.text=e['label']
 for n in nodes:
  E.SubElement(root,NS('rect'),{'id':n['id'],'x':str(n['x']),'y':str(n['y']),'width':str(n['w']),'height':str(n['h']),'rx':'7','fill':'#ffffff','stroke':'#243b53','stroke-width':'2'})
  t=E.SubElement(root,NS('text'),{'x':str(n['x']+n['w']/2),'y':str(n['y']+n['h']/2+fontsize*0.35),'text-anchor':'middle','font-family':font,'font-size':str(fontsize),'fill':'#102a43'});t.text=n['label']
 if edges:
  E.SubElement(root,NS('rect'),{'x':str(legend['x']),'y':str(legend['y']),'width':str(legend['w']),'height':str(legend['h']),'fill':'#ffffff','stroke':'#cbd5e1'})
  for i,kind in enumerate(kinds):
   y=legend['y']+18+i*24;attrs={'x1':str(legend['x']+10),'y1':str(y),'x2':str(legend['x']+45),'y2':str(y),'stroke':COLORS[kind],'stroke-width':'2.5','marker-end':'url(#arrow-'+kind+')'}
   if DASH[kind]:attrs['stroke-dasharray']=DASH[kind]
   E.SubElement(root,NS('line'),attrs);t=E.SubElement(root,NS('text'),{'x':str(legend['x']+55),'y':str(y+5),'font-family':font,'font-size':'14','fill':'#102a43'});t.text=kind.replace('_',' ')
 target=out/'route.svg';E.ElementTree(root).write(target,encoding='utf8',xml_declaration=True);(out/'route-plan.json').write_text(json.dumps(plan,ensure_ascii=False,indent=2),encoding='utf8');(out/'route-source.py').write_bytes(pathlib.Path(__file__).read_bytes());report={'status':'generated_requires_visual_and_scientific_review','nodes':[{'id':n['id'],'evidence':n['evidence']} for n in nodes],'edges':[{'id':e['id'],'source':e['source'],'target':e['target'],'kind':e['kind'],'evidence':e['evidence']} for e in edges],'limits':'Caller-supplied locators and geometry are not scientific validation. Fonts, glyphs, arrows, layout and source semantics require visual and domain review.'};(out/'route-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8');return report
if __name__=='__main__':
 try:
  if len(sys.argv)!=3:raise ValueError('expected plan JSON and fresh output directory')
  r=generate(json.loads(pathlib.Path(sys.argv[1]).read_text(encoding='utf8')),sys.argv[2]);print(json.dumps({'status':r['status'],'nodes':len(r['nodes']),'edges':len(r['edges'])},ensure_ascii=False))
 except Exception as e:print(json.dumps({'status':'partial','error':str(e)},ensure_ascii=False));sys.exit(2)
