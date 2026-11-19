import importlib.util,tempfile,unittest,subprocess,sys,zipfile,copy
from pathlib import Path
from xml.etree import ElementTree as ET
BASE=Path(__file__).parents[1]
s=importlib.util.spec_from_file_location("editor",BASE/"scripts/edit_slides.py")
m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
class Checks(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name)
  subprocess.run([sys.executable,str(BASE/"examples/synthetic_case.py"),"--outdir",str(self.root)],check=True,capture_output=True)
  self.deck=self.root/"template-deck.pptx";self.parts,self.names=m.read_parts(self.deck)
 def tearDown(self):self.tmp.cleanup()
 def save(self):
  with zipfile.ZipFile(self.deck,"w") as z:
   for name in self.names:z.writestr(name,self.parts[name])
 def merged(self,plan):
  r=m.merge(self.deck,plan,self.root/"out");p,n=m.read_parts(Path(r["out"]["path"]));return r,p
 def test_requested_unused_layout(self):
  layout=ET.fromstring(self.parts["ppt/slideLayouts/slideLayout1.xml"]);layout.find("{"+m.P+"}cSld").set("name","Unused Layout");layout.set("type","unused")
  name="ppt/slideLayouts/slideLayout2.xml";self.parts[name]=ET.tostring(layout);self.names.append(name)
  relname="ppt/slideLayouts/_rels/slideLayout2.xml.rels";self.parts[relname]=self.parts["ppt/slideLayouts/_rels/slideLayout1.xml.rels"];self.names.append(relname)
  ct=ET.fromstring(self.parts["[Content_Types].xml"]);ET.SubElement(ct,"{http://schemas.openxmlformats.org/package/2006/content-types}Override",{"PartName":"/"+name,"ContentType":"application/vnd.openxmlformats-officedocument.presentationml.slideLayout+xml"});self.parts["[Content_Types].xml"]=ET.tostring(ct)
  self.save()
  r,p=self.merged({"slides":[{"layout":"Unused Layout","title":{"text":"New title"}}]})
  new=r["operations"][0]["part"];rels=m.rels_of(p,new)
  self.assertEqual(next(x["resolved"] for x in rels.values() if x["type"].endswith("/slideLayout")),name)
  self.assertIn(b"New title",p[new]);self.assertTrue(r["template_parts_unchanged"])
  relname="ppt/slides/_rels/"+new.split("/")[-1]+".rels"
  p[relname]=p[relname].replace(b"slideLayout2.xml",b"slideLayout1.xml")
  wrong=self.root/"wrong.pptx"
  with zipfile.ZipFile(wrong,"w") as z:
   for name,raw in p.items():z.writestr(name,raw)
  checked=m.check(self.deck,wrong,{"slides":[{"layout":"Unused Layout","title":{"text":"New title"}}]},self.root/"out")
  self.assertTrue(any(x["id"]=="requested_layout" and x["status"]=="fail" for x in checked["checks"]))
 def test_presentation_order(self):
  pr=ET.fromstring(self.parts["ppt/presentation.xml"]);lst=pr.find("{"+m.P+"}sldIdLst");a,b=list(lst);lst.remove(a);lst.append(a)
  self.parts["ppt/presentation.xml"]=ET.tostring(pr);self.save()
  before=self.parts["ppt/slides/slide1.xml"]
  r,p=self.merged({"slides":[{"target_slide":1,"title":{"text":"First visible slide"}}]})
  self.assertEqual(p["ppt/slides/slide1.xml"],before)
  self.assertIn(b"First visible slide",p["ppt/slides/slide2.xml"])
 def test_unknown_named_layout(self):
  r,p=self.merged({"slides":[{"layout":"Not A Real Layout","title":{"text":"Should not add"}}]})
  self.assertEqual(r["slides_added"],0)
  self.assertEqual(r["operations"][0]["status"],"layout_not_found")
 def test_centered_title(self):
  tree=ET.fromstring(self.parts["ppt/slides/slide1.xml"]);tree.find(".//{"+m.P+"}ph").set("type","ctrTitle")
  self.assertIsNotNone(m.find_shape_by_placeholder(tree,"title"))
if __name__=="__main__":unittest.main()
