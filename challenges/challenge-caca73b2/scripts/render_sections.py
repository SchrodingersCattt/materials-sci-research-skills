#!/usr/bin/env python3
"""Real ordered doc-forge export and narrow plain-block fidelity gate; no scientific audit."""
import argparse,hashlib,importlib.metadata as md,json,pathlib,re,shutil,subprocess,sys,tempfile,time,zipfile
from xml.etree import ElementTree as ET
PIN='1fa02b08aea33debb3cc9fb1b5af138dd7e9b006';URL='https://github.com/SchrodingersCattt/doc-forge/archive/'+PIN+'.zip';W='{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def gfm_cells(line):
 """Split only unescaped pipes (including inside code spans, per GFM tables).
 Return cells and separator count; optional outer pipes are not empty cells.
 """
 line=line.strip();cuts=[];slashes=0
 for i,c in enumerate(line):
  if c=='|' and slashes%2==0:cuts.append(i)
  slashes=slashes+1 if c=='\\' else 0
 if not cuts:return [line],0
 cells=[];last=0
 for i in cuts:cells.append(line[last:i].strip());last=i+1
 cells.append(line[last:].strip())
 if cuts[0]==0:cells.pop(0)
 if cuts[-1]==len(line)-1:cells.pop()
 return cells,len(cuts)

def refuse_gfm_tables(text):
 """Narrow top-level header/delimiter guard, not a Markdown renderer.
 Containers/code/rules remain separately unsupported by plain_blocks.
 GFM permits optional outer pipes, one-hyphen cells and zero body rows.
 """
 lines=text.splitlines()
 for i in range(1,len(lines)):
  header,delimiter=lines[i-1],lines[i]
  if not header.strip() or not delimiter.strip():continue
  if re.match(r'^(?: {4}| *\t)',header) or re.match(r'^(?: {4}| *\t)',delimiter):continue
  if re.match(r'^ {0,3}(?:#{1,6}(?:[ \t]|$)|(?:[-*_][ \t]*){3,}$|(?:=+|-+)[ \t]*$)',header):continue
  h,hp=gfm_cells(header);d,dp=gfm_cells(delimiter)
  if (hp or dp) and h and len(h)==len(d) and all(re.fullmatch(r':?-+:?',c) for c in d):
   raise ValueError('GFM table header/delimiter at lines '+str(i)+'-'+str(i+1)+' unsupported by plain export; partial (no table exported)')

def plain_blocks(text):
 """Only ATX headings and soft-wrapped paragraphs;reject rich syntax first."""
 if len(text)>100000 or re.search(r'(?m)^\s*(?:```|~~~|>|[-*+]\s|\d+[.)]\s)|!\[|\$|<[^>]+>|\*\*|__|\[.*?\]\(',text):
  raise ValueError('Rich/oversized input unsupported by narrow full-text export gate; partial')
 refuse_gfm_tables(text)
 blocks=[];paragraph=[]
 def flush():
  if paragraph:blocks.append(' '.join(paragraph));paragraph.clear()
 for line in text.splitlines():
  if not line.strip():flush();continue
  if re.match(r'^ {4}|^\t',line) or re.match(r'^\s*(?:=+|-+)\s*$',line):
   raise ValueError('Indented code/setext/rule syntax outside narrow ATX/paragraph scope; partial')
  heading=re.match(r'^ {0,3}(#{1,6})[ \t]+(.+?)\s*$',line)
  if heading:
   flush();value=heading.group(2)
   if re.search(r'[ \t]+#+$',value):
    raise ValueError('Closing ATX markers outside verified plain-heading subset; partial')
   blocks.append(value)
  else:paragraph.append(line.strip())
 flush();return blocks

def ordered_blocks_equal(expected,actual):
 """Exact visible-unit sequence,not unordered/global substring matching."""
 norm=lambda s:' '.join(s.split())
 return [norm(s) for s in expected]==[norm(s) for s in actual if s.strip()]

def office_executable():
 """Use an actually available LibreOffice launcher; fail explicitly if absent."""
 path=shutil.which('libreoffice') or shutil.which('soffice')
 if not path:raise RuntimeError('LibreOffice/soffice is not available')
 return path

def main():
 p=argparse.ArgumentParser();p.add_argument('--section',action='append',required=True);p.add_argument('--outdir',required=True);p.add_argument('--font',default='Liberation Serif');p.add_argument('--budget-seconds',type=int,default=360);a=p.parse_args();out=pathlib.Path(a.outdir).resolve()
 if out.exists():p.error('New output directory required')
 out.mkdir(parents=True);begin=time.monotonic();report={'status':'partial','checks':[],'commands':[],'scope':'Own plain-block export technical checks only; not numerical/source/scientific validation.'};inputs=[pathlib.Path(x).resolve() for x in a.section];snapshot={}
 def ck(n,ok,d=None):report['checks'].append({'check':n,'passed':bool(ok),'details':d})
 def run(cmd):
  left=a.budget_seconds-(time.monotonic()-begin)
  if left<=0:raise RuntimeError('Helper time budget exhausted')
  try:q=subprocess.run(cmd,capture_output=True,text=True,timeout=min(120,left));d={'argv':cmd,'exit':q.returncode,'stdout':q.stdout,'stderr':q.stderr}
  except (OSError,subprocess.TimeoutExpired) as er:d={'argv':cmd,'exit':None,'error':str(er)}
  report['commands'].append(d)
  if d['exit']!=0:raise RuntimeError('Actual tool failed: '+cmd[0])
  return d['stdout']
 try:
  expected=[]
  if len(inputs)>16:raise ValueError('More than16 sections; scope export and mark remainder')
  for f in inputs:
   text=f.read_text();snapshot[str(f)]=sha(f)
   expected.extend(plain_blocks(text))
  dist=md.distribution('docforge');direct=json.loads(dist.read_text('direct_url.json') or '{}');report['dependency']={'version':dist.version,'direct_url':direct}
  if direct.get('url')!=URL:raise RuntimeError('Genuine pinned docforge provenance not verified')
  exe=pathlib.Path(sys.executable).parent/('docforge.exe' if sys.platform=='win32' else 'docforge');family=run(['fc-match','-f','%{family}',a.font]);ck('requested_local_font',a.font.lower() in family.lower(),family)
  target=out/'sections.docx';run([str(exe),'md2docx',*[str(x) for x in inputs],'-o',str(target),'--standalone-style','manuscript','--font',a.font,'--keep-comments','--table-grouping','off','--table-notes','explicit'])
  with zipfile.ZipFile(target) as z:root=ET.fromstring(z.read('word/document.xml'))
  actual=[''.join(t.text or '' for t in q.iter(W+'t')) for q in root.iter(W+'p')];norm=lambda x:' '.join(x.split());ck('all_plain_blocks_in_docx_order',ordered_blocks_equal(expected,actual));audit=run([str(exe),'audit',str(target)]);ck('native_docforge_package_audit',json.loads(audit).get('status')=='pass',audit)
  with tempfile.TemporaryDirectory(prefix='sections-lo-') as tmp:run([office_executable(),'-env:UserInstallation='+pathlib.Path(tmp).as_uri(),'--headless','--convert-to','pdf','--outdir',str(out),str(target)])
  pdf=target.with_suffix('.pdf')
  if not pdf.is_file() or not pdf.read_bytes().startswith(b'%PDF-'):raise RuntimeError('Actual PDF missing')
  run(['pdftoppm','-scale-to','1200','-png',str(pdf),str(out/'preview')]);ck('actual_png_exists',bool(list(out.glob('preview-*.png'))));text=norm(run(['pdftotext',str(pdf),'-']));position=0;ok=True
  for block in expected:
   index=text.find(norm(block),position)
   if index<0:ok=False;break
   position=index+len(norm(block))
  ck('all_plain_blocks_in_pdf_order',ok);fonts=run(['pdffonts',str(pdf)]);lines=fonts.splitlines()[2:];ck('actual_pdf_font_embedded',bool(lines) and all(len(l.split())>=6 and l.split()[-5]=='yes' for l in lines),fonts);ck('requested_pdf_family',any(a.font.replace(' ','').lower() in l.replace(' ','').lower() for l in lines))
  for f in inputs:ck('source_unchanged_'+f.name,sha(f)==snapshot[str(f)])
  report['status']='technical_checks_passed' if all(x['passed'] for x in report['checks']) else 'partial'
 except Exception as er:report['error']={'type':type(er).__name__,'message':str(er)}
 finally:
  report['source_sha256']=snapshot;report['artifacts']=[{'path':str(f),'sha256':sha(f)} for f in out.rglob('*') if f.is_file()];(out/'render-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2));print(json.dumps({'status':report['status'],'report':str(out/'render-report.json')}))
 return 0 if report['status']=='technical_checks_passed' else 2
if __name__=='__main__':sys.exit(main())
